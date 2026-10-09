<?php
if (!defined('ABSPATH')) { exit; }

/**
 * Auswertung (1.4.0): sieben Auswertungen über einen wählbaren Zeitraum, jede als Tabelle
 * und als Excel-taugliche CSV-Datei (Strichpunkt, BOM, deutsche Zahlen).
 *
 * Grundlage ist nur, was über den Webkatalog lief. Telefon- oder Vor-Ort-Verkäufe ohne Vorgang
 * stehen ausschließlich in der Excel-Artikelliste. Testdaten zählen außerhalb der Vorschau nicht.
 * Namen erscheinen nur dort, wo Buchhaltung und Abwicklung sie brauchen (Verkaufsliste, offene
 * Posten, Abholungen); sind die Kontaktdaten gelöscht, steht die Vorgangsnummer.
 */
class Kikripp_Auswertung {

    const ARTEN = [
        'verkauf'    => '1. Verkaufsliste für den Steuerberater',
        'umsatz'     => '2. Umsatz nach Monat und Woche',
        'kategorie'  => '3a. Nach Kategorie',
        'raum'       => '3b. Nach Raum',
        'ladenhueter'=> '4. Ladenhüter – noch nie reserviert',
        'offen'      => '5. Offene Posten',
        'abholungen' => '6. Abholungen',
        'kennzahlen' => '7. Kennzahlen',
    ];
    const ERSTER_TAG = '2026-09-01';

    public static function start() {
        add_action('admin_menu', [__CLASS__, 'menue'], 21);
        add_action('admin_post_kikripp_auswertung', [__CLASS__, 'export']);
    }

    public static function menue() {
        add_submenu_page('kikripp-reservierungen', 'Auswertung', 'Auswertung', 'manage_options',
            'kikripp-auswertung', [__CLASS__, 'seite']);
    }

    // ------------------------------------------------------------ Daten

    private static function vorgaenge() {
        $vorschau = (bool) get_option('kikripp_vorschau', 1);
        return array_values(array_filter(Kikripp_DB::vorgaenge(), function ($v) use ($vorschau) {
            return $vorschau || empty($v['testdaten']);
        }));
    }

    private static function artikel() {
        global $wpdb;
        $out = [];
        foreach ((array) $wpdb->get_results('SELECT * FROM ' . Kikripp_DB::t_artikel() . ' WHERE aktiv = 1 ORDER BY sortierung, artnr', ARRAY_A) as $z) {
            $d = json_decode((string) $z['daten'], true);
            $d = is_array($d) ? $d : [];
            $out[$z['artnr']] = ['artnr' => $z['artnr'], 'menge' => (int) $z['menge'], 'preis' => (float) $z['preis_netto'],
                'im_katalog' => (int) $z['im_katalog'], 'titel' => (string) ($d['titel'] ?? ''), 'kat' => (string) ($d['kat'] ?? '') ?: 'ohne Kategorie',
                'raum' => (string) ($d['raum'] ?? '') ?: 'ohne Raum', 'einheit' => (string) ($d['einheit'] ?? 'Stück')];
        }
        return $out;
    }

    private static function kaeufer($v) {
        return trim((string) $v['name']) === '' && trim((string) ($v['firma'] ?? '')) === ''
            ? 'Vorgang #' . (int) $v['id'] : Kikripp_Ablauf::wer($v);
    }

    private static function im_zeitraum($datum, $von, $bis) {
        $t = substr((string) $datum, 0, 10);
        return $t !== '' && $t >= $von && $t <= $bis;
    }

    private static function d($ymd) { return Kikripp_Ablauf::datum_text($ymd); }

    /**
     * Eine Auswertung: ['spalten' => [...], 'zeilen' => [[...]], 'summe' => [...]|null, 'geld' => [Spaltenindizes]]
     */
    public static function daten($art, $von, $bis) {
        $heute = Kikripp_Ablauf::heute();
        switch ($art) {
            case 'verkauf':
                $zeilen = []; $summe = 0.0; $stueck = 0;
                foreach (self::vorgaenge() as $v) {
                    foreach ($v['positionen'] as $p) {
                        if ($p['status'] !== 'bezahlt' || !self::im_zeitraum($p['bezahlt_am'] ?? '', $von, $bis)) { continue; }
                        $d = json_decode((string) ($p['daten'] ?? ''), true); $d = is_array($d) ? $d : [];
                        $betrag = (float) $p['preis_netto'] * (int) $p['menge'];
                        $summe += $betrag; $stueck += (int) $p['menge'];
                        $zeilen[] = [self::d($p['bezahlt_am']), $v['rechnungsnr'] ?? '', self::d($v['rechnung_am'] ?? ''), '#' . (int) $v['id'],
                            self::kaeufer($v), Kikripp_Ablauf::privat($v) ? 'Privat' : 'Firma', $p['artnr'], (string) ($d['titel'] ?? ''),
                            (string) ($d['kat'] ?? ''), (int) $p['menge'], (float) $p['preis_netto'], $betrag, self::d($v['abgeholt_am'] ?? '')];
                    }
                }
                usort($zeilen, function ($a, $b) { return [implode('', array_reverse(explode('.', $a[0]))), $a[3]] <=> [implode('', array_reverse(explode('.', $b[0]))), $b[3]]; });
                return ['spalten' => ['Bezahlt am', 'Rechnungsnr.', 'Rechnung vom', 'Vorgang', 'Käufer', 'Privat/Firma', 'Art.-Nr.',
                        'Bezeichnung', 'Kategorie', 'Menge', 'Einzelpreis', 'Betrag', 'Abgeholt am'],
                        'zeilen' => $zeilen, 'geld' => [10, 11],
                        'summe' => ['Summe', '', '', '', '', '', '', '', '', $stueck, '', $summe, '']];

            case 'umsatz':
                $monat = []; $woche = [];
                foreach (self::vorgaenge() as $v) {
                    foreach ($v['positionen'] as $p) {
                        if ($p['status'] !== 'bezahlt' || !self::im_zeitraum($p['bezahlt_am'] ?? '', $von, $bis)) { continue; }
                        $t = strtotime(substr($p['bezahlt_am'], 0, 10) . ' 12:00:00 UTC');
                        $betrag = (float) $p['preis_netto'] * (int) $p['menge'];
                        foreach ([[&$monat, gmdate('Y-m', $t)], [&$woche, gmdate('o-W', $t)]] as $ziel) {
                            $k = $ziel[1];
                            if (!isset($ziel[0][$k])) { $ziel[0][$k] = ['v' => [], 's' => 0, 'e' => 0.0]; }
                            $ziel[0][$k]['v'][$v['id']] = 1; $ziel[0][$k]['s'] += (int) $p['menge']; $ziel[0][$k]['e'] += $betrag;
                        }
                    }
                }
                ksort($monat); ksort($woche);
                $mn = ['', 'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'];
                $zeilen = []; $ges = ['v' => 0, 's' => 0, 'e' => 0.0];
                foreach ($monat as $k => $w) {
                    $zeilen[] = ['Monat', $mn[(int) substr($k, 5)] . ' ' . substr($k, 0, 4), count($w['v']), $w['s'], $w['e']];
                    $ges['v'] += count($w['v']); $ges['s'] += $w['s']; $ges['e'] += $w['e'];
                }
                foreach ($woche as $k => $w) {
                    list($j, $kw) = explode('-', $k);
                    $mo = new DateTime(); $mo->setISODate((int) $j, (int) $kw);
                    $so = clone $mo; $so->modify('+6 days');
                    $zeilen[] = ['Woche', 'KW ' . (int) $kw . ' (' . $mo->format('d.m.') . '–' . $so->format('d.m.Y') . ')', count($w['v']), $w['s'], $w['e']];
                }
                return ['spalten' => ['Art', 'Zeitraum', 'Vorgänge', 'Stück', 'Umsatz'], 'zeilen' => $zeilen, 'geld' => [4],
                        'summe' => ['Summe', '', $ges['v'], $ges['s'], $ges['e']]];

            case 'kategorie':
            case 'raum':
                $feld = $art === 'kategorie' ? 'kat' : 'raum';
                $artikel = self::artikel();
                $belegung = Kikripp_DB::belegung();
                $erloes = [];
                foreach (self::vorgaenge() as $v) {
                    foreach ($v['positionen'] as $p) {
                        if ($p['status'] === 'bezahlt') { $erloes[$p['artnr']] = ($erloes[$p['artnr']] ?? 0) + (float) $p['preis_netto'] * (int) $p['menge']; }
                    }
                }
                $g = [];
                foreach ($artikel as $a) {
                    $k = $a[$feld];
                    $b = $belegung[$a['artnr']] ?? ['bezahlt' => 0, 'reserviert' => 0];
                    $uebrig = max(0, $a['menge'] - $b['bezahlt'] - $b['reserviert']);
                    if (!isset($g[$k])) { $g[$k] = [$k, 0, 0, 0, 0.0, 0, 0, 0.0]; }
                    $g[$k][1]++; $g[$k][2] += $a['menge']; $g[$k][3] += $b['bezahlt']; $g[$k][4] += $erloes[$a['artnr']] ?? 0;
                    $g[$k][5] += $b['reserviert']; $g[$k][6] += $uebrig; $g[$k][7] += $uebrig * $a['preis'];
                }
                usort($g, function ($a, $b) { return $b[4] <=> $a[4] ?: $b[7] <=> $a[7]; });
                $summe = ['Summe', 0, 0, 0, 0.0, 0, 0, 0.0];
                foreach ($g as $z) { for ($i = 1; $i < 8; $i++) { $summe[$i] += $z[$i]; } }
                return ['spalten' => [$art === 'kategorie' ? 'Kategorie' : 'Raum', 'Artikel', 'Stück gesamt', 'verkauft Stück', 'verkauft €',
                        'reserviert Stück', 'übrig Stück', 'Restwert €'], 'zeilen' => array_values($g), 'geld' => [4, 7], 'summe' => $summe,
                        'hinweis' => 'Stand heute, unabhängig vom Zeitraum.'];

            case 'ladenhueter':
                global $wpdb;
                $je = $wpdb->get_col('SELECT DISTINCT artnr FROM ' . Kikripp_DB::t_position());
                $nie = array_flip((array) $je);
                $zeilen = []; $summe = 0.0;
                foreach (self::artikel() as $a) {
                    if (!$a['im_katalog'] || isset($nie[$a['artnr']]) || $a['menge'] < 1) { continue; }
                    $wert = $a['menge'] * $a['preis'];
                    $summe += $wert;
                    $zeilen[] = [$a['artnr'], $a['titel'], $a['kat'], $a['raum'], $a['menge'] . ' ' . $a['einheit'], $a['preis'], $wert];
                }
                usort($zeilen, function ($a, $b) { return $b[6] <=> $a[6]; });
                return ['spalten' => ['Art.-Nr.', 'Bezeichnung', 'Kategorie', 'Raum', 'Menge', 'Preis', 'Wert'], 'zeilen' => $zeilen,
                        'geld' => [5, 6], 'summe' => ['Summe', count($zeilen) . ' Artikel', '', '', '', '', $summe],
                        'hinweis' => 'Stand heute: Artikel im Katalog, für die es noch nie eine Reservierung gab – Kandidaten für eine Preissenkung.'];

            case 'offen':
                $zeilen = []; $summe = 0.0;
                foreach (self::vorgaenge() as $v) {
                    if ($v['status'] !== 'bestellt') { continue; }
                    $betrag = Kikripp_Ablauf::summe($v); $summe += $betrag;
                    $tage = ($v['rechnung_am'] ?? '') !== '' ? Kikripp_Ablauf::tage_zwischen($v['rechnung_am'], $heute) : '';
                    $zeilen[] = [$v['rechnungsnr'] ?: '(noch keine)', self::d($v['rechnung_am'] ?? ''), $tage, '#' . (int) $v['id'],
                        self::kaeufer($v), $betrag, Kikripp_Ablauf::termin_text($v['abholung'] ?? '', true)];
                }
                usort($zeilen, function ($a, $b) { return (int) $b[2] <=> (int) $a[2]; });
                return ['spalten' => ['Rechnungsnr.', 'Rechnung vom', 'Tage offen', 'Vorgang', 'Käufer', 'Betrag', 'Abholung'],
                        'zeilen' => $zeilen, 'geld' => [5], 'summe' => ['Summe', '', '', count($zeilen) . ' Vorgänge', '', $summe, ''],
                        'hinweis' => 'Stand heute: bestellt, aber noch nicht bezahlt.'];

            case 'abholungen':
                $zeilen = [];
                foreach (self::vorgaenge() as $v) {
                    if (!in_array($v['status'], ['bestellt', 'bezahlt'], true) || !self::im_zeitraum($v['abholung'] ?? '', $von, $bis)) { continue; }
                    $pos = Kikripp_Ablauf::positionen($v);
                    $t = strtotime(substr($v['abholung'], 0, 10) . ' 12:00:00 UTC');
                    $zeilen[] = [self::d($v['abholung']), Kikripp_Ablauf::WOCHENTAGE[(int) gmdate('N', $t)], substr($v['abholung'], 11, 5),
                        '#' . (int) $v['id'], self::kaeufer($v),
                        implode(', ', array_map(function ($p) { return $p['menge'] . '× ' . $p['artnr']; }, $pos)),
                        array_sum(array_column($pos, 'menge')), Kikripp_Ablauf::summe($v), $v['status'] === 'bezahlt' ? 'ja' : 'nein',
                        self::d($v['abgeholt_am'] ?? ''), !empty($v['demontage']) ? 'ja' : '', Kikripp_Ablauf::termin_betreff($v)[0]];
                }
                usort($zeilen, function ($a, $b) {
                    return [implode('', array_reverse(explode('.', $a[0]))), $a[2]] <=> [implode('', array_reverse(explode('.', $b[0]))), $b[2]];
                });
                return ['spalten' => ['Datum', 'Wochentag', 'Uhrzeit', 'Vorgang', 'Käufer', 'Artikel', 'Stück', 'Betrag', 'bezahlt',
                        'abgeholt am', 'Demontage', 'Betreff im Kalender'], 'zeilen' => $zeilen, 'geld' => [7],
                        'summe' => ['Summe', count($zeilen) . ' Abholungen', '', '', '', '', array_sum(array_column($zeilen, 6)),
                                    array_sum(array_column($zeilen, 7)), '', '', '', '']];

            case 'kennzahlen':
                $alle = self::vorgaenge();
                $im = array_filter($alle, function ($v) use ($von, $bis) { return self::im_zeitraum($v['erstellt'], $von, $bis); });
                $jetzt = current_time('timestamp');
                $n = ['gesamt' => count($im), 'weiter' => 0, 'bezahlt' => 0, 'storniert' => 0, 'abgelaufen' => 0, 'laufend' => 0];
                $privat = 0; $firma = 0; $werte = [];
                foreach ($im as $v) {
                    if ($v['status'] === 'storniert') { $n['storniert']++; continue; }
                    if ($v['status'] === 'offen') { strtotime($v['ablauf']) < $jetzt ? $n['abgelaufen']++ : $n['laufend']++; continue; }
                    $n['weiter']++;
                    if ($v['status'] === 'bezahlt') {
                        $n['bezahlt']++; $werte[] = Kikripp_Ablauf::summe($v);
                        Kikripp_Ablauf::privat($v) ? $privat++ : $firma++;
                    }
                }
                $pz = function ($x) use ($n) { return $n['gesamt'] ? round(100 * $x / $n['gesamt']) . ' %' : '–'; };
                $umsatz = self::daten('verkauf', $von, $bis)['summe'][11];
                $rest = self::daten('kategorie', $von, $bis)['summe'];
                $zeilen = [
                    ['Reservierungen im Zeitraum', $n['gesamt'], ''],
                    ['davon bestellt oder weiter', $n['weiter'], $pz($n['weiter'])],
                    ['davon bezahlt', $n['bezahlt'], $pz($n['bezahlt'])],
                    ['davon storniert', $n['storniert'], $pz($n['storniert'])],
                    ['davon abgelaufen ohne Rückmeldung', $n['abgelaufen'], $pz($n['abgelaufen'])],
                    ['davon noch reserviert', $n['laufend'], $pz($n['laufend'])],
                    ['Umsatz bezahlt im Zeitraum', $umsatz, ''],
                    ['Ø Bestellwert (bezahlte Vorgänge)', $werte ? array_sum($werte) / count($werte) : 0.0, ''],
                    ['bezahlte Vorgänge Privat / Firma', "$privat / $firma", ($privat + $firma) ? round(100 * $privat / ($privat + $firma)) . ' % privat' : ''],
                    ['noch übrig (Stück, Stand heute)', $rest[6], ''],
                    ['Restwert im Katalog (Stand heute)', $rest[7], ''],
                ];
                return ['spalten' => ['Kennzahl', 'Wert', 'Anteil'], 'zeilen' => $zeilen, 'geld_zeilen' => [6, 7, 10], 'summe' => null];
        }
        return ['spalten' => [], 'zeilen' => [], 'summe' => null];
    }

    // ------------------------------------------------------------ Ausgabe

    private static function zelle($wert, $geld) {
        if ($geld && (is_float($wert) || is_int($wert))) { return Kikripp_Mail::eur($wert); }
        if (is_float($wert)) { return number_format($wert, 2, ',', '.'); }
        return (string) $wert;
    }

    private static function ist_geld($daten, $zeile_nr, $spalte) {
        return in_array($spalte, $daten['geld'] ?? [], true)
            || ($spalte === 1 && in_array($zeile_nr, $daten['geld_zeilen'] ?? [], true));
    }

    public static function zeitraum() {
        $von = sanitize_text_field(wp_unslash($_GET['von'] ?? ''));
        $bis = sanitize_text_field(wp_unslash($_GET['bis'] ?? ''));
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $von)) { $von = self::ERSTER_TAG; }
        // Standard bis Jahresende: sonst fehlen geplante Abholungen, die noch in der Zukunft liegen.
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $bis)) { $bis = max(Kikripp_Ablauf::heute(), substr(Kikripp_Ablauf::heute(), 0, 4) . '-12-31'); }
        return $von <= $bis ? [$von, $bis] : [$bis, $von];
    }

    public static function seite() {
        if (!current_user_can('manage_options')) { return; }
        list($von, $bis) = self::zeitraum();
        echo '<div class="wrap"><h1>Auswertung</h1>';
        echo '<form method="get" style="background:#fff;border:1px solid #c3c4c7;padding:8px 12px;display:inline-block;margin:6px 0 12px">'
           . '<input type="hidden" name="page" value="kikripp-auswertung">Zeitraum von <input type="date" name="von" value="' . esc_attr($von) . '"> '
           . 'bis <input type="date" name="bis" value="' . esc_attr($bis) . '"> <button class="button button-primary">Anzeigen</button></form>';
        echo '<p style="color:#646970;max-width:900px;margin-top:0">Ausgewertet wird, was über den Webkatalog lief. Verkäufe ohne Vorgang in '
           . 'WordPress (Telefon, vor Ort) stehen nur in der Excel-Artikelliste. Jede Auswertung lässt sich als Excel-Datei herunterladen.</p>';
        foreach (self::ARTEN as $art => $titel) {
            $daten = self::daten($art, $von, $bis);
            $export = wp_nonce_url(admin_url('admin-post.php?action=kikripp_auswertung&art=' . $art . '&von=' . $von . '&bis=' . $bis), 'kikripp_auswertung');
            echo '<h2 style="margin:22px 0 6px;display:flex;gap:12px;align-items:center">' . esc_html($titel)
               . ' <a class="button button-small" href="' . esc_url($export) . '">Als Excel-Datei exportieren</a></h2>';
            if (!empty($daten['hinweis'])) { echo '<p style="color:#646970;margin:0 0 6px">' . esc_html($daten['hinweis']) . '</p>'; }
            if (!$daten['zeilen']) { echo '<p style="color:#646970">Keine Daten.</p>'; continue; }
            $max = 25;
            echo '<table class="widefat striped" style="max-width:1300px"><thead><tr>';
            foreach ($daten['spalten'] as $sp) { echo '<th>' . esc_html($sp) . '</th>'; }
            echo '</tr></thead><tbody>';
            foreach (array_slice($daten['zeilen'], 0, $max) as $nr => $z) {
                echo '<tr>';
                foreach ($z as $i => $w) { echo '<td>' . esc_html(self::zelle($w, self::ist_geld($daten, $nr, $i))) . '</td>'; }
                echo '</tr>';
            }
            if (count($daten['zeilen']) > $max) {
                echo '<tr><td colspan="' . count($daten['spalten']) . '" style="color:#646970">… und ' . (count($daten['zeilen']) - $max)
                   . ' weitere Zeilen – vollständig in der Excel-Datei.</td></tr>';
            }
            if ($daten['summe']) {
                echo '<tr style="font-weight:600;background:#f0f0f1">';
                foreach ($daten['summe'] as $i => $w) { echo '<td>' . esc_html(self::zelle($w, in_array($i, $daten['geld'] ?? [], true))) . '</td>'; }
                echo '</tr>';
            }
            echo '</tbody></table>';
        }
        echo '</div>';
    }

    /** CSV-Inhalt einer Auswertung (ohne Header), für Excel: BOM, Strichpunkt, Komma als Dezimaltrenner. */
    public static function csv($art, $von, $bis) {
        $daten = self::daten($art, $von, $bis);
        $f = fopen('php://temp', 'w+');
        fwrite($f, "\xEF\xBB\xBF");
        fputcsv($f, [self::ARTEN[$art] ?? $art, 'Zeitraum ' . self::d($von) . ' – ' . self::d($bis)], ';');
        fputcsv($f, $daten['spalten'], ';');
        foreach ($daten['zeilen'] as $z) {
            fputcsv($f, array_map(function ($w) { return is_float($w) ? number_format($w, 2, ',', '') : $w; }, $z), ';');
        }
        if ($daten['summe']) {
            fputcsv($f, array_map(function ($w) { return is_float($w) ? number_format($w, 2, ',', '') : $w; }, $daten['summe']), ';');
        }
        rewind($f);
        $inhalt = stream_get_contents($f);
        fclose($f);
        return $inhalt;
    }

    public static function export() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_auswertung');
        $art = sanitize_key($_GET['art'] ?? '');
        if (!isset(self::ARTEN[$art])) { wp_die('Unbekannte Auswertung.'); }
        list($von, $bis) = self::zeitraum();
        nocache_headers();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename=kikripp-' . $art . '-' . $von . '-bis-' . $bis . '.csv');
        echo self::csv($art, $von, $bis);
        exit;
    }
}
