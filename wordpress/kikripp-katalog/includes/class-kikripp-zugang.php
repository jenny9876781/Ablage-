<?php
if (!defined('ABSPATH')) { exit; }

/**
 * Zugang zum Katalog über ein gemeinsames Passwort.
 * Geprüft wird serverseitig; der Browser bekommt nur einen signierten Keks,
 * der nichts über das Passwort verrät. Ein Passwortwechsel erhöht die
 * Zugangsversion und macht damit alle alten Kekse ungültig.
 */
class Kikripp_Zugang {

    const KEKS = 'kikripp_zugang';

    public static function version() {
        return (int) get_option('kikripp_zugang_version', 1);
    }

    private static function marke() {
        return hash_hmac('sha256', 'kikripp-zugang|' . self::version(), wp_salt('auth'));
    }

    /**
     * Passwort aus dem Link (?k=…) einlösen.
     *
     * Läuft früh auf `init`, also bevor irgendein HTML oder eine externe
     * Ressource geladen wird — danach wird auf dieselbe Adresse ohne den
     * Parameter weitergeleitet. So steht das Passwort weder in der Adresszeile
     * noch im Verlauf, und es kann über keinen Verweis nach außen gelangen.
     */
    public static function link_einloesen() {
        if (is_admin() || empty($_GET['k'])) { return; }
        $pw = trim(wp_unslash((string) $_GET['k']));
        $ip = substr((string) ($_SERVER['REMOTE_ADDR'] ?? 'unbekannt'), 0, 45);
        $schluessel = 'kikripp_versuche_' . md5($ip);
        if ((int) get_transient($schluessel) < 10 && self::passwort_pruefen($pw)) {
            delete_transient($schluessel);
            self::keks_setzen();
        } else {
            set_transient($schluessel, (int) get_transient($schluessel) + 1, 15 * MINUTE_IN_SECONDS);
        }
        wp_safe_redirect(remove_query_arg('k'));
        exit;
    }

    public static function passwort_pruefen($passwort) {
        $hash = get_option('kikripp_passwort_hash');
        if (!$hash) { return false; }
        return wp_check_password((string) $passwort, $hash);
    }

    public static function passwort_setzen($passwort) {
        update_option('kikripp_passwort_hash', wp_hash_password((string) $passwort));
        update_option('kikripp_zugang_version', self::version() + 1);   // alte Kekse ungültig
    }

    public static function keks_setzen() {
        // Damit der Zugang schon in diesem Aufruf gilt und nicht erst beim nächsten.
        $_COOKIE[self::KEKS] = self::marke();
        if (headers_sent()) { return; }
        setcookie(self::KEKS, self::marke(), [
            'expires'  => time() + 30 * DAY_IN_SECONDS,
            'path'     => COOKIEPATH ? COOKIEPATH : '/',
            'secure'   => is_ssl(),
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        $_COOKIE[self::KEKS] = self::marke();
    }

    public static function keks_loeschen() {
        setcookie(self::KEKS, '', time() - 3600, COOKIEPATH ? COOKIEPATH : '/');
        unset($_COOKIE[self::KEKS]);
    }

    /** Angemeldete Redakteure kommen immer rein, alle anderen über den Keks. */
    public static function hat_zugang() {
        if (current_user_can('edit_posts')) { return true; }
        $keks = isset($_COOKIE[self::KEKS]) ? (string) $_COOKIE[self::KEKS] : '';
        return $keks !== '' && hash_equals(self::marke(), $keks);
    }

    public static function ist_admin() {
        return current_user_can('manage_options');
    }
}
