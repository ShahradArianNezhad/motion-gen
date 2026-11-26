#!/usr/bin/env python3
"""Build the original, metadata-rich SVG/JSON library and curate Lucide SVGs."""
from __future__ import annotations
import json, math, re, shutil, subprocess, sys, tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'
PACK=Path('/tmp/assetpacks/lucide-static-1.81.0.tgz')
if not PACK.exists():
    PACK.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['npm','pack','lucide-static@1.81.0','--pack-destination',str(PACK.parent)],check=True,stdout=subprocess.DEVNULL)
if len(list((ASSETS/'fonts').glob('*-latin.woff2')))<45:
    subprocess.run([sys.executable,str(ROOT/'scripts'/'fetch_font_assets.py')],check=True)
for d in ('icons','shapes','backgrounds','textures','illustrations','mockups','lottie','fonts','catalogs'):
    (ASSETS/d).mkdir(parents=True,exist_ok=True)
manifest=[]
def add(id,name,category,subcategory,tags,mood,style,description,path,fmt='svg',ratio='1:1',recolor=True,license='CC0-1.0',source='Original procedural artwork by Motion Studio',duration=None):
    manifest.append(dict(id=id,name=name,category=category,subcategory=subcategory,tags=tags,mood=mood,style=style,description=description,path=path,format=fmt,dimensions={'aspectRatio':ratio},duration=duration,recolorable=recolor,props={'color':'currentColor','size':'viewBox'},license=license,source=source))
def esc(s): return s.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def svg(body,view='0 0 100 100',extra=''):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" {extra}>{body}</svg>\n'
# 500+ canonical Lucide icons, selected evenly over the library and prioritized by real product themes.
with tarfile.open(PACK,'r:gz') as tar:
    names=sorted(m.name for m in tar.getmembers() if m.name.startswith('package/icons/') and m.name.endswith('.svg'))
    terms=['arrow','chevron','menu','close','check','search','home','user','users','mail','message','phone','camera','image','video','music','play','pause','volume','cart','credit-card','banknote','chart','wallet','dollar','receipt','heart','activity','stethoscope','pill','hospital','sun','cloud','rain','snow','wind','thermometer','globe','wifi','cpu','database','code','terminal','server','shield','lock','key','bell','calendar','clock','map','location','plane','car','truck','package','box','store','tag','gift','star','sparkles','share','download','upload','settings','layers','type','pen','file','folder','trash','edit','copy','link','external','command','keyboard','mouse','monitor','laptop','tablet','smartphone','watch','printer','rocket','zap','lightbulb','leaf','flame','coffee','book','graduation','briefcase','building','factory','chart','bar-chart','pie-chart','trending','target','award','trophy','megaphone','mic','headphones','radio','rss','cloud','sun','moon','smile','thumbs','hand','accessibility','baby','dog','cat','bird','fish','flower','tree','mountain','waves','circle','square','triangle','hexagon','infinity','move','rotate','maximize','minimize','filter','sliders','sparkle','wand','qr-code','scan','fingerprint','bug','git','github','instagram','facebook','linkedin','youtube','x','twitch','discord','whatsapp','tiktok','figma','spotify','apple','google','microsoft','amazon','stripe','paypal','slack','notion','openai']
    priority=[n for n in names if any(t in Path(n).stem for t in terms)]
    selected=[]
    for n in priority+names:
        if n not in selected: selected.append(n)
        if len(selected)>=1200: break
    subcats={
      'arrows':'navigation', 'chevrons':'navigation','communication':'communication','commerce':'commerce','tech':'technology','finance':'finance','health':'health','social':'social','weather':'weather','media':'media','interface':'interface','brands':'brands','files':'productivity'
    }
    for i,member in enumerate(selected):
        filename=Path(member).stem
        data=tar.extractfile(member).read().decode('utf-8')
        # Keep library vectors CSS-recolorable and normalized; sanitize title metadata.
        data=re.sub(r'<svg[^>]*', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"', data, count=1)
        out=ASSETS/'icons'/f'{filename}.svg'; out.write_text(data)
        low=filename.lower()
        sub='brands' if low in {'github','instagram','facebook','linkedin','youtube','twitch','discord','whatsapp','tiktok','figma','spotify','apple','google','microsoft','amazon','stripe','paypal','slack','notion','openai','x'} else next((v for k,v in subcats.items() if k in low), 'interface')
        add('icon-'+filename,filename.replace('-',' ').title(),'icons',sub,[*filename.split('-'),sub,'lucide'],['neutral','professional'],['outline','minimal'],f'Lucide outline icon for {filename.replace("-"," ")}. Use as a scalable UI or motion graphic accent.',f'assets/icons/{filename}.svg',license='ISC',source='Lucide (lucide-static) 1.81.0 · https://github.com/lucide-icons/lucide · ISC')
# Brand logos from the Simple Icons CC0 artwork collection (respect trademark guidelines).
SIMPLE_PACK=Path('/tmp/assetpacks/simple-icons-15.21.0.tgz')
if not SIMPLE_PACK.exists():
    SIMPLE_PACK.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['npm','pack','simple-icons@15.21.0','--pack-destination',str(SIMPLE_PACK.parent)],check=True,stdout=subprocess.DEVNULL)
brand_names='airbnb amd android appstore bandcamp behance bitcoin blender bluetooth bootstrap brave canva cashapp circle cplusplus d3 dotnet discord docker dribbble dropbox ebay elastic ethereum facebook figma firefox firebase flathub flutter github gitlab gmail go google googlechrome googlecloud googledrive graphql html5 huawei instagram intel intercom javascript jira jquery jsdelivr kickstarter kubernetes lastpass linux mailchimp mastercard medium meta mongodb mysql notion npm nvidia obsidian openai opera orcid paypal pinterest pixiv playstation proton protonmail python react reddit redis rust safari salesforce samsung shopify signal slack snapchat soundcloud spotify squarespace stackoverflow steam stripe telegram threads tiktok trello twitch ubuntu unity unrealengine vimeo visa vite vk webflow whatsapp wikipedia wordpress xiaomi ycombinator youtube zoom'.split()
with tarfile.open(SIMPLE_PACK,'r:gz') as simple:
    available={member.name.rsplit('/',1)[-1][:-4]:member for member in simple.getmembers() if member.name.startswith('package/icons/') and member.name.endswith('.svg')}
    for slug in brand_names:
        member=available.get(slug)
        if not member or f'icon-{slug}' in {'icon-'+Path(n).stem for n in selected}: continue
        data=simple.extractfile(member).read().decode('utf-8')
        data=re.sub(r'<svg\b','<svg fill="currentColor"',data,count=1)
        out=ASSETS/'icons'/'brands'/f'{slug}.svg';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(data)
        add('brand-'+slug,slug.replace('-',' ').title()+' logo','icons','brands',[slug,'brand','logo','simple-icons'],['professional','brand'],['logo','vector'],f'Official Simple Icons {slug} brand logo vector; verify trademark usage against brand guidelines.',f'assets/icons/brands/{slug}.svg',license='CC0-1.0',source='Simple Icons 15.21.0 · https://github.com/simple-icons/simple-icons · CC0-1.0; brand trademarks remain with their owners')
# Shape primitives, distinct geometric families
shape_defs=[('circle','circle'),('oval','ellipse'),('square','rect'),('rounded-square','rounded'),('diamond','diamond'),('triangle','triangle'),('right-triangle','right-triangle'),('pentagon','pentagon'),('hexagon','hexagon'),('octagon','octagon'),('parallelogram','parallelogram'),('trapezoid','trapezoid'),('cross','cross'),('plus','plus'),('ring','ring'),('donut','donut'),('arc','arc'),('semicircle','semicircle'),('quarter-circle','quarter'),('crescent','crescent'),('star-4-point','star4'),('star-5-point','star5'),('star-8-point','star8'),('burst-12','burst'),('burst-16','burst16'),('sunburst','sunburst'),('speech-bubble','bubble'),('thought-bubble','thought'),('callout-cloud','cloud'),('arrow-right','arrow'),('arrow-left','arrowleft'),('arrow-up','arrowup'),('curved-arrow','curvearrow'),('chevron','chevron'),('bracket-left','bracket'),('bracket-right','bracket'),('brace','brace'),('underline-swoosh','swoosh'),('squiggle','squiggle'),('wave-line','wave'),('zigzag','zigzag'),('dashed-divider','dash'),('dotted-divider','dots'),('ribbon','ribbon'),('badge','badge'),('ticket','ticket'),('label-tag','tag'),('blob-soft','blob'),('blob-liquid','blob'),('blob-organic','blob'),('spiral','spiral'),('concentric-rings','rings'),('target-rings','target'),('grid-cross','grid'),('sparkle','sparkle'),('asterisk','asterisk'),('handdrawn-circle','roughcircle'),('handdrawn-arrow','rougharrow'),('handdrawn-underline','roughline'),('handdrawn-star','roughstar')]
def shape_body(kind,seed):
    if kind=='circle':return '<circle cx="50" cy="50" r="35"/>'
    if kind=='ellipse':return '<ellipse cx="50" cy="50" rx="42" ry="27"/>'
    if kind in ('rect','rounded'):return '<rect x="16" y="16" width="68" height="68" rx="'+('17' if kind=='rounded' else '1')+'"/>'
    if kind=='diamond':return '<path d="M50 8 92 50 50 92 8 50Z"/>'
    if kind=='triangle':return '<path d="m50 10 43 76H7Z"/>'
    if kind=='right-triangle':return '<path d="M15 85V15h70Z"/>'
    if kind in ('pentagon','hexagon','octagon','star4','star5','star8','burst','burst16','sunburst','badge','roughstar'):
        count={'pentagon':5,'hexagon':6,'octagon':8,'star4':8,'star5':10,'star8':16,'burst':24,'burst16':32,'sunburst':32,'badge':24,'roughstar':10}[kind]
        pts=[]
        for j in range(count):
            angle=-math.pi/2+j*2*math.pi/count; r=38 if j%2==0 else (21 if kind.startswith('star') or kind in ('burst','burst16','sunburst','roughstar') else 38)
            pts.append(f'{50+r*math.cos(angle):.1f},{50+r*math.sin(angle):.1f}')
        return '<polygon points="'+' '.join(pts)+'"/>'
    if kind=='parallelogram':return '<path d="m30 18 60 0-20 64H10Z"/>'
    if kind=='trapezoid':return '<path d="m30 18 40 0 22 64H8Z"/>'
    if kind=='cross':return '<path d="M40 10h20v30h30v20H60v30H40V60H10V40h30Z"/>'
    if kind=='plus':return '<path d="M50 15v70M15 50h70"/>'
    if kind=='ring':return '<circle cx="50" cy="50" r="36"/>'
    if kind=='donut':return '<circle cx="50" cy="50" r="38"/><circle cx="50" cy="50" r="22"/>'
    if kind=='concentric-rings':return '<circle cx="50" cy="50" r="39"/><circle cx="50" cy="50" r="27"/><circle cx="50" cy="50" r="14"/>'
    if kind=='target':return '<circle cx="50" cy="50" r="37"/><circle cx="50" cy="50" r="22"/><path d="M50 6v26m0 36v26M6 50h26m36 0h26"/>'
    if kind=='arc':return '<path d="M15 70a38 38 0 1 1 70 0"/>'
    if kind=='semicircle':return '<path d="M10 50a40 40 0 0 1 80 0Z"/>'
    if kind=='quarter':return '<path d="M10 90V10a80 80 0 0 1 80 80Z"/>'
    if kind=='crescent':return '<path d="M66 12a40 40 0 1 0 22 69A37 37 0 0 1 66 12Z"/>'
    if kind=='bubble':return '<path d="M15 25q0-10 12-10h46q12 0 12 12v24q0 12-12 12H48L28 79V63q-13-2-13-14Z"/>'
    if kind=='thought':return '<path d="M29 67q-17-4-13-21 2-9 12-11Q23 17 41 15q11-2 17 7 17-10 25 8 15 7 7 21-4 9-15 10H44Z"/><circle cx="26" cy="78" r="5"/><circle cx="17" cy="90" r="3"/>'
    if kind=='cloud':return '<path d="M22 70q-14-3-14-17 0-13 14-17 2-22 24-22 14 0 21 12 21-7 27 12 15 3 15 18 0 14-16 14Z"/>'
    if kind in ('arrow','arrowleft','arrowup','curvearrow','rougharrow'):return {'arrow':'<path d="M12 50h72m-26-26 26 26-26 26"/>','arrowleft':'<path d="M88 50H16m26-26-26 26 26 26"/>','arrowup':'<path d="M50 88V16m-26 26 26-26 26 26"/>','curvearrow':'<path d="M16 74Q18 28 67 30L76 16m0 0 12 19m-12-19-17 9"/>','rougharrow':'<path d="M12 57q32-8 70-4m-27-24 29 24-30 22"/>'}[kind]
    if kind=='chevron':return '<path d="m20 35 30 30 30-30"/>'
    if kind=='bracket':return '<path d="'+('M64 16H28v68h36' if seed%2==0 else 'M36 16h36v68H36')+'"/>'
    if kind=='brace':return '<path d="M67 12H53q-8 0-8 10v15q0 12-13 13 13 1 13 13v15q0 10 8 10h14"/>'
    if kind in ('swoosh','roughline','squiggle','wave','zigzag'):
        d={'swoosh':'M12 70Q44 76 88 28','roughline':'M10 63q19-14 34-4t46-8','squiggle':'M10 50q10-30 20 0t20 0 20 0 20 0','wave':'M8 52q10-23 21 0t21 0 21 0 21 0','zigzag':'M10 70 28 30l18 40 18-40 18 40'}[kind]
        return f'<path d="{d}"/>'
    if kind in ('dash','dots'):return '<path d="M10 50h80" stroke-dasharray="'+('1 8' if kind=='dots' else '9 7')+'"/>'
    if kind=='ribbon':return '<path d="M15 22h70v38H15zM28 60l-8 30 25-13 5 13 9-30m26 0 8 30-25-13"/>'
    if kind=='ticket':return '<path d="M12 22h76v18a10 10 0 0 0 0 20v18H12V60a10 10 0 0 0 0-20Z" stroke-dasharray="5 5"/>'
    if kind=='tag':return '<path d="M12 18h43l34 32-34 32H12Z"/><circle cx="32" cy="50" r="4"/>'
    if kind=='blob':
        blob_paths=['M21 31q-6-18 12-19 17-14 30 2 24-4 20 19 17 19-3 30 1 23-22 19-18 15-27-2-22 3-23-18-20-12 1-31-5-17 12-20Z','M15 48Q14 21 39 17q19-4 26 11 29-11 30 17 3 17-13 22 2 24-20 25-20 2-24-14-27-1-23-18Z','M26 19q24-10 33 9 25-8 30 14 6 20-12 27 4 24-19 22-18-1-20-18-22-1-24-23-2-18 12-31Z']
        return '<path d="'+blob_paths[seed%len(blob_paths)]+'"/>'
    if kind=='spiral':return '<path d="M50 50c0-9 14-9 14 0 0 19-29 19-29 0 0-31 47-31 47 0 0 44-65 44-65 0"/>'
    if kind=='grid':return '<path d="M20 10v80M50 10v80M80 10v80M10 20h80M10 50h80M10 80h80"/>'
    if kind=='sparkle':return '<path d="M50 8 58 42 92 50 58 58 50 92 42 58 8 50 42 42Z"/><path d="m78 10 3 10 9 3-9 3-3 10-3-10-9-3 9-3Z"/>'
    if kind=='asterisk':return '<path d="M50 15v70M20 32l60 36M20 68l60-36"/>'
    return '<circle cx="50" cy="50" r="35"/>'
for i,(name,kind) in enumerate(shape_defs):
    p=ASSETS/'shapes'/f'{name}.svg';p.write_text(svg(shape_body(kind,i)))
    add('shape-'+name,name.replace('-',' ').title(),'shapes','primitives',[name.replace('-',' '),'vector','graphic'],['playful','versatile'],['geometric','outline'],f'Recolorable vector {name.replace("-"," ")} primitive for accents, labels, masks, or dividers.',f'assets/shapes/{name}.svg')
# 45 procedural repeatable background tiles
bg_names=['aurora-ribbon','aurora-mist','mesh-violet','mesh-ocean','mesh-sunset','mesh-mint','grid-fine','grid-bold','grid-perspective','dots-small','dots-large','dots-diagonal','checker-soft','checker-bold','topographic-lines','contour-waves','wave-horizontal','wave-diagonal','wave-radial','concentric-rings','sunburst-lines','isometric-cubes','isometric-diamonds','hexagon-grid','triangular-grid','crosshatch','pinstripe','diagonal-stripes','vertical-stripes','radial-rays','starfield-sparse','starfield-dense','bokeh-circles','particle-field','pixel-grid','paper-fiber','linen-weave','art-deco-fan','memphis-dashes','memphis-squiggles','soft-gradient-dark','soft-gradient-light','orbital-lines','scan-grid','noise-dots']
for i,name in enumerate(bg_names):
    color=['#7C5CFC','#1C9BC2','#F37C6B','#25B98C'][i%4]
    pattern={
      'grid':'<path d="M0 0H100M0 20H100M0 40H100M0 60H100M0 80H100M0 0V100M20 0V100M40 0V100M60 0V100M80 0V100" stroke="currentColor" opacity=".16"/>',
      'dots':'<pattern id="p" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="currentColor"/></pattern><rect width="100" height="100" fill="url(#p)"/>',
      'wave':'<path d="M-10 35Q15 8 40 35t50 0 50 0M-10 55q25-27 50 0t50 0 50 0M-10 75q25-27 50 0t50 0 50 0" stroke="currentColor" opacity=".35"/>',
      'ring':'<circle cx="50" cy="50" r="15"/><circle cx="50" cy="50" r="30"/><circle cx="50" cy="50" r="45"/>',
      'stripe':'<path d="M-10 100 100-10M10 110 110 10M30 110 110 30M50 110 110 50" stroke="currentColor" opacity=".18"/>',
      'hexagon':'<path d="m25 8 18 0 9 16-9 16H25l-9-16Zm34 0h18l9 16-9 16H59l-9-16Zm-17 32h18l9 16-9 16H42l-9-16Zm-34 0h18l9 16-9 16H8l-9-16Z" opacity=".25"/>',
      'mesh':'<defs><radialGradient id="g"><stop stop-color="currentColor" stop-opacity=".6"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient></defs><ellipse cx="25" cy="25" rx="50" ry="40" fill="url(#g)"/><ellipse cx="72" cy="62" rx="55" ry="46" fill="url(#g)"/>',
      'aurora':'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="currentColor" stop-opacity=".8"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></linearGradient></defs><path d="M-10 72Q20 2 49 40t62-25v80H-10Z" fill="url(#g)" opacity=".65"/>'}
    key=next((k for k in ('grid','dots','wave','ring','stripe','hexagon','mesh','aurora') if k in name), 'dots')
    body=pattern[key]
    overrides={
      'grid-perspective':'<path d="M50 15 0 100M50 15 25 100M50 15 50 100M50 15 75 100M50 15 100 100M0 85h100M8 65h84M18 45h64" opacity=".25"/>',
      'dots-small':'<defs><pattern id="p" width="6" height="6" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r=".7" fill="currentColor"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>',
      'dots-large':'<defs><pattern id="p" width="18" height="18" patternUnits="userSpaceOnUse"><circle cx="4" cy="4" r="2.1" fill="currentColor"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>',
      'dots-diagonal':'<defs><pattern id="p" width="14" height="14" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><circle cx="3" cy="3" r="1.4" fill="currentColor"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>',
      'checker-soft':'<defs><pattern id="p" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M0 0h8v8H0Zm8 8h8v8H8Z" fill="currentColor" opacity=".1"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>',
      'checker-bold':'<defs><pattern id="p" width="16" height="16" patternUnits="userSpaceOnUse"><path d="M0 0h8v8H0Zm8 8h8v8H8Z" fill="currentColor" opacity=".28"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>',
      'topographic-lines':'<path d="M-10 18Q18-4 41 18t55 0M-10 28Q18 6 41 28t55 0M-10 38Q18 16 41 38t55 0M-10 48Q18 26 41 48t55 0M-10 58Q18 36 41 58t55 0M-10 68Q18 46 41 68t55 0M-10 78Q18 56 41 78t55 0M-10 88Q18 66 41 88t55 0" opacity=".28"/>',
      'contour-waves':'<path d="M-8 30Q15 8 34 30t38 0 40 0M-8 37Q15 15 34 37t38 0 40 0M-8 62Q15 40 34 62t38 0 40 0M-8 69Q15 47 34 69t38 0 40 0" opacity=".35"/>',
      'wave-diagonal':'<g transform="rotate(-28 50 50)"><path d="M-10 24Q15 3 40 24t50 0 50 0M-10 50q25-21 50 0t50 0 50 0M-10 76q25-21 50 0t50 0 50 0" opacity=".35"/></g>',
      'wave-radial':'<circle cx="50" cy="50" r="10"/><circle cx="50" cy="50" r="22"/><circle cx="50" cy="50" r="34"/><circle cx="50" cy="50" r="46"/>',
      'sunburst-lines':'<path d="M50 50 50 0M50 50 75 0M50 50 100 10M50 50 100 50M50 50 100 90M50 50 75 100M50 50 50 100M50 50 25 100M50 50 0 90M50 50 0 50M50 50 0 10M50 50 25 0" opacity=".32"/>',
      'starfield-sparse':'<g fill="currentColor"><circle cx="12" cy="18" r="1"/><circle cx="75" cy="14" r="1.2"/><circle cx="48" cy="61" r="1"/><circle cx="89" cy="72" r="1.4"/><circle cx="28" cy="88" r=".8"/><path d="M56 28v8m-4-4h8M18 48v5m-2.5-2.5h5"/></g>',
      'starfield-dense':'<g fill="currentColor"><circle cx="12" cy="18" r="1"/><circle cx="75" cy="14" r="1.2"/><circle cx="48" cy="61" r="1"/><circle cx="89" cy="72" r="1.4"/><circle cx="28" cy="88" r=".8"/><circle cx="37" cy="12" r=".8"/><circle cx="61" cy="78" r=".9"/><circle cx="5" cy="54" r=".8"/><circle cx="96" cy="31" r="1"/><circle cx="20" cy="34" r=".7"/><circle cx="70" cy="48" r=".7"/><circle cx="44" cy="92" r=".8"/></g>',
      'bokeh-circles':'<circle cx="18" cy="24" r="13" opacity=".13"/><circle cx="75" cy="20" r="8" opacity=".16"/><circle cx="63" cy="70" r="19" opacity=".11"/><circle cx="21" cy="78" r="8" opacity=".16"/>',
      'particle-field':'<g fill="currentColor"><circle cx="15" cy="20" r="1"/><circle cx="36" cy="70" r="1.5"/><circle cx="57" cy="34" r="1"/><circle cx="82" cy="56" r="1.4"/><circle cx="72" cy="86" r=".8"/><circle cx="25" cy="44" r=".7"/><circle cx="91" cy="15" r=".9"/><circle cx="48" cy="91" r=".7"/></g>',
      'pixel-grid':'<defs><pattern id="p" width="8" height="8" patternUnits="userSpaceOnUse"><path d="M0 0h2v2H0Z" fill="currentColor" opacity=".4"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>',
      'crosshatch':'<path d="M-10 10 10-10m0 30L30 0m0 30L50 10m0 30L70 20m0 30L90 30m0 30L110 50M-10 50l20 20m0-30 20 20m0-30 20 20m0-30 20 20m0-30 20 20m0-30 20 20" opacity=".2"/>',
      'pinstripe':'<path d="M10 0v100M16 0v100M40 0v100M46 0v100M70 0v100M76 0v100" opacity=".18"/>',
      'art-deco-fan':'<path d="M50 94V10M50 94 18 18M50 94 82 18M50 94 5 48M50 94 95 48M20 42h60M13 58h74M7 76h86" opacity=".3"/>',
      'memphis-dashes':'<path d="M18 22l14 4m-7-10-2 14M69 24l12-8m-6 14 1-12M23 75l18-8m-8 15 3-14M70 76l17 5m-7-12 1 14" stroke-width="3"/>',
      'memphis-squiggles':'<path d="M10 24q8-16 16 0t16 0m28 0q8-16 16 0t16 0M10 72q8-16 16 0t16 0m28 0q8-16 16 0t16 0" stroke-width="2.5"/>',
      'soft-gradient-dark':'<defs><radialGradient id="g"><stop stop-color="currentColor" stop-opacity=".38"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient></defs><ellipse cx="50" cy="42" rx="56" ry="52" fill="url(#g)"/>',
      'soft-gradient-light':'<defs><radialGradient id="g"><stop stop-color="currentColor" stop-opacity=".22"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient></defs><ellipse cx="50" cy="45" rx="58" ry="54" fill="url(#g)"/>',
      'orbital-lines':'<ellipse cx="50" cy="50" rx="43" ry="17" transform="rotate(-30 50 50)"/><ellipse cx="50" cy="50" rx="43" ry="17" transform="rotate(30 50 50)"/><circle cx="50" cy="50" r="5" fill="currentColor"/>',
      'noise-dots':'<defs><pattern id="p" width="4" height="4" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".45" fill="currentColor" opacity=".22"/><circle cx="3" cy="2" r=".35" fill="currentColor" opacity=".12"/></pattern></defs><rect width="100" height="100" fill="url(#p)"/>'
    }
    if name in overrides: body=overrides[name]
    if name=='aurora-mist': body='<defs><radialGradient id="g"><stop stop-color="currentColor" stop-opacity=".42"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient></defs><ellipse cx="20" cy="30" rx="65" ry="35" fill="url(#g)"/><ellipse cx="75" cy="72" rx="60" ry="42" fill="url(#g)"/>'
    if name=='aurora-ribbon': body='<path d="M-12 62Q17 4 43 38t62-22v19Q65 75 42 57T-12 82Z" fill="currentColor" opacity=".22"/><path d="M-10 74Q24 20 48 52t61-13" opacity=".4"/>'
    p=ASSETS/'backgrounds'/f'{name}.svg';p.write_text(svg(body,'0 0 100 100',f'style="color:{color}"'))
    add('background-'+name,name.replace('-',' ').title(),'backgrounds',key,[name.replace('-',' '),key,'seamless','background'],['calm','modern'],['procedural','vector'],f'Seamless {name.replace("-"," ")} background tile; recolor with CSS color and layer beneath typography.',f'assets/backgrounds/{name}.svg',ratio='16:9')
# 32 transparent overlays (simple SVG filter / texture layers)
texture_names=['film-grain-fine','film-grain-heavy','paper-speckle','paper-crease','canvas-weave','linen-texture','dust-sparse','dust-dense','light-leak-amber','light-leak-violet','light-leak-cyan','halftone-small','halftone-large','halftone-diagonal','scanlines-fine','scanlines-bold','vignette-soft','vignette-dramatic','glow-orb','lens-flare-horizontal','lens-flare-star','chromatic-fringe','soft-blur-bloom','scratch-film','bokeh-overlay','sparkle-dust','noise-mono','noise-color','grain-warm','grain-cool','radial-glow','edge-burn']
for i,name in enumerate(texture_names):
    if 'vignette' in name: body='<defs><radialGradient id="v"><stop offset=".48" stop-color="black" stop-opacity="0"/><stop offset="1" stop-color="black" stop-opacity=".75"/></radialGradient></defs><rect width="100" height="100" fill="url(#v)"/>'
    elif 'scanline' in name: body='<path d="M0 2h100M0 7h100M0 12h100M0 17h100M0 22h100M0 27h100M0 32h100M0 37h100M0 42h100M0 47h100M0 52h100M0 57h100M0 62h100M0 67h100M0 72h100M0 77h100M0 82h100M0 87h100M0 92h100M0 97h100" opacity=".12"/>'
    elif 'halftone' in name or 'dust' in name or 'grain' in name or 'noise' in name or 'speckle' in name: body='<defs><pattern id="p" width="9" height="9" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1" fill="currentColor" opacity=".34"/><circle cx="7" cy="6" r=".7" fill="currentColor" opacity=".2"/></pattern></defs><rect width="100" height="100" fill="url(#p)" opacity=".45"/>'
    elif 'flare' in name or 'glow' in name or 'leak' in name or 'bloom' in name: body='<defs><radialGradient id="g"><stop stop-color="currentColor" stop-opacity=".5"/><stop offset="1" stop-color="currentColor" stop-opacity="0"/></radialGradient></defs><ellipse cx="50" cy="50" rx="48" ry="22" fill="url(#g)"/><path d="M8 50h84M50 8v84" opacity=".24"/>'
    else: body='<path d="M0 20Q25 10 50 20t50 0M0 52q25-10 50 0t50 0M0 84q25-10 50 0t50 0" opacity=".24"/>'
    p=ASSETS/'textures'/f'{name}.svg';p.write_text(svg(body,'0 0 100 100','style="color:#ffffff"'))
    add('texture-'+name,name.replace('-',' ').title(),'textures','overlays',[name.replace('-',' '),'overlay','texture'],['cinematic','analog'],['texture','overlay'],f'Transparent, low-opacity {name.replace("-"," ")} overlay. Keep subtle above imagery or gradients.',f'assets/textures/{name}.svg')
# 100 intentionally varied, simple bespoke vector stickers; semantic catalog names, varied motif geometry.
objects=['rocket','planet','satellite','comet','moon','sun','rainbow','cloud','lightning','flower','cactus','leaf','mushroom','mountain','wave','fish','butterfly','bee','ladybug','bird','cat','dog','rabbit','turtle','whale','octopus','dinosaur','ghost','robot','alien','astronaut','heart','sparkle','trophy','medal','crown','gift','balloon','confetti','party-hat','cake','coffee-cup','tea-cup','pizza','strawberry','lemon','avocado','cherry','ice-cream','donut','book','pencil','paintbrush','palette','camera','headphones','microphone','vinyl-record','film-camera','gamepad','keyboard','mouse','phone','laptop','watch','envelope','chat-bubble','notification','cursor','hand-wave','thumbs-up','megaphone','lightbulb','hourglass','calendar','checkmark','shield','lock','key','wallet','credit-card','coin','chart-up','bar-chart','target','compass','map-pin','globe','paper-plane','scooter','bicycle','car','train','airplane','house','storefront','plant-pot','lamp','chair','sparkling-star']
emoji_symbols=['🚀','🪐','🛰️','☄️','🌙','☀️','🌈','☁️','⚡','🌼','🌵','🍃','🍄','🏔️','🌊','🐟','🦋','🐝','🐞','🐦','🐱','🐶','🐰','🐢','🐳','🐙','🦕','👻','🤖','👽','🧑\u200d🚀','❤️','✨','🏆','🏅','👑','🎁','🎈','🎊','🎉','🎂','☕','🫖','🍕','🍓','🍋','🥑','🍒','🍦','🍩','📖','✏️','🖌️','🎨','📷','🎧','🎤','💿','🎥','🎮','⌨️','🖱️','📱','💻','⌚','✉️','💬','🔔','👆','👋','👍','📣','💡','⌛','📅','✅','🛡️','🔒','🔑','👛','💳','🪙','📈','📊','🎯','🧭','📍','🌎','📨','🛴','🚲','🚗','🚆','✈️','🏠','🏪','🪴','🪔','🪑','🌟']
TWEMOJI_PACK=Path('/tmp/assetpacks/twemoji-svg-15.0.0.tgz')
if not TWEMOJI_PACK.exists():
    TWEMOJI_PACK.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['npm','pack','@twemoji/svg@15.0.0','--pack-destination',str(TWEMOJI_PACK.parent)],check=True,stdout=subprocess.DEVNULL)
with tarfile.open(TWEMOJI_PACK,'r:gz') as twemoji:
    for name,character in zip(objects,emoji_symbols):
        code='-'.join(f'{ord(char):x}' for char in character if ord(char)!=0xfe0f)
        member=f'package/{code}.svg'; source_file=twemoji.extractfile(member)
        if source_file is None: raise RuntimeError(f'Twemoji vector missing for {name}: {code}')
        p=ASSETS/'illustrations'/f'{name}.svg';p.write_bytes(source_file.read())
        add('illustration-'+name,name.replace('-',' ').title(),'illustrations','stickers',[name.replace('-',' '),'sticker','illustration','emoji'],['playful','friendly'],['vector','emoji'],f'Full-color {name.replace("-"," ")} emoji sticker in SVG format.',f'assets/illustrations/{name}.svg',recolor=False,license='CC-BY-4.0',source='Twemoji SVG 15.0.0 · https://github.com/twitter/twemoji · CC BY 4.0; attribution to Twemoji contributors'); manifest[-1]['props']={'variant':'full-color','unicode':code}
# 20 composition-ready device/UI frames
mockups=['phone-minimal','phone-social-feed','phone-chat','phone-video-player','phone-dashboard','phone-notification','phone-map','phone-commerce','laptop-product-page','laptop-dashboard','laptop-code-editor','laptop-video-call','browser-window-light','browser-window-dark','tablet-presentation','tablet-dashboard','smartwatch-face','notification-toast','chat-message-card','cursor-pointer']
for i,name in enumerate(mockups):
    if name.startswith('phone') or name=='smartwatch-face': body='<rect x="25" y="7" width="50" height="86" rx="10" fill="#101522" stroke="currentColor" stroke-width="3"/><rect x="30" y="17" width="40" height="65" rx="3" fill="#F8FAFC" stroke="currentColor"/><circle cx="50" cy="87" r="2" fill="currentColor"/><rect x="40" y="11" width="20" height="2" rx="1" fill="currentColor"/>'
    elif name.startswith('laptop') or name.startswith('tablet'): body='<rect x="13" y="14" width="74" height="55" rx="5" fill="#101522" stroke="currentColor" stroke-width="3"/><rect x="18" y="20" width="64" height="43" fill="#F8FAFC"/><path d="M7 73h86l-7 10H14Z" fill="#CBD5E1" stroke="currentColor" stroke-width="2"/>'
    elif name.startswith('browser'): body='<rect x="8" y="15" width="84" height="67" rx="6" fill="#F8FAFC" stroke="currentColor" stroke-width="3"/><path d="M9 29h82" stroke="currentColor"/><circle cx="18" cy="22" r="2" fill="#F07191"/><circle cx="26" cy="22" r="2" fill="#F5A35B"/><circle cx="34" cy="22" r="2" fill="#28B8A0"/>'
    elif name.startswith('notification'): body='<rect x="12" y="30" width="76" height="40" rx="8" fill="#fff" stroke="currentColor" stroke-width="2"/><circle cx="25" cy="50" r="8" fill="#7C5CFC"/><path d="M40 44h35M40 53h26" stroke="#94A3B8" stroke-width="3"/>'
    elif name.startswith('chat'): body='<path d="M14 20h70v47H43L26 82V67h-12Z" rx="8" fill="#fff" stroke="currentColor" stroke-width="3"/><path d="M27 35h42M27 45h32M27 55h25" stroke="#94A3B8" stroke-width="3"/>'
    else: body='<path d="M25 10 77 55 54 58 43 86Z" fill="#fff" stroke="currentColor" stroke-width="4"/>'
    p=ASSETS/'mockups'/f'{name}.svg';p.write_text(svg(body))
    add('mockup-'+name,name.replace('-',' ').title(),'mockups','devices' if name.startswith(('phone','laptop','tablet','browser','smartwatch')) else 'ui',[name.replace('-',' '),'mockup','device','ui'],['modern','product'],['wireframe','vector'],f'Clean vector {name.replace("-"," ")} frame. Place your own UI, copy, and colors in the safe area.',f'assets/mockups/{name}.svg',ratio='9:16' if name.startswith('phone') else '16:9')
# 50 original, self-authored Lottie micro-animations with several distinct shape/motion families.
for i in range(50):
    family=['loader','checkmark','confetti','sparkle','reaction','success','error','heart','like','notification','progress','celebration','ring','pulse','bounce'][i%15]
    name=family+('-'+str(i//15+1) if i>=15 else '')
    rgb=[round((0.42+(i%4)*.11)*1000)/1000,round((0.34+((i+1)%4)*.12)*1000)/1000,.92,1]
    fill={'ty':'fl','c':{'a':0,'k':rgb},'o':{'a':0,'k':100},'r':1,'nm':'accent fill'}
    ellipse={'ty':'el','p':{'a':0,'k':[50,50]},'s':{'a':0,'k':[28+((i*7)%20),28+((i*11)%20)]},'nm':'orb'}
    if family=='checkmark':
        geometry={'ty':'sh','ks':{'a':0,'k':{'i':[[0,0],[0,0],[0,0]],'o':[[0,0],[0,0],[0,0]],'v':[[24,52],[43,70],[78,30]],'c':False}},'nm':'check path'}
        shapes=[geometry,{'ty':'st','c':{'a':0,'k':rgb},'o':{'a':0,'k':100},'w':{'a':0,'k':7},'lc':2,'lj':2,'nm':'check stroke'}]
    elif family=='heart':
        geometry={'ty':'sh','ks':{'a':0,'k':{'i':[[0,0],[-8,8],[-8,0],[0,-10],[8,0],[8,8]],'o':[[0,0],[8,-8],[8,0],[0,10],[-8,0],[-8,-8]],'v':[[50,82],[17,50],[22,25],[42,26],[50,40],[58,26]],'c':True}},'nm':'heart path'}
        shapes=[geometry,fill]
    elif family=='sparkle':
        geometry={'ty':'sr','sy':1,'pt':{'a':0,'k':4},'p':{'a':0,'k':[50,50]},'r':{'a':0,'k':0},'or':{'a':0,'k':38},'os':{'a':0,'k':0},'ir':{'a':0,'k':10},'is':{'a':0,'k':0},'nm':'sparkle star'}
        shapes=[geometry,fill]
    elif family=='notification':
        geometry={'ty':'rc','p':{'a':0,'k':[50,50]},'s':{'a':0,'k':[66,42]},'r':{'a':0,'k':10},'nm':'toast'}
        shapes=[geometry,fill]
    elif family=='confetti' or family=='celebration':
        shapes=[]
        for j in range(5):
            particle={'ty':'el','p':{'a':0,'k':[20+(j*17)%65,20+(j*23)%62]},'s':{'a':0,'k':[7+(j%3)*3,9+(j%2)*4]},'nm':f'confetti {j+1}'}
            shapes.extend([particle,{'ty':'fl','c':{'a':0,'k':[rgb[1],rgb[2],rgb[0],1]},'o':{'a':0,'k':100},'r':1,'nm':f'color {j+1}'}])
    elif family=='loader':
        shapes=[ellipse,{'ty':'st','c':{'a':0,'k':rgb},'o':{'a':0,'k':100},'w':{'a':0,'k':7},'lc':2,'lj':2,'d':[{'n':'d','nm':'dash','v':{'a':0,'k':48}},{'n':'g','nm':'gap','v':{'a':0,'k':115}}],'nm':'loader stroke'}]
    else:
        shapes=[ellipse,fill]
    if family in ('loader','ring'):
        rotation={'a':1,'k':[{'t':0,'s':[0],'e':[360 if i%2 else -360],'i':{'x':[.3],'y':[1]},'o':{'x':[.7],'y':[0]}},{'t':60,'s':[360 if i%2 else -360]}]}
    elif family=='error':
        rotation={'a':1,'k':[{'t':0,'s':[-8]},{'t':7,'s':[8]},{'t':14,'s':[-5]},{'t':21,'s':[5]},{'t':30,'s':[0]},{'t':60,'s':[0]}]}
    else:
        rotation={'a':1,'k':[{'t':0,'s':[0],'e':[12 if family in ('celebration','confetti') else 0],'i':{'x':[.35],'y':[1]},'o':{'x':[.65],'y':[0]}},{'t':60,'s':[12 if family in ('celebration','confetti') else 0]}]}
    if family in ('checkmark','success','like','heart','sparkle','reaction','bounce','pulse','ring'):
        scale={'a':1,'k':[{'t':0,'s':[20,20,100],'e':[100,100,100],'i':{'x':[.25],'y':[.1]},'o':{'x':[.65],'y':[1]}},{'t':14,'s':[100,100,100]},{'t':38,'s':[92,92,100]},{'t':48,'s':[100,100,100]},{'t':60,'s':[100,100,100]}]}
    elif family=='progress':
        scale={'a':1,'k':[{'t':0,'s':[10,100,100],'e':[100,100,100],'i':{'x':[.25],'y':[.1]},'o':{'x':[.7],'y':[1]}},{'t':60,'s':[100,100,100]}]}
    else:
        scale={'a':0,'k':[100,100,100]}
    if family in ('confetti','celebration'):
        position={'a':1,'k':[{'t':0,'s':[50,85,0],'e':[50,38,0],'i':{'x':[.3],'y':[.1]},'o':{'x':[.7],'y':[1]}},{'t':60,'s':[50,38,0]}]}
    elif family=='notification':
        position={'a':1,'k':[{'t':0,'s':[125,50,0],'e':[50,50,0],'i':{'x':[.25],'y':[.1]},'o':{'x':[.7],'y':[1]}},{'t':16,'s':[50,50,0]},{'t':60,'s':[50,50,0]}]}
    else:
        position={'a':0,'k':[50,50,0]}
    opacity={'a':1,'k':[{'t':0,'s':[0 if family in ('success','checkmark','confetti','notification') else 100],'e':[100],'i':{'x':[.3],'y':[.1]},'o':{'x':[.7],'y':[1]}},{'t':16,'s':[100]},{'t':60,'s':[100]}]}
    layer={'ddd':0,'ind':1,'ty':4,'nm':name,'sr':1,'ks':{'o':opacity,'r':rotation,'p':position,'a':{'a':0,'k':[0,0,0]},'s':scale},'ao':0,'shapes':shapes,'ip':0,'op':60,'st':0,'bm':0}
    lottie={'v':'5.7.4','fr':30,'ip':0,'op':60,'w':100,'h':100,'nm':name,'ddd':0,'assets':[],'layers':[layer],'markers':[]}
    p=ASSETS/'lottie'/f'{name}.json';p.write_text(json.dumps(lottie,separators=(',',':'))+'\n')
    add('lottie-'+name,name.replace('-',' ').title(),'lottie','micro-animations',[name.replace('-',' '),'loop','motion','lottie'],['playful','positive'],['minimal','vector'],f'Original 2-second {family.replace("-"," ")} vector micro-animation; render with a Lottie-compatible player or rebuild as SVG.',f'assets/lottie/{name}.json','lottie-json',ratio='1:1',license='CC0-1.0',duration=2)
    manifest[-1]['props']={'loop':True,'frameRate':30,'frames':60,'canvas':[100,100]}
# Curated catalog resources: searchable metadata, recommendations, and presets.
font_families=['DM Sans','Manrope','Vazirmatn','Inter','Roboto','Open Sans','Lato','Montserrat','Poppins','Plus Jakarta Sans','Outfit','Space Grotesk','Sora','Urbanist','Work Sans','Nunito Sans','Source Sans 3','Archivo','IBM Plex Sans','Roboto Condensed','Oswald','Barlow Condensed','Bebas Neue','Anton','Playfair Display','DM Serif Display','Fraunces','Lora','Libre Baskerville','Cormorant Garamond','Source Serif 4','Merriweather','Roboto Mono','IBM Plex Mono','Space Mono','JetBrains Mono','Fira Code','Caveat','Pacifico','Dancing Script','Caveat Brush','Nunito','Quicksand','Comfortaa','Fredoka']
font_roles=['clean sans','bold sans','clean sans','clean sans','clean sans','clean sans','clean sans','bold sans','rounded','clean sans','display','display','display','rounded','clean sans','rounded','clean sans','bold sans','clean sans','condensed','condensed','condensed','condensed','condensed','serif display','serif display','serif display','serif','serif','serif','serif','serif','mono','mono','mono','mono','mono','handwriting','script','script','handwriting','rounded','rounded','rounded','rounded']
font_sources={item['slug']:item for item in json.loads((ASSETS/'fonts'/'font-sources.json').read_text())}
font_catalog=[]
for family,role in zip(font_families,font_roles):
    slug=family.lower().replace(' ','-'); source=font_sources[slug]
    font_catalog.append({'family':family,'role':role,'weights':source['weights'],'license':'OFL-1.1','source':source['source'],'file':source['file'],'licenseFile':source['licenseFile'],'variable':source['variable'],'availability':'Bundled Latin WOFF2; variable weights 100–900.' if source['variable'] else 'Bundled Latin WOFF2; regular weight 400.'})
(ASSETS/'fonts'/'font-catalog.json').write_text(json.dumps(font_catalog,indent=2,ensure_ascii=False)+'\n')
(ASSETS/'fonts'/'font-faces.css').write_text('\n'.join(f"@font-face{{font-family:'{f['family']}';src:url('/asset-files/fonts/{Path(f['file']).name}') format('woff2');font-weight:{'100 900' if f['variable'] else '400'};font-style:normal;font-display:swap;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}" for f in font_catalog)+'\n')
(ROOT/'src'/'font-faces.css').write_text('\n'.join(f"@font-face{{font-family:'{f['family']}';src:url('../assets/fonts/{Path(f['file']).name}') format('woff2');font-weight:{'100 900' if f['variable'] else '400'};font-style:normal;font-display:swap;unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}}" for f in font_catalog)+'\n')
for f in font_catalog: add('font-'+f['family'].lower().replace(' ','-'),f['family'],'typography','font-families',[f['family'].lower(),f['role'],'font','type'],['versatile'],[f['role']],f"{f['role'].title()} family; bundled Latin WOFF2, recommended weights: {', '.join(map(str,f['weights']))}.",f['file'],'woff2',recolor=False,license='OFL-1.1',source=f['source']+' · SIL Open Font License 1.1'); manifest[-1]['props']={'family':f['family'],'weights':f['weights']}
pairings=[('DM Sans','DM Serif Display','Modern product + editorial accent'),('Manrope','Fraunces','Polished product + expressive editorial'),('Inter','Playfair Display','Clean interface + high-contrast titles'),('Space Grotesk','Space Mono','Technology + precise data'),('Outfit','DM Serif Display','Friendly launch + refined quote'),('Plus Jakarta Sans','Lora','Warm SaaS + readable long copy'),('Roboto Condensed','Roboto','Dense information + neutral body'),('Oswald','Inter','Punchy title + clean supporting text'),('Sora','IBM Plex Mono','Futuristic title + technical labels'),('Montserrat','Merriweather','Campaign display + literary detail'),('Archivo','Source Serif 4','Editorial hierarchy'),('Nunito Sans','Fraunces','Approachable brand + premium accent'),('Bebas Neue','DM Sans','Sports / event typography'),('Quicksand','Lato','Rounded social content'),('Vazirmatn','DM Sans','Persian-first RTL + Latin UI')]
palettes=[('midnight-violet',['#0B1020','#19142E','#7C5CFC','#B7A6FF','#F8FAFC'],'dark luxury'),('ocean-signal',['#071A2D','#168AAD','#41EAD4','#EAF8FF'],'corporate'),('citrus-pop',['#18220B','#A3D938','#F5E85C','#FFF9DD'],'playful'),('terracotta-studio',['#281A18','#B45E4A','#EDAD83','#FAE8D4'],'warm'),('soft-lavender',['#F7F4FF','#D9CCFF','#9274DB','#29223D'],'pastel'),('carbon-cobalt',['#10151E','#273B5A','#3978D4','#B9D9FF'],'technology'),('rosewater',['#2C1924','#BC5977','#F0A7B7','#FFE7EA'],'romantic'),('forest-moss',['#10221A','#286B4C','#91BD72','#E8F1D7'],'nature'),('copper-night',['#1B1717','#724938','#D99162','#F7DBB9'],'dark luxury'),('signal-red',['#1A1013','#D83A4B','#F89B63','#FFF2E9'],'bold'),('skyline',['#12243A','#4079B5','#8DD5E8','#F4FBFF'],'calm'),('candy-shop',['#401E5B','#EC6FB2','#FDBD68','#FFF1C4'],'playful'),('monochrome-paper',['#F5F2EB','#D2CEC3','#464641','#171816'],'editorial'),('mint-condition',['#0D2B27','#2B9C83','#7FE0B5','#E2FFF4'],'fresh'),('electric-lime',['#11180C','#638D20','#B9EE36','#EEFFC2'],'neon'),('sunset-hour',['#301A36','#934C70','#F48968','#FFD18B'],'cinematic'),('blueprint',['#F4F8FF','#D7E5FF','#3567B2','#132A4D'],'corporate'),('peach-fuzz',['#FFF7F0','#F4C5AA','#D78170','#523942'],'warm'),('ultraviolet',['#120D24','#4F2E93','#A87BFF','#E3CEFF'],'neon'),('gold-standard',['#1D1B15','#6B5934','#C9A959','#F4E4B6'],'premium'),('arctic-glass',['#0B1821','#1D677B','#72D1D1','#E5FFFF'],'technology'),('berry-soda',['#2B1231','#802C72','#E75B9B','#FFC0D8'],'playful'),('sage-paper',['#F2F4EB','#BCC9A9','#617454','#27352B'],'nature'),('mono-terminal',['#08120C','#193E28','#43D17C','#D5FFD7'],'technology'),('coral-reef',['#10282C','#167C83','#53C7B7','#FF987A'],'fresh'),('ink-and-ivory',['#F5F1E8','#D3C9B9','#292A2A','#090A0C'],'editorial'),('neon-tokyo',['#080D1A','#7D3CFF','#F93DCE','#72F3FF'],'neon'),('desert-modern',['#33241C','#99775B','#D4AF85','#F5E6D0'],'earthy'),('plum-cream',['#29192B','#69445D','#C89DBB','#F5E8EF'],'premium'),('blue-hour',['#10182B','#364C83','#819EE8','#E5ECFF'],'cinematic'),('lemonade',['#FDF8E9','#F2DE74','#D79339','#40391D'],'playful'),('evergreen',['#13271E','#244E3B','#6C9B6B','#D8E2CC'],'nature'),('punch-card',['#211C23','#F25F5C','#F5B841','#F7F3E8'],'retro'),('glacier',['#EFFAFF','#C8E9F1','#559CB0','#193E51'],'calm'),('black-cherry',['#1A1016','#451B31','#92385D','#E7A9BC'],'dark luxury'),('lavender-lime',['#F6F1FF','#A48CD8','#A5C94B','#283121'],'playful'),('rose-gold',['#21191B','#75505A','#D69B91','#F4D8C8'],'premium'),('cobalt-pop',['#0D1833','#254AC7','#FFCC47','#F6F8FF'],'bold'),('coffee-and-cream',['#241914','#604333','#B78763','#F4E5D3'],'warm'),('digital-mint',['#0C1918','#1A5145','#20D6A2','#D1FFF0'],'technology'),('soft-sky',['#F1F7FF','#BDD7F4','#739CC6','#243A52'],'pastel'),('orange-cream',['#30190F','#D76530','#F3A457','#FFE5C1'],'warm'),('royal-indigo',['#16152C','#383477','#7D78D2','#D3D0FF'],'premium'),('berry-lime',['#271B2B','#8B426F','#C4DB4D','#F6F0DA'],'playful'),('storm-cloud',['#14181F','#353D4A','#8592A2','#E1E7EF'],'corporate'),('fuchsia-flare',['#1A1020','#852A82','#EF54CA','#FFD2F4'],'neon'),('olive-editorial',['#24251A','#696A3D','#A8A879','#EFEBD8'],'earthy'),('crimson-ink',['#1F1218','#742B3E','#C15058','#F5E5D7'],'bold'),('sea-glass',['#F0FAF8','#A6DAD0','#4B968F','#164C4A'],'calm'),('mono-luxe',['#111111','#44423F','#B0AAA0','#F2EFE9'],'dark luxury'),('pop-art',['#191323','#F25353','#F8D948','#4AC9C0'],'playful'),('orchid-night',['#191024','#59377A','#BA78D2','#F2D7FC'],'cinematic'),('copper-sage',['#26221B','#9E704D','#9EAD83','#F1E5CF'],'earthy'),('glow-cyan',['#08151D','#14536A','#34DDF0','#E0FCFF'],'neon'),('soft-coral',['#FFF6F1','#F4C3B4','#E98376','#533A3E'],'pastel'),('deep-teal',['#0B2022','#124E50','#28A6A0','#C7F1E9'],'corporate'),('studio-neutral',['#FAF8F4','#E7E1D7','#A29A8E','#252525'],'editorial'),('festival',['#26143F','#794BC1','#FA5C99','#FFC857'],'playful'),('minimal-ice',['#FFFFFF','#E8EDF2','#74869A','#233344'],'minimal')]
def relative_luminance(color):
    channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    linear=[value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4 for value in channels]
    return .2126*linear[0]+.7152*linear[1]+.0722*linear[2]
def contrast_ratio(a,b):
    high,low=sorted((relative_luminance(a),relative_luminance(b)),reverse=True)
    return (high+.05)/(low+.05)
palette_list=[]
for name,colors,mood in palettes:
    pair_ratio=contrast_ratio(colors[0],colors[-1])
    palette_list.append({'name':name,'colors':colors,'mood':mood,'lightSuitable':sum(int(c[1:3],16)+int(c[3:5],16)+int(c[5:],16) for c in colors[:1])/3>145,'darkSuitable':sum(int(c[1:3],16)+int(c[3:5],16)+int(c[5:],16) for c in colors[:1])/3<145,'contrastPair':{'background':colors[0],'text':colors[-1],'ratio':round(pair_ratio,2),'wcagAA':pair_ratio>=4.5,'largeTextAA':pair_ratio>=3,'note':'Use this pair for normal text only when wcagAA is true; verify overlay opacity and font weight in final composition.'}})
(ASSETS/'catalogs'/'palettes.json').write_text(json.dumps(palette_list,indent=2)+'\n')
gradients=[]
for name,cols,mood in palettes:
    gradients.append({'name':name+'-gradient','colors':[cols[1],cols[-2],cols[-1]],'css':f'linear-gradient(135deg, {cols[1]} 0%, {cols[-2]} 58%, {cols[-1]} 100%)','mood':mood,'lightSuitable':sum(int(c[1:3],16)+int(c[3:5],16)+int(c[5:],16) for c in cols[0:1])/3>145,'darkSuitable':sum(int(c[1:3],16)+int(c[3:5],16)+int(c[5:],16) for c in cols[0:1])/3<145})
for n,(name,cols,mood) in enumerate(palettes):
    gradients.append({'name':name+'-radial','colors':[cols[1],cols[-2],cols[0]],'css':f'radial-gradient(ellipse at 25% 20%, {cols[-2]} 0%, {cols[1]} 42%, {cols[0]} 100%)','mood':mood,'lightSuitable':False,'darkSuitable':True})
(ASSETS/'catalogs'/'gradients.json').write_text(json.dumps(gradients,indent=2)+'\n')
for item in palette_list:
    add('palette-'+item['name'],item['name'].replace('-',' ').title(),'color','palettes',[item['name'],'color palette',item['mood']],[item['mood']],['palette'],f"{item['mood'].title()} palette. Suggested text/background contrast is {item['contrastPair']['ratio']}:1; WCAG AA {'passes' if item['contrastPair']['wcagAA'] else 'requires checking'}.",'assets/catalogs/palettes.json','color-palette',recolor=False)
    manifest[-1]['props']={'colors':item['colors'],'contrastPair':item['contrastPair']}
for item in gradients:
    add('gradient-'+item['name'],item['name'].replace('-',' ').title(),'color','gradients',[item['name'],'gradient',item['mood']],[item['mood']],['gradient'],f"Three-stop {item['mood']} gradient, usable as a background fill.",'assets/catalogs/gradients.json','gradient-preset',recolor=False)
    manifest[-1]['props']={'colors':item['colors'],'css':item['css']}
# Motion catalogs: discoverable descriptions, values, and advice; some catalog items are compositions, not files.
text_names=['typewriter','letter-stagger','word-stagger','line-stagger','blur-in','slide-mask-up','slide-mask-left','scale-pop','glitch-in','wave-text','scramble-reveal','highlight-sweep','counter-roll','gradient-shimmer','tracking-reveal','split-character','elastic-pop','soft-fade','rise-and-settle','flip-in','rotate-type','bounce-in','underline-draw','wipe-reveal','focus-pull','color-wash','kinetic-stack','drop-in','spring-word','shimmer-sweep','outline-to-fill','pixel-dissolve']
trans_names=['fade','crossfade','wipe-left','wipe-right','wipe-up','wipe-down','slide-left','slide-right','slide-up','slide-down','push-left','push-right','zoom-in','zoom-out','whip-pan-left','whip-pan-right','glitch-cut','circle-reveal','iris-close','shape-mask','split-open','split-close','flip-horizontal','flip-vertical','liquid-morph','blur-dissolve','light-leak','diagonal-wipe','match-cut','radial-burst']
eases=[('linear','Constant speed; UI indicators and process data.'),('smooth','Even acceleration and deceleration; default content movement.'),('snappy','Fast response with a short settle; UI and punchy titles.'),('bouncy','Overshoot then settle; playful stickers and reactions.'),('cinematic','Slow ease-in and long graceful settle; brand films.'),('elastic','Overshoot with spring-back; expressive emphasis only.'),('ease-in','Accelerate toward the end; exits and outgoing wipes.'),('ease-out','Fast start, soft landing; entrances.'),('ease-in-out','Balanced speed; transitions and position changes.'),('anticipate','Small backward wind-up before forward motion.'),('overshoot','Go slightly beyond target then settle.'),('spring-soft','Low stiffness and high damping; gentle material feel.'),('spring-medium','Balanced physical spring; general-purpose UI.'),('spring-stiff','High stiffness; crisp buttons and counters.'),('spring-bouncy','Low damping spring; playful reactions.'),('exponential','Strong acceleration; dramatic scale or camera move.'),('sine','Subtle smooth oscillation; ambient loops.'),('circ-out','Decisive entrance with smooth finish.'),('back-out','Confident overshoot; badges and callouts.'),('quart-out','Fast but controlled; titles and charts.')]
particles=['confetti-burst','sparkle-drift','radial-burst','soft-bokeh','falling-snow','rising-bubbles','floating-geometric','speed-lines','dust-motes','firefly-drift','heart-float','ribbon-streamers','star-trail','ambient-orbits','paper-shower','particle-dissolve','glow-pulse','smoke-wisp']
templates=['lower-third-clean','lower-third-editorial','lower-third-tech','title-card-cinematic','title-card-bold','intro-brand-mark','outro-call-to-action','quote-card-minimal','quote-card-social','callout-pill','callout-arrow','stat-kpi-single','stat-kpi-trio','progress-bar-linear','progress-ring','animated-bar-chart','animated-line-chart','animated-donut-chart','rolling-counter','timeline-milestones','logo-reveal-orbit','logo-reveal-mask','subscribe-button','cta-button-primary','social-frame-16x9','social-frame-9x16','social-frame-square','social-frame-4x5','product-hero','feature-comparison','testimonial-card','app-store-frame']
for category,items,sub in [('text-animation',text_names,'text-presets'),('transition',trans_names,'transitions'),('easing', [x[0] for x in eases],'easing-springs'),('particle-effect',particles,'particle-effects'),('template',templates,'components')]:
    for i,name in enumerate(items):
        desc=next((d for n,d in eases if n==name),None) if category=='easing' else None
        desc=desc or f'{name.replace("-"," ").title()} motion preset for clean, readable visual storytelling; tune onset, duration, distance, and stagger to match the scene.'
        obj={'id':category+'-'+name,'name':name.replace('-',' ').title(),'category':category,'subcategory':sub,'tags':name.split('-')+[category],'mood':['versatile'],'style':['motion-design'],'description':desc,'durationSeconds':0.55 if category in ('transition','text-animation') else 1.2,'parameters':{'duration':0.55,'delay':0,'stagger':0.045,'distance':32,'intensity':0.7},'license':'CC0-1.0','source':'Original motion-design recipe by Motion Studio'}
        add(obj['id'],obj['name'],category,sub,obj['tags'],obj['mood'],obj['style'],desc,'assets/catalogs/motion-presets.json','motion-preset',recolor=False,duration=obj['durationSeconds'] if category in ('text-animation','transition','particle-effect') else None)
        manifest[-1]['props']=obj['parameters']
        globals().setdefault('motion_catalog',[]).append(obj)
(ASSETS/'catalogs'/'motion-presets.json').write_text(json.dumps(motion_catalog,indent=2)+'\n')
# One index file houses pairing and collections; registry path exists and is license-attributed.
(ASSETS/'catalogs'/'font-pairings.json').write_text(json.dumps([{'display':a,'body':b,'guidance':c} for a,b,c in pairings],indent=2)+'\n')
# Document every upstream font package and retain its individual license notice.
font_rows='\n'.join(f"| {f['family']} | {f['source']} | OFL-1.1 | Fontsource package; notice: `{f['licenseFile']}` |" for f in font_catalog)
license_doc="""# Asset licenses and sources

| Asset family | Source | License | Attribution |
|---|---|---|---|
| Lucide icons (1,200 curated SVGs) | https://github.com/lucide-icons/lucide · lucide-static 1.81.0 | ISC | Lucide contributors; copyright notices and permission notice in upstream project. SVG paths are unchanged except normalized presentation attributes. |
| Brand logos (Simple Icons) | https://github.com/simple-icons/simple-icons · simple-icons 15.21.0 | CC0-1.0 | Simple Icons contributors; CC0 dedication. Brand names and marks remain the property of their respective owners; follow brand guidelines. |
| Procedural shapes, backgrounds, textures, illustrations, and device/UI vectors | Generated by `scripts/generate_asset_library.py` | CC0-1.0 (dedicated to public domain) | No attribution required. Original repository-authored geometry. |
| Lottie JSON micro-animations | Generated by `scripts/generate_asset_library.py` | CC0-1.0 | Original simple shape-layer animations; no third-party animation was copied. |
| Twemoji SVG sticker illustrations (100) | https://github.com/twitter/twemoji · Twemoji SVGs packaged by https://www.npmjs.com/package/@twemoji/svg | CC-BY-4.0 | Twemoji contributors; attribution is required by the graphics license. |
| Palette, gradient, and motion-preset data | Generated by `scripts/generate_asset_library.py` | CC0-1.0 | Original color and motion recommendations. |

## Bundled OFL fonts

All 45 font families include a Latin WOFF2 and the upstream package license text is retained per family. OFL-1.1 permits commercial use and redistribution subject to its terms; see each accompanying notice. No separate attribution is required by OFL, though upstream copyright notices remain in the license text.

| Font family | Source package | License | Notice |
|---|---|---|---|
"""+font_rows+"""

Stock-media results are supplied by their provider and retain provider-specific terms/attribution. The app does not cache or relicense media.
"""
(ASSETS/'LICENSES.md').write_text(license_doc)
(ASSETS/'manifest.json').write_text(json.dumps({'version':1,'generatedBy':'scripts/generate_asset_library.py','assets':manifest},indent=2,ensure_ascii=False)+'\n')
print(f'Wrote {len(manifest)} registry entries')
from collections import Counter
print(json.dumps(Counter(x['category'] for x in manifest),indent=2))
