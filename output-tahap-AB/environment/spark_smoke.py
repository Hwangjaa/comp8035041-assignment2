import json, os, tempfile
from pyspark.sql import SparkSession
spark=None
result={'scope':'Spark local[2], range/count sintetis saja, tanpa ML atau dataset','tempdir':tempfile.gettempdir()}
try:
    spark=(SparkSession.builder.appName('EnvironmentReadOnlyRangeSmoke').master('local[2]')
           .config('spark.ui.enabled','false').config('spark.driver.host','127.0.0.1')
           .config('spark.driver.bindAddress','127.0.0.1')
           .config('spark.local.dir',os.environ['SPARK_LOCAL_DIRS'])
           .config('spark.sql.warehouse.dir',os.environ['TMPDIR']+'/warehouse')
           .config('spark.hadoop.hadoop.tmp.dir',os.environ['TMPDIR']+'/hadoop')
           .config('spark.sql.catalogImplementation','in-memory').getOrCreate())
    result.update(version=spark.version,master=spark.sparkContext.master,count=spark.range(10).count())
    result['pass']=result['count']==10
finally:
    if spark is not None:
        spark.stop()
        result['session_stopped']=True
    print(json.dumps(result,indent=2))
