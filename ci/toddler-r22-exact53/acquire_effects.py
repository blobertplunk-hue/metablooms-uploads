#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, re, subprocess, sys, time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
SOURCES=json.loads((ROOT/'sources.json').read_text())
OUT=Path(sys.argv[1]).resolve()
RAW=OUT/'raw'; EFFECTS=OUT/'effects'; EVIDENCE=OUT/'evidence'
for d in (RAW,EFFECTS,EVIDENCE): d.mkdir(parents=True,exist_ok=True)

def run(cmd, check=True):
    print('+',' '.join(map(str,cmd)),flush=True)
    p=subprocess.run(cmd,text=True,capture_output=True)
    if p.stdout: print(p.stdout[-4000:])
    if p.stderr: print(p.stderr[-4000:],file=sys.stderr)
    if check and p.returncode: raise RuntimeError(f'exit {p.returncode}: {cmd}')
    return p

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def direct_download(url,dest):
    req=Request(url,headers={'User-Agent':'Mozilla/5.0 MetaBlooms-R22/1.0'})
    with urlopen(req,timeout=180) as r, dest.open('wb') as f:
        while True:
            b=r.read(1024*1024)
            if not b: break
            f.write(b)

def freesound_download(row,destbase):
    # Use the public CDN preview rather than downloading a potentially huge original file.
    req=Request(row['page_url'],headers={'User-Agent':'Mozilla/5.0 MetaBlooms-R22/1.0'})
    with urlopen(req,timeout=90) as r: html=r.read().decode('utf-8','replace')
    urls=re.findall(r'https:\\/\\/cdn\.freesound\.org\\/previews\\/[^"\\ ]+?\.(?:mp3|ogg)',html)
    urls=[u.replace('\\/','/') for u in urls]
    if not urls:
        urls=re.findall(r'https://cdn\.freesound\.org/previews/[^" ]+?\.(?:mp3|ogg)',html)
    if not urls: raise RuntimeError(f'no public preview URL found for {row["id"]}')
    preferred=next((u for u in urls if '-hq.' in u),next((u for u in urls if '-lq.' in u),urls[0]))
    suffix='.'+preferred.rsplit('.',1)[-1]
    target=destbase.with_suffix(suffix)
    direct_download(preferred,target)
    return target

def probe(path):
    p=run(['ffprobe','-v','error','-show_entries','format=duration','-show_entries','stream=codec_type,codec_name,sample_rate,channels','-of','json',str(path)])
    data=json.loads(p.stdout)
    duration=float(data['format']['duration'])
    assert duration>0 and any(s.get('codec_type')=='audio' for s in data.get('streams',[]))
    return data,duration

rows=[]
for index,row in enumerate(SOURCES,1):
    ident=row['id']; print(f'[{index}/{len(SOURCES)}] {ident}',flush=True)
    base=RAW/ident
    last=None
    for attempt in range(1,4):
        try:
            if row['method']=='direct':
                ext=Path(row['url'].split('?',1)[0]).suffix or '.bin'
                raw=base.with_suffix(ext)
                direct_download(row['url'],raw)
            else:
                raw=freesound_download(row,base)
            if not raw.is_file() or raw.stat().st_size<1000: raise RuntimeError('download too small')
            probe(raw)
            break
        except Exception as exc:
            last=exc
            for old in RAW.glob(ident+'.*'): old.unlink(missing_ok=True)
            if attempt==3: raise
            time.sleep(2**attempt)
    final=EFFECTS/f'{ident}.mp3'
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y']
    if row.get('trim_start') is not None: cmd += ['-ss',str(float(row['trim_start']))]
    cmd += ['-i',str(raw)]
    if row.get('trim_duration') is not None: cmd += ['-t',str(float(row['trim_duration']))]
    cmd += ['-vn','-ac','1','-ar','44100','-af','loudnorm=I=-20:TP=-3:LRA=7','-codec:a','libmp3lame','-b:a','128k',str(final)]
    run(cmd)
    meta,duration=probe(final)
    rows.append({'id':ident,'label':row['label'],'bytes':final.stat().st_size,'sha256':sha(final),'duration_seconds':duration,'source':row})
(EVIDENCE/'ACQUIRED_EFFECTS.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False))
assert len(rows)==26 and len({x['id'] for x in rows})==26
print('PASS: acquired and normalized 26/26 R22 effects')
