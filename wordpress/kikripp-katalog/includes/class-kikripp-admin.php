<?php
if (!defined('ABSPATH')) { exit; }

/** Verwaltung im WordPress-Backend: Reservierungen, Import, Einstellungen. */
class Kikripp_Admin {

    public static function start() {
        add_action('admin_menu', [__CLASS__, 'menue']);
        add_action('admin_post_kikripp_aktion', [__CLASS__, 'aktion']);
        add_action('admin_post_kikripp_import', [__CLASS__, 'import']);
        add_action('admin_post_kikripp_einstellungen', [__CLASS__, 'einstellungen_speichern']);
        add_action('admin_post_kikripp_export', [__CLASS__, 'export']);
        add_action('admin_notices', [__CLASS__, 'hinweis_passwort']);
    }

    /** Ohne Passwort bleibt der Katalog für alle zu – das muss auffallen. */
    public static function hinweis_passwort() {
        if (!current_user_can('manage_options')) { return; }
        if (get_option('kikripp_passwort_hash')) { return; }
        printf('<div class="notice notice-warning"><p><strong>Artikelkatalog:</strong> '
             . 'Es ist noch kein Passwort vergeben – der Katalog ist deshalb für alle gesperrt. '
             . '<a href="%s">Jetzt Passwort festlegen</a></p></div>',
             esc_url(admin_url('admin.php?page=kikripp-einstellungen')));
    }

    public static function menue() {
        add_menu_page('Artikelkatalog', 'Artikelkatalog', 'manage_options',
            'kikripp-reservierungen', [__CLASS__, 'seite_reservierungen'], 'dashicons-cart', 26);
        add_submenu_page('kikripp-reservierungen', 'Reservierungen', 'Reservierungen',
            'manage_options', 'kikripp-reservierungen', [__CLASS__, 'seite_reservierungen']);
        add_submenu_page('kikripp-reservierungen', 'Artikel importieren', 'Artikel importieren',
            'manage_options', 'kikripp-import', [__CLASS__, 'seite_import']);
        add_submenu_page('kikripp-reservierungen', 'Einstellungen', 'Einstellungen',
            'manage_options', 'kikripp-einstellungen', [__CLASS__, 'seite_einstellungen']);
    }

    private static function hinweis() {
        if (isset($_GET['kikripp_meldung'])) {
            $art = isset($_GET['kikripp_fehler']) ? 'error' : 'success';
            printf('<div class="notice notice-%s is-dismissible"><p>%s</p></div>',
                esc_attr($art), esc_html(wp_unslash($_GET['kikripp_meldung'])));
        }
    }

    private static function zurueck($seite, $meldung, $fehler = false) {
        $url = add_query_arg(array_filter([
            'page' => $seite,
            'kikripp_meldung' => $meldung,
            'kikripp_fehler' => $fehler ? '1' : null,
        ]), admin_url('admin.php'));
        wp_safe_redirect($url);
        exit;
    }

    // ---------------------------------------------------------------- Reservierungen

    public static function seite_reservierungen() {
        if (!current_user_can('manage_options')) { return; }
        $vorgaenge = Kikripp_DB::vorgaenge();
        $jetzt = current_time('timestamp');
        echo '<div class="wrap"><h1>Reservierungen</h1>';
        self::hinweis();

        $offen = $bezahlt = 0;
        foreach ($vorgaenge as $v) {
            if ($v['status'] === 'offen') { $offen++; }
            if ($v['status'] === 'bezahlt') { $bezahlt++; }
        }
        printf('<p>%d Vorgänge insgesamt · %d offen · %d bezahlt</p>',
            count($vorgaenge), $offen, $bezahlt);

        echo '<p><a href="' . esc_url(wp_nonce_url(admin_url('admin-post.php?action=kikripp_export'), 'kikripp_export')) . '" class="button">Alle Reservierungen als CSV exportieren</a></p>';

        if (empty($vorgaenge)) {
            echo '<p>Es liegen noch keine Reservierungen vor.</p></div>';
            return;
        }

        echo '<table class="widefat striped"><thead><tr>'
           . '<th>Nr.</th><th>Eingegangen</th><th>Interessent</th><th>Positionen</th>'
           . '<th>Summe netto</th><th>Status</th><th>Frist</th><th>Aktion</th>'
           . '</tr></thead><tbody>';

        foreach ($vorgaenge as $v) {
            $summe = 0;
            $posten = [];
            foreach ($v['positionen'] as $p) {
                $summe += (float) $p['preis_netto'] * (int) $p['menge'];
                $posten[] = sprintf('%d × %s', (int) $p['menge'], esc_html($p['artnr']));
            }
            $abgelaufen = $v['status'] === 'offen' && strtotime($v['ablauf']) < $jetzt;
            $status_text = $v['status'] === 'offen'
                ? ($abgelaufen ? '<span style="color:#b32d2e">abgelaufen</span>' : 'offen')
                : esc_html($v['status']);

            echo '<tr>';
            echo '<td>#' . (int) $v['id'] . ($v['testdaten'] ? ' <em>(Test)</em>' : '') . '</td>';
            echo '<td>' . esc_html(mysql2date('d.m.Y H:i', $v['erstellt'])) . '</td>';
            // Die Kontaktdaten stehen nach erfolgreichem Mailversand nur noch in der
            // Mail. Hier erscheint deshalb der Suchbegriff fürs Postfach.
            $suche = sprintf('[%s] Neue Reservierung #%d',
                get_option('kikripp_firma', 'Kikripp GmbH'), (int) $v['id']);
            echo '<td>';
            if ((int) $v['kontakt_weg']) {
                echo '<span style="color:#555">Kontaktdaten stehen in der Mail.</span><br>'
                   . '<code style="font-size:11px">' . esc_html($suche) . '</code><br>'
                   . '<span style="color:#777;font-size:11px">Diesen Text im Postfach suchen.</span>';
            } elseif ($v['name'] !== '') {
                $loesch = wp_nonce_url(admin_url('admin-post.php?action=kikripp_aktion&was=kontakt&id='
                    . (int) $v['id']), 'kikripp_aktion_' . $v['id']);
                echo '<span style="color:#b32d2e"><strong>Mail nicht versandt</strong></span><br>'
                   . '<strong>' . esc_html($v['name']) . '</strong><br>'
                   . '<a href="mailto:' . esc_attr($v['email']) . '">' . esc_html($v['email']) . '</a><br>'
                   . '<a href="tel:' . esc_attr(preg_replace('/[^0-9+]/', '', $v['telefon'])) . '">'
                   . esc_html($v['telefon']) . '</a><br>'
                   . '<a href="' . esc_url($loesch) . '" style="font-size:11px">notiert – Kontaktdaten löschen</a>';
            } else {
                echo '<span style="color:#777">—</span>';
            }
            echo '</td>';
            echo '<td>' . implode('<br>', $posten) . '</td>';
            echo '<td>' . esc_html(Kikripp_Mail::eur($summe)) . '</td>';
            echo '<td>' . $status_text . '</td>';
            echo '<td>' . esc_html(mysql2date('d.m.Y', $v['ablauf'])) . '</td>';
            echo '<td>';
            foreach ([
                'bezahlt'    => 'bezahlt',
                'storniert'  => 'stornieren',
                'verlaengern'=> 'Frist verlängern',
                'loeschen'   => 'löschen',
            ] as $was => $beschriftung) {
                $url = wp_nonce_url(admin_url('admin-post.php?action=kikripp_aktion&was=' . $was . '&id=' . (int) $v['id']), 'kikripp_aktion_' . $v['id']);
                $stil = $was === 'loeschen' ? ' style="color:#b32d2e"' : '';
                $frage = $was === 'loeschen' ? ' onclick="return confirm(\'Diesen Vorgang wirklich löschen?\')"' : '';
                echo '<a href="' . esc_url($url) . '"' . $stil . $frage . '>' . esc_html($beschriftung) . '</a><br>';
            }
            echo '</td></tr>';

            if (trim((string) $v['nachricht']) !== '') {
                echo '<tr><td></td><td colspan="7" style="color:#555">'
                   . esc_html($v['nachricht']) . '</td></tr>';
            }
        }
        echo '</tbody></table></div>';
    }

    public static function aktion() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        $id = isset($_GET['id']) ? (int) $_GET['id'] : 0;
        check_admin_referer('kikripp_aktion_' . $id);
        $was = isset($_GET['was']) ? sanitize_key($_GET['was']) : '';

        switch ($was) {
            case 'testdaten':
                $anzahl = Kikripp_DB::testdaten_loeschen();
                self::zurueck('kikripp-einstellungen', sprintf('%d Testreservierungen wurden gelöscht.', $anzahl));
            case 'bezahlt':
                Kikripp_DB::vorgang_status($id, 'bezahlt');
                self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d ist als bezahlt vermerkt. Die Artikel erscheinen nicht mehr im Katalog.', $id));
            case 'storniert':
                Kikripp_DB::vorgang_status($id, 'storniert');
                self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d wurde storniert, die Artikel sind wieder frei.', $id));
            case 'kontakt':
                Kikripp_DB::kontakt_loeschen($id);
                self::zurueck('kikripp-reservierungen', sprintf(
                    'Die Kontaktdaten zu Vorgang #%d wurden gelöscht.', $id));
            case 'verlaengern':
                Kikripp_DB::vorgang_verlaengern($id);
                self::zurueck('kikripp-reservierungen', sprintf('Die Frist für Vorgang #%d wurde verlängert.', $id));
            case 'loeschen':
                Kikripp_DB::vorgang_loeschen($id);
                self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d wurde gelöscht.', $id));
        }
        self::zurueck('kikripp-reservierungen', 'Unbekannte Aktion.', true);
    }

    public static function export() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_export');
        $vorgaenge = Kikripp_DB::vorgaenge();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename=kikripp-reservierungen-' . gmdate('Ymd-His') . '.csv');
        $aus = fopen('php://output', 'w');
        fwrite($aus, "\xEF\xBB\xBF");   // BOM, damit Excel die Umlaute erkennt
        fputcsv($aus, ['Vorgang', 'Eingegangen', 'Ablauf', 'Status', 'Name', 'Email', 'Telefon',
                       'Mailsuche', 'Nachricht', 'ArtNr', 'Menge', 'Preis_netto', 'Positionsstatus',
                       'Bezahlt_am'], ';');
        $firma = get_option('kikripp_firma', 'Kikripp GmbH');
        foreach ($vorgaenge as $v) {
            foreach ($v['positionen'] as $p) {
                fputcsv($aus, [
                    $v['id'], $v['erstellt'], $v['ablauf'], $v['status'], $v['name'], $v['email'],
                    $v['telefon'], sprintf('[%s] Neue Reservierung #%d', $firma, (int) $v['id']),
                    str_replace(["\r", "\n"], ' ', (string) $v['nachricht']),
                    $p['artnr'], $p['menge'],
                    number_format((float) $p['preis_netto'], 2, ',', '.'), $p['status'],
                    $p['bezahlt_am'] ?? '',
                ], ';');
            }
        }
        fclose($aus);
        exit;
    }

    // ---------------------------------------------------------------- Import

    public static function seite_import() {
        if (!current_user_can('manage_options')) { return; }
        global $wpdb;
        $anzahl = (int) $wpdb->get_var('SELECT COUNT(*) FROM ' . Kikripp_DB::t_artikel());
        $ohne_bild = (int) $wpdb->get_var("SELECT COUNT(*) FROM " . Kikripp_DB::t_artikel() . "
                                           WHERE daten LIKE '%\"bild\":\"\"%'");
        echo '<div class="wrap"><h1>Artikel importieren</h1>';
        self::hinweis();
        echo '<p>Im Katalog stehen derzeit <strong>' . $anzahl . '</strong> Artikel';
        if ($anzahl > 0) { echo ', davon <strong>' . $ohne_bild . '</strong> ohne gefundenes Foto'; }
        echo '.</p>';
        echo '<p>Die Importdatei erhalten Sie aus der Artikelstamm-Tabelle. Der Import <strong>aktualisiert</strong> '
           . 'vorhandene Artikel und ergänzt neue. Reservierungen bleiben dabei erhalten.</p>';
        echo '<p>Die Fotos gehören in die <a href="' . esc_url(admin_url('upload.php')) . '">Mediathek</a>; '
           . 'der Katalog sucht sie anhand des Dateinamens (F-001.jpg und so weiter).</p>';
        echo '<form method="post" enctype="multipart/form-data" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('kikripp_import');
        echo '<input type="hidden" name="action" value="kikripp_import">';
        echo '<p><input type="file" name="datei" accept=".json,application/json" required></p>';
        submit_button('Importieren');
        echo '</form></div>';
    }

    public static function import() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_import');
        if (empty($_FILES['datei']['tmp_name']) || !is_uploaded_file($_FILES['datei']['tmp_name'])) {
            self::zurueck('kikripp-import', 'Es wurde keine Datei hochgeladen.', true);
        }
        $roh = file_get_contents($_FILES['datei']['tmp_name']);
        $liste = json_decode((string) $roh, true);
        if (!is_array($liste)) {
            self::zurueck('kikripp-import', 'Die Datei konnte nicht gelesen werden. Erwartet wird eine JSON-Datei.', true);
        }

        global $wpdb;
        $neu = $geaendert = $ohne_bild = 0;
        $fehlende_fotos = [];
        $reserviert_entfernt = [];
        $belegung = Kikripp_DB::belegung();
        $gesehen = [];

        foreach ($liste as $i => $a) {
            if (empty($a['nr'])) { continue; }
            $artnr = sanitize_text_field((string) $a['nr']);
            $gesehen[] = $artnr;

            $bild = self::bild_url(isset($a['foto']) ? (string) $a['foto'] : '');
            if ($bild === '') {
                $ohne_bild++;
                if (!empty($a['foto'])) { $fehlende_fotos[] = (string) $a['foto']; }
            }

            $daten = [
                'nr'      => $artnr,
                'titel'   => (string) ($a['titel'] ?? ''),
                'beschr'  => (string) ($a['beschr'] ?? ''),
                'kat'     => (string) ($a['kat'] ?? ''),
                'raum'    => (string) ($a['raum'] ?? ''),
                'zustand' => (string) ($a['zustand'] ?? ''),
                'masse'   => (string) ($a['masse'] ?? ''),
                'einheit' => (string) ($a['einheit'] ?? 'Stück'),
                'basis'   => (string) ($a['basis'] ?? ''),
                'versand' => (string) ($a['versand'] ?? ''),
                'marke'   => (string) ($a['marke'] ?? ''),
                'buendel' => (string) ($a['buendel'] ?? ''),
                'foto'    => (string) ($a['foto'] ?? ''),
                'bild'    => $bild,
            ];
            $zeile = [
                'sortierung'   => (int) ($a['sortierung'] ?? $i),
                'menge'        => max(0, (int) ($a['menge'] ?? 0)),
                'preis_netto'  => (float) ($a['preis'] ?? 0),
                'aktiv'        => !empty($a['aktiv']) ? 1 : 0,
                'im_katalog'   => !empty($a['im_katalog']) ? 1 : 0,
                'daten'        => wp_json_encode($daten),
                'aktualisiert' => current_time('mysql'),
            ];

            $vorhanden = $wpdb->get_var($wpdb->prepare(
                'SELECT artnr FROM ' . Kikripp_DB::t_artikel() . ' WHERE artnr = %s', $artnr));
            if ($vorhanden) {
                $wpdb->update(Kikripp_DB::t_artikel(), $zeile, ['artnr' => $artnr]);
                $geaendert++;
            } else {
                $zeile['artnr'] = $artnr;
                $wpdb->insert(Kikripp_DB::t_artikel(), $zeile);
                $neu++;
            }
            // Artikel mit Reservierung, der stillgelegt werden soll -> melden statt still verschwinden
            $b = $belegung[$artnr] ?? null;
            if ($b && ($b['reserviert'] > 0 || $b['bezahlt'] > 0)
                && (empty($a['aktiv']) || empty($a['im_katalog']))) {
                $reserviert_entfernt[] = $artnr;
            }
        }

        // Artikel, die in der Importdatei gar nicht mehr vorkommen, werden aus dem Katalog
        // genommen – aber nicht gelöscht, denn an ihnen können Reservierungen und
        // Verkäufe hängen. Sonst bliebe eine gestrichene Position für immer sichtbar.
        $verschwunden = Kikripp_DB::fehlende_stilllegen($gesehen);
        // Wer eine Position streicht, auf der noch eine Reservierung liegt, muss das erfahren.
        foreach ($verschwunden as $weg) {
            $b = $belegung[$weg] ?? null;
            if ($b && ($b['reserviert'] > 0 || $b['bezahlt'] > 0)) { $reserviert_entfernt[] = $weg; }
        }

        $meldung = sprintf('Import abgeschlossen: %d neu, %d aktualisiert.', $neu, $geaendert);
        if ($verschwunden) {
            $meldung .= sprintf(' %d Artikel standen nicht mehr in der Datei und wurden aus dem '
                              . 'Katalog genommen (%s).', count($verschwunden),
                              implode(', ', array_slice($verschwunden, 0, 15)));
        }
        if ($ohne_bild > 0) {
            $fehlende_fotos = array_values(array_unique($fehlende_fotos));
            sort($fehlende_fotos);
            $meldung .= sprintf(' %d Artikel ohne gefundenes Foto. Diese Bilder fehlen in der '
                . 'Mediathek: %s%s', $ohne_bild,
                implode(', ', array_slice($fehlende_fotos, 0, 25)),
                count($fehlende_fotos) > 25 ? ' … und weitere' : '.');
        }
        if (!empty($reserviert_entfernt)) {
            $meldung .= ' ACHTUNG: Diese Artikel wurden stillgelegt, haben aber noch Reservierungen: '
                      . implode(', ', array_slice($reserviert_entfernt, 0, 15)) . '.';
        }
        delete_transient('kikripp_bilder');
        self::zurueck('kikripp-import', $meldung);
    }

    /** Foto in der Mediathek anhand des Dateinamens finden (F-001 -> Anhang). */
    private static function bild_url($fotoname) {
        $fotoname = trim($fotoname);
        if ($fotoname === '') { return ''; }
        $karte = get_transient('kikripp_bilder');
        if (!is_array($karte)) {
            $karte = [];
            $anhaenge = get_posts([
                'post_type'      => 'attachment',
                'post_mime_type' => 'image',
                'posts_per_page' => -1,
                'post_status'    => 'inherit',
                'fields'         => 'ids',
            ]);
            foreach ($anhaenge as $id) {
                $datei = basename((string) get_post_meta($id, '_wp_attached_file', true));
                $basis = strtoupper(preg_replace('/\.[a-zA-Z0-9]+$/', '', $datei));
                $basis = preg_replace('/-\d+$/', '', $basis);   // WordPress hängt bei Namensgleichheit -1 an
                if ($basis !== '' && !isset($karte[$basis])) {
                    $karte[$basis] = wp_get_attachment_url($id);
                }
            }
            set_transient('kikripp_bilder', $karte, HOUR_IN_SECONDS);
        }
        $schluessel = strtoupper($fotoname);
        return isset($karte[$schluessel]) ? (string) $karte[$schluessel] : '';
    }

    // ---------------------------------------------------------------- Einstellungen

    public static function seite_einstellungen() {
        if (!current_user_can('manage_options')) { return; }
        echo '<div class="wrap"><h1>Einstellungen</h1>';
        self::hinweis();
        echo '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '">';
        wp_nonce_field('kikripp_einstellungen');
        echo '<input type="hidden" name="action" value="kikripp_einstellungen">';
        echo '<table class="form-table"><tbody>';

        printf('<tr><th scope="row"><label for="k_pw">Katalog-Passwort</label></th><td>'
             . '<input type="text" id="k_pw" name="passwort" class="regular-text" placeholder="leer lassen = unverändert">'
             . '<p class="description">Wird das Passwort geändert, müssen sich alle erneut anmelden.</p></td></tr>');

        printf('<tr><th scope="row"><label for="k_mail">Reservierungen melden an</label></th><td>'
             . '<input type="email" id="k_mail" name="mail_an" class="regular-text" value="%s" required></td></tr>',
             esc_attr(get_option('kikripp_mail_an', '')));

        printf('<tr><th scope="row"><label for="k_band">Hinweisband</label></th><td>'
             . '<input type="text" id="k_band" name="hinweisband" class="large-text" value="%s">'
             . '<p class="description">Erscheint als Band über dem Katalog. Zum Livegang das Feld leeren.</p></td></tr>',
             esc_attr(get_option('kikripp_hinweisband', '')));

        printf('<tr><th scope="row"><label for="k_frist">Reservierung gilt</label></th><td>'
             . '<input type="number" id="k_frist" name="frist_tage" min="1" max="90" value="%d" class="small-text"> Tage'
             . '<p class="description">Danach wird der Artikel automatisch wieder frei, sofern er nicht auf bezahlt steht.</p></td></tr>',
             (int) get_option('kikripp_frist_tage', 7));

        printf('<tr><th scope="row"><label for="k_ust">Umsatzsteuer</label></th><td>'
             . '<input type="number" id="k_ust" name="ust" min="0" max="30" step="0.1" value="%s" class="small-text"> %%</td></tr>',
             esc_attr(get_option('kikripp_ust_prozent', 19)));

        printf('<tr><th scope="row"><label for="k_firma">Verkäuferin (Firma)</label></th><td>'
             . '<input type="text" id="k_firma" name="firma" class="regular-text" value="%s" required>'
             . '<p class="description">Erscheint im Katalog, im Mailbetreff und im Anbieter-Block. '
             . 'Bewusst hier und nicht der Name dieser Website – der Katalog läuft auf fremdem '
             . 'Speicherplatz.</p></td></tr>',
             esc_attr(get_option('kikripp_firma', '')));

        printf('<tr><th scope="row"><label for="k_tel">Telefon</label></th><td>'
             . '<input type="text" id="k_tel" name="telefon" class="regular-text" value="%s">'
             . '</td></tr>',
             esc_attr(get_option('kikripp_telefon', '')));

        printf('<tr><th scope="row"><label for="k_imp">Impressum</label></th><td>'
             . '<input type="url" id="k_imp" name="impressum_url" class="large-text" value="%s">'
             . '<p class="description">Vollständige Adresse der Impressumsseite der Verkäuferin. '
             . '<strong>Bitte prüfen</strong> – die Vorgabe ist geraten.</p></td></tr>',
             esc_attr(get_option('kikripp_impressum_url', '')));

        printf('<tr><th scope="row"><label for="k_ds">Datenschutzerklärung</label></th><td>'
             . '<input type="url" id="k_ds" name="datenschutz_url" class="large-text" value="%s">'
             . '<p class="description">Ebenfalls prüfen.</p></td></tr>',
             esc_attr(get_option('kikripp_datenschutz_url', '')));

        printf('<tr><th scope="row"><label for="k_abhol">Abholadresse</label></th><td>'
             . '<input type="text" id="k_abhol" name="abholadresse" class="large-text" value="%s">'
             . '<p class="description">Steht in der Bestätigungsmail an den Interessenten und unter dem Katalog.</p></td></tr>',
             esc_attr(get_option('kikripp_abholadresse', '')));

        printf('<tr><th scope="row"><label for="k_recht">Rechtliche Hinweise</label></th><td>'
             . '<textarea id="k_recht" name="rechtstext" class="large-text" rows="5">%s</textarea>'
             . '<p class="description">Erscheint unter dem Katalog. Leer lassen blendet den Block aus.</p></td></tr>',
             esc_textarea(get_option('kikripp_rechtstext', '')));

        printf('<tr><th scope="row">Vorschaubetrieb</th><td>'
             . '<label><input type="checkbox" name="vorschau" value="1" %s> '
             . 'Eingehende Reservierungen als Testdaten kennzeichnen</label>'
             . '<p class="description">In der Vorschauphase eingeschaltet lassen – Testreservierungen lassen sich dann '
             . 'mit einem Klick entfernen. Zum Livegang ausschalten.</p></td></tr>',
             checked(1, (int) get_option('kikripp_vorschau', 1), false));

        echo '</tbody></table>';
        submit_button('Einstellungen speichern');
        echo '</form>';

        $url = wp_nonce_url(admin_url('admin-post.php?action=kikripp_aktion&was=testdaten&id=0'), 'kikripp_aktion_0');
        echo '<hr><h2>Testdaten</h2><p>Entfernt alle Reservierungen, die im Vorschaubetrieb entstanden sind.</p>';
        echo '<p><a href="' . esc_url($url) . '" class="button" onclick="return confirm(\'Alle Testreservierungen löschen?\')">Testreservierungen löschen</a></p>';
        echo '</div>';
    }

    public static function einstellungen_speichern() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_einstellungen');
        $pw = isset($_POST['passwort']) ? trim(wp_unslash($_POST['passwort'])) : '';
        if ($pw !== '') { Kikripp_Zugang::passwort_setzen($pw); }
        update_option('kikripp_mail_an', sanitize_email(wp_unslash($_POST['mail_an'] ?? '')));
        update_option('kikripp_hinweisband', sanitize_text_field(wp_unslash($_POST['hinweisband'] ?? '')));
        update_option('kikripp_frist_tage', max(1, (int) ($_POST['frist_tage'] ?? 7)));
        update_option('kikripp_ust_prozent', (float) ($_POST['ust'] ?? 19));
        update_option('kikripp_vorschau', isset($_POST['vorschau']) ? 1 : 0);
        update_option('kikripp_abholadresse', sanitize_text_field(wp_unslash($_POST['abholadresse'] ?? '')));
        update_option('kikripp_rechtstext', sanitize_textarea_field(wp_unslash($_POST['rechtstext'] ?? '')));
        update_option('kikripp_firma', sanitize_text_field(wp_unslash($_POST['firma'] ?? '')));
        update_option('kikripp_telefon', sanitize_text_field(wp_unslash($_POST['telefon'] ?? '')));
        update_option('kikripp_impressum_url', esc_url_raw(wp_unslash($_POST['impressum_url'] ?? '')));
        update_option('kikripp_datenschutz_url', esc_url_raw(wp_unslash($_POST['datenschutz_url'] ?? '')));
        self::zurueck('kikripp-einstellungen', 'Einstellungen gespeichert.'
            . ($pw !== '' ? ' Das Passwort wurde geändert – alle Besucher müssen sich neu anmelden.' : ''));
    }
}
