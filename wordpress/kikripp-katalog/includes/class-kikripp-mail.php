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

        list($zeilen, $summe) = self::positionen($v);

        $betreff = sprintf('[Kikripp] Neue Reservierung #%d — %s', $vorgang_id, $v['name']);
        $text = implode("\n", [
            'Es ist eine neue Reservierung über den Artikelkatalog eingegangen.',
            '',
            'Vorgang:      #' . $vorgang_id,
            'Eingegangen:  ' . mysql2date('d.m.Y H:i', $v['erstellt']) . ' Uhr',
            'Reserviert bis: ' . mysql2date('d.m.Y', $v['ablauf']),
            '',
            'Name / Firma: ' . $v['name'],
            'E-Mail:       ' . $v['email'],
            'Telefon:      ' . ($v['telefon'] !== '' ? $v['telefon'] : '—'),
            'Wunschtermin: ' . ($v['wunschtermin'] !== '' ? $v['wunschtermin'] : '—'),
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
        ]);

        $kopf = ['Content-Type: text/plain; charset=UTF-8'];
        if (is_email($v['email'])) {
            $kopf[] = 'Reply-To: ' . $v['name'] . ' <' . $v['email'] . '>';
        }
        $ok = wp_mail($an, $betreff, $text, $kopf);

        global $wpdb;
        $wpdb->update(Kikripp_DB::t_vorgang(), ['mail_versandt' => $ok ? 1 : 0], ['id' => (int) $vorgang_id]);
        return $ok;
    }

    /** Bestätigung an den Interessenten – nur wenn eine gültige Adresse vorliegt. */
    public static function bestaetigung($vorgang_id) {
        $v = Kikripp_DB::vorgang($vorgang_id);
        if (!$v || !is_email($v['email'])) { return false; }
        $absender = get_option('kikripp_mail_an', get_option('admin_email'));
        $firma = get_bloginfo('name');
        $ust = (float) get_option('kikripp_ust_prozent', 19) / 100;
        list($zeilen, $summe) = self::positionen($v);
        $abholung = trim((string) get_option('kikripp_abholadresse', ''));

        $abholblock = $abholung !== ''
            ? ['Abholung nach Terminvereinbarung:', $abholung, '']
            : [];

        $betreff = 'Ihre Reservierung bei der ' . $firma;
        $text = implode("\n", array_merge([
            'Guten Tag ' . $v['name'] . ',',
            '',
            'vielen Dank für Ihre Reservierung. Wir haben sie erhalten und melden uns',
            'in Kürze bei Ihnen, um einen Abholtermin abzustimmen.',
            '',
            'Ihre Reservierung ist bis zum ' . mysql2date('d.m.Y', $v['ablauf']) . ' vorgemerkt.',
            'Vorgangsnummer: #' . $vorgang_id,
            '',
            str_repeat('-', 60),
            implode("\n", $zeilen),
            str_repeat('-', 60),
            'Summe netto:  ' . self::eur($summe),
            sprintf('zzgl. %d %% USt: %s', (int) get_option('kikripp_ust_prozent', 19), self::eur($summe * $ust)),
            'Summe brutto: ' . self::eur($summe * (1 + $ust)),
            '',
        ], $abholblock, [
            'Bitte beachten Sie: Mit der Reservierung kommt noch kein Kaufvertrag',
            'zustande. Der Kauf wird bei der Abholung vor Ort abgeschlossen. Es handelt',
            'sich durchweg um gebrauchte Gegenstände, die wie besichtigt verkauft werden.',
            '',
            'Möchten Sie die Reservierung zurücknehmen? Eine kurze Antwort auf diese',
            'E-Mail genügt.',
            '',
            'Mit freundlichen Grüßen',
            $firma,
        ]));
        return wp_mail($v['email'], $betreff, $text, [
            'Content-Type: text/plain; charset=UTF-8',
            'Reply-To: ' . $absender,
        ]);
    }

    public static function eur($v) {
        return number_format((float) $v, 2, ',', '.') . ' €';
    }
}
