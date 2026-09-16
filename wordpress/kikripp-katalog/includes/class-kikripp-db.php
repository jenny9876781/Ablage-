<?php
if (!defined('ABSPATH')) { exit; }

/**
 * Datenhaltung: Artikel, Vorgänge (eine Reservierungsanfrage) und Positionen
 * (ein Artikel darin). Die Verfügbarkeit wird immer aus den Positionen
 * gerechnet, nie als Zähler geführt – ein Zähler läuft bei gleichzeitigen
 * Zugriffen auseinander.
 */
class Kikripp_DB {

    const SCHEMA_VERSION = 2;

    public static function t_artikel()  { global $wpdb; return $wpdb->prefix . 'kikripp_artikel'; }
    public static function t_vorgang()  { global $wpdb; return $wpdb->prefix . 'kikripp_vorgang'; }
    public static function t_position() { global $wpdb; return $wpdb->prefix . 'kikripp_position'; }

    public static function tabellen_anlegen() {
        global $wpdb;
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $coll = $wpdb->get_charset_collate();

        dbDelta("CREATE TABLE " . self::t_artikel() . " (
            artnr VARCHAR(32) NOT NULL,
            sortierung INT NOT NULL DEFAULT 0,
            menge INT NOT NULL DEFAULT 0,
            preis_netto DECIMAL(10,2) NOT NULL DEFAULT 0,
            aktiv TINYINT(1) NOT NULL DEFAULT 1,
            im_katalog TINYINT(1) NOT NULL DEFAULT 1,
            daten LONGTEXT NOT NULL,
            aktualisiert DATETIME NOT NULL,
            PRIMARY KEY (artnr),
            KEY im_katalog (im_katalog, aktiv)
        ) ENGINE=InnoDB $coll;");

        dbDelta("CREATE TABLE " . self::t_vorgang() . " (
            id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
            name VARCHAR(190) NOT NULL DEFAULT '',
            email VARCHAR(190) NOT NULL DEFAULT '',
            telefon VARCHAR(80) NOT NULL DEFAULT '',
            wunschtermin VARCHAR(20) NOT NULL DEFAULT '',
            nachricht TEXT NULL,
            erstellt DATETIME NOT NULL,
            ablauf DATETIME NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'offen',
            mail_versandt TINYINT(1) NOT NULL DEFAULT 0,
            testdaten TINYINT(1) NOT NULL DEFAULT 0,
            herkunft VARCHAR(45) NOT NULL DEFAULT '',
            PRIMARY KEY (id),
            KEY status (status, ablauf)
        ) ENGINE=InnoDB $coll;");

        dbDelta("CREATE TABLE " . self::t_position() . " (
            id BIGINT(20) UNSIGNED NOT NULL AUTO_INCREMENT,
            vorgang_id BIGINT(20) UNSIGNED NOT NULL,
            artnr VARCHAR(32) NOT NULL,
            menge INT NOT NULL DEFAULT 1,
            preis_netto DECIMAL(10,2) NOT NULL DEFAULT 0,
            status VARCHAR(20) NOT NULL DEFAULT 'reserviert',
            bezahlt_am DATETIME NULL,
            PRIMARY KEY (id),
            KEY vorgang_id (vorgang_id),
            KEY artnr (artnr, status)
        ) ENGINE=InnoDB $coll;");

        update_option('kikripp_schema_version', self::SCHEMA_VERSION);
    }

    public static function pruefe_version() {
        if ((int) get_option('kikripp_schema_version', 0) < self::SCHEMA_VERSION) {
            self::tabellen_anlegen();
        }
    }

    /** Belegung je Artikel: bezahlte Mengen und noch gültige Reservierungen. */
    public static function belegung($artnr = null) {
        global $wpdb;
        $p = self::t_position();
        $v = self::t_vorgang();
        $jetzt = current_time('mysql');
        $wo = '';
        $args = [$jetzt];
        if ($artnr !== null) {
            $wo = ' AND p.artnr = %s';
            $args[] = $artnr;
        }
        $sql = "SELECT p.artnr,
                       SUM(CASE WHEN p.status = 'bezahlt' THEN p.menge ELSE 0 END) AS bezahlt,
                       SUM(CASE WHEN p.status = 'reserviert' AND v.status = 'offen'
                                     AND v.ablauf > %s THEN p.menge ELSE 0 END) AS reserviert
                FROM $p p INNER JOIN $v v ON v.id = p.vorgang_id
                WHERE 1=1 $wo
                GROUP BY p.artnr";
        $zeilen = $wpdb->get_results($wpdb->prepare($sql, $args), ARRAY_A);
        $out = [];
        foreach ((array) $zeilen as $z) {
            $out[$z['artnr']] = [
                'bezahlt'    => (int) $z['bezahlt'],
                'reserviert' => (int) $z['reserviert'],
            ];
        }
        return $out;
    }

    /**
     * Artikel für den Katalog, angereichert um die Verfügbarkeit.
     * Vollständig bezahlte Artikel fallen heraus – sie sind verkauft.
     */
    public static function katalog_artikel() {
        global $wpdb;
        $zeilen = $wpdb->get_results(
            "SELECT * FROM " . self::t_artikel() . "
             WHERE aktiv = 1 AND im_katalog = 1
             ORDER BY sortierung ASC, artnr ASC", ARRAY_A);
        $belegung = self::belegung();
        $out = [];
        foreach ((array) $zeilen as $z) {
            $daten = json_decode($z['daten'], true);
            if (!is_array($daten)) { $daten = []; }
            $b = $belegung[$z['artnr']] ?? ['bezahlt' => 0, 'reserviert' => 0];
            $menge = (int) $z['menge'];
            $rest  = max(0, $menge - $b['bezahlt']);          // noch nicht verkauft
            if ($rest <= 0) { continue; }                      // bezahlt = aus dem Katalog
            $frei = max(0, $rest - $b['reserviert']);
            $daten['nr']         = $z['artnr'];
            $daten['menge']      = $rest;
            $daten['frei']       = $frei;
            $daten['reserviert'] = min($b['reserviert'], $rest);
            $daten['preis']      = (float) $z['preis_netto'];
            $daten['status']     = $frei > 0 ? 'verfügbar' : 'reserviert';
            $out[] = $daten;
        }
        return $out;
    }

    /** Wie viele Stück sind von einem Artikel gerade frei? */
    public static function frei($artnr) {
        global $wpdb;
        $menge = (int) $wpdb->get_var($wpdb->prepare(
            "SELECT menge FROM " . self::t_artikel() . "
             WHERE artnr = %s AND aktiv = 1 AND im_katalog = 1", $artnr));
        if ($menge <= 0) { return 0; }
        $b = self::belegung($artnr)[$artnr] ?? ['bezahlt' => 0, 'reserviert' => 0];
        return max(0, $menge - $b['bezahlt'] - $b['reserviert']);
    }

    /**
     * Reservierung anlegen. Läuft in einer Transaktion mit Zeilensperre,
     * damit zwei gleichzeitige Anfragen nicht dasselbe letzte Stück bekommen.
     * Gibt die Vorgangs-ID zurück oder ein WP_Error.
     */
    public static function reservieren($kontakt, $wunsch) {
        global $wpdb;
        if (empty($wunsch)) {
            return new WP_Error('leer', 'Es wurden keine Artikel ausgewählt.');
        }
        $frist = max(1, (int) get_option('kikripp_frist_tage', 7));
        $jetzt = current_time('mysql');
        $ablauf = gmdate('Y-m-d H:i:s', strtotime($jetzt) + $frist * DAY_IN_SECONDS);

        $wpdb->query('START TRANSACTION');
        try {
            $positionen = [];
            foreach ($wunsch as $artnr => $menge) {
                $artnr = sanitize_text_field((string) $artnr);
                $menge = (int) $menge;
                if ($menge <= 0) { continue; }

                // Zeilensperre auf den Artikel – blockiert eine parallele Reservierung
                $artikel = $wpdb->get_row($wpdb->prepare(
                    "SELECT artnr, menge, preis_netto FROM " . self::t_artikel() . "
                     WHERE artnr = %s AND aktiv = 1 AND im_katalog = 1 FOR UPDATE", $artnr), ARRAY_A);
                if (!$artikel) {
                    $wpdb->query('ROLLBACK');
                    return new WP_Error('unbekannt', sprintf('Artikel %s ist nicht mehr im Katalog.', $artnr));
                }
                $b = self::belegung($artnr)[$artnr] ?? ['bezahlt' => 0, 'reserviert' => 0];
                $frei = (int) $artikel['menge'] - $b['bezahlt'] - $b['reserviert'];
                if ($menge > $frei) {
                    $wpdb->query('ROLLBACK');
                    return new WP_Error('zu_wenig', sprintf(
                        'Von %s sind nur noch %d Stück verfügbar. Bitte passen Sie die Menge an.',
                        $artnr, max(0, $frei)));
                }
                $positionen[] = [
                    'artnr' => $artnr,
                    'menge' => $menge,
                    'preis' => (float) $artikel['preis_netto'],   // Preis wird eingefroren
                ];
            }
            if (empty($positionen)) {
                $wpdb->query('ROLLBACK');
                return new WP_Error('leer', 'Es wurden keine Artikel ausgewählt.');
            }

            $ok = $wpdb->insert(self::t_vorgang(), [
                'name'         => $kontakt['name'],
                'email'        => $kontakt['email'],
                'telefon'      => $kontakt['telefon'],
                'wunschtermin' => $kontakt['wunschtermin'],
                'nachricht'    => $kontakt['nachricht'],
                'erstellt'     => $jetzt,
                'ablauf'       => $ablauf,
                'status'       => 'offen',
                'testdaten'    => (int) get_option('kikripp_vorschau', 1),
                'herkunft'     => substr((string) ($_SERVER['REMOTE_ADDR'] ?? ''), 0, 45),
            ]);
            if ($ok === false) {
                $wpdb->query('ROLLBACK');
                return new WP_Error('db', 'Die Reservierung konnte nicht gespeichert werden.');
            }
            $vorgang_id = (int) $wpdb->insert_id;
            foreach ($positionen as $pos) {
                $wpdb->insert(self::t_position(), [
                    'vorgang_id'  => $vorgang_id,
                    'artnr'       => $pos['artnr'],
                    'menge'       => $pos['menge'],
                    'preis_netto' => $pos['preis'],
                    'status'      => 'reserviert',
                ]);
            }
            $wpdb->query('COMMIT');
            return $vorgang_id;
        } catch (Exception $e) {
            $wpdb->query('ROLLBACK');
            return new WP_Error('fehler', $e->getMessage());
        }
    }

    public static function vorgang($id) {
        global $wpdb;
        $v = $wpdb->get_row($wpdb->prepare(
            "SELECT * FROM " . self::t_vorgang() . " WHERE id = %d", $id), ARRAY_A);
        if (!$v) { return null; }
        $v['positionen'] = $wpdb->get_results($wpdb->prepare(
            "SELECT p.*, a.daten FROM " . self::t_position() . " p
             LEFT JOIN " . self::t_artikel() . " a ON a.artnr = p.artnr
             WHERE p.vorgang_id = %d ORDER BY p.id", $id), ARRAY_A);
        return $v;
    }

    public static function vorgaenge($status = null) {
        global $wpdb;
        $sql = "SELECT * FROM " . self::t_vorgang();
        if ($status) {
            $sql = $wpdb->prepare($sql . " WHERE status = %s", $status);
        }
        $sql .= " ORDER BY erstellt DESC";
        $liste = $wpdb->get_results($sql, ARRAY_A);
        foreach ($liste as &$v) {
            $v['positionen'] = $wpdb->get_results($wpdb->prepare(
                "SELECT * FROM " . self::t_position() . " WHERE vorgang_id = %d ORDER BY id", $v['id']), ARRAY_A);
        }
        return $liste;
    }

    /**
     * Nimmt alle Artikel aus dem Katalog, die in der Importdatei nicht mehr vorkommen.
     * Gelöscht wird nichts – an den Zeilen können Reservierungen und Verkäufe hängen.
     * Gibt die Artikelnummern zurück, die dabei stillgelegt wurden.
     */
    public static function fehlende_stilllegen(array $gesehen) {
        global $wpdb;
        if (!$gesehen) { return []; }
        $platzhalter = implode(',', array_fill(0, count($gesehen), '%s'));
        $betroffen = $wpdb->get_col($wpdb->prepare(
            'SELECT artnr FROM ' . self::t_artikel() . "
              WHERE artnr NOT IN ($platzhalter) AND (im_katalog = 1 OR aktiv = 1)", $gesehen));
        if (!$betroffen) { return []; }
        $wpdb->query($wpdb->prepare(
            'UPDATE ' . self::t_artikel() . " SET im_katalog = 0, aktiv = 0
              WHERE artnr NOT IN ($platzhalter) AND (im_katalog = 1 OR aktiv = 1)", $gesehen));
        return $betroffen;
    }

    /** Vorgang auf bezahlt/storniert setzen oder die Frist verlängern. */
    public static function vorgang_status($id, $status) {
        global $wpdb;
        if (!in_array($status, ['offen', 'bezahlt', 'storniert'], true)) { return false; }
        $wpdb->update(self::t_vorgang(), ['status' => $status], ['id' => (int) $id]);
        $pos_status = $status === 'bezahlt' ? 'bezahlt' : ($status === 'storniert' ? 'storniert' : 'reserviert');
        $felder = ['status' => $pos_status];
        // Das Zahldatum wird beim ersten Mal gesetzt und danach nicht mehr angefasst;
        // wird der Vorgang zurückgenommen, fällt es wieder weg.
        if ($status === 'bezahlt') {
            $felder['bezahlt_am'] = current_time('mysql');
        } else {
            $felder['bezahlt_am'] = null;
        }
        $wpdb->update(self::t_position(), $felder, ['vorgang_id' => (int) $id]);
        return true;
    }

    public static function vorgang_verlaengern($id) {
        global $wpdb;
        $frist = max(1, (int) get_option('kikripp_frist_tage', 7));
        $neu = gmdate('Y-m-d H:i:s', strtotime(current_time('mysql')) + $frist * DAY_IN_SECONDS);
        return (bool) $wpdb->update(self::t_vorgang(),
            ['ablauf' => $neu, 'status' => 'offen'], ['id' => (int) $id]);
    }

    public static function vorgang_loeschen($id) {
        global $wpdb;
        $wpdb->delete(self::t_position(), ['vorgang_id' => (int) $id]);
        return (bool) $wpdb->delete(self::t_vorgang(), ['id' => (int) $id]);
    }

    public static function testdaten_loeschen() {
        global $wpdb;
        $ids = $wpdb->get_col("SELECT id FROM " . self::t_vorgang() . " WHERE testdaten = 1");
        foreach ($ids as $id) { self::vorgang_loeschen($id); }
        return count($ids);
    }
}
