/* Artikelkatalog Kikripp – Anzeige und Reservierung. Daten kommen live über die
   Schnittstelle, damit ein Seiten-Cache nichts veralten lässt. */
(function () {
  'use strict';

  var W = window.KIKRIPP || {};
  var wurzel = document.getElementById('kikripp-katalog');
  if (!wurzel) { return; }

  var ARTIKEL = [], UST = 0.19, HINWEIS = '', FRIST = 3, IST_ADMIN = false;
  var RECHT = '', ABHOLUNG = '', ANBIETER = {}, STEUER = '', ABLAUF = '';
  var MINDEST = 0, BES_AB = 0, SCHLUSS = '', HEUTE = '';
  var BES_ZEITEN = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30'];
  var formularSeit = 0;
  var merk = {};                       // ArtNr -> gewünschte Stückzahl

  function eur(v) {
    return (v || 0).toLocaleString('de-DE', { style: 'currency', currency: 'EUR' });
  }
  function sicher(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (z) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[z];
    });
  }
  // Zeilenumbrueche aus der Arbeitsmappe (Alt+Enter in Excel) sollen im Katalog
  // auch als Umbruch ankommen. Erst maskieren, dann umwandeln - nie umgekehrt.
  function absatz(s) { return sicher(s).replace(/\r?\n/g, '<br>'); }
  function el(id) { return document.getElementById(id); }
  function brutto(p) { return p * (1 + UST); }

  // Datumsrechnung immer in UTC und ab dem Serverdatum - die Uhr des Besuchers kann falsch gehen.
  function tag(iso) { return new Date(iso + 'T12:00:00Z'); }
  function iso(d) { return d.toISOString().slice(0, 10); }
  var WOCHENTAG = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  function datumText(isoDatum) {
    var d = tag(isoDatum);
    return WOCHENTAG[d.getUTCDay()] + ', ' + ('0' + d.getUTCDate()).slice(-2) + '.' +
           ('0' + (d.getUTCMonth() + 1)).slice(-2) + '.' + d.getUTCFullYear();
  }
  /** Alle Tage mit den gewünschten Wochentagen ab morgen bis zum Abholschluss. */
  function tage(wochentage) {
    var aus = [];
    if (!HEUTE) { return aus; }
    var d = tag(HEUTE), ende = SCHLUSS ? tag(SCHLUSS) : new Date(d.getTime() + 70 * 864e5);
    for (d = new Date(d.getTime() + 864e5); d <= ende && aus.length < 40; d = new Date(d.getTime() + 864e5)) {
      if (wochentage.indexOf(d.getUTCDay()) >= 0) { aus.push(iso(d)); }
    }
    return aus;
  }

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
      UST = typeof a.daten.ust === 'number' ? a.daten.ust : 0.19;   // 0 = steuerfrei, nicht „fehlt“
      STEUER = a.daten.steuer || '';
      ABLAUF = a.daten.ablauf || '';
      MINDEST = a.daten.mindestwert || 0;
      BES_AB = a.daten.besichtigung_ab || 0;
      SCHLUSS = a.daten.abholschluss || '';
      HEUTE = a.daten.heute || iso(new Date());
      HINWEIS = a.daten.hinweis || '';
      FRIST = a.daten.frist || 3;
      IST_ADMIN = !!a.daten.admin;
      RECHT = a.daten.recht || '';
      ABHOLUNG = a.daten.abholung || '';
      ANBIETER = a.daten.anbieter || {};
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
        '<p>' + (ANBIETER.firma ? 'Ein Angebot der ' + sicher(ANBIETER.firma) + ' · ' : '') +
        'Abholung durch den Käufer · ' +
        (UST > 0 ? 'Preise inklusive ' + Math.round(UST * 100) + '&nbsp;% USt' : 'Endpreise, umsatzsteuerfrei') +
        (IST_ADMIN ? ' · <a href="' + sicher(W.verwaltung) + '">Reservierungen verwalten</a>' : '') + '</p>' +
      '</div>' +
      ablaufKasten() +
      '<div class="leiste"><div class="inner">' +
        '<div class="sum" id="k-merk"></div>' +
        '<button class="sek" id="k-leeren">Auswahl leeren</button>' +
        '<button id="k-anfragen">Reservierung abschicken</button>' +
      '</div></div>' +
      '<div class="filter">' +
        '<div class="zeile">' +
          '<input type="search" id="k-q" placeholder="Suchen: Bezeichnung, Nummer, Beschreibung …">' +
          '<select id="k-kat"><option value="">Alle Kategorien</option>' + optionen(kats) + '</select>' +
          '<select id="k-raum"><option value="">Alle Räume</option>' + optionen(raeume) + '</select>' +
          '<label class="chk"><input type="checkbox" id="k-design"> nur Markenware</label>' +
          '<label class="chk"><input type="checkbox" id="k-frei" checked> nur verfügbare</label>' +
        '</div>' +
        '<div class="zaehler" id="k-zaehler"></div>' +
      '</div>' +
      '<div class="raster" id="k-raster"></div>' +
      '<div id="k-formular"></div>' +
      ((RECHT || ANBIETER.firma) ? '<div class="recht">' + anbieterBlock() +
        (RECHT ? '<h4>Kaufbedingungen</h4>' + RECHT.split(/\n\s*\n/).map(function (t) {
          return '<p>' + absatz(t.trim()) + '</p>'; }).join('') : '') +
        ((ABHOLUNG && ABHOLUNG !== ANBIETER.adresse)
          ? '<p>Abholung nach Terminvereinbarung: ' + sicher(ABHOLUNG) + '</p>' : '') +
        '</div>' : '');

    ['k-q', 'k-kat', 'k-raum', 'k-design', 'k-frei'].forEach(function (id) {
      el(id).addEventListener('input', render);
    });
    el('k-leeren').addEventListener('click', function () {
      merk = {}; render(); leiste();
    });
    el('k-anfragen').addEventListener('click', formular);
    leiste();
  }

  /* „So läuft es ab“: jede Zeile aus den Einstellungen wird ein Punkt. Auf dem Telefon
     zugeklappt, damit die Artikel nicht erst nach einem Bildschirm Text beginnen. */
  function ablaufKasten() {
    var punkte = String(ABLAUF).split(/\r?\n/).map(function (t) { return t.trim(); }).filter(Boolean);
    if (!punkte.length) { return ''; }
    var offen = window.matchMedia && window.matchMedia('(min-width: 561px)').matches;
    return '<details class="ablauf"' + (offen ? ' open' : '') + '><summary>So läuft es ab</summary><ul>' +
      punkte.map(function (t) { return '<li>' + sicher(t) + '</li>'; }).join('') + '</ul></details>';
  }

  /* Anbieterkennzeichnung. Der Katalog liegt auf fremdem Speicherplatz — es muss
     deshalb unmissverständlich dranstehen, wer hier verkauft. */
  function anbieterBlock() {
    if (!ANBIETER.firma) { return ''; }
    var zeilen = [sicher(ANBIETER.firma)];
    if (ANBIETER.adresse) {
      // Die Abholadresse beginnt meist mit der Firma – dann nicht doppelt nennen.
      var a = String(ANBIETER.adresse);
      zeilen.push(sicher(a.indexOf(ANBIETER.firma) === 0
        ? a.slice(ANBIETER.firma.length).replace(/^[,\s]+/, '') : a));
    }
    var kontakt = [];
    if (ANBIETER.telefon) { kontakt.push('Telefon ' + sicher(ANBIETER.telefon)); }
    if (ANBIETER.email) {
      kontakt.push('<a href="mailto:' + sicher(ANBIETER.email) + '">' + sicher(ANBIETER.email) + '</a>');
    }
    if (ANBIETER.impressum) {
      kontakt.push('<a href="' + sicher(ANBIETER.impressum) + '" target="_blank" rel="noopener">Impressum</a>');
    }
    if (ANBIETER.datenschutz) {
      kontakt.push('<a href="' + sicher(ANBIETER.datenschutz) + '" target="_blank" rel="noopener">Datenschutz</a>');
    }
    return '<h4>Anbieter</h4><p>' + zeilen.join(' · ') + '</p>' +
           (kontakt.length ? '<p>' + kontakt.join(' · ') + '</p>' : '');
  }

  // ------------------------------------------------------------------ Karten

  function render() {
    var q = el('k-q').value.toLowerCase().trim();
    var kat = el('k-kat').value, raum = el('k-raum').value;
    var nurFrei = el('k-frei').checked, nurDesign = el('k-design').checked;
    var liste = ARTIKEL.filter(function (a) {
      return (!q || (a.nr + ' ' + a.titel + ' ' + a.beschr + ' ' + (a.buendel || '')).toLowerCase().indexOf(q) >= 0)
        && (!kat || a.kat === kat) && (!raum || a.raum === raum)
        && (!nurFrei || a.frei > 0) && (!nurDesign || !!a.marke);
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
        (a.marke ? '<span class="markenschild">' + sicher(a.marke) + '</span>' : '') + '</div>' +
      '<div class="txt"><h3>' + sicher(a.titel) + '</h3>' +
      '<p class="b">' + absatz(a.beschr) + '</p>' +
      (a.mengenhinweis ? '<p class="hw">' + absatz(a.mengenhinweis) + '</p>' : '') +
      '<div class="meta">' +
        '<span>Zustand: ' + sicher(a.zustand) + '</span>' +
        '<span' + knapp + '>' + mengeText + '</span>' +
        (a.masse ? '<span>' + sicher(a.masse) + '</span>' : '') +
        '<span>' + sicher(a.raum) + '</span>' +
        (BES_AB > 0 && a.preis >= BES_AB ? '<span class="bes">Besichtigung möglich</span>' : '') +
        (a.buendel ? '<span class="bnd">Sammlung ' + sicher(a.buendel) + '</span>' : '') +
      '</div>' +
      '<div class="preis"><b>' + eur(brutto(a.preis)) + vhb + '</b>' +
        '<small>' + (UST > 0 ? 'inkl. USt · netto ' + eur(a.preis) : sicher(STEUER || 'Endpreis')) +
        ' · je ' + sicher(a.einheit) + '</small></div>' +
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
    var fehlt = MINDEST > 0 ? MINDEST - brutto(netto) : 0;
    el('k-merk').innerHTML = stueck
      ? stueck + ' Stück vorgemerkt · <b>' + eur(brutto(netto)) + '</b>' +
        (UST > 0 ? ' <span style="opacity:.8">inkl. USt</span>' : '') +
        (fehlt > 0.004 ? '<br><span class="mindest">Mindestbestellwert ' + eur(MINDEST) +
          ' – es fehlen noch ' + eur(fehlt) + '</span>' : '')
      : 'Noch nichts vorgemerkt – Stückzahl eintragen und auf „reservieren“ klicken.' +
        (MINDEST > 0 ? ' Mindestbestellwert ' + eur(MINDEST) + '.' : '');
    el('k-anfragen').disabled = stueck === 0 || fehlt > 0.004;
    // Ohne Auswahl braucht die Leiste auf dem Telefon keine Knoepfe (siehe katalog.css).
    var l = wurzel.querySelector('.leiste');
    if (l) { l.className = stueck ? 'leiste' : 'leiste leer'; }
  }

  // ------------------------------------------------------------------ Formular

  function auswahlFeld(id, liste, leer) {
    return '<select id="' + id + '"><option value="">' + sicher(leer) + '</option>' +
      liste.map(function (w) { return '<option value="' + sicher(w[0]) + '">' + sicher(w[1]) + '</option>'; }).join('') +
      '</select>';
  }

  function formular() {
    var w = auswahl();
    if (!w.length) { return; }
    var netto = 0, stueck = 0, teuerster = 0;
    var zeilen = w.map(function (p) {
      netto += p.menge * p.a.preis; stueck += p.menge; teuerster = Math.max(teuerster, p.a.preis);
      return '<div><span>' + p.menge + ' × ' + sicher(p.a.nr) + ' ' + sicher(p.a.titel) + '</span>' +
             '<span>' + eur(brutto(p.menge * p.a.preis)) + '</span></div>';
    }).join('');
    var mitBesichtigung = BES_AB > 0 && teuerster >= BES_AB;
    var donnerstage = tage([4]).map(function (d) { return [d, datumText(d)]; });
    var abholtage = tage([1, 2]).map(function (d) { return [d, datumText(d)]; });

    el('k-formular').innerHTML =
      '<div class="dlg" id="k-dlg">' +
      '<h3>Reservierung abschicken</h3>' +
      '<p class="s">Die Artikel bleiben ' + FRIST + ' Werktage für Sie reserviert. Nach Eingang Ihrer Reservierung ' +
      'rufen wir Sie an. Eine Reservierung ist noch kein Kaufvertrag – dieser kommt mit Ihrer unterschriebenen ' +
      'Bestellung zustande. Sie können die Reservierung jederzeit formlos zurücknehmen.</p>' +
      '<div class="pos">' + zeilen +
        '<div style="border-top:1px solid #dcdcdc;margin-top:8px;padding-top:8px">' +
        '<b>' + stueck + ' Stück gesamt</b><b>' + eur(brutto(netto)) + (UST > 0 ? ' inkl. USt' : '') + '</b></div></div>' +
      '<div class="feld"><label for="k-name">Name *</label><input id="k-name" autocomplete="name" required></div>' +
      '<div class="feld"><label for="k-firma">Firma / Einrichtung</label><input id="k-firma" autocomplete="organization">' +
      '<small class="hint">Leer lassen, wenn Sie als Privatperson kaufen.</small></div>' +
      '<div class="feld"><label for="k-strasse">Straße und Hausnummer *</label><input id="k-strasse" autocomplete="street-address" required></div>' +
      '<div class="feld zwei"><div><label for="k-plz">PLZ *</label><input id="k-plz" inputmode="numeric" autocomplete="postal-code" maxlength="5" required></div>' +
      '<div><label for="k-ort">Ort *</label><input id="k-ort" autocomplete="address-level2" required></div></div>' +
      '<div class="feld"><label for="k-mail">E-Mail *</label><input id="k-mail" type="email" autocomplete="email" required></div>' +
      '<div class="feld"><label for="k-tel">Telefon *</label><input id="k-tel" type="tel" autocomplete="tel" required>' +
      '<small class="hint">Wir rufen Sie nach der Reservierung an – bitte unbedingt angeben.</small></div>' +
      (mitBesichtigung
        ? '<div class="feld"><label class="chk2"><input type="checkbox" id="k-bes"> Ich möchte die Artikel vorab besichtigen ' +
          '(donnerstags 08:00–11:00 Uhr)</label>' +
          '<div class="zwei" id="k-bes-wahl" hidden><div>' + auswahlFeld('k-bes-tag', donnerstage, 'Donnerstag wählen') + '</div>' +
          '<div>' + auswahlFeld('k-bes-zeit', BES_ZEITEN.map(function (z) { return [z, z + ' Uhr']; }), 'Uhrzeit wählen') + '</div></div></div>'
        : '') +
      '<div class="feld"><label for="k-abhol">Gewünschter Abholtermin *</label>' +
        auswahlFeld('k-abhol', abholtage, 'Montag oder Dienstag wählen') +
        '<small class="hint">Abholung montags und dienstags 08:00–11:00 Uhr' +
        (SCHLUSS ? ', spätestens ' + datumText(SCHLUSS).slice(4) : '') + '. Abgeholt wird nach Zahlungseingang.</small>' +
        '<label class="chk2"><input type="checkbox" id="k-demontage"> Demontage nötig – Termin Freitagnachmittag ' +
        'oder Samstagvormittag nach Vereinbarung</label></div>' +
      '<div class="feld"><label for="k-text">Nachricht (optional)</label><textarea id="k-text" rows="2"></textarea></div>' +
      // Unsichtbares Feld gegen Formular-Roboter. Menschen sehen es nicht und lassen es leer.
      '<div class="hp" aria-hidden="true"><label for="k-webseite">Webseite</label>' +
      '<input id="k-webseite" tabindex="-1" autocomplete="off"></div>' +
      '<p class="datenschutz">Ihre Angaben verwenden wir ausschließlich zur Abwicklung dieser Reservierung und für ' +
      'Bestellung und Rechnung. Sie werden auf dieser Website gespeichert und nach Abschluss des Verkaufs gelöscht; ' +
      'Rechnungsdaten bewahren wir so lange auf, wie es das Gesetz verlangt. ' +
      '<strong>Sie erhalten keine Bestätigungsmail</strong> – bitte machen Sie im nächsten Schritt ein Bildschirmfoto.</p>' +
      '<div id="k-meldung"></div>' +
      '<button id="k-senden">Reservierung verbindlich abschicken</button> ' +
      '<button class="sek" style="color:#1a1a1a;border-color:#dcdcdc" id="k-abbrechen">Abbrechen</button>' +
      '</div>';

    formularSeit = Date.now();
    if (el('k-bes')) {
      el('k-bes').addEventListener('change', function () { el('k-bes-wahl').hidden = !this.checked; });
    }
    el('k-abbrechen').addEventListener('click', function () { el('k-formular').innerHTML = ''; });
    el('k-senden').addEventListener('click', senden);
    el('k-dlg').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  var letzteAuswahl = [];


  function beleg_positionen() {
    var netto = 0, stueck = 0;
    var zeilen = letzteAuswahl.map(function (p) {
      netto += p.menge * p.preis; stueck += p.menge;
      return '<div class="zeile"><span>' + p.menge + ' × ' + sicher(p.nr) + ' ' +
             sicher(p.titel) + '</span><b>' + eur(brutto(p.menge * p.preis)) + '</b></div>';
    }).join('');
    return zeilen + '<div class="zeile summe"><span>' + stueck + ' Stück gesamt</span><b>' +
           eur(brutto(netto)) + (UST > 0 ? ' inkl. USt' : '') + '</b></div>';
  }

  function senden() {
    var knopf = el('k-senden'), meldung = el('k-meldung');
    letzteAuswahl = auswahl().map(function (p) {
      return { nr: p.a.nr, titel: p.a.titel, preis: p.a.preis, menge: p.menge };
    });
    function wert(id) { return el(id) ? el(id).value.trim() : ''; }
    var besichtigung = !!(el('k-bes') && el('k-bes').checked);
    var nutzlast = {
      name: wert('k-name'), firma: wert('k-firma'), strasse: wert('k-strasse'),
      plz: wert('k-plz'), ort: wert('k-ort'),
      email: wert('k-mail'), telefon: wert('k-tel'), nachricht: wert('k-text'),
      besichtigung: besichtigung, besichtigung_tag: wert('k-bes-tag'), besichtigung_zeit: wert('k-bes-zeit'),
      abholwunsch: wert('k-abhol'), demontage: !!(el('k-demontage') && el('k-demontage').checked),
      webseite: wert('k-webseite'), dauer: Date.now() - formularSeit,
      artikel: merk
    };
    function fehler(t) { meldung.innerHTML = '<div class="meldung schlecht">' + t + '</div>'; }
    if (!nutzlast.name) { fehler('Bitte geben Sie Ihren Namen an.'); return; }
    if (!nutzlast.strasse || !nutzlast.ort || !/^\d{4,5}$/.test(nutzlast.plz)) {
      fehler('Bitte geben Sie Ihre vollständige Anschrift an (Straße, Postleitzahl, Ort) – sie wird für die Rechnung gebraucht.');
      return;
    }
    if (!nutzlast.email) { fehler('Bitte geben Sie eine E-Mail-Adresse an.'); return; }
    if (nutzlast.telefon.replace(/\D/g, '').length < 6) {
      fehler('Bitte geben Sie eine Telefonnummer an, unter der wir Sie erreichen. Wir rufen Sie nach der ' +
        'Reservierung an.');
      return;
    }
    if (besichtigung && (!nutzlast.besichtigung_tag || !nutzlast.besichtigung_zeit)) {
      fehler('Bitte wählen Sie für die Besichtigung einen Donnerstag und eine Uhrzeit.'); return;
    }
    if (!nutzlast.abholwunsch && !nutzlast.demontage) {
      fehler('Bitte wählen Sie einen Wunschtermin für die Abholung oder kreuzen Sie an, dass eine Demontage nötig ist.');
      return;
    }

    knopf.disabled = true; knopf.textContent = 'Wird abgeschickt …'; meldung.innerHTML = '';
    hole('/reservierung', { method: 'POST', body: JSON.stringify(nutzlast) })
      .then(function (a) {
        if (a.daten && a.daten.ok) {
          // Die Bildschirmbestätigung ist der einzige Nachweis, den der Interessent
          // bekommt – es geht bewusst keine Mail an ihn. Deshalb steht hier alles,
          // was er später braucht, in einem Block zum Abfotografieren.
          var k = a.daten.kontakt || {};
          el('k-formular').innerHTML =
            '<div class="meldung gut"><strong>Vielen Dank – Ihre Reservierung ist eingegangen.</strong><br>' +
            'Wir rufen Sie in den nächsten Tagen an.' +
            '<div class="beleg">' +
              '<div class="zeile"><span>Vorgangsnummer</span><b>' + a.daten.vorgang + '</b></div>' +
              (a.daten.bis ? '<div class="zeile"><span>Reserviert bis</span><b>' + datumText(a.daten.bis) + '</b></div>' : '') +
              beleg_positionen() +
              (nutzlast.besichtigung ? '<div class="zeile"><span>Besichtigung gewünscht</span><b>' +
                datumText(nutzlast.besichtigung_tag) + ', ' + sicher(nutzlast.besichtigung_zeit) + ' Uhr</b></div>' : '') +
              '<div class="zeile"><span>Abholung gewünscht</span><b>' +
                (nutzlast.abholwunsch ? datumText(nutzlast.abholwunsch) : '') +
                (nutzlast.demontage ? (nutzlast.abholwunsch ? ' · ' : '') + 'Demontage nach Vereinbarung' : '') + '</b></div>' +
              (k.email || k.telefon
                ? '<div class="zeile"><span>Wir erreichen Sie unter</span><b>' +
                  [k.email, k.telefon].filter(Boolean).map(sicher).join(' · ') + '</b></div>'
                : '') +
            '</div>' +
            '<p class="s" style="margin:10px 0 0">Bitte machen Sie ein <strong>Bildschirmfoto</strong> – ' +
            'Sie erhalten keine Bestätigungsmail. Stimmen Ihre Kontaktdaten nicht? Schreiben Sie uns ' +
            (ANBIETER.email ? 'an <a href="mailto:' + sicher(ANBIETER.email) + '">' +
              sicher(ANBIETER.email) + '</a>' : 'kurz') + '.</p>' +
            (a.daten.mail ? '' : '<p class="s" style="margin:8px 0 0"><em>Ihre Reservierung ist ' +
            'gespeichert. Sollten wir uns nicht innerhalb von zwei Werktagen melden, ' +
            'kontaktieren Sie uns bitte noch einmal.</em></p>') +
            '</div>';
          ARTIKEL = a.daten.artikel || ARTIKEL;
          merk = {};
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
