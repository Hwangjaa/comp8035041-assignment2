import concurrent.futures, datetime, glob, hashlib, json, os, pathlib, platform, shlex, shutil, signal, subprocess, sys
ROOT=pathlib.Path('/Users/rafaelyudianto/Documents/COMP8035041-Assignment-II')
OUT=ROOT/'output-tahap-AB/environment'
RUNTIME=ROOT/'runtime'
SCRATCH=pathlib.Path('/Users/rafaelyudianto/.hermes/cache/scratch/comp8035041-environment')
SCRATCH.mkdir(parents=True,exist_ok=True)
BASE=os.environ.copy()
BASE.update(PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH))
records=[]
def run(label,cmd,env=None,timeout=60):
    env=env or BASE
    start=datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc=subprocess.Popen(cmd,cwd=OUT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    expired=False
    try: stdout,stderr=proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        expired=True
        os.killpg(proc.pid,signal.SIGTERM)
        try: stdout,stderr=proc.communicate(timeout=8)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL); stdout,stderr=proc.communicate()
    (OUT/(label+'.stdout.log')).write_bytes(stdout)
    (OUT/(label+'.stderr.log')).write_bytes(stderr)
    overrides={k:v for k,v in env.items() if BASE.get(k)!=v or k in ['TMPDIR','PYTHONDONTWRITEBYTECODE']}
    rec={'label':label,'argv':cmd,'cwd':str(OUT),'environment_overrides':overrides,'started_utc':start,'exit_code':proc.returncode,'timed_out':expired,'stdout_path':str(OUT/(label+'.stdout.log')),'stderr_path':str(OUT/(label+'.stderr.log')),'reproduce':'cd '+shlex.quote(str(OUT))+' && env '+ ' '.join(shlex.quote(k+'='+v) for k,v in overrides.items())+' '+shlex.join(cmd)}
    try: rec['result']=json.loads(stdout)
    except Exception: pass
    (OUT/(label+'.json')).write_text(json.dumps(rec,indent=2))
    records.append(rec)
    return rec
sources={}
for rel in ['env.sh','README.md','conf/spark/spark-defaults.conf','conf/hadoop/core-site.xml','conf/hadoop/hdfs-site.xml','conf/hadoop/hadoop-env.sh','logs/smoke-test.log','logs/start-hdfs.log','logs/stop-hdfs.log','logs/restart-hdfs.log']:
    p=RUNTIME/rel
    if p.is_file():
        raw=p.read_bytes()
        sources[str(p)]={'sha256':hashlib.sha256(raw).hexdigest(),'size_bytes':len(raw),'mtime_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'content':raw.decode(errors='replace')}
(OUT/'source-evidence.json').write_text(json.dumps(sources,indent=2))
run('system_state',['/bin/bash','-c','date -u; uname -a; sw_vers; /usr/sbin/sysctl -n hw.memsize hw.ncpu; df -h .; command -v python python3 python3.11 python3.12 python3.13 python3.14; /bin/ps -axo pid,comm | /usr/bin/grep -E "java|hdfs|spark|python" || true'])
interpreters=[]
for name in ['python','python3','python3.9','python3.10','python3.11','python3.12','python3.13','python3.14']:
    p=shutil.which(name)
    if p: interpreters.append(p)
interpreters += glob.glob('/Users/rafaelyudianto/.hermes/venv/bin/python')+glob.glob('/Users/rafaelyudianto/.hermes/installs/*/environments/*/venv/bin/python')
interpreters += glob.glob('/Users/rafaelyudianto/.hermes/installs/*/pm-runtime/generations/*/bin/python')
interpreters += glob.glob('/opt/homebrew/bin/python3')+glob.glob('/usr/local/bin/python3')
interpreters=list(dict.fromkeys(interpreters))
(OUT/'interpreters.json').write_text(json.dumps({'discovered':interpreters,'discovery':'PATH Python version aliases, ~/.hermes/venv, ~/.hermes/installs/*/environments/*/venv, Homebrew/local python3; not exhaustive disk scan'},indent=2))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(lambda pair:run('python_'+str(pair[0])+'_native',[pair[1],'-B',str(OUT/'probe_imports.py')],timeout=90),enumerate(interpreters)))
envrec=run('runtime_environment',['/bin/bash','-c','source "$1"; for key in JAVA_HOME HADOOP_HOME HADOOP_CONF_DIR HADOOP_IDENT_STRING SPARK_HOME SPARK_CONF_DIR SPARK_LOCAL_IP PATH; do printf "%s=%s\\0" "$key" "${!key}"; done','bash',str(RUNTIME/'env.sh')])
raw=(OUT/'runtime_environment.stdout.log').read_bytes()
runtime_env=BASE.copy()
for item in raw.split(b'\0'):
    if b'=' in item:
        k,v=item.split(b'=',1)
        key=k.decode()
        if key in ['JAVA_HOME','HADOOP_HOME','HADOOP_CONF_DIR','HADOOP_IDENT_STRING','SPARK_HOME','SPARK_CONF_DIR','SPARK_LOCAL_IP','PATH']:
            runtime_env[key]=v.decode()
# Never inherit runtime/tmp, log destinations, or daemon pid destinations.
runtime_env.update(TMPDIR=str(SCRATCH),TMP=str(SCRATCH),TEMP=str(SCRATCH),SPARK_LOCAL_DIRS=str(SCRATCH/'spark'),HADOOP_LOG_DIR=str(SCRATCH/'hadoop-logs'),HADOOP_PID_DIR=str(SCRATCH/'pids'),HADOOP_OPTS='-Djava.io.tmpdir='+str(SCRATCH),SPARK_SUBMIT_OPTS='-Djava.io.tmpdir='+str(SCRATCH))
sparkhome=pathlib.Path(runtime_env['SPARK_HOME'])
pythonpaths=[str(sparkhome/'python')]+glob.glob(str(sparkhome/'python/lib/py4j-*.zip'))
bundled=runtime_env.copy(); bundled['PYTHONPATH']=os.pathsep.join(pythonpaths)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    list(pool.map(lambda pair:run('python_'+str(pair[0])+'_spark_bundled',[pair[1],'-B',str(OUT/'probe_imports.py')],env=bundled,timeout=90),enumerate(interpreters)))
run('java_version',[runtime_env['JAVA_HOME']+'/bin/java','-version'],runtime_env)
hdfs=runtime_env['HADOOP_HOME']+'/bin/hdfs'
run('hadoop_version',[runtime_env['HADOOP_HOME']+'/bin/hadoop','version'],runtime_env)
run('hdfs_ls',[hdfs,'dfs','-Dipc.client.connect.max.retries=0','-Dipc.client.connect.timeout=4000','-ls','/'],runtime_env,20)
run('hdfs_report',[hdfs,'dfsadmin','-Dipc.client.connect.max.retries=0','-Dipc.client.connect.timeout=4000','-report'],runtime_env,20)
# Use an interpreter whose bundled PySpark import really passed.
valid=[r for r in records if r['label'].endswith('_spark_bundled') and r.get('result',{}).get('modules',{}).get('pyspark',{}).get('import')]
if valid:
    chosen=valid[0]['argv'][0]
    smokeenv=bundled.copy(); smokeenv.update(PYSPARK_PYTHON=chosen,PYSPARK_DRIVER_PYTHON=chosen)
    run('spark_range_smoke',[chosen,'-B',str(OUT/'spark_smoke.py')],smokeenv,120)
(OUT/'command-index.json').write_text(json.dumps(sorted(records,key=lambda r:r['label']),indent=2))
print(json.dumps({'output_directory':str(OUT),'commands':len(records),'interpreters':interpreters,'results':[{'label':r['label'],'exit_code':r['exit_code'],'timed_out':r['timed_out'],'result':r.get('result')} for r in sorted(records,key=lambda r:r['label'])]},indent=2))
