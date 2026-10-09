<?php
/**
 * Minimale WordPress-Attrappe auf SQLite-Basis, nur für die Tests.
 * Bildet genau die Funktionen nach, die das Plugin benutzt.
 */
define('ABSPATH', '/tmp/wp-attrappe/');
@mkdir(ABSPATH . 'wp-admin/includes', 0777, true);
if (!file_exists(ABSPATH . 'wp-admin/includes/upgrade.php')) {
    file_put_contents(ABSPATH . 'wp-admin/includes/upgrade.php', '<?php /* Attrappe */');
}
define('DAY_IN_SECONDS', 86400);
define('HOUR_IN_SECONDS', 3600);
define('MINUTE_IN_SECONDS', 60);
define('COOKIEPATH', '/');
define('ARRAY_A', 'ARRAY_A');
define('ARRAY_N', 'ARRAY_N');
define('OBJECT', 'OBJECT');

class WP_Error {
    private $code, $message;
    public function __construct($code = '', $message = '') { $this->code = $code; $this->message = $message; }
    public function get_error_code() { return $this->code; }
    public function get_error_message() { return $this->message; }
}
function is_wp_error($ding) { return $ding instanceof WP_Error; }

class Attrappe_WPDB {
    public $prefix = 'wp_';
    public $insert_id = 0;
    private $pdo;
    public function __construct($datei) {
        $this->pdo = new PDO('sqlite:' . $datei);
        $this->pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    }
    public function get_charset_collate() { return ''; }

    /** MySQL-Eigenheiten für SQLite entschärfen. */
    private function uebersetze($sql) {
        $sql = preg_replace('/\s+FOR UPDATE/i', '', $sql);          // Zeilensperre: SQLite kennt sie nicht
        $sql = preg_replace('/ENGINE=InnoDB/i', '', $sql);
        $sql = preg_replace('/BIGINT\(20\) UNSIGNED NOT NULL AUTO_INCREMENT/i',
                            'INTEGER PRIMARY KEY AUTOINCREMENT', $sql);
        $sql = preg_replace('/,\s*PRIMARY KEY \(id\)/i', '', $sql);
        $sql = preg_replace('/\bUNSIGNED\b/i', '', $sql);
        $sql = preg_replace('/BIGINT\(\d+\)/i', 'INTEGER', $sql);
        $sql = preg_replace('/,\s*KEY [a-z_]+ \([^)]*\)/i', '', $sql);
        $sql = preg_replace('/TINYINT\(1\)/i', 'INTEGER', $sql);
        $sql = preg_replace('/INT NOT NULL/i', 'INTEGER NOT NULL', $sql);
        $sql = preg_replace('/DECIMAL\(10,2\)/i', 'REAL', $sql);
        $sql = preg_replace('/VARCHAR\(\d+\)/i', 'TEXT', $sql);
        $sql = preg_replace('/LONGTEXT/i', 'TEXT', $sql);
        $sql = preg_replace('/DATETIME/i', 'TEXT', $sql);
        return $sql;
    }
    public function prepare($sql, ...$args) {
        if (count($args) === 1 && is_array($args[0])) { $args = $args[0]; }
        $sql = str_replace(['%s', '%d', '%f'], '?', $sql);
        $st = $this->pdo->prepare($this->uebersetze($sql));
        return ['sql' => $sql, 'args' => $args, 'st' => $st];
    }
    private function fuehre_aus($sql) {
        if (is_array($sql)) {
            $st = $this->pdo->prepare($this->uebersetze($sql['sql']));
            $st->execute(array_values($sql['args']));
            return $st;
        }
        $st = $this->pdo->prepare($this->uebersetze($sql));
        $st->execute();
        return $st;
    }
    public function query($sql) {
        if (preg_match('/^\s*(START TRANSACTION|COMMIT|ROLLBACK)/i', is_array($sql) ? $sql['sql'] : $sql, $m)) {
            $b = strtoupper($m[1]);
            try {
                if ($b === 'START TRANSACTION') { $this->pdo->beginTransaction(); }
                elseif ($b === 'COMMIT') { $this->pdo->commit(); }
                else { $this->pdo->rollBack(); }
            } catch (Exception $e) { /* verschachtelte Transaktion */ }
            return true;
        }
        return $this->fuehre_aus($sql)->rowCount();
    }
    public function get_var($sql) {
        $r = $this->fuehre_aus($sql)->fetch(PDO::FETCH_NUM);
        return $r ? $r[0] : null;
    }
    public function get_row($sql, $typ = null) { return $this->fuehre_aus($sql)->fetch(PDO::FETCH_ASSOC) ?: null; }
    public function get_results($sql, $typ = null) { return $this->fuehre_aus($sql)->fetchAll(PDO::FETCH_ASSOC); }
    public function get_col($sql) { return $this->fuehre_aus($sql)->fetchAll(PDO::FETCH_COLUMN); }
    public function insert($tabelle, $daten) {
        $spalten = array_keys($daten);
        $sql = "INSERT INTO $tabelle (" . implode(',', $spalten) . ") VALUES ("
             . implode(',', array_fill(0, count($spalten), '?')) . ")";
        $st = $this->pdo->prepare($sql);
        $ok = $st->execute(array_values($daten));
        $this->insert_id = (int) $this->pdo->lastInsertId();
        return $ok ? 1 : false;
    }
    public function update($tabelle, $daten, $wo) {
        $setz = implode(',', array_map(function ($s) { return "$s = ?"; }, array_keys($daten)));
        $bed  = implode(' AND ', array_map(function ($s) { return "$s = ?"; }, array_keys($wo)));
        $st = $this->pdo->prepare("UPDATE $tabelle SET $setz WHERE $bed");
        $st->execute(array_merge(array_values($daten), array_values($wo)));
        return $st->rowCount();
    }
    public function delete($tabelle, $wo) {
        $bed = implode(' AND ', array_map(function ($s) { return "$s = ?"; }, array_keys($wo)));
        $st = $this->pdo->prepare("DELETE FROM $tabelle WHERE $bed");
        $st->execute(array_values($wo));
        return $st->rowCount();
    }
}

$GLOBALS['wpdb'] = new Attrappe_WPDB($GLOBALS['ATTRAPPE_DB']);
$GLOBALS['optionen'] = [];
$GLOBALS['mails'] = [];

function get_option($name, $vorgabe = false) { return $GLOBALS['optionen'][$name] ?? $vorgabe; }
function update_option($name, $wert) { $GLOBALS['optionen'][$name] = $wert; return true; }
function add_option($name, $wert) { if (!isset($GLOBALS['optionen'][$name])) { $GLOBALS['optionen'][$name] = $wert; } return true; }
function delete_option($name) { unset($GLOBALS['optionen'][$name]); return true; }
function get_transient($n) { return false; }
function set_transient($n, $w, $z) { return true; }
function delete_transient($n) { return true; }
function current_time($typ) { return $typ === 'timestamp' ? time() : gmdate('Y-m-d H:i:s'); }
function sanitize_text_field($s) { return trim(strip_tags((string) $s)); }
function sanitize_textarea_field($s) { return trim(strip_tags((string) $s)); }
function sanitize_email($s) { return filter_var((string) $s, FILTER_SANITIZE_EMAIL); }
function sanitize_key($s) { return preg_replace('/[^a-z0-9_]/', '', strtolower((string) $s)); }
function is_email($s) { return (bool) filter_var((string) $s, FILTER_VALIDATE_EMAIL); }
function wp_json_encode($d) { return json_encode($d, JSON_UNESCAPED_UNICODE); }
function current_user_can($f) { return $GLOBALS['ist_admin'] ?? false; }
function wp_mail($an, $betreff, $text, $kopf = []) {
    $GLOBALS['mails'][] = compact('an', 'betreff', 'text', 'kopf');
    // Im Serverbetrieb zusaetzlich mitschreiben, damit der Mailtext pruefbar bleibt.
    if (!empty($GLOBALS['MAIL_MITSCHRIFT'])) {
        file_put_contents($GLOBALS['MAIL_MITSCHRIFT'], str_repeat('=', 70) . "\nAn: $an\nBetreff: $betreff\n"
            . 'Kopf: ' . implode(' | ', (array) $kopf) . "\n\n$text\n", FILE_APPEND);
    }
    return $GLOBALS['mail_geht'] ?? true;
}
function mysql2date($format, $datum) { return gmdate($format === 'd.m.Y H:i' ? 'd.m.Y H:i' : 'd.m.Y', strtotime($datum)); }
function admin_url($p = '') { return 'https://kikripp.de/wp-admin/' . $p; }
function get_bloginfo($w) { return 'Kikripp GmbH'; }
function wp_hash_password($p) { return password_hash($p, PASSWORD_DEFAULT); }
function wp_check_password($p, $h) { return password_verify($p, $h); }
function wp_salt($s = '') { return 'test-salt-1234567890'; }
function is_ssl() { return !empty($_SERVER['HTTPS']); }
function is_admin() { return false; }
function nocache_headers() { if (!headers_sent()) { header('Cache-Control: no-store'); } }
function is_feed() { return false; }
function wp_unslash($w) { return is_array($w) ? array_map('stripslashes', $w) : stripslashes((string) $w); }
function remove_query_arg($schluessel, $url = null) {
    $url = $url ?: ($_SERVER['REQUEST_URI'] ?? '/');
    $teile = parse_url($url);
    $frage = [];
    if (!empty($teile['query'])) { parse_str($teile['query'], $frage); }
    unset($frage[$schluessel]);
    return ($teile['path'] ?? '/') . ($frage ? '?' . http_build_query($frage) : '');
}
class Attrappe_Weiterleitung extends Exception {}
function wp_safe_redirect($ziel, $status = 302) {
    $GLOBALS['weiterleitung'] = $ziel;
    if (!headers_sent()) { header('Location: ' . $ziel, true, $status); }
    // Im Test statt `exit` eine Ausnahme – sonst bricht der ganze Lauf ab.
    if (!empty($GLOBALS['ATTRAPPE_WIRFT_BEI_WEITERLEITUNG'])) {
        throw new Attrappe_Weiterleitung($ziel);
    }
    return true;
}
function esc_html($s) { return htmlspecialchars((string) $s, ENT_QUOTES); }
// Der Testserver bringt einige dieser Helfer selbst mit - deshalb nur anlegen,
// wenn sie fehlen. Sonst bricht der Server mit "Cannot redeclare function" ab.
if (!function_exists('esc_url'))      { function esc_url($u) { return (string) $u; } }
if (!function_exists('esc_url_raw'))  { function esc_url_raw($u) { return (string) $u; } }
if (!function_exists('wp_nonce_url')) { function wp_nonce_url($u, $a = -1) { return $u . '&_wpnonce=test'; } }
// Die Menuetitel werden mitgeschrieben, damit der Test die Zaehler-Blase pruefen kann.
if (!function_exists('add_menu_page')) {
    function add_menu_page($seite, $titel, $rechte, $slug, $fn = null, $icon = '', $pos = null) {
        $GLOBALS['menue_titel'][] = $titel; return $slug;
    }
}
if (!function_exists('add_submenu_page')) {
    function add_submenu_page($eltern, $seite, $titel, $rechte, $slug, $fn = null) {
        $GLOBALS['menue_titel'][] = $titel; return $slug;
    }
}
function esc_attr($s) { return htmlspecialchars((string) $s, ENT_QUOTES); }
function esc_textarea($s) { return htmlspecialchars((string) $s, ENT_QUOTES); }
// Fuer die Verwaltungsseite ab Fassung 1.2.0 (Abholtermin-Formular, Aktionslinks).
if (!function_exists('add_query_arg')) {
    function add_query_arg($args, $url = '') {
        $trenner = strpos((string) $url, '?') === false ? '?' : '&';
        return $url . $trenner . http_build_query(array_filter((array) $args, function ($w) { return $w !== null; }));
    }
}
if (!function_exists('wp_nonce_field')) {
    function wp_nonce_field($aktion = -1, $name = '_wpnonce', $referer = true, $ausgeben = true) {
        $feld = '<input type="hidden" name="' . $name . '" value="test">';
        if ($ausgeben) { echo $feld; }
        return $feld;
    }
}
// Ab Fassung 1.3.0 (Bearbeitungszeile, Abholplan, Rücksprung)
if (!function_exists('checked')) {
    function checked($a, $b = true, $ausgeben = true) {
        $r = ((string) $a === (string) $b) ? ' checked="checked"' : '';
        if ($ausgeben) { echo $r; }
        return $r;
    }
}
if (!function_exists('wp_get_referer')) { function wp_get_referer() { return $GLOBALS['referer'] ?? ''; } }
if (!function_exists('date_i18n')) { function date_i18n($f, $t = null) { return gmdate($f, $t ?? time()); } }
if (!function_exists('nocache_headers')) { function nocache_headers() {} }
if (!function_exists('wp_add_dashboard_widget')) {
    function wp_add_dashboard_widget($id, $titel, $fn) { $GLOBALS['widgets'][$id] = $titel; }
}
if (!function_exists('check_admin_referer')) { function check_admin_referer($a = -1, $n = '_wpnonce') { return 1; } }
