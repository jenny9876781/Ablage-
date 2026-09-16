<?php
if (!defined('ABSPATH')) { exit; }

/** Ausgabe des Katalogs über den Kurzbefehl [kikripp_katalog]. */
class Kikripp_Frontend {

    public static function start() {
        add_shortcode('kikripp_katalog', [__CLASS__, 'ausgabe']);
        add_action('wp_head', [__CLASS__, 'kein_index']);
    }

    /** Die Katalogseite gehört nicht in Suchmaschinen. */
    public static function kein_index() {
        if (self::ist_katalogseite()) {
            echo '<meta name="robots" content="noindex, nofollow">' . "\n";
        }
    }

    private static function ist_katalogseite() {
        if (!is_singular()) { return false; }
        $post = get_post();
        return $post && has_shortcode((string) $post->post_content, 'kikripp_katalog');
    }

    public static function ausgabe($attribute = []) {
        wp_enqueue_style('kikripp-katalog', KIKRIPP_URL . 'assets/katalog.css', [], KIKRIPP_VERSION);
        wp_enqueue_script('kikripp-katalog', KIKRIPP_URL . 'assets/katalog.js', [], KIKRIPP_VERSION, true);
        wp_localize_script('kikripp-katalog', 'KIKRIPP', [
            'basis'   => esc_url_raw(rest_url(Kikripp_REST::NS)),
            'signet'  => KIKRIPP_URL . 'assets/signet.svg',
            'zugang'  => Kikripp_Zugang::hat_zugang(),
            'admin'   => Kikripp_Zugang::ist_admin(),
            'verwaltung' => admin_url('admin.php?page=kikripp-reservierungen'),
        ]);
        // Der Rahmen ist statisch und darf zwischengespeichert werden,
        // die Daten kommen live über die Schnittstelle.
        return '<div id="kikripp-katalog" class="kikripp"><noscript>'
             . '<p class="kikripp-hinweis">Für den Artikelkatalog muss JavaScript aktiviert sein.</p>'
             . '</noscript></div>';
    }
}
