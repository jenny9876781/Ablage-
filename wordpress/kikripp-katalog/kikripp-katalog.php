<?php
/**
 * Plugin Name: Kikripp Artikelkatalog
 * Description: Artikelkatalog mit Reservierung für die Betriebsauflösung der Kikripp GmbH. Artikel werden importiert, Reservierungen im Backend verwaltet.
 * Version:     1.2.2
 * Author:      Kikripp GmbH
 * Text Domain: kikripp-katalog
 * Requires at least: 5.8
 * Requires PHP: 7.4
 */

if (!defined('ABSPATH')) {
    exit;
}

define('KIKRIPP_VERSION', '1.2.2');
define('KIKRIPP_PFAD', plugin_dir_path(__FILE__));
define('KIKRIPP_URL', plugin_dir_url(__FILE__));

require_once KIKRIPP_PFAD . 'includes/kikripp-vorgaben.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-db.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-zugang.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-mail.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-rest.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-admin.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-frontend.php';

register_activation_hook(__FILE__, ['Kikripp_DB', 'tabellen_anlegen']);

add_action('plugins_loaded', function () {
    Kikripp_DB::pruefe_version();
    kikripp_umstellen();
    Kikripp_REST::start();
    Kikripp_Admin::start();
    Kikripp_Frontend::start();
});

/** Standardwerte beim ersten Aktivieren. */
register_activation_hook(__FILE__, function () {
    // Bewusst kein voreingestelltes Passwort: solange keins vergeben ist, lässt
    // Kikripp_Zugang::passwort_pruefen() niemanden durch. Das Passwort wird einmal
    // unter „Artikelkatalog → Einstellungen" gesetzt und steht in keiner Datei.
    add_option('kikripp_zugang_version', 1);
    // Zwei verschiedene Adressen, bewusst getrennt: die interne Meldung geht an ein
    // Postfach auf kikripp.de (dorthin stellt der Webserver ueberhaupt zu), die Adresse
    // fuer Interessenten ist die des Verkaufs.
    add_option('kikripp_mail_an', 'jennyp@kikripp.de');
    add_option('kikripp_kontakt_email', 'saldi4kids@outlook.com');
    // Kein Vorschau-Hinweis: der Katalog geht als fertiger Stand online. Das Band bleibt
    // leer, bis es einen echten Hinweis zu geben gibt (Wunsch der Nutzerin, 29.09.2026).
    add_option('kikripp_hinweisband', '');
    add_option('kikripp_vorschau', 1);
    add_option('kikripp_abholadresse', 'Kikripp GmbH, Hermann-Schwer-Str. 1, 78048 Villingen-Schwenningen');
    add_option('kikripp_firma', 'Kikripp GmbH');
    add_option('kikripp_telefon', '07725 5179702');
    // Der Katalog laeuft auf kikripp.de, die beiden Seiten liegen dort. Beim Aktivieren
    // muessen sie veroeffentlicht sein – als Entwurf sind sie oeffentlich nicht erreichbar
    // und der Anbieter-Block unter dem Katalog zeigt ins Leere.
    add_option('kikripp_impressum_url', 'https://www.kikripp.de/impressum/');
    add_option('kikripp_datenschutz_url', 'https://www.kikripp.de/datenschutz/');
    foreach (kikripp_vorgaben_120() as $name => $wert) { add_option($name, $wert); }
    add_option('kikripp_plugin_version', KIKRIPP_VERSION);
});

/**
 * Einmalige Umstellung einer bestehenden Einrichtung auf die Fassung 1.2.0.
 *
 * Beim Ersetzen des Plugins läuft der Aktivierungshaken nicht – die neuen Vorgaben
 * kämen sonst nie an, und der Katalog zeigte weiter Preise mit 19 % USt und den alten
 * Rechtstext. Was die Nutzerin danach in den Einstellungen ändert, bleibt: die
 * Umstellung läuft genau einmal. Das Hinweisband wird nur gefüllt, wenn es leer ist.
 */
function kikripp_umstellen() {
    $stand = (string) get_option('kikripp_plugin_version', '1.0.0');
    if (version_compare($stand, '1.2.0', '>=')) {
        kikripp_umstellen_122($stand);
        return;
    }
    foreach (kikripp_vorgaben_120() as $name => $wert) { update_option($name, $wert); }
    if (trim((string) get_option('kikripp_hinweisband', '')) === '') {
        update_option('kikripp_hinweisband', 'Ein Großteil unseres Spielzeugs kommt im November dazu – '
            . 'schauen Sie gern wieder vorbei. Der Katalog wird wöchentlich aktualisiert.');
    }
    update_option('kikripp_plugin_version', '1.2.2');
}

/**
 * 1.2.2: kürzerer Ablauftext als Fließtext. Ersetzt wird nur, wenn noch der Text von 1.2.0
 * drinsteht – was die Nutzerin selbst geändert hat, bleibt.
 */
function kikripp_umstellen_122($stand) {
    if (version_compare($stand, '1.2.2', '>=')) { return; }
    $jetzt = str_replace("\r", '', (string) get_option('kikripp_ablauftext', ''));
    if (trim($jetzt) === trim(kikripp_ablauf_120())) {
        update_option('kikripp_ablauftext', kikripp_ablauf_122());
    }
    update_option('kikripp_plugin_version', '1.2.2');
}
