"""Browsertest 1.15.1: Kategorie-Knöpfe, „bis 15 €“, Neuheiten nach Datum, Sale, Teilen, Merkliste.

Der Testserver läuft mit einer Importdatei, in der drei Artikel einen Sale-Preis haben,
zwei Artikel heute und zwei vor fünf Tagen NEU wurden:

    python3 wordpress/tests/browsertest_sale.py --vorbereiten     # schreibt /tmp/kikweb/sale_import.json, nennt die Nummern
    rm -f /tmp/kikripp-web.sqlite /tmp/kikripp-optionen.json
    cd wordpress/tests && KIK_TEST_IMPORT=/tmp/kikweb/sale_import.json KIK_TEST_NEU=<heute> KIK_TEST_NEU_ALT=<alt> \\
        php -S 127.0.0.1:8801 -t /tmp/kikweb server.php &
    NO_PROXY=127.0.0.1 python3 wordpress/tests/browsertest_sale.py
"""
import sys, os, json
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium"
BASIS = "http://127.0.0.1:8801/"
HIER = os.path.dirname(os.path.abspath(__file__))
IMPORT = os.path.join(HIER, "../../ausgabe/katalog_import.json")
ZIEL = "/tmp/kikweb/sale_import.json"

def sichtbar(a): return a["aktiv"] and a["im_katalog"]

liste = json.load(open(IMPORT, encoding="utf-8"))
kauf = [a for a in liste if sichtbar(a) and float(a["preis"] or 0) >= 20]
SALE = [a["nr"] for a in kauf[5:8]]
NEU_HEUTE = [kauf[20]["nr"], kauf[21]["nr"]]
NEU_ALT = [kauf[0]["nr"], kauf[1]["nr"]]          # stehen in der Datei vor den heutigen

if "--vorbereiten" in sys.argv:
    for a in liste:
        a["sale"] = round(float(a["preis"]) * 0.7, 2) if a["nr"] in SALE else None
    json.dump(liste, open(ZIEL, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"KIK_TEST_IMPORT={ZIEL} KIK_TEST_NEU={','.join(NEU_HEUTE)} KIK_TEST_NEU_ALT={','.join(NEU_ALT)}")
    sys.exit(0)

fehler, proben = [], 0
def pruefe(name, bedingung, zusatz=""):
    global proben
    proben += 1
    print(("  ok   " if bedingung else "  FEHL ") + name + ("" if bedingung else " " + zusatz))
    if not bedingung: fehler.append(name)

# Aufwärmen: beim ersten Aufruf füllt der Testserver die Datenbank, das dauert
import urllib.request
urllib.request.build_opener(urllib.request.ProxyHandler({})).open(BASIS + "wp-json/kikripp/v1/artikel", timeout=180).read()

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    ctx = b.new_context(viewport={"width": 1280, "height": 1000})
    s = ctx.new_page()
    konsole = []
    s.on("pageerror", lambda e: konsole.append(str(e)))
    s.goto(BASIS, wait_until="networkidle"); s.wait_for_selector(".karte", timeout=30000)
    nrs = lambda n: [s.locator(".karte .nr").nth(i).inner_text() for i in range(n)]

    print("\n1) Reihenfolge: Neuheiten nach Datum, dann Sale")
    erste = nrs(7)
    pruefe("heutige Neuheiten ganz oben", sorted(erste[:2]) == sorted(NEU_HEUTE), f"({erste!r})")
    pruefe("dann die älteren Neuheiten", sorted(erste[2:4]) == sorted(NEU_ALT), f"({erste!r})")
    pruefe("dann die Sale-Artikel", sorted(erste[4:7]) == sorted(SALE), f"({erste!r})")

    print("\n2) Sale an der Karte")
    karte = s.locator(".karte", has=s.locator(f'.nr:text-is("{SALE[0]}")'))
    pruefe("Schild „Sale“", karte.locator(".saleschild").count() == 1)
    alt = karte.locator(".preis s").inner_text()
    soll = next(a for a in liste if a["nr"] == SALE[0])
    pruefe("alter Preis durchgestrichen", alt.replace("\xa0", " ").startswith(f"{float(soll['preis']):.2f}".replace(".", ",")), f"({alt!r})")
    pruefe("Karte ohne Sale hat kein Schild",
           s.locator(".karte", has=s.locator(f'.nr:text-is("{NEU_HEUTE[0]}")')).locator(".saleschild").count() == 0)

    print("\n3) Kategorie-Knöpfe")
    pruefe("Knopf „Alle“ ist gewählt", "an" in (s.locator('#k-kats button[data-kat=""]').get_attribute("class") or ""))
    sale_k = s.locator("#k-kats button.sale")
    pruefe("Knopf „Sale“ mit Zahl 3", sale_k.count() == 1 and sale_k.inner_text().strip().endswith("3"), f"({sale_k.all_inner_texts()!r})")
    sale_k.click(); s.wait_for_timeout(300)
    pruefe("Sale-Knopf zeigt nur Sale", sorted(nrs(s.locator(".karte").count())) == sorted(SALE))
    kat = next(a for a in liste if a["nr"] == SALE[0])["kat"]
    s.click(f'#k-kats button[data-kat="{kat}"]'); s.wait_for_timeout(300)
    pruefe("Sale-Artikel steht auch in seiner Kategorie", SALE[0] in nrs(s.locator(".karte").count()))
    s.click('#k-kats button.preiswert'); s.wait_for_timeout(300)
    preise = s.evaluate("""() => Array.from(document.querySelectorAll('.karte .preis b')).map(b => parseFloat(b.textContent.replace(/[^0-9,]/g,'').replace(',','.')))""")
    pruefe("„bis 15 €“: alle Preise bis 15 €", preise and max(preise) <= 15, f"(max {max(preise) if preise else None})")
    pruefe("„bis 15 €“: keine Geschenke", s.locator(".karte .preis.geschenk").count() == 0)
    s.click('#k-kats button[data-kat=""]'); s.wait_for_timeout(300)

    print("\n4) Teilen per WhatsApp in der Großansicht")
    s.locator(".karte img[data-gross]").first.click(); s.wait_for_timeout(200)
    link = s.locator("#k-gross .teilen")
    pruefe("Link sichtbar", link.is_visible())
    href = link.get_attribute("href") or ""
    pruefe("Link geht an WhatsApp mit Artikeltext", href.startswith("https://wa.me/?text=") and "Kikripp" in __import__("urllib.parse").parse.unquote(href), f"({href[:80]!r})")
    pruefe("Karten selbst haben keinen Teilen-Knopf", s.locator(".karte .teilen").count() == 0)
    s.keyboard.press("Escape")

    print("\n5) Merkliste bleibt beim Neuladen")
    nr = s.locator(".karte button[data-res]").first.get_attribute("data-res")
    s.locator(f'button[data-res="{nr}"]').click(); s.wait_for_timeout(200)
    s.reload(wait_until="networkidle"); s.wait_for_selector(".karte")
    pruefe("vorgemerkter Artikel nach Neuladen noch da", "vorgemerkt" in s.locator(f'button[data-res="{nr}"]').inner_text())
    s.click("#k-leeren"); s.reload(wait_until="networkidle"); s.wait_for_selector(".karte")
    pruefe("nach „Auswahl leeren“ bleibt sie leer", "Noch nichts vorgemerkt" in s.inner_text("#k-merk"))
    s.screenshot(path="/tmp/kikweb/s01-sale.png")

    print("\n6) Telefon: Knöpfe in einer Zeile, kein waagerechtes Scrollen")
    m = b.new_context(viewport={"width": 375, "height": 667}, is_mobile=True, has_touch=True).new_page()
    m.goto(BASIS, wait_until="networkidle"); m.wait_for_selector(".karte", timeout=30000)
    breite = m.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
    pruefe("Seite nicht breiter als das Telefon", breite[0] <= breite[1] + 1, str(breite))
    hoehen = m.evaluate("() => Array.from(document.querySelectorAll('#k-kats button')).map(b => b.getBoundingClientRect().top)")
    pruefe("alle Knöpfe in einer Zeile", len(set(round(h) for h in hoehen)) == 1, f"({sorted(set(round(h) for h in hoehen))})")
    m.screenshot(path="/tmp/kikweb/s02-mobil.png")

    pruefe("keine Skriptfehler", not konsole, f"({konsole!r})")
    b.close()

print(f"\n== Sale-Browsertest: {proben} Prüfungen, {len(fehler)} Fehler ==")
sys.exit(1 if fehler else 0)
