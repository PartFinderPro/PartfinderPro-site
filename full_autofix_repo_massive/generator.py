
import os, csv, json, re, yaml, urllib.parse
with open('config.yml','r') as f: CFG=yaml.safe_load(f)
SITE=CFG.get('site_name','Instant Auto Fix'); DESC=CFG.get('site_description',''); AMZ=CFG.get('amazon_tag','YOUR'); EBA=CFG.get('ebay_cid','CID'); CAR=CFG.get('carparts_pid','PID'); MECH=CFG.get('mechanic_cta_url','https://www.repairpal.com/estimator')
OUT='site'; AS='assets'; FIX='fixes'; MK='makes'; PR='problems'
import os; [os.makedirs(os.path.join(OUT,d), exist_ok=True) for d in (AS, FIX, MK, PR)]
open(os.path.join(OUT,AS,'style.css'),'w').write(open('templates/style.css').read())
def slug(s): import re; return re.sub(r'[^A-Za-z0-9]+','-',s.strip()).strip('-').lower()
def A(q): from urllib.parse import quote_plus; q=quote_plus(q); return f'https://www.amazon.com/s?k={q}&tag={AMZ}'
def E(q): from urllib.parse import quote_plus; q=quote_plus(q); return f'https://www.ebay.com/sch/i.html?_nkw={q}&campid={EBA}'
def C(q): from urllib.parse import quote_plus; q=quote_plus(q); return f'https://www.carparts.com/search?q={q}&pid={CAR}'
IDX=open('templates/index.html').read(); PAGE=open('templates/page.html').read()
rows=list(csv.DictReader(open('data/problems.csv')))
site=[]; by_make={}; by_prob={}
def li(xs): return '\n'.join([f'<li>{x}</li>' for x in xs])
def lip(parts): 
    out=[]
    for p in parts: out.append(f'<li><strong>{p[0]}</strong> — <a href="{A(p[1])}">Amazon</a> · <a href="{E(p[1])}">eBay</a> · <a href="{C(p[1])}">CarParts</a></li>')
    return '\n'.join(out)
for r in rows:
    y,make,model,prob=r['year'],r['make'],r['model'],r['problem']
    v=f'{y} {make} {model}'; title=f'{v} — {prob} (Instant Fix Guide)'; h1=f'{v}: {prob} — Quick DIY Guide'
    causes=['Battery/charging issue','Corroded connectors','Failed component','Sensor out-of-range','ECU code present']
    if 'alternator' in prob.lower(): causes=['Regulator/brushes','Loose/glazed belt','Bad ground','Wiring corrosion','Weak battery']
    if "won't start" in prob.lower() or 'wont start' in prob.lower(): causes=['Weak or dead battery','Corroded terminals','Starter/solenoid fault','Ignition switch','Immobilizer issue']
    parts=[('OBD2 scanner',f'{v} OBD2 scanner'),('Relevant sensor',f'{v} sensor'),('Basic tools',f'{v} tools')]
    if 'alternator' in prob.lower(): parts=[('Alternator (reman/new)',f'{v} alternator'),('Serpentine belt',f'{v} serpentine belt'),('Digital multimeter',f'{v} multimeter')]
    diag=['Scan for codes','Check fuses/relays','Voltage tests','Inspect grounds','DIY vs shop decision']
    fix=['Identify failed part','Replace with OEM-spec','Clear codes','Road test and verify']
    slugv=slug(f'{v} {prob}'); fp=os.path.join(OUT,FIX,f'{slugv}.html')
    open(fp,'w',encoding='utf-8').write(PAGE.format(title=title, h1=h1, year=y, make=make, model=model, problem=prob, causes_html=li(causes), diagnostic_html=li(diag), parts_html=lip(parts), fix_html=li(fix), site_name=SITE, root='../'))
    site.append({'title':title,'url':f'./fixes/{slugv}.html','meta':f'{v} — {prob}','make':make,'problem':prob})
open(os.path.join(OUT,'index.html'),'w',encoding='utf-8').write(IDX.format(site_name=SITE, site_description=DESC))
import json; open(os.path.join(OUT,'sitemap.json'),'w').write(json.dumps(site,indent=2))
open(os.path.join(OUT,'sitemap.xml'),'w').write("<?xml version='1.0' encoding='UTF-8'?>\n<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\n"+"\n".join([f"<url><loc>{i['url']}</loc></url>" for i in site])+"\n</urlset>")
open(os.path.join(OUT,'robots.txt'),'w').write('User-agent: *\nAllow: /\nSitemap: ./sitemap.xml\n')
print('Built',len(site),'pages')
