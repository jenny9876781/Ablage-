"""Erzeugt 04_Webkatalog_MOCKUP.html – passwortgeschützter Katalog im kikripp-Design."""
import sys, os, json, base64, html, io
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (lade_artikel, foto, AUSGABE, ASSETS, USt_SATZ, FIRMA, STRASSE, PLZ_ORT,
                 ANSPRECH, TELEFON, EMAIL, ROT, SCHWARZ, PAPIER, GRAU, LINIE, WEBFONT)
from PIL import Image

E = html.escape
SIGNET = open(os.path.join(ASSETS, "signet.svg"), encoding="utf-8").read()
SIGNET_B64 = base64.b64encode(SIGNET.encode()).decode()

def b64(p, breite=520):
    with Image.open(p) as im:
        im.thumbnail((breite, breite))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=72, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

daten = []
for a in lade_artikel():
    p = foto(a["Foto"])
    daten.append({
        "nr": a["ArtNr"], "titel": a["Bezeichnung"], "beschr": a["Beschreibung"],
        "kat": a["Kategorie"], "raum": a["Raum"], "zustand": a["Zustand"],
        "masse": a.get("Maße", ""), "menge": a["Menge"], "einheit": a["Einheit"],
        "preis": a["Preis_netto"], "basis": a["Preisbasis"], "versand": a["Versand"],
        "design": a["Wertklasse"] == "A",
        "status": "verfügbar" if a["Menge"] > 0 else "verkauft",
        "bild": b64(p) if p else "",
    })
kategorien = sorted({d["kat"] for d in daten})
raeume = []
for d in daten:
    if d["raum"] not in raeume:
        raeume.append(d["raum"])
opt = lambda vs: "".join(f'<option>{E(v)}</option>' for v in vs)

DOK = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Artikelkatalog – __FIRMA__</title>
<link rel="icon" href="data:image/svg+xml;base64,__SIGB64__">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=__WEBFONT__:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--rot:#__ROT__;--schwarz:#__SCHWARZ__;--papier:#__PAPIER__;--grau:#__GRAU__;--linie:#__LINIE__;
      --font:'__WEBFONT__',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font);font-size:15px;line-height:1.5;color:var(--schwarz);background:#fff}
/* ---------- Login ---------- */
#login{position:fixed;inset:0;background:var(--schwarz);display:flex;align-items:center;
       justify-content:center;z-index:60;padding:24px}
#login .box{width:100%;max-width:340px;text-align:center}
#login svg{width:92px;height:auto;margin-bottom:6px}
#login .wort{font-weight:800;letter-spacing:.12em;font-size:30px;color:#fff;margin-bottom:26px}
#login h2{font-size:15px;font-weight:600;color:#fff;margin:0 0 6px}
#login p{font-size:13.5px;color:#9aa0a6;margin:0 0 20px}
#login input{width:100%;padding:12px 14px;border:1px solid #3a3a3a;background:#242424;color:#fff;
             border-radius:3px;font:inherit;font-size:15px;text-align:center}
#login input::placeholder{color:#7a7a7a}
#login button{width:100%;margin-top:10px}
#login .fuss{font-size:12px;color:#6b6b6b;margin-top:18px}
button{background:var(--rot);color:#fff;border:0;border-radius:3px;padding:11px 20px;
       font:inherit;font-weight:600;font-size:14.5px;cursor:pointer;letter-spacing:.01em}
button:hover{background:#a50d26}
button.sek{background:transparent;color:#fff;border:1px solid #4a4a4a}
button.sek:hover{background:#2a2a2a}
/* ---------- Kopf ---------- */
.wrap{max-width:1200px;margin:0 auto;padding:0 20px}
header{background:#fff;border-bottom:3px solid var(--rot);padding:18px 0 16px}
.marke{display:flex;align-items:center;gap:11px}
.marke svg{width:46px;height:auto}
.marke .wort{font-weight:800;letter-spacing:.11em;font-size:22px;color:var(--schwarz)}
header h1{font-size:16px;font-weight:600;margin:14px 0 2px}
header p{margin:0;color:var(--grau);font-size:13.5px}
.demo{background:var(--schwarz);color:#fff;font-size:12.5px;padding:7px 0;text-align:center;letter-spacing:.02em}
/* ---------- Filter ---------- */
.filter{background:#fff;border-bottom:1px solid var(--linie);padding:13px 0 11px;position:sticky;
        top:env(safe-area-inset-top,0px);z-index:20}
.zeile{display:flex;gap:8px;flex-wrap:wrap}
input[type=search],select{padding:9px 11px;border:1px solid var(--linie);border-radius:3px;
                          font:inherit;font-size:14px;background:#fff;color:var(--schwarz)}
input[type=search]{flex:2 1 230px} select{flex:1 1 150px}
input:focus,select:focus{outline:none;border-color:var(--rot)}
.chk{display:flex;align-items:center;gap:7px;font-size:14px;color:var(--grau);white-space:nowrap}
.chk input{width:auto;accent-color:var(--rot)}
.zaehler{font-size:13px;color:var(--grau);padding-top:9px}
.zaehler b{color:var(--schwarz)}
/* ---------- Karten ---------- */
.raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:16px;
        padding:20px 0 130px}
.karte{background:#fff;border:1px solid var(--linie);border-radius:3px;overflow:hidden;
       display:flex;flex-direction:column;transition:border-color .15s}
.karte:hover{border-color:#b9bcc2}
.karte.weg{opacity:.45}
.bild{position:relative;height:186px;background:var(--papier);overflow:hidden}
.bild img{width:100%;height:186px;object-fit:cover;display:block}
.nr{position:absolute;left:0;top:0;background:var(--schwarz);color:#fff;font-size:11px;
    font-weight:600;padding:3px 8px;letter-spacing:.04em}
.badge{position:absolute;top:8px;right:8px;font-size:10.5px;font-weight:700;padding:3px 9px;
       border-radius:2px;letter-spacing:.03em;text-transform:uppercase}
.badge.frei{background:rgba(255,255,255,.92);color:var(--schwarz);border:1px solid var(--linie)}
.badge.res{background:var(--rot);color:#fff}
.badge.verk{background:#c9c9c9;color:#4b5563}
.dsgn{position:absolute;left:0;bottom:0;background:var(--rot);color:#fff;font-size:10px;
      font-weight:700;padding:3px 8px;letter-spacing:.04em;text-transform:uppercase}
.txt{padding:12px 14px 14px;display:flex;flex-direction:column;flex:1}
.txt h3{margin:0 0 4px;font-size:15px;font-weight:600;line-height:1.3}
.txt .b{font-size:13px;color:var(--grau);margin:0 0 10px;line-height:1.4}
.meta{font-size:12px;color:var(--grau);display:flex;gap:6px;flex-wrap:wrap;margin-bottom:11px}
.meta span{background:var(--papier);padding:3px 8px;border-radius:2px}
.preis{margin-top:auto;border-top:1px solid var(--linie);padding-top:10px;
       display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.preis b{font-size:19px;font-weight:700}
.vhb{font-size:11px;font-weight:700;color:var(--rot);border:1px solid var(--rot);
     padding:1px 5px;border-radius:2px}
.preis small{display:block;width:100%;color:var(--grau);font-size:11.5px;margin-top:1px}
.mengen{display:flex;gap:7px;align-items:center;margin-top:11px}
.mengen input{width:86px;text-align:center;padding:9px 6px;border:1px solid var(--linie);
              border-radius:3px;font:inherit}
.mengen button{flex:1}
/* ---------- Merkzettel ---------- */
.leiste{position:fixed;left:0;right:0;bottom:0;background:var(--schwarz);color:#fff;
        padding:14px 0 calc(14px + env(safe-area-inset-bottom,0px));z-index:30}
.leiste .inner{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.leiste .sum{flex:1;font-size:14px;color:#c9ccd1}
.leiste .sum b{font-size:18px;color:#fff;font-weight:700}
dialog{border:0;border-radius:4px;padding:0;max-width:540px;width:calc(100% - 32px)}
dialog::backdrop{background:rgba(0,0,0,.6)}
.dlg{padding:24px}
.dlg h2{margin:0 0 4px;font-size:19px;font-weight:700}
.dlg p.s{margin:0 0 18px;color:var(--grau);font-size:13.5px}
.feld{margin-bottom:12px}
.feld label{display:block;font-size:12.5px;font-weight:600;margin-bottom:5px}
.feld input,.feld textarea{width:100%;padding:10px 12px;border:1px solid var(--linie);
                           border-radius:3px;font:inherit;font-size:14px}
.pos{background:var(--papier);border-left:3px solid var(--rot);padding:12px 14px;
     font-size:13.5px;margin-bottom:16px}
.pos div{display:flex;justify-content:space-between;padding:2px 0;gap:12px}
.leer{grid-column:1/-1;text-align:center;color:var(--grau);padding:60px 0}
.leer svg{width:64px;opacity:.22;margin-bottom:10px}
footer{background:var(--papier);border-top:1px solid var(--linie);padding:22px 0;
       font-size:12.5px;color:var(--grau);margin-bottom:96px}
@media(max-width:560px){.leiste .sum{flex:1 1 100%}}
</style></head><body>

<div id="login"><div class="box">
  __SIGNET__
  <div class="wort">KIKRIPP</div>
  <h2>Artikelkatalog Betriebsauflösung</h2>
  <p>Dieser Bereich ist geschützt. Bitte geben Sie das Passwort ein, das Sie von uns erhalten haben.</p>
  <form onsubmit="event.preventDefault();document.getElementById('login').remove()">
    <input type="password" placeholder="Passwort" autofocus>
    <button>Katalog öffnen</button>
  </form>
  <p class="fuss">Muster-Ansicht – ein beliebiges Passwort öffnet den Katalog.</p>
</div></div>

<div class="demo">MUSTER-ANSICHT · so könnte der Katalog auf kikripp.de aussehen</div>
<header><div class="wrap">
  <div class="marke">__SIGNET__<span class="wort">KIKRIPP</span></div>
  <h1>Artikelkatalog aus der Betriebsauflösung</h1>
  <p>Abholung nach Terminvereinbarung · Preise netto zzgl. __USTP__&nbsp;% USt · rot markiert = Marken- und Designstücke</p>
</div></header>

<div class="filter"><div class="wrap">
  <div class="zeile">
    <input type="search" id="q" placeholder="Suchen: Bezeichnung, Nummer, Beschreibung …">
    <select id="fkat"><option value="">Alle Kategorien</option>__KAT__</select>
    <select id="fraum"><option value="">Alle Räume</option>__RAUM__</select>
    <label class="chk"><input type="checkbox" id="fdesign"> nur Designstücke</label>
    <label class="chk"><input type="checkbox" id="fnur" checked> nur verfügbare</label>
  </div>
  <div class="zaehler" id="zaehler"></div>
</div></div>

<div class="wrap"><div class="raster" id="raster"></div></div>

<footer><div class="wrap">__FIRMA__ · __STRASSE__ · __PLZORT__ · __ANSPRECH__ · __TELEFON__ · __EMAIL__</div></footer>

<div class="leiste"><div class="wrap inner">
  <div class="sum" id="merk"></div>
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
  <div class="feld"><label>Telefon</label><input placeholder="07721 123456"></div>
  <div class="feld"><label>Wunschtermin zur Abholung</label><input type="date"></div>
  <div class="feld"><label>Nachricht (optional)</label><textarea rows="2"
       placeholder="z. B. Rückfragen zu Maßen oder Zustand"></textarea></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
    <button class="sek" style="color:#1a1a1a;border-color:#dcdcdc" onclick="dlg.close()">Abbrechen</button>
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
  const nurD = document.getElementById('fdesign').checked;
  const liste = ARTIKEL.filter(a =>
    (!q || (a.nr+' '+a.titel+' '+a.beschr).toLowerCase().includes(q)) &&
    (!k || a.kat === k) && (!r || a.raum === r) &&
    (!nur || a.status === 'verfügbar') && (!nurD || a.design));
  const wert = liste.reduce((s,a)=>s+a.preis*a.menge,0);
  document.getElementById('zaehler').innerHTML =
    `<b>${liste.length}</b> von ${ARTIKEL.length} Positionen · Listenwert ${eur(wert)} netto`;
  raster.innerHTML = liste.length ? liste.map(karte).join('')
    : `<div class="leer">__SIGNET__<div>Keine Artikel gefunden – bitte Filter anpassen.</div></div>`;
}
function karte(a){
  const bc = a.status==='verfügbar'?'frei':(a.status==='reserviert'?'res':'verk');
  const bild = a.bild ? `<img src="${a.bild}" alt="">` : '';
  const dsgn = a.design ? '<span class="dsgn">Designstück</span>' : '';
  const masse = a.masse ? `<span>${a.masse}</span>` : '';
  const kauf = a.status==='verfügbar' ? `<div class="mengen">
      <input type="number" min="0" max="${a.menge}" value="${merk[a.nr]||''}" placeholder="Menge"
             oninput="setzen('${a.nr}',this.value)">
      <button onclick="plus('${a.nr}')">vormerken</button></div>` : '';
  return `<div class="karte ${a.status!=='verfügbar'?'weg':''}">
    <div class="bild">${bild}<span class="nr">${a.nr}</span>
      <span class="badge ${bc}">${a.status}</span>${dsgn}</div>
    <div class="txt"><h3>${a.titel}</h3><p class="b">${a.beschr}</p>
      <div class="meta"><span>${a.zustand}</span><span>${a.menge} ${a.einheit}</span>
        ${masse}<span>${a.raum}</span><span>${a.versand}</span></div>
      <div class="preis"><b>${eur(a.preis)}</b>${a.basis==='VHB'?'<span class="vhb">VHB</span>':''}
        <small>netto je ${a.einheit} · ${eur(a.preis*(1+UST))} brutto</small></div>
      ${kauf}</div></div>`;
}
function setzen(nr,v){ const n=parseInt(v||0); if(n>0) merk[nr]=n; else delete merk[nr]; leiste(); }
function plus(nr){ merk[nr]=(merk[nr]||0)+1; render(); leiste(); }
function leeren(){ Object.keys(merk).forEach(k=>delete merk[k]); render(); leiste(); }
function leiste(){
  const keys=Object.keys(merk);
  const sum=keys.reduce((s,nr)=>s+merk[nr]*ARTIKEL.find(a=>a.nr===nr).preis,0);
  document.getElementById('merk').innerHTML = keys.length
    ? `${keys.length} Position(en) vorgemerkt · <b>${eur(sum)}</b> netto &nbsp;(${eur(sum*(1+UST))} brutto)`
    : 'Noch nichts vorgemerkt – tragen Sie bei den gewünschten Artikeln eine Menge ein.';
}
function anfrage(){
  const keys=Object.keys(merk);
  if(!keys.length){ alert('Bitte merken Sie zuerst Artikel vor.'); return; }
  const sum=keys.reduce((s,nr)=>s+merk[nr]*ARTIKEL.find(a=>a.nr===nr).preis,0);
  document.getElementById('dlgpos').innerHTML = keys.map(nr=>{
    const a=ARTIKEL.find(x=>x.nr===nr);
    return `<div><span>${merk[nr]} × ${a.nr} ${a.titel}</span><span>${eur(merk[nr]*a.preis)}</span></div>`;
  }).join('') + `<div style="border-top:1px solid #dcdcdc;margin-top:8px;padding-top:8px">
    <b>Summe netto</b><b>${eur(sum)}</b></div>`;
  document.getElementById('dlg').showModal();
}
['q','fkat','fraum','fnur','fdesign'].forEach(id=>
  document.getElementById(id).addEventListener('input',render));
render(); leiste();
</script></body></html>"""

ersetzungen = {
    "__SIGNET__": SIGNET, "__SIGB64__": SIGNET_B64, "__KAT__": opt(kategorien),
    "__RAUM__": opt(raeume), "__DATEN__": json.dumps(daten, ensure_ascii=False),
    "__UST__": str(USt_SATZ), "__USTP__": str(int(USt_SATZ * 100)),
    "__ROT__": ROT, "__SCHWARZ__": SCHWARZ, "__PAPIER__": PAPIER, "__GRAU__": GRAU,
    "__LINIE__": LINIE, "__WEBFONT__": WEBFONT, "__FIRMA__": E(FIRMA), "__STRASSE__": E(STRASSE),
    "__PLZORT__": E(PLZ_ORT), "__ANSPRECH__": E(ANSPRECH), "__TELEFON__": TELEFON, "__EMAIL__": EMAIL,
}
for k, v in ersetzungen.items():
    DOK = DOK.replace(k, v)

pfad = os.path.join(AUSGABE, "04_Webkatalog_MOCKUP.html")
with open(pfad, "w", encoding="utf-8") as f:
    f.write(DOK)
print("geschrieben:", pfad, os.path.getsize(pfad) // 1024, "KB")
