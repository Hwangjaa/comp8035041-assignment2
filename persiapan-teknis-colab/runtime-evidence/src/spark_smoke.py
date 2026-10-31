import json, traceback
from pathlib import Path
from pyspark.sql import SparkSession
out=Path('/content/assignment_ii_prep'); s=None
try:
    s=(SparkSession.builder.master('local[2]').appName('AssignmentII-readonly-audit').config('spark.ui.enabled','false').config('spark.driver.memory','1g').config('spark.sql.shuffle.partitions','2').getOrCreate())
    s.sparkContext.setLogLevel('ERROR')
    df=s.read.option('header',True).option('encoding','ISO-8859-1').option('inferSchema',False).option('mode','FAILFAST').csv('/content/DataCoSupplyChainDataset.csv')
    n=df.count(); assert n==180519 and len(df.columns)==53
    # Order keys dibaca lewat Python worker.
    keys=df.select('Order Id').limit(10).rdd.map(lambda row: row[0]).collect()
    assert len(keys)==10 and all(k is not None for k in keys)
    j=s.sparkContext._jvm
    h=s.sparkContext._jsc.hadoopConfiguration()
    fs=j.org.apache.hadoop.fs.FileSystem.get(h)
    result={'spark_version':s.version,'master':s.sparkContext.master,'rows':n,'columns':len(df.columns),'python_worker_rows_verified':len(keys),'hadoop_library_version':j.org.apache.hadoop.util.VersionInfo.getVersion(),'fs_defaultFS':h.get('fs.defaultFS'),'filesystem_uri':str(fs.getUri()),'configuration':dict(s.sparkContext.getConf().getAll()),'status':'passed','hdfs_service_tested':False,'training_executed':False,'note':'Spark raw CSV count + Python workers only. file:/// is local filesystem, NOT HDFS service.'}
    (out/'spark-smoke.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
except Exception as e:
    (out/'spark-smoke.json').write_text(json.dumps({'status':'failed','error':repr(e),'traceback':traceback.format_exc()},indent=2)); raise
finally:
    if s is not None:s.stop()
