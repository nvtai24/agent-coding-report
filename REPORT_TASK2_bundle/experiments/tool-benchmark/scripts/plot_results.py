"""Export static report figures from summary.json and the raw trial metrics."""
import json
import os
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[1]
local_packages=Path('/tmp/coding-benchmark/plot-packages')
if local_packages.exists():sys.path.insert(0,str(local_packages))
os.environ.setdefault('MPLCONFIGDIR','/tmp/coding-benchmark/matplotlib-config')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

summary=json.loads((root/'results/summary.json').read_text())
trials=[json.loads(file.read_text()) for file in (root/'results').glob('*/metrics.json')]
tools=['opencode','pi','codex'];names=['OpenCode 2.2.7','Pi 1.5.0','Codex CLI 0.166.0-alpha.6'];tasks=['T1','T2','T3']
colors=['#2563eb','#059669','#ea580c']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','axes.titleweight':'bold'})
fig,axes=plt.subplots(2,1,figsize=(10.5,7.6),layout='constrained')
width=.22
for metric,axis,title,scale in [('seconds',axes[0],'Elapsed time per run (seconds)',1),('tokens',axes[1],'Processed tokens per run (thousands)',1000)]:
    for tool_index,tool in enumerate(tools):
        positions=[task_index+(tool_index-1)*width for task_index in range(3)]
        values=[summary['by_task'][task][tool][metric] for task in tasks]
        medians=[value['median']/scale for value in values]
        axis.bar(positions,medians,width=width*.9,color=colors[tool_index],alpha=.9,label=names[tool_index])
        axis.errorbar(positions,medians,yerr=[[m-value['min']/scale for m,value in zip(medians,values)],[value['max']/scale-m for m,value in zip(medians,values)]],fmt='none',ecolor='#334155',capsize=4,linewidth=1)
        for task_index,task in enumerate(tasks):
            rows=sorted([row for row in trials if row['tool']==tool and row['task']==task],key=lambda row:row['repeat'])
            data=[(row['elapsed_seconds'] if metric=='seconds' else row['usage']['total_tokens'])/scale for row in rows]
            offsets=[-.035,0,.035]
            axis.scatter([positions[task_index]+offset for offset in offsets[:len(data)]],data,s=18,color='white',edgecolors='#334155',linewidths=.7,zorder=4)
    axis.set_xticks([0,1,2],['T1 · Fix quantity validation','T2 · CSV import + CLI','T3 · Single-pass refactor'])
    axis.set_title(title,loc='left',pad=12)
    axis.set_ylim(bottom=0)
    axis.grid(axis='y',alpha=.18);axis.set_axisbelow(True)
axes[0].legend(loc='upper left',frameon=False,ncol=3,bbox_to_anchor=(0,1.21),fontsize=9)
fig.suptitle('Same model and tasks · gpt-6.1-sol / medium',x=.06,ha='left',fontsize=15,fontweight='bold')
fig.text(.06,-.025,'Bars = medians; dots = individual runs; whiskers = observed min–max. Three runs per tool and task.',fontsize=9,color='#475569')
for extension in ['png','svg']:fig.savefig(root/'charts'/f'time-and-tokens.{extension}',dpi=180,bbox_inches='tight',facecolor='white')
plt.close(fig)

fig,axis=plt.subplots(figsize=(9.6,4.9),layout='constrained')
parts=[('input_uncached','Uncached input','#2563eb'),('input_cached','Cached input','#93c5fd'),('visible_output','Visible output','#f97316'),('reasoning','Reasoning output','#fbbf24')]
bottom=[0.,0.,0.]
for key,label,color in parts:
    values=[]
    for tool in tools:
        value=summary['tools'][tool]
        values.append((value['output_total']-value['reasoning'] if key=='visible_output' else value[key])/1000)
    axis.bar(names,values,bottom=bottom,label=label,color=color,width=.55)
    bottom=[a+b for a,b in zip(bottom,values)]
for index,total in enumerate(bottom):axis.annotate(f'{total:,.1f}k',(index,total),xytext=(0,6),textcoords='offset points',ha='center',fontweight='bold')
axis.set_ylim(0,max(bottom)*1.2)
axis.set_ylabel('Processed tokens (thousands)')
axis.set_title('Token composition across nine runs per tool',loc='left',pad=18)
axis.grid(axis='y',alpha=.18);axis.set_axisbelow(True)
axis.legend(frameon=False,ncol=2,loc='upper left',fontsize=9)
for extension in ['png','svg']:fig.savefig(root/'charts'/f'token-composition.{extension}',dpi=180,bbox_inches='tight',facecolor='white')
plt.close(fig)
print('Exported two figures as PNG and SVG.')
