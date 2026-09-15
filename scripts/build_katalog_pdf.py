"""Erzeugt 03_Katalog_Klinik_BEISPIEL.pdf - der Bildkatalog zum Verschicken."""
import sys, os, base64, subprocess, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, foto, BASIS, USt_SATZ

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
ANGEBOT_NR = "ANG-2026-0007"; DATUM = "15. September 2026"; GUELTIG = "30. September 2026"
EMPFAENGER = "Klinikum Musterstadt – Einkauf, Frau Muster"

def eur(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")

def b64(pfad):
    with open(pfad, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

artikel = [a for a in lade_artikel() if a["Kanal"] == "Klinik" and a["Status"] != "verkauft"]
E = html.escape

karten = []
for i, a in enumerate(artikel, start=1):
    rest = (a["Menge"] or 0) - (a["Verkauft_Menge"] or 0)
    p = foto(a["ArtNr"])
    bild = f'<img src="{b64(p)}" alt="">' if p else '<div class="kein-bild">kein Foto</div>'
    badge = ('<span class="badge res">reserviert</span>' if a["Status"] == "reserviert"
             else '<span class="badge frei">verfügbar</span>')
    vhb = ' <span class="vhb">VHB</span>' if a["Preisbasis"] == "VHB" else ""
    karten.append(f"""
    <div class="karte">
      <div class="bild">{bild}<span class="pos">{i:02d}</span></div>
      <div class="inhalt">
        <div class="kopfzeile"><span class="artnr">{E(a['ArtNr'])}</span>{badge}</div>
        <h3>{E(a['Bezeichnung'])}</h3>
        <p class="beschr">{E(a['Beschreibung'])}</p>
        <table class="meta">
          <tr><td>Zustand</td><td>{E(a['Zustand'])}</td></tr>
          <tr><td>Verfügbar</td><td>{rest} {E(a['Einheit'])}</td></tr>
          <tr><td>Standort</td><td>{E(a['Raum'])}</td></tr>
          <tr><td>Lieferung</td><td>{E(a['Versand'])}</td></tr>
        </table>
        <div class="preis"><span class="wert">{eur(a['Preis_netto'])}{vhb}</span>
          <span class="einheit">netto je {E(a['Einheit'])}</span></div>
      </div>
    </div>""")

zeilen = "".join(
    f"<tr><td>{i:02d}</td><td>{E(a['ArtNr'])}</td><td>{E(a['Bezeichnung'])}</td>"
    f"<td class='z'>{(a['Menge'] or 0) - (a['Verkauft_Menge'] or 0)} {E(a['Einheit'])}</td>"
    f"<td class='z'>{E(a['Zustand'])}</td><td class='r'>{eur(a['Preis_netto'])}"
    f"{' VHB' if a['Preisbasis']=='VHB' else ''}</td><td class='r'>"
    f"{eur(a['Preis_netto'] * ((a['Menge'] or 0) - (a['Verkauft_Menge'] or 0)))}</td></tr>"
    for i, a in enumerate(artikel, start=1))
gesamt = sum(a["Preis_netto"] * ((a["Menge"] or 0) - (a["Verkauft_Menge"] or 0)) for a in artikel)

DOK = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 14mm 12mm 16mm 12mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Arial, Helvetica, sans-serif; color:#22262d; margin:0; font-size:10pt; }}
h1 {{ font-size:22pt; color:#1f3864; margin:0 0 4px; }}
.sub {{ color:#6b7280; font-size:10.5pt; margin:0 0 18px; }}
.kopf {{ border-bottom:3px solid #1f3864; padding-bottom:12px; margin-bottom:16px; }}
.infobox {{ display:flex; gap:10px; margin-bottom:16px; }}
.infobox div {{ flex:1; background:#f3f5f9; border-left:3px solid #2e5a9c; padding:8px 10px; }}
.infobox b {{ display:block; font-size:8pt; text-transform:uppercase; letter-spacing:.5px;
              color:#2e5a9c; margin-bottom:2px; }}
.intro {{ background:#fff8e6; border:1px solid #f0d89b; padding:10px 12px; margin-bottom:18px;
          font-size:9.5pt; line-height:1.5; }}
.raster {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
.karte {{ border:1px solid #d8dde6; border-radius:4px; overflow:hidden; break-inside:avoid;
          page-break-inside:avoid; display:flex; flex-direction:column; }}
.bild {{ position:relative; height:112px; background:#eef1f6; overflow:hidden; }}
.bild img {{ width:100%; height:112px; object-fit:cover; display:block; }}
.pos {{ position:absolute; left:0; top:0; background:#1f3864; color:#fff; font-size:9pt;
        font-weight:bold; padding:3px 8px; }}
.inhalt {{ padding:8px 10px 10px; display:flex; flex-direction:column; flex:1; }}
.kopfzeile {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:3px; }}
.artnr {{ font-size:8.5pt; color:#6b7280; letter-spacing:.5px; }}
.badge {{ font-size:7.5pt; padding:2px 6px; border-radius:9px; font-weight:bold; }}
.badge.frei {{ background:#e2efda; color:#37672a; }}
.badge.res {{ background:#fff2cc; color:#8a6400; }}
h3 {{ font-size:11pt; margin:0 0 3px; color:#1f3864; }}
.beschr {{ font-size:8.5pt; color:#4b5563; margin:0 0 6px; line-height:1.35; }}
.meta {{ width:100%; border-collapse:collapse; font-size:8.5pt; margin-bottom:7px; }}
.meta td {{ padding:1.5px 0; vertical-align:top; }}
.meta td:first-child {{ color:#9aa2af; width:66px; }}
.preis {{ margin-top:auto; border-top:1px solid #e5e8ee; padding-top:6px; }}
.preis .wert {{ font-size:13pt; font-weight:bold; color:#1f3864; }}
.vhb {{ font-size:8pt; font-weight:normal; color:#8a6400; background:#fff2cc;
        padding:1px 5px; border-radius:3px; vertical-align:middle; }}
.preis .einheit {{ display:block; font-size:8pt; color:#9aa2af; }}
.neue-seite {{ page-break-before:always; }}
table.liste {{ width:100%; border-collapse:collapse; font-size:9pt; margin-top:8px; }}
table.liste th {{ background:#2e5a9c; color:#fff; text-align:left; padding:6px 7px; font-size:8.5pt; }}
table.liste td {{ border-bottom:1px solid #e5e8ee; padding:5px 7px; }}
table.liste tr:nth-child(even) td {{ background:#f7f9fc; }}
td.r, th.r {{ text-align:right; }} td.z, th.z {{ text-align:center; }}
tr.summe td {{ font-weight:bold; background:#d9e2f3 !important; border-top:2px solid #1f3864; }}
h2 {{ font-size:14pt; color:#1f3864; margin:0 0 2px; }}
.agb {{ font-size:8.5pt; color:#6b7280; line-height:1.55; margin-top:18px;
        border-top:1px solid #e5e8ee; padding-top:10px; }}
.agb b {{ color:#22262d; }}
</style></head><body>

<div class="kopf">
  <h1>Artikelkatalog aus Betriebsauflösung</h1>
  <p class="sub">Kinderkrippe Musterstadt GmbH · Auswahl für {E(EMPFAENGER)}</p>
</div>

<div class="infobox">
  <div><b>Angebot-Nr.</b>{ANGEBOT_NR}</div>
  <div><b>Datum</b>{DATUM}</div>
  <div><b>Gültig bis</b>{GUELTIG}</div>
  <div><b>Positionen</b>{len(artikel)}</div>
</div>

<div class="intro">
  <b>So können Sie auswählen:</b> Bitte notieren Sie die Positionsnummern und Wunschmengen der
  Artikel, die für Sie in Frage kommen – oder nutzen Sie die beiliegende Excel-Liste, in der Sie
  die Mengen direkt eintragen können. Wir bestätigen Ihnen die Reservierung anschließend
  schriftlich und stimmen einen Abholtermin ab. Alle Preise verstehen sich <b>netto zzgl. 19&nbsp;% USt</b>.
  Rückfragen jederzeit an J. Preisigke, 0123&nbsp;456789, info@kikripp.de.
</div>

<div class="raster">{''.join(karten)}</div>

<div class="neue-seite">
  <h2>Positionsübersicht</h2>
  <p class="sub">Alle Artikel dieses Angebots auf einen Blick</p>
  <table class="liste">
    <tr><th class="z">Pos</th><th>ArtNr</th><th>Bezeichnung</th><th class="z">Verfügbar</th>
        <th class="z">Zustand</th><th class="r">Einzelpreis netto</th><th class="r">Gesamt netto</th></tr>
    {zeilen}
    <tr class="summe"><td colspan="6">Gesamtwert bei Abnahme aller Positionen (netto)</td>
        <td class="r">{eur(gesamt)}</td></tr>
    <tr class="summe"><td colspan="6">zzgl. {int(USt_SATZ*100)} % Umsatzsteuer</td>
        <td class="r">{eur(gesamt*USt_SATZ)}</td></tr>
    <tr class="summe"><td colspan="6">Gesamt brutto</td>
        <td class="r">{eur(gesamt*(1+USt_SATZ))}</td></tr>
  </table>

  <div class="agb">
    <b>Verkaufsbedingungen.</b> Der Verkauf erfolgt aus einer Betriebsauflösung unter Ausschluss
    jeglicher Gewährleistung; es handelt sich durchweg um gebrauchte Gegenstände, die in dem
    Zustand verkauft werden, in dem sie sich befinden. Das Angebot ist freibleibend, Zwischenverkauf
    vorbehalten. Eine Reservierung wird erst mit unserer schriftlichen Bestätigung verbindlich.
    Abholung nach Terminvereinbarung; Demontage, Verladung und Transport erfolgen durch den Käufer
    auf eigene Kosten und Gefahr. Elektrogeräte werden ohne Prüfnachweis nach DGUV V3 übergeben;
    der Anschluss von Starkstromgeräten ist durch einen Fachbetrieb vorzunehmen. Die Rechnung wird
    nach Abholung gestellt, zahlbar innerhalb von 14 Tagen ohne Abzug. Das Eigentum geht erst mit
    vollständiger Bezahlung über.<br><br>
    <b>Kinderkrippe Musterstadt GmbH</b> · Musterstraße 1 · 12345 Musterstadt ·
    Geschäftsführer: M. Mustermann · Amtsgericht Musterstadt HRB 12345 · USt-IdNr. DE123456789
  </div>
</div>
</body></html>"""

html_pfad = "/tmp/katalog.html"
with open(html_pfad, "w", encoding="utf-8") as f:
    f.write(DOK)
pdf = os.path.join(BASIS, "ausgabe", "03_Katalog_Klinik_BEISPIEL.pdf")
subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", html_pfad], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("geschrieben:", pdf, os.path.getsize(pdf) // 1024, "KB")
