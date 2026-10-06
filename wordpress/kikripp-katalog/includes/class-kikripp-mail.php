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
            $zeilen[] = sprintf('%d × %s  %s — %s',
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
            'Name:',
            $v['name'],
            '',
            'Firma:',
            trim((string) ($v['firma'] ?? '')) !== '' ? $v['firma'] : '—',
            '',
            'Rechnungsanschrift:',
            trim(($v['strasse'] ?? '') . ', ' . ($v['plz'] ?? '') . ' ' . ($v['ort'] ?? ''), ', '),
            '',
            'E-Mail:',
            $v['email'],
            '',
            'Telefon:',
            $v['telefon'] !== '' ? $v['telefon'] : '—',
            '',
            'Besichtigung gewünscht:',
            self::besichtigung_text($v),
            '',
            'Abholung gewünscht:',
            self::abholung_text($v),
            '',
            'Nachricht:',
            trim((string) $v['nachricht']) !== '' ? $v['nachricht'] : '—',
            '',
            str_repeat('-', 60),
            implode("\n", $zeilen),
            str_repeat('-', 60),
            $ust > 0
                ? implode("\n", ['Summe netto:  ' . self::eur($summe),
                    sprintf('zzgl. %s %% USt: %s', rtrim(rtrim(number_format($ust * 100, 1, ',', ''), '0'), ','),
                        self::eur($summe * $ust)),
                    'Summe brutto: ' . self::eur($summe * (1 + $ust))])
                : 'Summe:        ' . self::eur($summe) . ' (umsatzsteuerfrei)',
            '',
            'Verwalten: ' . admin_url('admin.php?page=kikripp-reservierungen'),
            '',
            'Die Kontaktdaten stehen auch in der Verwaltung unter Artikelkatalog →',
            'Reservierungen. Bitte dort löschen, sobald der Vorgang abgewickelt ist.',
        ]);

        // Ohne eigene Absenderadresse nimmt WordPress "wordpress@<domain>" - ein Postfach,
        // das es nicht gibt. Fremde Mailanbieter verwerfen solche Mails gern stillschweigend.
        // Als Absender dient deshalb die Adresse, an die gemeldet wird: die gibt es wirklich.
        $kopf = ['Content-Type: text/plain; charset=UTF-8'];
        if (is_email($an)) {
            $kopf[] = sprintf('From: %s <%s>', get_option('kikripp_firma', 'Kikripp GmbH'), $an);
        }
        if (is_email($v['email'])) {
            $kopf[] = 'Reply-To: ' . $v['name'] . ' <' . $v['email'] . '>';
        }
        $ok = wp_mail($an, $betreff, $text, $kopf);

        global $wpdb;
        $wpdb->update(Kikripp_DB::t_vorgang(), ['mail_versandt' => $ok ? 1 : 0], ['id' => (int) $vorgang_id]);

        // Die Kontaktdaten bleiben in der Datenbank, bis der Mensch sie löscht.
        //
        // Bis zum 29.09.2026 wurden sie nach erfolgreichem Versand sofort gelöscht - die
        // Mail war dann der einzige Ort, an dem sie standen. Der Webserver von kikripp.de
        // verschickt aber gar keine Mails: wp_mail() meldet Erfolg, die Mail verschwindet.
        // Damit wäre jeder Interessent unwiederbringlich verloren gewesen. Gespeichert wird
        // jetzt also bewusst - auf der eigenen Website der Gesellschaft, mit einem Absatz
        // in der Datenschutzerklärung und einem Löschknopf je Vorgang.
        return $ok;
    }

    /** „Do 08.10.2026, 09:00 Uhr“ oder „nein“. */
    public static function besichtigung_text($v) {
        $b = trim((string) ($v['besichtigung'] ?? ''));
        if ($b === '') { return 'nein'; }
        $t = strtotime(substr($b, 0, 10) . ' 12:00:00 UTC');
        return 'Do ' . gmdate('d.m.Y', $t) . ', ' . substr($b, 11) . ' Uhr';
    }

    /** „Mo 12.10.2026“, ergänzt um den Demontagehinweis. */
    public static function abholung_text($v) {
        $teile = [];
        $w = trim((string) ($v['abholwunsch'] ?? ''));
        if ($w !== '') {
            $t = strtotime($w . ' 12:00:00 UTC');
            $teile[] = ['', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'][(int) gmdate('N', $t)] . ' ' . gmdate('d.m.Y', $t);
        }
        if (!empty($v['demontage'])) { $teile[] = 'Demontage nötig – Termin Fr nachmittag / Sa vormittag nach Vereinbarung'; }
        return $teile ? implode('; ', $teile) : '—';
    }

    public static function eur($v) {
        return number_format((float) $v, 2, ',', '.') . ' €';
    }
}
