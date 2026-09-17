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
update_option('kikripp_mail_an', 'jennyp@kikripp.de');
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
pruefe('Empfänger ist die Kikripp-Adresse', $m['an'], 'jennyp@kikripp.de');
pruefe('Betreff nennt Firma und Vorgang',
       strpos($m['betreff'], '[Kikripp GmbH] Neue Reservierung #' . $v6) === 0, true);
pruefe('Text nennt die Artikelnummer', strpos($m['text'], 'K-003') !== false, true);
pruefe('Text nennt die Bruttosumme', strpos($m['text'], '119,00 €') !== false, true);
pruefe('Text nennt Name und Telefon',
       strpos($m['text'], 'Mailtest') !== false && strpos($m['text'], '07721 123456') !== false, true);
pruefe('Bestätigungsfunktion existiert nicht mehr',
       method_exists('Kikripp_Mail', 'bestaetigung'), false);

titel('11. Kontaktdaten verlassen die Datenbank');
$nach = Kikripp_DB::vorgang($v6);
pruefe('Name gelöscht', $nach['name'], '');
pruefe('E-Mail gelöscht', $nach['email'], '');
pruefe('Telefon gelöscht', $nach['telefon'], '');
pruefe('als gelöscht vermerkt', (int) $nach['kontakt_weg'], 1);
pruefe('Positionen sind noch da', count($nach['positionen']), 1);
pruefe('Preis ist noch da', (float) $nach['positionen'][0]['preis_netto'], 50.0);
pruefe('Reservierung wirkt weiter', katalog_nach('K-003')['frei'], 3);
pruefe('keine IP gespeichert', array_key_exists('herkunft', $nach), false);

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
pruefe('der versandte Vorgang steht nicht darauf', in_array((int) $v6, $offen, true), false);
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

printf("\n== Ergebnis: %d Prüfungen, %d Fehler ==\n", $geprueft, $fehler);
exit($fehler > 0 ? 1 : 0);
