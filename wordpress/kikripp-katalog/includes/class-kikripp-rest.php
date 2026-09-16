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
            'hinweis'  => (string) get_option('kikripp_hinweisband', ''),
            'frist'    => (int) get_option('kikripp_frist_tage', 7),
            'admin'    => Kikripp_Zugang::ist_admin(),
            'recht'    => (string) get_option('kikripp_rechtstext', ''),
            'abholung' => (string) get_option('kikripp_abholadresse', ''),
            'absender' => [
                'firma'   => get_bloginfo('name'),
                'email'   => get_option('kikripp_mail_an', ''),
            ],
        ]));
    }

    public static function reservierung($anfrage) {
        if (!Kikripp_Zugang::hat_zugang()) {
            return self::ohne_cache(new WP_REST_Response(['ok' => false, 'gesperrt' => true], 401));
        }
        $kontakt = [
            'name'         => sanitize_text_field((string) $anfrage->get_param('name')),
            'email'        => sanitize_email((string) $anfrage->get_param('email')),
            'telefon'      => sanitize_text_field((string) $anfrage->get_param('telefon')),
            'wunschtermin' => sanitize_text_field((string) $anfrage->get_param('wunschtermin')),
            'nachricht'    => sanitize_textarea_field((string) $anfrage->get_param('nachricht')),
        ];
        if ($kontakt['name'] === '') {
            return self::ohne_cache(new WP_REST_Response([
                'ok' => false, 'meldung' => 'Bitte geben Sie Ihren Namen oder Ihre Firma an.'], 400));
        }
        if (!is_email($kontakt['email'])) {
            return self::ohne_cache(new WP_REST_Response([
                'ok' => false, 'meldung' => 'Bitte geben Sie eine gültige E-Mail-Adresse an.'], 400));
        }
        $wunsch = $anfrage->get_param('artikel');
        if (!is_array($wunsch)) { $wunsch = []; }

        $id = Kikripp_DB::reservieren($kontakt, $wunsch);
        if (is_wp_error($id)) {
            return self::ohne_cache(new WP_REST_Response([
                'ok' => false, 'meldung' => $id->get_error_message()], 409));
        }

        $mail = Kikripp_Mail::reservierung($id);
        Kikripp_Mail::bestaetigung($id);

        return self::ohne_cache(new WP_REST_Response([
            'ok'       => true,
            'vorgang'  => $id,
            'mail'     => (bool) $mail,
            'frist'    => (int) get_option('kikripp_frist_tage', 7),
            'artikel'  => Kikripp_DB::katalog_artikel(),   // aktualisierter Stand für die Anzeige
        ]));
    }
}
