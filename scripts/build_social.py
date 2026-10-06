"""Erzeugt Bilder für WhatsApp-Status und Instagram (Story 1080×1920, Beitrag 1080×1350).

Die Bilder entstehen als HTML und werden mit Chromium abfotografiert. Fotos kommen aus
fotos/, nur Artikel ohne Personen. Ausgabe: ausgabe/social/*.png
Aufruf: python3 scripts/build_social.py
"""
import base64, os
from playwright.sync_api import sync_playwright

WURZEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIEL = os.path.join(WURZEL, "ausgabe", "social")
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
LINK = "kikripp.de/artikelkatalog"
ORT = "Abholung in Villingen-Schwenningen"

# (Datei, Format, Kopfzeile klein, Überschrift, Fotos mit optionalem Bildausschnitt, Stichworte)
MOTIVE = [
    ("1_Story_Alles_muss_raus", "story", "Inventarverkauf", "Alles muss raus!",
     [("F-019", "50% 60%"), ("F-176", "50% 60%"), ("F-522", "40% 50%"),
      ("F-102", "50% 40%"), ("F-017", "50% 72%"), ("F-596", "50% 55%")],
     "Möbel · Kita · Garten · Deko"),
    ("2_Story_Moebel", "story", "Alles muss raus!", "Möbel & Wohnen",
     [("F-019", "50% 60%"), ("F-043", "50% 55%"), ("F-058", "40% 50%"),
      ("F-007", "50% 50%"), ("F-059", "50% 55%"), ("F-057", "50% 60%")],
     "Sofas · Tische · Stühle · Leuchten"),
    ("3_Story_Kita_Spielplatz", "story", "Alles muss raus!", "Kita & Spielplatz",
     [("F-522", "40% 50%"), ("F-176", "50% 60%"), ("F-356", "50% 55%"),
      ("F-599", "50% 35%"), ("F-163", "50% 50%"), ("F-600", "50% 55%")],
     "Spielküchen · Betten · Fahrzeuge · Spielturm"),
    ("4_Story_Garten", "story", "Alles muss raus!", "Garten & Terrasse",
     [("F-111", "50% 50%"), ("F-102", "50% 40%"), ("F-105", "50% 50%"),
      ("F-536", "50% 50%"), ("F-095", "50% 50%"), ("F-614", "50% 45%")],
     "Grill · Liegen · Sitzgruppen · Spielgeräte"),
    ("5_Story_Kunst_Deko", "story", "Alles muss raus!", "Kunst & Deko",
     [("F-037", "50% 35%"), ("F-091", "50% 35%"), ("F-012", "50% 50%"),
      ("F-258", "50% 35%"), ("F-397", "50% 30%"), ("F-013", "50% 50%")],
     "Bilder · Leuchten · Schwarzwald-Charme"),
    ("6_Story_Spielzeug_November", "story", "Bald im Katalog", "Spielzeug ab November",
     [], "Jetzt schon reinschauen – Möbel, Kita, Garten und Deko gibt es ab sofort"),
    ("7_Beitrag_Alles_muss_raus", "beitrag", "Inventarverkauf", "Alles muss raus!",
     [("F-019", "50% 60%"), ("F-176", "50% 60%"), ("F-102", "50% 40%"), ("F-017", "50% 72%")],
     "Möbel · Kita · Garten · Deko"),
]

CSS = """
@font-face { font-family: 'Archivo Black'; src: url(%(archivo)s) format('woff2'); }
@font-face { font-family: Inter; font-weight: 100 900; src: url(%(inter)s) format('woff2'); }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { width: %(w)dpx; height: %(h)dpx; background: #C8102E; font-family: Inter, sans-serif; color: #fff;
       display: flex; flex-direction: column; padding: %(oben)dpx 64px %(unten)dpx; overflow: hidden; }
.klein { font-weight: 800; letter-spacing: .18em; text-transform: uppercase; font-size: 34px; opacity: .92; }
h1 { font-family: 'Archivo Black', sans-serif; font-weight: 400; line-height: .98; margin-top: 14px;
     font-size: %(h1)dpx; letter-spacing: -.01em; }
.raster { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 40px; flex: 1; min-height: 0; }
.raster div { background-size: cover; border-radius: 22px; border: 6px solid #fff; }
.stich { margin-top: 34px; font-size: 38px; font-weight: 700; }
.ort { margin-top: 8px; font-size: 32px; font-weight: 500; opacity: .92; }
.link { margin-top: 30px; background: #fff; color: #C8102E; border-radius: 999px; text-align: center;
        font-weight: 800; font-size: 46px; padding: 24px 20px; }
.unter { margin-top: 14px; text-align: center; font-size: 30px; font-weight: 700; }
.leer { flex: 1; display: flex; align-items: center; justify-content: center; }
.leer span { font-size: 460px; }
"""

def bild(nr):
    with open(os.path.join(WURZEL, "fotos", nr + ".jpg"), "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

def schrift(name):
    # Schriften liegen in assets/schriften (SIL Open Font License), eingebettet statt nachgeladen
    with open(os.path.join(WURZEL, "assets", "schriften", name), "rb") as f:
        return "data:font/woff2;base64," + base64.b64encode(f.read()).decode()

def html(fmt, klein, titel, fotos, stich):
    story = fmt == "story"
    masse = dict(w=1080, h=1920 if story else 1350,
                 # Story: oben und unten verdecken WhatsApp/Instagram ihre Bedienleisten
                 oben=230 if story else 64, unten=300 if story else 56,
                 h1=124 if len(titel) < 18 else 104,
                 archivo=schrift("ArchivoBlack.woff2"), inter=schrift("Inter.woff2"))
    if not story: masse["h1"] = 96
    kacheln = "".join(f'<div style="background-image:url({bild(nr)});background-position:{pos}"></div>'
                      for nr, pos in fotos)
    mitte = f'<div class="raster">{kacheln}</div>' if fotos else '<div class="leer"><span>🧸</span></div>'
    unter = '<div class="unter">Jetzt online reservieren</div>' if story else ""
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS % masse}</style></head><body>"
            f"<div class='klein'>{klein}</div><h1>{titel}</h1>{mitte}"
            f"<div class='stich'>{stich}</div><div class='ort'>{ORT}</div>"
            f"<div class='link'>{LINK}</div>{unter}</body></html>")

def main():
    os.makedirs(ZIEL, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        for name, fmt, klein, titel, fotos, stich in MOTIVE:
            h = 1920 if fmt == "story" else 1350
            s = b.new_page(viewport={"width": 1080, "height": h})
            s.set_content(html(fmt, klein, titel, fotos, stich), wait_until="networkidle")
            s.evaluate("document.fonts.ready.then(() => true)")
            assert s.evaluate("document.fonts.check('40px \"Archivo Black\"')"), "Schrift fehlt"
            s.screenshot(path=os.path.join(ZIEL, name + ".png"))
            s.close()
            print("  ", name)
        b.close()

if __name__ == "__main__":
    main()
