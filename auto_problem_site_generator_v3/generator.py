
import os, csv, json, re, yaml, textwrap, urllib.parse, time
from datetime import datetime

import requests
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_OK = True
except Exception:
    PIL_OK = False

# --- Load config ---
with open("config.yml","r") as f:
    CFG = yaml.safe_load(f)

SITE_NAME = CFG.get("site_name","Instant Auto Fix")
SITE_DESC = CFG.get("site_description","Fast DIY car problem guides with parts links and quick fixes.")
BASEURL = CFG.get("site_baseurl","")
PUBLIC_BASE = CFG.get("public_base_url","").rstrip("/")
BRAND_COLOR = CFG.get("brand_color","#0f172a")
ACCENT_COLOR = CFG.get("accent_color","#22c55e")
MECH_URL = CFG.get("mechanic_cta_url","https://www.repairpal.com/estimator")
AMZ_TAG = CFG.get("amazon_tag","YOUR_AMAZON_TAG")
EBAY_CID = CFG.get("ebay_cid","YOUR_EBAY_CAMPAIGN_ID")
CARPARTS_PID = CFG.get("carparts_pid","YOUR_CARPARTS_PID")
CONTACT = CFG.get("contact_email","you@example.com")
GA_TAG = CFG.get("analytics_google_tag","")
CF_TOKEN = CFG.get("analytics_cloudflare_token","")
ENABLE_BITLY = CFG.get("enable_bitly", True)
BITLY_TOKEN = os.getenv("BITLY_TOKEN") or CFG.get("bitly_token","")
BITLY_DOMAIN = CFG.get("bitly_domain","bit.ly")

OUT_DIR = "site"
ASSETS_DIR = os.path.join(OUT_DIR, "assets")
OG_DIR = os.path.join(ASSETS_DIR, "og")
FIX_DIR = os.path.join(OUT_DIR, "fixes")
MAKES_DIR = os.path.join(OUT_DIR, "makes")
PROBS_DIR = os.path.join(OUT_DIR, "problems")
for d in (ASSETS_DIR, OG_DIR, FIX_DIR, MAKES_DIR, PROBS_DIR):
    os.makedirs(d, exist_ok=True)

# --- Analytics snippet ---
def analytics_snippet():
    bits = []
    if GA_TAG:
        bits.append(f"<script async src=\"https://www.googletagmanager.com/gtag/js?id={GA_TAG}\"></script>")
        bits.append("<script>window.dataLayer = window.dataLayer || []; function gtag(){dataLayer.push(arguments);} gtag('js', new Date()); gtag('config', '%s');</script>" % GA_TAG)
    if CF_TOKEN:
        bits.append(f"<script defer src=\"https://static.cloudflareinsights.com/beacon.min.js\" data-cf-beacon='{{\"token\":\"{CF_TOKEN}\"}}'></script>")
    return "\n".join(bits)

ANALYTICS = analytics_snippet()

# --- Copy assets ---
with open("templates/style.css","r") as f:
    STYLE = f.read()
with open(os.path.join(ASSETS_DIR,"style.css"),"w") as f:
    f.write(STYLE)

def slugify(s):
    s = re.sub(r"[^A-Za-z0-9]+","-", s.strip(), flags=re.M).strip("-")
    return s.lower()

def make_amazon_search_link(query):
    q = urllib.parse.quote_plus(query)
    return f"https://www.amazon.com/s?k={q}&tag={AMZ_TAG}"

def make_ebay_search_link(query):
    q = urllib.parse.quote_plus(query)
    return f"https://www.ebay.com/sch/i.html?_nkw={q}&campid={EBAY_CID}"

def make_carparts_search_link(query):
    q = urllib.parse.quote_plus(query)
    return f"https://www.carparts.com/search?q={q}&pid={CARPARTS_PID}"

def bitly_shorten(url):
    if not (ENABLE_BITLY and BITLY_TOKEN and url.startswith("http")):
        return url
    try:
        r = requests.post(
            "https://api-ssl.bitly.com/v4/shorten",
            headers={"Authorization": f"Bearer {BITLY_TOKEN}","Content-Type":"application/json"},
            json={"long_url": url, "domain": BITLY_DOMAIN},
            timeout=10
        )
        if r.ok:
            return r.json().get("link", url)
    except Exception:
        pass
    return url

def generate_content(year, make, model, problem):
    vehicle = f"{year} {make} {model}"
    title = f"{vehicle} — {problem} (Instant Fix Guide)"
    meta = f"DIY diagnostic steps, likely causes, and parts for {vehicle} with '{problem.lower()}'. "
    h1 = f"{vehicle}: {problem} — Quick DIY Guide"

    p = problem.lower()
    causes = []
    parts = []
    steps = []

    if "won't start" in p or "wont start" in p or "no start" in p:
        causes = ["Weak or dead battery","Corroded/loose battery terminals","Failed starter motor or solenoid","Faulty ignition switch","Immobilizer/security issue"]
        parts = ["Replacement battery","Battery terminal cleaning kit","Starter motor","OBD2 scanner"]
        steps = ["Measure battery voltage (~12.6V off).","Clean/tighten terminals; try jump-start.","If single click heard, suspect starter/solenoid.","Scan for codes; rule out immobilizer.","Replace failed component; verify charging."]
    elif "alternator" in p:
        causes = ["Worn brushes or regulator","Loose/slipping belt","Poor ground/corroded wiring","Battery near end-of-life"]
        parts = ["Alternator (reman/new)","Serpentine belt","Digital multimeter","Battery charger/maintainer"]
        steps = ["Test ~13.8–14.6V at idle.","Inspect belt; replace if glazed/cracked.","Check grounds/wiring for corrosion.","Replace alternator if low/erratic output."]
    elif "rough idle" in p:
        causes = ["Vacuum leak","Dirty throttle body/IAC","Fouled plugs/weak coils","Clogged MAF sensor"]
        parts = ["Vacuum hose kit","Throttle body cleaner","Spark plugs (OEM)","MAF sensor cleaner"]
        steps = ["Inspect vacuum lines; listen for hiss.","Clean throttle body and idle passages.","Replace worn plugs; test coils.","Clean MAF; clear codes; re-learn idle."]
    elif "ac" in p or "a/c" in p or "air conditioning" in p:
        causes = ["Low refrigerant/leak","Failed compressor clutch","Clogged cabin filter","Faulty condenser fan"]
        parts = ["UV dye + recharge kit (if legal)","Cabin air filter","Condenser fan","Leak detection kit"]
        steps = ["Replace cabin filter if dirty.","Verify clutch engagement; check fuses/relays.","Ensure condenser fan runs with AC.","Leak-test; recharge to spec."]
    elif "overheating" in p:
        causes = ["Low coolant/leak","Thermostat stuck","Radiator fan inoperative","Clogged radiator"]
        parts = ["Thermostat","Radiator fan assembly","Coolant + pressure tester","Radiator flush kit"]
        steps = ["Check coolant level; pressure test.","Verify fan operation; inspect relays.","Replace stuck thermostat.","Flush clogged radiator; verify cap pressure."]
    elif "abs light" in p or "abs" in p:
        causes = ["Wheel speed sensor","Damaged tone ring","Wiring harness damage","ABS module fault"]
        parts = ["Wheel speed sensor","OBD2 scanner (ABS)","Tone ring","Contact cleaner"]
        steps = ["Scan for ABS codes to identify wheel.","Inspect sensor wiring/connectors.","Check tone ring for cracks/rust.","Replace sensor; clear codes."]
    elif "transmission" in p or "slipping" in p or "rough shift" in p:
        causes = ["Low/dirty fluid","Clogged filter","Valve body wear","TCM software issue"]
        parts = ["ATF + filter kit","OBD2 scanner","Gasket kit","Service manual"]
        steps = ["Check fluid level/condition.","Service fluid/filter if due.","Scan TCM; perform updates/relearn.","If persists, seek pro diagnosis."]
    elif "oil leak" in p or "valve cover" in p:
        causes = ["Aged valve cover gasket","PCV overpressure","Warped cover/loose fasteners","Cam seal seepage"]
        parts = ["Valve cover gasket set","RTV sealant (spec)","PCV valve","Brake cleaner"]
        steps = ["Clean area; verify source.","Replace gasket; torque to spec.","Replace PCV if clogged.","Recheck after drive cycle."]
    elif "p0420" in p or "catalytic" in p:
        causes = ["Aged catalytic converter","Exhaust leak pre-cat","O2 sensor slow response","Misfire damaging catalyst"]
        parts = ["Catalytic converter","Upstream O2 sensor","Exhaust gaskets","OBD2 scanner"]
        steps = ["Check for leaks; inspect O2 readings.","Fix misfires first.","Replace failing O2 if lazy.","Replace cat if efficiency remains low."]
    elif "p0442" in p or "evap" in p:
        causes = ["Loose/faulty gas cap","Small EVAP leak (hoses)","Purge/vent valve fault","Cracked charcoal canister"]
        parts = ["Gas cap (OEM)","EVAP hose","Purge valve","Smoke tester (shop)"]
        steps = ["Tighten/replace gas cap.","Inspect EVAP lines for cracks.","Test purge/vent solenoids.","Clear codes; run EVAP monitor."]
    elif "wheel bearing" in p or "humming" in p:
        causes = ["Worn wheel bearing","Uneven tire wear","Bent rim","CV joint wear"]
        parts = ["Wheel hub/bearing","Torque wrench","Jack stands","Axle nut socket"]
        steps = ["Confirm noise changes with steering load.","Check tire wear and wheel balance.","Replace hub assembly if play/noise present.","Torque to spec; road test."]
    elif "brake" in p and "squeal" in p:
        causes = ["Worn pads","Glazed rotors","Missing shims","Sticking caliper"]
        parts = ["Brake pads","Rotors","Shim kit","High-temp grease"]
        steps = ["Measure pad thickness; replace if low.","Resurface/replace rotors if glazed.","Install shims; lube slide pins.","Bed-in pads per instructions."]
    elif "tpms" in p or "tire pressure" in p:
        causes = ["Low tire","Dead TPMS sensor battery","Sensor not learned","Damaged valve stem"]
        parts = ["TPMS sensor","Valve stem kit","TPMS relearn tool","Tire inflator"]
        steps = ["Set pressures to door placard.","Relearn sensors if needed.","Replace dead sensors.","Check stems for leaks."]
    elif "key fob" in p or "remote" in p:
        causes = ["Dead fob battery","Desync with BCM","Button failure","Receiver issue"]
        parts = ["CR2032 battery","Replacement fob","OBD programmer (some makes)","Contact cleaner"]
        steps = ["Replace battery.","Reprogram/initialize per manual.","Clean contacts.","Replace fob if unresponsive."]
    elif "window" in p and ("won't" in p or "stuck" in p or "wont" in p):
        causes = ["Failed window regulator","Switch fault","Blown fuse","Broken window track"]
        parts = ["Window regulator","Switch panel","Fuse set","Plastic trim tools"]
        steps = ["Check fuses first.","Test switch output.","Inspect regulator/motor operation.","Replace failed component."]
    else:
        causes = ["Wear item related to symptom","Corroded/loose wiring/connectors","Sensor out of range","ECU codes indicate subsystem"]
        parts = ["OBD2 scanner","Relevant sensor","Basic hand tools","Safety gear"]
        steps = ["Scan for codes + freeze frame.","Inspect/connectors/grounds.","Test components vs manual specs.","Replace failed part; clear codes."]

    part_links = []
    for part in parts:
        query = f"{year} {make} {model} {part}"
        amz = make_amazon_search_link(query)
        eba = make_ebay_search_link(query)
        car = make_carparts_search_link(query)
        # Shorten if configured
        amz = bitly_shorten(amz)
        eba = bitly_shorten(eba)
        car = bitly_shorten(car)
        part_links.append({"label": part, "amazon": amz, "ebay": eba, "carparts": car})

    diagnostic = [
        "Scan for OBD-II codes to narrow subsystem.",
        "Check fuses/relays related to the symptom.",
        "Quick voltage/continuity tests as applicable.",
        "Inspect for leaks/damage/loose connectors.",
        "Decide DIY vs shop quote based on time/cost."
    ]

    related = [
        f"{year} {make} {model} check engine light on",
        f"{year} {make} {model} battery light flickers",
        f"{year} {make} {model} stalls at idle",
        f"{year} {make} {model} vibration at highway speed"
    ]

    return {
        "title": title, "meta": meta, "h1": h1,
        "vehicle": f"{year} {make} {model}", "year": year, "make": make, "model": model, "problem": problem,
        "causes": causes, "diagnostic": diagnostic, "parts": part_links, "fix_steps": steps, "related": related
    }

def ensure_font():
    # Rely on default PIL bitmap font if TTF not found
    return None

def gen_og_image(slug, title):
    path = os.path.join(OG_DIR, f"{slug}.png")
    if not PIL_OK:
        return None
    W, H = 1200, 630
    img = Image.new("RGB", (W,H), color=BRAND_COLOR)
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 64)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 30)
    except Exception:
        font_big = ImageFont.load_default()
        font_small = ImageFont.load_default()
    margin = 60
    draw.text((margin, margin), SITE_NAME, fill="#ffffff", font=font_small)
    # Wrap title
    lines = textwrap.wrap(title, width=28)
    y = margin+60
    for line in lines[:6]:
        draw.text((margin, y), line, fill="#ffffff", font=font_big)
        y += 70
    img.save(path, format="PNG")
    return path

# Load HTML templates
with open("templates/page.html","r") as f:
    TEMPLATE_PAGE = f.read()
with open("templates/index.html","r") as f:
    TEMPLATE_INDEX = f.read()

# Read CSV
rows = []
with open("data/problems.csv","r", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append({k:v.strip() for k,v in r.items()})

sitemap = []
by_make = {}
by_problem = {}

def head_common(root, og_image):
    return f'''{ANALYTICS}
<link rel="stylesheet" href="{root}assets/style.css">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">'''

# Build pages
for r in rows:
    ctx = generate_content(r["year"], r["make"], r["model"], r["problem"])
    slug = slugify(f"{ctx['vehicle']} {ctx['problem']}")
    og_path = gen_og_image(slug, ctx["title"])
    og_rel = f"{BASEURL}/assets/og/{slug}.png" if BASEURL else f"assets/og/{slug}.png"
    root = "../"  # for page depth
    # absolute share URL if possible
    page_rel_url = f"{BASEURL}/fixes/{slug}.html" if BASEURL else f"./fixes/{slug}.html"
    if PUBLIC_BASE:
        share_url = f"{PUBLIC_BASE}/fixes/{slug}.html"
        share_url_short = bitly_shorten(share_url)
    else:
        share_url = page_rel_url
        share_url_short = share_url

    def li(items): 
        return "\\n".join([f"<li>{x}</li>" for x in items])
    def li_parts(items):
        out = []
        for p in items:
            # prefer shortened affiliate links already in ctx
            amz = p["amazon"]; eba = p["ebay"]; car = p["carparts"]
            out.append(f'<li><strong>{p["label"]}</strong> — '
                       f'<a href="{amz}" rel="nofollow noopener" target="_blank">Amazon</a> · '
                       f'<a href="{eba}" rel="nofollow noopener" target="_blank">eBay</a> · '
                       f'<a href="{car}" rel="nofollow noopener" target="_blank">CarParts</a></li>')
        return "\\n".join(out)
    related_html = "\\n".join([f'<li><a href="../fixes/{slugify(r)}.html">{r}</a></li>' for r in ctx["related"]])

    json_ld = {
      "@context":"https://schema.org",
      "@type":"TechArticle",
      "headline": ctx["title"],
      "about": f"{ctx['vehicle']} {ctx['problem']}",
      "audience": "DIY car owners",
      "author": {"@type":"Organization","name": SITE_NAME},
      "publisher": {"@type":"Organization","name": SITE_NAME},
      "description": ctx["meta"],
      "dateModified": datetime.utcnow().isoformat()+"Z"
    }

    html = TEMPLATE_PAGE.format(
        title = ctx["title"],
        meta_description = ctx["meta"],
        head_common = head_common(root, og_rel if og_path else ""),
        json_ld = json.dumps(json_ld, indent=2),
        h1 = ctx["h1"],
        year = ctx["year"], make = ctx["make"], model = ctx["model"], problem = ctx["problem"],
        causes_html = li(ctx["causes"]),
        diagnostic_html = li(ctx["diagnostic"]),
        parts_html = li_parts(ctx["parts"]),
        fix_html = li(ctx["fix_steps"]),
        related_html = related_html,
        site_name = SITE_NAME,
        mechanic_cta_url = MECH_URL,
        contact_email = CONTACT,
        make = ctx["make"],
        make_slug = slugify(ctx["make"]),
        problem_slug = slugify(ctx["problem"]),
        share_url = share_url_short,
        share_url_enc = urllib.parse.quote_plus(share_url_short),
        share_text = urllib.parse.quote_plus(ctx["title"]),
        causes_js = json.dumps(ctx["causes"]),
        parts_js = json.dumps(ctx["parts"]),
        root = root,
        og_image = og_rel if og_path else ""
    )
    with open(os.path.join(FIX_DIR, f"{slug}.html"),"w", encoding="utf-8") as f:
        f.write(html)

    meta = f"{ctx['vehicle']} — {ctx['problem']}"
    url_rel = f".{BASEURL}/fixes/{slug}.html" if BASEURL else f"./fixes/{slug}.html"
    sitemap.append({"title": ctx["title"], "url": url_rel, "meta": meta, "make": ctx["make"], "problem": ctx["problem"]})

    by_make.setdefault(ctx["make"], []).append((ctx["title"], url_rel, meta))
    by_problem.setdefault(ctx["problem"], []).append((ctx["title"], url_rel, meta))

# Index page
with open(os.path.join(OUT_DIR, "index.html"),"w", encoding="utf-8") as f:
    f.write(TEMPLATE_INDEX.format(
        site_name=SITE_NAME, site_description=SITE_DESC,
        head_common = head_common("./", f"assets/og/{slugify(SITE_NAME)}.png")
    ))

# Make index pages
for mk, items in by_make.items():
    items_html = "\\n".join([f'<div class="card"><a href="{u}"><h3>{t}</h3></a><div class="meta">{m}</div></div>' for t,u,m in items])
    with open(os.path.join(MAKES_DIR, f"{slugify(mk)}.html"),"w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f\"\"\"
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{SITE_NAME} — {mk} Issues</title>
          <meta name="description" content="Common issues and fixes for {mk} models.">
          {head_common('../', 'assets/og/{slugify(mk)}.png')}
        </head>
        <body>
          <div class="headerbar">
            <header class="container">
              <a href="../index.html" class="brand">{SITE_NAME}</a>
            </header>
          </div>
          <main class="container card">
            <h1>{mk} — Common Problems and DIY Fixes</h1>
            {items_html}
          </main>
          <footer class="container foot">
            <p>© {SITE_NAME}.</p>
          </footer>
        </body>
        </html>
        \"\"\"))

# Problem index pages
for pb, items in by_problem.items():
    items_html = "\\n".join([f'<div class="card"><a href="{u}"><h3>{t}</h3></a><div class="meta">{m}</div></div>' for t,u,m in items])
    with open(os.path.join(PROBS_DIR, f"{slugify(pb)}.html"),"w", encoding="utf-8") as f:
        f.write(textwrap.dedent(f\"\"\"
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <title>{SITE_NAME} — Fixes for {pb}</title>
          <meta name="description" content="Guides for {pb} across many vehicles.">
          {head_common('../', 'assets/og/{slugify(pb)}.png')}
        </head>
        <body>
          <div class="headerbar">
            <header class="container">
              <a href="../index.html" class="brand">{SITE_NAME}</a>
            </header>
          </div>
          <main class="container card">
            <h1>Fixes for: {pb}</h1>
            {items_html}
          </main>
          <footer class="container foot">
            <p>© {SITE_NAME}.</p>
          </footer>
        </body>
        </html>
        \"\"\"))

# Write JSON sitemap
with open(os.path.join(OUT_DIR, "sitemap.json"),"w", encoding="utf-8") as f:
    json.dump(sitemap, f, indent=2)

# Write XML sitemap
base = PUBLIC_BASE + "/" if PUBLIC_BASE else BASEURL + "/" if BASEURL else "./"
items_xml = []
for it in sitemap[:5000]:
    loc = (PUBLIC_BASE + it["url"][1:]) if (PUBLIC_BASE and it["url"].startswith(".")) else it["url"]
    items_xml.append(f"<url><loc>{loc}</loc></url>")
with open(os.path.join(OUT_DIR,"sitemap.xml"),"w", encoding="utf-8") as f:
    f.write("<?xml version='1.0' encoding='UTF-8'?>\\n<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>\\n" + "\\n".join(items_xml) + "\\n</urlset>")

# robots.txt
with open(os.path.join(OUT_DIR,"robots.txt"),"w", encoding="utf-8") as f:
    f.write(f"User-agent: *\\nAllow: /\\nSitemap: {base}sitemap.xml\\n")

# RSS feed from first 50 items
rss_items = []
nowrfc = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
for it in sitemap[:50]:
    link = (PUBLIC_BASE + it["url"][1:]) if (PUBLIC_BASE and it["url"].startswith(".")) else it["url"]
    rss_items.append(f"<item><title>{it['title']}</title><link>{link}</link><pubDate>{nowrfc}</pubDate><description>{it['meta']}</description></item>")
with open(os.path.join(OUT_DIR,"feed.xml"),"w", encoding="utf-8") as f:
    f.write(f"<?xml version='1.0' encoding='UTF-8' ?>\\n<rss version='2.0'><channel><title>{SITE_NAME}</title><link>{base}</link><description>{SITE_DESC}</description>{''.join(rss_items)}</channel></rss>")

print(f"Built {len(sitemap)} pages in {FIX_DIR}")
