<?php
/** Prüft die Kette: Artikel streichen in der Datenbasis -> Import -> weg aus dem Katalog. */
$GLOBALS['ATTRAPPE_DB'] = '/tmp/kikripp-kette.sqlite';
$IMPORT = __DIR__ . '/../../ausgabe/katalog_import.json';
@unlink($GLOBALS['ATTRAPPE_DB']);
require __DIR__ . '/wp-attrappe.php';
$b = __DIR__ . '/../kikripp-katalog/';
require $b . 'includes/class-kikripp-db.php';
function dbDelta($sql) { global $wpdb;
    foreach (array_filter(array_map('trim', explode(';', $sql))) as $t) { $wpdb->query($t . ';'); } }
$GLOBALS['optionen'] = ['kikripp_frist_tage' => 7, 'kikripp_vorschau' => 1];
Kikripp_DB::tabellen_anlegen();
global $wpdb;

/** Spielt eine Importdatei ein – dieselbe Logik wie die Verwaltung. */
function importiere($pfad) {
    global $wpdb;
    $liste = json_decode(file_get_contents($pfad), true);
    $gesehen = [];
    foreach ($liste as $i => $a) {
        if (empty($a['nr'])) { continue; }
        $gesehen[] = $a['nr'];
        $zeile = ['sortierung' => (int) $a['sortierung'], 'menge' => (int) $a['menge'],
                  'preis_netto' => (float) $a['preis'], 'aktiv' => !empty($a['aktiv']) ? 1 : 0,
                  'im_katalog' => !empty($a['im_katalog']) ? 1 : 0,
                  'daten' => wp_json_encode(['nr' => $a['nr'], 'titel' => $a['titel'],
                      'beschr' => $a['beschr'], 'kat' => $a['kat'], 'raum' => $a['raum'],
                      'zustand' => $a['zustand'], 'masse' => $a['masse'], 'einheit' => $a['einheit'],
                      'basis' => $a['basis'], 'versand' => $a['versand'], 'marke' => $a['marke'] ?? '',
                      'foto' => $a['foto'], 'bild' => '/fotos/' . $a['foto'] . '.jpg']),
                  'aktualisiert' => current_time('mysql')];
        if ($wpdb->get_var($wpdb->prepare('SELECT artnr FROM ' . Kikripp_DB::t_artikel()
                . ' WHERE artnr = %s', $a['nr']))) {
            $wpdb->update(Kikripp_DB::t_artikel(), $zeile, ['artnr' => $a['nr']]);
        } else {
            $zeile['artnr'] = $a['nr'];
            $wpdb->insert(Kikripp_DB::t_artikel(), $zeile);
        }
    }
    return Kikripp_DB::fehlende_stilllegen($gesehen);
}

$fehler = 0;
function pruefe($was, $ist, $soll) {
    global $fehler;
    $ok = $ist === $soll;
    if (!$ok) { $fehler++; }
    printf("  %s %-52s %s\n", $ok ? 'ok  ' : 'FEHL', $was,
        $ok ? '' : 'ist: ' . json_encode($ist) . '  soll: ' . json_encode($soll));
}
function im_katalog($nr) {
    foreach (Kikripp_DB::katalog_artikel() as $a) { if ($a['nr'] === $nr) { return $a; } }
    return null;
}

echo "\n1. Erstimport\n";
$erwartet = count(array_filter(json_decode(file_get_contents($IMPORT), true),
    function ($a) { return !empty($a['aktiv']) && !empty($a['im_katalog']); }));
importiere($IMPORT);
$katalog = Kikripp_DB::katalog_artikel();
pruefe('alle aktiven Artikel im Katalog', count($katalog), $erwartet);

// Prüfartikel aus den Daten holen, damit der Test eine Umnummerierung übersteht:
// A = ein Artikel mit Foto, B = ein zweiter.
$A = $katalog[0]['nr'];
$B = $katalog[1]['nr'];
$A_bild = $katalog[0]['bild'];
$A_preis = (float) $katalog[0]['preis'];
pruefe("$A ist sichtbar", im_katalog($A) !== null, true);
pruefe("$A hat ein Foto", $A_bild !== '', true);

echo "\n2. Jemand reserviert $A\n";
$v = Kikripp_DB::reservieren(['name' => 'Test', 'email' => 't@example.org', 'telefon' => '',
    'wunschtermin' => '', 'nachricht' => ''], [$A => 1]);
pruefe('Reservierung angelegt', is_int($v) && $v > 0, true);
pruefe("$A ist reserviert", im_katalog($A)['status'], 'reserviert');

echo "\n3. $A wird in der Datenbasis auf „entfällt\" gesetzt\n";
$daten = json_decode(file_get_contents($IMPORT), true);
foreach ($daten as &$a) { if ($a['nr'] === $A) { $a['aktiv'] = false; } } unset($a);
file_put_contents('/tmp/import-entfaellt.json', json_encode($daten));
importiere('/tmp/import-entfaellt.json');
pruefe("$A ist aus dem Katalog verschwunden", im_katalog($A), null);
pruefe('einer weniger im Katalog', count(Kikripp_DB::katalog_artikel()), $erwartet - 1);
pruefe('die Reservierung ist noch da', Kikripp_DB::vorgang($v) !== null, true);

echo "\n4. $B wird komplett aus der Datei gestrichen\n";
// Weiter auf dem Stand aus Schritt 3: $A steht dort schon auf „entfällt".
$daten = json_decode(file_get_contents('/tmp/import-entfaellt.json'), true);
$daten = array_values(array_filter($daten, function ($a) use ($B) { return $a['nr'] !== $B; }));
file_put_contents('/tmp/import-geloescht.json', json_encode($daten));
$weg = importiere('/tmp/import-geloescht.json');
pruefe("Import meldet genau $B", $weg, [$B]);
pruefe("$B ist weg", im_katalog($B), null);
pruefe("$A bleibt weg", im_katalog($A), null);
pruefe('zwei weniger im Katalog', count(Kikripp_DB::katalog_artikel()), $erwartet - 2);

echo "\n5. $A kommt zurück\n";
importiere($IMPORT);
pruefe("$A ist wieder da", im_katalog($A) !== null, true);
pruefe("$A hat wieder sein Foto", im_katalog($A)['bild'], $A_bild);
pruefe('die alte Reservierung zählt wieder', im_katalog($A)['status'], 'reserviert');
pruefe('wieder alle im Katalog', count(Kikripp_DB::katalog_artikel()), $erwartet);

echo "\n6. Preisänderung schlägt durch, friert aber nichts auf\n";
$C = $katalog[2]['nr'];
$daten = json_decode(file_get_contents($IMPORT), true);
foreach ($daten as &$a) { if ($a['nr'] === $C) { $a['preis'] = 99.0; } } unset($a);
file_put_contents('/tmp/import-preis.json', json_encode($daten));
importiere('/tmp/import-preis.json');
pruefe('neuer Preis im Katalog', im_katalog($C)['preis'], 99.0);
$pos = $wpdb->get_row($wpdb->prepare('SELECT preis_netto FROM ' . Kikripp_DB::t_position()
    . ' WHERE artnr = %s', $A), ARRAY_A);
pruefe('alte Reservierung behält ihren Preis', (float) $pos['preis_netto'], $A_preis);

printf("\n== Kettentest: %d Fehler ==\n", $fehler);
exit($fehler > 0 ? 1 : 0);
