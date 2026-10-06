<?php
if (!defined('ABSPATH')) { exit; }

/** Schnittstelle für die Katalogseite. Antworten werden nie zwischengespeichert. */
class Kikripp_REST {

    const NS = 'kikripp/v1';

    public static function start() {
        add_action('rest_api_init', [__CLASS__, 'routen']);
    }

    public static function routen() {
        register_rest_route(self::NS, '/zugang', [
            'methods'             => 'POST',
            'callback'            => [__CLASS__, 'zugang'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::NS, '/artikel', [
            'methods'             => 'GET',
            'callback'            => [__CLASS__, 'artikel'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::NS, '/reservierung', [
            'methods'             => 'POST',
            'callback'            => [__CLASS__, 'reservierung'],
            'permission_callback' => '__return_true',
        ]);
    }

    private static function ohne_cache($antwort) {
        $antwort->header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
        $antwort->header('Pragma', 'no-cache');
        return $antwort;
    }

    /** Anmeldung mit dem gemeinsamen Passwort, mit Bremse gegen Durchprobieren. */
    public static function zugang($anfrage) {
        $ip = substr((string) ($_SERVER['REMOTE_ADDR'] ?? 'unbekannt'), 0, 45);
        $schluessel = 'kikripp_versuche_' . md5($ip);
        $versuche = (int) get_transient($schluessel);
        if ($versuche >= 10) {
            return self::ohne_cache(new WP_REST_Response([
                'ok' => false,
                'meldung' => 'Zu viele Fehlversuche. Bitte in 15 Minuten noch einmal probieren.',
            ], 429));
        }
        $passwort = (string) $anfrage->get_param('passwort');
        if (Kikripp_Zugang::passwort_pruefen(trim($passwort))) {
            delete_transient($schluessel);
            Kikripp_Zugang::keks_setzen();
            return self::ohne_cache(new WP_REST_Response(['ok' => true]));
        }
        set_transient($schluessel, $versuche + 1, 15 * MINUTE_IN_SECONDS);
        return self::ohne_cache(new WP_REST_Response([
            'ok' => false,
            'meldung' => 'Passwort falsch. Bitte noch einmal versuchen.',
        ], 401));
    }

    public static function artikel($anfrage) {
        if (!Kikripp_Zugang::hat_zugang()) {
            return self::ohne_cache(new WP_REST_Response(['ok' => false, 'gesperrt' => true], 401));
        }
        return self::ohne_cache(new WP_REST_Response([
            'ok'       => true,
            'artikel'  => Kikripp_DB::katalog_artikel(),
            'ust'      => (float) get_option('kikripp_ust_prozent', 19) / 100,
            'steuer'   => (string) get_option('kikripp_steuerhinweis', ''),
            'hinweis'  => (string) get_option('kikripp_hinweisband', ''),
            'frist'    => Kikripp_DB::frist_werktage(),
            'ablauf'   => (string) get_option('kikripp_ablauftext', ''),
            'mindestwert'     => (float) get_option('kikripp_mindestwert', 0),
            'besichtigung_ab' => (float) get_option('kikripp_besichtigung_ab', 0),
            'abholschluss'    => (string) get_option('kikripp_abholschluss', ''),
            'heute'    => substr(current_time('mysql'), 0, 10),
            'admin'    => Kikripp_Zugang::ist_admin(),
            'recht'    => (string) get_option('kikripp_rechtstext', ''),
            'abholung' => (string) get_option('kikripp_abholadresse', ''),
            'anbieter' => [
                'firma'       => (string) get_option('kikripp_firma', 'Kikripp GmbH'),
                'adresse'     => (string) get_option('kikripp_abholadresse', ''),
                'telefon'     => (string) get_option('kikripp_telefon', ''),
                'email'       => self::kontakt_email(),
                'impressum'   => (string) get_option('kikripp_impressum_url', ''),
                'datenschutz' => (string) get_option('kikripp_datenschutz_url', ''),
            ],
        ]));
    }

    /**
     * Die Adresse, die Interessenten sehen — im Anbieter-Block und in der Bestätigung.
     *
     * Bewusst getrennt von `kikripp_mail_an`: dorthin geht die interne Benachrichtigung,
     * und das muss nicht dieselbe Adresse sein. Auf kikripp.de ist es das auch nicht —
     * der Webserver stellt nur an die eigene Domain zu, geantwortet wird aber aus einem
     * anderen Postfach. Ist das Feld leer, gilt weiter die Meldeadresse; so ändert sich
     * für eine bestehende Einrichtung nichts, solange niemand etwas einträgt.
     */
    public static function kontakt_email() {
        $eigen = trim((string) get_option('kikripp_kontakt_email', ''));
        return $eigen !== '' ? $eigen : (string) get_option('kikripp_mail_an', '');
    }

    /** Halbstündliche Besichtigungszeiten am Donnerstagvormittag. */
    const BESICHTIGUNG_ZEITEN = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30'];

    private static function fehler($meldung, $code = 400) {
        return self::ohne_cache(new WP_REST_Response(['ok' => false, 'meldung' => $meldung], $code));
    }

    /** Datum JJJJ-MM-TT prüfen; gibt den Zeitstempel (12 Uhr UTC) zurück oder 0. */
    private static function datum($text) {
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) $text)) { return 0; }
        $t = strtotime($text . ' 12:00:00 UTC');
        return ($t && gmdate('Y-m-d', $t) === $text) ? $t : 0;
    }

    /**
     * Schutz gegen Formular-Roboter, seit der Katalog ohne Passwort erreichbar ist:
     * ein unsichtbares Feld, das Menschen nicht ausfüllen, eine Mindestzeit zwischen
     * Öffnen und Abschicken und höchstens fünf Reservierungen je Stunde und Anschluss.
     * Gespeichert wird dafür nur eine Prüfsumme der Adresse für eine Stunde, nichts am Vorgang.
     */
    private static function sieht_nach_roboter_aus($anfrage) {
        if (trim((string) $anfrage->get_param('webseite')) !== '') { return true; }
        $dauer = (int) $anfrage->get_param('dauer');
        if ($dauer > 0 && $dauer < 3000) { return true; }
        return false;
    }

    private static function zu_viele($zaehlen) {
        $ip = substr((string) ($_SERVER['REMOTE_ADDR'] ?? 'unbekannt'), 0, 45);
        $schluessel = 'kikripp_res_' . md5($ip);
        $n = (int) get_transient($schluessel);
        if ($zaehlen) { set_transient($schluessel, $n + 1, HOUR_IN_SECONDS); }
        return $n >= 5;
    }

    public static function reservierung($anfrage) {
        if (!Kikripp_Zugang::hat_zugang()) {
            return self::ohne_cache(new WP_REST_Response(['ok' => false, 'gesperrt' => true], 401));
        }
        if (self::sieht_nach_roboter_aus($anfrage)) {
            return self::fehler('Die Reservierung konnte nicht verarbeitet werden. Bitte versuchen Sie es erneut.');
        }
        if (self::zu_viele(false)) {
            return self::fehler('Von diesem Anschluss sind in der letzten Stunde schon mehrere Reservierungen '
                . 'eingegangen. Bitte rufen Sie uns an.', 429);
        }
        $text = function ($n) use ($anfrage) { return sanitize_text_field((string) $anfrage->get_param($n)); };
        $kontakt = [
            'name'      => $text('name'),
            'firma'     => $text('firma'),
            'strasse'   => $text('strasse'),
            'plz'       => $text('plz'),
            'ort'       => $text('ort'),
            'email'     => sanitize_email((string) $anfrage->get_param('email')),
            'telefon'   => $text('telefon'),
            'nachricht' => sanitize_textarea_field((string) $anfrage->get_param('nachricht')),
            'demontage' => !empty($anfrage->get_param('demontage')),
        ];
        if ($kontakt['name'] === '') { return self::fehler('Bitte geben Sie Ihren Namen an.'); }
        if ($kontakt['strasse'] === '' || $kontakt['ort'] === '' || !preg_match('/^\d{4,5}$/', $kontakt['plz'])) {
            return self::fehler('Bitte geben Sie Ihre vollständige Anschrift an (Straße, Postleitzahl, Ort) – '
                . 'sie wird für die Rechnung gebraucht.');
        }
        if (!is_email($kontakt['email'])) { return self::fehler('Bitte geben Sie eine gültige E-Mail-Adresse an.'); }
        // Telefon ist Pflicht: nach der Reservierung rufen wir an.
        if (strlen(preg_replace('/\D/', '', $kontakt['telefon'])) < 6) {
            return self::fehler('Bitte geben Sie eine Telefonnummer an, unter der wir Sie erreichen.');
        }

        $wunsch = $anfrage->get_param('artikel');
        if (!is_array($wunsch)) { $wunsch = []; }
        // Preise für Mindestbestellwert und Besichtigung kommen aus der Datenbank, nie vom Browser.
        $summe = 0.0; $teuerster = 0.0;
        foreach (Kikripp_DB::katalog_artikel() as $a) {
            if (!empty($wunsch[$a['nr']]) && (int) $wunsch[$a['nr']] > 0) {
                $summe += (int) $wunsch[$a['nr']] * (float) $a['preis'];
                $teuerster = max($teuerster, (float) $a['preis']);
            }
        }
        $mindest = (float) get_option('kikripp_mindestwert', 0);
        if ($summe > 0 && $summe < $mindest) {
            return self::fehler(sprintf('Der Mindestbestellwert beträgt %s. Ihre Auswahl liegt bei %s.',
                Kikripp_Mail::eur($mindest), Kikripp_Mail::eur($summe)));
        }

        $heute = self::datum(substr(current_time('mysql'), 0, 10));
        $schluss = self::datum((string) get_option('kikripp_abholschluss', '')) ?: PHP_INT_MAX;

        // Besichtigung: nur bei Artikeln ab der Grenze, nur donnerstags, halbstündlich 8 bis 10:30 Uhr
        $kontakt['besichtigung'] = '';
        $ab = (float) get_option('kikripp_besichtigung_ab', 0);
        if (!empty($anfrage->get_param('besichtigung')) && $teuerster >= $ab) {
            $tag = self::datum((string) $anfrage->get_param('besichtigung_tag'));
            $zeit = (string) $anfrage->get_param('besichtigung_zeit');
            if (!$tag || (int) gmdate('N', $tag) !== 4 || $tag < $heute || $tag > $schluss
                || !in_array($zeit, self::BESICHTIGUNG_ZEITEN, true)) {
                return self::fehler('Bitte wählen Sie für die Besichtigung einen Donnerstag und eine Uhrzeit '
                    . 'zwischen 08:00 und 10:30 Uhr.');
            }
            $kontakt['besichtigung'] = gmdate('Y-m-d', $tag) . ' ' . $zeit;
        }

        // Abholwunsch: Montag oder Dienstag bis zum Abholschluss. Bei Demontage nach Vereinbarung.
        $kontakt['abholwunsch'] = '';
        $abhol = (string) $anfrage->get_param('abholwunsch');
        if ($abhol !== '') {
            $t = self::datum($abhol);
            if (!$t || !in_array((int) gmdate('N', $t), [1, 2], true) || $t < $heute || $t > $schluss) {
                return self::fehler('Abgeholt werden kann montags und dienstags bis zum '
                    . ($schluss < PHP_INT_MAX ? gmdate('d.m.Y', $schluss) : 'Ende des Verkaufs') . '.');
            }
            $kontakt['abholwunsch'] = gmdate('Y-m-d', $t);
        } elseif (!$kontakt['demontage']) {
            return self::fehler('Bitte wählen Sie einen Wunschtermin für die Abholung (montags oder dienstags) '
                . 'oder kreuzen Sie an, dass eine Demontage nötig ist.');
        }

        $id = Kikripp_DB::reservieren($kontakt, $wunsch);
        if (is_wp_error($id)) {
            return self::fehler($id->get_error_message(), 409);
        }
        self::zu_viele(true);

        // Die Mail an die Kikripp GmbH ist die einzige, die rausgeht. Die Kontaktdaten
        // bleiben in der Verwaltung, bis dort jemand „erledigt“ klickt.
        $mail = Kikripp_Mail::reservierung($id);
        $v = Kikripp_DB::vorgang($id);

        return self::ohne_cache(new WP_REST_Response([
            'ok'       => true,
            'vorgang'  => $id,
            'mail'     => (bool) $mail,
            'frist'    => Kikripp_DB::frist_werktage(),
            'bis'      => $v ? substr((string) $v['ablauf'], 0, 10) : '',
            'kontakt'  => ['email' => $kontakt['email'], 'telefon' => $kontakt['telefon']],
            'artikel'  => Kikripp_DB::katalog_artikel(),   // aktualisierter Stand für die Anzeige
        ]));
    }
}
