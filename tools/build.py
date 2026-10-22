import os, re, json, shutil, html
from data import RAJKOT, AHMEDABAD, AIRPORTS

DOMAIN = "https://www.chamundacab.in"   # <-- change to your real domain, then re-run: python3 build.py
BRAND = "Chamunda Cab"
BOOK_NUM, BOOK_DISP = "+918128295920", "+91 81282 95920"
WA_NUM, WA_DISP = "916352179909", "+91 63521 79909"
OUT = "out"
VEH = [("Swift Dzire / Sedan","5 Seater",12),("Ertiga / MUV","7 Seater",14),("Innova","7 Seater",17),("Innova Crysta","8 Seater",20)]
TODAY = "2026-10-04"

def slug(s): return re.sub(r'[^a-z0-9]+','-',s.lower()).strip('-')
def r50(x): return int(round(x/50.0)*50)
def inr(x): return "\u20b9{:,}".format(x)
e = html.escape
def wa(text="Hello Chamunda Cab, I want to book a taxi."):
    from urllib.parse import quote
    return "https://wa.me/%s?text=%s" % (WA_NUM, quote(text))

# ---------- build route list ----------
pairs = {}
def add(o, d, km, via, hrs, note, kind):
    s = "%s-to-%s-taxi" % (slug(o), slug(d))
    if s in pairs: return
    pairs[s] = dict(slug=s,o=o,d=d,km=km,via=via,hrs=hrs,note=note,kind=kind)
def both(a, b, km, via, hrs, note_b, note_a, kind):
    add(a,b,km,via,hrs,note_b,kind); add(b,a,km,via,hrs,note_a,kind)

for c,km,via,h,n in RAJKOT:
    kind = "airport" if "Airport" in c else "oneway"
    both("Rajkot",c,km,via,h,n,"Rajkot city, Gujarat's Saurashtra hub",kind)
for c,km,via,h,n in AHMEDABAD:
    both("Ahmedabad",c,km,via,h,n,"Ahmedabad city and SVPI Airport region","oneway")
    off = 22 if c=="Gandhinagar" else km+5
    both("Ahmedabad Airport",c,off if c=="Gandhinagar" else off,via,h,n,"SVPI Airport, Ahmedabad","airport")
rk = {c:(km,via,h,n) for c,km,via,h,n in RAJKOT}
for nm,code,city,off,note in AIRPORTS:
    if nm=="Mundra": continue
    # city <-> own airport
    both(city,nm+" Airport",off,"Direct city-to-airport road","%s"%("0.5-1" if off<20 else "1"),note,"%s city"%city,"airport")
    # Rajkot <-> other-city airports
    if city in rk and city!="Rajkot":
        km,via,h,n = rk[city]
        both("Rajkot",nm+" Airport",km+off,via,h,note,"Rajkot city","airport")
LOCAL = [
 ("rajkot-railway-station-taxi","Rajkot Railway Station Taxi & Cab","Pickup and drop taxi at Rajkot Junction railway station, 24x7."),
 ("rajkot-sightseeing-taxi","Rajkot Sightseeing Taxi & Cab","City sightseeing cab in Rajkot: Watson Museum, Kaba Gandhi No Delo, Race Course and Lalpari Lake."),
 ("one-way-taxi-gujarat","One-Way Taxi & Cab in Gujarat","One-way drop taxi from Rajkot and Ahmedabad: pay only one side."),
 ("round-trip-cab-gujarat","Round Trip Taxi & Cab in Gujarat","Round trip outstation cab from Rajkot and Ahmedabad with waiting and multi-day options."),
]

def fares(km):
    return [(n,s,r,r50(km*r),r50(km*r*2)) for n,s,r in VEH]

# ---------- shared chunks ----------
def head(pf, title, desc, path, kw="", schema=None, robots="index,follow,max-image-preview:large"):
    url = DOMAIN + "/" + path
    h = ['<!DOCTYPE html>\n<html lang="en-IN">\n<head>\n<meta charset="UTF-8">',
     '<meta name="viewport" content="width=device-width, initial-scale=1">',
     '<title>%s</title>' % e(title),
     '<meta name="description" content="%s">' % e(desc),
     ('<meta name="keywords" content="%s">' % e(kw)) if kw else '',
     '<meta name="robots" content="%s">' % robots,
     '<link rel="canonical" href="%s">' % url,
     '<link rel="alternate" hreflang="en-in" href="%s">' % url,
     '<meta name="author" content="%s">' % BRAND,
     '<meta name="geo.region" content="IN-GJ"><meta name="geo.placename" content="Rajkot, Gujarat"><meta name="geo.position" content="22.3039;70.8022"><meta name="ICBM" content="22.3039, 70.8022">',
     '<meta name="theme-color" content="#0d0d0d">',
     '<meta property="og:type" content="website"><meta property="og:site_name" content="%s"><meta property="og:locale" content="en_IN">' % BRAND,
     '<meta property="og:title" content="%s"><meta property="og:description" content="%s"><meta property="og:url" content="%s"><meta property="og:image" content="%s/images/hero.jpg">' % (e(title),e(desc),url,DOMAIN),
     '<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="%s"><meta name="twitter:description" content="%s">' % (e(title),e(desc)),
     '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
     '<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">',
     '<link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">',
     '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,800&family=Manrope:wght@400;500;600;700;800&family=Poppins:wght@600;700&display=swap" rel="stylesheet">',
     '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" rel="stylesheet">',
     '<link href="%sstyle.css" rel="stylesheet">' % pf]
    for s in (schema or []):
        h.append('<script type="application/ld+json">%s</script>' % json.dumps(s, ensure_ascii=False))
    return "\n".join(x for x in h if x)

def nav(pf):
    return '''<nav class="site-nav navbar navbar-expand-lg">
  <div class="container">
    <a class="brand" href="%(p)sindex.html"><img class="brand-logo" src="%(p)simages/logo-header.jpg" alt="Chamunda Cab Tourism - Your Journey, Our Responsibility" width="680" height="272"></a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mainNav" aria-controls="mainNav" aria-expanded="false" aria-label="Toggle menu"><i class="bi bi-list fs-4"></i></button>
    <div class="collapse navbar-collapse" id="mainNav">
      <ul class="navbar-nav mx-auto">
        <li class="nav-item"><a class="nav-link" href="%(p)sbooking.html">Cab Booking</a></li>
        <li class="nav-item"><a class="nav-link" href="%(p)sroutes.html">All Routes</a></li>
        <li class="nav-item"><a class="nav-link" href="%(p)sfleet.html">Our Fleet</a></li>
        <li class="nav-item"><a class="nav-link" href="%(p)sabout.html">About Us</a></li>
      </ul>
      <a href="tel:%(bn)s" class="btn btn-call me-lg-2 mb-2 mb-lg-0"><i class="bi bi-telephone-fill me-2"></i>%(bd)s</a>
      <a href="https://wa.me/%(wn)s" target="_blank" rel="noopener" class="btn btn-wa wa-link"><i class="fab fa-whatsapp me-2"></i>WhatsApp</a>
    </div>
  </div>
</nav>''' % dict(p=pf,bn=BOOK_NUM,bd=BOOK_DISP,wn=WA_NUM)

TPL_FOOTER = r'''<footer class="cc-footer">
  <div class="container">
    <div class="cc-foot-grid">

      <!-- 1. Brand + contact -->
      <div class="cc-foot-brand">
        <a href="@@P@@index.html" class="cc-foot-logo"><img src="@@P@@images/logo.jpg" alt="Chamunda Cab Tourism - Your Journey, Our Responsibility" width="1643" height="656"></a>
        <p class="cc-foot-about">All-India taxi &amp; cab service, based in Rajkot: one-way, outstation, round trip, local and airport transfers.</p>
        <ul class="cc-foot-contact">
          <li><a href="mailto:booking.chamundacab@gmail.com" aria-label="Email Chamunda Cab"><i class="bi bi-envelope-fill" aria-hidden="true"></i><span>booking.chamundacab@gmail.com</span></a></li>
          <li><a href="tel:+918128295920" aria-label="Call Chamunda Cab"><i class="bi bi-telephone-fill" aria-hidden="true"></i><span>+91 81282 95920</span></a></li>
          <li><a href="https://wa.me/916352179909" target="_blank" rel="noopener noreferrer" aria-label="Chat with Chamunda Cab on WhatsApp"><i class="fab fa-whatsapp" aria-hidden="true"></i><span>+91 63521 79909</span></a></li>
        </ul>
      </div>

      <!-- 2. Navigation -->
      <nav class="cc-foot-col" aria-label="Footer navigation">
        <h4>Navigation</h4>
        <a href="@@P@@index.html">Home</a>
        <a href="@@P@@booking.html">Cab Booking</a>
        <a href="@@P@@routes.html">All Routes</a>
        <a href="@@P@@fleet.html">Our Cars &amp; Rates</a>
        <a href="@@P@@about.html">About Us</a>
        <a href="@@P@@contact.html">Contact Us</a>
      </nav>

      <!-- 3. Popular routes (2-column grid) -->
      <nav class="cc-foot-col cc-foot-routes" aria-label="Popular taxi routes">
        <h4>Popular taxi routes across India</h4>
        <div class="cc-routes-grid">
          @@LINKS@@
        </div>
      </nav>

      <!-- 4. Policies -->
      <nav class="cc-foot-col" aria-label="Policies">
        <h4>Quick links</h4>
        <a href="@@P@@privacy-policy.html">Privacy Policy</a>
        <a href="@@P@@terms-conditions.html">Terms &amp; Conditions</a>
        <a href="@@P@@refund-policy.html">Refund &amp; Cancellation Policy</a>
        <a href="@@P@@faqs.html">FAQs</a>
      </nav>

    </div>

    <div class="cc-foot-bottom">
      <span>&copy; 2026 Chamunda Cab, Rajkot, Gujarat. Fares shown are indicative and confirmed at booking.</span>
    </div>
  </div>
</footer>
'''

def footer(pf):
    top = ["rajkot-to-ahmedabad-taxi","ahmedabad-to-rajkot-taxi","rajkot-to-ahmedabad-airport-taxi","rajkot-to-jamnagar-taxi","rajkot-to-dwarka-taxi","rajkot-to-somnath-taxi","rajkot-to-surat-taxi","rajkot-to-vadodara-taxi"]
    links = "".join('<a href="%sroutes/%s.html">%s</a>' % (pf,s,e(pairs[s]["o"]+" to "+pairs[s]["d"]+" Taxi")) for s in top)
    return TPL_FOOTER.replace('@@P@@',pf).replace('@@LINKS@@',links) + '''
<div class="floating-cta" role="group" aria-label="Quick contact"><a href="https://wa.me/916352179909?text=Hello%%20Chamunda%%20Cab%%2C%%20I%%20want%%20to%%20book%%20a%%20taxi." target="_blank" rel="noopener" class="floating-cta__btn floating-cta__btn--wa" aria-label="Chat on WhatsApp"><i class="fab fa-whatsapp" aria-hidden="true"></i></a><a href="tel:%(bn)s" class="floating-cta__btn floating-cta__btn--call" aria-label="Call +91 81282 95920"><i class="bi bi-telephone-fill" aria-hidden="true"></i></a></div>''' % dict(p=pf,bn=BOOK_NUM,wn=WA_NUM,links=links)

def biz_schema(pf_url=""):
    return {"@context":"https://schema.org","@type":["TaxiService","LocalBusiness"],"@id":DOMAIN+"/#business","name":BRAND,
      "alternateName":["Chamunda Cab Rajkot","Chamunda Taxi Rajkot"],"url":DOMAIN+"/","image":DOMAIN+"/images/hero.jpg",
      "telephone":["+918128295920","+916352179909"],"priceRange":"\u20b9\u20b9",
      "description":"Taxi and cab service in Rajkot, Gujarat for one-way, round-trip, local and airport transfers across Gujarat and India.",
      "address":{"@type":"PostalAddress","addressLocality":"Rajkot","addressRegion":"Gujarat","addressCountry":"IN"},
      "geo":{"@type":"GeoCoordinates","latitude":22.3039,"longitude":70.8022},
      "openingHoursSpecification":{"@type":"OpeningHoursSpecification","dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],"opens":"00:00","closes":"23:59"},
      "areaServed":[{"@type":"State","name":"Gujarat"}]+[{"@type":"City","name":c} for c in ["Rajkot","Ahmedabad","Surat","Vadodara","Jamnagar","Junagadh","Bhavnagar","Gandhinagar","Morbi","Porbandar","Dwarka","Somnath","Bhuj"]],
      "contactPoint":[{"@type":"ContactPoint","telephone":"+918128295920","contactType":"reservations","areaServed":"IN","availableLanguage":["en","hi","gu"]},
                      {"@type":"ContactPoint","telephone":"+916352179909","contactType":"customer support","contactOption":"WhatsApp","areaServed":"IN","availableLanguage":["en","hi","gu"]}]}

def faq_schema(qas):
    return {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in qas]}
def crumb_schema(items):
    return {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":i+1,"name":n,"item":DOMAIN+"/"+u} for i,(n,u) in enumerate(items)]}

def faq_html(qas):
    return '<div class="faq">' + "".join('<details><summary>%s</summary><p>%s</p></details>' % (e(q),e(a)) for q,a in qas) + '</div>'

def page(pf, title, desc, path, kw, body, schema, crumbs=None):
    return head(pf,title,desc,path,kw,schema) + "\n</head>\n<body>\n" + nav(pf) + "\n<main id=\"top\">\n" + body + "\n</main>\n" + footer(pf) + \
      '\n<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>\n</body>\n</html>\n'

def cta_btns(text):
    return '<a href="tel:%s" class="btn btn-call"><i class="bi bi-telephone-fill me-2"></i>Call 8128295920</a> <a href="%s" target="_blank" rel="noopener" class="btn btn-wa"><i class="fab fa-whatsapp me-2"></i>WhatsApp 6352179909</a>' % (BOOK_NUM, wa(text))

# ---------- route page ----------
INTRO = [
 "Looking for a reliable {o} to {d} taxi? Chamunda Cab runs clean, air-conditioned cabs with verified local drivers between {o} and {d}, available 24x7 for one-way drops and round trips.",
 "Book a {o} {d} cab with fixed, transparent pricing. Whether you need a quick one-way drop or a return journey, our chauffeur-driven taxis cover the {km} km between {o} and {d} comfortably.",
 "Chamunda Cab offers dependable {o} to {d} cab service for families, business travellers and pilgrims. Pick your car, share your pickup point, and we confirm a fixed fare on call or WhatsApp.",
]
def route_page(p):
    o,d,km = p["o"],p["d"],p["km"]
    F = fares(km); lo = F[0][3]; rt = F[0][4]
    kindtxt = "airport transfer" if p["kind"]=="airport" else "outstation trip"
    title = "%s to %s Taxi & Cab | One-Way from %s | Chamunda Cab" % (o,d,inr(lo))
    desc = "%s to %s taxi & cab: one-way from %s, round trip from %s. %d km, about %s hrs. AC Dzire, Ertiga, Innova. Call 8128295920." % (o,d,inr(lo),inr(rt),km,p["hrs"])
    kw = ", ".join([f"{o} to {d} taxi",f"{o} to {d} cab",f"{o} {d} taxi",f"{o} {d} cab",f"{o} to {d} one way taxi",f"{o} to {d} round trip cab",f"{o} to {d} taxi fare",f"{o} to {d} cab booking",f"{d} to {o} taxi",f"{d} to {o} cab","Chamunda Cab"])
    rev = pairs.get("%s-to-%s-taxi" % (slug(d),slug(o)))
    intro = INTRO[sum(map(ord,p["slug"]))%3].format(o=o,d=d,km=km)
    qas = [
     ("What is the %s to %s taxi fare?" % (o,d), "Indicative one-way fare is from %s in a sedan and from %s in an Ertiga for about %d km. A round trip starts around %s. Chamunda Cab confirms a final fixed fare on call (8128295920) or WhatsApp (6352179909)." % (inr(F[0][3]),inr(F[1][3]),km,inr(rt))),
     ("How long does the %s to %s cab take?" % (o,d), "The drive is about %d km via %s and usually takes %s hours depending on traffic and stops." % (km,p["via"],p["hrs"])),
     ("Do you offer one-way and round-trip cabs from %s to %s?" % (o,d), "Yes. You can book a one-way drop, a same-day return, or a multi-day round trip. Tell us your dates and waiting needs and we quote accordingly."),
     ("How do I book a %s to %s taxi?" % (o,d), "Call 8128295920 or WhatsApp 6352179909 with pickup address, date, time and passenger count. You can also use the online booking form on this website."),
    ]
    if p["kind"]=="airport":
        qas.append(("Will the driver track my flight?","Share your flight number and timing on WhatsApp so the driver can plan the pickup or drop with a safe buffer."))
    related = [pairs[s] for s in pairs if pairs[s]["o"]==o and s!=p["slug"]][:8]
    related += [pairs[s] for s in pairs if pairs[s]["d"]==d and pairs[s]["o"]!=o and pairs[s]["o"] in ("Rajkot","Ahmedabad")][:4]
    chips = "".join('<a href="%s.html">%s to %s taxi</a>' % (r["slug"],e(r["o"]),e(r["d"])) for r in ([rev] if rev else [])+related if r)
    rows = "".join('<tr><td data-label="Vehicle" class="col-veh"><span class="veh-name">%s</span></td><td data-label="Seating">%s</td><td data-label="Rate" class="rt">%s/km</td><td data-label="One-way" class="rt">%s</td><td data-label="Round trip" class="rt">%s</td></tr>' % (e(n),s,inr(r),inr(a),inr(b)) for n,s,r,a,b in F)
    body = '''<div class="page-head"><div class="container">
  <nav class="crumbs" aria-label="breadcrumb"><a href="../index.html">Home</a> / <a href="../routes.html">Routes</a> / %(o)s to %(d)s</nav>
  <h1>%(o)s to %(d)s Taxi &amp; Cab Service</h1>
  <p>One-way and round-trip %(o)s %(d)s cab from %(lo)s. %(km)d km &middot; about %(h)s hrs &middot; AC cars &middot; 24x7 booking.</p>
  <div class="d-flex gap-2 justify-content-center flex-wrap mt-3">%(cta)s</div>
</div></div>
<section><div class="container">
  <div class="row g-3 mb-4">
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-signpost-split"></i><h3>%(km)d km</h3><span>Approx. distance</span></div></div>
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-clock"></i><h3>%(h)s hrs</h3><span>Approx. travel time</span></div></div>
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-currency-rupee"></i><h3>%(lo)s</h3><span>One-way from</span></div></div>
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-arrow-repeat"></i><h3>%(rt)s</h3><span>Round trip from</span></div></div>
  </div>
  <h2 class="sec-title">%(o)s to %(d)s taxi fare &amp; cab rates</h2>
  <p class="sec-sub">Indicative fares calculated from our per-km rate card for about %(km)d km. Tolls, parking and state taxes are confirmed at booking.</p>
  <div class="rate-card"><div class="table-responsive"><table class="table rate-table align-middle mb-0"><thead><tr><th>Vehicle</th><th>Seating</th><th>Rate</th><th>One-way</th><th>Round trip</th></tr></thead><tbody>%(rows)s</tbody></table></div></div>
  <div class="row g-4 mt-4">
    <div class="col-lg-7"><h2 class="sec-title" style="font-size:1.6rem">Book a %(o)s %(d)s cab with Chamunda Cab</h2>
      <p class="sec-sub" style="max-width:none">%(intro)s</p>
      <p class="sec-sub" style="max-width:none">Route: %(via)s. About %(d)s: %(note)s. This %(kt)s is suitable for solo riders, couples, families and groups; pick a sedan for 1-4 passengers, Ertiga or Innova for 5-7, and Tempo Traveller for larger groups.</p>
      <ul class="tick"><li>Clean, sanitized AC cabs and experienced Gujarati &amp; Hindi speaking drivers</li><li>Fixed fare confirmed before travel, no hidden surge</li><li>On-time pickup, available day and night</li><li>One-way drop, round trip and multi-day packages</li></ul></div>
    <div class="col-lg-5"><div class="cta-band h-100 d-flex flex-column justify-content-center"><h3 class="serif">Book %(o)s to %(d)s now</h3><p>Call or WhatsApp with pickup point, date and passengers.</p><div class="d-flex flex-column gap-2">%(cta)s<a class="btn btn-amber" href="../booking.html">Online booking form</a></div></div></div>
  </div>
</div></section>
<section><div class="container"><h2 class="sec-title">%(o)s to %(d)s taxi FAQs</h2>%(faq)s</div></section>
<section><div class="container"><h2 class="sec-title" style="font-size:1.6rem">More taxi &amp; cab routes</h2><div class="chips">%(chips)s</div></div></section>''' % dict(o=e(o),d=e(d),km=km,h=p["hrs"],lo=inr(lo),rt=inr(rt),rows=rows,intro=e(intro),via=e(p["via"]),note=e(p["note"]),kt=kindtxt,faq=faq_html(qas),chips=chips,cta=cta_btns("Hello Chamunda Cab, I need a taxi from %s to %s." % (o,d)))
    sch = [biz_schema(), crumb_schema([("Home","index.html"),("Routes","routes.html"),("%s to %s Taxi"%(o,d),"routes/%s.html"%p["slug"])]), faq_schema(qas),
      {"@context":"https://schema.org","@type":"Service","serviceType":"Taxi and cab service","name":"%s to %s taxi & cab"%(o,d),"provider":{"@id":DOMAIN+"/#business"},"areaServed":["%s"%o,"%s"%d],
       "offers":{"@type":"Offer","priceCurrency":"INR","price":str(lo),"description":"Indicative one-way sedan fare; final fixed fare confirmed at booking"}}]
    return page("../",title,desc,"routes/%s.html"%p["slug"],kw,body,sch)

# ---------- local / info pages ----------
def local_pages():
    out = {}
    S = {
     "rajkot-railway-station-taxi": ("Rajkot Railway Station Taxi & Cab | 24x7 Pickup | Chamunda Cab","Taxi and cab pickup or drop at Rajkot Junction railway station, any time. Local and outstation. Call 8128295920.","Rajkot railway station taxi, Rajkot junction cab, Rajkot station cab booking",
      "Rajkot Railway Station Taxi &amp; Cab","Pre-book a driver at Rajkot Junction or arrange a late-night pickup.",
      ["Meet-and-greet style pickup; share your train number on WhatsApp.","Transfers to hotels, bus stand and Hirasar airport.","Direct outstation drops to Ahmedabad, Jamnagar, Junagadh, Somnath and Dwarka."]),
     "rajkot-sightseeing-taxi": ("Rajkot Sightseeing Taxi & Cab | City Tour | Chamunda Cab","Rajkot sightseeing taxi and cab: Watson Museum, Kaba Gandhi No Delo, Race Course, Lalpari Lake. Call 8128295920.","Rajkot sightseeing taxi, Rajkot city tour cab, Rajkot tourist taxi",
      "Rajkot Sightseeing Taxi &amp; Cab","Half-day and full-day city tours.",
      ["Watson Museum and Lang Library","Kaba Gandhi No Delo (Mahatma Gandhi's childhood home)","Race Course Ring Road and Rajkumar College","Lalpari and Randarda lakes, Swaminarayan Temple","Extend to Gondal Palace or Jamnagar as a day trip."]),
     "one-way-taxi-gujarat": ("One-Way Taxi & Cab in Gujarat | Rajkot & Ahmedabad | Chamunda Cab","One-way taxi and cab in Gujarat from Rajkot and Ahmedabad. Pay for one side only. Fixed fares. Call 8128295920.","one way taxi Gujarat, one way cab Rajkot, Rajkot one way drop taxi, Ahmedabad one way cab",
      "One-Way Taxi &amp; Cab in Gujarat","Pay only for the one-way distance on intercity drops.",
      ["Rajkot to Ahmedabad, Jamnagar, Surat, Vadodara, Bhavnagar, Junagadh one-way drops.","Ahmedabad to Rajkot, Surat, Vadodara, Udaipur, Mount Abu one-way cabs.","Airport one-way drops at Ahmedabad, Rajkot, Jamnagar and Surat."]),
     "round-trip-cab-gujarat": ("Round Trip Taxi & Cab in Gujarat | Outstation | Chamunda Cab","Round trip taxi and cab from Rajkot and Ahmedabad: pilgrimage, family and business trips. Call 8128295920.","round trip taxi Gujarat, round trip cab Rajkot, outstation cab Rajkot, Rajkot to Dwarka Somnath round trip cab",
      "Round Trip Taxi &amp; Cab in Gujarat","Return journeys and multi-day outstation packages.",
      ["Dwarka-Somnath-Sasan Gir circuits from Rajkot.","Rajkot-Ahmedabad-Udaipur-Mount Abu family tours.","Business round trips with waiting time; multi-day halt terms confirmed at booking."]),
    }
    for sl,(t,dsc,kw,h1,sub,pts) in S.items():
        qas=[("How can I book a %s?"%t.split("|")[0].strip().lower(),"Call 8128295920 or WhatsApp 6352179909 with your pickup, date and time."),("Is the service available at night?","Yes, Chamunda Cab accepts bookings 24 hours a day, 7 days a week."),("Are fares fixed?","We confirm a fixed fare before the trip; tolls, parking and state taxes are clarified at booking.")]
        hero_cta = '<div class="hero-cta"><a href="../booking.html#booking" class="btn-book-cta" aria-label="Book in seconds - go to the cab booking form">Book in seconds<i class="bi bi-arrow-right ms-2"></i></a></div>' if False else ""
        lis = "".join("<li>%s</li>"%x for x in pts)
        chips = "".join('<a href="%s.html">%s to %s taxi</a>'%(p["slug"],e(p["o"]),e(p["d"])) for p in list(pairs.values())[:0])
        pop = ["rajkot-to-ahmedabad-taxi","rajkot-to-ahmedabad-airport-taxi","rajkot-to-jamnagar-taxi","rajkot-to-junagadh-taxi","rajkot-to-somnath-taxi","rajkot-to-dwarka-taxi","rajkot-to-surat-taxi","rajkot-to-vadodara-taxi"]
        chips = "".join('<a href="%s.html">%s to %s taxi &amp; cab</a>'%(s,e(pairs[s]["o"]),e(pairs[s]["d"])) for s in pop)
        body = '''<div class="page-head"><div class="container"><nav class="crumbs"><a href="../index.html">Home</a> / <a href="../routes.html">Routes</a> / %s</nav><h1>%s</h1>%s<p>%s Call 8128295920 or WhatsApp 6352179909.</p><div class="d-flex gap-2 justify-content-center flex-wrap mt-3">%s</div></div></div>
<section><div class="container"><h2 class="sec-title">What we offer</h2><ul class="tick">%s</ul>
<div class="rate-card mt-4"><div class="table-responsive"><table class="table rate-table align-middle mb-0"><thead><tr><th>Vehicle</th><th>Seating</th><th>Rate per km</th></tr></thead><tbody>%s</tbody></table></div></div></div></section>
<section><div class="container"><h2 class="sec-title">FAQs</h2>%s</div></section>
<section><div class="container"><h2 class="sec-title" style="font-size:1.6rem">Popular outstation taxi routes</h2><div class="chips">%s</div></div></section>''' % (h1,h1,hero_cta,sub,cta_btns("Hello Chamunda Cab, I need a taxi. "+t.split("|")[0]),lis,"".join('<tr><td data-label="Vehicle" class="col-veh"><span class="veh-name">%s</span></td><td data-label="Seating">%s</td><td data-label="Rate" class="rt">%s/km</td></tr>'%(e(n),s,inr(r)) for n,s,r in VEH),faq_html(qas),chips)
        if hero_cta: body = body.replace('<div class="page-head">','<div class="page-head hero-compact">',1)
        out[sl]=page("../",t,dsc,"routes/%s.html"%sl,kw,body,[biz_schema(),crumb_schema([("Home","index.html"),("Routes","routes.html"),(t.split("|")[0].strip(),"routes/%s.html"%sl)]),faq_schema(qas)])
    return out

def directory():
    def grp(title, filt):
        items = [p for p in pairs.values() if filt(p)]
        return '<h2 class="sec-title" style="font-size:1.5rem;margin-top:36px">%s</h2><div class="chips">%s</div>' % (title,"".join('<a href="routes/%s.html">%s to %s taxi</a>'%(p["slug"],e(p["o"]),e(p["d"])) for p in items))
    body = '''<div class="page-head"><div class="container">
  <h1>Chamunda Cab Routes</h1>
  <div class="hero-cta"><a href="%(p)sbooking.html#booking" class="btn-book-cta" aria-label="Book in seconds - go to the cab booking form">Book in seconds<i class="bi bi-arrow-right ms-2"></i></a></div>
  <p>Explore 220+ One-Way, Round-Trip &amp; Airport Taxi Routes from Rajkot &amp; Ahmedabad. <strong style="color:var(--gold);font-weight:800">Instant Call &amp; WhatsApp Booking</strong> with professional drivers, and <strong style="color:var(--gold);font-weight:800">24/7 support</strong>.</p>
  <div class="d-flex gap-2 justify-content-center flex-wrap mt-3">
    <a href="tel:+918128295920" class="btn btn-call"><i class="bi bi-telephone-fill me-2"></i>Call +91 81282 95920</a>
    <a href="https://wa.me/916352179909?text=Hello%%20Chamunda%%20Cab%%2C%%20I%%20want%%20to%%20book%%20a%%20taxi." target="_blank" rel="noopener" class="btn btn-wa"><i class="fab fa-whatsapp me-2"></i>WhatsApp Booking</a>
  </div>
</div></div>
<section class="routes-sec"><div class="container">%s%s%s%s%s%s<h2 class="sec-title" style="font-size:1.5rem;margin-top:36px">Local &amp; service pages</h2><div class="chips">%s</div></div></section>''' % (
      grp("Rajkot to other cities - taxi &amp; cab",lambda p:p["o"]=="Rajkot" and p["kind"]=="oneway"),
      grp("Other cities to Rajkot - taxi &amp; cab",lambda p:p["d"]=="Rajkot" and p["kind"]=="oneway"),
      grp("Ahmedabad taxi &amp; cab routes",lambda p:p["o"]=="Ahmedabad"),
      grp("To Ahmedabad - taxi &amp; cab",lambda p:p["d"]=="Ahmedabad" and p["o"]!="Rajkot"),
      grp("Airport taxi &amp; cab",lambda p:p["kind"]=="airport"),"",
      "".join('<a href="routes/%s.html">%s</a>'%(s,e(t)) for s,t,_ in LOCAL))
    t="All Gujarat Taxi & Cab Routes | Rajkot, Ahmedabad, Airport | Chamunda Cab"
    d="Complete list of Rajkot and Ahmedabad taxi and cab routes: one-way, round trip, local and airport transfers across Gujarat. Call 8128295920."
    return page("",t,d,"routes.html","Rajkot taxi routes, Gujarat cab routes, Rajkot to Ahmedabad taxi, airport cab Gujarat",body,[biz_schema(),crumb_schema([("Home","index.html"),("Routes","routes.html")])])

# ---------- index ----------
def index_page():
    fleet_js = open(os.path.join("src","fleet-data.js"),encoding="utf8").read()
    fl = re.findall(r"name:'([^']+)', seats:'([^']+)', rate:'([^']+)'", fleet_js)
    frows = "".join('<tr><td data-label="Vehicle" class="col-veh"><span class="veh-name">%s</span></td><td data-label="Seating">%s</td><td data-label="Rate" class="rt">\u20b9%s/km</td></tr>'%(e(n),s,r) for n,s,r in fl)
    pop = ["rajkot-to-ahmedabad-taxi","rajkot-to-ahmedabad-airport-taxi","rajkot-to-rajkot-airport-taxi","rajkot-to-jamnagar-taxi","rajkot-to-junagadh-taxi","rajkot-to-somnath-taxi","rajkot-to-dwarka-taxi","rajkot-to-surat-taxi","rajkot-to-vadodara-taxi","rajkot-to-bhavnagar-taxi","rajkot-to-porbandar-taxi","rajkot-to-bhuj-taxi"]
    cards = ""
    for s in pop:
        p = pairs[s]; F = fares(p["km"])
        cards += '<div class="col-md-6 col-xl-4"><div class="route"><div class="d-flex justify-content-between align-items-center"><span class="tag">%s</span><span class="km">~%d km</span></div><h4>%s to %s Taxi &amp; Cab</h4><p>%s</p><div class="fares"><div><span>Sedan one-way</span><b>%s approx.</b></div><div><span>Ertiga / SUV one-way</span><b>%s approx.</b></div></div><a href="routes/%s.html" class="btn btn-amber mt-3">View fare &amp; book</a></div></div>' % ("Airport" if p["kind"]=="airport" else "One-Way",p["km"],e(p["o"]),e(p["d"]),e(p["note"]),inr(F[0][3]),inr(F[1][3]),s)
    def chips(f,n=999):
        return "".join('<a href="routes/%s.html">%s to %s taxi</a>'%(p["slug"],e(p["o"]),e(p["d"])) for p in [p for p in pairs.values() if f(p)][:n])
    air = chips(lambda p:p["kind"]=="airport" and p["o"] in ("Rajkot","Ahmedabad Airport") ,40)
    svc = [("arrow-right","One-Way Taxi","Pay only one side on intercity drops across Gujarat.","routes/one-way-taxi-gujarat.html"),
           ("diagram-2","Round Trip Cab","Outstation and multi-day round trips with courteous drivers.","routes/round-trip-cab-gujarat.html"),
           ("bank","Dwarka-Somnath Yatra","Pilgrimage packages with drivers who know temple timings.","routes/rajkot-to-dwarka-taxi.html"),
           ("briefcase","Corporate Cab","GST invoices and monthly billing for business travel.","booking.html"),
           ("heart","Wedding Car Rental","Decorated sedans and fleets for baraat and guests.","booking.html"),
           ("globe","All India Tours","Commercial permits for Rajasthan, Maharashtra, MP and North India.","routes/rajkot-to-udaipur-taxi.html")]
    svch = "".join('<div class="col-sm-6 col-lg-3"><a class="svc d-block text-decoration-none text-reset" href="%s"><div class="ico"><i class="bi bi-%s"></i></div><h5>%s</h5><p>%s</p></a></div>'%(u,i,t,d) for i,t,d,u in svc)
    qas = [("What is the Rajkot to Ahmedabad taxi fare?","A sedan one-way Rajkot to Ahmedabad taxi starts around %s for about 215 km; an Ertiga starts around %s. Final fixed fare is confirmed on call."%(inr(fares(215)[0][3]),inr(fares(215)[1][3]))),
           ("How can I book a Rajkot to Ahmedabad airport cab?","Call 8128295920 or WhatsApp 6352179909 with flight time and pickup point. Rajkot to Ahmedabad airport taxi starts around %s."%inr(fares(225)[0][3])),
           ("Do you provide Rajkot to Rajkot airport taxi?","Yes. Rajkot city to Hirasar airport (about 35 km) and airport to city pickups are available 24x7."),
           ("Do you offer one-way and round-trip cabs?","Yes. Book one-way drops from Rajkot and Ahmedabad, or round trips and multi-day outstation packages."),
           ("Which Gujarat cities do you cover?","Ahmedabad, Surat, Vadodara, Jamnagar, Junagadh, Bhavnagar, Gandhinagar, Morbi, Porbandar, Dwarka, Somnath, Bhuj, Gandhidham, Mehsana, Anand and more, plus Mumbai, Udaipur and Mount Abu."),
           ("What are your contact numbers?","Booking: 8128295920. WhatsApp: 6352179909. Available 24 hours.")]
    title = "Rajkot Taxi & Cab Service | Rajkot to Ahmedabad Taxi, Airport Cab | Chamunda Cab"
    desc = "Chamunda Cab: Rajkot taxi & cab for one-way, round trip, local & airport drops. Rajkot to Ahmedabad taxi, Jamnagar, Surat, Dwarka, Somnath. Call 8128295920."
    kw = "Rajkot taxi, Rajkot cab, Rajkot to Ahmedabad taxi, Rajkot Ahmedabad cab, Rajkot to Rajkot airport taxi, Rajkot to Ahmedabad airport cab, outstation cab Rajkot, one way taxi Rajkot, Rajkot local taxi, Gujarat taxi service, Chamunda Cab"
    sch = [biz_schema(), faq_schema(qas), {"@context":"https://schema.org","@type":"WebSite","name":BRAND,"url":DOMAIN+"/"}]
    src = open(os.path.join("src","index.html"),encoding="utf8").read()
    _i = src.index("<script>\n$('html')"); script = src[_i:src.index("</script>", _i)]
    # strip data-driven route/service rendering (now static)
    script = re.sub(r"  /\* ---------- Data ---------- \*/.*?  /\* Featured vehicles", "  /* Featured vehicles", script, flags=re.S)
    script = re.sub(r"\$\('#routeGrid'\)\.html\(.*?\n  \}\)\.join\(''\)\);\n\n", "", script, flags=re.S)
    script = re.sub(r"\n  \$\('#svcGrid'\)\.html\(.*?\}\)\.join\(''\)\);\n", "\n", script, flags=re.S)
    script = script.replace("var featured = $.grep","var chat = '<i class=\"fab fa-whatsapp me-2\"></i>';\n  var featured = $.grep",1) if "var chat" not in script else script
    script = re.sub(r"  var svcs = \[.*?\n  \];\n", "", script, flags=re.S)
    script += "</script>"
    body = '''<section class="hero"><div class="container">
  <h1>Rajkot Taxi &amp; Cab Service<br>One-Way, Round Trip, Local &amp; Airport</h1>
  <div class="hero-cta"><a href="%(p)sbooking.html#booking" class="btn-book-cta" aria-label="Book in seconds - go to the cab booking form">Book in seconds<i class="bi bi-arrow-right ms-2"></i></a></div>
  <p>Rajkot to Ahmedabad taxi, airport cab and outstation trips across Gujarat. Fixed fares, punctual drivers, Available 24/7.</p>
  <div class="d-flex gap-2 justify-content-center flex-wrap mb-4">%(cta)s</div>
  <div class="hero-card"><div class="hero-cap"><span class="pill">Your ride, our responsibility</span><p>Verified local drivers for airport transfers, one-way drops, round trips and pilgrimage tours.</p></div></div>
  <div class="row g-3 mt-4">
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-shield-check"></i><h3>100%%</h3><span>Pickup guarantee</span></div></div>
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-currency-rupee"></i><h3>Fixed Rate</h3><span>No hidden surge</span></div></div>
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-stars"></i><h3>Sanitized</h3><span>Spotless fleet</span></div></div>
    <div class="col-6 col-lg-3"><div class="stat"><i class="bi bi-clock"></i><h3>24 / 7</h3><span>Driver dispatch</span></div></div>
  </div></div></section>
<section id="routes"><div class="container">
  <div class="text-center mb-5"><h2 class="sec-title">Popular Routes</h2><p class="sec-sub mx-auto">Rajkot to Ahmedabad taxi, Rajkot Ahmedabad cab, airport drops and pilgrimage routes at indicative fixed fares.</p></div>
  <div class="row g-4" id="routeGrid">%(cards)s</div>
  <div class="text-center mt-5"><a href="routes.html" class="btn btn-amber">See all %(n)d taxi &amp; cab routes</a></div>
</div></section>
<section id="airport"><div class="container"><h2 class="sec-title">Airport Taxi &amp; Cab in Gujarat</h2><p class="sec-sub mb-4">Rajkot to Rajkot airport taxi, Rajkot to Ahmedabad airport cab, and airport transfers for Jamnagar, Surat, Vadodara, Bhavnagar and more.</p><div class="chips">%(air)s</div></div></section>
<section id="tours" class="tp-sec"><div class="container">
  <div class="tp-card">
    <span class="tp-eyebrow"><i class="bi bi-compass-fill" aria-hidden="true"></i>Tour Packages</span>
    <h2 class="sec-title tp-title">Customized Tour &amp; Holiday Packages Across India</h2>
    <p class="tp-desc">Planning a family vacation, pilgrimage, or group trip? Get customized all-inclusive cab packages with flexible itineraries, experienced drivers, and fixed transparent pricing.</p>
    <ul class="tp-badges">
      <li><i class="bi bi-bank2" aria-hidden="true"></i>Temple &amp; Pilgrimage Tours</li>
      <li><i class="bi bi-tree-fill" aria-hidden="true"></i>Hill Station &amp; Holiday Trips</li>
      <li><i class="bi bi-people-fill" aria-hidden="true"></i>Customized Family &amp; Group Packages</li>
    </ul>
    <div class="tp-actions">
      <a href="https://wa.me/916352179909?text=Hello%%20Chamunda%%20Cab%%2C%%20I%%20want%%20to%%20inquire%%20about%%20a%%20tour%%20package." target="_blank" rel="noopener noreferrer" class="btn btn-wa"><i class="fab fa-whatsapp me-2" aria-hidden="true"></i>Inquire Tour Package on WhatsApp</a>
      <a href="tel:+918128295920" class="btn btn-call"><i class="bi bi-telephone-fill me-2" aria-hidden="true"></i>Call for Custom Plan</a>
    </div>
  </div>
</div></section>
<section id="fleet"><div class="container">
  <div class="text-center mb-5"><h2 class="sec-title">Our Taxi &amp; Cab Fleet and Rates</h2><p class="sec-sub mx-auto">Air-conditioned, sanitized vehicles with courteous local chauffeurs.</p></div>
  <div class="fleet-carousel" id="fleetCarousel" role="region" aria-roledescription="carousel" aria-label="Our taxi and cab fleet">
    <div class="fc-viewport"><div class="fc-track" id="fleetGrid"></div></div>
    <div class="fc-controls">
      <button type="button" class="fc-btn fc-prev" aria-label="Previous vehicles"><i class="bi bi-chevron-left"></i></button>
      <div class="fc-dots" id="fleetDots"></div>
      <button type="button" class="fc-btn fc-next" aria-label="Next vehicles"><i class="bi bi-chevron-right"></i></button>
    </div>
  </div>
  <div class="rate-card mt-5"><div class="table-responsive"><table class="table rate-table align-middle mb-0"><thead><tr><th>Vehicle</th><th>Seating</th><th>Rate</th></tr></thead><tbody>%(frows)s</tbody></table></div></div>
  <div class="text-center mt-4"><a href="fleet.html" class="btn btn-amber">View all vehicles &amp; rates</a></div>
</div></section>
<section id="services"><div class="container"><div class="text-center mb-5"><h2 class="sec-title">Our Cab Services</h2><p class="sec-sub mx-auto">Ground transport for individuals, corporates and tourist groups.</p></div><div class="row g-4" id="svcGrid">%(svch)s</div></div></section>
<section id="cities"><div class="container"><h2 class="sec-title">Taxi &amp; Cab from Rajkot to Every Major Gujarat City</h2><p class="sec-sub mb-4">Tap a route for distance, travel time and fares.</p><div class="chips">%(rchips)s</div>
  <h2 class="sec-title mt-5" style="font-size:1.6rem">Ahmedabad Taxi &amp; Cab Routes</h2><div class="chips">%(achips)s</div></div></section>
<section id="why" class="why"><div class="container"><div class="row g-5 align-items-center">
  <div class="col-lg-6"><span class="eyebrow">Why riders choose us</span><h2>On-Time Pickups. No Last-Minute Cancellations.</h2>
  <p class="lead2">Chamunda Cab has served Gujarati families, tourists and corporate travellers with honest pricing. Your cab arrives on time with a clean cabin and a verified driver.</p>
  <div class="check"><i class="bi bi-check-lg"></i><div><b>Clean &amp; Sanitized Interiors</b><span>Washed and vacuumed before every outstation trip.</span></div></div>
  <div class="check"><i class="bi bi-check-lg"></i><div><b>Experienced Local Chauffeurs</b><span>Gujarati and Hindi speaking drivers who know the highways.</span></div></div>
  <div class="check"><i class="bi bi-check-lg"></i><div><b>24/7 Human Support</b><span>Call 8128295920 or WhatsApp 6352179909 any time.</span></div></div></div>
  <div class="col-lg-6"><h2 class="sec-title" style="font-size:1.6rem">Frequently asked questions</h2>%(faq)s</div>
</div></div></section>''' % dict(cta=cta_btns("Hello Chamunda Cab, I want to book a taxi."),cards=cards,n=len(pairs),air=air,frows=frows,svch=svch,
      rchips=chips(lambda p:p["o"]=="Rajkot" and p["kind"]=="oneway"),achips=chips(lambda p:p["o"]=="Ahmedabad"),faq=faq_html(qas))
    return head("",title,desc,"index.html",kw,sch) + '\n<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>\n<script src="fleet-data.js"></script>\n</head>\n<body>\n' + nav("") + '\n<main id="top">\n' + body + '\n</main>\n' + footer("") + '\n<div id="progress"></div>\n<button id="toTop" type="button" aria-label="Back to top"><i class="bi bi-arrow-up"></i></button>\n' + script.replace("$('#mainNav').collapse('toggle')","void 0") + '\n<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>\n</body>\n</html>\n'

# ---------- patch booking/fleet ----------
def patch(name, title, desc, kw, extra=None):
    s = open(os.path.join("src",name),encoding="utf8").read()
    h = head("",title,desc,name,kw,[biz_schema()]+(extra or []))
    if name=="about.html": h = h.replace('<link href="style.css" rel="stylesheet">','<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Gujarati:wght@400;600;700&display=swap" rel="stylesheet">\n<link href="style.css" rel="stylesheet">')
    # replace head block up to stylesheet/script tags: keep original script/link lines for jquery/fleet-data
    keep = "\n".join(l for l in re.findall(r"<script src=[^>]+></script>", s.split("</head>")[0]))
    s = re.sub(r"<!DOCTYPE html>.*?</head>", lambda m: h + "\n" + keep + "\n</head>", s, count=1, flags=re.S)
    s = re.sub(r"<nav class=\"site-nav.*?</nav>", lambda m: nav("").replace('class="nav-link" href="booking.html"','class="nav-link%s" href="booking.html"' % (" active" if name=="booking.html" else "")).replace('class="nav-link" href="fleet.html"','class="nav-link%s" href="fleet.html"' % (" active" if name=="fleet.html" else "")).replace('class="nav-link" href="about.html"','class="nav-link%s" href="about.html"' % (" active" if name=="about.html" else "")), s, count=1, flags=re.S)
    s = re.sub(r"<footer>.*?</footer>", lambda m: footer(""), s, count=1, flags=re.S)
    s = s.replace("tel:818295920","tel:+918128295920").replace("tel:+916352179909","tel:+918128295920")
    s = s.replace("$('#menuToggle').on('click', function () { $('#mainNav').collapse('toggle'); });","")
    return s

# ---------- write ----------
if os.path.exists(OUT): shutil.rmtree(OUT)
shutil.copytree("src",OUT)
os.makedirs(OUT+"/routes")
open(OUT+"/index.html","w",encoding="utf8").write(index_page())
open(OUT+"/booking.html","w",encoding="utf8").write(patch("booking.html","Cab Booking | Book Taxi & Cab in Rajkot Online | Chamunda Cab","Book a taxi or cab online from Rajkot: one-way, round trip, local and airport. Booking 8128295920, WhatsApp 6352179909.","book cab Rajkot, Rajkot taxi booking, Rajkot cab booking online"))
open(OUT+"/fleet.html","w",encoding="utf8").write(patch("fleet.html","Taxi & Cab Fleet and Rate Card | Rajkot | Chamunda Cab","Chamunda Cab fleet and per-km rates: WagonR, Dzire, Ertiga, Innova, Crysta, Tempo Traveller, Urbania. Call 8128295920.","Rajkot cab rates, taxi per km rate Rajkot, Innova rental Rajkot, tempo traveller Rajkot"))
open(OUT+"/about.html","w",encoding="utf8").write(patch("about.html",'About Us | Chamunda Cab Tourism, Rajkot | Safe Taxi & Cab Service in Gujarat','About Chamunda Cab Tourism, Rajkot: 24/7 taxi and cab service with experienced drivers, sanitized AC cars (Sedan, SUV, Innova Crysta) and fixed fares. Call 8128295920.','about Chamunda Cab, Chamunda Cab Tourism Rajkot, taxi service Rajkot, trusted cab service Gujarat, Rajkot cab company',[{'@context': 'https://schema.org', '@type': 'AboutPage', 'name': 'About Chamunda Cab Tourism', 'url': 'https://www.chamundacab.in/about.html', 'about': {'@id': 'https://www.chamundacab.in/#business'}}]))
open(OUT+"/routes.html","w",encoding="utf8").write(directory().replace("<body>","<body class=\"routes-page\">",1))
for p in pairs.values(): open(OUT+"/routes/%s.html"%p["slug"],"w",encoding="utf8").write(route_page(p))
for sl,h in local_pages().items(): open(OUT+"/routes/%s.html"%sl,"w",encoding="utf8").write(h)
# sitemap, robots
urls = ["index.html","routes.html","booking.html","fleet.html","about.html","terms-conditions.html","privacy-policy.html","refund-policy.html","faqs.html"]+["routes/%s.html"%s for s in pairs]+["routes/%s.html"%s for s,_,_ in LOCAL]
sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join('<url><loc>%s/%s</loc><lastmod>%s</lastmod><priority>%s</priority></url>\n'%(DOMAIN,u.replace("index.html",""),TODAY,"1.0" if u=="index.html" else "0.8") for u in urls) + '</urlset>\n'
open(OUT+"/sitemap.xml","w").write(sm)
open(OUT+"/robots.txt","w").write("User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n"%DOMAIN)
# css
css = open(OUT+"/style.css",encoding="utf8").read()
css += '''
/* ---- SEO pages additions ---- */
.crumbs{font-size:.8rem;color:var(--muted);margin-bottom:10px}.crumbs a{color:var(--gold);text-decoration:none}
.chips{display:flex;flex-wrap:wrap;gap:8px}.chips a{background:var(--card);border:1px solid var(--line);color:#ddd;text-decoration:none;font-size:.8rem;font-weight:600;padding:7px 12px;border-radius:999px;transition:.15s}.chips a:hover{border-color:var(--amber);color:var(--gold)}
.faq details{background:var(--card);border:1px solid rgba(255,255,255,.08);border-radius:12px;padding:14px 18px;margin-bottom:10px}.faq summary{cursor:pointer;font-weight:700}.faq p{color:var(--muted);margin:10px 0 0;font-size:.9rem}
.tick{list-style:none;padding:0}.tick li{padding:6px 0 6px 28px;position:relative;color:#ddd}.tick li:before{content:"\\2713";position:absolute;left:0;color:var(--amber);font-weight:800}
.foot-links a{display:block;margin:5px 0}.ft-ph{margin:0 0 0 4px;color:var(--gold)}
/* Floating WhatsApp + Call widget (fixed, bottom-right, all pages) */
.floating-cta{position:fixed;right:18px;bottom:18px;right:calc(18px + env(safe-area-inset-right,0px));bottom:calc(18px + env(safe-area-inset-bottom,0px));z-index:1050;display:flex;flex-direction:column;align-items:center;gap:12px}
.floating-cta__btn{box-sizing:border-box;position:relative;display:inline-flex;align-items:center;justify-content:center;width:56px;height:56px;border-radius:50%;line-height:1;text-decoration:none;transition:transform .25s,box-shadow .25s,background .25s}
.floating-cta__btn:hover{transform:translateY(-3px) scale(1.06)}
.floating-cta__btn:focus-visible{outline:2px solid #fff;outline-offset:3px}
.floating-cta__btn--wa{font-size:1.9rem;color:#fff;background:#25D366;box-shadow:0 6px 18px rgba(37,211,102,.4),0 2px 8px rgba(0,0,0,.55)}
.floating-cta__btn--wa:hover{color:#fff;background:#1ebe5b;box-shadow:0 10px 26px rgba(37,211,102,.55),0 2px 8px rgba(0,0,0,.55)}
.floating-cta__btn--wa:after{content:"";position:absolute;inset:0;border-radius:50%;border:2px solid #25D366;animation:fcta-pulse 2.4s ease-out infinite;pointer-events:none}
.floating-cta__btn--call{font-size:1.4rem;color:#111;border:1.5px solid var(--amber);background:linear-gradient(180deg,var(--gold),var(--amber));box-shadow:0 6px 18px rgba(245,158,11,.38),0 2px 8px rgba(0,0,0,.55)}
.floating-cta__btn--call:hover{color:#111;box-shadow:0 10px 26px rgba(245,158,11,.55),0 2px 8px rgba(0,0,0,.55)}
@keyframes fcta-pulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.55);opacity:0}}
@media(prefers-reduced-motion:reduce){.floating-cta__btn--wa:after{animation:none;display:none}.floating-cta__btn{transition:none}}
@media(max-width:575.98px){.floating-cta{right:14px;right:calc(14px + env(safe-area-inset-right,0px));bottom:14px;bottom:calc(14px + env(safe-area-inset-bottom,0px));gap:10px}.floating-cta__btn{width:52px;height:52px}.floating-cta__btn--wa{font-size:1.75rem}.floating-cta__btn--call{font-size:1.3rem}}
/* keep the back-to-top button clear of the floating widget */
#toTop{right:24px;bottom:calc(150px + env(safe-area-inset-bottom,0px))}
@media(max-width:575.98px){#toTop{right:18px;bottom:calc(136px + env(safe-area-inset-bottom,0px))}}
.rate-table td[data-label="Vehicle"]{min-width:150px}
'''
open(OUT+"/style.css","w",encoding="utf8").write(css)
# fleet-data: add numbers
fd = open(OUT+"/fleet-data.js",encoding="utf8").read()
fd = fd.replace("window.WA_LINK = 'https://wa.me/916352179909';","window.WA_LINK = 'https://wa.me/916352179909';   /* WhatsApp: 6352179909 */\nwindow.CALL_LINK = 'tel:+918128295920';          /* Booking: 8128295920 */")
open(OUT+"/fleet-data.js","w",encoding="utf8").write(fd)
print(len(pairs),"route pages;",len(urls),"urls")
