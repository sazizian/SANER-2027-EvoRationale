#!/usr/bin/env python3
"""Plot verified all-scope development metrics; never run a model or scorer."""
import json
from pathlib import Path

def main():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path(__file__).resolve().parent.parent
    summary=json.loads((root/'data/results/summary.json').read_text(encoding='utf-8'))
    rows=[row for row in summary['rows'] if row['scope']=='all' and row['f1'] is not None]
    labels=[row['run_label'].replace('v4.','4.').replace('cached scope recheck','Scope') for row in rows]
    colors=['#2563eb','#d97706','#15803d']
    figure,axis=plt.subplots(figsize=(8.0,4.7),layout='constrained')
    width=.24
    for offset,(metric,color) in enumerate(zip(['precision','recall','f1'],colors)):
        axis.bar([i+(offset-1)*width for i in range(len(rows))],
                 [r[metric] for r in rows],width,label=metric.upper() if metric=='f1' else metric.title(),
                 color=color,zorder=3)
    axis.set_xticks(range(len(rows)),labels)
    axis.set_ylim(0,1.06)
    axis.set_ylabel('Score')
    axis.set_xlabel('Development run')
    axis.set_title('Inspected single-case pilot: exact-triple scores',loc='left',fontweight='bold')
    axis.grid(axis='y',alpha=.18,zorder=0)
    axis.spines[['top','right']].set_visible(False)
    axis.legend(ncol=3,frameon=False,loc='upper right')
    figure.supxlabel('30 hunks / 19 positive triples; development comparison, differing models and compute.\nPrimary Effects hosted result pending and excluded.',fontsize=9)
    output=root/'figures';output.mkdir(exist_ok=True)
    figure.savefig(output/'development_pilot_metrics.png',dpi=300)
    figure.savefig(output/'development_pilot_metrics.pdf')
    plt.close(figure)

if __name__=='__main__':main()
