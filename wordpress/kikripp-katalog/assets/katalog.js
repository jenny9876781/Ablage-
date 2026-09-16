/* Artikelkatalog Kikripp – Anzeige und Reservierung. Daten kommen live über die
   Schnittstelle, damit ein Seiten-Cache nichts veralten lässt. */
(function () {
  'use strict';

  var W = window.KIKRIPP || {};
  var wurzel = document.getElementById('kikripp-katalog');
  if (!wurzel) { return; }

  var ARTIKEL = [], UST = 0.19, HINWEIS = '', FRIST = 7, IST_ADMIN = false;
  var RECHT = '', ABHOLUNG = '';
  var merk = {};                       // ArtNr -> gewünschte Stückzahl

  function eur(v) {
    return (v || 0).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
  }
  function sicher(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (z) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[z];
    });
  }
  function el(id) { return document.getElementById(id); }

  function hole(pfad, optionen) {
    return fetch(W.basis + pfad, Object.assign({
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store'
    }, optionen || {})).then(function (a) {
      return a.json().then(function (d) { return { status: a.status, daten: d }; });
    });
  }

  // ------------------------------------------------------------------ Sperre

  function zeigeSperre(meldung) {
    wurzel.innerHTML =
      '<div class="sperre"><div class="box">' +
      '<img src="' + sicher(W.signet) + '" alt="">' +
      '<div class="wort">KIKRIPP</div>' +
      '<h2>Artikelkatalog Betriebsauflösung</h2>' +
      '<p>Dieser Bereich ist geschützt. Bitte geben Sie das Passwort ein, das Sie von uns erhalten haben.</p>' +
      '<form id="k-sperrform">' +
      '<input type="password" id="k-pw" placeholder="Passwort" autocomplete="current-password">' +
      '<button type="submit" id="k-auf">Katalog öffnen</button>' +
      '</form><p class="fehler" id="k-fehler" role="alert">' + sicher(meldung || '') + '</p>' +
      '</div></div>';
    el('k-sperrform').addEventListener('submit', function (e) {
      e.preventDefault();
      var pw = el('k-pw').value.trim();
      var knopf = el('k-auf'), fehler = el('k-fehler');
      if (!pw) { fehler.textContent = 'Bitte Passwort eingeben.'; return; }
      knopf.disabled = true; knopf.textContent = 'Wird geprüft …'; fehler.textContent = '';
      hole('/zugang', { method: 'POST', body: JSON.stringify({ passwort: pw }) })
        .then(function (a) {
          if (a.daten && a.daten.ok) { laden(); return; }
          fehler.textContent = (a.daten && a.daten.meldung) || 'Passwort falsch.';
          knopf.disabled = false; knopf.textContent = 'Katalog öffnen';
          el('k-pw').select();
        })
        .catch(function () {
          fehler.textContent = 'Der Katalog ist gerade nicht erreichbar. Bitte später erneut versuchen.';
          knopf.disabled = false; knopf.textContent = 'Katalog öffnen';
        });
    });
  }

  // ------------------------------------------------------------------ Laden

  function laden() {
    wurzel.innerHTML = '<div class="laedt">Katalog wird geladen …</div>';
    hole('/artikel').then(function (a) {
      if (a.status === 401 || (a.daten && a.daten.gesperrt)) { zeigeSperre(''); return; }
      if (!a.daten || !a.daten.ok) { throw new Error('unerwartete Antwort'); }
      ARTIKEL = a.daten.artikel || [];
      UST = a.daten.ust || 0.19;
      HINWEIS = a.daten.hinweis || '';
      FRIST = a.daten.frist || 7;
      IST_ADMIN = !!a.daten.admin;
      RECHT = a.daten.recht || '';
      ABHOLUNG = a.daten.abholung || '';
      geruest();
      render();
    }).catch(function () {
      wurzel.innerHTML = '<div class="meldung schlecht">Der Katalog konnte nicht geladen werden. ' +
        'Bitte laden Sie die Seite neu. Besteht das Problem weiter, melden Sie sich bitte bei uns.</div>';
    });
  }

  // ------------------------------------------------------------------ Gerüst

  function geruest() {
    var kats = [], raeume = [];
    ARTIKEL.forEach(function (a) {
      if (a.kat && kats.indexOf(a.kat) < 0) { kats.push(a.kat); }
      if (a.raum && raeume.indexOf(a.raum) < 0) { raeume.push(a.raum); }
    });
    kats.sort();
    function optionen(liste) {
      return liste.map(function (v) { return '<option>' + sicher(v) + '</option>'; }).join('');
    }
    wurzel.innerHTML =
      (HINWEIS ? '<div class="band">' + sicher(HINWEIS) + '</div>' : '') +
      '<div class="kopf">' +
        '<div class="marke"><img src="' + sicher(W.signet) + '" alt=""><span class="wort">KIKRIPP</span></div>' +
        '<h2>Artikelkatalog aus der Betriebsauflösung</h2>' +
        '<p>Abholung nach Terminvereinbarung · Preise inklusive ' + Math.round(UST * 100) + '&nbsp;% USt' +
        (IST_ADMIN ? ' · <a href="' + sicher(W.verwaltung) + '">Reservierungen verwalten</a>' : '') + '</p>' +
      '</div>' +
      '<div class="filter">' +
        '<div class="zeile">' +
          '<input type="search" id="k-q" placeholder="Suchen: Bezeichnung, Nummer, Beschreibung …">' +
          '<select id="k-kat"><option value="">Alle Kategorien</option>' + optionen(kats) + '</select>' +
          '<select id="k-raum"><option value="">Alle Räume</option>' + optionen(raeume) + '</select>' +
          '<label class="chk"><input type="checkbox" id="k-design"> nur Designstücke</label>' +
          '<label class="chk"><input type="checkbox" id="k-frei" checked> nur verfügbare</label>' +
        '</div>' +
        '<div class="zaehler" id="k-zaehler"></div>' +
      '</div>' +
      '<div class="raster" id="k-raster"></div>' +
      '<div id="k-formular"></div>' +
      (RECHT ? '<div class="recht"><h4>Rechtliche Hinweise</h4><p>' + sicher(RECHT) + '</p>' +
        (ABHOLUNG ? '<p>Abholung nach Terminvereinbarung: ' + sicher(ABHOLUNG) + '</p>' : '') +
        '</div>' : '') +
      '<div class="leiste"><div class="inner">' +
        '<div class="sum" id="k-merk"></div>' +
        '<button class="sek" id="k-leeren">Auswahl leeren</button>' +
        '<button id="k-anfragen">Reservierung abschicken</button>' +
      '</div></div>';

    ['k-q', 'k-kat', 'k-raum', 'k-design', 'k-frei'].forEach(function (id) {
      el(id).addEventListener('input', render);
    });
    el('k-leeren').addEventListener('click', function () {
      merk = {}; render(); leiste();
    });
    el('k-anfragen').addEventListener('click', formular);
    leiste();
  }

  // ------------------------------------------------------------------ Karten

  function render() {
    var q = el('k-q').value.toLowerCase().trim();
    var kat = el('k-kat').value, raum = el('k-raum').value;
    var nurFrei = el('k-frei').checked, nurDesign = el('k-design').checked;
    var liste = ARTIKEL.filter(function (a) {
      return (!q || (a.nr + ' ' + a.titel + ' ' + a.beschr).toLowerCase().indexOf(q) >= 0)
        && (!kat || a.kat === kat) && (!raum || a.raum === raum)
        && (!nurFrei || a.frei > 0) && (!nurDesign || a.design);
    });
    el('k-zaehler').innerHTML = '<b>' + liste.length + '</b> von ' + ARTIKEL.length + ' Positionen';
    el('k-raster').innerHTML = liste.length
      ? liste.map(karte).join('')
      : '<div class="leer">Keine Artikel gefunden – bitte Filter anpassen.</div>';
  }

  function karte(a) {
    var frei = a.frei > 0;
    var bild = a.bild
      ? '<img src="' + sicher(a.bild) + '" alt="' + sicher(a.titel) + '" loading="lazy">'
      : '<div class="kein-bild">kein Foto</div>';
    var abzeichen = frei
      ? '<span class="badge frei">verfügbar</span>'
      : '<span class="badge res">reserviert</span>';
    // Teilreservierung sichtbar machen: „5 von 10 verfügbar“
    var mengeText = !frei
      ? 'vollständig reserviert (' + a.menge + ' ' + a.einheit + ')'
      : (a.reserviert > 0
          ? a.frei + ' von ' + a.menge + ' ' + a.einheit + ' verfügbar'
          : a.menge + ' ' + a.einheit + ' verfügbar');
    var knapp = (a.reserviert > 0 && a.frei > 0) ? ' class="knapp"' : '';
    var brutto = a.preis * (1 + UST);
    var vhb = a.basis === 'VHB' ? '<span class="vhb">VHB</span>' : '';
    var auswahl = frei
      ? '<div class="mengen">' +
          '<input type="number" min="1" max="' + a.frei + '" step="1" value="' + (merk[a.nr] || 1) + '" ' +
          'id="m-' + sicher(a.nr) + '" data-menge="' + sicher(a.nr) + '" aria-label="Stückzahl ' + sicher(a.nr) + '">' +
          '<button data-res="' + sicher(a.nr) + '">reservieren</button>' +
        '</div>'
      : '';
    return '<div class="karte' + (frei ? '' : ' weg') + '">' +
      '<div class="bild">' + bild + '<span class="nr">' + sicher(a.nr) + '</span>' + abzeichen +
        (a.design ? '<span class="dsgn">Designstück</span>' : '') + '</div>' +
      '<div class="txt"><h3>' + sicher(a.titel) + '</h3>' +
      '<p class="b">' + sicher(a.beschr) + '</p>' +
      '<div class="meta">' +
        '<span>Zustand: ' + sicher(a.zustand) + '</span>' +
        '<span' + knapp + '>' + mengeText + '</span>' +
        (a.masse ? '<span>' + sicher(a.masse) + '</span>' : '') +
        '<span>' + sicher(a.raum) + '</span>' +
        '<span>' + sicher(a.versand) + '</span>' +
      '</div>' +
      '<div class="preis"><b>' + eur(brutto) + vhb + '</b>' +
        '<small>inkl. USt · netto ' + eur(a.preis) + ' je ' + sicher(a.einheit) + '</small></div>' +
      auswahl + '</div></div>';
  }

  // Eingabefeld: hart auf die verfügbare Menge begrenzen
  document.addEventListener('input', function (e) {
    var nr = e.target && e.target.dataset && e.target.dataset.menge;
    if (!nr) { return; }
    var a = ARTIKEL.filter(function (x) { return x.nr === nr; })[0];
    if (!a) { return; }
    var n = parseInt(e.target.value, 10);
    if (isNaN(n) || n < 1) { return; }        // leeres Feld beim Tippen zulassen
    if (n > a.frei) { e.target.value = a.frei; }
  });

  // „reservieren“ übernimmt die eingetragene Menge – ohne sie zu verändern
  document.addEventListener('click', function (e) {
    var nr = e.target && e.target.dataset && e.target.dataset.res;
    if (!nr) { return; }
    var a = ARTIKEL.filter(function (x) { return x.nr === nr; })[0];
    if (!a) { return; }
    var feld = el('m-' + nr);
    var n = feld ? parseInt(feld.value, 10) : 1;
    if (isNaN(n) || n < 1) { n = 1; }
    if (n > a.frei) { n = a.frei; if (feld) { feld.value = n; } }
    merk[nr] = n;
    leiste();
    e.target.textContent = 'vorgemerkt ✓';
    setTimeout(function () { e.target.textContent = 'reservieren'; }, 1200);
  });

  // ------------------------------------------------------------------ Leiste

  function auswahl() {
    return Object.keys(merk).map(function (nr) {
      var a = ARTIKEL.filter(function (x) { return x.nr === nr; })[0];
      return a ? { a: a, menge: merk[nr] } : null;
    }).filter(Boolean);
  }

  function leiste() {
    var w = auswahl();
    var stueck = 0, netto = 0;
    w.forEach(function (p) { stueck += p.menge; netto += p.menge * p.a.preis; });
    el('k-merk').innerHTML = stueck
      ? stueck + ' Stück vorgemerkt · <b>' + eur(netto * (1 + UST)) + '</b> <span style="opacity:.8">inkl. USt</span>'
      : 'Noch nichts vorgemerkt – Stückzahl eintragen und auf „reservieren“ klicken.';
    el('k-anfragen').disabled = stueck === 0;
  }

  // ------------------------------------------------------------------ Formular

  function formular() {
    var w = auswahl();
    if (!w.length) { return; }
    var netto = 0, stueck = 0;
    var zeilen = w.map(function (p) {
      netto += p.menge * p.a.preis; stueck += p.menge;
      return '<div><span>' + p.menge + ' × ' + sicher(p.a.nr) + ' ' + sicher(p.a.titel) + '</span>' +
             '<span>' + eur(p.menge * p.a.preis * (1 + UST)) + '</span></div>';
    }).join('');

    el('k-formular').innerHTML =
      '<div class="dlg" id="k-dlg">' +
      '<h3>Reservierung abschicken</h3>' +
      '<p class="s">Wir bestätigen Ihnen die Reservierung per E-Mail und stimmen einen Abholtermin ab. ' +
      'Die Artikel bleiben ' + FRIST + ' Tage für Sie vorgemerkt. Bezahlt wird bei Abholung bzw. per Rechnung. ' +
      'Mit der Reservierung kommt noch kein Kaufvertrag zustande – dieser wird bei der Abholung vor Ort ' +
      'geschlossen. Sie können die Reservierung jederzeit formlos zurücknehmen.</p>' +
      '<div class="pos">' + zeilen +
        '<div style="border-top:1px solid #dcdcdc;margin-top:8px;padding-top:8px">' +
        '<b>' + stueck + ' Stück gesamt</b><b>' + eur(netto * (1 + UST)) + ' inkl. USt</b></div></div>' +
      '<div class="feld"><label for="k-name">Name / Firma *</label><input id="k-name" required></div>' +
      '<div class="feld"><label for="k-mail">E-Mail *</label><input id="k-mail" type="email" required></div>' +
      '<div class="feld"><label for="k-tel">Telefon</label><input id="k-tel"></div>' +
      '<div class="feld"><label for="k-termin">Wunschtermin zur Abholung</label><input id="k-termin" type="date"></div>' +
      '<div class="feld"><label for="k-text">Nachricht (optional)</label><textarea id="k-text" rows="2"></textarea></div>' +
      '<p class="datenschutz">Ihre Angaben werden ausschließlich zur Abwicklung dieser Reservierung ' +
      'verwendet und nach Abschluss des Verkaufs gelöscht.</p>' +
      '<div id="k-meldung"></div>' +
      '<button id="k-senden">Reservierung verbindlich abschicken</button> ' +
      '<button class="sek" style="color:#1a1a1a;border-color:#dcdcdc" id="k-abbrechen">Abbrechen</button>' +
      '</div>';

    el('k-abbrechen').addEventListener('click', function () { el('k-formular').innerHTML = ''; });
    el('k-senden').addEventListener('click', senden);
    el('k-dlg').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function senden() {
    var knopf = el('k-senden'), meldung = el('k-meldung');
    var nutzlast = {
      name: el('k-name').value.trim(),
      email: el('k-mail').value.trim(),
      telefon: el('k-tel').value.trim(),
      wunschtermin: el('k-termin').value,
      nachricht: el('k-text').value.trim(),
      artikel: merk
    };
    if (!nutzlast.name) { meldung.innerHTML = '<div class="meldung schlecht">Bitte geben Sie Ihren Namen oder Ihre Firma an.</div>'; return; }
    if (!nutzlast.email) { meldung.innerHTML = '<div class="meldung schlecht">Bitte geben Sie eine E-Mail-Adresse an.</div>'; return; }

    knopf.disabled = true; knopf.textContent = 'Wird abgeschickt …'; meldung.innerHTML = '';
    hole('/reservierung', { method: 'POST', body: JSON.stringify(nutzlast) })
      .then(function (a) {
        if (a.daten && a.daten.ok) {
          ARTIKEL = a.daten.artikel || ARTIKEL;
          merk = {};
          el('k-formular').innerHTML =
            '<div class="meldung gut"><strong>Vielen Dank – Ihre Reservierung ist eingegangen.</strong><br>' +
            'Vorgangsnummer ' + a.daten.vorgang + '. Die Artikel sind ' + (a.daten.frist || FRIST) +
            ' Tage für Sie vorgemerkt. Wir melden uns zur Terminabsprache.' +
            (a.daten.mail ? '' : '<br><em>Hinweis: Die Bestätigungsmail konnte nicht versandt werden. ' +
            'Ihre Reservierung ist trotzdem gespeichert.</em>') + '</div>';
          render(); leiste();
          el('k-formular').scrollIntoView({ behavior: 'smooth', block: 'center' });
          return;
        }
        if (a.status === 401) { zeigeSperre('Bitte melden Sie sich erneut an.'); return; }
        meldung.innerHTML = '<div class="meldung schlecht">' +
          sicher((a.daten && a.daten.meldung) || 'Die Reservierung konnte nicht gespeichert werden.') + '</div>';
        knopf.disabled = false; knopf.textContent = 'Reservierung verbindlich abschicken';
        if (a.status === 409) { laden(); }     // Bestand hat sich geändert – neu einlesen
      })
      .catch(function () {
        meldung.innerHTML = '<div class="meldung schlecht">Die Verbindung ist abgebrochen. ' +
          'Bitte prüfen Sie Ihre Internetverbindung und versuchen Sie es erneut.</div>';
        knopf.disabled = false; knopf.textContent = 'Reservierung verbindlich abschicken';
      });
  }

  if (W.zugang) { laden(); } else { zeigeSperre(''); }
})();
