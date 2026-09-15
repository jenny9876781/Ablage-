"""Erzeugt 05_Arbeitsanweisung.pdf aus ARBEITSANWEISUNG.md – zum Ausdrucken und Aushändigen."""
import sys, os, subprocess, base64
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import AUSGABE, ASSETS, BASIS, ROT, SCHWARZ, PAPIER, GRAU, LINIE
import markdown

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
QUELLE = os.path.join(BASIS, "ARBEITSANWEISUNG.md")

with open(QUELLE, encoding="utf-8") as f:
    roh = f.read()
# Die Kopfzeile des Dokuments wird durch den gestalteten Titelblock ersetzt
zeilen = roh.split("\n")
start = next(i for i, z in enumerate(zeilen) if z.startswith("## 1."))
rumpf = "\n".join(zeilen[start:])

koerper = markdown.markdown(rumpf, extensions=["tables", "sane_lists"])
signet = base64.b64encode(open(os.path.join(ASSETS, "signet.svg"), "rb").read()).decode()

DOK = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 18mm 16mm 16mm 16mm; }}
@page :first {{ margin-top: 0; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Arial, Helvetica, sans-serif; font-size: 10pt; line-height: 1.55;
        color: #{SCHWARZ}; margin: 0; }}
h2 {{ font-size:15pt; color:#{SCHWARZ}; margin:26px 0 8px; padding-bottom:5px;
      border-bottom:2.5px solid #{ROT}; page-break-after:avoid; }}
.inhalt h1 {{ font-size:17pt; color:#fff; background:#{SCHWARZ}; margin:26px -6mm 14px;
      padding:10px 6mm; page-break-after:avoid; page-break-before:always; }}
h3 {{ font-size:11.5pt; margin:18px 0 5px; page-break-after:avoid; }}
p {{ margin:0 0 8px; }}
ul, ol {{ margin:0 0 10px; padding-left:20px; }}
li {{ margin-bottom:3px; }}
table {{ width:100%; border-collapse:collapse; font-size:9pt; margin:8px 0 14px;
         page-break-inside:avoid; }}
th {{ background:#{SCHWARZ}; color:#fff; text-align:left; padding:6px 8px; font-size:8.5pt; }}
td {{ border-bottom:1px solid #{LINIE}; padding:5px 8px; vertical-align:top; }}
tbody tr:nth-child(even) td {{ background:#FAFAFA; }}
blockquote {{ background:#{PAPIER}; border-left:3px solid #{ROT}; margin:10px 0 14px;
              padding:9px 13px; font-size:9.5pt; }}
blockquote p {{ margin:0; }}
code {{ background:#{PAPIER}; padding:1px 4px; border-radius:2px; font-size:9pt; }}
strong {{ color:#{SCHWARZ}; }}
hr {{ border:0; border-top:1px solid #{LINIE}; margin:18px 0; }}
a {{ color:#{ROT}; text-decoration:none; }}
.fuss {{ margin-top:22px; padding-top:9px; border-top:1px solid #{LINIE};
         font-size:8.5pt; color:#{GRAU}; }}
/* Titelblock zuletzt, damit er die allgemeinen Ueberschriftenregeln ueberschreibt */
.titel {{ background:#{SCHWARZ}; color:#fff; padding:24mm 16mm 18mm; margin:0 -16mm 14mm;
          page-break-after:avoid; page-break-before:auto; }}
.titel img {{ width:54px; margin:0 0 10px; }}
.titel .wort {{ font-weight:bold; letter-spacing:.14em; font-size:21pt; margin-bottom:26px; }}
.titel h1 {{ font-size:24pt; margin:0 0 10px; padding:0; line-height:1.18;
             background:none; color:#fff; page-break-before:auto; }}
.titel p {{ margin:0; color:#b9bcc2; font-size:10.5pt; line-height:1.5; }}
</style></head><body>
<div class="titel">
  <img src="data:image/svg+xml;base64,{signet}" alt="">
  <div class="wort">KIKRIPP</div>
  <h1>Arbeitsanweisung<br>Auflösung und Verkauf des Inventars</h1>
  <p>Kikripp GmbH · Hermann-Schwer-Str. 1 · 78048 Villingen-Schwenningen<br>
     Stand 15.09.2026 · Jenny Preisigke · jenny@kikripp.de · 07725 5179702</p>
</div>
<div class="inhalt">{koerper}</div>
<div class="fuss">Kikripp GmbH · Arbeitsanweisung Inventarauflösung · Stand 15.09.2026</div>
</body></html>"""

html_pfad = "/tmp/arbeitsanweisung.html"
with open(html_pfad, "w", encoding="utf-8") as f:
    f.write(DOK)
pdf = os.path.join(AUSGABE, "05_Arbeitsanweisung.pdf")
subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", html_pfad], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("geschrieben:", pdf, os.path.getsize(pdf) // 1024, "KB")
