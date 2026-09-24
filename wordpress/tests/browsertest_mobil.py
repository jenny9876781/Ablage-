"""Prüft den Katalog in Telefonbreite. Der Testserver muss laufen (siehe browsertest.py).

Die meisten Interessenten öffnen den Link auf dem Telefon. Geprüft wird deshalb, was
dort kaputtgehen kann: waagerechtes Scrollen, abgeschnittene Bedienelemente, eine
Leiste, die den Inhalt verdeckt, und zu kleine Tippflächen.
"""
import sys
from playwright.sync_api import sync_playwright

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
BASIS = "http://127.0.0.1:8801/"
PW = "2026sales4kids"

fehler, proben = [], 0
def pruefe(name, bedingung, zusatz=""):
    global proben
    proben += 1
    if bedingung:
        print(f"  ok   {name}")
    else:
        fehler.append(name)
        print(f"  FEHL {name} {zusatz}")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    # iPhone SE: die schmalste Breite, die heute noch verbreitet ist
    s = b.new_context(viewport={"width": 375, "height": 667},
                      device_scale_factor=2, is_mobile=True, has_touch=True)
    seite = s.new_page()
    konsole = []
    seite.on("console", lambda m: konsole.append(m.text) if m.type == "error" else None)

    # Anmelden wie browsertest.py: erst der Link, sonst das Formular.
    seite.goto(BASIS + "?kik=" + PW, wait_until="networkidle")
    if seite.locator("#k-pw").count():
        seite.fill("#k-pw", PW)
        seite.click("#k-auf")
    seite.wait_for_selector(".karte", timeout=30000)
    seite.wait_for_timeout(600)

    seite.screenshot(path="/tmp/kikweb/m00-liste.png", full_page=False)

    print("\n1) Seitenbreite")
    breite = seite.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
    pruefe("kein waagerechtes Scrollen", breite[0] <= breite[1] + 1, f"{breite}")

    print("\n2) Karten und Bedienelemente")
    k = seite.locator(".karte").first
    kasten = k.bounding_box()
    pruefe("Karte passt in die Breite", kasten["width"] <= breite[1], str(kasten))
    knopf = seite.locator(".karte button[data-res]").first
    kb = knopf.bounding_box()
    pruefe("Reservieren-Knopf ist gross genug zum Tippen", kb["height"] >= 40, f"{kb['height']:.0f} px")
    feld = seite.locator(".karte input[data-menge]").first
    fb = feld.bounding_box()
    pruefe("Mengenfeld ist gross genug", fb["height"] >= 36, f"{fb['height']:.0f} px")
    pruefe("Knopf liegt vollstaendig im Sichtfeld", kb["x"] >= 0 and kb["x"] + kb["width"] <= breite[1] + 1)

    print("\n3) Filterzeile")
    for name, wahl in (("Suchfeld", "#k-q"), ("Kategorie", "#k-kat"), ("Raum", "#k-raum"), ("Merkleiste", "#k-merk")):
        el = seite.locator(wahl)
        eb = el.bounding_box()
        pruefe(f"{name} sichtbar und nicht abgeschnitten",
               eb is not None and eb["x"] >= 0 and eb["x"] + eb["width"] <= breite[1] + 1, str(eb))

    print("\n4) Merkleiste verdeckt den Inhalt nicht dauerhaft")
    feld.fill("2")
    knopf.click()
    seite.wait_for_timeout(300)
    leiste = seite.locator("#k-merk").first
    lb = leiste.bounding_box()
    pruefe("Leiste sitzt am unteren Rand", lb is not None and lb["y"] > 300, str(lb))
    pruefe("Leiste nimmt hoechstens ein Drittel der Hoehe ein",
           lb is not None and lb["height"] <= 667 / 3, f"{lb['height']:.0f} px")

    print("\n5) Formular in Telefonbreite")
    seite.locator("#k-anfragen").first.click()
    seite.wait_for_selector("#k-formular input", timeout=10000)
    breite2 = seite.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
    pruefe("auch mit Formular kein waagerechtes Scrollen", breite2[0] <= breite2[1] + 1, f"{breite2}")
    for feldname in ("name", "mail", "tel"):
        el = seite.locator("#k-" + feldname).first
        eb = el.bounding_box() if el.count() else None
        pruefe(f"Feld {feldname} passt in die Breite",
               eb is not None and eb["x"] + eb["width"] <= breite2[1] + 1, str(eb))

    seite.screenshot(path="/tmp/kikweb/m01-telefon.png", full_page=False)

    print("\n6) Konsole")
    pruefe("keine JS-Fehler", not konsole, str(konsole[:2]))
    b.close()

print(f"\n{proben} Pruefungen, {len(fehler)} Fehler")
sys.exit(1 if fehler else 0)
