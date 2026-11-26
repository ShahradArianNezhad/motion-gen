#!/usr/bin/env python3
"""Fetch Latin WOFF2 files and upstream OFL texts from Fontsource's npm packages."""
from __future__ import annotations
import subprocess, tarfile, tempfile, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=['dm-sans','manrope','vazirmatn','inter','roboto','open-sans','lato','montserrat','poppins','plus-jakarta-sans','outfit','space-grotesk','sora','urbanist','work-sans','nunito-sans','source-sans-3','archivo','ibm-plex-sans','roboto-condensed','oswald','barlow-condensed','bebas-neue','anton','playfair-display','dm-serif-display','fraunces','lora','libre-baskerville','cormorant-garamond','source-serif-4','merriweather','roboto-mono','ibm-plex-mono','space-mono','jetbrains-mono','fira-code','caveat','pacifico','dancing-script','caveat-brush','nunito','quicksand','comfortaa','fredoka']
OUT=ROOT/'assets'/'fonts'; OUT.mkdir(parents=True,exist_ok=True); (OUT/'licenses').mkdir(exist_ok=True)
sources=[]
def pack(spec: str, dest: Path) -> Path|None:
    result=subprocess.run(['npm','pack',spec,'--pack-destination',str(dest),'--silent'],text=True,capture_output=True)
    if result.returncode: return None
    path=dest/result.stdout.strip().splitlines()[-1]
    return path if path.exists() else None
for slug in FAMILIES:
    with tempfile.TemporaryDirectory(prefix='motion-font-') as tmp:
        td=Path(tmp); package=pack(f'@fontsource-variable/{slug}@5.3.0',td); package_name=f'@fontsource-variable/{slug}'
        if package is None:
            package=pack(f'@fontsource/{slug}@5.3.0',td); package_name=f'@fontsource/{slug}'
        if package is None:
            print(f'ERROR: no OFL Fontsource package found for {slug}',file=sys.stderr); sys.exit(1)
        with tarfile.open(package,'r:gz') as tar:
            files=[m for m in tar.getmembers() if m.isfile() and m.name.endswith('.woff2') and 'latin-' in m.name and '-ext-' not in m.name and '-italic' not in m.name]
            variable=[m for m in files if 'wght' in m.name]
            static=[m for m in files if '400-normal' in m.name]
            choices=variable or static or files
            if not choices: print(f'ERROR: Latin WOFF2 missing for {slug}',file=sys.stderr);sys.exit(1)
            chosen=sorted(choices,key=lambda m:(('standard' not in m.name),('opsz' in m.name),m.name))[0]
            (OUT/f'{slug}-latin.woff2').write_bytes(tar.extractfile(chosen).read())
            lic=next((m for m in tar.getmembers() if m.isfile() and m.name.endswith('/LICENSE')),None)
            if lic: (OUT/'licenses'/f'{slug}-OFL.txt').write_bytes(tar.extractfile(lic).read())
        sources.append({'slug':slug,'package':package_name,'source':f'https://www.npmjs.com/package/{package_name}','file':f'assets/fonts/{slug}-latin.woff2','licenseFile':f'assets/fonts/licenses/{slug}-OFL.txt','variable':bool(variable),'weights':[100,900] if variable else [400]})
        print(f'{slug}: {package_name} → {chosen.name}')
(ROOT/'assets'/'fonts'/'font-sources.json').write_text(__import__('json').dumps(sources,indent=2)+'\n')
