"""Browsertest „zu verschenken“ (Plugin 1.5.0) und NEU-Schild (1.6.0).

Der Testserver muss mit KIK_TEST_NOVEMBER=1 laufen, damit die vorbereiteten Positionen
(Spielzeug und Geschenke, im Artikelstamm noch Im_Katalog = nein) sichtbar sind:

    rm -f /tmp/kikripp-web.sqlite /tmp/kikripp-optionen.json /tmp/kikripp-mails.log
    cd wordpress/tests && KIK_TEST_NOVEMBER=1 KIK_TEST_NEU=NE04-17,NE03-12 php -S 127.0.0.1:8801 -t /tmp/kikweb server.php &
"""
import sys, json, urllib.request
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BASIS = "http://127.0.0.1:8801/"

fehler, proben = [], 0
def pruefe(name, bedingung, zusatz=""):
    global proben
    proben += 1
    print(("  ok   " if bedingung else "  FEHL ") + name + ("" if bedingung else " " + zusatz))
    if not bedingung:
        fehler.append(name)

try:
    with urllib.request.urlopen(BASIS + "wp-json/kikripp/v1/artikel", timeout=5) as a:
        daten = json.load(a)
except Exception as e:
    sys.exit(f"Testserver auf {BASIS} nicht erreichbar: {e}")
geschenke = [a["nr"] for a in daten["artikel"] if a["preis"] <= 0 and a["frei"] > 0]
billig = [a["nr"] for a in daten["artikel"] if 0 < a["preis"] < 10 and a["frei"] > 0]
if len(geschenke) < 6:
    sys.exit("Zu wenige Geschenke im Katalog – läuft der Server mit KIK_TEST_NOVEMBER=1?")
pruefe("Höchstzahl kommt vom Server", daten.get("geschenke_max") == 5, f"({daten.get('geschenke_max')!r})")

def post(koerper, admin=False):
    kopf = {"Content-Type": "application/json"}
    if admin:
        kopf["Cookie"] = "kik_test_admin=1"
    anfrage = urllib.request.Request(BASIS + "wp-json/kikripp/v1/reservierung", method="POST",
                                     data=json.dumps(koerper).encode(), headers=kopf)
    try:
        with urllib.request.urlopen(anfrage, timeout=10) as a:
            return json.load(a)
    except urllib.error.HTTPError as e:
        return json.load(e)

kontakt = {"name": "Test Geschenk", "strasse": "Teststr. 1", "plz": "78048", "ort": "VS",
           "email": "test@example.de", "telefon": "07721 123456", "demontage": True}

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    seite = b.new_page(viewport={"width": 1280, "height": 1100})
    konsole = []
    seite.on("pageerror", lambda e: konsole.append(str(e)))
    meldungen = []
    seite.on("dialog", lambda d: (meldungen.append(d.message), d.accept()))
    seite.goto(BASIS, wait_until="networkidle")
    seite.wait_for_selector(".karte", timeout=20000)

    print("\n1) Anzeige")
    pruefe("Kategorie „zu verschenken“ im Filter", seite.locator('#k-kat option', has_text="zu verschenken").count() == 1)
    pruefe("Kategorie „Spielzeug“ im Filter", seite.locator('#k-kat option', has_text="Spielzeug").count() == 1)
    seite.select_option("#k-kat", "zu verschenken"); seite.wait_for_timeout(400)
    karten = seite.locator(".karte")
    pruefe("Filter zeigt nur Geschenke", karten.count() == len(geschenke), f"({karten.count()} statt {len(geschenke)})")
    text = karten.first.inner_text()
    pruefe("Preisfeld sagt „zu verschenken“", "zu verschenken" in text and "0,00" not in text, f"({text[-120:]!r})")
    seite.screenshot(path="/tmp/kikweb/g01-geschenke.png")

    print("\n1b) NEU-Schild und Sortierung")
    seite.select_option("#k-kat", ""); seite.wait_for_timeout(400)
    erste = [seite.locator(".karte .nr").nth(i).inner_text() for i in range(2)]
    pruefe("Neuheiten stehen ganz oben", sorted(erste) == ["NE03-12", "NE04-17"], f"({erste!r})")
    pruefe("Schild NEU an genau 2 Karten", seite.locator(".karte .neuschild").count() == 2,
           f"({seite.locator('.karte .neuschild').count()})")
    seite.check("#k-neu"); seite.wait_for_timeout(300)
    pruefe("Häkchen „nur Neuheiten“ filtert", seite.locator(".karte").count() == 2)
    seite.screenshot(path="/tmp/kikweb/g02-neu.png")
    seite.uncheck("#k-neu")
    seite.select_option("#k-sort", "auf"); seite.wait_for_timeout(300)
    erste = seite.locator(".karte .nr").first.inner_text()
    pruefe("Sortierung nach Preis zieht NEU nicht vor", erste not in ("NE03-12", "NE04-17"), f"({erste!r})")
    seite.select_option("#k-sort", ""); seite.select_option("#k-kat", "zu verschenken"); seite.wait_for_timeout(300)

    print("\n2) Nur Geschenke: kein Mindestbestellwert, höchstens 5")
    for nr in geschenke[:5]:
        seite.locator(f'button[data-res="{nr}"]').click(); seite.wait_for_timeout(150)
    merk = seite.inner_text("#k-merk")
    pruefe("Leiste sagt „geschenkt“ statt 0,00 €", "geschenkt" in merk and "0,00" not in merk, f"({merk!r})")
    pruefe("kein Hinweis auf Mindestbestellwert", "es fehlen" not in merk)
    pruefe("Abschicken freigegeben", not seite.locator("#k-anfragen").is_disabled())
    seite.locator(f'button[data-res="{geschenke[5]}"]').click(); seite.wait_for_timeout(300)
    pruefe("sechstes Geschenk abgewiesen", seite.locator(f'button[data-res="{geschenke[5]}"]').inner_text() == "reservieren")
    pruefe("Meldung erklärt die Grenze", meldungen and "höchstens 5" in meldungen[-1], f"({meldungen!r})")

    print("\n3) Geschenk + billiger Kaufartikel: Mindestwert gilt für den Kaufanteil")
    seite.locator("#k-leeren").click(); seite.wait_for_timeout(200)
    seite.select_option("#k-kat", ""); seite.wait_for_timeout(400)
    seite.locator(f'button[data-res="{geschenke[0]}"]').click()
    seite.locator(f'button[data-res="{billig[0]}"]').click(); seite.wait_for_timeout(300)
    pruefe("unter 50 € Kaufwert gesperrt", seite.locator("#k-anfragen").is_disabled())
    seite.locator("#k-leeren").click(); seite.wait_for_timeout(200)

    print("\n4) Abschicken nur Geschenke")
    for nr in geschenke[:2]:
        seite.locator(f'button[data-res="{nr}"]').click(); seite.wait_for_timeout(150)
    seite.click("#k-anfragen"); seite.wait_for_selector("#k-dlg", timeout=5000)
    dlg = seite.inner_text("#k-dlg")
    pruefe("Formular zeigt „geschenkt“", "geschenkt" in dlg and "\n0,00" not in dlg, f"({dlg[300:700]!r})")
    pruefe("keine Seitenfehler", not konsole, f"({konsole!r})")

    print("\n4b) Verwaltung angemeldet: kein Mindestbestellwert (1.7.0)")
    s2 = b.new_context(viewport={"width": 1280, "height": 1100})
    s2.add_cookies([{"name": "kik_test_admin", "value": "1", "url": BASIS}])
    v = s2.new_page()
    nonce = []
    v.on("request", lambda r: nonce.append(r.headers.get("x-wp-nonce")) if "/wp-json/" in r.url else None)
    v.goto(BASIS, wait_until="networkidle"); v.wait_for_selector(".karte", timeout=20000)
    pruefe("Nonce geht mit", "test-nonce" in nonce, f"({nonce[:2]!r})")
    pruefe("Hinweis für die Verwaltung", "als Verwaltung angemeldet" in v.inner_text("#k-merk"))
    v.locator(f'button[data-res="{billig[1]}"]').click(); v.wait_for_timeout(300)
    pruefe("Verwaltung: unter 50 € abschickbar", not v.locator("#k-anfragen").is_disabled())
    s2.close()
    b.close()

print("\n5) Server")
a = post(dict(kontakt, artikel={nr: 1 for nr in geschenke[:6]}, dauer=5000))
pruefe("Server lehnt 6 Geschenke ab", not a.get("ok") and "höchstens 5" in (a.get("fehler") or a.get("meldung") or json.dumps(a, ensure_ascii=False)), f"({a!r})")
a = post(dict(kontakt, artikel={billig[0]: 1, geschenke[0]: 1}, dauer=5000))
pruefe("Server: Kaufanteil unter Mindestwert abgelehnt", not a.get("ok"), f"({a!r})")
a = post(dict(kontakt, artikel={nr: 1 for nr in geschenke[:5]}, dauer=5000))
pruefe("Server nimmt 5 Geschenke ohne Mindestwert an", a.get("ok") is True, f"({a!r})")

a = post(dict(kontakt, artikel={billig[2]: 1}, dauer=5000), admin=True)
pruefe("Server: Verwaltung darf unter Mindestwert reservieren", a.get("ok") is True, f"({a!r})")

kurz = {"name": "Barverkauf vor Ort", "telefon": "0171 2345678"}
a = post(dict(kurz, artikel={billig[3]: 1}, dauer=5000), admin=True)
pruefe("Server: Verwaltung reserviert nur mit Name und Telefon (1.11.2)", a.get("ok") is True, f"({a!r})")
a = post(dict(kurz, artikel={billig[4]: 1}, dauer=5000))
pruefe("Server: Kunde braucht weiter Anschrift", not a.get("ok"), f"({a!r})")
a = post(dict(name="Ohne Telefon", artikel={billig[4]: 1}, dauer=5000), admin=True)
pruefe("Server: Verwaltung braucht weiter Telefon", not a.get("ok"), f"({a!r})")

print(f"\n== Geschenke-Browsertest: {proben} Prüfungen, {len(fehler)} Fehler ==")
sys.exit(1 if fehler else 0)
