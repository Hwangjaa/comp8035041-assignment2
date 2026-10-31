import os,sys,json,traceback
from pathlib import Path
import nbformat
from nbclient import NotebookClient
from ipykernel.kernelspec import install
install(kernel_name='dataco-assignment-ii',user=True,display_name='DataCo Assignment II')
root=Path(__file__).resolve().parents[1]
bundle=Path(__file__).resolve().parent
runtime=root/'runtime'
os.environ.update(JAVA_HOME=str(runtime/'amazon-corretto-17.jdk/Contents/Home'),SPARK_LOCAL_IP='127.0.0.1',PYSPARK_PYTHON=sys.executable,PYSPARK_DRIVER_PYTHON=sys.executable,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2')
os.environ.pop('SPARK_HOME',None)
nb=nbformat.v4.new_notebook()
nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
nb.cells=[nbformat.v4.new_markdown_cell('COMP8035041 Assignment II — eksekusi lokal keputusan mahasiswa. Bukan notebook Colab dan bukan HDFS. Interpretasi serta kesimpulan wajib ditulis mahasiswa.'),nbformat.v4.new_code_cell("from pathlib import Path\nimport sys, json\nroot=Path("+repr(str(root))+")\nsys.path.insert(0,str(root/'eksekusi-final-lokal/src'))\nfrom pipeline import run\nresult=run(root,root/'eksekusi-final-lokal/run-actual')\nprint(json.dumps(result,indent=2,ensure_ascii=False))")]
path=bundle/'Assignment-II-DataCo-executed-local.ipynb'
nbformat.write(nb,path)
try:
    NotebookClient(nb,timeout=1800,kernel_name='dataco-assignment-ii',resources={'metadata':{'path':str(root)}}).execute()
    print('NOTEBOOK_EXECUTION_EXIT_STATUS=0')
except Exception:
    (bundle/'notebook-error.log').write_text(traceback.format_exc());raise
finally:
    nbformat.write(nb,path)
