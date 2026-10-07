"""Browsertest des Artikelkatalogs gegen die echten REST-Rueckrufe.

Der Testserver muss laufen:

    rm -f /tmp/kikripp-web.sqlite /tmp/kikripp-optionen.json /tmp/kikripp-mails.log
    cd wordpress/tests && KIK_TEST_PW=... php -S 127.0.0.1:8801 -t /tmp/kikweb server.php &

Beide Zustandsdateien loeschen, nicht nur eine: die Optionsdatei entscheidet ueber
das Passwort, die SQLite-Datei ueber die Artikel.
"""
import re, sys, os
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

# Vorbedingung pruefen, statt spaeter an einem leeren Katalog zu raten.
import urllib.request, json as _json
try:
    with urllib.request.urlopen(BASIS, timeout=5) as a:
        a.read(1)
except Exception as e:
    sys.exit(f"Testserver auf {BASIS} nicht erreichbar: {e}")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    s = b.new_context(viewport={"width": 1280, "height": 1100})
    seite = s.new_page()
    konsole = []
    seite.on("console", lambda m: konsole.append(f"{m.type}: {m.text}"))
    seite.on("pageerror", lambda e: konsole.append(f"pageerror: {e}"))

    print("\n0) Katalog ohne Passwort (ab Fassung 1.2.0)")
    seite.goto(BASIS, wait_until="networkidle")
    seite.wait_for_selector(".karte", timeout=20000)
    seite.wait_for_timeout(800)
    pruefe("keine Sperrseite", seite.locator("#k-pw").count() == 0)
    pruefe("Katalog lädt direkt", seite.locator(".karte").count() > 50)

    print("\n2) Katalogaufbau")
    karten = seite.locator(".karte").count()
    import json
    hier = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(hier, "../../ausgabe/katalog_import.json"), encoding="utf-8") as f:
        erwartet = sum(1 for a in json.load(f) if a["aktiv"] and a["im_katalog"])
    pruefe("alle aktiven Artikel geladen", karten == erwartet, f"({karten} von {erwartet})")
    # Fotos haengen an loading="lazy". Zaehlen, wie viele insgesamt geladen sind, taugt hier
    # nicht: der eingebaute PHP-Testserver bedient genau eine Anfrage nach der anderen, also
    # haengt das Ergebnis am Zufall. Geprueft wird deshalb, was zaehlt — ein Bild, das in den
    # Blick geraet, wird nachgeladen. Dafuer drei Karten quer durch die Liste.
    gesamt_bilder = seite.locator(".karte .bild img").count()
    stellen = [0, gesamt_bilder // 2, gesamt_bilder - 1]
    nicht_geladen = []
    for i in stellen:
        bild = seite.locator(".karte .bild img").nth(i)
        bild.scroll_into_view_if_needed()
        try:
            seite.wait_for_function(
                "el => el.complete && el.naturalWidth > 0", arg=bild.element_handle(),
                timeout=15000)
        except Exception:
            nicht_geladen.append(i)
    pruefe("Fotos laden beim Hineinscrollen", not nicht_geladen,
           f"(Karten {nicht_geladen} von {gesamt_bilder} blieben leer)")
    seite.evaluate("window.scrollTo(0, 0)"); seite.wait_for_timeout(500)

    erste = seite.locator(".karte").first.inner_text()
    alles = seite.inner_text(".kikripp")
    pruefe("Zustand beschriftet", "Zustand:" in erste, f"({erste[:160]!r})")
    pruefe("kein Listenwert", "Listenwert" not in alles)
    pruefe("keine Rot-Erklaerung", "rot markiert" not in alles.lower())
    pruefe("ein Preis, umsatzsteuerfrei", "umsatzsteuerfrei" in erste and "netto" not in erste
           and "inkl. USt" not in erste, f"({erste[:200]!r})")
    pruefe("Kopf: Endpreise, Abholung durch den Käufer",
           "Endpreise, umsatzsteuerfrei" in seite.inner_text(".kopf")
           and "Abholung durch den Käufer" in seite.inner_text(".kopf"))
    ablauf = seite.inner_text(".ablauf") if seite.locator(".ablauf").count() else ""
    pruefe("Kasten „So läuft es ab“", "3 Werktage" in ablauf and "Mindestbestellwert" in ablauf
           and "10.12.2026" in ablauf, f"({ablauf[:200]!r})")
    pruefe("kein Versandhinweis mehr", "Versand möglich" not in alles)
    pruefe("Besichtigung möglich an teuren Artikeln", seite.locator(".meta .bes").count() > 10,
           f"({seite.locator('.meta .bes').count()})")
    pruefe("Knopf heisst reservieren",
           seite.locator("button[data-res]").count() > 50,
           f"({seite.locator('button[data-res]').count()})")
    pruefe("Hinweisband sichtbar", seite.locator(".band").count() == 1)
    recht = seite.inner_text(".recht") if seite.locator(".recht").count() else ""
    pruefe("Kaufbedingungen vorhanden", "Gewährleistung" in recht and "§ 4 Nr. 28 UStG" in recht
           and "§ 4 Nr. 23 UStG" in recht, f"({recht[:160]!r})")
    # Seit 07.10.2026 zahlen auch Privatpersonen per Rechnung vorab – Verbraucher haben ein Widerrufsrecht.
    pruefe("Hinweis auf das Widerrufsrecht für Verbraucher", "gesetzliches Widerrufsrecht" in recht, f"({recht[-200:]!r})")
    pruefe("Abholadresse genannt", "Hermann-Schwer-Str. 1" in recht)
    pruefe("Anbieter benannt",
           "anbieter" in recht.lower() and "Kikripp GmbH" in recht, f"({recht[:200]!r})")
    pruefe("Impressum verlinkt",
           seite.locator('.recht a[href*="impressum"]').count() == 1)
    pruefe("Datenschutz verlinkt",
           seite.locator('.recht a[href*="datenschutz"]').count() == 1)
    pruefe("Menü und Social-Media-Symbole im Kopf sind ausgeblendet",
           seite.locator("#probe-menue").count() == 1 and not seite.locator("#probe-menue").is_visible()
           and not seite.locator("#probe-social").is_visible())
    pruefe("Logo im Kopf bleibt sichtbar", seite.locator("#probe-logo").is_visible())
    pruefe("Fußzeile der Website ist auf der Katalogseite ausgeblendet",
           seite.locator("#probe-fusszeile").count() == 1 and not seite.locator("#probe-fusszeile").is_visible())
    pruefe("kein Hut und kein Schriftzug KIKRIPP im Kopf", seite.locator(".kopf img").count() == 0
           and "KIKRIPP" not in seite.inner_text(".kopf"))
    band_farbe = seite.evaluate("() => getComputedStyle(document.querySelector('.band')).backgroundColor")
    band_fett = seite.evaluate("() => getComputedStyle(document.querySelector('.band')).fontWeight")
    pruefe("Ankündigung rot hinterlegt und fett", band_farbe == "rgb(200, 16, 46)" and int(band_fett) >= 700,
           f"({band_farbe}, {band_fett})")
    pruefe("Ablauf als Fließtext in zwei Absätzen", seite.locator(".ablauf p").count() == 2 and seite.locator(".ablauf li").count() == 0)
    pruefe("Ablauf: Bezahlung generell gegen Rechnung", "generell per Überweisung gegen Rechnung" in ablauf, f"({ablauf!r})")
    pruefe("Kopf nennt die Verkäuferin",
           "Ein Angebot der Kikripp GmbH" in seite.inner_text(".kopf"))
    seite.screenshot(path="/tmp/kikweb/t02-katalog.png")

    print("\n3) Menge und Knopf")
    with open(os.path.join(hier, "../../ausgabe/katalog_import.json"), encoding="utf-8") as f:
        preise = {a["nr"]: a["preis"] for a in json.load(f)}
    felder = seite.locator("input[data-menge]")
    ziel = None
    for i in range(felder.count()):
        f = felder.nth(i)
        if int(f.get_attribute("max") or 0) >= 4 and preise.get(f.get_attribute("data-menge"), 0) >= 25:
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

    print("\n4a) Merkliste und Knöpfe")
    knopf_text = seite.locator(f'button[data-res="{nr}"]').inner_text()
    pruefe("Knopf zeigt die Vormerkung dauerhaft", knopf_text == "✓ vorgemerkt (2)", f"({knopf_text!r})")
    seite.click("#k-merk"); seite.wait_for_timeout(300)
    pruefe("Merkliste klappt auf", seite.locator("#k-liste").is_visible() and seite.locator("#k-liste .zeile").count() == 2)
    seite.locator(f'#k-liste button[data-weg="{nr2}"]').click(); seite.wait_for_timeout(300)
    pruefe("Artikel einzeln entfernt", seite.locator("#k-liste .zeile").count() == 1
           and seite.inner_text("#k-merk").startswith("2 Stück"), f"({seite.inner_text('#k-merk')!r})")
    pruefe("Knopf des entfernten Artikels zurückgesetzt", seite.locator(f'button[data-res="{nr2}"]').inner_text() == "reservieren")
    seite.locator(f'input[data-menge="{nr2}"]').fill("1"); seite.locator(f'button[data-res="{nr2}"]').click()
    seite.wait_for_timeout(300)
    seite.click("#k-merk"); seite.wait_for_timeout(200)
    pruefe("Merkliste wieder zu", not seite.locator("#k-liste").is_visible())

    # Wunsch 01.10.2026: Leiste oben statt unter der Liste, Fotos ganz statt beschnitten
    lb = seite.locator(".leiste").bounding_box()
    rb = seite.locator("#k-raster").bounding_box()
    pruefe("Leiste steht oberhalb der Artikel", lb is not None and rb is not None and lb["y"] < rb["y"],
           f"({lb}, {rb})")
    seite.mouse.wheel(0, 3000)
    seite.wait_for_timeout(400)
    lb2 = seite.locator(".leiste").bounding_box()
    pruefe("Leiste bleibt beim Scrollen oben sichtbar", lb2 is not None and abs(lb2["y"]) <= 2, f"({lb2})")
    seite.mouse.wheel(0, -6000)
    seite.wait_for_timeout(300)
    passung = seite.evaluate("() => { const i = document.querySelector('.bild img');"
                             " return i ? getComputedStyle(i).objectFit : null; }")
    pruefe("Fotos werden ganz gezeigt (object-fit: contain)", passung == "contain", f"({passung!r})")

    # Mindestbestellwert: ein billiger Einzelartikel allein reicht nicht
    print("\n4b) Mindestbestellwert")
    billig = [n for n, p in preise.items() if 0 < p < 10]
    probe = None
    for i in range(felder.count()):
        f = felder.nth(i)
        if f.get_attribute("data-menge") in billig and f.get_attribute("data-menge") not in (nr, nr2):
            probe = f.get_attribute("data-menge"); break
    seite.locator("#k-leeren").click(); seite.wait_for_timeout(200)
    seite.locator(f'input[data-menge="{probe}"]').fill("1")
    seite.locator(f'button[data-res="{probe}"]').click(); seite.wait_for_timeout(300)
    pruefe("Hinweis auf den Mindestbestellwert", "Mindestbestellwert" in seite.inner_text("#k-merk"),
           f"({seite.inner_text('#k-merk')!r})")
    pruefe("Abschicken gesperrt unter 50 €", seite.locator("#k-anfragen").is_disabled())
    seite.locator("#k-leeren").click(); seite.wait_for_timeout(200)
    ziel.fill("2"); seite.locator(f'button[data-res="{nr}"]').click()
    seite.locator(f'input[data-menge="{nr2}"]').fill("1"); seite.locator(f'button[data-res="{nr2}"]').click()
    seite.wait_for_timeout(300)
    pruefe("mit genug Wert wieder freigegeben", not seite.locator("#k-anfragen").is_disabled())

    print("\n5) Reservierung abschicken")
    seite.evaluate("window.scrollTo(0, 2500)"); seite.wait_for_timeout(300)
    vorher_y = seite.evaluate("window.scrollY")
    seite.click("#k-anfragen")
    seite.wait_for_selector("#k-dlg", timeout=5000)
    dlg = seite.inner_text("#k-dlg")
    pruefe("Formular öffnet als Fenster, die Seite springt nicht", seite.locator("#k-fenster").is_visible()
           and abs(seite.evaluate("window.scrollY") - vorher_y) < 5, f"(vorher {vorher_y}, nachher {seite.evaluate('window.scrollY')})")
    pruefe("Formular zeigt Stueck gesamt", "3 Stück gesamt" in dlg, f"({dlg[:300]!r})")
    pruefe("Frist genannt", "3 Werktage" in dlg, f"({dlg[:200]!r})")
    pruefe("„melden wir uns“ statt Anruf", "melden wir uns" in dlg and "rufen wir" not in dlg)
    pruefe("Datenschutzhinweis", seite.locator(".datenschutz").count() == 1)
    pruefe("Hinweis: noch kein Kaufvertrag", "noch kein Kaufvertrag" in dlg, f"({dlg[:400]!r})")
    pruefe("Hinweis: keine Bestätigungsmail",
           "keine Bestätigungsmail" in seite.inner_text(".datenschutz"),
           f"({seite.inner_text('.datenschutz')!r})")
    abhol = [t.strip() for t in seite.locator("#k-abhol option").all_inner_texts()[1:]]
    pruefe("Abholtermine nur montags und dienstags", abhol and all(t[:3] in ("Mo,", "Di,") for t in abhol),
           f"({abhol[:4]})")
    pruefe("letzter Abholtag ist der 10.12.2026 oder früher",
           abhol and abhol[-1][-4:] == "2026" and tuple(map(int, abhol[-1][4:9].split(".")[::-1])) <= (12, 10),
           f"({abhol[-1:] })")
    pruefe("Adressfelder vorhanden", all(seite.locator(i).count() == 1
           for i in ("#k-firma", "#k-strasse", "#k-plz", "#k-ort")))
    pruefe("Demontage ankreuzbar", seite.locator("#k-demontage").count() == 1)
    hp = seite.locator("#k-webseite").bounding_box()
    pruefe("unsichtbares Feld gegen Roboter liegt außerhalb des Bildes", hp is not None and hp["x"] < 0, f"({hp})")
    pruefe("Telefon ist als Pflichtfeld markiert",
           "Telefon *" in dlg and seite.locator("#k-tel[required]").count() == 1)

    seite.click("#k-senden")
    seite.wait_for_timeout(600)
    pruefe("Pflichtfeld Name geprueft", "Namen" in seite.inner_text("#k-meldung"),
           f"({seite.inner_text('#k-meldung')!r})")

    seite.fill("#k-name", "Testkaeufer Muster")
    seite.fill("#k-firma", "Muster GmbH")
    seite.fill("#k-mail", "test@example.org")
    seite.click("#k-senden")
    seite.wait_for_timeout(500)
    pruefe("ohne Anschrift wird nicht abgeschickt",
           "Anschrift" in seite.inner_text("#k-meldung"), f"({seite.inner_text('#k-meldung')!r})")
    seite.fill("#k-strasse", "Hauptstraße 5"); seite.fill("#k-plz", "78048"); seite.fill("#k-ort", "Villingen")
    seite.click("#k-senden")
    seite.wait_for_timeout(500)
    pruefe("ohne Telefon wird nicht abgeschickt",
           "Telefonnummer" in seite.inner_text("#k-meldung"),
           f"({seite.inner_text('#k-meldung')!r})")

    seite.fill("#k-tel", "07721 123456")
    seite.click("#k-senden")
    seite.wait_for_timeout(500)
    pruefe("ohne Abholtermin wird nicht abgeschickt",
           "Abholung" in seite.inner_text("#k-meldung"), f"({seite.inner_text('#k-meldung')!r})")
    seite.select_option("#k-abhol", index=1)
    zeiten = [t.strip() for t in seite.locator("#k-abhol-zeit option").all_inner_texts()[1:]]
    pruefe("Abholung: Uhrzeiten 08:00 bis 10:30", zeiten[:1] == ["08:00 Uhr"] and zeiten[-1:] == ["10:30 Uhr"], f"({zeiten})")
    seite.select_option("#k-abhol-zeit", "09:30")
    if seite.locator("#k-bes").count():
        seite.check("#k-bes")
        seite.select_option("#k-bes-tag", index=1); seite.select_option("#k-bes-zeit", "09:00")
    seite.fill("#k-text", "Automatischer Testlauf")
    seite.wait_for_timeout(3200)        # Mindestzeit gegen Formular-Roboter
    seite.click("#k-senden")
    seite.wait_for_selector(".meldung.gut", timeout=15000)
    erfolg = seite.inner_text(".meldung.gut")
    pruefe("Erfolgsmeldung", "Vielen Dank" in erfolg and "melden uns" in erfolg,
           f"({erfolg[:200]!r})")
    beleg = seite.inner_text(".beleg")
    pruefe("Beleg zeigt Vorgangsnummer", "Vorgangsnummer" in beleg, f"({beleg[:200]!r})")
    pruefe("Beleg zeigt das Fristdatum (Werktag)",
           re.search(r"Reserviert bis\s+(Mo|Di|Mi|Do|Fr), \d{2}\.\d{2}\.\d{4}", beleg) is not None, f"({beleg!r})")
    pruefe("Beleg zeigt den Abholwunsch mit Uhrzeit", "Abholung gewünscht" in beleg and "09:30 Uhr" in beleg, f"({beleg!r})")
    pruefe("Beleg zeigt die Positionen", "3 Stück gesamt" in beleg, f"({beleg!r})")
    pruefe("Beleg zeigt die Kontaktdaten zum Gegenlesen",
           "test@example.org" in beleg and "07721 123456" in beleg, f"({beleg!r})")
    pruefe("Hinweis auf Bildschirmfoto", "Bildschirmfoto" in erfolg)
    pruefe("Leiste zurueckgesetzt", "Noch nichts vorgemerkt" in seite.inner_text("#k-merk"))
    pruefe("Knopf zum Drucken der Bestätigung", seite.locator("#k-drucken").count() == 1)
    seite.click("#k-fertig"); seite.wait_for_timeout(300)
    pruefe("Schließen führt zurück an dieselbe Stelle", not seite.locator("#k-fenster").is_visible()
           and abs(seite.evaluate("window.scrollY") - vorher_y) < 5)
    pruefe("Knopf „nach oben“ nach langem Scrollen", seite.locator("#k-oben").is_visible())

    print("\n5b) Foto groß, Sortierung, Besichtigungshinweis")
    seite.evaluate("window.scrollTo(0, 0)"); seite.wait_for_timeout(300)
    seite.locator(".karte .bild img").first.click(); seite.wait_for_timeout(300)
    pruefe("Foto öffnet groß", seite.locator("#k-gross").is_visible())
    seite.keyboard.press("Escape"); seite.wait_for_timeout(200)
    pruefe("Esc schließt das Foto", not seite.locator("#k-gross").is_visible())
    seite.select_option("#k-sort", "ab"); seite.wait_for_timeout(400)
    erste_nr = seite.locator(".karte .nr").first.inner_text()
    sichtbar = [preise[n] for n in preise if n in set(seite.locator(".karte .nr").all_inner_texts())]
    pruefe("Preis absteigend: teuerster Artikel zuerst", preise.get(erste_nr, 0) == max(sichtbar),
           f"({erste_nr}, {preise.get(erste_nr)} von max {max(sichtbar)})")
    seite.select_option("#k-sort", "auf"); seite.wait_for_timeout(400)
    pruefe("Preis aufsteigend: günstigster zuerst",
           preise.get(seite.locator(".karte .nr").first.inner_text(), 99) == min(sichtbar))
    seite.select_option("#k-sort", ""); seite.wait_for_timeout(300)
    # ein Artikel zwischen 50 und 100 €: erreicht den Mindestbestellwert, aber keine Besichtigung
    mittel = [n for n, p in preise.items() if 50 <= p < 100]
    seite.fill("#k-q", "")
    for n in mittel:
        if seite.locator(f'input[data-menge="{n}"]').count():
            seite.locator(f'input[data-menge="{n}"]').fill("1")
            seite.locator(f'button[data-res="{n}"]').click(); break
    seite.wait_for_timeout(300)
    seite.click("#k-anfragen"); seite.wait_for_timeout(500)
    pruefe("unter 100 € pro Artikel: Hinweis statt Besichtigungsfrage",
           seite.locator("#k-bes").count() == 0 and "ab 100,00" in seite.inner_text("#k-dlg"))
    seite.keyboard.press("Escape"); seite.wait_for_timeout(200)
    seite.click("#k-leeren")
    seite.screenshot(path="/tmp/kikweb/t04-erfolg.png")

    print("\n6) Bestand nach der Reservierung")
    seite.reload(wait_until="networkidle")
    seite.wait_for_selector(".karte", timeout=20000)
    seite.wait_for_timeout(600)
    pruefe("nach dem Neuladen keine Sperrseite", seite.locator("#k-pw").count() == 0)

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
