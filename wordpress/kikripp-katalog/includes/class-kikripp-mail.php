<?php
if (!defined('ABSPATH')) { exit; }

/** Benachrichtigung über eine neue Reservierung. */
class Kikripp_Mail {

    /** Positionszeilen und Nettosumme eines Vorgangs. */
    private static function positionen($v) {
        $zeilen = [];
        $summe = 0.0;
        foreach ($v['positionen'] as $p) {
            $daten = json_decode((string) $p['daten'], true);
            $titel = is_array($daten) && !empty($daten['titel']) ? $daten['titel'] : $p['artnr'];
            $wert = (float) $p['preis_netto'] * (int) $p['menge'];
            $summe += $wert;
            $zeilen[] = sprintf('%d × %s  %s — %s netto',
                (int) $p['menge'], $p['artnr'], $titel, self::eur($wert));
        }
        return [$zeilen, $summe];
    }

    public static function reservierung($vorgang_id) {
        $v = Kikripp_DB::vorgang($vorgang_id);
        if (!$v) { return false; }

        $an = get_option('kikripp_mail_an', get_option('admin_email'));
        $ust = (float) get_option('kikripp_ust_prozent', 19) / 100;
        $firma = (string) get_option('kikripp_firma', 'Kikripp GmbH');

        list($zeilen, $summe) = self::positionen($v);

        // Der Betreff ist der Suchbegriff fürs Postfach – die Verwaltung zeigt ihn an.
        $betreff = sprintf('[%s] Neue Reservierung #%d — %s', $firma, $vorgang_id, $v['name']);
        $text = implode("\n", [
            'Es ist eine neue Reservierung über den Artikelkatalog eingegangen.',
            '',
            'Vorgang:      #' . $vorgang_id,
            'Eingegangen:  ' . mysql2date('d.m.Y H:i', $v['erstellt']) . ' Uhr',
            'Reserviert bis: ' . mysql2date('d.m.Y', $v['ablauf']),
            '',
            'Name / Firma:',
            $v['name'],
            '',
            'E-Mail:',
            $v['email'],
            '',
            'Telefon:',
            $v['telefon'] !== '' ? $v['telefon'] : '—',
            '',
            'Nachricht:',
            trim((string) $v['nachricht']) !== '' ? $v['nachricht'] : '—',
            '',
            str_repeat('-', 60),
            implode("\n", $zeilen),
            str_repeat('-', 60),
            'Summe netto:  ' . self::eur($summe),
            sprintf('zzgl. %d %% USt: %s', (int) get_option('kikripp_ust_prozent', 19), self::eur($summe * $ust)),
            'Summe brutto: ' . self::eur($summe * (1 + $ust)),
            '',
            'Verwalten: ' . admin_url('admin.php?page=kikripp-reservierungen'),
            '',
            'Diese Mail ist der einzige Ort, an dem die Kontaktdaten stehen —',
            'im Katalog werden sie nicht gespeichert. Bitte aufbewahren.',
        ]);

        $kopf = ['Content-Type: text/plain; charset=UTF-8'];
        if (is_email($v['email'])) {
            $kopf[] = 'Reply-To: ' . $v['name'] . ' <' . $v['email'] . '>';
        }
        $ok = wp_mail($an, $betreff, $text, $kopf);

        global $wpdb;
        $wpdb->update(Kikripp_DB::t_vorgang(), ['mail_versandt' => $ok ? 1 : 0], ['id' => (int) $vorgang_id]);

        // Ist die Mail draußen, sind die Kontaktdaten dort aufgehoben und haben
        // in der Datenbank nichts mehr zu suchen. Scheitert der Versand, bleiben
        // sie liegen – sonst wäre der Kontakt endgültig verloren.
        if ($ok) {
            Kikripp_DB::kontakt_loeschen($vorgang_id);
        }
        return $ok;
    }

    public static function eur($v) {
        return number_format((float) $v, 2, ',', '.') . ' €';
    }
}
