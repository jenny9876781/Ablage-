<?php
/** Prüft die Reservierungslogik des Plugins gegen eine SQLite-Attrappe. */
$GLOBALS['ATTRAPPE_DB'] = '/tmp/kikripp-test.sqlite';
@unlink($GLOBALS['ATTRAPPE_DB']);
require __DIR__ . '/wp-attrappe.php';

function dbDelta($sql) {
    global $wpdb;
    foreach (array_filter(array_map('trim', explode(';', $sql))) as $teil) {
        $wpdb->query($teil . ';');
    }
}
require __DIR__ . '/../kikripp-katalog/includes/class-kikripp-db.php';
require __DIR__ . '/../kikripp-katalog/includes/class-kikripp-mail.php';
require __DIR__ . '/../kikripp-katalog/includes/class-kikripp-zugang.php';

$fehler = 0; $geprueft = 0;
function pruefe($beschreibung, $ist, $soll) {
    global $fehler, $geprueft;
    $geprueft++;
    $ok = $ist === $soll;
    if (!$ok) { $fehler++; }
    printf("  %s %-58s %s\n", $ok ? 'ok  ' : 'FEHL',
        $beschreibung, $ok ? '' : "ist: " . var_export($ist, true) . "  soll: " . var_export($soll, true));
}
function titel($t) { echo "\n== $t ==\n"; }

update_option('kikripp_frist_tage', 7);
update_option('kikripp_ust_prozent', 19);
update_option('kikripp_vorschau', 1);
update_option('kikripp_mail_an', 'saldi4kids@outlook.com');
update_option('kikripp_firma', 'Kikripp GmbH');
Kikripp_DB::tabellen_anlegen();

/** Artikel anlegen wie der Import es tut. */
function artikel_anlegen($nr, $menge, $preis, $titel = 'Testartikel') {
    global $wpdb;
    $wpdb->insert(Kikripp_DB::t_artikel(), [
        'artnr' => $nr, 'sortierung' => 0, 'menge' => $menge, 'preis_netto' => $preis,
        'aktiv' => 1, 'im_katalog' => 1,
        'daten' => wp_json_encode(['nr' => $nr, 'titel' => $titel, 'einheit' => 'Stück']),
        'aktualisiert' => current_time('mysql'),
    ]);
}
function kontakt($name = 'Testfirma') {
    return ['name' => $name, 'email' => 'test@example.de',
            'telefon' => '07721 123456', 'nachricht' => ''];
}
function katalog_nach($nr) {
    foreach (Kikripp_DB::katalog_artikel() as $a) { if ($a['nr'] === $nr) { return $a; } }
    return null;
}

titel('1. Ausgangslage');
artikel_anlegen('K-001', 10, 100.0, 'Stuhl');
artikel_anlegen('K-002', 1, 1200.0, 'Vitra Sofa');
artikel_anlegen('K-003', 5, 50.0, 'Teppich');
pruefe('drei Artikel im Katalog', count(Kikripp_DB::katalog_artikel()), 3);
pruefe('K-001 zehn Stück frei', katalog_nach('K-001')['frei'], 10);
pruefe('K-001 Status verfügbar', katalog_nach('K-001')['status'], 'verfügbar');

titel('2. Teilreservierung');
$v1 = Kikripp_DB::reservieren(kontakt('Klinik'), ['K-001' => 4]);
pruefe('Reservierung angelegt', is_int($v1) && $v1 > 0, true);
pruefe('noch 6 frei', katalog_nach('K-001')['frei'], 6);
pruefe('4 als reserviert ausgewiesen', katalog_nach('K-001')['reserviert'], 4);
pruefe('Gesamtmenge weiterhin 10', katalog_nach('K-001')['menge'], 10);
pruefe('Status bleibt verfügbar', katalog_nach('K-001')['status'], 'verfügbar');

titel('3. Vollreservierung');
$v2 = Kikripp_DB::reservieren(kontakt('Herr Meier'), ['K-001' => 6]);
pruefe('zweite Reservierung angelegt', is_int($v2), true);
pruefe('null frei', katalog_nach('K-001')['frei'], 0);
pruefe('Status wechselt auf reserviert', katalog_nach('K-001')['status'], 'reserviert');
pruefe('Artikel bleibt sichtbar', katalog_nach('K-001') !== null, true);

titel('4. Überbuchung wird abgewiesen');
$v3 = Kikripp_DB::reservieren(kontakt('Zuspät'), ['K-001' => 1]);
pruefe('Reservierung abgelehnt', is_wp_error($v3), true);
pruefe('Fehlercode', is_wp_error($v3) ? $v3->get_error_code() : '', 'zu_wenig');
pruefe('Meldung nennt die Restmenge', is_wp_error($v3) && strpos($v3->get_error_message(), '0 Stück') !== false, true);
$v4 = Kikripp_DB::reservieren(kontakt(), ['K-003' => 99]);
pruefe('mehr als vorhanden wird abgelehnt', is_wp_error($v4), true);
pruefe('K-003 unverändert frei', katalog_nach('K-003')['frei'], 5);

titel('5. Preis wird beim Reservieren eingefroren');
global $wpdb;
$wpdb->update(Kikripp_DB::t_artikel(), ['preis_netto' => 1450.0], ['artnr' => 'K-002']);
$v5 = Kikripp_DB::reservieren(kontakt('Frühbucher'), ['K-002' => 1]);
$wpdb->update(Kikripp_DB::t_artikel(), ['preis_netto' => 1800.0], ['artnr' => 'K-002']);
$vorgang = Kikripp_DB::vorgang($v5);
pruefe('Position behält den Preis von der Reservierung', (float) $vorgang['positionen'][0]['preis_netto'], 1450.0);

titel('6. Stornieren gibt frei');
Kikripp_DB::vorgang_status($v1, 'storniert');
pruefe('nach Storno 4 frei', katalog_nach('K-001')['frei'], 4);
pruefe('Status wieder verfügbar', katalog_nach('K-001')['status'], 'verfügbar');

titel('7. Ablauf nach Frist');
$wpdb->update(Kikripp_DB::t_vorgang(),
    ['ablauf' => gmdate('Y-m-d H:i:s', time() - 3600)], ['id' => $v2]);
pruefe('abgelaufene Reservierung gibt frei', katalog_nach('K-001')['frei'], 10);
Kikripp_DB::vorgang_verlaengern($v2);
pruefe('Verlängern reserviert wieder', katalog_nach('K-001')['frei'], 4);

titel('8. Bezahlt entfernt aus dem Katalog');
Kikripp_DB::vorgang_status($v2, 'bezahlt');
pruefe('6 bezahlt, 4 bleiben sichtbar', katalog_nach('K-001')['menge'], 4);
pruefe('davon 4 frei', katalog_nach('K-001')['frei'], 4);
Kikripp_DB::vorgang_status($v5, 'bezahlt');
pruefe('vollständig bezahlter Artikel verschwindet', katalog_nach('K-002'), null);
pruefe('Katalog enthält noch zwei Artikel', count(Kikripp_DB::katalog_artikel()), 2);

titel('9. Bezahltes bleibt auch nach Fristablauf weg');
$wpdb->update(Kikripp_DB::t_vorgang(),
    ['ablauf' => gmdate('Y-m-d H:i:s', time() - 86400)], ['id' => $v5]);
pruefe('bezahlter Artikel kommt nicht zurück', katalog_nach('K-002'), null);

titel('10. Mail – und nur eine');
$GLOBALS['mails'] = [];
$v6 = Kikripp_DB::reservieren(kontakt('Mailtest'), ['K-003' => 2]);
Kikripp_Mail::reservierung($v6);
pruefe('genau eine Mail, keine an den Interessenten', count($GLOBALS['mails']), 1);
$m = $GLOBALS['mails'][0];
pruefe('Empfänger ist die Kikripp-Adresse', $m['an'], 'saldi4kids@outlook.com');
pruefe('Betreff nennt Firma und Vorgang',
       strpos($m['betreff'], '[Kikripp GmbH] Neue Reservierung #' . $v6) === 0, true);
pruefe('Text nennt die Artikelnummer', strpos($m['text'], 'K-003') !== false, true);
pruefe('Text nennt die Bruttosumme', strpos($m['text'], '119,00 €') !== false, true);
pruefe('Text nennt Name und Telefon',
       strpos($m['text'], 'Mailtest') !== false && strpos($m['text'], '07721 123456') !== false, true);
pruefe('Bestätigungsfunktion existiert nicht mehr',
       method_exists('Kikripp_Mail', 'bestaetigung'), false);
// Ohne echte Absenderadresse verwerfen fremde Mailanbieter die Mail stillschweigend.
$kopfzeilen = implode(' | ', (array) $m['kopf']);
pruefe('Absender ist gesetzt und existiert',
       strpos($kopfzeilen, 'From: Kikripp GmbH <saldi4kids@outlook.com>') !== false, true);
pruefe('Antwort-an zeigt auf den Interessenten',
       strpos($kopfzeilen, 'Reply-To: Mailtest <test@example.de>') !== false, true);
pruefe('Text verweist auf die Verwaltung statt auf die Mail als einzigen Ort',
       strpos($m['text'], 'auch in der Verwaltung') !== false, true);

titel('11. Kontaktdaten bleiben, bis ein Mensch sie löscht');
// Umgestellt am 29.09.2026: Der Webserver von kikripp.de verschickt keine Mails, meldet
// aber Erfolg. Wuerden die Kontaktdaten daraufhin geloescht, waere jeder Interessent
// unwiederbringlich verloren. Sie bleiben deshalb bis zum Loeschen durch die Nutzerin.
$nach = Kikripp_DB::vorgang($v6);
pruefe('Name bleibt trotz erfolgreicher Mail', $nach['name'], 'Mailtest');
pruefe('E-Mail bleibt', $nach['email'], 'test@example.de');
pruefe('Telefon bleibt', $nach['telefon'], '07721 123456');
pruefe('nicht als gelöscht vermerkt', (int) $nach['kontakt_weg'], 0);
pruefe('Mailversand ist vermerkt', (int) $nach['mail_versandt'], 1);
pruefe('Positionen sind noch da', count($nach['positionen']), 1);
pruefe('Preis ist noch da', (float) $nach['positionen'][0]['preis_netto'], 50.0);
pruefe('Reservierung wirkt weiter', katalog_nach('K-003')['frei'], 3);
pruefe('keine IP gespeichert', array_key_exists('herkunft', $nach), false);
// Der Loeschknopf je Vorgang ist jetzt der einzige Weg, die Daten wieder loszuwerden.
Kikripp_DB::kontakt_loeschen($v6);
$leer = Kikripp_DB::vorgang($v6);
pruefe('von Hand gelöscht: Name weg', $leer['name'], '');
pruefe('von Hand gelöscht: Mail weg', $leer['email'], '');
pruefe('von Hand gelöscht: Telefon weg', $leer['telefon'], '');
pruefe('als gelöscht vermerkt', (int) $leer['kontakt_weg'], 1);
pruefe('die Positionen überleben das Löschen', count($leer['positionen']), 1);
pruefe('die Reservierung wirkt auch danach weiter', katalog_nach('K-003')['frei'], 3);

titel('11b. Scheitert die Mail, bleiben die Kontaktdaten als Netz');
$GLOBALS['mail_geht'] = false;
$GLOBALS['mails'] = [];
$v7 = Kikripp_DB::reservieren(kontakt('Mail kaputt'), ['K-003' => 1]);
Kikripp_Mail::reservierung($v7);
$gespeichert = Kikripp_DB::vorgang($v7);
pruefe('Reservierung trotz Mailfehler gespeichert', $gespeichert !== null, true);
pruefe('Mailfehler ist vermerkt', (int) $gespeichert['mail_versandt'], 0);
pruefe('Kontaktdaten sind noch da', $gespeichert['name'], 'Mail kaputt');
$offen = array_map('intval', Kikripp_DB::kontakte_offen());
pruefe('Vorgang steht auf der Nachliste', in_array((int) $v7, $offen, true), true);
pruefe('der von Hand geleerte steht nicht darauf', in_array((int) $v6, $offen, true), false);
Kikripp_DB::kontakt_loeschen($v7);
pruefe('nach dem Löschen leer', Kikripp_DB::vorgang($v7)['name'], '');
pruefe('und von der Nachliste verschwunden',
       in_array((int) $v7, array_map('intval', Kikripp_DB::kontakte_offen()), true), false);
$GLOBALS['mail_geht'] = true;

titel('12. Testdaten löschen');
$vorher = count(Kikripp_DB::vorgaenge());
$anzahl = Kikripp_DB::testdaten_loeschen();
pruefe('alle Vorgänge waren Testdaten', $anzahl, $vorher);
pruefe('keine Vorgänge mehr vorhanden', count(Kikripp_DB::vorgaenge()), 0);
pruefe('K-001 wieder vollständig frei', katalog_nach('K-001')['frei'], 10);

titel('13. Leere und unsinnige Eingaben');
pruefe('leere Auswahl abgelehnt', is_wp_error(Kikripp_DB::reservieren(kontakt(), [])), true);
pruefe('Menge 0 abgelehnt', is_wp_error(Kikripp_DB::reservieren(kontakt(), ['K-001' => 0])), true);
pruefe('negative Menge abgelehnt', is_wp_error(Kikripp_DB::reservieren(kontakt(), ['K-001' => -5])), true);
pruefe('unbekannter Artikel abgelehnt', is_wp_error(Kikripp_DB::reservieren(kontakt(), ['K-999' => 1])), true);

titel('14. Stillgelegter Artikel');
$wpdb->update(Kikripp_DB::t_artikel(), ['im_katalog' => 0], ['artnr' => 'K-003']);
pruefe('nicht mehr im Katalog', katalog_nach('K-003'), null);
pruefe('auch nicht mehr reservierbar', is_wp_error(Kikripp_DB::reservieren(kontakt(), ['K-003' => 1])), true);

titel('15. Artikel, der aus der Importdatei verschwunden ist');
// K-002 kommt in der neuen Datei nicht mehr vor, K-001 und K-003 schon.
$vorher = katalog_nach('K-002');
pruefe('K-002 ist vorher im Katalog', $vorher !== null, true);
$betroffen = Kikripp_DB::fehlende_stilllegen(['K-001', 'K-003']);
pruefe('genau ein Artikel stillgelegt', $betroffen, ['K-002']);
pruefe('K-002 ist aus dem Katalog verschwunden', katalog_nach('K-002'), null);
pruefe('K-002 ist auch nicht mehr reservierbar',
       is_wp_error(Kikripp_DB::reservieren(kontakt(), ['K-002' => 1])), true);
pruefe('K-002 steht aber noch in der Datenbank',
       (int) $wpdb->get_var("SELECT COUNT(*) FROM " . Kikripp_DB::t_artikel() . " WHERE artnr = 'K-002'"), 1);
pruefe('K-001 blieb unberührt', katalog_nach('K-001') !== null, true);
pruefe('leere Liste legt nichts still', Kikripp_DB::fehlende_stilllegen([]), []);
pruefe('zweiter Lauf legt nichts mehr still', Kikripp_DB::fehlende_stilllegen(['K-001', 'K-003']), []);

titel('16. Zugang über das Passwort im Link');
Kikripp_Zugang::passwort_setzen('geheim-im-link');
pruefe('richtiges Passwort wird erkannt', Kikripp_Zugang::passwort_pruefen('geheim-im-link'), true);
pruefe('falsches Passwort nicht', Kikripp_Zugang::passwort_pruefen('daneben'), false);
pruefe('Leerzeichen werden verziehen', Kikripp_Zugang::passwort_pruefen(trim('  geheim-im-link ')), true);
$GLOBALS['ATTRAPPE_WIRFT_BEI_WEITERLEITUNG'] = true;

function link_aufrufen($pw) {
    $par = Kikripp_Zugang::LINK_PARAMETER;
    $_GET[$par] = $pw;
    $_SERVER['REQUEST_URI'] = '/katalog/?' . $par . '=' . rawurlencode($pw) . '&seite=2';
    $_COOKIE = [];
    $GLOBALS['weiterleitung'] = null;
    try { Kikripp_Zugang::link_einloesen(); } catch (Attrappe_Weiterleitung $e) { /* erwartet */ }
    unset($_GET[$par]);
    return $GLOBALS['weiterleitung'];
}

$ziel = link_aufrufen('geheim-im-link');
pruefe('Zugang gilt sofort', Kikripp_Zugang::hat_zugang(), true);
pruefe('Passwort ist aus der Adresse entfernt',
       strpos((string) $ziel, Kikripp_Zugang::LINK_PARAMETER . '=') === false, true);
pruefe('andere Parameter bleiben erhalten', strpos((string) $ziel, 'seite=2') !== false, true);

$ziel = link_aufrufen('falsches-passwort');
pruefe('falscher Link öffnet nichts', Kikripp_Zugang::hat_zugang(), false);
pruefe('auch dann wird das Passwort entfernt',
       strpos((string) $ziel, Kikripp_Zugang::LINK_PARAMETER . '=') === false, true);
pruefe('Parametername ist nicht der einzelne Buchstabe k',
       Kikripp_Zugang::LINK_PARAMETER !== 'k', true);

$_COOKIE = [];
pruefe('ohne Keks kein Zugang', Kikripp_Zugang::hat_zugang(), false);

// -----------------------------------------------------------------------------
// Fotos aus der Mediathek: Der Import findet ein Bild ueber den Dateinamen.
// Ein falscher Schluessel bedeutet: kein einziger Artikel hat ein Bild.
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
// Die Verwaltungsseite ist seit dem 29.09.2026 der EINZIGE Weg, an die Kontaktdaten
// zu kommen - der Webserver verschickt keine Mails. Bricht diese Anzeige, verliert
// die Nutzerin Interessenten, ohne es zu merken. Deshalb wird sie geprueft.
// -----------------------------------------------------------------------------
// -----------------------------------------------------------------------------
// Zwei Adressen, zwei Zwecke: intern gemeldet wird an ein Postfach, das der Webserver
// wirklich erreicht; angezeigt bekommen Interessenten die Adresse des Verkaufs.
// Wer das verwechselt, zeigt Kaeufern eine Adresse, die niemand liest.
// -----------------------------------------------------------------------------
titel('16b. Meldeadresse und Kontaktadresse sind getrennt');
require_once __DIR__ . '/../kikripp-katalog/includes/class-kikripp-rest.php';
update_option('kikripp_mail_an', 'jennyp@kikripp.de');
update_option('kikripp_kontakt_email', 'saldi4kids@outlook.com');
pruefe('Interessenten sehen die Verkaufsadresse',
       Kikripp_REST::kontakt_email(), 'saldi4kids@outlook.com');
$GLOBALS['mails'] = [];
$v9 = Kikripp_DB::reservieren(kontakt('Trennungstest'), ['K-001' => 1]);
Kikripp_Mail::reservierung($v9);
pruefe('die Meldung geht an die interne Adresse',
       $GLOBALS['mails'][0]['an'], 'jennyp@kikripp.de');
pruefe('und traegt sie auch als Absender',
       strpos(implode(' ', (array) $GLOBALS['mails'][0]['kopf']),
              'From: Kikripp GmbH <jennyp@kikripp.de>') !== false, true);

// Bleibt das neue Feld leer, darf sich fuer eine bestehende Einrichtung nichts aendern.
update_option('kikripp_kontakt_email', '');
pruefe('leeres Feld faellt auf die Meldeadresse zurueck',
       Kikripp_REST::kontakt_email(), 'jennyp@kikripp.de');
update_option('kikripp_kontakt_email', 'saldi4kids@outlook.com');
update_option('kikripp_mail_an', 'saldi4kids@outlook.com');

titel('17. Die Kontaktdaten stehen auf der Verwaltungsseite');
require_once __DIR__ . '/../kikripp-katalog/includes/class-kikripp-admin.php';
$GLOBALS['ist_admin'] = true;
update_option('kikripp_vorschau', 0);
// Eigener Artikel, damit die Bestaende der vorherigen Abschnitte nicht hineinspielen.
artikel_anlegen('Z-001', 3, 250.0, 'Hobelbank');
$v8 = Kikripp_DB::reservieren(
    ['name' => 'Frau Beispiel', 'email' => 'beispiel@example.org',
     'telefon' => '07721 998877', 'wunschtermin' => '', 'nachricht' => 'Samstag möglich?'],
    ['Z-001' => 1]);
Kikripp_Mail::reservierung($v8);
ob_start(); Kikripp_Admin::seite_reservierungen(); $seite = ob_get_clean();
foreach (['Frau Beispiel' => 'der Name',
          'beispiel@example.org' => 'die Mailadresse',
          '07721 998877' => 'die Telefonnummer',
          'Samstag möglich?' => 'die Nachricht',
          'erledigt – Kontaktdaten löschen' => 'der Löschknopf'] as $text => $was) {
    pruefe($was . ' steht auf der Seite', strpos($seite, $text) !== false, true);
}
// Die Nachricht hat eine eigene Zeile ueber die ganze Breite. Sie darf nicht zusaetzlich
// in der Interessentenspalte stehen - am 29.09.2026 stand sie kurzzeitig doppelt da.
pruefe('die Nachricht steht genau einmal da',
       substr_count($seite, 'Samstag möglich?'), 1);

titel('17b. Der Zähler am Menüpunkt ersetzt die Benachrichtigung');
$GLOBALS['menue_titel'] = [];
Kikripp_Admin::menue();
$offene = count(array_filter(Kikripp_DB::vorgaenge(),
    function ($v) { return $v['status'] === 'offen'; }));
pruefe('es gibt offene Vorgänge zum Anzeigen', $offene > 0, true);
pruefe('der Menüpunkt trägt die Zahl der offenen Vorgänge',
       strpos($GLOBALS['menue_titel'][0], '>' . $offene . '<') !== false, true);
pruefe('Import und Einstellungen tragen keine Zahl',
       strpos($GLOBALS['menue_titel'][2] . $GLOBALS['menue_titel'][3], 'count-') === false, true);

titel('17c. Nach dem Löschen ist nichts mehr zu sehen');
Kikripp_DB::kontakt_loeschen($v8);
ob_start(); Kikripp_Admin::seite_reservierungen(); $seite = ob_get_clean();
pruefe('der Name ist weg', strpos($seite, 'Frau Beispiel') === false, true);
pruefe('die Mailadresse ist weg', strpos($seite, 'beispiel@example.org') === false, true);
pruefe('die Seite sagt, dass gelöscht wurde',
       strpos($seite, 'Kontaktdaten gelöscht') !== false, true);
pruefe('die Position bleibt sichtbar', strpos($seite, 'Z-001') !== false, true);

titel('Zuordnung der Fotos aus der Mediathek');
require_once __DIR__ . '/../kikripp-katalog/includes/class-kikripp-admin.php';
function schluessel($n) { $r = Kikripp_Admin::bild_schluessel($n); return $r[0]; }
function ist_genau($n) { $r = Kikripp_Admin::bild_schluessel($n); return $r[1]; }

pruefe('F-001.jpg behaelt seine Nummer',      schluessel('F-001.jpg'), 'F-001');
pruefe('dreistellige Nummer bleibt ganz',     schluessel('F-540.jpg'), 'F-540');
pruefe('vierstellige Nummer bleibt ganz',     schluessel('F-1024.jpg'), 'F-1024');
pruefe('Kleinschreibung wird angeglichen',    schluessel('f-007.JPEG'), 'F-007');
pruefe('Pfad davor stoert nicht',             schluessel('2026/09/F-123.jpg'), 'F-123');
pruefe('WordPress-Zusatz -1 faellt weg',      schluessel('F-001-1.jpg'), 'F-001');
pruefe('auch -12 faellt weg',                 schluessel('F-001-12.jpg'), 'F-001');
pruefe('fremder Dateiname bleibt unberuehrt', schluessel('logo-2024.png'), 'LOGO-2024');
pruefe('leerer Name ergibt leeren Schluessel', schluessel(''), '');
pruefe('genaue Datei ist als genau erkannt',  ist_genau('F-001.jpg'), true);
pruefe('Datei mit Zusatz ist nicht genau',    ist_genau('F-001-1.jpg'), false);

// -----------------------------------------------------------------------------
// Autoptimize buendelt JavaScript und CSS aller Seiten. Landet unser Skript im
// Sammelpaket, bleibt der Katalog leer. Das Plugin traegt sich selbst in die
// Ausschlussliste ein - was die Nutzerin dort stehen hat, muss erhalten bleiben.
// -----------------------------------------------------------------------------
titel('Ausschluss aus der Sammeldatei von Autoptimize');
require_once __DIR__ . '/../kikripp-katalog/includes/class-kikripp-frontend.php';
$aus = ['Kikripp_Frontend', 'nicht_zusammenfassen'];

pruefe('leere Liste ergibt genau unseren Eintrag',
       $aus(''), 'kikripp');
pruefe('vorhandene Eintraege bleiben stehen',
       $aus('wp-includes/js/dist/, jquery.js'), 'wp-includes/js/dist/, jquery.js, kikripp');
pruefe('kein zweiter Eintrag, wenn wir schon drin stehen',
       $aus('jquery.js, kikripp'), 'jquery.js, kikripp');
pruefe('Leerzeichen um die Kommas stoeren nicht',
       $aus('  a.js ,  b.js  '), 'a.js, b.js, kikripp');
pruefe('leere Zwischeneintraege fallen weg',
       $aus('a.js,,b.js'), 'a.js, b.js, kikripp');
pruefe('Autoptimize mit Feld statt Zeichenkette bekommt ein Feld zurueck',
       $aus(['a.js']), ['a.js', 'kikripp']);
pruefe('Feld ohne Doppelung',
       $aus(['kikripp']), ['kikripp']);

printf("\n== Ergebnis: %d Prüfungen, %d Fehler ==\n", $geprueft, $fehler);
exit($fehler > 0 ? 1 : 0);
