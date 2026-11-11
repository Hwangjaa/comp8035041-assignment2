import os
import sys
import json
import hashlib
import platform
import subprocess
import traceback
import logging
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    average_precision_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)
import networkx as nx

os.environ.setdefault(
    "MPLCONFIGDIR",
    os.path.join(os.environ.get("TMPDIR", "."), "dataco-mpl"),
)

SINGLE_VALUED_COLUMNS = [
    "Days for shipment (scheduled)",
    "Customer Segment",
    "Market",
    "order date (DateOrders)",
    "Late_delivery_risk",
]
# Retain backward-compatible alias for existing test imports
SINGLE = SINGLE_VALUED_COLUMNS


def dump_json(file_path, data):
    """Serialize data to JSON with indentation and UTF-8 encoding."""
    target_path = Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str, allow_nan=False),
        encoding="utf-8",
    )


# Retain alias for test compatibility
dump = dump_json


def compute_sha256(file_path):
    """Compute SHA-256 checksum of a file in 1MB chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# Retain alias for test compatibility
sha = compute_sha256


def make_orders(raw_df):
    """Clean and aggregate item-level transactions into order-level records."""
    required_columns = SINGLE_VALUED_COLUMNS + [
        "Order Id",
        "Order Item Id",
        "Category Id",
        "Delivery Status",
    ]

    missing_cols = set(required_columns) - set(raw_df.columns)
    if missing_cols:
        raise ValueError(f"Kolom wajib tidak tersedia: {sorted(missing_cols)}")

    critical_fields = [
        "Order Id",
        "Order Item Id",
        "Days for shipment (scheduled)",
        "Late_delivery_risk",
    ]
    if raw_df[critical_fields].isna().any().any():
        raise ValueError("Missing numerik/identitas/target wajib: pipeline berhenti")

    canceled_mask = raw_df["Delivery Status"].eq("Shipping canceled")
    status_summary = canceled_mask.groupby(raw_df["Order Id"]).agg(["any", "all"])
    mixed_orders = status_summary.index[
        status_summary["any"] != status_summary["all"]
    ].tolist()
    if mixed_orders:
        raise ValueError(f"Pesanan campuran batal/nonbatal: {mixed_orders}")

    retained_df = raw_df.loc[~canceled_mask, required_columns].copy()

    conflicts = retained_df.groupby("Order Id")[SINGLE_VALUED_COLUMNS].nunique(dropna=False)
    inconsistent_orders = conflicts.loc[(conflicts > 1).any(axis=1)]
    if len(inconsistent_orders) > 0:
        raise ValueError(f"Konflik singleton/target Order Id: {inconsistent_orders.to_json()}")

    target_values = set(retained_df["Late_delivery_risk"].unique())
    if not target_values <= {0, 1}:
        raise ValueError("Target bukan binary 0/1")

    for numeric_col in ["Days for shipment (scheduled)", "Order Id", "Order Item Id"]:
        values = retained_df[numeric_col].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"Numerik nonfinite: {numeric_col}")

    orders_df = retained_df.groupby("Order Id", sort=True)[SINGLE_VALUED_COLUMNS].first()
    orders_df["item_count"] = retained_df.groupby("Order Id")["Order Item Id"].nunique()

    def extract_categories(series):
        tokens = set(
            "MISSING" if pd.isna(val) else str(int(val)) for val in series
        )
        return sorted(tokens)

    orders_df["categories"] = retained_df.groupby("Order Id")["Category Id"].apply(
        extract_categories
    )

    date_series = orders_df.pop("order date (DateOrders)")
    orders_df["order_date"] = pd.to_datetime(
        date_series, format="%m/%d/%Y %H:%M", errors="raise"
    )
    if orders_df["order_date"].isna().any():
        raise ValueError("Tanggal pesanan missing")

    train_cutoff = pd.Timestamp("2017-07-01")
    val_cutoff = pd.Timestamp("2017-10-01")

    orders_df["partition"] = np.where(
        orders_df.order_date < train_cutoff,
        "train",
        np.where(orders_df.order_date < val_cutoff, "validation", "test"),
    )

    audit_summary = {
        "source_rows": len(raw_df),
        "source_orders": int(raw_df["Order Id"].nunique()),
        "excluded_items": int(canceled_mask.sum()),
        "excluded_orders": int(status_summary["all"].sum()),
        "mixed_orders": len(mixed_orders),
        "retained_items": len(retained_df),
        "retained_orders": len(orders_df),
        "singleton_conflicts": 0,
        "label_conflicts": 0,
        "missing_category_items": int(retained_df["Category Id"].isna().sum()),
    }

    return orders_df.reset_index(), retained_df, audit_summary


class Features:
    """Feature engineering and multi-hot vector encoding for order attributes."""

    def __init__(self):
        self.vocab = {}
        self.names = []
        self.fit_order_ids = []

    def fit(self, train_df):
        self.vocab = {}
        for col in ["Customer Segment", "Market"]:
            unique_vals = set(train_df[col].dropna().astype(str)) | {"MISSING", "UNKNOWN"}
            self.vocab[col] = sorted(unique_vals)

        category_ids = set(
            cat_id for cat_list in train_df["categories"] for cat_id in cat_list
        ) | {"MISSING", "UNKNOWN"}
        self.vocab["Category Id"] = sorted(category_ids)

        self.names = [
            "Days for shipment (scheduled)",
            "unique_Order_Item_Id_count",
        ] + [
            f"{col}={val}"
            for col, val_list in self.vocab.items()
            for val in val_list
        ]
        self.fit_order_ids = train_df["Order Id"].astype(int).tolist()
        return self

    def transform(self, df):
        rows = []
        cols = []
        values = []

        numeric_matrix = df[["Days for shipment (scheduled)", "item_count"]].to_numpy(
            dtype=float
        )
        if not np.isfinite(numeric_matrix).all():
            raise ValueError("Missing/nonfinite numerik")

        num_records = len(df)
        for i in range(num_records):
            for j in range(2):
                rows.append(i)
                cols.append(j)
                values.append(numeric_matrix[i, j])

        col_offset = 2
        for col_name, vocab_list in self.vocab.items():
            lookup = {val: idx for idx, val in enumerate(vocab_list)}
            for i, (_, record) in enumerate(df.iterrows()):
                if col_name == "Category Id":
                    tokens = record["categories"]
                else:
                    field_val = record[col_name]
                    tokens = ["MISSING" if pd.isna(field_val) else str(field_val)]

                mapped_tokens = set(t if t in lookup else "UNKNOWN" for t in tokens)
                for token in mapped_tokens:
                    rows.append(i)
                    cols.append(col_offset + lookup[token])
                    values.append(1.0)
            col_offset += len(vocab_list)

        return sparse.csr_matrix(
            (values, (rows, cols)),
            shape=(num_records, len(self.names)),
        )


def threshold(y_true, y_prob):
    """Identify optimal classification threshold maximizing binary F1 score."""
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(y_prob, dtype=float)

    sorted_indices = np.argsort(-p, kind="stable")
    y = y[sorted_indices]
    p = p[sorted_indices]

    best_f1 = Fraction(0)
    best_t = float(np.nextafter(p.max(), np.inf))
    total_positives = int(y.sum())
    true_positives = 0
    start = 0

    while start < len(y):
        end = start + 1
        while end < len(y) and p[end] == p[start]:
            end += 1

        true_positives += int(y[start:end].sum())
        denominator = total_positives + end
        current_f1 = (
            Fraction(2 * true_positives, denominator)
            if denominator > 0
            else Fraction(0)
        )

        if current_f1 > best_f1 or (current_f1 == best_f1 and p[start] > best_t):
            best_f1 = current_f1
            best_t = float(p[start])

        start = end

    return best_t


def evaluate(y_true, y_prob, decision_threshold):
    """Compute precision, recall, F1, and PR-AUC metrics at given threshold."""
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(y_prob, dtype=float)
    predictions = (p >= decision_threshold).astype(int)

    assert len(y) == len(p)
    assert np.isfinite(p).all()
    assert ((p >= 0) & (p <= 1)).all()

    conf_mat = confusion_matrix(y, predictions, labels=[0, 1]).ravel().astype(int).tolist()
    assert sum(conf_mat) == len(y)

    return {
        "n": len(y),
        "average_precision": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "binary_f1": float(f1_score(y, predictions, zero_division=0)),
        "confusion_matrix": conf_mat,
        "confusion_matrix_order": ["TN", "FP", "FN", "TP"],
        "threshold": float(decision_threshold),
        "undefined": ["precision"] if not predictions.sum() else [],
    }


def run(root, out):
    """Execute end-to-end Big Data Analytics training, evaluation, and graph pipeline."""
    root_dir = Path(root).resolve()
    out_dir = Path(out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(out_dir / "execution.log"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    start_time = datetime.now(timezone.utc).isoformat()
    config = {
        "started_utc": start_time,
        "seed": 42,
        "split": {
            "train": "order_date < 2017-07-01",
            "validation": "2017-07-01 <= order_date < 2017-10-01",
            "test": "order_date >= 2017-10-01",
        },
        "gap": "none; label maturation unknown",
        "benchmark": "not performed",
        "feature_groups": [
            "Days for shipment (scheduled)",
            "Customer Segment",
            "Market",
            "Category Id multi-hot",
            "unique Order Item Id count",
        ],
        "threshold": "validation binary F1 maximum; ties largest; >=; all-negative candidate included",
        "refit": False,
        "storage": "local file:///; not HDFS",
    }
    dump_json(out_dir / "config.json", config)

    try:
        logging.info("A: audit sumber dan environment")
        manifest = json.loads((root_dir / "data/source-manifest.json").read_text())
        data_manifest = []

        for file_entry in manifest["files"]:
            file_path = root_dir / "data/raw" / Path(file_entry["file"]).name
            digest = compute_sha256(file_path)
            if digest != file_entry["sha256"]:
                raise ValueError(f"SHA256 mismatch {file_path}")

            parsed = pd.read_csv(file_path, encoding="latin1", low_memory=False)
            data_manifest.append({
                "file": str(file_path),
                "bytes": file_path.stat().st_size,
                "sha256": digest,
                "matches_prior_manifest": True,
                "rows": len(parsed),
                "columns": len(parsed.columns),
                "schema": {c: str(t) for c, t in parsed.dtypes.items()},
            })

        dump_json(
            out_dir / "data-manifest.json",
            {
                "source": manifest["source"],
                "comparison": "manifest lokal yang tersedia; tidak mengambil ulang metadata penerbit",
                "files": data_manifest,
            },
        )

        import sklearn
        import scipy
        import pyspark
        import matplotlib

        java_home = os.environ.get("JAVA_HOME", "")
        java_bin = str(Path(java_home) / "bin/java") if java_home else "java"
        java_version = subprocess.run(
            [java_bin, "-version"], capture_output=True, text=True
        ).stderr

        env_info = {
            "python": sys.version,
            "executable": sys.executable,
            "platform": platform.platform(),
            "versions": {
                m.__name__: m.__version__
                for m in [pd, np, sklearn, scipy, pyspark, nx, matplotlib]
            },
            "java": java_version,
            "thread_environment": {
                k: os.environ.get(k)
                for k in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"]
            },
        }
        dump_json(out_dir / "environment.json", env_info)
        (out_dir / "requirements-observed.txt").write_text(
            subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout
        )

        raw_dataset = pd.read_csv(
            root_dir / "data/raw/DataCoSupplyChainDataset.csv",
            encoding="latin1",
            low_memory=False,
        )
        orders, items, audit_stats = make_orders(raw_dataset)
        del raw_dataset

        dump_json(out_dir / "audit-orders.json", audit_stats)
        orders.assign(categories=orders.categories.map(json.dumps)).to_csv(
            out_dir / "orders.csv", index=False
        )

        split_table = (
            orders.groupby(["partition", "Late_delivery_risk"])
            .size()
            .unstack(fill_value=0)
            .reindex(["train", "validation", "test"])
        )
        split_table.columns = ["label_0", "label_1"]
        split_table["total"] = split_table.sum(axis=1)
        split_table.to_csv(out_dir / "split.csv")

        assert orders["Order Id"].is_unique
        assert int(split_table.total.sum()) == len(orders)

        partitions = {
            p: orders.loc[orders.partition == p].copy()
            for p in ["train", "validation", "test"]
        }
        encoder = Features().fit(partitions["train"])
        features_dict = {p: encoder.transform(d) for p, d in partitions.items()}
        labels_dict = {
            p: d["Late_delivery_risk"].to_numpy(dtype=int)
            for p, d in partitions.items()
        }

        dump_json(
            out_dir / "feature-contract.json",
            {
                "vocabulary": encoder.vocab,
                "feature_names": encoder.names,
                "n_features": len(encoder.names),
                "fit_partition": "train",
                "fit_order_ids_sha256": hashlib.sha256(
                    json.dumps(encoder.fit_order_ids).encode()
                ).hexdigest(),
                "shape": {p: list(x.shape) for p, x in features_dict.items()},
                "forbidden_predictors_present": False,
                "numeric_units": "original; no scaling/log",
                "source_columns": config["feature_groups"],
            },
        )

        assert features_dict["train"].shape[1] == len(encoder.names)
        assert all(x.shape[1] == len(encoder.names) for x in features_dict.values())
        logging.info(
            "B: order dan fitur selesai: %s; ukuran %s",
            audit_stats,
            {p: x.shape for p, x in features_dict.items()},
        )

        lr_model = LogisticRegression(
            C=1.0,
            solver="lbfgs",
            max_iter=1000,
            tol=1e-6,
            random_state=42,
            class_weight=None,
            l1_ratio=0.0,
        )
        lr_model.fit(features_dict["train"], labels_dict["train"])
        assert lr_model.classes_.tolist() == [0, 1]

        baseline_dummy = DummyClassifier(strategy="prior", random_state=42).fit(
            features_dict["train"], labels_dict["train"]
        )

        import joblib

        joblib.dump(lr_model, out_dir / "sklearn-model.joblib")
        joblib.dump(baseline_dummy, out_dir / "baseline-model.joblib")
        joblib.dump(encoder, out_dir / "preprocessor.joblib")

        dump_json(out_dir / "sklearn-parameters.json", lr_model.get_params())
        dump_json(
            out_dir / "baseline-parameters.json",
            {
                "parameters": baseline_dummy.get_params(),
                "classes": baseline_dummy.classes_.tolist(),
                "class_prior": baseline_dummy.class_prior_.tolist(),
                "majority_class": int(
                    baseline_dummy.classes_[np.argmax(baseline_dummy.class_prior_)]
                ),
            },
        )

        from pyspark.sql import SparkSession, types as T
        from pyspark.ml.linalg import Vectors, VectorUDT
        from pyspark.ml.classification import LogisticRegression as SparkLR

        spark = (
            SparkSession.builder.master("local[2]")
            .appName("COMP8035041-Assignment-II")
            .config("spark.driver.bindAddress", "127.0.0.1")
            .config("spark.sql.shuffle.partitions", "2")
            .config("spark.default.parallelism", "2")
            .config("spark.driver.memory", "2g")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")

        dump_json(
            out_dir / "spark-environment.json",
            {
                "version": spark.version,
                "master": spark.sparkContext.master,
                "conf": dict(spark.sparkContext.getConf().getAll()),
                "defaultFS": spark.sparkContext._jsc.hadoopConfiguration().get(
                    "fs.defaultFS"
                ),
            },
        )

        spark_schema = T.StructType([
            T.StructField("Order Id", T.LongType(), False),
            T.StructField("label", T.DoubleType(), False),
            T.StructField("features", VectorUDT(), False),
        ])

        def create_spark_df(partition_key):
            matrix = features_dict[partition_key]
            order_ids = partitions[partition_key]["Order Id"].to_numpy()
            target_labels = labels_dict[partition_key]
            rows_data = [
                (
                    int(order_ids[i]),
                    float(target_labels[i]),
                    Vectors.sparse(
                        matrix.shape[1],
                        matrix[i].indices.tolist(),
                        matrix[i].data.tolist(),
                    ),
                )
                for i in range(matrix.shape[0])
            ]
            return spark.createDataFrame(rows_data, spark_schema)

        spark_train_df = create_spark_df("train")
        spark_lr_trainer = SparkLR(
            regParam=0.1,
            elasticNetParam=0.0,
            maxIter=1000,
            tol=1e-6,
            standardization=False,
        )
        spark_model = spark_lr_trainer.fit(spark_train_df)
        spark_model.write().overwrite().save(str(out_dir / "spark-model"))
        dump_json(
            out_dir / "spark-parameters.json",
            {param.name: val for param, val in spark_model.extractParamMap().items()},
        )

        def spark_predict_probabilities(partition_key):
            transformed_rows = (
                spark_model.transform(create_spark_df(partition_key))
                .select("Order Id", "probability")
                .collect()
            )
            prob_by_id = {int(r[0]): float(r[1][1]) for r in transformed_rows}
            assert len(prob_by_id) == len(partitions[partition_key])
            return np.array([
                prob_by_id[int(order_id)]
                for order_id in partitions[partition_key]["Order Id"]
            ])

        val_probabilities = {
            "baseline": baseline_dummy.predict_proba(features_dict["validation"])[:, 1],
            "sklearn_lr": lr_model.predict_proba(features_dict["validation"])[:, 1],
            "spark_lr": spark_predict_probabilities("validation"),
        }

        optimal_thresholds = {
            model_name: threshold(labels_dict["validation"], prob_array)
            for model_name, prob_array in val_probabilities.items()
        }

        dump_json(
            out_dir / "thresholds-frozen.json",
            {
                "frozen_utc": datetime.now(timezone.utc).isoformat(),
                "selection_partition": "validation",
                "test_predictions_not_yet_computed": True,
                "thresholds": optimal_thresholds,
            },
        )
        logging.info("C: threshold validation dibekukan %s", optimal_thresholds)

        evaluation_probabilities = {
            "validation": val_probabilities,
            "test": {
                "baseline": baseline_dummy.predict_proba(features_dict["test"])[:, 1],
                "sklearn_lr": lr_model.predict_proba(features_dict["test"])[:, 1],
                "spark_lr": spark_predict_probabilities("test"),
            },
        }

        metrics_results = []
        for partition_name, models_preds in evaluation_probabilities.items():
            for model_name, prob_scores in models_preds.items():
                thresh = optimal_thresholds[model_name]
                eval_metrics = evaluate(labels_dict[partition_name], prob_scores, thresh)
                eval_metrics.update(model=model_name, partition=partition_name)
                metrics_results.append(eval_metrics)

                predictions_export = partitions[partition_name][[
                    "Order Id", "order_date", "partition", "Late_delivery_risk"
                ]].copy()
                predictions_export["model"] = model_name
                predictions_export["probability_1"] = prob_scores
                predictions_export["threshold"] = thresh
                predictions_export["prediction"] = (prob_scores >= thresh).astype(int)
                predictions_export.to_csv(
                    out_dir / f"predictions-{partition_name}-{model_name}.csv",
                    index=False,
                )

        dump_json(out_dir / "metrics.json", metrics_results)
        pd.DataFrame(metrics_results).to_csv(out_dir / "metrics.csv", index=False)
        dump_json(
            out_dir / "convergence.json",
            {
                "sklearn_iterations": lr_model.n_iter_.tolist(),
                "sklearn_max_iter": 1000,
                "spark_iterations": spark_model.summary.totalIterations,
                "spark_objective_history": spark_model.summary.objectiveHistory,
            },
        )
        logging.info("C: training dan evaluasi selesai; metrics.json tersimpan")

        graph_records = [
            (int(order_id), "MISSING" if pd.isna(cat_id) else str(int(cat_id)))
            for order_id, cat_id in zip(items["Order Id"], items["Category Id"])
        ]
        spark_graph_df = spark.createDataFrame(
            graph_records, ["order_id", "category_id"]
        )
        distinct_edges = (
            spark_graph_df.select("order_id", "category_id")
            .distinct()
            .orderBy("order_id", "category_id")
        )

        edges_pandas = distinct_edges.toPandas()
        edges_pandas["source"] = "order:" + edges_pandas["order_id"].astype(str)
        edges_pandas["target"] = "category:" + edges_pandas["category_id"].astype(str)

        assert not edges_pandas[["order_id", "category_id"]].duplicated().any()
        assert not (edges_pandas["source"] == edges_pandas["target"]).any()
        edges_pandas.to_csv(out_dir / "graph-edges.csv", index=False)

        graph_network = nx.Graph()
        graph_network.add_edges_from(
            edges_pandas[["source", "target"]].itertuples(index=False, name=None)
        )

        degree_records = [
            {"Category Id": c, "degree": graph_network.degree[f"category:{c}"]}
            for c in sorted(
                edges_pandas["category_id"].unique(),
                key=lambda x: (x == "MISSING", int(x) if x != "MISSING" else 0),
            )
        ]
        degree_df = pd.DataFrame(degree_records)
        degree_df["sort_id"] = degree_df["Category Id"].map(
            lambda x: int(x) if x != "MISSING" else 10**9
        )
        degree_df = degree_df.sort_values(
            ["degree", "sort_id"], ascending=[False, True]
        ).drop(columns="sort_id")
        degree_df.to_csv(out_dir / "graph-category-degree.csv", index=False)

        connected_components_list = sorted(
            nx.connected_components(graph_network), key=lambda c: (-len(c), min(c))
        )
        component_reports = []
        node_memberships = []

        for idx, component_set in enumerate(connected_components_list, 1):
            sub_edges = graph_network.subgraph(component_set).number_of_edges()
            component_reports.append({
                "component_id": idx,
                "nodes": len(component_set),
                "orders": sum(node.startswith("order:") for node in component_set),
                "categories": sum(
                    node.startswith("category:") for node in component_set
                ),
                "edges": sub_edges,
            })
            node_memberships.extend({
                "node": node,
                "component_id": idx
            } for node in sorted(component_set))

        pd.DataFrame(component_reports).to_csv(
            out_dir / "graph-components.csv", index=False
        )
        pd.DataFrame(node_memberships).to_csv(
            out_dir / "graph-component-membership.csv", index=False
        )

        top_categories = [
            f"category:{c}" for c in degree_df["Category Id"].iloc[:10]
        ]
        adjacent_orders = sorted(
            {node for cat in top_categories for node in graph_network.neighbors(cat)},
            key=lambda n: int(n.split(":")[1]),
        )[:200]

        subgraph_view = graph_network.subgraph(top_categories + adjacent_orders).copy()

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axis = plt.subplots(figsize=(12, 8))
        layout_positions = nx.spring_layout(subgraph_view, seed=42, iterations=50)

        nx.draw_networkx_edges(
            subgraph_view, layout_positions, alpha=0.2, width=0.5, ax=axis
        )
        nx.draw_networkx_nodes(
            subgraph_view,
            layout_positions,
            nodelist=adjacent_orders,
            node_size=12,
            node_color="#6aaed6",
            ax=axis,
        )
        nx.draw_networkx_nodes(
            subgraph_view,
            layout_positions,
            nodelist=top_categories,
            node_size=250,
            node_color="#f4a340",
            ax=axis,
        )
        nx.draw_networkx_labels(
            subgraph_view,
            layout_positions,
            labels={c: c for c in top_categories},
            font_size=8,
            ax=axis,
        )

        axis.set_title("Subset: 10 kategori degree tertinggi, maksimal 200 order")
        axis.axis("off")
        fig.tight_layout()
        fig.savefig(out_dir / "graph-subset.png", dpi=180)
        plt.close(fig)

        graph_summary = {
            "nodes": graph_network.number_of_nodes(),
            "orders": len(orders),
            "categories": len(degree_df),
            "edges": graph_network.number_of_edges(),
            "connected_components": len(connected_components_list),
            "self_loops": nx.number_of_selfloops(graph_network),
            "duplicate_edges": int(
                edges_pandas[["order_id", "category_id"]].duplicated().sum()
            ),
            "missing_category_items": audit_stats["missing_category_items"],
            "edge_construction": "Spark DataFrame distinct; full retained cohort",
            "metric_engine": "NetworkX; single-machine",
            "visualization": {
                "categories": len(top_categories),
                "orders": len(adjacent_orders),
                "nodes": subgraph_view.number_of_nodes(),
                "edges": subgraph_view.number_of_edges(),
                "selection": "top-10 degree descending, Category Id ascending ties; neighboring Order Id ascending first 200",
                "seed": 42,
                "iterations": 50,
            },
            "source_sha256": data_manifest[0]["sha256"],
        }

        assert graph_summary["nodes"] == graph_summary["orders"] + graph_summary["categories"]
        assert sum(degree_df.degree) == graph_summary["edges"]
        assert sum(item["nodes"] for item in component_reports) == graph_summary["nodes"]

        dump_json(out_dir / "graph-summary.json", graph_summary)
        spark.stop()

        dump_json(
            out_dir / "status.json",
            {
                "started_utc": start_time,
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "exit_status": 0,
                "training_evaluation_graph": "executed",
                "report": "separate deliverable stage",
            },
        )
        logging.info("D: graph selesai %s", graph_summary)

        return {
            "output": str(out_dir),
            "audit": audit_stats,
            "thresholds": optimal_thresholds,
            "metrics": metrics_results,
            "graph": graph_summary,
        }

    except Exception:
        (out_dir / "traceback.log").write_text(traceback.format_exc())
        dump_json(
            out_dir / "status.json",
            {
                "started_utc": start_time,
                "finished_utc": datetime.now(timezone.utc).isoformat(),
                "exit_status": 1,
            },
        )
        logging.exception("Eksekusi gagal")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="DataCo Big Data Analytics Pipeline Runner"
    )
    parser.add_argument("--root", required=True, help="Root path of dataset")
    parser.add_argument("--output", required=True, help="Output destination folder")
    cli_args = parser.parse_args()
    run(cli_args.root, cli_args.output)
