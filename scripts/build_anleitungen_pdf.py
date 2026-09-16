"""Macht aus den Anleitungen (Markdown) lesbare PDFs im kikripp-Design.

    python3 scripts/build_anleitungen_pdf.py

Markdown ist reiner Text und lässt sich unter Windows nicht ohne Weiteres öffnen;
die PDFs kann man lesen, drucken und weiterleiten.
"""
import sys, os, subprocess, tempfile, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import AUSGABE, ASSETS, ROT, SCHWARZ, GRAU, LINIE, PAPIER, FIRMA
import markdown

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

ANLEITUNGEN = [
    ("WEBSHOP_EINRICHTEN.md", "A1_Webshop_einrichten.pdf",
     "Den Artikelkatalog auf kikripp.de in Betrieb nehmen"),
    ("ARTIKEL_VERWALTEN.md", "A2_Artikel_verwalten.pdf",
     "Artikel ändern, streichen und Verkäufe zurückholen"),
    ("FOTOGRAFIEREN.md", "A3_Fotografieren.pdf",
     "Aufnahmen, die sauber in den Katalog laufen"),
    ("ARBEITSANWEISUNG.md", "A4_Arbeitsanweisung.pdf",
     "Der ganze Ablauf auf einer Seite"),
]


def signet():
    """Das Bollenhut-Signet als eingebettete Datenadresse, damit das PDF eigenständig ist."""
    pfad = os.path.join(ASSETS, "signet.svg")
    if not os.path.exists(pfad):
        return ""
    with open(pfad, "rb") as f:
        return "data:image/svg+xml;base64," + base64.b64encode(f.read()).decode()


STIL = f"""
@page {{ size: A4; margin: 18mm 16mm 20mm; }}
* {{ box-sizing: border-box; }}
body {{ font: 10.5pt/1.62 "Helvetica Neue", Arial, sans-serif; color: {SCHWARZ};
        margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}

.kopf {{ display: flex; align-items: center; gap: 12px; border-bottom: 2.5px solid #{ROT};
         padding-bottom: 10px; margin-bottom: 22px; }}
.kopf img {{ height: 30px; }}
.kopf .wort {{ font-size: 17pt; font-weight: 800; letter-spacing: .10em; }}
.kopf .rechts {{ margin-left: auto; text-align: right; font-size: 8.5pt; color: #{GRAU}; line-height: 1.45; }}

h1 {{ font-size: 19pt; font-weight: 800; margin: 0 0 3px; line-height: 1.25; }}
.unter {{ font-size: 11pt; color: #{GRAU}; margin: 0 0 24px; }}

h2 {{ font-size: 13pt; font-weight: 800; margin: 26px 0 9px; padding-top: 12px;
      border-top: 1px solid #{LINIE}; page-break-after: avoid; }}
h2:first-of-type {{ border-top: 0; padding-top: 0; }}
/* Ein „---" direkt vor einer Überschrift ergäbe sonst zwei Linien übereinander. */
hr + h2 {{ border-top: 0; padding-top: 0; margin-top: 0; }}
h3 {{ font-size: 11pt; font-weight: 700; margin: 18px 0 6px; page-break-after: avoid; }}
p {{ margin: 0 0 10px; }}
ul, ol {{ margin: 0 0 12px; padding-left: 20px; }}
li {{ margin-bottom: 4px; }}
strong {{ font-weight: 700; }}
hr {{ border: 0; border-top: 1px solid #{LINIE}; margin: 22px 0; }}

code {{ font-family: "Consolas", "Courier New", monospace; font-size: 9.5pt;
        background: {PAPIER}; padding: 1px 4px; border-radius: 2px; }}
pre {{ background: {PAPIER}; border-left: 3px solid #{ROT}; padding: 10px 13px;
       margin: 0 0 13px; overflow-wrap: break-word; white-space: pre-wrap;
       page-break-inside: avoid; }}
pre code {{ background: none; padding: 0; font-size: 9.5pt; line-height: 1.5; }}

blockquote {{ margin: 0 0 13px; padding: 10px 14px; background: {PAPIER};
              border-left: 3px solid #{GRAU}; color: {SCHWARZ}; page-break-inside: avoid; }}
blockquote p {{ margin: 0 0 5px; }}
blockquote p:last-child {{ margin: 0; }}

table {{ border-collapse: collapse; width: 100%; margin: 0 0 15px; font-size: 9.5pt;
         page-break-inside: avoid; }}
th {{ background: {SCHWARZ}; color: #fff; text-align: left; font-weight: 700;
      padding: 7px 9px; }}
td {{ border: 1px solid #{LINIE}; padding: 6px 9px; vertical-align: top; }}
tr:nth-child(even) td {{ background: #FAFAFA; }}

.fuss {{ margin-top: 26px; padding-top: 9px; border-top: 1px solid #{LINIE};
         font-size: 8pt; color: #{GRAU}; }}
"""


def baue(md_datei, pdf_datei, untertitel):
    quelle = os.path.join(BASIS, md_datei)
    with open(quelle, encoding="utf-8") as f:
        roh = f.read()

    # Die erste Überschrift wird zum Titel, der Rest zum Inhalt.
    zeilen = roh.split("\n")
    titel = zeilen[0].lstrip("# ").strip() if zeilen[0].startswith("# ") else md_datei
    rumpf = "\n".join(zeilen[1:]).lstrip("\n")

    inhalt = markdown.markdown(rumpf, extensions=["tables", "fenced_code", "sane_lists"])
    html = f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<title>{titel}</title><style>{STIL}</style></head><body>
<div class="kopf">
  {'<img src="' + signet() + '" alt="">' if signet() else ''}
  <span class="wort">KIKRIPP</span>
  <span class="rechts">{FIRMA}<br>Betriebsauflösung</span>
</div>
<h1>{titel}</h1>
<p class="unter">{untertitel}</p>
{inhalt}
<div class="fuss">{FIRMA} · Stand {os.popen('date +%d.%m.%Y').read().strip()} ·
Diese Anleitung entsteht aus {md_datei} und wird bei Änderungen neu erzeugt.</div>
</body></html>"""

    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html)
        tmp = f.name

    ziel = os.path.join(AUSGABE, pdf_datei)
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={ziel}", "file://" + tmp],
                   check=True, capture_output=True, timeout=120)
    os.unlink(tmp)
    return ziel


if __name__ == "__main__":
    for md, pdf, unter in ANLEITUNGEN:
        if not os.path.exists(os.path.join(BASIS, md)):
            print(f"  übersprungen (fehlt): {md}")
            continue
        ziel = baue(md, pdf, unter)
        print(f"geschrieben: {ziel}  ({os.path.getsize(ziel)//1024} KB)")
