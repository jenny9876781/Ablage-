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

// -----------------------------------------------------------------------------
// Mediathek-Attrappe. Der Import sucht die Fotos ueber den Dateinamen. Damit der
// Test denselben Weg geht wie WordPress spaeter, bauen wir eine Mediathek aus den
// echten Fotonamen - einschliesslich der beiden Faelle, die in der Praxis stolpern
// lassen: ein Bild zweimal hochgeladen (F-xxx-1.jpg) und ein fehlendes Bild.
// -----------------------------------------------------------------------------
$GLOBALS['mediathek'] = [];        // ID => Pfad in uploads
function mediathek_fuellen(array $dateinamen) {
    $GLOBALS['mediathek'] = [];
    $id = 1000;
    foreach ($dateinamen as $d) { $GLOBALS['mediathek'][$id++] = '2026/09/' . $d; }
}
function get_posts($args) {
    $out = [];
    foreach (array_keys($GLOBALS['mediathek']) as $id) { $out[] = (object) ['ID' => $id]; }
    return $out;
}
function get_post_meta($id, $schluessel, $einzeln = false) {
    return $GLOBALS['mediathek'][$id] ?? '';
}
function wp_get_attachment_url($id) {
    return 'https://www.kikripp.de/wp-content/uploads/' . ($GLOBALS['mediathek'][$id] ?? '');
}
function check_admin_referer($a) { return true; }
function wp_die($t) { throw new RuntimeException($t); }

require $b . 'includes/class-kikripp-admin.php';

/** Spielt eine Importdatei ein - ueber genau den Code, der auch in WordPress laeuft. */
function importiere($pfad) {
    $bericht = Kikripp_Admin::einspielen(json_decode(file_get_contents($pfad), true));
    return $bericht['verschwunden'];
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
$alle = json_decode(file_get_contents($IMPORT), true);
$erwartet = count(array_filter($alle,
    function ($a) { return !empty($a['aktiv']) && !empty($a['im_katalog']); }));

// Mediathek so fuellen, wie sie nach dem Hochladen aussieht: jedes Foto einmal.
$fotos = array_values(array_unique(array_filter(array_column($alle, 'foto'))));
mediathek_fuellen(array_map(function ($f) { return $f . '.jpg'; }, $fotos));

$bericht = Kikripp_Admin::einspielen($alle);
pruefe('Import meldet alle Artikel als neu', $bericht['neu'], count($alle));
pruefe('kein Artikel ohne Foto', $bericht['ohne_bild'], 0);
pruefe('keine fehlenden Bilder gemeldet', $bericht['fehlende_fotos'], []);
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

echo "\n7. Fotos: doppelt hochgeladen, fehlend, Gross- und Kleinschreibung\n";
// WordPress haengt beim zweiten Hochladen ein "-1" an. Der Import muss das Bild
// trotzdem finden, sonst stehen nach einem zweiten Upload alle Artikel ohne Foto da.
mediathek_fuellen(array_map(function ($f) { return $f . '-1.jpg'; }, $fotos));
$bericht = Kikripp_Admin::einspielen($alle);
pruefe('zweifach hochgeladene Fotos werden gefunden', $bericht['ohne_bild'], 0);

// Grossbuchstaben in der Dateiendung sind bei Fotos vom Telefon ueblich.
mediathek_fuellen(array_map(function ($f) { return strtolower($f) . '.JPG'; }, $fotos));
$bericht = Kikripp_Admin::einspielen($alle);
pruefe('Kleinschreibung und .JPG stoeren nicht', $bericht['ohne_bild'], 0);

// Fehlt ein Foto, muss der Import es beim Namen nennen - sonst sucht die Nutzerin blind.
$ohne = array_slice($fotos, 1);
mediathek_fuellen(array_map(function ($f) { return $f . '.jpg'; }, $ohne));
$bericht = Kikripp_Admin::einspielen($alle);
$fehlt_erwartet = count(array_filter($alle, function ($a) use ($fotos) {
    return ($a['foto'] ?? '') === $fotos[0]; }));
pruefe('fehlendes Foto wird gezaehlt', $bericht['ohne_bild'], $fehlt_erwartet);
pruefe('fehlendes Foto wird beim Namen genannt', $bericht['fehlende_fotos'], [$fotos[0]]);
pruefe('die Meldung nennt die Mediathek',
       strpos(Kikripp_Admin::import_meldung($bericht), 'fehlen in der Mediathek') !== false, true);

// Zum Schluss wieder vollstaendig, damit nichts ohne Bild zurueckbleibt.
mediathek_fuellen(array_map(function ($f) { return $f . '.jpg'; }, $fotos));
Kikripp_Admin::einspielen($alle);
pruefe('am Ende hat jeder sichtbare Artikel ein Bild',
       count(array_filter(Kikripp_DB::katalog_artikel(),
             function ($a) { return ($a['bild'] ?? '') === ''; })), 0);

printf("\n== Kettentest: %d Fehler ==\n", $fehler);
exit($fehler > 0 ? 1 : 0);
