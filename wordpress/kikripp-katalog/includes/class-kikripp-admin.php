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
        add_action('admin_post_kikripp_termin', [__CLASS__, 'termin_speichern']);
        add_action('admin_post_kikripp_vorgang', [__CLASS__, 'vorgang_speichern']);
        add_action('admin_post_kikripp_bestellung', [__CLASS__, 'bestellung']);
        add_action('admin_notices', [__CLASS__, 'hinweis_passwort']);
    }

    /** Ohne Passwort bleibt der Katalog für alle zu – das muss auffallen. */
    public static function hinweis_passwort() {
        if (!current_user_can('manage_options')) { return; }
        if (!Kikripp_Zugang::passwortschutz()) { return; }
        if (get_option('kikripp_passwort_hash')) { return; }
        printf('<div class="notice notice-warning"><p><strong>Artikelkatalog:</strong> '
             . 'Es ist noch kein Passwort vergeben – der Katalog ist deshalb für alle gesperrt. '
             . '<a href="%s">Jetzt Passwort festlegen</a></p></div>',
             esc_url(admin_url('admin.php?page=kikripp-einstellungen')));
    }

    /**
     * Zahl der offenen Reservierungen als Blase am Menuepunkt - wie bei Plugin-Updates.
     *
     * Der Webserver dieser Website verschickt keine Mails. Ohne diese Blase muesste die
     * Nutzerin daran denken, jeden Tag in die Reservierungen zu schauen; mit ihr sieht
     * sie es beim Einloggen. Das ersetzt die Benachrichtigungsmail.
     */
    private static function offene_blase() {
        // Seit 1.3.0: Zahl der Aufgaben aus „Zu erledigen“, die etwas verlangen – nicht mehr nur
        // die neuen Reservierungen. Eine unbezahlte Abholung morgen muss genauso auffallen.
        $n = count(array_filter(Kikripp_Ablauf::aufgaben(Kikripp_DB::vorgaenge()),
            function ($a) { return $a['art'] === 'warn'; }));
        if ($n < 1) { return ''; }
        return sprintf(' <span class="update-plugins count-%d"><span class="plugin-count">%d'
                     . '</span></span>', $n, $n);
    }

    public static function menue() {
        $blase = self::offene_blase();
        add_menu_page('Artikelkatalog', 'Artikelkatalog' . $blase, 'manage_options',
            'kikripp-reservierungen', [__CLASS__, 'seite_reservierungen'], 'dashicons-cart', 26);
        add_submenu_page('kikripp-reservierungen', 'Reservierungen', 'Reservierungen' . $blase,
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

    private static function zurueck($seite, $meldung, $fehler = false, $anker = '') {
        // Aus dem Abholplan heraus geklickt? Dann dorthin zurück, nicht in die Reservierungen.
        $herkunft = (string) wp_get_referer();
        if ($seite === 'kikripp-reservierungen' && strpos($herkunft, 'page=kikripp-abholplan') !== false) {
            $seite = 'kikripp-abholplan';
        }
        $reiter = null;
        if (preg_match('/[?&]reiter=([a-z]+)/', $herkunft, $m)) { $reiter = $m[1]; }
        $url = add_query_arg(array_filter([
            'page' => $seite,
            'reiter' => $seite === 'kikripp-reservierungen' ? $reiter : null,
            'kikripp_meldung' => $meldung,
            'kikripp_fehler' => $fehler ? '1' : null,
        ]), admin_url('admin.php'));
        wp_safe_redirect($url . ($anker !== '' ? '#' . $anker : ''));
        exit;
    }

    // ---------------------------------------------------------------- Reservierungen

    /** Statusbezeichnung für die Liste. */
    private static function status_text($v, $jetzt) {
        if ($v['status'] === 'offen') {
            return strtotime($v['ablauf']) < $jetzt
                ? '<span style="color:#b32d2e">abgelaufen</span>' : 'reserviert';
        }
        if ($v['status'] === 'bestellt') { return '<strong>bestellt</strong>'; }
        return esc_html($v['status']);
    }

    public static function aktion_url($was, $id, $extra = []) {
        return wp_nonce_url(add_query_arg(array_merge(['action' => 'kikripp_aktion', 'was' => $was,
            'id' => (int) $id], $extra), admin_url('admin-post.php')), 'kikripp_aktion_' . (int) $id);
    }

    const REITER = ['aktiv' => 'Aktiv', 'neu' => 'Neu', 'bestellt' => 'Bestellt (unbezahlt)', 'bezahlt' => 'Bezahlt',
                    'abgeholt' => 'Abgeholt', 'erledigt' => 'Storniert / abgelaufen', 'alle' => 'Alle'];

    public static function seite_reservierungen() {
        if (!current_user_can('manage_options')) { return; }
        $vorgaenge = Kikripp_DB::vorgaenge();
        $jetzt = current_time('timestamp');
        echo '<div class="wrap"><h1>Reservierungen</h1>';
        self::hinweis();

        // F: Kennzahlen
        $k = Kikripp_Ablauf::kennzahlen($vorgaenge, $jetzt);
        echo '<p style="font-size:14px;background:#fff;border:1px solid #ccd0d4;padding:8px 12px;display:inline-block">'
           . 'Umsatz bezahlt: <strong>' . esc_html(Kikripp_Mail::eur($k['bezahlt'])) . '</strong> &nbsp;·&nbsp; '
           . 'Rechnungen offen: <strong>' . esc_html(Kikripp_Mail::eur($k['rechnung_offen'])) . '</strong> &nbsp;·&nbsp; '
           . 'bestellt, ohne Rechnung: <strong>' . esc_html(Kikripp_Mail::eur($k['ohne_rechnung'])) . '</strong> &nbsp;·&nbsp; '
           . 'reserviert: <strong>' . esc_html(Kikripp_Mail::eur($k['reserviert'])) . '</strong></p>';

        // C: Zu erledigen
        $aufgaben = Kikripp_Ablauf::aufgaben($vorgaenge, $jetzt);
        echo '<div style="background:#fff;border:1px solid #ccd0d4;border-left:4px solid #C8102E;padding:8px 14px;margin:8px 0 14px;max-width:1100px">'
           . '<h2 style="margin:4px 0 6px;font-size:15px">Zu erledigen (' . count($aufgaben) . ')</h2>'
           . Kikripp_Ablauf::aufgaben_html($aufgaben) . '</div>';

        // E: Reiter
        $zahl = array_fill_keys(array_keys(self::REITER), 0);
        foreach ($vorgaenge as $v) {
            $r = Kikripp_Ablauf::reiter_von($v, $jetzt);
            $zahl[$r]++; $zahl['alle']++;
            if (in_array($r, ['neu', 'bestellt', 'bezahlt'], true)) { $zahl['aktiv']++; }
        }
        $reiter = sanitize_key($_GET['reiter'] ?? 'aktiv');
        if (!isset(self::REITER[$reiter])) { $reiter = 'aktiv'; }
        echo '<nav class="nav-tab-wrapper" style="margin-bottom:10px">';
        foreach (self::REITER as $schluessel => $name) {
            echo '<a class="nav-tab' . ($schluessel === $reiter ? ' nav-tab-active' : '') . '" href="'
               . esc_url(admin_url('admin.php?page=kikripp-reservierungen&reiter=' . $schluessel)) . '">'
               . esc_html($name) . ' <span style="color:#777">(' . $zahl[$schluessel] . ')</span></a>';
        }
        echo '</nav>';
        echo '<p style="color:#555;max-width:1100px;margin:4px 0 10px">Ablauf: <strong>Neu</strong> (läuft nach '
           . Kikripp_DB::frist_werktage() . ' Werktagen ab) → nach der Zusage <strong>bestellt</strong>, Abholtermin, Bestellung erstellen, '
           . 'Rechnung aus DATEV, „Mail schreiben“, „In Outlook eintragen“ → nach Zahlungseingang <strong>bezahlt</strong> → '
           . 'bei der Übergabe <strong>abgeholt</strong>.</p>';
        echo '<p><a href="' . esc_url(wp_nonce_url(admin_url('admin-post.php?action=kikripp_export'), 'kikripp_export')) . '" class="button">Alle Reservierungen als CSV exportieren</a> '
           . '<a href="' . esc_url(admin_url('admin.php?page=kikripp-abholplan')) . '" class="button">Abholplan</a></p>';

        $sichtbar = array_filter($vorgaenge, function ($v) use ($reiter, $jetzt) {
            $r = Kikripp_Ablauf::reiter_von($v, $jetzt);
            return $reiter === 'alle' || $r === $reiter || ($reiter === 'aktiv' && in_array($r, ['neu', 'bestellt', 'bezahlt'], true));
        });
        if (empty($sichtbar)) {
            echo '<p>' . (empty($vorgaenge) ? 'Es liegen noch keine Reservierungen vor.' : 'In diesem Reiter ist nichts.') . '</p></div>';
            return;
        }

        echo '<table class="widefat striped"><thead><tr>'
           . '<th>Nr.</th><th>Eingegangen</th><th>Interessent</th><th>Positionen</th>'
           . '<th>Summe</th><th>Status</th><th>Wünsche</th><th>Aktion</th>'
           . '</tr></thead><tbody>';

        foreach ($sichtbar as $v) {
            $summe = 0;
            $posten = [];
            $offen_oder_bestellt = in_array($v['status'], ['offen', 'bestellt'], true);
            foreach ($v['positionen'] as $p) {
                $zeile = sprintf('%d × %s', (int) $p['menge'], esc_html($p['artnr']));
                if ($p['status'] === 'storniert') {
                    $posten[] = '<s style="color:#999">' . $zeile . '</s>';
                    continue;
                }
                $summe += (float) $p['preis_netto'] * (int) $p['menge'];
                if ($offen_oder_bestellt && count($v['positionen']) > 1) {
                    $zeile .= ' <a href="' . esc_url(self::aktion_url('pos', $v['id'], ['pid' => (int) $p['id']]))
                            . '" style="font-size:11px" onclick="return confirm(\'Nur diese Position stornieren?\')">'
                            . 'stornieren</a>';
                }
                $posten[] = $zeile;
            }

            echo '<tr id="vorgang-' . (int) $v['id'] . '">';
            echo '<td><strong>#' . (int) $v['id'] . '</strong>' . ($v['testdaten'] ? ' <em>(Test)</em>' : '') . '</td>';
            echo '<td>' . esc_html(mysql2date('d.m.Y H:i', $v['erstellt'])) . '</td>';
            $suche = sprintf('[%s] Neue Reservierung #%d',
                get_option('kikripp_firma', 'Kikripp GmbH'), (int) $v['id']);
            echo '<td>';
            if ($v['name'] !== '' || $v['email'] !== '' || $v['telefon'] !== '') {
                $loesch = self::aktion_url('kontakt', $v['id']);
                echo '<strong>' . esc_html($v['name']) . '</strong><br>';
                if (trim((string) ($v['firma'] ?? '')) !== '') { echo esc_html($v['firma']) . '<br>'; }
                if (trim((string) ($v['strasse'] ?? '')) !== '') {
                    echo esc_html($v['strasse']) . ', ' . esc_html(trim($v['plz'] . ' ' . $v['ort'])) . '<br>';
                }
                if ($v['email'] !== '') {
                    echo '<a href="mailto:' . esc_attr($v['email']) . '">'
                       . esc_html($v['email']) . '</a><br>';
                }
                if ($v['telefon'] !== '') {
                    echo '<a href="tel:' . esc_attr(preg_replace('/[^0-9+]/', '', $v['telefon']))
                       . '">' . esc_html($v['telefon']) . '</a><br>';
                }
                echo '<a href="' . esc_url($loesch) . '" style="font-size:11px" onclick="return confirm(\'Kontaktdaten zu diesem Vorgang endgültig löschen?\')">'
                   . 'erledigt – Kontaktdaten löschen</a>';
            } elseif ((int) $v['kontakt_weg']) {
                echo '<span style="color:#777">Kontaktdaten gelöscht.</span><br>'
                   . '<code style="font-size:11px">' . esc_html($suche) . '</code>';
            } else {
                echo '<span style="color:#777">—</span>';
            }
            echo '</td>';
            echo '<td>' . implode('<br>', $posten) . '</td>';
            echo '<td>' . esc_html(Kikripp_Mail::eur($summe)) . '</td>';
            echo '<td>' . self::status_text($v, $jetzt);
            if ($v['status'] === 'offen') {
                echo '<br><span style="font-size:11px;color:#555">bis ' . esc_html(mysql2date('d.m.Y', $v['ablauf'])) . '</span>';
            }
            if (trim((string) ($v['abgeholt_am'] ?? '')) !== '') {
                echo '<br><span style="color:#00a32a">abgeholt ' . esc_html(Kikripp_Ablauf::datum_text($v['abgeholt_am'])) . '</span>';
            }
            echo '</td>';

            echo '<td style="font-size:12px">Besichtigung: ' . esc_html(Kikripp_Mail::besichtigung_text($v))
               . '<br>Abholwunsch: ' . esc_html(Kikripp_Mail::abholung_text($v)) . '</td>';

            echo '<td>';
            $aktionen = [];
            if ($v['status'] === 'offen') { $aktionen['bestellt'] = 'bestellt'; }
            if ($offen_oder_bestellt) {
                $aktionen['bezahlt'] = 'bezahlt';
                $aktionen['storniert'] = 'stornieren';
            }
            if ($v['status'] === 'offen') { $aktionen['verlaengern'] = 'Frist verlängern'; }
            $aktionen['loeschen'] = 'löschen';
            foreach ($aktionen as $was => $beschriftung) {
                $stil = $was === 'loeschen' ? ' style="color:#b32d2e"' : '';
                $frage = $was === 'loeschen' ? ' onclick="return confirm(\'Diesen Vorgang wirklich löschen?\')"'
                       : ($was === 'storniert' ? ' onclick="return confirm(\'Vorgang stornieren? Die Artikel sind dann wieder im Katalog.\')"' : '');
                echo '<a href="' . esc_url(self::aktion_url($was, $v['id'])) . '"' . $stil . $frage . '>'
                   . esc_html($beschriftung) . '</a><br>';
            }
            if ($v['status'] !== 'storniert') {
                $b = wp_nonce_url(admin_url('admin-post.php?action=kikripp_bestellung&id=' . (int) $v['id']),
                    'kikripp_bestellung_' . (int) $v['id']);
                $privat = Kikripp_Ablauf::privat($v);
                echo '<span style="font-size:11px;color:#555">Bestellung erstellen:</span><br>'
                   . '<a href="' . esc_url($b . '&art=unternehmen') . '" target="_blank"' . ($privat ? '' : ' style="font-weight:600"') . '>Unternehmen</a> · '
                   . '<a href="' . esc_url($b . '&art=privat') . '" target="_blank"' . ($privat ? ' style="font-weight:600"' : '') . '>Privatperson</a>';
            }
            echo '</td></tr>';

            if (trim((string) $v['nachricht']) !== '') {
                echo '<tr><td></td><td colspan="7" style="color:#555">Nachricht: '
                   . esc_html($v['nachricht']) . '</td></tr>';
            }
            if ($v['status'] !== 'storniert') {
                echo '<tr><td></td><td colspan="7" style="background:#f6f7f7">' . self::bearbeiten_html($v) . '</td></tr>';
            }
        }
        echo '</tbody></table>';
        echo '<script>function kikKopieren(id){var t=document.getElementById(id);if(!t)return;'
           . 'if(navigator.clipboard){navigator.clipboard.writeText(t.value);}else{t.style.display="block";t.select();document.execCommand("copy");t.style.display="none";}'
           . 'var m=document.getElementById(id+"-ok");if(m){m.style.display="inline";setTimeout(function(){m.style.display="none";},2000);}}</script>';
        echo '</div>';
    }

    /**
     * B + D + A: Bearbeitungszeile eines Vorgangs – Abholtermin, Rechnung, Notiz, Du/Sie –
     * und die Knöpfe für Mail, Zahlungserinnerung, Outlook und „abgeholt“.
     */
    private static function bearbeiten_html($v) {
        $id = (int) $v['id'];
        $abholung = (string) ($v['abholung'] ?? '');
        $vorschlag = false;
        if ($abholung === '' && trim((string) ($v['abholwunsch'] ?? '')) !== '') {
            $abholung = strlen($v['abholwunsch']) > 10 ? $v['abholwunsch'] : $v['abholwunsch'] . ' 09:00';
            $vorschlag = true;
        }
        $tag = substr($abholung, 0, 10);
        $zeit = substr($abholung, 11, 5);
        $h = '<form method="post" action="' . esc_url(admin_url('admin-post.php')) . '" style="display:flex;flex-wrap:wrap;gap:10px 16px;align-items:flex-end">'
           . wp_nonce_field('kikripp_vorgang_' . $id, '_wpnonce', true, false)
           . '<input type="hidden" name="action" value="kikripp_vorgang"><input type="hidden" name="id" value="' . $id . '">'
           . '<label style="font-size:12px">Abholtermin' . ($vorschlag ? ' <span style="color:#b26200">(Wunsch – bitte bestätigen)</span>' : '') . '<br>'
           . '<input type="date" name="abhol_tag" value="' . esc_attr($tag) . '"> '
           . '<input type="time" name="abhol_zeit" step="900" value="' . esc_attr($zeit) . '" style="width:100px"></label>'
           . '<label style="font-size:12px">Rechnungsnr.<br><input type="text" name="rechnungsnr" value="' . esc_attr((string) ($v['rechnungsnr'] ?? '')) . '" style="width:110px"></label>'
           . '<label style="font-size:12px">Rechnung vom<br><input type="date" name="rechnung_am" value="' . esc_attr((string) ($v['rechnung_am'] ?? '')) . '"></label>'
           . '<label style="font-size:12px;flex:1;min-width:200px">Notiz (intern)<br><input type="text" name="notiz" value="' . esc_attr((string) ($v['notiz'] ?? '')) . '" style="width:100%"></label>'
           . '<label style="font-size:12px"><input type="checkbox" name="du" value="1"' . checked(1, (int) ($v['du'] ?? 0), false) . '> per Du</label>'
           . '<button class="button button-primary">Speichern</button></form>';
        if (trim((string) ($v['abholtermin'] ?? '')) !== '') {
            $h .= '<div style="font-size:11px;color:#777;margin-top:4px">Früher eingetragen: ' . esc_html($v['abholtermin']) . '</div>';
        }

        $knoepfe = [];
        if (trim((string) $v['email']) !== '') {
            $knoepfe[] = '<a class="button" href="' . esc_attr(Kikripp_Ablauf::mailto($v)) . '">✉ Mail schreiben</a>'
                . ' <a href="#" onclick="kikKopieren(\'kik-text-' . $id . '\');return false" style="font-size:11px">Text kopieren</a>'
                . '<span id="kik-text-' . $id . '-ok" style="display:none;color:#00a32a;font-size:11px"> kopiert</span>'
                . '<textarea id="kik-text-' . $id . '" style="display:none">' . esc_textarea(implode("\n\n", Kikripp_Ablauf::mail_text($v))) . '</textarea>';
            if ($v['status'] === 'bestellt' && trim((string) $v['rechnungsnr']) !== '') {
                $knoepfe[] = '<a class="button" href="' . esc_attr(Kikripp_Ablauf::mailto($v, 'erinnerung')) . '">✉ Zahlungserinnerung</a>';
            }
        }
        if (trim((string) ($v['abholung'] ?? '')) !== '') {
            $knoepfe[] = '<a class="button" href="' . esc_url(Kikripp_Ablauf::ics_url($id)) . '">📅 In Outlook eintragen</a>';
        }
        if (in_array($v['status'], ['bestellt', 'bezahlt'], true)) {
            if (trim((string) ($v['abgeholt_am'] ?? '')) === '') {
                $knoepfe[] = '<a class="button" href="' . esc_url(self::aktion_url('abgeholt', $id)) . '"'
                    . ($v['status'] === 'bezahlt' ? '' : ' onclick="return confirm(\'Noch nicht als bezahlt vermerkt. Trotzdem abgeholt (wird dabei als bezahlt vermerkt)?\')"')
                    . '>✓ abgeholt</a>';
            } else {
                $knoepfe[] = '<a href="' . esc_url(self::aktion_url('nicht_abgeholt', $id)) . '" style="font-size:11px">„abgeholt“ zurücknehmen</a>';
            }
        }
        if ($knoepfe) { $h .= '<div style="margin-top:8px;display:flex;flex-wrap:wrap;gap:8px;align-items:center">' . implode(' ', $knoepfe) . '</div>'; }
        return $h;
    }

    public static function vorgang_speichern() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        $id = (int) ($_POST['id'] ?? 0);
        check_admin_referer('kikripp_vorgang_' . $id);
        $tag = sanitize_text_field(wp_unslash($_POST['abhol_tag'] ?? ''));
        $zeit = sanitize_text_field(wp_unslash($_POST['abhol_zeit'] ?? ''));
        $abholung = ($tag !== '' && preg_match('/^\d{2}:\d{2}$/', $zeit)) ? "$tag $zeit"
                  : ($tag !== '' ? "$tag 09:00" : '');
        Kikripp_DB::vorgang_bearbeiten($id, [
            'abholung'    => $abholung,
            'rechnungsnr' => sanitize_text_field(wp_unslash($_POST['rechnungsnr'] ?? '')),
            'rechnung_am' => sanitize_text_field(wp_unslash($_POST['rechnung_am'] ?? '')),
            'notiz'       => sanitize_text_field(wp_unslash($_POST['notiz'] ?? '')),
            'du'          => !empty($_POST['du']),
        ]);
        self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d gespeichert.', $id) .
            ($abholung !== '' ? ' Abholung: ' . Kikripp_Ablauf::termin_text($abholung) . ' – jetzt „In Outlook eintragen“.' : ''),
            false, 'vorgang-' . $id);
    }

    public static function termin_speichern() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        $id = (int) ($_POST['id'] ?? 0);
        check_admin_referer('kikripp_termin_' . $id);
        Kikripp_DB::abholtermin_setzen($id, sanitize_text_field(wp_unslash($_POST['termin'] ?? '')));
        self::zurueck('kikripp-reservierungen', sprintf('Abholtermin für Vorgang #%d gespeichert.', $id));
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
            case 'bestellt':
                Kikripp_DB::vorgang_status($id, 'bestellt');
                self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d ist bestellt. Die Reservierung läuft nicht mehr ab.', $id));
            case 'pos':
                $rest = Kikripp_DB::position_stornieren($id, (int) ($_GET['pid'] ?? 0));
                self::zurueck('kikripp-reservierungen', $rest > 0
                    ? sprintf('Die Position wurde storniert und ist wieder im Katalog. Vorgang #%d läuft mit %d Position(en) weiter.', $id, $rest)
                    : sprintf('Die letzte Position wurde storniert – Vorgang #%d ist damit storniert.', $id));
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
            case 'abgeholt':
                Kikripp_DB::abgeholt_setzen($id, Kikripp_Ablauf::heute());
                self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d ist abgeholt.', $id), false, 'vorgang-' . $id);
            case 'nicht_abgeholt':
                Kikripp_DB::abgeholt_setzen($id, '');
                self::zurueck('kikripp-reservierungen', sprintf('„abgeholt“ bei Vorgang #%d zurückgenommen.', $id), false, 'vorgang-' . $id);
            case 'loeschen':
                Kikripp_DB::vorgang_loeschen($id);
                self::zurueck('kikripp-reservierungen', sprintf('Vorgang #%d wurde gelöscht.', $id));
        }
        self::zurueck('kikripp-reservierungen', 'Unbekannte Aktion.', true);
    }

    // ---------------------------------------------------------------- Bestellung

    /**
     * Druckfertige Bestellung (Kaufvertrag) zu einem Vorgang.
     *
     * Zwei Fassungen, weil das Recht es verlangt: Gegenüber Unternehmen ist die
     * Gewährleistung ausgeschlossen. Gegenüber Privatpersonen darf die Verjährung bei
     * gebrauchten Sachen nur auf ein Jahr verkürzt werden, wenn das gesondert vereinbart
     * wird – deshalb ein eigener Kasten mit eigener Unterschrift. Seit 07.10.2026 zahlen auch
     * Privatpersonen per Rechnung vor der Abholung; der Vertrag kann also ohne Treffen
     * zustande kommen (Fernabsatz). Die Fassung für Privatpersonen enthält deshalb die
     * Widerrufsbelehrung und das Muster-Widerrufsformular (Anlage 1 und 2 zu Art. 246a EGBGB).
     */
    public static function bestellung() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        $id = (int) ($_GET['id'] ?? 0);
        check_admin_referer('kikripp_bestellung_' . $id);
        echo self::bestellung_html($id, sanitize_key($_GET['art'] ?? 'unternehmen'));
        exit;
    }

    public static function bestellung_html($id, $art) {
        $v = Kikripp_DB::vorgang($id);
        if (!$v) { return 'Vorgang nicht gefunden.'; }
        $privat = $art === 'privat';
        $e = function ($t) { return esc_html((string) $t); };
        $firma = (string) get_option('kikripp_firma', 'Kikripp GmbH');
        $ust = (float) get_option('kikripp_ust_prozent', 0) / 100;
        $schluss = (string) get_option('kikripp_abholschluss', '');
        $schluss_text = $schluss ? gmdate('d.m.Y', strtotime($schluss . ' 12:00:00 UTC')) : '';

        $zeilen = ''; $summe = 0.0;
        foreach ($v['positionen'] as $p) {
            if ($p['status'] === 'storniert') { continue; }
            $d = json_decode((string) $p['daten'], true);
            $titel = is_array($d) && !empty($d['titel']) ? $d['titel'] : $p['artnr'];
            $einheit = is_array($d) && !empty($d['einheit']) ? $d['einheit'] : 'Stück';
            $wert = (float) $p['preis_netto'] * (int) $p['menge'];
            $summe += $wert;
            $zeilen .= '<tr><td>' . $e($p['artnr']) . '</td><td>' . $e($titel) . '</td><td class="r">'
                . (int) $p['menge'] . ' ' . $e($einheit) . '</td><td class="r">' . $e(Kikripp_Mail::eur($p['preis_netto']))
                . '</td><td class="r">' . $e(Kikripp_Mail::eur($wert)) . '</td></tr>';
        }
        $summenzeile = $ust > 0
            ? '<tr class="s"><td colspan="4">Summe netto</td><td class="r">' . $e(Kikripp_Mail::eur($summe)) . '</td></tr>'
              . '<tr class="s"><td colspan="4">zzgl. Umsatzsteuer</td><td class="r">' . $e(Kikripp_Mail::eur($summe * $ust)) . '</td></tr>'
              . '<tr class="s"><td colspan="4"><b>Gesamtbetrag</b></td><td class="r"><b>' . $e(Kikripp_Mail::eur($summe * (1 + $ust))) . '</b></td></tr>'
            : '<tr class="s"><td colspan="4"><b>Gesamtbetrag</b> (umsatzsteuerfrei)</td><td class="r"><b>'
              . $e(Kikripp_Mail::eur($summe)) . '</b></td></tr>';

        $anschrift = array_filter([
            trim((string) ($v['firma'] ?? '')), trim((string) $v['name']),
            trim((string) ($v['strasse'] ?? '')), trim(($v['plz'] ?? '') . ' ' . ($v['ort'] ?? '')),
        ]);
        $kontakt = array_filter([trim((string) $v['email']), trim((string) $v['telefon'])]);
        $bedingungen = '';
        foreach (preg_split('/\n\s*\n/', trim((string) get_option('kikripp_rechtstext', ''))) as $absatz) {
            if (trim($absatz) !== '') { $bedingungen .= '<p>' . $e(trim($absatz)) . '</p>'; }
        }
        $zahlung = 'Die Rechnung wird per E-Mail versandt. Der Betrag ist vorab auf das in der Rechnung angegebene Konto '
              . 'zu überweisen; abgeholt wird erst nach Zahlungseingang.';
        $gewaehr = $privat
            ? '<div class="kasten"><b>Gesonderte Vereinbarung zur Verjährung</b>'
              . '<p>Der Käufer ist Verbraucher. Es handelt sich um gebrauchte Sachen. Die Verjährungsfrist für '
              . 'Mängelansprüche wird abweichend von der gesetzlichen Frist auf <b>ein Jahr ab Übergabe</b> verkürzt. '
              . 'Der Käufer wurde vor Abgabe seiner Vertragserklärung gesondert auf diese Verkürzung hingewiesen.</p>'
              . '<p>☐ Ich bin mit der Verkürzung der Verjährungsfrist auf ein Jahr einverstanden.</p>'
              . '<div class="unterschrift"><span>Ort, Datum</span><span>Unterschrift Käufer</span></div></div>'
            : '<div class="kasten"><b>Gewährleistung</b><p>Der Käufer ist Unternehmer. Die Gewährleistung für '
              . 'Sach- und Rechtsmängel ist ausgeschlossen.</p></div>';

        $termine = [];
        if (trim((string) ($v['abholung'] ?? '')) !== '') { $termine[] = 'Vereinbarter Abholtermin: ' . Kikripp_Ablauf::termin_text($v['abholung']); }
        elseif (trim((string) ($v['abholtermin'] ?? '')) !== '') { $termine[] = 'Vereinbarter Abholtermin: ' . $v['abholtermin']; }
        elseif (Kikripp_Mail::abholung_text($v) !== '—') { $termine[] = 'Abholwunsch: ' . Kikripp_Mail::abholung_text($v); }
        if (Kikripp_Mail::besichtigung_text($v) !== 'nein') { $termine[] = 'Besichtigung: ' . Kikripp_Mail::besichtigung_text($v); }

        return '<!doctype html><html lang="de"><head><meta charset="utf-8"><title>Bestellung ' . (int) $id . '</title>'
            . '<style>body{font:13px/1.45 Arial,Helvetica,sans-serif;color:#1a1a1a;max-width:780px;margin:24px auto;padding:0 20px}'
            . 'h1{font-size:20px;margin:18px 0 2px}.kopf{display:flex;justify-content:space-between;border-bottom:3px solid #C8102E;padding-bottom:10px}'
            . '.klein{color:#555;font-size:12px}table{width:100%;border-collapse:collapse;margin:14px 0}th,td{padding:5px 6px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}'
            . 'th{background:#F7F5F2;font-size:12px}.r{text-align:right;white-space:nowrap}tr.s td{border-bottom:0}'
            . '.kasten{border:1px solid #bbb;padding:10px 12px;margin:14px 0}.unterschrift{display:flex;gap:40px;margin-top:34px}'
            . '.unterschrift span{flex:1;border-top:1px solid #1a1a1a;padding-top:4px;font-size:12px;color:#555}'
            . '.knopf{background:#C8102E;color:#fff;border:0;padding:9px 16px;font-size:14px;cursor:pointer;border-radius:3px}'
            . '@media print{.knopf,.nicht-drucken{display:none}body{margin:0}}</style></head><body>'
            . '<p class="nicht-drucken"><button class="knopf" onclick="window.print()">Drucken / als PDF speichern</button> '
            . '<span class="klein">Fassung: ' . ($privat ? 'Privatperson' : 'Unternehmen') . '</span></p>'
            . '<div class="kopf"><div><b>' . $e($firma) . '</b><br><span class="klein">' . $e(get_option('kikripp_abholadresse', ''))
            . '<br>Telefon ' . $e(get_option('kikripp_telefon', '')) . ' · ' . $e(Kikripp_REST::kontakt_email()) . '</span></div>'
            . '<div class="klein" style="text-align:right">Vorgang ' . (int) $id . '<br>' . $e(gmdate('d.m.Y', current_time('timestamp'))) . '</div></div>'
            . '<h1>Bestellung (Kaufvertrag) Nr. ' . (int) $id . '</h1>'
            . '<p class="klein">Gebrauchte Artikel aus Betriebsauflösung</p>'
            . '<table><tr><th style="width:50%">Käufer (' . ($privat ? 'Privatperson' : 'Unternehmen') . ')</th><th>Kontakt</th></tr>'
            . '<tr><td>' . implode('<br>', array_map($e, $anschrift)) . '</td><td>' . implode('<br>', array_map($e, $kontakt)) . '</td></tr></table>'
            . '<table><tr><th>Art.-Nr.</th><th>Bezeichnung</th><th class="r">Menge</th><th class="r">Einzelpreis</th><th class="r">Gesamt</th></tr>'
            . $zeilen . $summenzeile . '</table>'
            . ($termine ? '<p>' . implode('<br>', array_map($e, $termine)) . '</p>' : '')
            . '<p><b>Zahlung:</b> ' . $e($zahlung) . '</p>'
            . '<p><b>Abholung:</b> durch den Käufer, montags und dienstags von 08:00 bis 11:00 Uhr; Demontage nach '
            . 'Vereinbarung auch Freitagnachmittag oder Samstagvormittag. Werkzeug ist mitzubringen.'
            . ($schluss_text ? ' Die Ware ist bis spätestens <b>' . $e($schluss_text) . '</b> abzuholen. Nicht abgeholte Ware geht '
              . 'ohne Erstattung in das Eigentum der ' . $e($firma) . ' zurück.' : '') . '</p>'
            . $gewaehr
            . '<div class="klein"><b>Kaufbedingungen</b>' . $bedingungen . '</div>'
            . '<div class="unterschrift"><span>Ort, Datum</span><span>Unterschrift Käufer</span><span>' . $e($firma) . '</span></div>'
            . ($privat ? self::widerruf_html($firma, $e) : '')
            . '</body></html>';
    }

    /**
     * Widerrufsbelehrung und Muster-Widerrufsformular für Verbraucher, nach den gesetzlichen
     * Mustern. Angepasst an die Abholung: Die Ware wird an der Abholadresse zurückgegeben.
     */
    private static function widerruf_html($firma, $e) {
        $adresse = (string) get_option('kikripp_abholadresse', '');
        $mail = Kikripp_REST::kontakt_email();
        $tel = (string) get_option('kikripp_telefon', '');
        $wir = $e($firma) . ($adresse !== '' ? ', ' . $e($adresse) : '')
            . ($tel !== '' ? ', Telefon ' . $e($tel) : '') . ($mail !== '' ? ', E-Mail ' . $e($mail) : '');
        return '<div class="kasten" style="page-break-before:always"><b>Widerrufsbelehrung</b>'
            . '<p><b>Widerrufsrecht</b><br>Sie haben das Recht, binnen vierzehn Tagen ohne Angabe von Gründen diesen Vertrag '
            . 'zu widerrufen. Die Widerrufsfrist beträgt vierzehn Tage ab dem Tag, an dem Sie oder ein von Ihnen benannter '
            . 'Dritter, der nicht der Beförderer ist, die Waren in Besitz genommen haben bzw. hat.</p>'
            . '<p>Um Ihr Widerrufsrecht auszuüben, müssen Sie uns (' . $wir . ') mittels einer eindeutigen Erklärung '
            . '(z. B. ein mit der Post versandter Brief oder eine E-Mail) über Ihren Entschluss, diesen Vertrag zu widerrufen, '
            . 'informieren. Sie können dafür das beigefügte Muster-Widerrufsformular verwenden, das jedoch nicht vorgeschrieben '
            . 'ist. Zur Wahrung der Widerrufsfrist reicht es aus, dass Sie die Mitteilung über die Ausübung des '
            . 'Widerrufsrechts vor Ablauf der Widerrufsfrist absenden.</p>'
            . '<p><b>Folgen des Widerrufs</b><br>Wenn Sie diesen Vertrag widerrufen, haben wir Ihnen alle Zahlungen, die wir '
            . 'von Ihnen erhalten haben, unverzüglich und spätestens binnen vierzehn Tagen ab dem Tag zurückzuzahlen, an dem '
            . 'die Mitteilung über Ihren Widerruf dieses Vertrags bei uns eingegangen ist. Für diese Rückzahlung verwenden wir '
            . 'dasselbe Zahlungsmittel, das Sie bei der ursprünglichen Transaktion eingesetzt haben, es sei denn, mit Ihnen '
            . 'wurde ausdrücklich etwas anderes vereinbart; in keinem Fall werden Ihnen wegen dieser Rückzahlung Entgelte '
            . 'berechnet. Wir können die Rückzahlung verweigern, bis wir die Waren wieder zurückerhalten haben oder bis Sie '
            . 'den Nachweis erbracht haben, dass Sie die Waren zurückgesandt haben, je nachdem, welches der frühere Zeitpunkt ist.</p>'
            . '<p>Sie haben die Waren unverzüglich und in jedem Fall spätestens binnen vierzehn Tagen ab dem Tag, an dem Sie uns '
            . 'über den Widerruf dieses Vertrags unterrichten, an uns zurückzugeben' . ($adresse !== '' ? ' (' . $e($adresse) . ')' : '')
            . '. Die Frist ist gewahrt, wenn Sie die Waren vor Ablauf der Frist von vierzehn Tagen zurückbringen oder absenden. '
            . 'Sie tragen die unmittelbaren Kosten der Rückgabe der Waren. Sie müssen für einen etwaigen Wertverlust der Waren '
            . 'nur aufkommen, wenn dieser Wertverlust auf einen zur Prüfung der Beschaffenheit, Eigenschaften und '
            . 'Funktionsweise der Waren nicht notwendigen Umgang mit ihnen zurückzuführen ist.</p></div>'
            . '<div class="kasten"><b>Muster-Widerrufsformular</b>'
            . '<p class="klein">(Wenn Sie den Vertrag widerrufen wollen, dann füllen Sie bitte dieses Formular aus und senden Sie es zurück.)</p>'
            . '<p>An ' . $wir . ':</p>'
            . '<p>Hiermit widerrufe(n) ich/wir (*) den von mir/uns (*) abgeschlossenen Vertrag über den Kauf der folgenden Waren (*):</p>'
            . '<p>_______________________________________________________________</p>'
            . '<p>Bestellt am (*) / erhalten am (*): ____________________</p>'
            . '<p>Name des/der Verbraucher(s): ____________________</p>'
            . '<p>Anschrift des/der Verbraucher(s): ____________________</p>'
            . '<div class="unterschrift"><span>Datum</span><span>Unterschrift des/der Verbraucher(s) (nur bei Mitteilung auf Papier)</span></div>'
            . '<p class="klein">(*) Unzutreffendes streichen.</p></div>';
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
                       'Bezahlt_am', 'Firma', 'Strasse', 'PLZ', 'Ort', 'Besichtigung', 'Abholwunsch',
                       'Abholtermin', 'Abholung', 'Rechnungsnr', 'Rechnung_am', 'Abgeholt_am', 'Notiz'], ';');
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
                    $v['firma'] ?? '', $v['strasse'] ?? '', $v['plz'] ?? '', $v['ort'] ?? '',
                    Kikripp_Mail::besichtigung_text($v), Kikripp_Mail::abholung_text($v),
                    $v['abholtermin'] ?? '',
                    $v['abholung'] ?? '', $v['rechnungsnr'] ?? '', $v['rechnung_am'] ?? '', $v['abgeholt_am'] ?? '',
                    str_replace(["\r", "\n"], ' ', (string) ($v['notiz'] ?? '')),
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
        $bericht = self::einspielen($liste);
        self::zurueck('kikripp-import', self::import_meldung($bericht));
    }

    /**
     * Spielt die Artikelliste ein. Der ganze Import steckt hier – ohne Formular,
     * ohne Weiterleitung, ohne Ausgabe. Nur so kann der Kettentest genau den Code
     * prüfen, der später auch in WordPress läuft.
     *
     * Gibt einen Bericht zurück: neu, geaendert, ohne_bild, fehlende_fotos,
     * verschwunden, reserviert_entfernt.
     */
    public static function einspielen(array $liste) {
        // Eine alte Bildkarte aus einem abgebrochenen Lauf wäre eine Stunde lang gültig
        // und würde frisch hochgeladene Fotos übersehen. Deshalb hier neu aufbauen.
        delete_transient('kikripp_bilder');

        global $wpdb;
        $neu = $geaendert = $ohne_bild = $ohne_bild_versteckt = 0;
        $fehlende_fotos = [];
        $reserviert_entfernt = [];
        $belegung = Kikripp_DB::belegung();
        $gesehen = [];

        foreach ($liste as $i => $a) {
            if (empty($a['nr'])) { continue; }
            $artnr = sanitize_text_field((string) $a['nr']);
            $gesehen[] = $artnr;

            $bild = self::bild_url(isset($a['foto']) ? (string) $a['foto'] : '');
            // Gemeldet wird nur, was im Katalog auch zu sehen ist. Gestrichene Positionen
            // und die der zweiten Welle brauchen kein Foto in der Mediathek - sie als
            // "fehlend" zu melden, schickt die Nutzerin auf eine Suche ohne Anlass.
            $im_katalog = !empty($a['aktiv']) && !empty($a['im_katalog']);
            if ($bild === '') {
                if ($im_katalog) {
                    $ohne_bild++;
                    if (!empty($a['foto'])) { $fehlende_fotos[] = (string) $a['foto']; }
                } else {
                    $ohne_bild_versteckt++;
                }
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
                'mengenhinweis' => (string) ($a['mengenhinweis'] ?? ''),
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

        $fehlende_fotos = array_values(array_unique($fehlende_fotos));
        sort($fehlende_fotos);
        delete_transient('kikripp_bilder');

        return [
            'neu'                 => $neu,
            'geaendert'           => $geaendert,
            'ohne_bild'           => $ohne_bild,
            'ohne_bild_versteckt' => $ohne_bild_versteckt,
            'fehlende_fotos'      => $fehlende_fotos,
            'verschwunden'        => $verschwunden,
            'reserviert_entfernt' => array_values(array_unique($reserviert_entfernt)),
        ];
    }

    /** Aus dem Bericht den Satz bauen, der nach dem Import oben auf der Seite steht. */
    public static function import_meldung(array $b) {
        $meldung = sprintf('Import abgeschlossen: %d neu, %d aktualisiert.', $b['neu'], $b['geaendert']);
        if (!empty($b['verschwunden'])) {
            $meldung .= sprintf(' %d Artikel standen nicht mehr in der Datei und wurden aus dem '
                              . 'Katalog genommen (%s).', count($b['verschwunden']),
                              implode(', ', array_slice($b['verschwunden'], 0, 15)));
        }
        if ($b['ohne_bild'] > 0) {
            $meldung .= sprintf(' ACHTUNG: %d im Katalog sichtbare Artikel ohne gefundenes Foto. '
                . 'Diese Bilder fehlen in der Mediathek: %s%s', $b['ohne_bild'],
                implode(', ', array_slice($b['fehlende_fotos'], 0, 25)),
                count($b['fehlende_fotos']) > 25 ? ' … und weitere' : '.');
        } else {
            $meldung .= ' Jeder im Katalog sichtbare Artikel hat sein Foto gefunden.';
        }
        if (!empty($b['ohne_bild_versteckt'])) {
            $meldung .= sprintf(' (%d Positionen stehen nicht im Katalog und haben deshalb '
                . 'kein Foto in der Mediathek – das ist so gewollt.)',
                $b['ohne_bild_versteckt']);
        }
        if (!empty($b['reserviert_entfernt'])) {
            $meldung .= ' ACHTUNG: Diese Artikel wurden stillgelegt, haben aber noch Reservierungen: '
                      . implode(', ', array_slice($b['reserviert_entfernt'], 0, 15)) . '.';
        }
        return $meldung;
    }

    /** Foto in der Mediathek anhand des Dateinamens finden (F-001 -> Anhang). */
    /**
     * Schlüssel, unter dem ein Bild aus der Mediathek gefunden wird.
     *
     * Aus "F-001.jpg" wird "F-001". Lädt jemand dasselbe Bild ein zweites Mal hoch,
     * legt WordPress es als "F-001-1.jpg" ab - dieser Zusatz wird abgeschnitten,
     * damit das Foto trotzdem gefunden wird. Die Nummer des Fotos selbst darf dabei
     * nicht verlorengehen: "F-540" ist der Name, nicht "F" mit dem Zusatz "-540".
     *
     * Zweiter Rückgabewert: ob der Dateiname der genaue ist (ohne WordPress-Zusatz).
     * Bei Namensgleichheit gewinnt die genaue Datei.
     */
    public static function bild_schluessel($dateiname) {
        $datei = basename(trim((string) $dateiname));
        $name  = strtoupper(preg_replace('/\.[a-zA-Z0-9]+$/', '', $datei));
        if ($name === '') { return ['', false]; }
        if (preg_match('/^(F-\d{3,})-\d+$/', $name, $t)) { return [$t[1], false]; }
        return [$name, true];
    }

    private static function bild_url($fotoname) {
        $fotoname = trim($fotoname);
        if ($fotoname === '') { return ''; }
        $karte = get_transient('kikripp_bilder');
        if (!is_array($karte)) {
            $karte = [];
            // Ohne 'fields' => 'ids' legt WordPress die Beitraege und ihre Zusatzfelder
            // in zwei Abfragen in den Zwischenspeicher. Mit 'ids' waeren es stattdessen
            // zwei Abfragen je Bild - bei tausend Bildern in der Mediathek der
            // Unterschied zwischen einer Sekunde und einem Zeitueberschreitungsfehler.
            $anhaenge = get_posts([
                'post_type'      => 'attachment',
                'post_mime_type' => 'image',
                'posts_per_page' => -1,
                'post_status'    => 'inherit',
                'no_found_rows'  => true,
            ]);
            foreach ($anhaenge as $anhang) {
                $id = $anhang->ID;
                list($basis, $genau) = self::bild_schluessel(
                    (string) get_post_meta($id, '_wp_attached_file', true));
                if ($basis === '') { continue; }
                if ($genau || !isset($karte[$basis])) {
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

        printf('<tr><th scope="row">Passwortschutz</th><td>'
             . '<label><input type="checkbox" name="passwortschutz" value="1" %s> '
             . 'Katalog nur mit Passwort öffnen</label>'
             . '<p class="description">Seit Oktober 2026 ausgeschaltet: der Katalog ist frei zugänglich, '
             . 'erscheint aber nicht bei Google.</p></td></tr>',
             checked(1, (int) get_option('kikripp_passwortschutz', 1), false));

        printf('<tr><th scope="row"><label for="k_pw">Katalog-Passwort</label></th><td>'
             . '<input type="text" id="k_pw" name="passwort" class="regular-text" placeholder="leer lassen = unverändert">'
             . '<p class="description">Gilt nur bei eingeschaltetem Passwortschutz. Wird das Passwort geändert, müssen sich alle erneut anmelden.</p></td></tr>');

        printf('<tr><th scope="row"><label for="k_mail">Reservierungen melden an</label></th><td>'
             . '<input type="email" id="k_mail" name="mail_an" class="regular-text" value="%s" required>'
             . '<p class="description">Interne Benachrichtigung. Sie erreicht Interessenten '
             . 'nicht — dafür ist das Feld darunter da. Die Reservierungen stehen ohnehin '
             . 'vollständig auf dieser Seite.</p></td></tr>',
             esc_attr(get_option('kikripp_mail_an', '')));

        printf('<tr><th scope="row"><label for="k_kontakt">Kontaktadresse für Interessenten</label></th><td>'
             . '<input type="email" id="k_kontakt" name="kontakt_email" class="regular-text" value="%s">'
             . '<p class="description">Steht im Katalog unter dem Anbieter-Block und in der '
             . 'Bestätigung nach der Reservierung. Bleibt das Feld leer, gilt die Adresse '
             . 'von oben.</p></td></tr>',
             esc_attr(get_option('kikripp_kontakt_email', '')));
        printf('<tr><th scope="row"><label for="k_band">Hinweisband</label></th><td>'
             . '<input type="text" id="k_band" name="hinweisband" class="large-text" value="%s">'
             . '<p class="description">Erscheint als Band über dem Katalog. Zum Livegang das Feld leeren.</p></td></tr>',
             esc_attr(get_option('kikripp_hinweisband', '')));

        printf('<tr><th scope="row"><label for="k_frist">Reservierung gilt</label></th><td>'
             . '<input type="number" id="k_frist" name="frist_werktage" min="1" max="30" value="%d" class="small-text"> Werktage (Mo–Fr)'
             . '<p class="description">Danach wird der Artikel automatisch wieder frei – außer der Vorgang steht auf '
             . '„bestellt“ oder „bezahlt“.</p></td></tr>',
             Kikripp_DB::frist_werktage());

        printf('<tr><th scope="row"><label for="k_mindest">Mindestbestellwert</label></th><td>'
             . '<input type="number" id="k_mindest" name="mindestwert" min="0" step="1" value="%s" class="small-text"> €'
             . '<p class="description">Darunter lässt sich die Reservierung nicht abschicken. 0 = kein Mindestwert.</p></td></tr>',
             esc_attr(get_option('kikripp_mindestwert', 0)));

        printf('<tr><th scope="row"><label for="k_besicht">Besichtigung ab</label></th><td>'
             . '<input type="number" id="k_besicht" name="besichtigung_ab" min="0" step="1" value="%s" class="small-text"> € Stückpreis'
             . '<p class="description">Artikel ab diesem Preis tragen im Katalog „Besichtigung möglich“, und das '
             . 'Formular fragt nach einem Besichtigungstermin am Donnerstagvormittag.</p></td></tr>',
             esc_attr(get_option('kikripp_besichtigung_ab', 0)));

        printf('<tr><th scope="row"><label for="k_schluss">Abholung bis</label></th><td>'
             . '<input type="date" id="k_schluss" name="abholschluss" value="%s">'
             . '<p class="description">Letzter Abholtag. Das Formular bietet nur Montage und Dienstage bis dahin an.</p></td></tr>',
             esc_attr(get_option('kikripp_abholschluss', '')));

        printf('<tr><th scope="row"><label for="k_ablauf">So läuft es ab</label></th><td>'
             . '<textarea id="k_ablauf" name="ablauftext" class="large-text" rows="7">%s</textarea>'
             . '<p class="description">Erscheint als Kasten über den Artikeln. Jede Zeile wird ein Punkt.</p></td></tr>',
             esc_textarea(get_option('kikripp_ablauftext', '')));

        printf('<tr><th scope="row"><label for="k_ust">Umsatzsteuer</label></th><td>'
             . '<input type="number" id="k_ust" name="ust" min="0" max="30" step="0.1" value="%s" class="small-text"> %%'
             . '<p class="description">0 = steuerfreie Lieferung (§ 4 Nr. 28 UStG): der Katalog zeigt dann nur einen Preis.</p></td></tr>',
             esc_attr(get_option('kikripp_ust_prozent', 19)));

        printf('<tr><th scope="row"><label for="k_steuer">Steuerhinweis</label></th><td>'
             . '<input type="text" id="k_steuer" name="steuerhinweis" class="large-text" value="%s">'
             . '<p class="description">Steht unter jedem Preis, wenn die Umsatzsteuer auf 0 steht.</p></td></tr>',
             esc_attr(get_option('kikripp_steuerhinweis', '')));

        printf('<tr><th scope="row"><label for="k_firma">Verkäuferin (Firma)</label></th><td>'
             . '<input type="text" id="k_firma" name="firma" class="regular-text" value="%s" required>'
             . '<p class="description">Erscheint im Katalog, im Mailbetreff, im Anbieter-Block und auf der '
             . 'Bestellung. Bewusst hier und nicht der Name der Website.</p></td></tr>',
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
             . '<p class="description">Ebenfalls veröffentlicht und erreichbar.</p></td></tr>',
             esc_attr(get_option('kikripp_datenschutz_url', '')));

        printf('<tr><th scope="row"><label for="k_abhol">Abholadresse</label></th><td>'
             . '<input type="text" id="k_abhol" name="abholadresse" class="large-text" value="%s">'
             . '<p class="description">Steht in der Bestätigungsmail an den Interessenten und unter dem Katalog.</p></td></tr>',
             esc_attr(get_option('kikripp_abholadresse', '')));

        printf('<tr><th scope="row"><label for="k_zufahrt">Zufahrt</label></th><td>'
             . '<input type="text" id="k_zufahrt" name="zufahrt" class="large-text" value="%s">'
             . '<p class="description">Wegbeschreibung für die Mail an den Käufer („Mail schreiben“).</p></td></tr>',
             esc_attr(get_option('kikripp_zufahrt', '')));

        printf('<tr><th scope="row"><label for="k_mailname">Name in Mailvorlagen</label></th><td>'
             . '<input type="text" id="k_mailname" name="mail_name" class="regular-text" value="%s">'
             . '<p class="description">Steht unter den Mails an Käufer und unter der Zahlungserinnerung.</p></td></tr>',
             esc_attr(get_option('kikripp_mail_name', 'Jenny Preisigke')));

        printf('<tr><th scope="row"><label for="k_erinn">Erinnerung am Vortag um</label></th><td>'
             . '<input type="time" id="k_erinn" name="erinnerung_zeit" step="900" value="%s">'
             . '<p class="description">Uhrzeit des Outlook-Termins „Vorbereiten“ am Werktag vor der Abholung. '
             . 'Die Abholung selbst erinnert 15 Minuten vorher.</p></td></tr>',
             esc_attr(get_option('kikripp_erinnerung_zeit', '14:00')));

        printf('<tr><th scope="row"><label for="k_zahl">Zahlungserinnerung nach</label></th><td>'
             . '<input type="number" id="k_zahl" name="zahlung_tage" min="1" max="60" value="%d" style="width:70px"> Tagen'
             . '<p class="description">Ab dann steht ein unbezahlter Vorgang unter „Zu erledigen“ (gezählt ab Rechnungsdatum).</p></td></tr>',
             (int) get_option('kikripp_zahlung_tage', 5));

        printf('<tr><th scope="row"><label for="k_recht">Rechtliche Hinweise</label></th><td>'
             . '<textarea id="k_recht" name="rechtstext" class="large-text" rows="5">%s</textarea>'
             . '<p class="description">Erscheint unter dem Katalog als „Kaufbedingungen“ und auf jeder Bestellung. '
             . 'Leerzeilen trennen Absätze. Leer lassen blendet den Block aus.</p></td></tr>',
             esc_textarea(get_option('kikripp_rechtstext', '')));

        printf('<tr><th scope="row">Fußzeile ausblenden</th><td>'
             . '<label><input type="checkbox" name="fusszeile_aus" value="1" %s> '
             . 'Fußzeile der Website auf der Katalogseite nicht anzeigen</label>'
             . '<p class="description">Impressum und Datenschutz stehen dann nur im Anbieter-Block unter dem Katalog. '
             . 'Bleibt die Fußzeile trotzdem sichtbar, nutzt das Theme eine ungewöhnliche Auszeichnung – bitte melden.</p></td></tr>',
             checked(1, (int) get_option('kikripp_fusszeile_aus', 1), false));

        printf('<tr><th scope="row">Menü ausblenden</th><td>'
             . '<label><input type="checkbox" name="kopf_aus" value="1" %s> '
             . 'Menü und Social-Media-Symbole im Kopf der Website auf der Katalogseite nicht anzeigen</label>'
             . '<p class="description">Das Logo bleibt stehen. Auf den übrigen Seiten der Website ändern Sie das Menü unter '
             . 'Design → Editor → Header.</p></td></tr>',
             checked(1, (int) get_option('kikripp_kopf_aus', 1), false));

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
        update_option('kikripp_kontakt_email',
            sanitize_email(wp_unslash($_POST['kontakt_email'] ?? '')));
        update_option('kikripp_hinweisband', sanitize_text_field(wp_unslash($_POST['hinweisband'] ?? '')));
        update_option('kikripp_passwortschutz', isset($_POST['passwortschutz']) ? 1 : 0);
        update_option('kikripp_frist_werktage', max(1, (int) ($_POST['frist_werktage'] ?? 3)));
        update_option('kikripp_mindestwert', max(0, (float) ($_POST['mindestwert'] ?? 0)));
        update_option('kikripp_besichtigung_ab', max(0, (float) ($_POST['besichtigung_ab'] ?? 0)));
        $schluss = sanitize_text_field(wp_unslash($_POST['abholschluss'] ?? ''));
        update_option('kikripp_abholschluss', preg_match('/^\d{4}-\d{2}-\d{2}$/', $schluss) ? $schluss : '');
        update_option('kikripp_ablauftext', sanitize_textarea_field(wp_unslash($_POST['ablauftext'] ?? '')));
        update_option('kikripp_ust_prozent', (float) ($_POST['ust'] ?? 0));
        update_option('kikripp_steuerhinweis', sanitize_text_field(wp_unslash($_POST['steuerhinweis'] ?? '')));
        update_option('kikripp_vorschau', isset($_POST['vorschau']) ? 1 : 0);
        update_option('kikripp_fusszeile_aus', isset($_POST['fusszeile_aus']) ? 1 : 0);
        update_option('kikripp_kopf_aus', isset($_POST['kopf_aus']) ? 1 : 0);
        update_option('kikripp_abholadresse', sanitize_text_field(wp_unslash($_POST['abholadresse'] ?? '')));
        update_option('kikripp_zufahrt', sanitize_text_field(wp_unslash($_POST['zufahrt'] ?? '')));
        update_option('kikripp_mail_name', sanitize_text_field(wp_unslash($_POST['mail_name'] ?? '')));
        $erinn = sanitize_text_field(wp_unslash($_POST['erinnerung_zeit'] ?? ''));
        update_option('kikripp_erinnerung_zeit', preg_match('/^\d{2}:\d{2}$/', $erinn) ? $erinn : '14:00');
        update_option('kikripp_zahlung_tage', max(1, min(60, (int) ($_POST['zahlung_tage'] ?? 5))));
        update_option('kikripp_rechtstext', sanitize_textarea_field(wp_unslash($_POST['rechtstext'] ?? '')));
        update_option('kikripp_firma', sanitize_text_field(wp_unslash($_POST['firma'] ?? '')));
        update_option('kikripp_telefon', sanitize_text_field(wp_unslash($_POST['telefon'] ?? '')));
        update_option('kikripp_impressum_url', esc_url_raw(wp_unslash($_POST['impressum_url'] ?? '')));
        update_option('kikripp_datenschutz_url', esc_url_raw(wp_unslash($_POST['datenschutz_url'] ?? '')));
        self::zurueck('kikripp-einstellungen', 'Einstellungen gespeichert.'
            . ($pw !== '' ? ' Das Passwort wurde geändert – alle Besucher müssen sich neu anmelden.' : ''));
    }
}
