"""Erzeugt 04_Webkatalog_MOCKUP.html - Klickbares Muster fuer den Katalog auf kikripp.de."""
import sys, os, json, base64, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, foto, BASIS, USt_SATZ

def b64(p):
    with open(p, "rb") as f:
        return "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()

daten = []
for a in lade_artikel():
    rest = (a["Menge"] or 0) - (a["Verkauft_Menge"] or 0)
    p = foto(a["ArtNr"])
    daten.append({
        "nr": a["ArtNr"], "titel": a["Bezeichnung"], "beschr": a["Beschreibung"],
        "kat": a["Kategorie"], "raum": a["Raum"], "zustand": a["Zustand"],
        "menge": rest, "einheit": a["Einheit"], "preis": a["Preis_netto"],
        "basis": a["Preisbasis"], "versand": a["Versand"],
        "status": "verkauft" if rest <= 0 or a["Status"] == "verkauft" else a["Status"],
        "bild": b64(p) if p else "",
    })
kategorien = sorted({d["kat"] for d in daten})
raeume = sorted({d["raum"] for d in daten})

DOK = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Artikelkatalog – Kinderkrippe Musterstadt</title>
<style>
:root{--navy:#1f3864;--blau:#2e5a9c;--rand:#dfe3ea;--grau:#6b7280;--bg:#f5f7fa;}
*{box-sizing:border-box}
body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
     background:var(--bg);color:#22262d}
.wrap{max-width:1180px;margin:0 auto;padding:0 16px}
header{background:var(--navy);color:#fff;padding:22px 0}
header h1{margin:0;font-size:21px} header p{margin:4px 0 0;opacity:.75;font-size:14px}
.demo{background:#8a6400;color:#fff;font-size:13px;padding:7px 0;text-align:center}
/* Login */
#login{position:fixed;inset:0;background:var(--navy);display:flex;align-items:center;
       justify-content:center;z-index:50;padding:16px}
#login .box{background:#fff;border-radius:10px;padding:28px;max-width:380px;width:100%;
            box-shadow:0 18px 50px rgba(0,0,0,.3)}
#login h2{margin:0 0 6px;font-size:19px;color:var(--navy)}
#login p{margin:0 0 18px;color:var(--grau);font-size:14px}
input,select,textarea{width:100%;padding:10px 12px;border:1px solid var(--rand);border-radius:6px;
                      font:inherit;background:#fff}
button{background:var(--blau);color:#fff;border:0;border-radius:6px;padding:10px 18px;
       font:inherit;font-weight:600;cursor:pointer}
button:hover{background:var(--navy)}
button.sek{background:#fff;color:var(--navy);border:1px solid var(--rand)}
.hinweis{font-size:13px;color:var(--grau);margin-top:12px}
/* Filter */
.filter{background:#fff;border-bottom:1px solid var(--rand);padding:12px 0;position:sticky;
        top:env(safe-area-inset-top,0px);z-index:20}
.filter .zeile{display:flex;gap:8px;flex-wrap:wrap}
.filter input[type=search]{flex:2 1 220px} .filter select{flex:1 1 150px}
.chk{display:flex;align-items:center;gap:6px;font-size:14px;color:var(--grau);white-space:nowrap}
.chk input{width:auto}
.zaehler{font-size:14px;color:var(--grau);padding:10px 0 0}
/* Karten */
.raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;
        padding:14px 0 120px}
.karte{background:#fff;border:1px solid var(--rand);border-radius:8px;overflow:hidden;
       display:flex;flex-direction:column}
.karte.weg{opacity:.5}
.bild{position:relative;aspect-ratio:4/3;background:#eef1f6}
.bild img{width:100%;height:100%;object-fit:cover;display:block}
.badge{position:absolute;top:8px;right:8px;font-size:11px;font-weight:700;padding:3px 9px;
       border-radius:10px;background:#e2efda;color:#37672a}
.badge.res{background:#fff2cc;color:#8a6400} .badge.verk{background:#e5e7eb;color:#4b5563}
.nr{position:absolute;top:0;left:0;background:var(--navy);color:#fff;font-size:11px;padding:3px 8px}
.txt{padding:11px 13px 13px;display:flex;flex-direction:column;flex:1}
.txt h3{margin:0 0 3px;font-size:15.5px;color:var(--navy)}
.txt .b{font-size:13px;color:var(--grau);margin:0 0 9px}
.meta{font-size:12.5px;color:var(--grau);display:flex;gap:10px;flex-wrap:wrap;margin-bottom:9px}
.meta span{background:var(--bg);padding:2px 8px;border-radius:4px}
.preis{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;gap:8px;
       border-top:1px solid #eef0f4;padding-top:9px}
.preis b{font-size:18px;color:var(--navy);display:block}
.preis small{color:var(--grau);font-size:11.5px}
.mengen{display:flex;gap:6px;align-items:center;margin-top:9px}
.mengen input{width:88px;text-align:center;padding:10px 6px}
.mengen button{padding:8px 12px;font-size:14px;flex:1}
/* Merkzettel */
.leiste{position:fixed;left:0;right:0;bottom:0;background:#fff;border-top:1px solid var(--rand);
        box-shadow:0 -6px 24px rgba(0,0,0,.08);padding:12px 0
        calc(12px + env(safe-area-inset-bottom,0px));z-index:30}
.leiste .inner{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.leiste .sum{flex:1;font-size:14px}
.leiste .sum b{font-size:17px;color:var(--navy)}
dialog{border:0;border-radius:10px;padding:0;max-width:540px;width:calc(100% - 32px)}
dialog::backdrop{background:rgba(15,23,42,.55)}
.dlg{padding:22px} .dlg h2{margin:0 0 4px;font-size:19px;color:var(--navy)}
.dlg p.s{margin:0 0 16px;color:var(--grau);font-size:14px}
.feld{margin-bottom:11px} .feld label{display:block;font-size:13px;font-weight:600;margin-bottom:4px}
.pos{background:var(--bg);border-radius:6px;padding:10px 12px;font-size:13.5px;margin-bottom:14px}
.pos div{display:flex;justify-content:space-between;padding:2px 0}
.leer{text-align:center;color:var(--grau);padding:50px 0}
@media(max-width:560px){.leiste .sum{flex:1 1 100%}}
</style></head><body>

<div id="login"><div class="box">
  <h2>Artikelkatalog Betriebsauflösung</h2>
  <p>Dieser Bereich ist geschützt. Bitte geben Sie das Passwort ein, das Sie von uns erhalten haben.</p>
  <form onsubmit="event.preventDefault();document.getElementById('login').remove()">
    <div class="feld"><input type="password" placeholder="Passwort" autofocus></div>
    <button style="width:100%">Katalog öffnen</button>
  </form>
  <p class="hinweis">Muster-Ansicht – ein beliebiges Passwort öffnet den Katalog.</p>
</div></div>

<div class="demo">MUSTER-ANSICHT mit erfundenen Artikeln – so könnte der Katalog auf kikripp.de aussehen</div>
<header><div class="wrap">
  <h1>Artikelkatalog aus der Betriebsauflösung</h1>
  <p>Kinderkrippe Musterstadt GmbH · Abholung nach Terminvereinbarung · Preise netto zzgl. 19&nbsp;% USt</p>
</div></header>

<div class="filter"><div class="wrap">
  <div class="zeile">
    <input type="search" id="q" placeholder="Suchen: Bezeichnung, Nummer, Beschreibung …">
    <select id="fkat"><option value="">Alle Kategorien</option>__KAT__</select>
    <select id="fraum"><option value="">Alle Räume</option>__RAUM__</select>
    <label class="chk"><input type="checkbox" id="fnur" checked> nur verfügbare</label>
  </div>
  <div class="zaehler" id="zaehler"></div>
</div></div>

<div class="wrap"><div class="raster" id="raster"></div></div>

<div class="leiste"><div class="wrap inner">
  <div class="sum" id="merk">Noch nichts vorgemerkt – tragen Sie bei den gewünschten Artikeln eine Menge ein.</div>
  <button class="sek" onclick="leeren()">Leeren</button>
  <button onclick="anfrage()">Reservierung anfragen</button>
</div></div>

<dialog id="dlg"><div class="dlg">
  <h2>Verbindliche Reservierungsanfrage</h2>
  <p class="s">Wir bestätigen Ihnen die Reservierung per E-Mail und stimmen einen Abholtermin ab.
     Bezahlt wird bei Abholung bzw. per Rechnung.</p>
  <div class="pos" id="dlgpos"></div>
  <div class="feld"><label>Name / Firma</label><input placeholder="Musterfirma GmbH, Frau Muster"></div>
  <div class="feld"><label>E-Mail</label><input type="email" placeholder="einkauf@musterfirma.de"></div>
  <div class="feld"><label>Telefon</label><input placeholder="0123 456789"></div>
  <div class="feld"><label>Wunschtermin zur Abholung</label><input type="date"></div>
  <div class="feld"><label>Nachricht (optional)</label><textarea rows="2"
       placeholder="z. B. Rückfragen zu Maßen oder Zustand"></textarea></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:6px">
    <button class="sek" onclick="dlg.close()">Abbrechen</button>
    <button onclick="dlg.close();alert('Muster-Ansicht: hier würde die Anfrage abgeschickt und im Artikelstamm als Reservierung eingetragen.')">Anfrage senden</button>
  </div>
</div></dialog>

<script>
const ARTIKEL = __DATEN__, UST = __UST__;
const merk = {};
const eur = v => v.toLocaleString('de-DE',{style:'currency',currency:'EUR'});
const raster = document.getElementById('raster');

function render(){
  const q = document.getElementById('q').value.toLowerCase().trim();
  const k = document.getElementById('fkat').value, r = document.getElementById('fraum').value;
  const nur = document.getElementById('fnur').checked;
  const liste = ARTIKEL.filter(a =>
    (!q || (a.nr+' '+a.titel+' '+a.beschr).toLowerCase().includes(q)) &&
    (!k || a.kat === k) && (!r || a.raum === r) && (!nur || a.status === 'verfügbar'));
  document.getElementById('zaehler').textContent =
    liste.length + ' von ' + ARTIKEL.length + ' Artikeln';
  raster.innerHTML = liste.length ? liste.map(karte).join('')
    : '<div class="leer">Keine Artikel gefunden – bitte Filter anpassen.</div>';
}
function karte(a){
  const bc = a.status==='verfügbar'?'':(a.status==='reserviert'?'res':'verk');
  const bild = a.bild ? `<img src="${a.bild}" alt="">` : '';
  const kauf = a.status==='verfügbar' ? `<div class="mengen">
      <input type="number" min="0" max="${a.menge}" value="${merk[a.nr]||''}" placeholder="Menge"
             oninput="setzen('${a.nr}',this.value)">
      <button onclick="plus('${a.nr}')">vormerken</button></div>` : '';
  return `<div class="karte ${a.status!=='verfügbar'?'weg':''}">
    <div class="bild">${bild}<span class="nr">${a.nr}</span>
      <span class="badge ${bc}">${a.status}</span></div>
    <div class="txt"><h3>${a.titel}</h3><p class="b">${a.beschr}</p>
      <div class="meta"><span>${a.zustand}</span><span>${a.menge} ${a.einheit} verfügbar</span>
        <span>${a.raum}</span><span>${a.versand}</span></div>
      <div class="preis"><div><b>${eur(a.preis)}${a.basis==='VHB'?' VHB':''}</b>
        <small>netto je ${a.einheit} · ${eur(a.preis*(1+UST))} brutto</small></div></div>
      ${kauf}</div></div>`;
}
function setzen(nr,v){ const n=parseInt(v||0); if(n>0) merk[nr]=n; else delete merk[nr]; leiste(); }
function plus(nr){ merk[nr]=(merk[nr]||0)+1; render(); leiste(); }
function leeren(){ Object.keys(merk).forEach(k=>delete merk[k]); render(); leiste(); }
function leiste(){
  const keys=Object.keys(merk);
  const sum=keys.reduce((s,nr)=>s+merk[nr]*ARTIKEL.find(a=>a.nr===nr).preis,0);
  document.getElementById('merk').innerHTML = keys.length
    ? `${keys.length} Position(en) vorgemerkt · <b>${eur(sum)}</b> netto (${eur(sum*(1+UST))} brutto)`
    : 'Noch nichts vorgemerkt – tragen Sie bei den gewünschten Artikeln eine Menge ein.';
}
function anfrage(){
  const keys=Object.keys(merk);
  if(!keys.length){ alert('Bitte merken Sie zuerst Artikel vor.'); return; }
  const sum=keys.reduce((s,nr)=>s+merk[nr]*ARTIKEL.find(a=>a.nr===nr).preis,0);
  document.getElementById('dlgpos').innerHTML = keys.map(nr=>{
    const a=ARTIKEL.find(x=>x.nr===nr);
    return `<div><span>${merk[nr]} × ${a.nr} ${a.titel}</span><span>${eur(merk[nr]*a.preis)}</span></div>`;
  }).join('') + `<div style="border-top:1px solid #dfe3ea;margin-top:6px;padding-top:6px">
    <b>Summe netto</b><b>${eur(sum)}</b></div>`;
  document.getElementById('dlg').showModal();
}
['q','fkat','fraum','fnur'].forEach(id=>
  document.getElementById(id).addEventListener('input',render));
render(); leiste();
</script></body></html>"""

opt = lambda vs: "".join(f'<option>{html.escape(v)}</option>' for v in vs)
DOK = (DOK.replace("__KAT__", opt(kategorien)).replace("__RAUM__", opt(raeume))
          .replace("__DATEN__", json.dumps(daten, ensure_ascii=False))
          .replace("__UST__", str(USt_SATZ)))
pfad = os.path.join(BASIS, "ausgabe", "04_Webkatalog_MOCKUP.html")
with open(pfad, "w", encoding="utf-8") as f:
    f.write(DOK)
print("geschrieben:", pfad, os.path.getsize(pfad) // 1024, "KB")
