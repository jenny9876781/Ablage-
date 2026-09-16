"""Browsertest des Artikelkatalogs gegen die echten REST-Rueckrufe."""
import re, sys
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
        fehler.append(f"{name} {zusatz}".strip())
        print(f"  FEHL {name} {zusatz}")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    s = b.new_context(viewport={"width": 1280, "height": 1100})
    seite = s.new_page()
    konsole = []
    seite.on("console", lambda m: konsole.append(f"{m.type}: {m.text}"))
    seite.on("pageerror", lambda e: konsole.append(f"pageerror: {e}"))

    print("\n1) Anmeldung")
    seite.goto(BASIS, wait_until="networkidle")
    pruefe("Sperrseite sichtbar", seite.locator("#k-pw").is_visible())
    pruefe("Katalog noch nicht geladen", seite.locator(".karte").count() == 0)
    seite.screenshot(path="/tmp/kikweb/t01-sperre.png")

    seite.fill("#k-pw", "falsches-passwort")
    seite.click("#k-auf")
    seite.wait_for_timeout(900)
    pruefe("Fehlermeldung bei falschem Passwort",
           "falsch" in seite.inner_text("#k-fehler").lower(),
           f"({seite.inner_text('#k-fehler')!r})")
    pruefe("kein Katalog trotz Fehlversuch", seite.locator(".karte").count() == 0)

    seite.fill("#k-pw", PW)
    seite.click("#k-auf")
    seite.wait_for_selector(".karte", timeout=20000)
    seite.wait_for_timeout(800)

    print("\n2) Katalogaufbau")
    karten = seite.locator(".karte").count()
    pruefe("Artikel geladen", karten > 100, f"({karten} Karten)")
    gesamt_bilder = seite.locator(".karte .bild img").count()
    seite.mouse.wheel(0, 40000); seite.wait_for_timeout(1500)
    seite.mouse.wheel(0, 80000); seite.wait_for_timeout(2000)
    geladen = seite.eval_on_selector_all(
        ".karte .bild img", "els => els.filter(e => e.naturalWidth > 0).length")
    pruefe("Fotos laden", geladen > 30, f"({geladen}/{gesamt_bilder} sichtbar geladen)")
    seite.mouse.wheel(0, -200000); seite.wait_for_timeout(500)

    erste = seite.locator(".karte").first.inner_text()
    alles = seite.inner_text(".kikripp")
    pruefe("Zustand beschriftet", "Zustand:" in erste, f"({erste[:160]!r})")
    pruefe("kein Listenwert", "Listenwert" not in alles)
    pruefe("keine Rot-Erklaerung", "rot markiert" not in alles.lower())
    pruefe("Brutto prominent, netto klein", "inkl. USt · netto" in erste, f"({erste[:200]!r})")
    pruefe("Knopf heisst reservieren",
           seite.locator("button[data-res]").count() > 50,
           f"({seite.locator('button[data-res]').count()})")
    pruefe("Hinweisband sichtbar", seite.locator(".band").count() == 1)
    recht = seite.inner_text(".recht") if seite.locator(".recht").count() else ""
    pruefe("Rechtshinweis vorhanden", "Gewährleistung" in recht and "Widerrufsrecht" in recht,
           f"({recht[:160]!r})")
    pruefe("Abholadresse genannt", "Hermann-Schwer-Str. 1" in recht)
    seite.screenshot(path="/tmp/kikweb/t02-katalog.png")

    print("\n3) Menge und Knopf")
    felder = seite.locator("input[data-menge]")
    ziel = None
    for i in range(felder.count()):
        f = felder.nth(i)
        if int(f.get_attribute("max") or 0) >= 4:
            ziel = f; break
    pruefe("Artikel mit Menge >= 4 gefunden", ziel is not None)
    nr = ziel.get_attribute("data-menge")
    maxwert = int(ziel.get_attribute("max"))
    print(f"     Testartikel {nr}, verfuegbar {maxwert}")
    pruefe("max-Attribut = verfuegbare Menge", maxwert >= 4)

    ziel.fill(str(maxwert + 7))
    seite.wait_for_timeout(300)
    pruefe("Menge hart gedeckelt", ziel.input_value() == str(maxwert),
           f"(eingetippt {maxwert+7}, jetzt {ziel.input_value()})")

    ziel.fill("2"); seite.wait_for_timeout(200)
    seite.locator(f'button[data-res="{nr}"]').click()
    seite.wait_for_timeout(300)
    pruefe("Knopf laesst Menge unveraendert", ziel.input_value() == "2",
           f"(nach Klick {ziel.input_value()})")
    seite.locator(f'button[data-res="{nr}"]').click()
    seite.locator(f'button[data-res="{nr}"]').click()
    seite.wait_for_timeout(300)
    pruefe("Mehrfachklick aendert Menge nicht", ziel.input_value() == "2",
           f"(nach 3 Klicks {ziel.input_value()})")

    print("\n4) Leiste zaehlt Stueck, nicht Positionen")
    merk = seite.inner_text("#k-merk")
    pruefe("Stueckzahl in der Leiste", merk.startswith("2 Stück"), f"({merk!r})")

    nr2 = None
    for i in range(felder.count()):
        f = felder.nth(i)
        if f.get_attribute("data-menge") != nr and int(f.get_attribute("max") or 0) >= 1:
            nr2 = f.get_attribute("data-menge")
            f.fill("1"); break
    seite.locator(f'button[data-res="{nr2}"]').click()
    seite.wait_for_timeout(300)
    merk = seite.inner_text("#k-merk")
    pruefe("Stueck summiert ueber zwei Positionen", merk.startswith("3 Stück"), f"({merk!r})")
    seite.screenshot(path="/tmp/kikweb/t03-vorgemerkt.png")

    print("\n5) Reservierung abschicken")
    seite.click("#k-anfragen")
    seite.wait_for_selector("#k-dlg", timeout=5000)
    dlg = seite.inner_text("#k-dlg")
    pruefe("Formular zeigt Stueck gesamt", "3 Stück gesamt" in dlg, f"({dlg[:300]!r})")
    pruefe("Frist genannt", "7 Tage" in dlg)
    pruefe("Datenschutzhinweis", seite.locator(".datenschutz").count() == 1)
    pruefe("Hinweis: noch kein Kaufvertrag", "noch kein Kaufvertrag" in dlg, f"({dlg[:400]!r})")

    seite.click("#k-senden")
    seite.wait_for_timeout(600)
    pruefe("Pflichtfeld Name geprueft", "Namen" in seite.inner_text("#k-meldung"),
           f"({seite.inner_text('#k-meldung')!r})")

    seite.fill("#k-name", "Testkaeufer Muster GmbH")
    seite.fill("#k-mail", "test@example.org")
    seite.fill("#k-tel", "07721 123456")
    seite.fill("#k-text", "Automatischer Testlauf")
    seite.click("#k-senden")
    seite.wait_for_selector(".meldung.gut", timeout=15000)
    erfolg = seite.inner_text(".meldung.gut")
    pruefe("Erfolgsmeldung mit Vorgangsnummer",
           "Vielen Dank" in erfolg and re.search(r"Vorgangsnummer\s+\S+", erfolg) is not None,
           f"({erfolg[:200]!r})")
    pruefe("kein Mailfehler-Hinweis", "konnte nicht versandt" not in erfolg, f"({erfolg!r})")
    pruefe("Leiste zurueckgesetzt", "Noch nichts vorgemerkt" in seite.inner_text("#k-merk"))
    seite.screenshot(path="/tmp/kikweb/t04-erfolg.png")

    print("\n6) Bestand nach der Reservierung")
    seite.reload(wait_until="networkidle")
    seite.wait_for_selector(".karte", timeout=20000)
    seite.wait_for_timeout(600)
    pruefe("Anmeldung bleibt bestehen (Cookie)", seite.locator("#k-pw").count() == 0)

    seite.fill("#k-q", nr); seite.wait_for_timeout(400)
    k1 = seite.locator(".karte").first.inner_text()
    pruefe(f"Teilverfuegbarkeit bei {nr}",
           f"{maxwert-2} von {maxwert}" in k1, f"({k1!r})")
    feld1 = seite.locator("input[data-menge]").first
    pruefe("Obergrenze nachgezogen", feld1.get_attribute("max") == str(maxwert - 2),
           f"(max={feld1.get_attribute('max')})")

    seite.fill("#k-q", nr2); seite.wait_for_timeout(400)
    pruefe("voll reservierter Artikel ausgeblendet (Filter 'nur verfügbare')",
           seite.locator(".karte").count() == 0, f"({seite.locator('.karte').count()})")
    seite.uncheck("#k-frei"); seite.wait_for_timeout(400)
    k2 = seite.locator(".karte").first.inner_text()
    pruefe("voll reserviert klar benannt", "vollständig reserviert" in k2, f"({k2!r})")
    pruefe("kein Mengenfeld bei reserviertem Artikel",
           seite.locator(".karte input[data-menge]").count() == 0)
    seite.screenshot(path="/tmp/kikweb/t05-danach.png")

    print("\n7) Konsole")
    schlimm = [k for k in konsole if (k.startswith("error") or k.startswith("pageerror")) and "401" not in k]
    pruefe("keine JS-Fehler", not schlimm, f"({schlimm[:3]})")

    b.close()

print(f"\n{proben} Pruefungen, {len(fehler)} Fehler")
for f in fehler: print("  -", f)
sys.exit(1 if fehler else 0)
