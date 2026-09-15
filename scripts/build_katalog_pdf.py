"""Erzeugt 03_Katalog_Klinik.pdf – Bildkatalog nach Räumen, mit Positionsliste und Paketangebot."""
import sys, os, base64, subprocess, html, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (lade_artikel, foto, AUSGABE, USt_SATZ, PAKETRABATT, eur, FIRMA, STRASSE,
                 PLZ_ORT as ORT, ANSPRECH as ANSPRECHPARTNER, TELEFON, EMAIL, EMPFAENGER,
                 ANGEBOT_NR, DATUM, GUELTIG)
from PIL import Image

CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
E = html.escape

def b64(pfad, breite=560):
    with Image.open(pfad) as im:
        im.thumbnail((breite, breite))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

artikel = lade_artikel()
RAUM_REIHENFOLGE = []
for a in artikel:
    if a["Raum"] not in RAUM_REIHENFOLGE:
        RAUM_REIHENFOLGE.append(a["Raum"])

abschnitte, pos = [], 0
for raum in RAUM_REIHENFOLGE:
    karten = []
    for a in [x for x in artikel if x["Raum"] == raum]:
        pos += 1
        a["_pos"] = pos
        p = foto(a["Foto"])
        bild = f'<img src="{b64(p)}" alt="">' if p else '<div class="kein"></div>'
        vhb = ' <span class="vhb">VHB</span>' if a["Preisbasis"] == "VHB" else ""
        klasse = '<span class="badge a">Designstück</span>' if a["Wertklasse"] == "A" else ""
        karten.append(f"""
        <div class="karte">
          <div class="bild">{bild}<span class="pos">{a['_pos']:03d}</span>{klasse}</div>
          <div class="inhalt">
            <div class="artnr">{E(a['ArtNr'])}</div>
            <h3>{E(a['Bezeichnung'])}</h3>
            <p class="beschr">{E(a['Beschreibung'])}</p>
            <table class="meta">
              <tr><td>Zustand</td><td>{E(a['Zustand'])}</td></tr>
              <tr><td>Menge</td><td>{a['Menge']} {E(a['Einheit'])}</td></tr>
              <tr><td>Lieferung</td><td>{E(a['Versand'])}</td></tr>
            </table>
            <div class="preis"><span class="wert">{eur(a['Preis_netto'])}{vhb}</span>
              <span class="eh">netto je {E(a['Einheit'])}</span></div>
          </div>
        </div>""")
    abschnitte.append(f'<h2 class="raum">{E(raum)}<span>{len(karten)} Positionen</span></h2>'
                      f'<div class="raster">{"".join(karten)}</div>')

zeilen = "".join(
    f"<tr><td class='z'>{a['_pos']:03d}</td><td>{E(a['ArtNr'])}</td><td>{E(a['Bezeichnung'])}"
    f"{' <b>·  Designstück</b>' if a['Wertklasse']=='A' else ''}</td><td>{E(a['Raum'])}</td>"
    f"<td class='z'>{a['Menge']} {E(a['Einheit'])}</td><td class='z'>{E(a['Zustand'])}</td>"
    f"<td class='r'>{eur(a['Preis_netto'])}{' VHB' if a['Preisbasis']=='VHB' else ''}</td>"
    f"<td class='r'>{eur(a['Positionswert'])}</td></tr>"
    for a in sorted(artikel, key=lambda x: x["_pos"]))

gesamt = sum(a["Positionswert"] for a in artikel)
paket = gesamt * (1 - PAKETRABATT)

DOK = f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 13mm 11mm 15mm 11mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Arial, Helvetica, sans-serif; color:#22262d; margin:0; font-size:10pt; }}
h1 {{ font-size:21pt; color:#1f3864; margin:0 0 4px; }}
.sub {{ color:#6b7280; font-size:10.5pt; margin:0; }}
.kopf {{ border-bottom:3px solid #1f3864; padding-bottom:11px; margin-bottom:14px; }}
.infobox {{ display:flex; gap:8px; margin-bottom:14px; }}
.infobox div {{ flex:1; background:#f3f5f9; border-left:3px solid #2e5a9c; padding:7px 9px; font-size:9.5pt; }}
.infobox b {{ display:block; font-size:7.5pt; text-transform:uppercase; letter-spacing:.5px;
              color:#2e5a9c; margin-bottom:2px; }}
.intro {{ background:#fff8e6; border:1px solid #f0d89b; padding:9px 11px; margin-bottom:8px;
          font-size:9pt; line-height:1.5; }}
h2.raum {{ font-size:12.5pt; color:#1f3864; margin:14px 0 7px; padding-bottom:4px;
           border-bottom:1.5px solid #d8dde6; display:flex; justify-content:space-between;
           align-items:baseline; break-after:avoid; page-break-after:avoid; }}
h2.raum span {{ font-size:8.5pt; font-weight:normal; color:#9aa2af; }}
.raster {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }}
.karte {{ border:1px solid #d8dde6; border-radius:4px; overflow:hidden; break-inside:avoid;
          page-break-inside:avoid; display:flex; flex-direction:column; }}
.bild {{ position:relative; height:86px; background:#eef1f6; }}
.bild img {{ width:100%; height:86px; object-fit:cover; display:block; }}
.kein {{ height:86px; }}
.pos {{ position:absolute; left:0; top:0; background:#1f3864; color:#fff; font-size:8pt;
        font-weight:bold; padding:2px 6px; }}
.badge.a {{ position:absolute; right:4px; top:4px; background:#f8cbad; color:#7a3b00;
            font-size:6.5pt; font-weight:bold; padding:2px 5px; border-radius:8px; }}
.inhalt {{ padding:6px 8px 8px; display:flex; flex-direction:column; flex:1; }}
.artnr {{ font-size:7.5pt; color:#9aa2af; letter-spacing:.4px; }}
h3 {{ font-size:9.5pt; margin:1px 0 3px; color:#1f3864; line-height:1.2; }}
.beschr {{ font-size:7.5pt; color:#4b5563; margin:0 0 5px; line-height:1.3; }}
.meta {{ width:100%; border-collapse:collapse; font-size:7.5pt; margin-bottom:5px; }}
.meta td {{ padding:1px 0; vertical-align:top; }}
.meta td:first-child {{ color:#9aa2af; width:50px; }}
.preis {{ margin-top:auto; border-top:1px solid #e5e8ee; padding-top:4px; }}
.preis .wert {{ font-size:11pt; font-weight:bold; color:#1f3864; }}
.vhb {{ font-size:7pt; font-weight:normal; color:#8a6400; background:#fff2cc;
        padding:1px 4px; border-radius:3px; vertical-align:middle; }}
.preis .eh {{ display:block; font-size:7pt; color:#9aa2af; }}
.neue-seite {{ page-break-before:always; }}
table.liste {{ width:100%; border-collapse:collapse; font-size:8pt; margin-top:6px; }}
table.liste th {{ background:#2e5a9c; color:#fff; text-align:left; padding:5px 6px; font-size:7.5pt; }}
table.liste td {{ border-bottom:1px solid #e5e8ee; padding:3px 6px; }}
table.liste tr:nth-child(even) td {{ background:#f7f9fc; }}
td.r, th.r {{ text-align:right; }} table.liste td:nth-child(2) {{ white-space:nowrap; }} td.z, th.z {{ text-align:center; }}
tr.summe td {{ font-weight:bold; background:#d9e2f3 !important; border-top:2px solid #1f3864; }}
tr.paket td {{ font-weight:bold; background:#fff2cc !important; }}
.agb {{ font-size:8pt; color:#6b7280; line-height:1.55; margin-top:16px;
        border-top:1px solid #e5e8ee; padding-top:9px; }}
.agb b {{ color:#22262d; }}
</style></head><body>

<div class="kopf">
  <h1>Artikelkatalog aus der Betriebsauflösung</h1>
  <p class="sub">{E(FIRMA)} · Auswahl für {E(EMPFAENGER)}</p>
</div>

<div class="infobox">
  <div><b>Angebot-Nr.</b>{ANGEBOT_NR}</div>
  <div><b>Datum</b>{DATUM}</div>
  <div><b>Gültig bis</b>{GUELTIG}</div>
  <div><b>Positionen</b>{len(artikel)}</div>
  <div><b>Einheiten</b>{sum(a['Menge'] for a in artikel)}</div>
</div>

<div class="intro">
  <b>So können Sie auswählen:</b> Notieren Sie die Positionsnummern und Wunschmengen – oder nutzen Sie
  die beiliegende Excel-Liste, in der Sie die Mengen direkt eintragen und die Summe automatisch berechnet
  wird. Sie können einzelne Positionen wählen oder den <b>gesamten Bestand als Paket</b> übernehmen
  (Paketpreis am Ende dieses Katalogs). Alle Preise verstehen sich <b>netto zzgl. {int(USt_SATZ*100)}&nbsp;% USt</b>.
  Mit <span style="background:#f8cbad;padding:1px 5px;border-radius:8px;font-size:7.5pt;font-weight:bold;color:#7a3b00">Designstück</span>
  markierte Positionen sind Markenmöbel (Vitra, USM Haller, Kartell) bzw. hochwertige Einzelstücke.
  Rückfragen an {E(ANSPRECHPARTNER)}, {TELEFON}, {EMAIL}.
</div>

{''.join(abschnitte)}

<div class="neue-seite">
  <h1 style="font-size:16pt">Positionsübersicht</h1>
  <p class="sub">Alle {len(artikel)} Positionen auf einen Blick</p>
  <table class="liste">
    <tr><th class="z">Pos</th><th>ArtNr</th><th>Bezeichnung</th><th>Raum</th><th class="z">Menge</th>
        <th class="z">Zustand</th><th class="r">Einzelpreis netto</th><th class="r">Positionswert netto</th></tr>
    {zeilen}
    <tr class="summe"><td colspan="7">A · Gesamtwert aller Positionen zu Einzelpreisen (netto)</td>
        <td class="r">{eur(gesamt)}</td></tr>
    <tr class="summe"><td colspan="7">zzgl. {int(USt_SATZ*100)} % Umsatzsteuer</td>
        <td class="r">{eur(gesamt*USt_SATZ)}</td></tr>
    <tr class="summe"><td colspan="7">Gesamt brutto</td>
        <td class="r">{eur(gesamt*(1+USt_SATZ))}</td></tr>
    <tr class="paket"><td colspan="7">B · Paketpreis bei Übernahme des gesamten Bestands (netto,
        abzüglich {int(PAKETRABATT*100)} % Paketnachlass)</td>
        <td class="r">{eur(paket)}</td></tr>
    <tr class="paket"><td colspan="7">Paketpreis brutto</td>
        <td class="r">{eur(paket*(1+USt_SATZ))}</td></tr>
  </table>

  <div class="agb">
    <b>Verkaufsbedingungen.</b> Der Verkauf erfolgt aus einer Betriebsauflösung unter Ausschluss jeglicher
    Gewährleistung; es handelt sich durchweg um gebrauchte Gegenstände, die in dem Zustand verkauft werden,
    in dem sie sich befinden. Das Angebot ist freibleibend, Zwischenverkauf vorbehalten. Eine Reservierung
    wird erst mit unserer schriftlichen Bestätigung verbindlich. Abholung nach Terminvereinbarung; Demontage,
    Verladung und Transport erfolgen durch den Käufer auf eigene Kosten und Gefahr. Elektrogeräte werden ohne
    Prüfnachweis nach DGUV V3 übergeben. Die Rechnung wird nach Abholung gestellt, zahlbar innerhalb von
    14 Tagen ohne Abzug. Das Eigentum geht erst mit vollständiger Bezahlung über. Das Paketangebot gilt für
    die Übernahme sämtlicher Positionen in einem Zug, inklusive Abholung innerhalb von zwei Wochen nach
    Zuschlag.<br><br>
    <b>{E(FIRMA)}</b> · {E(STRASSE)} · {E(ORT)} · {E(ANSPRECHPARTNER)} · {TELEFON} · {EMAIL}
  </div>
</div>
</body></html>"""

html_pfad = "/tmp/katalog_klinik.html"
with open(html_pfad, "w", encoding="utf-8") as f:
    f.write(DOK)
pdf = os.path.join(AUSGABE, "03_Katalog_Klinik.pdf")
subprocess.run([CHROME, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                f"--print-to-pdf={pdf}", html_pfad], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("geschrieben:", pdf, os.path.getsize(pdf) // 1024, "KB")
