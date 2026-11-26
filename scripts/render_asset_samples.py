#!/usr/bin/env python3
"""Render five small MP4 sample stories through the production Remotion CLI."""
from __future__ import annotations
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'/'samples'; OUT.mkdir(parents=True,exist_ok=True)
recipes=[
 ('tech-product-launch','Tech product launch','16:9',['#08131F','#1C9BC2','#60E6D0','#F2FAFF'],'The next wave of work.','Ideas into motion.','01 / READY','icon-rocket'),
 ('social-quote-reel','Social quote reel','9:16',['#29162E','#9A5596','#F2A7C4','#FFF0F6'],'Make room to grow.','Small steps. Big change.','STAY CURIOUS','icon-sparkles'),
 ('data-stat-explainer','Data stat explainer','16:9',['#F4F8FF','#D7E5FF','#3567B2','#132A4D'],'Progress, made visible.','A clearer view of the numbers.','+38% THIS QUARTER','icon-chart-no-axes-column-increasing'),
 ('cinematic-product-reveal','Cinematic product reveal','16:9',['#1B1717','#724938','#D99162','#F7DBB9'],'Designed for the details.','A quieter kind of confidence.','NEW COLLECTION','icon-sparkles'),
 ('creator-community-cta','Creator community CTA','1:1',['#401E5B','#EC6FB2','#FDBD68','#FFF1C4'],'Thanks for being here.','The best part is what comes next.','10K COMMUNITY','icon-heart'),
]
def element(id,kind,text,y,color,size,asset=None,animation='rise'):
    row={'id':id,'kind':kind,'text':text,'x':50,'y':y,'width':82 if kind!='icon' else 18,'color':color,'font_size':size,'weight':750 if kind=='headline' else 500,'animation':animation,'delay':.1}
    if asset: row['asset_id']=asset
    return row
for slug,title,ratio,palette,headline,body,metric,icon in recipes:
    duration=1.5; width,height={'16:9':(1920,1080),'9:16':(1080,1920),'1:1':(1080,1080)}[ratio]
    scenes=[]
    for i,(head,caption,transition) in enumerate(((headline,body,'fade'),(metric,'Made to move with you.','wipe'))):
        color='#F9FAFC' if i==0 or sum(int(palette[0][j:j+2],16) for j in (1,3,5))<360 else palette[3]
        elements=[element(f'{slug}-{i}-label','label',title.upper(),23,palette[2],14,'','reveal'),element(f'{slug}-{i}-title','headline',head,43 if ratio!='9:16' else 39,color,64 if ratio=='16:9' else 56),element(f'{slug}-{i}-copy','body',caption,60 if ratio!='9:16' else 52,palette[3] if color=='#F9FAFC' else palette[0],24),element(f'{slug}-{i}-icon','icon','✦',77 if ratio!='9:16' else 69,palette[2],44,icon,'scale')]
        scenes.append({'id':f'{slug}-scene-{i+1}','title':f'{title} · beat {i+1}','duration':duration,'description':f'{title} composition sample.','narration':'','transition':transition,'background':palette[0],'background_asset':['background-grid-fine','background-dots-small','background-aurora-mist','background-radial-rays'][i],'elements':elements})
    spec={'title':title,'prompt':f'Asset library render sample: {title}','language':'en','aspect_ratio':ratio,'fps':24,'width':width,'height':height,'palette':palette,'scenes':scenes}
    spec_path=OUT/f'{slug}.json'; output=OUT/f'{slug}.mp4'; spec_path.write_text(json.dumps(spec,indent=2))
    env={**os.environ,'REMOTION_SCALE':'0.35'}
    subprocess.run(['node',str(ROOT/'renderer'/'render.mjs'),str(spec_path),str(output),'mp4'],cwd=ROOT,env=env,check=True)
    print(f'RENDERED {output.relative_to(ROOT)} ({output.stat().st_size:,} bytes)')
