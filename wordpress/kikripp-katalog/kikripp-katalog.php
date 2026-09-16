<?php
/**
 * Plugin Name: Kikripp Artikelkatalog
 * Description: Passwortgeschützter Artikelkatalog mit Reservierung für die Betriebsauflösung der Kikripp GmbH. Artikel werden importiert, Reservierungen im Backend verwaltet.
 * Version:     1.0.0
 * Author:      Kikripp GmbH
 * Text Domain: kikripp-katalog
 * Requires at least: 5.8
 * Requires PHP: 7.4
 */

if (!defined('ABSPATH')) {
    exit;
}

define('KIKRIPP_VERSION', '1.0.0');
define('KIKRIPP_PFAD', plugin_dir_path(__FILE__));
define('KIKRIPP_URL', plugin_dir_url(__FILE__));

require_once KIKRIPP_PFAD . 'includes/class-kikripp-db.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-zugang.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-mail.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-rest.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-admin.php';
require_once KIKRIPP_PFAD . 'includes/class-kikripp-frontend.php';

register_activation_hook(__FILE__, ['Kikripp_DB', 'tabellen_anlegen']);

add_action('plugins_loaded', function () {
    Kikripp_DB::pruefe_version();
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
    add_option('kikripp_mail_an', 'jennyp@kikripp.de');
    add_option('kikripp_hinweisband', 'Vorschau – Artikel und Preise sind noch nicht vollständig.');
    add_option('kikripp_frist_tage', 7);
    add_option('kikripp_vorschau', 1);
    add_option('kikripp_ust_prozent', 19);
    add_option('kikripp_abholadresse', 'Kikripp GmbH, Hermann-Schwer-Str. 1, 78048 Villingen-Schwenningen');
    add_option('kikripp_rechtstext', 'Alle Artikel stammen aus der Auflösung unseres Kindergartens und sind gebraucht. Sie werden verkauft wie besichtigt; Abbildungen zeigen den tatsächlichen Zustand. Preise verstehen sich inklusive der gesetzlichen Umsatzsteuer. Eine Reservierung ist noch kein Kaufvertrag – dieser kommt erst bei der Abholung vor Ort zustande, ein Widerrufsrecht besteht daher nicht. Gegenüber Unternehmern ist die Gewährleistung ausgeschlossen; gegenüber Verbrauchern verjähren Ansprüche wegen Mängeln bei gebrauchten Sachen nach einem Jahr.');
});
