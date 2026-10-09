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
require_once __DIR__ . '/../kikripp-katalog/includes/class-kikripp-ablauf.php';
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
// Seit 1.3.0 zählt die Blase die Aufgaben unter „Zu erledigen“, die etwas verlangen.
$offene = count(array_filter(Kikripp_Ablauf::aufgaben(Kikripp_DB::vorgaenge()),
    function ($a) { return $a['art'] === 'warn'; }));
pruefe('es gibt offene Vorgänge zum Anzeigen', $offene > 0, true);
pruefe('der Menüpunkt trägt die Zahl der offenen Aufgaben',
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

titel('20. Reservierung gilt 3 Werktage (Mo–Fr)');
update_option('kikripp_frist_werktage', 3);
pruefe('Freitag + 3 Werktage = Mittwoch', Kikripp_DB::ablauf_nach_werktagen('2026-10-09 15:00:00', 3), '2026-10-14 23:59:59');
pruefe('Montag + 3 Werktage = Donnerstag', Kikripp_DB::ablauf_nach_werktagen('2026-10-12 08:00:00', 3), '2026-10-15 23:59:59');
pruefe('Samstag + 3 Werktage = Mittwoch', Kikripp_DB::ablauf_nach_werktagen('2026-10-10 10:00:00', 3), '2026-10-14 23:59:59');
artikel_anlegen('W-001', 4, 120.0, 'Sofa');
artikel_anlegen('W-002', 6, 30.0, 'Stuhl');
$vw = Kikripp_DB::reservieren(array_merge(kontakt('Werktag GmbH'), [
    'firma' => 'Werktag GmbH', 'strasse' => 'Hauptstr. 1', 'plz' => '78048', 'ort' => 'VS',
    'besichtigung' => '2026-10-15 09:00', 'abholwunsch' => '2026-10-19', 'demontage' => true]),
    ['W-001' => 1, 'W-002' => 4]);
$gw = Kikripp_DB::vorgang($vw);
pruefe('Ablauf steht auf dem errechneten Werktag',
       $gw['ablauf'], Kikripp_DB::ablauf_nach_werktagen(current_time('mysql'), 3));
pruefe('Firma gespeichert', $gw['firma'], 'Werktag GmbH');
pruefe('Anschrift gespeichert', $gw['strasse'] . '|' . $gw['plz'] . '|' . $gw['ort'], 'Hauptstr. 1|78048|VS');
pruefe('Besichtigung gespeichert', $gw['besichtigung'], '2026-10-15 09:00');
pruefe('Abholwunsch gespeichert', $gw['abholwunsch'], '2026-10-19');
pruefe('Demontage vermerkt', (int) $gw['demontage'], 1);
pruefe('Besichtigung lesbar', Kikripp_Mail::besichtigung_text($gw), 'Do 15.10.2026, 09:00 Uhr');
pruefe('Abholwunsch lesbar mit Demontage', strpos(Kikripp_Mail::abholung_text($gw), 'Mo 19.10.2026; Demontage') === 0, true);

titel('21. Status „bestellt“ läuft nicht ab');
Kikripp_DB::vorgang_status($vw, 'bestellt');
$wpdb->update(Kikripp_DB::t_vorgang(), ['ablauf' => gmdate('Y-m-d H:i:s', time() - 86400)], ['id' => $vw]);
pruefe('bestellter Vorgang hält die Ware trotz abgelaufener Frist', katalog_nach('W-002')['frei'], 2);
pruefe('Positionen bleiben reserviert', Kikripp_DB::vorgang($vw)['positionen'][0]['status'], 'reserviert');
Kikripp_DB::vorgang_status($vw, 'offen');
pruefe('zurück auf reserviert: abgelaufene Frist gibt frei', katalog_nach('W-002')['frei'], 6);
Kikripp_DB::vorgang_verlaengern($vw);
pruefe('verlängern reserviert wieder', katalog_nach('W-002')['frei'], 2);

titel('22. Teilabholung: einzelne Position stornieren');
Kikripp_DB::vorgang_status($vw, 'bestellt');
$pos = Kikripp_DB::vorgang($vw)['positionen'];
$rest = Kikripp_DB::position_stornieren($vw, $pos[1]['id']);
pruefe('eine Position bleibt', $rest, 1);
pruefe('stornierte Position ist wieder frei', katalog_nach('W-002')['frei'], 6);
pruefe('die andere bleibt reserviert', katalog_nach('W-001')['frei'], 3);
pruefe('Vorgang bleibt bestellt', Kikripp_DB::vorgang($vw)['status'], 'bestellt');
Kikripp_DB::vorgang_status($vw, 'bezahlt');
$nach = Kikripp_DB::vorgang($vw)['positionen'];
pruefe('bezahlt: die übrige Position ist bezahlt', $nach[0]['status'], 'bezahlt');
pruefe('bezahlt: die stornierte bleibt storniert', $nach[1]['status'], 'storniert');
pruefe('bezahlter Artikel verlässt den Katalog anteilig', katalog_nach('W-001')['menge'], 3);
$vt = Kikripp_DB::reservieren(kontakt('Teil'), ['W-002' => 1]);
pruefe('letzte Position storniert: nichts bleibt', Kikripp_DB::position_stornieren($vt, Kikripp_DB::vorgang($vt)['positionen'][0]['id']), 0);
pruefe('… und der Vorgang ist storniert', Kikripp_DB::vorgang($vt)['status'], 'storniert');

titel('23. Kontaktdaten löschen nimmt auch die Anschrift mit');
Kikripp_DB::kontakt_loeschen($vw);
$weg = Kikripp_DB::vorgang($vw);
pruefe('Firma weg', $weg['firma'], '');
pruefe('Straße weg', $weg['strasse'], '');
pruefe('Ort weg', $weg['ort'], '');

titel('24. Mail ohne Umsatzsteuer');
update_option('kikripp_ust_prozent', 0);
$GLOBALS['mails'] = [];
$vm = Kikripp_DB::reservieren(array_merge(kontakt('Steuerfrei'), ['firma' => 'Kita Sonnenschein',
    'strasse' => 'Weg 2', 'plz' => '78050', 'ort' => 'VS', 'abholwunsch' => '2026-10-20']), ['W-002' => 2]);
Kikripp_Mail::reservierung($vm);
$t = $GLOBALS['mails'][0]['text'];
pruefe('Summe als umsatzsteuerfrei ausgewiesen', strpos($t, '60,00 € (umsatzsteuerfrei)') !== false, true);
pruefe('keine USt-Zeile', strpos($t, 'USt:') === false && strpos($t, 'brutto') === false, true);
pruefe('keine „netto“-Angabe an den Positionen', strpos($t, 'netto') === false, true);
pruefe('Firma und Anschrift in der Mail', strpos($t, 'Kita Sonnenschein') !== false && strpos($t, 'Weg 2, 78050 VS') !== false, true);
pruefe('Abholwunsch in der Mail', strpos($t, 'Di 20.10.2026') !== false, true);

titel('25. Bestellung erstellen');
update_option('kikripp_rechtstext', "Gebrauchte Artikel.\n\nSteuerfreie Lieferung gemäß § 4 Nr. 28 UStG.");
update_option('kikripp_abholschluss', '2026-12-10');
$GLOBALS['ist_admin'] = true;
$hu = Kikripp_Admin::bestellung_html($vm, 'unternehmen');
$hp = Kikripp_Admin::bestellung_html($vm, 'privat');
pruefe('Unternehmen: Gewährleistung ausgeschlossen', strpos($hu, 'Gewährleistung für Sach- und Rechtsmängel ist ausgeschlossen') !== false, true);
pruefe('Unternehmen: keine Verjährungsklausel', strpos($hu, 'ein Jahr ab Übergabe') === false, true);
pruefe('Privat: gesonderte Verjährungsvereinbarung', strpos($hp, 'Gesonderte Vereinbarung zur Verjährung') !== false
       && strpos($hp, 'ein Jahr ab Übergabe') !== false, true);
pruefe('Privat: eigene Unterschrift für die Klausel', substr_count($hp, 'Unterschrift Käufer'), 2);
pruefe('Privat: Zahlung ebenfalls per Rechnung vorab', strpos($hp, 'per E-Mail versandt') !== false
       && strpos($hp, 'vor Ort unterschrieben') === false, true);
pruefe('Privat: Widerrufsbelehrung', strpos($hp, 'Widerrufsbelehrung') !== false
       && strpos($hp, 'binnen vierzehn Tagen ohne Angabe von Gründen') !== false, true);
pruefe('Privat: Muster-Widerrufsformular', strpos($hp, 'Muster-Widerrufsformular') !== false
       && strpos($hp, 'Hiermit widerrufe(n) ich/wir') !== false, true);
pruefe('Unternehmen: keine Widerrufsbelehrung', strpos($hu, 'Widerrufsbelehrung') === false, true);
pruefe('Unternehmen: Rechnung per Mail, Zahlung vorab', strpos($hu, 'per E-Mail versandt') !== false, true);
pruefe('Steuerhinweis steht drauf', strpos($hu, '§ 4 Nr. 28 UStG') !== false, true);
pruefe('Gesamtbetrag umsatzsteuerfrei', strpos($hu, '(umsatzsteuerfrei)') !== false && strpos($hu, '60,00 €') !== false, true);
pruefe('Abholschluss und Eigentumsrückfall', strpos($hu, '10.12.2026') !== false && strpos($hu, 'ohne Erstattung') !== false, true);
pruefe('Käuferanschrift steht drauf', strpos($hu, 'Kita Sonnenschein') !== false && strpos($hu, '78050 VS') !== false, true);
$vs = Kikripp_DB::reservieren(kontakt('Storno-Test'), ['W-002' => 1, 'W-001' => 1]);
Kikripp_DB::position_stornieren($vs, Kikripp_DB::vorgang($vs)['positionen'][0]['id']);
$hs = Kikripp_Admin::bestellung_html($vs, 'unternehmen');
pruefe('stornierte Position fehlt auf der Bestellung', strpos($hs, '>W-002<') === false && strpos($hs, '>W-001<') !== false, true);
$GLOBALS['ist_admin'] = false;

titel('26. Passwortschutz abschaltbar');
unset($_COOKIE[Kikripp_Zugang::KEKS]);
update_option('kikripp_passwortschutz', 1);
pruefe('mit Schutz und ohne Keks kein Zugang', Kikripp_Zugang::hat_zugang(), false);
update_option('kikripp_passwortschutz', 0);
pruefe('ohne Schutz Zugang für alle', Kikripp_Zugang::hat_zugang(), true);

titel('27. Umstellung einer bestehenden Einrichtung auf 1.2.0');
if (!defined('ABSPATH')) { define('ABSPATH', __DIR__ . '/'); }
foreach (['plugin_dir_path' => function ($f) { return dirname($f) . '/'; },
          'plugin_dir_url' => function ($f) { return '/'; }] as $n => $fn) {
    if (!function_exists($n)) { eval('function ' . $n . '($f) { return ' . ($n === 'plugin_dir_path' ? 'dirname($f) . "/"' : '"/"') . '; }'); }
}
foreach (['register_activation_hook', 'add_action', 'add_filter', 'add_shortcode'] as $n) {
    if (!function_exists($n)) { eval('function ' . $n . '(...$a) { return true; }'); }
}
foreach (['kikripp_plugin_version', 'kikripp_passwortschutz', 'kikripp_frist_werktage', 'kikripp_ablauftext'] as $o) {
    unset($GLOBALS['optionen'][$o]);
}
update_option('kikripp_ust_prozent', 19);
update_option('kikripp_rechtstext', 'alter Text inklusive Umsatzsteuer');
update_option('kikripp_hinweisband', '');
update_option('kikripp_mail_an', 'jennyp@kikripp.de');
require_once __DIR__ . '/../kikripp-katalog/kikripp-katalog.php';
kikripp_umstellen();
pruefe('Umsatzsteuer auf 0', get_option('kikripp_ust_prozent'), 0);
pruefe('Passwortschutz aus', get_option('kikripp_passwortschutz'), 0);
pruefe('3 Werktage', get_option('kikripp_frist_werktage'), 3);
pruefe('Mindestbestellwert 50', get_option('kikripp_mindestwert'), 50);
pruefe('Besichtigung ab 100', get_option('kikripp_besichtigung_ab'), 100);
pruefe('Abholschluss 10.12.2026', get_option('kikripp_abholschluss'), '2026-12-10');
pruefe('neuer Rechtstext mit § 4 Nr. 23', strpos(get_option('kikripp_rechtstext'), '§ 4 Nr. 23 UStG') !== false, true);
pruefe('Ablauftext (Fließtext 1.2.2) nennt die Abholzeiten', strpos(get_option('kikripp_ablauftext'), 'montags und dienstags von 8 bis 11 Uhr') !== false, true);
pruefe('Ablauftext sagt „melden wir uns“', strpos(get_option('kikripp_ablauftext'), 'melden wir uns') !== false, true);
pruefe('Hinweisband angekündigt', strpos(get_option('kikripp_hinweisband'), 'Spielzeugs kommt im November') !== false, true);
pruefe('Meldeadresse bleibt unangetastet', get_option('kikripp_mail_an'), 'jennyp@kikripp.de');
update_option('kikripp_rechtstext', 'von Hand geändert');
update_option('kikripp_hinweisband', 'eigener Text');
kikripp_umstellen();
pruefe('zweiter Lauf überschreibt nichts', get_option('kikripp_rechtstext'), 'von Hand geändert');
pruefe('eigenes Hinweisband bleibt', get_option('kikripp_hinweisband'), 'eigener Text');

titel('28. Fußzeile der Website auf der Katalogseite ausblenden');
if (!function_exists('is_singular')) { function is_singular() { return true; } }
if (!function_exists('get_post')) {
    function get_post() { return (object) ['post_content' => $GLOBALS['seiteninhalt'] ?? '']; }
}
if (!function_exists('has_shortcode')) {
    function has_shortcode($inhalt, $kurz) { return strpos((string) $inhalt, '[' . $kurz) !== false; }
}
$GLOBALS['seiteninhalt'] = '<!-- wp:shortcode -->[kikripp_katalog]<!-- /wp:shortcode -->';
unset($GLOBALS['optionen']['kikripp_fusszeile_aus']);
pruefe('Katalogseite bekommt die Klasse (Vorgabe: an)',
       in_array('kikripp-ohne-fusszeile', Kikripp_Frontend::body_klasse(['page']), true), true);
pruefe('vorhandene Klassen bleiben', in_array('page', Kikripp_Frontend::body_klasse(['page']), true), true);
update_option('kikripp_fusszeile_aus', 0);
pruefe('ausgeschaltet: keine Klasse',
       in_array('kikripp-ohne-fusszeile', Kikripp_Frontend::body_klasse(['page']), true), false);
update_option('kikripp_fusszeile_aus', 1);
$GLOBALS['seiteninhalt'] = 'Impressum der Kikripp GmbH';
pruefe('andere Seiten behalten ihre Fußzeile',
       in_array('kikripp-ohne-fusszeile', Kikripp_Frontend::body_klasse(['page']), true), false);
$css = file_get_contents(__DIR__ . '/../kikripp-katalog/assets/katalog.css');
pruefe('CSS blendet die Block-Theme-Fußzeile aus',
       strpos($css, 'body.kikripp-ohne-fusszeile footer.wp-block-template-part') !== false, true);
pruefe('CSS deckt auch klassische Themes ab',
       strpos($css, 'body.kikripp-ohne-fusszeile #colophon') !== false, true);

titel('29. Umstellung 1.2.0 → 1.2.2: kürzerer Ablauftext');
update_option('kikripp_plugin_version', '1.2.0');
update_option('kikripp_ablauftext', str_replace("\n", "\r\n", kikripp_ablauf_120()));   // so speichert ein Formular
kikripp_umstellen();
pruefe('alter Text wird über 1.2.2 bis zum Text von 1.2.3 ersetzt', get_option('kikripp_ablauftext'), kikripp_ablauf_123());
pruefe('Stand steht auf 1.3.1', get_option('kikripp_plugin_version'), '1.3.1');
update_option('kikripp_plugin_version', '1.2.0');
update_option('kikripp_ablauftext', 'Eigener Text der Nutzerin');
update_option('kikripp_ust_prozent', 7);
kikripp_umstellen();
pruefe('eigener Ablauftext bleibt', get_option('kikripp_ablauftext'), 'Eigener Text der Nutzerin');
pruefe('1.2.2 fasst sonst nichts an', get_option('kikripp_ust_prozent'), 7);

titel('30. Umstellung 1.2.2 → 1.2.3: Bezahlung gegen Rechnung, Widerrufshinweis, Menü');
update_option('kikripp_plugin_version', '1.2.2');
update_option('kikripp_ablauftext', kikripp_ablauf_122());
update_option('kikripp_rechtstext', str_replace("\n", "\r\n", kikripp_rechtstext_120()));
delete_option('kikripp_kopf_aus');
kikripp_umstellen();
pruefe('Ablauftext von 1.2.2 wird ersetzt', get_option('kikripp_ablauftext'), kikripp_ablauf_123());
pruefe('neuer Text: Bezahlung generell gegen Rechnung',
       strpos(get_option('kikripp_ablauftext'), 'generell per Überweisung gegen Rechnung vor der Abholung') !== false, true);
pruefe('Kaufbedingungen bekommen den Widerrufshinweis', get_option('kikripp_rechtstext'), kikripp_rechtstext_123());
pruefe('Menü ausblenden ist eingeschaltet', (int) get_option('kikripp_kopf_aus'), 1);
pruefe('Stand steht auf 1.3.1', get_option('kikripp_plugin_version'), '1.3.1');
update_option('kikripp_plugin_version', '1.2.2');
update_option('kikripp_ablauftext', 'Eigener Text');
update_option('kikripp_rechtstext', 'Eigene Bedingungen');
update_option('kikripp_kopf_aus', 0);
kikripp_umstellen();
pruefe('eigener Ablauftext bleibt', get_option('kikripp_ablauftext'), 'Eigener Text');
pruefe('eigene Kaufbedingungen bleiben', get_option('kikripp_rechtstext'), 'Eigene Bedingungen');
pruefe('ausgeschaltetes Menü-Ausblenden bleibt aus', (int) get_option('kikripp_kopf_aus'), 0);
kikripp_umstellen();
pruefe('läuft nur einmal', get_option('kikripp_ablauftext'), 'Eigener Text');

titel('31. Abholwunsch mit Uhrzeit');
pruefe('mit Uhrzeit lesbar', Kikripp_Mail::abholung_text(['abholwunsch' => '2026-10-19 09:30']), 'Mo 19.10.2026, 09:30 Uhr');
pruefe('ohne Uhrzeit wie bisher', Kikripp_Mail::abholung_text(['abholwunsch' => '2026-10-20']), 'Di 20.10.2026');
$va = Kikripp_DB::reservieren(array_merge(kontakt('Uhrzeit'), ['abholwunsch' => '2026-10-19 10:30']), ['W-002' => 1]);
pruefe('Datum und Uhrzeit passen in die Spalte', Kikripp_DB::vorgang($va)['abholwunsch'], '2026-10-19 10:30');

titel('32. Menü im Kopf der Website auf der Katalogseite ausblenden');
$GLOBALS['seiteninhalt'] = '[kikripp_katalog]';
update_option('kikripp_kopf_aus', 1);
pruefe('Katalogseite bekommt die Klasse', in_array('kikripp-ohne-menue', Kikripp_Frontend::body_klasse([]), true), true);
update_option('kikripp_kopf_aus', 0);
pruefe('ausgeschaltet: keine Klasse', in_array('kikripp-ohne-menue', Kikripp_Frontend::body_klasse([]), true), false);
update_option('kikripp_kopf_aus', 1);
$GLOBALS['seiteninhalt'] = 'Impressum der Kikripp GmbH';
pruefe('andere Seiten bleiben unberührt', in_array('kikripp-ohne-menue', Kikripp_Frontend::body_klasse([]), true), false);
pruefe('CSS blendet Navigation und Social-Icons-Block aus',
       strpos($css, 'body.kikripp-ohne-menue header .wp-block-navigation') !== false
       && strpos($css, 'body.kikripp-ohne-menue header .wp-block-social-links') !== false, true);


titel('33. Abwicklung 1.3.0: Felder am Vorgang');
update_option('kikripp_vorschau', 0);
update_option('kikripp_abholadresse', 'Hermann-Schwer-Str. 1, 78048 Villingen-Schwenningen');
update_option('kikripp_telefon', '07725 5179702');
update_option('kikripp_kontakt_email', 'saldi4kids@outlook.com');
foreach (kikripp_vorgaben_130() as $n => $w) { update_option($n, $w); }
artikel_anlegen('AB-001', 5, 50.0, 'Sitzbank');
$va = Kikripp_DB::reservieren(array_merge(kontakt('Sonja Müller'), ['abholwunsch' => '2026-10-20 10:30']), ['AB-001' => 2]);
pruefe('gültiger Termin wird gespeichert', Kikripp_DB::vorgang_bearbeiten($va, ['abholung' => '2026-10-20 10:30',
    'rechnungsnr' => '4000113', 'rechnung_am' => '2026-10-08', 'notiz' => 'kommt mit Anhänger', 'du' => true]), true);
$g = Kikripp_DB::vorgang($va);
pruefe('Abholung', $g['abholung'], '2026-10-20 10:30');
pruefe('Rechnungsnummer', $g['rechnungsnr'], '4000113');
pruefe('Rechnungsdatum', $g['rechnung_am'], '2026-10-08');
pruefe('Notiz', $g['notiz'], 'kommt mit Anhänger');
pruefe('per Du', (int) $g['du'], 1);
Kikripp_DB::vorgang_bearbeiten($va, ['abholung' => '20.10.2026', 'rechnung_am' => 'gestern']);
$g = Kikripp_DB::vorgang($va);
pruefe('ungültiger Termin wird verworfen, nicht halb gespeichert', $g['abholung'], '');
pruefe('ungültiges Rechnungsdatum wird verworfen', $g['rechnung_am'], '');
Kikripp_DB::vorgang_bearbeiten($va, ['abholung' => '2026-10-20 10:30', 'rechnung_am' => '2026-10-08']);

titel('34. Abgeholt');
Kikripp_DB::vorgang_status($va, 'bestellt');
Kikripp_DB::abgeholt_setzen($va, '2026-10-20');
$g = Kikripp_DB::vorgang($va);
pruefe('abgeholt setzt den Vorgang auf bezahlt', $g['status'], 'bezahlt');
pruefe('Abholdatum steht', $g['abgeholt_am'], '2026-10-20');
pruefe('Ware ist verkauft', katalog_nach('AB-001')['menge'], 3);
pruefe('Reiter: abgeholt', Kikripp_Ablauf::reiter_von($g, time()), 'abgeholt');
Kikripp_DB::abgeholt_setzen($va, '');
$g = Kikripp_DB::vorgang($va);
pruefe('zurücknehmen leert nur das Datum', $g['abgeholt_am'] . '|' . $g['status'], '|bezahlt');
pruefe('Reiter: bezahlt', Kikripp_Ablauf::reiter_von($g, time()), 'bezahlt');
$vs = Kikripp_DB::reservieren(kontakt('Storno'), ['AB-001' => 1]);
Kikripp_DB::vorgang_status($vs, 'storniert');
pruefe('stornierter Vorgang kann nicht abgeholt werden', Kikripp_DB::abgeholt_setzen($vs, '2026-10-20'), false);

titel('35. Zu erledigen');
// Fester Stichtag: Montag, 19.10.2026, 12 Uhr
$jetzt = strtotime('2026-10-19 12:00:00 UTC');
$fall = function ($f) { return array_merge(['id' => 900, 'name' => 'Test Person', 'firma' => '', 'status' => 'bestellt',
    'ablauf' => '2026-10-30 23:59:59', 'abholung' => '', 'rechnungsnr' => '', 'rechnung_am' => '', 'abgeholt_am' => '',
    'kontakt_weg' => 0, 'testdaten' => 0, 'positionen' => [], 'du' => 0, 'email' => 'a@b.de', 'telefon' => '1'], $f); };
$texte = function ($v) use ($jetzt) { return implode(' | ', array_column(Kikripp_Ablauf::aufgaben([$v], $jetzt), 'text')); };
pruefe('neue Reservierung', strpos($texte($fall(['status' => 'offen'])), 'Neue Reservierung') !== false, true);
pruefe('Frist läuft morgen ab', strpos($texte($fall(['status' => 'offen', 'ablauf' => '2026-10-20 23:59:59'])), 'läuft am 20.10.2026 ab') !== false, true);
pruefe('abgelaufen', strpos($texte($fall(['status' => 'offen', 'ablauf' => '2026-10-16 23:59:59'])), 'abgelaufen') !== false, true);
$t = $texte($fall([]));
pruefe('bestellt: Rechnung fehlt', strpos($t, 'Rechnung schreiben') !== false, true);
pruefe('bestellt: Abholtermin fehlt', strpos($t, 'Abholtermin eintragen') !== false, true);
pruefe('5 Tage unbezahlt → Zahlungserinnerung', strpos($texte($fall(['rechnungsnr' => '1', 'rechnung_am' => '2026-10-13',
    'abholung' => '2026-10-27 09:00'])), 'Seit 6 Tagen unbezahlt') !== false, true);
pruefe('4 Tage unbezahlt → noch nicht', $texte($fall(['rechnungsnr' => '1', 'rechnung_am' => '2026-10-15', 'abholung' => '2026-10-27 09:00'])), '');
pruefe('Abholung morgen, unbezahlt → Warnung', strpos($texte($fall(['rechnungsnr' => '1', 'rechnung_am' => '2026-10-19',
    'abholung' => '2026-10-20 10:30'])), 'noch nicht bezahlt') !== false, true);
pruefe('bezahlt, Abholung morgen → bereitstellen (Info)', Kikripp_Ablauf::aufgaben([$fall(['status' => 'bezahlt',
    'abholung' => '2026-10-20 10:30'])], $jetzt)[0]['art'] ?? '', 'info');
pruefe('bezahlt, Termin vorbei, nicht abgeholt', strpos($texte($fall(['status' => 'bezahlt', 'abholung' => '2026-10-13 09:00'])), 'abgeholt?') !== false, true);
pruefe('Privat: Kontaktdaten erst nach 14 Tagen löschen', $texte($fall(['status' => 'bezahlt', 'abgeholt_am' => '2026-10-13'])), '');
pruefe('Privat nach 14 Tagen: löschen', strpos($texte($fall(['status' => 'bezahlt', 'abgeholt_am' => '2026-10-05'])), 'Kontaktdaten löschen') !== false, true);
pruefe('Firma: gleich löschen', strpos($texte($fall(['status' => 'bezahlt', 'firma' => 'Kita GmbH', 'abgeholt_am' => '2026-10-19'])), 'Kontaktdaten löschen') !== false, true);
pruefe('gelöschte Kontaktdaten: nichts mehr zu tun', $texte($fall(['status' => 'bezahlt', 'abgeholt_am' => '2026-10-05', 'kontakt_weg' => 1])), '');
$reihe = Kikripp_Ablauf::aufgaben([$fall(['id' => 1, 'status' => 'bezahlt', 'abgeholt_am' => '2026-10-01']),
    $fall(['id' => 2, 'rechnungsnr' => '1', 'rechnung_am' => '2026-10-19', 'abholung' => '2026-10-20 10:30'])], $jetzt);
pruefe('dringendstes zuerst: unbezahlte Abholung morgen', $reihe[0]['id'] . ':' . $reihe[0]['art'], '2:warn');
pruefe('Testdaten zählen außerhalb der Vorschau nicht', Kikripp_Ablauf::aufgaben([$fall(['testdaten' => 1])], $jetzt), []);
pruefe('Freitag → nächster Werktag ist Montag', Kikripp_Ablauf::naechster_werktag('2026-10-16'), '2026-10-19');
pruefe('Montag → Werktag davor ist Freitag', Kikripp_Ablauf::vorheriger_werktag('2026-10-19'), '2026-10-16');

titel('36. Kennzahlen');
$pos = function ($preis, $menge, $st = 'reserviert') { return ['artnr' => 'X-1', 'menge' => $menge, 'preis_netto' => $preis, 'status' => $st, 'daten' => '{}']; };
$k = Kikripp_Ablauf::kennzahlen([
    $fall(['id' => 1, 'status' => 'bezahlt', 'positionen' => [$pos(50, 2, 'bezahlt')]]),
    $fall(['id' => 2, 'status' => 'bestellt', 'rechnungsnr' => '7', 'positionen' => [$pos(30, 1)]]),
    $fall(['id' => 3, 'status' => 'bestellt', 'positionen' => [$pos(20, 1), $pos(99, 1, 'storniert')]]),
    $fall(['id' => 4, 'status' => 'offen', 'positionen' => [$pos(10, 3)]]),
    $fall(['id' => 5, 'status' => 'offen', 'ablauf' => '2026-10-01 23:59:59', 'positionen' => [$pos(500, 1)]]),
], $jetzt);
pruefe('Umsatz bezahlt', $k['bezahlt'], 100.0);
pruefe('Rechnungen offen', $k['rechnung_offen'], 30.0);
pruefe('bestellt ohne Rechnung (Storno zählt nicht)', $k['ohne_rechnung'], 20.0);
pruefe('reserviert (abgelaufene zählen nicht)', $k['reserviert'], 30.0);

titel('37. Mailtexte: Sie/Du × Privat/Firma');
$m = $fall(['name' => 'Sonja Müller', 'abholung' => '2026-10-20 10:30', 'rechnungsnr' => '4000113', 'rechnung_am' => '2026-10-08',
    'positionen' => [$pos(50, 2)]]);
list($b1, $t1) = Kikripp_Ablauf::mail_text($m);
pruefe('Sie privat: Anrede mit Namen', strpos($t1, 'Guten Tag Sonja Müller,') === 0, true);
pruefe('Termin ausgeschrieben', strpos($t1, 'Ihr Abholtermin: Dienstag, 20.10.2026 um 10:30 Uhr') !== false, true);
pruefe('Zufahrt aus den Einstellungen', strpos($t1, 'Peterzeller Straße 8') !== false, true);
pruefe('Privat: Widerrufsbelehrung erwähnt', strpos($t1, 'Widerrufsbelehrung') !== false, true);
pruefe('Name in der Signatur', strpos($t1, "Mit freundlichen Grüßen\nJenny Preisigke\nKikripp GmbH") !== false, true);
list(, $t2) = Kikripp_Ablauf::mail_text(array_merge($m, ['firma' => 'Kita Sonnenschein']));
pruefe('Sie Firma: Damen und Herren', strpos($t2, 'Sehr geehrte Damen und Herren,') === 0, true);
pruefe('Firma: keine Widerrufsbelehrung', strpos($t2, 'Widerruf') === false, true);
list(, $t3) = Kikripp_Ablauf::mail_text(array_merge($m, ['du' => 1]));
pruefe('Du privat: Vorname', strpos($t3, 'Hallo Sonja,') === 0, true);
pruefe('Du privat: Dein Abholtermin', strpos($t3, 'Dein Abholtermin:') !== false && strpos($t3, 'Viele Grüße') !== false, true);
pruefe('Du privat: Widerruf in Du-Form', strpos($t3, 'findest du in der beigefügten Bestellung') !== false, true);
list(, $t4) = Kikripp_Ablauf::mail_text(array_merge($m, ['du' => 1, 'firma' => 'Kita Sonnenschein']));
pruefe('Du Firma: ihr-Form', strpos($t4, 'Hallo zusammen,') === 0 && strpos($t4, 'Euer Abholtermin') !== false, true);
pruefe('Du Firma: kein Sie, kein Widerruf', strpos($t4, ' Sie ') === false && strpos($t4, 'Widerruf') === false, true);
list(, $t5) = Kikripp_Ablauf::mail_text(array_merge($m, ['abholung' => '']));
pruefe('ohne Termin bleibt ein Platzhalter', strpos($t5, '[Abholtermin]') !== false, true);
list($b6, $t6) = Kikripp_Ablauf::mail_text($m, 'erinnerung');
pruefe('Erinnerung: Betreff mit Rechnungsnummer', $b6, 'Zahlungserinnerung – Rechnung 4000113');
pruefe('Erinnerung: Datum und Betrag', strpos($t6, 'Nr. 4000113 vom 08.10.2026 über 100,00 €') !== false, true);
$link = Kikripp_Ablauf::mailto($m);
pruefe('Mail-Link geht an den Käufer', strpos($link, 'mailto:a%40b.de?subject=') === 0, true);
pruefe('Mail-Link bleibt unter 2000 Zeichen (Outlook)', strlen(Kikripp_Ablauf::mailto(array_merge($m, ['du' => 1]))) < 2000, true);
pruefe('Zeilenumbrüche als CRLF', strpos($link, '%0D%0A') !== false, true);

titel('38. Outlook-Termine');
$ics = Kikripp_Ablauf::ics(array_merge($m, ['id' => 77, 'telefon' => '0171 123', 'notiz' => 'Anhänger, Kombi',
    'positionen' => [['artnr' => 'NE05-02', 'menge' => 2, 'preis_netto' => 50, 'status' => 'reserviert',
                      'daten' => '{"titel":"Sitzbank Massivholz","raum":"Nebenraum","einheit":"Stück"}']]]));
pruefe('zwei Termine', substr_count($ics, 'BEGIN:VEVENT'), 2);
pruefe('Abholung 10:30 Sommerzeit = 08:30 UTC', strpos($ics, 'DTSTART:20261020T083000Z') !== false, true);
pruefe('Erinnerung 15 Minuten vorher', strpos($ics, 'TRIGGER:-PT15M') !== false, true);
pruefe('Vortag Montag 19.10. 11:00 = 09:00 UTC', strpos($ics, 'DTSTART:20261019T090000Z') !== false, true);
pruefe('„Barrierefrei“ vorn im Betreff der Abholung', strpos($ics, 'SUMMARY:Barrierefrei – Abholung #77') !== false, true);
pruefe('„Barrierefrei“ vorn im Betreff des Vortags', strpos($ics, 'SUMMARY:Barrierefrei – Vorbereiten') !== false, true);
pruefe('beide Termine tragen den Zusatz', substr_count($ics, 'SUMMARY:Barrierefrei'), 2);
update_option('kikripp_termin_zusatz', '');
pruefe('leerer Zusatz: kein Präfix', strpos(Kikripp_Ablauf::ics($m), 'SUMMARY:Abholung #') !== false, true);
update_option('kikripp_termin_zusatz', 'Barrierefrei');
pruefe('Vortag erinnert zur Startzeit', strpos($ics, 'TRIGGER:PT0M') !== false, true);
pruefe('feste UID je Vorgang', strpos($ics, 'UID:kikripp-77-abholung@kikripp.de') !== false, true);
pruefe('Artikel mit Raum und Post-it-Code', strpos(str_replace("\r\n ", '', $ics), 'NE05-02 Sitzbank Massivholz – Raum Nebenraum (NE05)') !== false, true);
pruefe('Komma und Strichpunkt maskiert', strpos(str_replace("\r\n ", '', $ics), 'Anhänger\\, Kombi') !== false, true);
pruefe('Zeilen höchstens 75 Byte', max(array_map('strlen', explode("\r\n", $ics))) <= 75, true);
pruefe('Zeilenenden CRLF', substr($ics, -2) === "\r\n" && strpos(str_replace("\r\n", '', $ics), "\n") === false, true);
pruefe('Abholung Montag → Vorbereiten am Freitag', strpos(Kikripp_Ablauf::ics(array_merge($m, ['abholung' => '2026-10-26 09:00'])),
    'DTSTART:20261023T090000Z') !== false, true);
pruefe('Winterzeit: 26.10. 09:00 = 08:00 UTC', strpos(Kikripp_Ablauf::ics(array_merge($m, ['abholung' => '2026-10-26 09:00'])),
    'DTSTART:20261026T080000Z') !== false, true);
pruefe('ohne Termin keine Datei', Kikripp_Ablauf::ics(array_merge($m, ['abholung' => ''])), '');
update_option('kikripp_erinnerung_zeit', '15:30');
pruefe('Uhrzeit der Vortagserinnerung einstellbar', strpos(Kikripp_Ablauf::ics($m), 'DTSTART:20261019T133000Z') !== false, true);
update_option('kikripp_erinnerung_zeit', '11:00');

titel('39. Verwaltungsseite, Abholplan, Dashboard');
$GLOBALS['ist_admin'] = true;
$_GET = [];
Kikripp_DB::vorgang_status($va, 'bestellt');
ob_start(); Kikripp_Admin::seite_reservierungen(); $seite = ob_get_clean();
foreach (['Umsatz bezahlt:' => 'Kennzahlen', 'Zu erledigen (' => 'Aufgabenliste', 'nav-tab-active' => 'Reiter',
          'name="abhol_tag" value="2026-10-20"' => 'Abholtag im Formular', 'name="rechnungsnr" value="4000113"' => 'Rechnungsnummer im Formular',
          '✉ Mail schreiben' => 'Mail-Knopf', '✉ Zahlungserinnerung' => 'Erinnerungs-Knopf', '📅 In Outlook eintragen' => 'Outlook-Knopf',
          '✓ abgeholt' => 'Abgeholt-Knopf', 'id="vorgang-' . $va . '"' => 'Sprungmarke'] as $text => $was) {
    pruefe($was . ' steht auf der Seite', strpos($seite, $text) !== false, true);
}
$_GET = ['reiter' => 'abgeholt'];
ob_start(); Kikripp_Admin::seite_reservierungen(); $seite = ob_get_clean();
pruefe('Reiter „Abgeholt“ blendet bestellte Vorgänge aus', strpos($seite, 'id="vorgang-' . $va . '"') === false, true);
$_GET = [];
$vw = Kikripp_DB::reservieren(array_merge(kontakt('Wunsch Person'), ['abholwunsch' => '2026-10-27']), ['AB-001' => 1]);
ob_start(); Kikripp_Admin::seite_reservierungen(); $seite = ob_get_clean();
pruefe('Abholwunsch wird als Vorschlag vorbelegt', strpos($seite, 'name="abhol_tag" value="2026-10-27"') !== false
       && strpos($seite, 'Wunsch – bitte bestätigen') !== false, true);
ob_start(); Kikripp_Ablauf::seite_abholplan(); $plan = ob_get_clean();
pruefe('Abholplan zeigt den Tag', strpos($plan, 'Dienstag, 20.10.2026') !== false, true);
pruefe('Abholplan: unbezahlt rot markiert', strpos($plan, 'NOCH NICHT BEZAHLT') !== false, true);
pruefe('Abholplan: Artikel mit Bezeichnung und Post-it-Code', strpos($plan, 'Sitzbank') !== false && strpos($plan, '<td>AB</td>') !== false, true);
pruefe('Abholplan: Druckknopf', strpos($plan, 'Tag drucken') !== false, true);
pruefe('Abholplan: Vorgänge ohne Termin', strpos($plan, 'Noch ohne Abholtermin') !== false, true);
$druck = Kikripp_Ablauf::druck_html('2026-10-20');
pruefe('Druckansicht: Titel und Abhakkästchen', strpos($druck, 'Abholungen Dienstag, 20.10.2026') !== false && strpos($druck, '☐') !== false, true);
pruefe('Druckansicht ohne Knöpfe zum Klicken', strpos($druck, '✓ abgeholt') === false, true);
ob_start(); Kikripp_Ablauf::widget(); $w = ob_get_clean();
pruefe('Dashboard-Kasten mit Aufgaben', strpos($w, 'Abholplan') !== false && strpos($w, '<li') !== false, true);

titel('40. Einstellungen und Umstellung 1.3.0');
$_POST = ['zufahrt' => 'Über den Hof', 'mail_name' => 'Anna', 'erinnerung_zeit' => '13:45', 'zahlung_tage' => '7'];
$GLOBALS['ATTRAPPE_WIRFT_BEI_WEITERLEITUNG'] = true;
try { Kikripp_Admin::einstellungen_speichern(); } catch (Attrappe_Weiterleitung $e) {}
pruefe('Zufahrt gespeichert', get_option('kikripp_zufahrt'), 'Über den Hof');
pruefe('Name gespeichert', get_option('kikripp_mail_name'), 'Anna');
pruefe('Erinnerungszeit gespeichert', get_option('kikripp_erinnerung_zeit'), '13:45');
pruefe('Zahlungsfrist gespeichert', get_option('kikripp_zahlung_tage'), 7);
$_POST = ['erinnerung_zeit' => 'mittags'];
try { Kikripp_Admin::einstellungen_speichern(); } catch (Attrappe_Weiterleitung $e) {}
pruefe('ungültige Uhrzeit → 11:00', get_option('kikripp_erinnerung_zeit'), '11:00');
$_POST = [];
foreach (array_keys(kikripp_vorgaben_130()) as $n) { delete_option($n); }
update_option('kikripp_plugin_version', '1.2.5');
kikripp_umstellen();
pruefe('Umstellung setzt die Zufahrt', strpos((string) get_option('kikripp_zufahrt'), 'Peterzeller') !== false, true);
pruefe('Umstellung: 11:00 Uhr', get_option('kikripp_erinnerung_zeit'), '11:00');
pruefe('Umstellung: Zusatz Barrierefrei', get_option('kikripp_termin_zusatz'), 'Barrierefrei');
pruefe('Stand 1.3.1', get_option('kikripp_plugin_version'), '1.3.1');
update_option('kikripp_erinnerung_zeit', '14:00');
update_option('kikripp_plugin_version', '1.3.0');
kikripp_umstellen();
pruefe('1.3.0 → 1.3.1: 14:00 wird 11:00', get_option('kikripp_erinnerung_zeit'), '11:00');
update_option('kikripp_erinnerung_zeit', '13:15');
update_option('kikripp_plugin_version', '1.3.0');
kikripp_umstellen();
pruefe('selbst gewählte Uhrzeit bleibt', get_option('kikripp_erinnerung_zeit'), '13:15');
update_option('kikripp_zufahrt', 'Eigener Text');
update_option('kikripp_plugin_version', '1.2.5');
kikripp_umstellen();
pruefe('eigene Zufahrt bleibt', get_option('kikripp_zufahrt'), 'Eigener Text');
$GLOBALS['ATTRAPPE_WIRFT_BEI_WEITERLEITUNG'] = false;
$GLOBALS['ist_admin'] = false;

printf("\n== Ergebnis: %d Prüfungen, %d Fehler ==\n", $geprueft, $fehler);
exit($fehler > 0 ? 1 : 0);
