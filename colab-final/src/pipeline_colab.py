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
SINGLE = SINGLE_VALUED_COLUMNS

KNOWN_DELIVERY_STATUSES = {
    "Advance shipping",
    "Late delivery",
    "Shipping canceled",
    "Shipping on time",
}


def dump_json(file_path, data):
    """Serialize data to JSON with indentation and UTF-8 encoding."""
    target_path = Path(file_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str, allow_nan=False),
        encoding="utf-8",
    )


dump = dump_json


def compute_sha256(file_path):
    """Compute SHA-256 checksum of a file in 1MB chunks."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


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

    if raw_df["Delivery Status"].isna().any():
        raise ValueError("Delivery Status missing: pipeline berhenti")

    unknown_status = sorted(
        set(raw_df["Delivery Status"].astype(str)) - KNOWN_DELIVERY_STATUSES
    )
    if unknown_status:
        raise ValueError(f"Delivery Status tidak dikenal: {unknown_status}")

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
