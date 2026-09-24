<?php
/** Testserver: bedient die echten REST-Rückrufe des Plugins über eine SQLite-Attrappe. */
$GLOBALS['ATTRAPPE_DB'] = '/tmp/kikripp-web.sqlite';
$GLOBALS['MAIL_MITSCHRIFT'] = '/tmp/kikripp-mails.log';
require __DIR__ . '/wp-attrappe.php';

class WP_REST_Response {
    public $data; public $status; public $kopf = [];
    public function __construct($data = null, $status = 200) { $this->data = $data; $this->status = $status; }
    public function header($n, $w) { $this->kopf[$n] = $w; }
    public function get_data() { return $this->data; }
    public function get_status() { return $this->status; }
}
class WP_REST_Request {
    private $p;
    public function __construct($p) { $this->p = $p; }
    public function get_param($n) { return $this->p[$n] ?? null; }
}
function register_rest_route() {}
function add_action() {}
function add_filter() {}
function add_shortcode() {}
function rest_url($n) { return '/wp-json/' . $n; }
function esc_url_raw($u) { return $u; }
function wp_enqueue_style() {}
function wp_enqueue_script() {}
function wp_localize_script() {}
function has_shortcode() { return true; }
function is_singular() { return true; }
function get_post() { return null; }
function plugin_dir_path($f) { return dirname($f) . '/'; }
function plugin_dir_url($f) { return '/'; }

define('KIKRIPP_VERSION', 'test');
define('KIKRIPP_URL', '/');
$basis = __DIR__ . '/../kikripp-katalog/';
require $basis . 'includes/class-kikripp-db.php';
require $basis . 'includes/class-kikripp-zugang.php';
require $basis . 'includes/class-kikripp-mail.php';
require $basis . 'includes/class-kikripp-rest.php';

function dbDelta($sql) {
    global $wpdb;
    foreach (array_filter(array_map('trim', explode(';', $sql))) as $t) { $wpdb->query($t . ';'); }
}

// ---- einmalige Einrichtung -------------------------------------------------
if (!file_exists($GLOBALS['ATTRAPPE_DB']) || filesize($GLOBALS['ATTRAPPE_DB']) === 0) {
    Kikripp_DB::tabellen_anlegen();
}
$zustand = '/tmp/kikripp-optionen.json';
if (file_exists($zustand)) {
    $GLOBALS['optionen'] = json_decode(file_get_contents($zustand), true) ?: [];
}
if (empty($GLOBALS['optionen'])) {
    $GLOBALS['optionen'] = [
        'kikripp_passwort_hash' => wp_hash_password(getenv('KIK_TEST_PW') ?: 'test-passwort'),
        'kikripp_zugang_version' => 1,
        'kikripp_mail_an' => 'jennyp@kikripp.de',
        'kikripp_hinweisband' => 'Vorschau – Artikel und Preise sind noch nicht vollständig.',
        'kikripp_frist_tage' => 7,
        'kikripp_vorschau' => 1,
        'kikripp_ust_prozent' => 19,
        'kikripp_firma' => 'Kikripp GmbH',
        'kikripp_telefon' => '07725 5179702',
        'kikripp_impressum_url' => 'https://www.kikripp.de/impressum/',
        'kikripp_datenschutz_url' => 'https://www.kikripp.de/datenschutz/',
        'kikripp_abholadresse' => 'Kikripp GmbH, Hermann-Schwer-Str. 1, 78048 Villingen-Schwenningen',
        'kikripp_rechtstext' => 'Alle Artikel stammen aus der Auflösung unseres Kindergartens und sind gebraucht. Sie werden verkauft wie besichtigt; Abbildungen zeigen den tatsächlichen Zustand. Preise verstehen sich inklusive der gesetzlichen Umsatzsteuer. Eine Reservierung ist noch kein Kaufvertrag – dieser kommt erst bei der Abholung vor Ort zustande, ein Widerrufsrecht besteht daher nicht. Gegenüber Unternehmern ist die Gewährleistung ausgeschlossen; gegenüber Verbrauchern verjähren Ansprüche wegen Mängeln bei gebrauchten Sachen nach einem Jahr.',
    ];
    file_put_contents($zustand, json_encode($GLOBALS['optionen']));
}

global $wpdb;
if ((int) $wpdb->get_var('SELECT COUNT(*) FROM ' . Kikripp_DB::t_artikel()) === 0) {
    $daten = json_decode(file_get_contents(__DIR__ . '/../../ausgabe/katalog_import.json'), true);
    foreach ($daten as $i => $a) {
        $wpdb->insert(Kikripp_DB::t_artikel(), [
            'artnr' => $a['nr'], 'sortierung' => $i, 'menge' => $a['menge'],
            'preis_netto' => $a['preis'], 'aktiv' => $a['aktiv'] ? 1 : 0,
            'im_katalog' => $a['im_katalog'] ? 1 : 0,
            'daten' => wp_json_encode([
                'nr' => $a['nr'], 'titel' => $a['titel'], 'beschr' => $a['beschr'],
                'kat' => $a['kat'], 'raum' => $a['raum'], 'zustand' => $a['zustand'],
                'masse' => $a['masse'], 'einheit' => $a['einheit'], 'basis' => $a['basis'],
                'versand' => $a['versand'], 'marke' => $a['marke'] ?? '', 'buendel' => $a['buendel'] ?? '',
                'mengenhinweis' => $a['mengenhinweis'] ?? '', 'foto' => $a['foto'],
                'bild' => '/fotos/' . $a['foto'] . '.jpg',
            ]),
            'aktualisiert' => current_time('mysql'),
        ]);
    }
}

// ---- Auslieferung ----------------------------------------------------------
// Passwort aus dem Link einlösen – genau wie das Plugin es auf `init` tut.
Kikripp_Zugang::link_einloesen();

$pfad = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);

if (strpos($pfad, '/wp-json/kikripp/v1/') === 0) {
    $route = substr($pfad, strlen('/wp-json/kikripp/v1/'));
    $koerper = json_decode(file_get_contents('php://input'), true) ?: [];
    $anfrage = new WP_REST_Request($koerper);
    $antwort = null;
    if ($route === 'zugang')            { $antwort = Kikripp_REST::zugang($anfrage); }
    elseif ($route === 'artikel')       { $antwort = Kikripp_REST::artikel($anfrage); }
    elseif ($route === 'reservierung')  { $antwort = Kikripp_REST::reservierung($anfrage); }
    if ($antwort === null) { http_response_code(404); echo '{}'; exit; }
    http_response_code($antwort->get_status());
    header('Content-Type: application/json; charset=utf-8');
    foreach ($antwort->kopf as $n => $w) { header("$n: $w"); }
    echo json_encode($antwort->get_data(), JSON_UNESCAPED_UNICODE);
    exit;
}

if (preg_match('#^/(assets|fotos)/#', $pfad)) { return false; }   // Datei direkt ausliefern

$zugang = Kikripp_Zugang::hat_zugang() ? 'true' : 'false';
?><!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Testseite Artikelkatalog</title>
<link rel="stylesheet" href="/assets/katalog.css">
<style>body{margin:0;font:15px system-ui;background:#fafafa}.huelle{max-width:1200px;margin:0 auto;padding:0 20px;background:#fff}</style>
</head><body>
<div class="huelle"><div id="kikripp-katalog" class="kikripp"></div></div>
<script>window.KIKRIPP = {basis:'/wp-json/kikripp/v1', signet:'/assets/signet.svg', zugang:<?php echo $zugang; ?>, admin:false, verwaltung:'#'};</script>
<script src="/assets/katalog.js"></script>
</body></html>
