<?php
if (!defined('ABSPATH')) { exit; }

/** Ausgabe des Katalogs über den Kurzbefehl [kikripp_katalog]. */
class Kikripp_Frontend {

    public static function start() {
        add_shortcode('kikripp_katalog', [__CLASS__, 'ausgabe']);
        add_action('wp_head', [__CLASS__, 'kein_index']);
        add_filter('body_class', [__CLASS__, 'body_klasse']);
        add_filter('wpseo_robots', [__CLASS__, 'yoast_robots']);
        add_filter('wpseo_robots_array', [__CLASS__, 'yoast_robots']);
        // Zustimmungsbanner wie CookieYes blockieren fremde Skripte. Unser eigenes
        // ist technisch notwendig – das markieren wir ausdrücklich.
        add_filter('script_loader_tag', [__CLASS__, 'skript_notwendig'], 10, 2);
        // Autoptimize fasst JavaScript und CSS aller Seiten zu Sammeldateien zusammen.
        // Dabei ändert sich die Reihenfolge, und der Katalog bleibt leer. Statt die
        // Nutzerin das in den Einstellungen eintragen zu lassen, tragen wir uns selbst
        // in die Ausschlussliste ein – alle unsere Dateien heißen „kikripp…“.
        add_filter('autoptimize_filter_js_exclude', [__CLASS__, 'nicht_zusammenfassen']);
        add_filter('autoptimize_filter_css_exclude', [__CLASS__, 'nicht_zusammenfassen']);
        // Muss vor jeder Ausgabe laufen, damit das Passwort aus dem Link
        // sofort wieder aus der Adresse verschwindet.
        add_action('init', ['Kikripp_Zugang', 'link_einloesen']);
    }

    /**
     * Die Katalogseite gehört nicht in Suchmaschinen.
     *
     * Ist Yoast SEO aktiv, setzt es selbst eine robots-Angabe. Zwei solche
     * Angaben auf einer Seite sind unzuverlässig, deshalb hängen wir uns dort
     * in den Filter ein statt eine zweite Zeile zu schreiben.
     */
    public static function kein_index() {
        if (!self::ist_katalogseite()) { return; }
        echo '<meta name="referrer" content="same-origin">' . "\n";
        if (!self::yoast_aktiv()) {
            echo '<meta name="robots" content="noindex, nofollow">' . "\n";
        }
    }

    /**
     * Kennzeichnet die Katalogseite am <body>. Daran hängt in katalog.css das Ausblenden
     * der Fußzeile der Website: sie nennt die frühere Betreiberin, und Impressum und
     * Datenschutz der Verkäuferin stehen ohnehin im Anbieter-Block unter dem Katalog.
     */
    public static function body_klasse($klassen) {
        if (self::ist_katalogseite() && (int) get_option('kikripp_fusszeile_aus', 1) === 1) {
            $klassen[] = 'kikripp-ohne-fusszeile';
        }
        // Menü und Social-Media-Symbole im Kopf führen auf die alten Seiten der früheren Betreiberin.
        if (self::ist_katalogseite() && (int) get_option('kikripp_kopf_aus', 1) === 1) {
            $klassen[] = 'kikripp-ohne-menue';
        }
        return $klassen;
    }

    private static function yoast_aktiv() {
        return defined('WPSEO_VERSION');
    }

    /** Yoast: robots-Angabe für die Katalogseite überschreiben. */
    public static function yoast_robots($robots) {
        if (!self::ist_katalogseite()) { return $robots; }
        if (is_array($robots)) {
            $robots['index'] = 'noindex';
            $robots['follow'] = 'nofollow';
            return $robots;
        }
        return 'noindex, nofollow';
    }

    private static function ist_katalogseite() {
        if (!is_singular()) { return false; }
        $post = get_post();
        return $post && has_shortcode((string) $post->post_content, 'kikripp_katalog');
    }

    /**
     * Hängt „kikripp" an die Ausschlussliste von Autoptimize an.
     *
     * Die Liste ist eine kommagetrennte Zeichenkette. Was die Nutzerin dort selbst
     * eingetragen hat, bleibt stehen; ein doppelter Eintrag wird vermieden.
     */
    public static function nicht_zusammenfassen($ausschluss) {
        $liste = is_array($ausschluss) ? $ausschluss : explode(',', (string) $ausschluss);
        $liste = array_map('trim', $liste);
        if (!in_array('kikripp', $liste, true)) { $liste[] = 'kikripp'; }
        $liste = array_values(array_filter($liste, static function ($e) { return $e !== ''; }));
        return is_array($ausschluss) ? $liste : implode(', ', $liste);
    }

    public static function skript_notwendig($tag, $handle) {
        if ($handle !== 'kikripp-katalog') { return $tag; }
        return str_replace('<script ', '<script data-cookieyes="cookieyes-necessary" ', $tag);
    }

    public static function ausgabe($attribute = []) {
        wp_enqueue_style('kikripp-katalog', KIKRIPP_URL . 'assets/katalog.css', [], KIKRIPP_VERSION);
        wp_enqueue_script('kikripp-katalog', KIKRIPP_URL . 'assets/katalog.js', [], KIKRIPP_VERSION, true);
        // Der Rahmen ist statisch, aber `zugang` hängt am Keks des Besuchers.
        // Ein Seiten-Cache würde den Zustand eines Fremden ausliefern.
        if (!defined('DONOTCACHEPAGE')) { define('DONOTCACHEPAGE', true); }
        // W3 Total Cache und andere Cache-Plugins verkleinern und bündeln JavaScript
        // ebenfalls. Diese Konstante schaltet das für die Katalogseite ab.
        if (!defined('DONOTMINIFY')) { define('DONOTMINIFY', true); }

        wp_localize_script('kikripp-katalog', 'KIKRIPP', [
            'basis'   => esc_url_raw(rest_url(Kikripp_REST::NS)),
            'signet'  => KIKRIPP_URL . 'assets/signet.svg',
            'zugang'  => Kikripp_Zugang::hat_zugang(),
            'admin'   => Kikripp_Zugang::ist_admin(),
            'verwaltung' => admin_url('admin.php?page=kikripp-reservierungen'),
            'linkparam'  => Kikripp_Zugang::LINK_PARAMETER,
        ]);
        // Der Rahmen ist statisch und darf zwischengespeichert werden,
        // die Daten kommen live über die Schnittstelle.
        return '<div id="kikripp-katalog" class="kikripp"><noscript>'
             . '<p class="kikripp-hinweis">Für den Artikelkatalog muss JavaScript aktiviert sein.</p>'
             . '</noscript></div>';
    }
}
