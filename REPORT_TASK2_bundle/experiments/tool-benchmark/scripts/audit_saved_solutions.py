"""Exploratory behavior check, separate from the frozen primary acceptance suite."""
import json
import tempfile
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
probe='''import json
import tempfile
from cartkit.csvio import load_orders
text="\\norder_id,sku,quantity,unit_price_cents\\nA,X,1,10\\n"
try:
    result=load_orders(text)
    print(json.dumps({"accepted":True,"result":result}))
except Exception as error:
    print(json.dumps({"accepted":False,"errorType":type(error).__name__,"message":str(error)}))
'''
rows=[]
for folder in sorted((root/'results').glob('*-T2-r*')):
    if not (folder/'metrics.json').exists():continue
    result=subprocess.run([sys.executable,'-c',probe],cwd=folder/'solution',capture_output=True,text=True,timeout=10)
    legacy={}
    with tempfile.TemporaryDirectory() as temporary:
        totals_file=Path(temporary)/'lines.json';totals_file.write_text(json.dumps([{'unit_price_cents':125,'quantity':2}]))
        summary_file=Path(temporary)/'orders.json';summary_file.write_text(json.dumps([{'customer':'A','status':'paid','total_cents':250}]))
        for command,file,expected in [
            ('totals',totals_file,{'subtotal_cents':250,'discount_cents':0,'shipping_cents':0,'total_cents':250}),
            ('summary',summary_file,{'paid_count':1,'paid_total_cents':250,'cancelled_count':0,'customers':{'A':250}}),
        ]:
            process=subprocess.run([sys.executable,'-m','cartkit.cli',command,str(file)],cwd=folder/'solution',capture_output=True,text=True,timeout=10)
            try:legacy[command]=process.returncode==0 and json.loads(process.stdout)==expected
            except json.JSONDecodeError:legacy[command]=False
    rows.append({'run_id':folder.name,'probe':'blank line before header','behavior':json.loads(result.stdout),'legacy_cli':legacy})
(root/'results/exploratory-audit.json').write_text(json.dumps({'scope':'Post-run exploratory probe; excluded from primary completion rates.','rows':rows},ensure_ascii=False,indent=2))
print(json.dumps(rows))
