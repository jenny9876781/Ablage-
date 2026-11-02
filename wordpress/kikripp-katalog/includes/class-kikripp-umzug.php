<?php
/**
 * 1.13.0: Umzug auf einen neuen Server.
 *
 * kikripp.de ist ein Multisite-Netzwerk; die kostenlosen Umzugs-Plugins können das nicht. Der Katalog
 * zieht deshalb allein um: Artikel und Fotos kommen wie immer über Import und Mediathek, die
 * Reservierungen und Einstellungen über diese Seite – alte Seite „Daten exportieren“, neue Seite
 * „Daten importieren“. Die Vorgangsnummern bleiben dabei erhalten (Rechnungen und Notizen verweisen
 * darauf), ebenso die NEU-Stempel der Artikel, damit nach dem Umzug nicht alles als neu erscheint.
 *
 * Bewusst ohne PHP-8-Sprachmittel: der alte Server läuft noch mit PHP 7.4.
 */
if (!defined('ABSPATH')) { exit; }

class Kikripp_Umzug {

    const FORMAT = 'kikripp-umzug';

    /** Einstellungen, die mitziehen. Versionen und Zähler bleiben Sache der jeweiligen Seite. */
    const OPTIONEN = [
        'abholadresse', 'abholschluss', 'ablauftext', 'besichtigung_ab', 'datenschutz_url', 'erinnerung_zeit',
        'firma', 'frist_werktage', 'fusszeile_aus', 'geschenke_max', 'hinweis_bis', 'hinweisband', 'impressum_url',
        'kontakt_email', 'kopf_aus', 'mail_an', 'mail_name', 'mindestwert', 'passwort_hash', 'passwortschutz',
        'rechtstext', 'rueckmeldung_ab', 'steuerhinweis', 'telefon', 'termin_zusatz', 'termine_ab', 'ust_prozent',
        'vorschau', 'zahlung_tage', 'zufahrt',
    ];

    public static function start() {
        add_action('admin_menu', [__CLASS__, 'menue'], 22);
        add_action('admin_post_kikripp_umzug_export', [__CLASS__, 'export']);
        add_action('admin_post_kikripp_umzug_import', [__CLASS__, 'import']);
    }

    public static function menue() {
        add_submenu_page('kikripp-reservierungen', 'Umzug', 'Umzug', 'manage_options',
            'kikripp-umzug', [__CLASS__, 'seite']);
    }

    // ------------------------------------------------------------ Daten

    /** Alles, was umziehen muss, als Array – der Download ist nur dessen JSON. */
    public static function export_daten() {
        global $wpdb;
        $optionen = [];
        foreach (self::OPTIONEN as $name) {
            $wert = get_option('kikripp_' . $name, null);
            if ($wert !== null) { $optionen[$name] = $wert; }
        }
        $neu = [];
        foreach ((array) $wpdb->get_results('SELECT artnr, daten FROM ' . Kikripp_DB::t_artikel(), ARRAY_A) as $a) {
            $d = json_decode((string) $a['daten'], true);
            if (is_array($d) && !empty($d['neu_seit'])) { $neu[$a['artnr']] = $d['neu_seit']; }
        }
        return [
            'format'     => self::FORMAT,
            'version'    => 1,
            'plugin'     => KIKRIPP_VERSION,
            'schema'     => Kikripp_DB::SCHEMA_VERSION,
            'erstellt'   => current_time('mysql'),
            'optionen'   => $optionen,
            'vorgaenge'  => (array) $wpdb->get_results('SELECT * FROM ' . Kikripp_DB::t_vorgang() . ' ORDER BY id', ARRAY_A),
            'positionen' => (array) $wpdb->get_results('SELECT * FROM ' . Kikripp_DB::t_position() . ' ORDER BY id', ARRAY_A),
            'neu_seit'   => $neu,
        ];
    }

    /**
     * Daten einspielen. Ersetzt alle Vorgänge und Positionen dieser Seite – nur mit $ersetzen, wenn schon
     * welche da sind. Gibt einen Bericht zurück oder WP_Error.
     */
    public static function import_daten($d, $ersetzen = false) {
        global $wpdb;
        if (!is_array($d) || ($d['format'] ?? '') !== self::FORMAT) {
            return new WP_Error('format', 'Das ist keine Umzugsdatei des Artikelkatalogs.');
        }
        if ((int) ($d['schema'] ?? 0) !== Kikripp_DB::SCHEMA_VERSION) {
            return new WP_Error('schema', 'Die Datei stammt von einer anderen Plugin-Version. Bitte auf beiden Seiten '
                . 'dieselbe Version des Artikelkatalogs installieren und neu exportieren.');
        }
        $vorhanden = (int) $wpdb->get_var('SELECT COUNT(*) FROM ' . Kikripp_DB::t_vorgang());
        if ($vorhanden > 0 && !$ersetzen) {
            return new WP_Error('vorhanden', sprintf('Auf dieser Seite gibt es schon %d Reservierungen. Zum Ersetzen '
                . 'bitte das Häkchen „vorhandene Reservierungen ersetzen“ setzen.', $vorhanden));
        }
        $wpdb->query('DELETE FROM ' . Kikripp_DB::t_position());
        $wpdb->query('DELETE FROM ' . Kikripp_DB::t_vorgang());
        $v = 0; $p = 0;
        foreach ((array) ($d['vorgaenge'] ?? []) as $zeile) {
            if (is_array($zeile) && $wpdb->insert(Kikripp_DB::t_vorgang(), $zeile) !== false) { $v++; }
        }
        foreach ((array) ($d['positionen'] ?? []) as $zeile) {
            if (is_array($zeile) && $wpdb->insert(Kikripp_DB::t_position(), $zeile) !== false) { $p++; }
        }
        $o = 0;
        foreach ((array) ($d['optionen'] ?? []) as $name => $wert) {
            if (in_array($name, self::OPTIONEN, true)) { update_option('kikripp_' . $name, $wert); $o++; }
        }
        // NEU-Stempel auf die bereits importierten Artikel übertragen
        $stempel = (array) ($d['neu_seit'] ?? []);
        $n = 0;
        $artikel = (array) $wpdb->get_results('SELECT artnr, daten FROM ' . Kikripp_DB::t_artikel(), ARRAY_A);
        foreach ($artikel as $a) {
            $daten = json_decode((string) $a['daten'], true);
            if (!is_array($daten)) { $daten = []; }
            $soll = isset($stempel[$a['artnr']]) ? (string) $stempel[$a['artnr']] : '';
            if ((string) ($daten['neu_seit'] ?? '') === $soll) { continue; }
            if ($soll === '') { unset($daten['neu_seit']); } else { $daten['neu_seit'] = $soll; }
            $wpdb->update(Kikripp_DB::t_artikel(), ['daten' => wp_json_encode($daten)], ['artnr' => $a['artnr']]);
            $n++;
        }
        return [
            'vorgaenge' => $v, 'vorgaenge_soll' => count((array) ($d['vorgaenge'] ?? [])),
            'positionen' => $p, 'positionen_soll' => count((array) ($d['positionen'] ?? [])),
            'optionen' => $o, 'stempel' => $n, 'artikel' => count($artikel),
        ];
    }

    // ------------------------------------------------------------ Seite und Aktionen

    public static function seite() {
        if (!current_user_can('manage_options')) { return; }
        global $wpdb;
        $v = (int) $wpdb->get_var('SELECT COUNT(*) FROM ' . Kikripp_DB::t_vorgang());
        $a = (int) $wpdb->get_var('SELECT COUNT(*) FROM ' . Kikripp_DB::t_artikel());
        echo '<div class="wrap"><h1>Umzug auf einen neuen Server</h1>';
        if (isset($_GET['kikripp_meldung'])) {
            printf('<div class="notice notice-%s"><p>%s</p></div>', isset($_GET['kikripp_fehler']) ? 'error' : 'success',
                esc_html(wp_unslash($_GET['kikripp_meldung'])));
        }
        printf('<p>Auf dieser Seite: <strong>%d Reservierungen</strong>, <strong>%d Artikel</strong>.</p>', $v, $a);

        echo '<h2>1. Auf der alten Seite: Daten exportieren</h2>'
           . '<p>Lädt alle Reservierungen, die Einstellungen und die NEU-Schilder als eine Datei herunter. '
           . 'Artikel und Fotos sind nicht dabei – die kommen auf der neuen Seite wie gewohnt über „Artikel importieren“ '
           . 'und die Mediathek.</p>'
           . '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">'
           . wp_nonce_field('kikripp_umzug_export', '_wpnonce', true, false)
           . '<input type="hidden" name="action" value="kikripp_umzug_export">'
           . '<button class="button button-primary">Daten exportieren</button></form>';

        echo '<h2>2. Auf der neuen Seite: Daten importieren</h2>'
           . '<p><strong>Reihenfolge:</strong> zuerst die Fotos in die Mediathek, dann „Artikel importieren“, '
           . 'dann hier die Umzugsdatei.</p>'
           . ($a === 0 ? '<p style="color:#b32d2e"><strong>Auf dieser Seite sind noch keine Artikel importiert.</strong> '
                . 'Bitte zuerst „Artikel importieren“.</p>' : '')
           . '<form method="post" enctype="multipart/form-data" action="' . esc_url(admin_url('admin-post.php')) . '">'
           . wp_nonce_field('kikripp_umzug_import', '_wpnonce', true, false)
           . '<input type="hidden" name="action" value="kikripp_umzug_import">'
           . '<p><input type="file" name="datei" accept=".json,application/json" required></p>'
           . ($v > 0 ? '<p><label><input type="checkbox" name="ersetzen" value="1"> vorhandene Reservierungen ersetzen ('
                . $v . ' Stück)</label></p>' : '')
           . '<button class="button button-primary">Daten importieren</button></form></div>';
    }

    public static function export() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_umzug_export');
        nocache_headers();
        header('Content-Type: application/json; charset=utf-8');
        header('Content-Disposition: attachment; filename=kikripp-umzug-' . gmdate('Ymd-His') . '.json');
        echo wp_json_encode(self::export_daten(), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
        exit;
    }

    public static function import() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_umzug_import');
        $datei = $_FILES['datei']['tmp_name'] ?? '';
        $d = ($datei !== '' && is_uploaded_file($datei)) ? json_decode((string) file_get_contents($datei), true) : null;
        $b = self::import_daten($d, !empty($_POST['ersetzen']));
        $ziel = admin_url('admin.php?page=kikripp-umzug');
        if (is_wp_error($b)) {
            wp_safe_redirect(add_query_arg(['kikripp_meldung' => rawurlencode($b->get_error_message()), 'kikripp_fehler' => 1], $ziel));
            exit;
        }
        $text = sprintf('Umzug eingespielt: %d von %d Reservierungen, %d von %d Positionen, %d Einstellungen, '
            . '%d NEU-Schilder übernommen (%d Artikel auf dieser Seite).',
            $b['vorgaenge'], $b['vorgaenge_soll'], $b['positionen'], $b['positionen_soll'], $b['optionen'], $b['stempel'], $b['artikel']);
        wp_safe_redirect(add_query_arg(['kikripp_meldung' => rawurlencode($text)], $ziel));
        exit;
    }
}
