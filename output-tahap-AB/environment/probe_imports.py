import sys, platform, importlib, json, traceback
result = {'executable':sys.executable,'version':sys.version,'platform':platform.platform(),'modules':{},'classes':{},'metrics':{},'scope':'Import saja; tanpa instansiasi, fit, training, evaluasi data, atau benchmark.'}
for name in ['numpy','pandas','sklearn','scipy','networkx','pyspark']:
    try:
        mod=importlib.import_module(name)
        result['modules'][name]={'import':True,'version':getattr(mod,'__version__',None),'path':getattr(mod,'__file__',None)}
    except Exception as e:
        result['modules'][name]={'import':False,'error':repr(e)}
checks={'sklearn.linear_model':['LogisticRegression'],'sklearn.tree':['DecisionTreeClassifier'],'sklearn.ensemble':['RandomForestClassifier','GradientBoostingClassifier'],'pyspark.ml.classification':['LogisticRegression','DecisionTreeClassifier','RandomForestClassifier','GBTClassifier']}
for module,names in checks.items():
    for name in names:
        key=module+'.'+name
        try:
            obj=getattr(importlib.import_module(module),name)
            result['classes'][key]={'import':True,'module':obj.__module__}
        except Exception as e: result['classes'][key]={'import':False,'error':repr(e)}
checks={'sklearn.metrics':['accuracy_score','precision_score','recall_score','f1_score','roc_auc_score','average_precision_score','confusion_matrix','precision_recall_curve','roc_curve'],'pyspark.ml.evaluation':['BinaryClassificationEvaluator','MulticlassClassificationEvaluator']}
for module,names in checks.items():
    for name in names:
        key=module+'.'+name
        try:
            obj=getattr(importlib.import_module(module),name)
            record={'import':True}
            if module=='pyspark.ml.evaluation':
                record['documented_metric_names']=[line.strip() for line in (obj.__doc__ or '').splitlines() if any(x in line for x in ['areaUnder','f1','accuracy','weightedPrecision','weightedRecall','precisionByLabel','recallByLabel'])]
            result['metrics'][key]=record
        except Exception as e: result['metrics'][key]={'import':False,'error':repr(e)}
print(json.dumps(result,indent=2))
