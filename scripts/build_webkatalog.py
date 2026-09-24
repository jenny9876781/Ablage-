"""Erzeugt den Webkatalog – offline als Datei und/oder als geschützte Fassung zum Veröffentlichen.

    python3 scripts/build_webkatalog.py                      # nur die offene Datei
    python3 scripts/build_webkatalog.py --geschuetzt PASSWORT # zusätzlich die verschlüsselte

Bei der geschützten Fassung sind die Artikeldaten samt Bildern mit AES-256-GCM verschlüsselt;
der Schlüssel wird im Browser aus dem Passwort abgeleitet (PBKDF2-SHA256, 210.000 Runden).
Ohne das richtige Passwort stehen die Daten nicht in der Seite – anders als bei einer bloßen
Abfrage, die man im Quelltext umgehen könnte.
"""
import sys, os, json, base64, html, io, hashlib, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import (lade_artikel, foto, AUSGABE, ASSETS, USt_SATZ, FIRMA, STRASSE, PLZ_ORT,
                 ANSPRECH, TELEFON, EMAIL, ROT, SCHWARZ, PAPIER, GRAU, LINIE, WEBFONT)
from PIL import Image

E = html.escape
SIGNET = open(os.path.join(ASSETS, "signet.svg"), encoding="utf-8").read()
SIGNET_B64 = base64.b64encode(SIGNET.encode()).decode()


def b64bild(p, breite=520):
    with Image.open(p) as im:
        im.thumbnail((breite, breite))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=72, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def daten_sammeln():
    daten = []
    for a in lade_artikel():
        # Was nicht in den Webkatalog gehört, gehört auch nicht in das Muster.
        if (a.get("Im_Katalog") or "ja").strip().lower() != "ja":
            continue
        p = foto(a["Foto"])
        daten.append({
            "nr": a["ArtNr"], "titel": a["Bezeichnung"], "beschr": a["Beschreibung"],
            "kat": a["Kategorie"], "raum": a["Raum"], "zustand": a["Zustand"],
            "masse": a.get("Maße", ""), "menge": a["Menge"], "einheit": a["Einheit"],
            "preis": a["Preis_netto"], "basis": a["Preisbasis"], "versand": a["Versand"],
            "marke": a.get("Marke", ""),
            "buendel": a.get("Bündel", ""),
            "hinweis": a.get("Mengenhinweis", ""),
            "status": "verfügbar" if a["Menge"] > 0 else "verkauft",
            "bild": b64bild(p) if p else "",
        })
    return daten


STIL = """
:root{--rot:#%(ROT)s;--schwarz:#%(SCHWARZ)s;--papier:#%(PAPIER)s;--grau:#%(GRAU)s;
      --linie:#%(LINIE)s;--grund:#ffffff;
      --font:'%(WEBFONT)s',-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font);font-size:15px;line-height:1.5;
     color:var(--schwarz);background:var(--grund)}
[hidden]{display:none!important}
button{background:var(--rot);color:#fff;border:0;border-radius:3px;padding:11px 20px;
       font:inherit;font-weight:600;font-size:14.5px;cursor:pointer}
button:hover{background:#a50d26}
button:focus-visible,input:focus-visible,select:focus-visible{outline:2px solid var(--rot);outline-offset:2px}
button.sek{background:transparent;color:#fff;border:1px solid #4a4a4a}
button.sek:hover{background:#2a2a2a}
/* Sperre */
#sperre{position:fixed;inset:0;background:var(--schwarz);display:flex;align-items:center;
        justify-content:center;z-index:60;padding:24px}
#sperre .box{width:100%%;max-width:340px;text-align:center}
#sperre svg{width:92px;height:auto;margin-bottom:6px}
#sperre .wort{font-weight:800;letter-spacing:.12em;font-size:30px;color:#fff;margin-bottom:26px}
#sperre h2{font-size:15px;font-weight:600;color:#fff;margin:0 0 6px}
#sperre p{font-size:13.5px;color:#9aa0a6;margin:0 0 20px}
#sperre input{width:100%%;padding:12px 14px;border:1px solid #3a3a3a;background:#242424;
              color:#fff;border-radius:3px;font:inherit;font-size:15px;text-align:center}
#sperre input::placeholder{color:#7a7a7a}
#sperre button{width:100%%;margin-top:10px}
#sperre .fehler{color:#ff8a95;font-size:13.5px;margin:12px 0 0;min-height:19px}
/* Kopf */
.wrap{max-width:1200px;margin:0 auto;padding:0 20px}
header{background:var(--grund);border-bottom:3px solid var(--rot);padding:18px 0 16px}
.marke{display:flex;align-items:center;gap:11px}
.marke svg{width:46px;height:auto}
.marke .wort{font-weight:800;letter-spacing:.11em;font-size:22px;color:var(--schwarz)}
header h1{font-size:16px;font-weight:600;margin:14px 0 2px;text-wrap:balance}
header p{margin:0;color:var(--grau);font-size:13.5px}
.demo{background:var(--schwarz);color:#fff;font-size:12.5px;padding:7px 0;text-align:center}
/* Filter */
.filter{background:var(--grund);border-bottom:1px solid var(--linie);padding:13px 0 11px;
        position:sticky;top:env(safe-area-inset-top,0px);z-index:20}
.zeile{display:flex;gap:8px;flex-wrap:wrap}
input[type=search],select{padding:9px 11px;border:1px solid var(--linie);border-radius:3px;
                          font:inherit;font-size:14px;background:var(--grund);color:var(--schwarz)}
input[type=search]{flex:2 1 230px} select{flex:1 1 150px}
input:focus,select:focus{outline:none;border-color:var(--rot)}
.chk{display:flex;align-items:center;gap:7px;font-size:14px;color:var(--grau);white-space:nowrap}
.chk input{width:auto;accent-color:var(--rot)}
.zaehler{font-size:13px;color:var(--grau);padding-top:9px;font-variant-numeric:tabular-nums}
.zaehler b{color:var(--schwarz)}
/* Karten */
.raster{display:grid;grid-template-columns:repeat(auto-fill,minmax(248px,1fr));gap:16px;
        padding:20px 0 130px}
.karte{background:var(--grund);border:1px solid var(--linie);border-radius:3px;overflow:hidden;
       display:flex;flex-direction:column}
.karte.weg{opacity:.45}
.bild{position:relative;height:186px;background:var(--papier);overflow:hidden}
.bild img{width:100%%;max-width:100%%;height:186px;object-fit:cover;display:block}
.nr{position:absolute;left:0;top:0;background:var(--schwarz);color:#fff;font-size:11px;
    font-weight:600;padding:3px 8px;letter-spacing:.04em}
.badge{position:absolute;top:8px;right:8px;font-size:10.5px;font-weight:700;padding:3px 9px;
       border-radius:2px;letter-spacing:.03em;text-transform:uppercase}
.badge.frei{background:rgba(255,255,255,.92);color:var(--schwarz);border:1px solid var(--linie)}
.badge.res{background:var(--rot);color:#fff}
.badge.verk{background:#c9c9c9;color:#4b5563}
.meta span.bnd{background:var(--rot);color:#fff;font-weight:700}
.markenschild{position:absolute;left:0;bottom:0;background:var(--rot);color:#fff;font-size:10px;
      font-weight:700;padding:3px 8px;letter-spacing:.04em;text-transform:uppercase}
.txt{padding:12px 14px 14px;display:flex;flex-direction:column;flex:1}
.txt h3{margin:0 0 4px;font-size:15px;font-weight:600;line-height:1.3;text-wrap:balance}
.txt .b{font-size:13px;color:var(--grau);margin:0 0 10px;line-height:1.4}
.txt .hw{font-size:12.5px;color:var(--schwarz);margin:0 0 10px;line-height:1.45;
         border-left:2px solid var(--linie);padding-left:9px}
.meta{font-size:12px;color:var(--grau);display:flex;gap:6px;flex-wrap:wrap;margin-bottom:11px}
.meta span{background:var(--papier);padding:3px 8px;border-radius:2px}
.preis{margin-top:auto;border-top:1px solid var(--linie);padding-top:10px;
       display:flex;align-items:baseline;gap:7px;flex-wrap:wrap}
.preis b{font-size:19px;font-weight:700;font-variant-numeric:tabular-nums}
.vhb{font-size:11px;font-weight:700;color:var(--rot);border:1px solid var(--rot);
     padding:1px 5px;border-radius:2px}
.preis small{display:block;width:100%%;color:var(--grau);font-size:11.5px;margin-top:1px}
.mengen{display:flex;gap:7px;align-items:center;margin-top:11px}
.mengen input{width:86px;text-align:center;padding:9px 6px;border:1px solid var(--linie);
              border-radius:3px;font:inherit}
.mengen button{flex:1}
/* Merkzettel */
.leiste{position:fixed;left:0;right:0;bottom:0;background:var(--schwarz);color:#fff;
        padding:14px 0 calc(14px + env(safe-area-inset-bottom,0px));z-index:30}
.leiste .inner{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.leiste .sum{flex:1;font-size:14px;color:#c9ccd1}
.leiste .sum b{font-size:18px;color:#fff;font-weight:700}
dialog{border:0;border-radius:4px;padding:0;max-width:540px;width:calc(100%% - 32px);
       color:var(--schwarz);background:var(--grund)}
dialog::backdrop{background:rgba(0,0,0,.6)}
.dlg{padding:24px}
.dlg h2{margin:0 0 4px;font-size:19px;font-weight:700}
.dlg p.s{margin:0 0 18px;color:var(--grau);font-size:13.5px}
.feld{margin-bottom:12px}
.feld label{display:block;font-size:12.5px;font-weight:600;margin-bottom:5px}
.feld input,.feld textarea{width:100%%;padding:10px 12px;border:1px solid var(--linie);
                           border-radius:3px;font:inherit;font-size:14px}
.pos{background:var(--papier);border-left:3px solid var(--rot);padding:12px 14px;
     font-size:13.5px;margin-bottom:16px}
.pos div{display:flex;justify-content:space-between;padding:2px 0;gap:12px}
.leer{grid-column:1/-1;text-align:center;color:var(--grau);padding:60px 0}
.leer svg{width:64px;opacity:.22;margin-bottom:10px}
footer{background:var(--papier);border-top:1px solid var(--linie);padding:22px 0;
       font-size:12.5px;color:var(--grau);margin-bottom:96px}
@media(max-width:560px){.leiste .sum{flex:1 1 100%%}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
""" % dict(ROT=ROT, SCHWARZ=SCHWARZ, PAPIER=PAPIER, GRAU=GRAU, LINIE=LINIE, WEBFONT=WEBFONT)


RUMPF = """
<div class="demo">MUSTER-ANSICHT · so könnte der Katalog auf kikripp.de aussehen</div>
<header><div class="wrap">
  <div class="marke">__SIGNET__<span class="wort">KIKRIPP</span></div>
  <h1>Artikelkatalog aus der Betriebsauflösung</h1>
  <p>Abholung nach Terminvereinbarung · Preise netto zzgl. __USTP__&nbsp;% USt · rot markiert = Markenware, die Marke steht am Bild</p>
</div></header>

<div class="filter"><div class="wrap">
  <div class="zeile">
    <input type="search" id="q" placeholder="Suchen: Bezeichnung, Nummer, Beschreibung …">
    <select id="fkat"><option value="">Alle Kategorien</option></select>
    <select id="fraum"><option value="">Alle Räume</option></select>
    <label class="chk"><input type="checkbox" id="fdesign"> nur Markenware</label>
    <label class="chk"><input type="checkbox" id="fnur" checked> nur verfügbare</label>
  </div>
  <div class="zaehler" id="zaehler"></div>
</div></div>

<div class="wrap"><div class="raster" id="raster"></div></div>

<footer><div class="wrap">__FIRMA__ · __STRASSE__ · __PLZORT__ · __ANSPRECH__ · __TELEFON__ · __EMAIL__</div></footer>

<div class="leiste"><div class="wrap inner">
  <div class="sum" id="merk"></div>
  <button class="sek" id="btn-leeren">Leeren</button>
  <button id="btn-anfrage">Reservierung anfragen</button>
</div></div>

<dialog id="dlg"><div class="dlg">
  <h2>Verbindliche Reservierungsanfrage</h2>
  <p class="s">Wir bestätigen Ihnen die Reservierung per E-Mail und stimmen einen Abholtermin ab.
     Bezahlt wird bei Abholung bzw. per Rechnung.</p>
  <div class="pos" id="dlgpos"></div>
  <div class="feld"><label for="f-name">Name / Firma</label><input id="f-name" placeholder="Musterfirma GmbH, Frau Muster"></div>
  <div class="feld"><label for="f-mail">E-Mail</label><input id="f-mail" type="email" placeholder="einkauf@musterfirma.de"></div>
  <div class="feld"><label for="f-tel">Telefon</label><input id="f-tel" placeholder="07721 123456"></div>
  <div class="feld"><label for="f-datum">Wunschtermin zur Abholung</label><input id="f-datum" type="date"></div>
  <div class="feld"><label for="f-text">Nachricht (optional)</label><textarea id="f-text" rows="2"
       placeholder="z. B. Rückfragen zu Maßen oder Zustand"></textarea></div>
  <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
    <button class="sek" style="color:var(--schwarz);border-color:var(--linie)" id="btn-ab">Abbrechen</button>
    <button id="btn-senden">Anfrage senden</button>
  </div>
</div></dialog>
"""

SKRIPT = """
let ARTIKEL = [];
const UST = __UST__, merk = {};
const eur = v => v.toLocaleString('de-DE',{style:'currency',currency:'EUR'});
// Zeilenumbrueche aus der Arbeitsmappe als Umbruch anzeigen (wie im Plugin).
const br = s => String(s??'').replace(/[&<>"]/g,z=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[z])).replace(/\r?\n/g,'<br>');
const $ = id => document.getElementById(id);

function fuelleFilter(){
  const kats = [...new Set(ARTIKEL.map(a=>a.kat))].sort();
  const raeume = []; ARTIKEL.forEach(a=>{ if(!raeume.includes(a.raum)) raeume.push(a.raum); });
  $('fkat').innerHTML = '<option value="">Alle Kategorien</option>' + kats.map(k=>`<option>${k}</option>`).join('');
  $('fraum').innerHTML = '<option value="">Alle Räume</option>' + raeume.map(r=>`<option>${r}</option>`).join('');
}
function render(){
  const q = $('q').value.toLowerCase().trim();
  const k = $('fkat').value, r = $('fraum').value;
  const nur = $('fnur').checked, nurD = $('fdesign').checked;
  const liste = ARTIKEL.filter(a =>
    (!q || (a.nr+' '+a.titel+' '+a.beschr+' '+a.buendel+' '+a.hinweis).toLowerCase().includes(q)) &&
    (!k || a.kat === k) && (!r || a.raum === r) &&
    (!nur || a.status === 'verfügbar') && (!nurD || !!a.marke));
  const wert = liste.reduce((s,a)=>s+a.preis*a.menge,0);
  $('zaehler').innerHTML = `<b>${liste.length}</b> von ${ARTIKEL.length} Positionen · Listenwert ${eur(wert)} netto`;
  $('raster').innerHTML = liste.length ? liste.map(karte).join('')
    : `<div class="leer">__SIGNET__<div>Keine Artikel gefunden – bitte Filter anpassen.</div></div>`;
}
function karte(a){
  const bc = a.status==='verfügbar'?'frei':(a.status==='reserviert'?'res':'verk');
  const bild = a.bild ? `<img src="${a.bild}" alt="${a.titel}">` : '';
  const mk = a.marke ? `<span class="markenschild">${a.marke}</span>` : '';
  const masse = a.masse ? `<span>${a.masse}</span>` : '';
  const bnd = a.buendel ? `<span class="bnd">Sammlung ${a.buendel}</span>` : '';
  const kauf = a.status==='verfügbar' ? `<div class="mengen">
      <input type="number" min="0" max="${a.menge}" value="${merk[a.nr]||''}" placeholder="Menge"
             id="m-${a.nr}" aria-label="Wunschmenge ${a.nr}" data-nr="${a.nr}">
      <button data-plus="${a.nr}">vormerken</button></div>` : '';
  return `<div class="karte ${a.status!=='verfügbar'?'weg':''}">
    <div class="bild">${bild}<span class="nr">${a.nr}</span>
      <span class="badge ${bc}">${a.status}</span>${mk}</div>
    <div class="txt"><h3>${a.titel}</h3><p class="b">${br(a.beschr)}</p>
      ${a.hinweis ? `<p class="hw">${br(a.hinweis)}</p>` : ''}
      <div class="meta"><span>${a.zustand}</span><span>${a.menge} ${a.einheit}</span>
        ${masse}<span>${a.raum}</span><span>${a.versand}</span>${bnd}</div>
      <div class="preis"><b>${eur(a.preis)}</b>${a.basis==='VHB'?'<span class="vhb">VHB</span>':''}
        <small>netto je ${a.einheit} · ${eur(a.preis*(1+UST))} brutto</small></div>
      ${kauf}</div></div>`;
}
function leiste(){
  const keys=Object.keys(merk);
  const sum=keys.reduce((s,nr)=>s+merk[nr]*ARTIKEL.find(a=>a.nr===nr).preis,0);
  $('merk').innerHTML = keys.length
    ? `${keys.length} Position(en) vorgemerkt · <b>${eur(sum)}</b> netto &nbsp;(${eur(sum*(1+UST))} brutto)`
    : 'Noch nichts vorgemerkt – tragen Sie bei den gewünschten Artikeln eine Menge ein.';
}
document.addEventListener('input', e => {
  if(e.target.dataset && e.target.dataset.nr){
    const n = parseInt(e.target.value||0);
    if(n>0) merk[e.target.dataset.nr]=n; else delete merk[e.target.dataset.nr];
    leiste();
  }
});
document.addEventListener('click', e => {
  const nr = e.target.dataset && e.target.dataset.plus;
  if(nr){ merk[nr]=(merk[nr]||0)+1; render(); leiste(); }
});
function start(){
  fuelleFilter();
  ['q','fkat','fraum','fnur','fdesign'].forEach(id=>$(id).addEventListener('input',render));
  $('btn-leeren').addEventListener('click',()=>{ Object.keys(merk).forEach(k=>delete merk[k]); render(); leiste(); });
  $('btn-ab').addEventListener('click',()=>$('dlg').close());
  $('btn-senden').addEventListener('click',()=>{ $('dlg').close();
    alert('Muster-Ansicht: hier würde die Anfrage abgeschickt und im Artikelstamm als Reservierung eingetragen.'); });
  $('btn-anfrage').addEventListener('click',()=>{
    const keys=Object.keys(merk);
    if(!keys.length){ alert('Bitte merken Sie zuerst Artikel vor.'); return; }
    const sum=keys.reduce((s,nr)=>s+merk[nr]*ARTIKEL.find(a=>a.nr===nr).preis,0);
    $('dlgpos').innerHTML = keys.map(nr=>{
      const a=ARTIKEL.find(x=>x.nr===nr);
      return `<div><span>${merk[nr]} × ${a.nr} ${a.titel}</span><span>${eur(merk[nr]*a.preis)}</span></div>`;
    }).join('') + `<div style="border-top:1px solid var(--linie);margin-top:8px;padding-top:8px">
      <b>Summe netto</b><b>${eur(sum)}</b></div>`;
    $('dlg').showModal();
  });
  render(); leiste();
}
"""


def ersetze(text, daten_json=""):
    for k, v in {"__SIGNET__": SIGNET, "__UST__": str(USt_SATZ), "__USTP__": str(int(USt_SATZ * 100)),
                 "__FIRMA__": E(FIRMA), "__STRASSE__": E(STRASSE), "__PLZORT__": E(PLZ_ORT),
                 "__ANSPRECH__": E(ANSPRECH), "__TELEFON__": TELEFON, "__EMAIL__": EMAIL,
                 "__DATEN__": daten_json}.items():
        text = text.replace(k, v)
    return text


KOPF_LINKS = f"""<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family={WEBFONT}:wght@400;500;600;700;800&display=swap" rel="stylesheet">"""


def offene_datei(daten):
    dok = f"""<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Artikelkatalog – {E(FIRMA)}</title>
<link rel="icon" href="data:image/svg+xml;base64,{SIGNET_B64}">
{KOPF_LINKS}
<style>{STIL}</style></head><body>
{ersetze(RUMPF)}
<script>{ersetze(SKRIPT)}
ARTIKEL = __DATEN__;
start();
</script></body></html>""".replace("__DATEN__", json.dumps(daten, ensure_ascii=False))
    pfad = os.path.join(AUSGABE, "04_Webkatalog_MOCKUP.html")
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(dok)
    return pfad


def geschuetzte_datei(daten, passwort):
    from Crypto.Cipher import AES
    klartext = json.dumps(daten, ensure_ascii=False).encode("utf-8")
    salz, iv = os.urandom(16), os.urandom(12)
    schluessel = hashlib.pbkdf2_hmac("sha256", passwort.encode("utf-8"), salz, 210000, 32)
    ct, tag = AES.new(schluessel, AES.MODE_GCM, nonce=iv).encrypt_and_digest(klartext)
    nutzlast = base64.b64encode(ct + tag).decode()

    dok = f"""<title>Kikripp Artikelkatalog</title>
{KOPF_LINKS}
<style>{STIL}</style>

<div id="sperre"><div class="box">
  {SIGNET}
  <div class="wort">KIKRIPP</div>
  <h2>Artikelkatalog Betriebsauflösung</h2>
  <p>Dieser Katalog ist verschlüsselt. Bitte geben Sie das Passwort ein, das Sie von uns erhalten haben.</p>
  <form id="sperrform">
    <input type="password" id="pw" placeholder="Passwort" autocomplete="current-password" autofocus>
    <button type="submit" id="btn-auf">Katalog öffnen</button>
  </form>
  <p class="fehler" id="fehler" role="alert"></p>
</div></div>

<div id="inhalt" hidden>
{ersetze(RUMPF)}
</div>

<script>
const SALZ = "{base64.b64encode(salz).decode()}";
const IV   = "{base64.b64encode(iv).decode()}";
const DATEN = "{nutzlast}";
{ersetze(SKRIPT)}

function roh(s) {{                     // kein fetch('data:...') - das faellt unter connect-src
  const bin = atob(s);
  const u = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
  return u;
}}

async function oeffnen(pw){{
  const km = await crypto.subtle.importKey('raw', new TextEncoder().encode(pw),
                                           'PBKDF2', false, ['deriveKey']);
  const key = await crypto.subtle.deriveKey(
    {{name:'PBKDF2', salt: roh(SALZ), iterations: 210000, hash:'SHA-256'}},
    km, {{name:'AES-GCM', length:256}}, false, ['decrypt']);
  const klar = await crypto.subtle.decrypt({{name:'AES-GCM', iv: roh(IV)}}, key, roh(DATEN));
  return JSON.parse(new TextDecoder().decode(klar));
}}

document.getElementById('sperrform').addEventListener('submit', async e => {{
  e.preventDefault();
  const btn = document.getElementById('btn-auf'), fehler = document.getElementById('fehler');
  const pw = document.getElementById('pw').value.trim();   // gegen Leerzeichen aus der Zwischenablage
  if(!pw){{ fehler.textContent = 'Bitte Passwort eingeben.'; return; }}
  if(!(window.crypto && window.crypto.subtle)){{
    fehler.textContent = 'Dieser Katalog muss über den Link geöffnet werden, nicht als gespeicherte Datei.';
    return;
  }}
  btn.disabled = true; btn.textContent = 'Wird geöffnet …'; fehler.textContent = '';
  try {{
    ARTIKEL = await oeffnen(pw);
    document.getElementById('sperre').remove();
    document.getElementById('inhalt').hidden = false;
    start();
  }} catch (err) {{
    const falsch = err && err.name === 'OperationError';
    fehler.textContent = falsch
      ? 'Passwort falsch. Bitte noch einmal versuchen.'
      : 'Der Katalog lässt sich hier nicht öffnen (' + ((err && err.name) || 'Fehler') + ').';
    console.error('Entschlüsselung fehlgeschlagen:', err);
    btn.disabled = false; btn.textContent = 'Katalog öffnen';
    document.getElementById('pw').select();
  }}
}});
</script>"""
    pfad = os.path.join(AUSGABE, "06_Webkatalog_geschuetzt.html")
    with open(pfad, "w", encoding="utf-8") as f:
        f.write(dok)
    return pfad


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--geschuetzt", metavar="PASSWORT", help="zusätzlich eine verschlüsselte Fassung erzeugen")
    args = ap.parse_args()
    daten = daten_sammeln()
    p = offene_datei(daten)
    print("geschrieben:", p, os.path.getsize(p) // 1024, "KB")
    if args.geschuetzt:
        p = geschuetzte_datei(daten, args.geschuetzt)
        print("geschrieben:", p, os.path.getsize(p) // 1024, "KB  (AES-256-GCM, PBKDF2 210.000 Runden)")
