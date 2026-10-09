<?php
if (!defined('ABSPATH')) { exit; }

/**
 * Abwicklung nach der Reservierung (1.3.0): Aufgabenliste, Kennzahlen, Abholplan,
 * Outlook-Termine und fertige Mailtexte.
 *
 * Alles wird aus den Vorgängen gerechnet – es gibt keine zweite Liste, die man pflegen
 * müsste. Mails verschickt das Plugin bewusst nicht selbst: der Webserver von kikripp.de
 * stellt an Microsoft-Adressen nicht zu (siehe Arbeitsanweisung, Abschnitt 9). Die Mailtexte
 * öffnen sich deshalb im eigenen Mailprogramm, die Erinnerungen kommen aus Outlook.
 */
class Kikripp_Ablauf {

    const ZEITEN = ['08:00', '08:30', '09:00', '09:30', '10:00', '10:30'];
    const WOCHENTAGE = ['', 'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'];

    public static function start() {
        add_action('admin_menu', [__CLASS__, 'menue'], 20);
        add_action('wp_dashboard_setup', [__CLASS__, 'dashboard']);
        add_action('admin_post_kikripp_ics', [__CLASS__, 'ics_herunterladen']);
        add_action('admin_post_kikripp_abholplan_druck', [__CLASS__, 'druck']);
    }

    public static function menue() {
        add_submenu_page('kikripp-reservierungen', 'Abholplan', 'Abholplan', 'manage_options',
            'kikripp-abholplan', [__CLASS__, 'seite_abholplan']);
    }

    // ------------------------------------------------------------ Grundbausteine

    public static function heute() { return substr(current_time('mysql'), 0, 10); }

    /** Nächster Werktag (Mo–Fr) nach einem Datum. */
    public static function naechster_werktag($ymd) {
        $t = strtotime($ymd . ' 12:00:00 UTC');
        do { $t += DAY_IN_SECONDS; } while ((int) gmdate('N', $t) > 5);
        return gmdate('Y-m-d', $t);
    }

    /** Werktag davor – für eine Montagsabholung ist das der Freitag. */
    public static function vorheriger_werktag($ymd) {
        $t = strtotime($ymd . ' 12:00:00 UTC');
        do { $t -= DAY_IN_SECONDS; } while ((int) gmdate('N', $t) > 5);
        return gmdate('Y-m-d', $t);
    }

    public static function tage_zwischen($von, $bis) {
        return (int) round((strtotime($bis . ' 12:00:00 UTC') - strtotime($von . ' 12:00:00 UTC')) / DAY_IN_SECONDS);
    }

    public static function privat($v) { return trim((string) ($v['firma'] ?? '')) === ''; }

    public static function wer($v) {
        $n = trim((string) $v['name']);
        $f = trim((string) ($v['firma'] ?? ''));
        if ($n === '' && $f === '') { return 'Vorgang #' . (int) $v['id']; }
        return $f !== '' ? ($n !== '' ? "$f ($n)" : $f) : $n;
    }

    /** „Dienstag, 20.10.2026 um 10:30 Uhr“ */
    public static function termin_text($abholung, $kurz = false) {
        if (!preg_match('/^(\d{4})-(\d{2})-(\d{2}) (\d{2}:\d{2})$/', (string) $abholung, $m)) { return ''; }
        $t = strtotime("$m[1]-$m[2]-$m[3] 12:00:00 UTC");
        $tag = self::WOCHENTAGE[(int) gmdate('N', $t)];
        return $kurz ? substr($tag, 0, 2) . " $m[3].$m[2]., $m[4] Uhr"
                     : "$tag, $m[3].$m[2].$m[1] um $m[4] Uhr";
    }

    public static function datum_text($ymd) {
        return preg_match('/^(\d{4})-(\d{2})-(\d{2})/', (string) $ymd, $m) ? "$m[3].$m[2].$m[1]" : '';
    }

    /** Aktive (nicht stornierte) Positionen mit Bezeichnung und Raum. */
    public static function positionen($v) {
        $out = [];
        foreach ($v['positionen'] as $p) {
            if ($p['status'] === 'storniert') { continue; }
            $d = json_decode((string) ($p['daten'] ?? ''), true);
            $d = is_array($d) ? $d : [];
            $code = strtok((string) $p['artnr'], '-');
            $raum = trim((string) ($d['raum'] ?? ''));
            $out[] = [
                'artnr' => $p['artnr'], 'menge' => (int) $p['menge'], 'preis' => (float) $p['preis_netto'],
                'titel' => (string) ($d['titel'] ?? ''), 'einheit' => (string) ($d['einheit'] ?? 'Stück'),
                'raum'  => $raum !== '' ? "$raum ($code)" : $code,
            ];
        }
        return $out;
    }

    public static function summe($v) {
        $s = 0.0;
        foreach (self::positionen($v) as $p) { $s += $p['preis'] * $p['menge']; }
        return $s;
    }

    /** In welchen Reiter gehört ein Vorgang? */
    public static function reiter_von($v, $jetzt) {
        if ($v['status'] === 'storniert') { return 'erledigt'; }
        if ($v['status'] === 'offen') { return strtotime($v['ablauf']) < $jetzt ? 'erledigt' : 'neu'; }
        if ($v['status'] === 'bestellt') { return 'bestellt'; }
        return trim((string) ($v['abgeholt_am'] ?? '')) !== '' ? 'abgeholt' : 'bezahlt';
    }

    // ------------------------------------------------------------ C: Zu erledigen

    /**
     * Die Aufgabenliste. Jede Aufgabe: id (Vorgang), text, art (warn = muss gemacht werden,
     * info = nur zur Kenntnis). Sortiert: erst Warnungen, darin nach Dringlichkeit.
     */
    public static function aufgaben(array $vorgaenge, $jetzt = null) {
        $jetzt = $jetzt ?? current_time('timestamp');
        $heute = gmdate('Y-m-d', $jetzt);
        $morgen = self::naechster_werktag($heute);
        $zahl_tage = max(1, (int) get_option('kikripp_zahlung_tage', 5));
        $liste = [];
        $neu = function ($v, $text, $art, $rang) use (&$liste) {
            $liste[] = ['id' => (int) $v['id'], 'wer' => self::wer($v), 'text' => $text, 'art' => $art, 'rang' => $rang];
        };
        foreach ($vorgaenge as $v) {
            if (!empty($v['testdaten']) && !get_option('kikripp_vorschau', 1)) { continue; }
            $tag = substr((string) ($v['abholung'] ?? ''), 0, 10);
            $abgeholt = trim((string) ($v['abgeholt_am'] ?? '')) !== '';
            $kontakt = (int) ($v['kontakt_weg'] ?? 0) === 0 && trim((string) $v['name']) !== '';
            switch ($v['status']) {
                case 'offen':
                    $ablauf = strtotime($v['ablauf']);
                    if ($ablauf < $jetzt) {
                        $neu($v, 'Reservierung ohne Rückmeldung abgelaufen – stornieren oder Frist verlängern.', 'warn', 5);
                    } elseif (substr($v['ablauf'], 0, 10) <= $morgen) {
                        $neu($v, 'Reservierung läuft ' . (substr($v['ablauf'], 0, 10) === $heute ? 'heute' : 'am '
                            . self::datum_text($v['ablauf'])) . ' ab – beim Interessenten melden und auf „bestellt“ setzen.', 'warn', 1);
                    } else {
                        $neu($v, 'Neue Reservierung – beim Interessenten melden.', 'warn', 3);
                    }
                    break;
                case 'bestellt':
                    if ($tag !== '' && $tag <= $morgen) {
                        $neu($v, 'Abholung ' . ($tag < $heute ? 'war am ' . self::datum_text($tag) : ($tag === $heute ? 'heute' : 'am '
                            . self::termin_text($v['abholung'], true))) . ' – noch nicht bezahlt!', 'warn', 0);
                    }
                    if (trim((string) $v['rechnungsnr']) === '') {
                        $neu($v, 'Rechnung schreiben und die Rechnungsnummer eintragen.', 'warn', 2);
                    } elseif (($v['rechnung_am'] ?? '') !== '' && self::tage_zwischen($v['rechnung_am'], $heute) >= $zahl_tage) {
                        $neu($v, 'Seit ' . self::tage_zwischen($v['rechnung_am'], $heute) . ' Tagen unbezahlt – Zahlungserinnerung schicken.', 'warn', 4);
                    }
                    if ($tag === '') { $neu($v, 'Abholtermin eintragen.', 'warn', 2); }
                    break;
                case 'bezahlt':
                    if ($abgeholt) {
                        $frist = self::privat($v) ? self::tage_zwischen($v['abgeholt_am'], $heute) >= 14 : true;
                        if ($kontakt && $frist) { $neu($v, 'Abgewickelt – Kontaktdaten löschen.', 'info', 9); }
                    } elseif ($tag !== '' && $tag < $heute) {
                        $neu($v, 'Abholtermin war am ' . self::datum_text($tag) . ' – abgeholt? Bitte vermerken.', 'warn', 1);
                    } elseif ($tag === '') {
                        $neu($v, 'Bezahlt, aber noch kein Abholtermin eingetragen.', 'warn', 2);
                    } elseif ($tag <= $morgen) {
                        $neu($v, 'Abholung ' . ($tag === $heute ? 'heute' : self::termin_text($v['abholung'], true))
                            . ' – Ware bereitstellen.', 'info', 6);
                    }
                    break;
                case 'storniert':
                    if ($kontakt) { $neu($v, 'Storniert – Kontaktdaten löschen.', 'info', 9); }
                    break;
            }
        }
        usort($liste, function ($a, $b) {
            return [$a['art'] === 'warn' ? 0 : 1, $a['rang'], $a['id']] <=> [$b['art'] === 'warn' ? 0 : 1, $b['rang'], $b['id']];
        });
        return $liste;
    }

    public static function aufgaben_html(array $aufgaben, $max = 0) {
        if (!$aufgaben) { return '<p style="margin:0">Nichts zu tun. 👍</p>'; }
        $html = '<ul style="margin:0">';
        foreach ($max ? array_slice($aufgaben, 0, $max) : $aufgaben as $a) {
            $farbe = $a['art'] === 'warn' ? '#b32d2e' : '#2271b1';
            $html .= '<li style="margin:3px 0"><span style="color:' . $farbe . '">●</span> '
                . '<a href="' . esc_url(admin_url('admin.php?page=kikripp-reservierungen&reiter=alle#vorgang-' . $a['id'])) . '">#'
                . $a['id'] . ' ' . esc_html($a['wer']) . '</a>: ' . esc_html($a['text']) . '</li>';
        }
        if ($max && count($aufgaben) > $max) {
            $html .= '<li>… und ' . (count($aufgaben) - $max) . ' weitere</li>';
        }
        return $html . '</ul>';
    }

    // ------------------------------------------------------------ F: Kennzahlen

    public static function kennzahlen(array $vorgaenge, $jetzt = null) {
        $jetzt = $jetzt ?? current_time('timestamp');
        $k = ['bezahlt' => 0.0, 'rechnung_offen' => 0.0, 'ohne_rechnung' => 0.0, 'reserviert' => 0.0];
        foreach ($vorgaenge as $v) {
            if (!empty($v['testdaten']) && !get_option('kikripp_vorschau', 1)) { continue; }
            $s = self::summe($v);
            $r = self::reiter_von($v, $jetzt);
            if ($r === 'bezahlt' || $r === 'abgeholt') { $k['bezahlt'] += $s; }
            elseif ($r === 'bestellt') { $k[trim((string) $v['rechnungsnr']) !== '' ? 'rechnung_offen' : 'ohne_rechnung'] += $s; }
            elseif ($r === 'neu') { $k['reserviert'] += $s; }
        }
        return $k;
    }

    // ------------------------------------------------------------ D: Mailtexte

    /**
     * Betreff und Text für die Mail an den Käufer. $art: rechnung | erinnerung.
     * Sie/Du kommt aus dem Vorgang, Privat/Firma aus dem Feld „Firma“.
     */
    public static function mail_text($v, $art = 'rechnung') {
        $du = !empty($v['du']);
        $privat = self::privat($v);
        $name = trim((string) $v['name']);
        $vorname = $name !== '' ? strtok($name, ' ') : '';
        $termin = self::termin_text($v['abholung'] ?? '') ?: '[Abholtermin]';
        $absender = trim((string) get_option('kikripp_mail_name', 'Jenny Preisigke'));
        $firma = (string) get_option('kikripp_firma', 'Kikripp GmbH');
        $tel = (string) get_option('kikripp_telefon', '');
        $mail = Kikripp_REST::kontakt_email();
        $adresse = (string) get_option('kikripp_abholadresse', '');
        $zufahrt = trim((string) get_option('kikripp_zufahrt', ''));
        $rnr = trim((string) ($v['rechnungsnr'] ?? ''));
        $ihr = $du && !$privat;     // Firma per Du: „ihr“

        if ($du) {
            $anrede = $privat ? 'Hallo ' . ($vorname ?: '[Vorname]') . ',' : 'Hallo zusammen,';
            $gruss = "Viele Grüße\n$absender\n$firma";
        } else {
            $anrede = $privat ? 'Guten Tag ' . ($name ?: '[Name]') . ',' : 'Sehr geehrte Damen und Herren,';
            $gruss = "Mit freundlichen Grüßen\n$absender\n$firma";
        }
        $w = function ($sie, $du_text, $ihr_text) use ($du, $ihr) { return $ihr ? $ihr_text : ($du ? $du_text : $sie); };

        if ($art === 'erinnerung') {
            $betreff = 'Zahlungserinnerung' . ($rnr !== '' ? " – Rechnung $rnr" : '');
            $text = "$anrede\n\n"
                . $w('zu unserer Rechnung', 'zu unserer Rechnung', 'zu unserer Rechnung')
                . ($rnr !== '' ? " Nr. $rnr" : '')
                . (!empty($v['rechnung_am']) ? ' vom ' . self::datum_text($v['rechnung_am']) : '')
                . ' über ' . Kikripp_Mail::eur(self::summe($v)) . ' konnten wir noch keinen Zahlungseingang feststellen. '
                . $w('Bitte überweisen Sie den Betrag zeitnah unter Angabe der Rechnungsnummer, damit wir Ihren Abholtermin ',
                     'Bitte überweise den Betrag zeitnah unter Angabe der Rechnungsnummer, damit wir deinen Abholtermin ',
                     'Bitte überweist den Betrag zeitnah unter Angabe der Rechnungsnummer, damit wir euren Abholtermin ')
                . "am $termin halten können.\n\n"
                . $w('Sollte sich Ihre Zahlung mit dieser Nachricht überschnitten haben, betrachten Sie sie bitte als gegenstandslos.',
                     'Falls sich deine Zahlung mit dieser Nachricht überschnitten hat, betrachte sie bitte als gegenstandslos.',
                     'Falls sich eure Zahlung mit dieser Nachricht überschnitten hat, betrachtet sie bitte als gegenstandslos.')
                . "\n\n$gruss";
            return [$betreff, $text];
        }

        $betreff = 'Rechnung und Abholtermin – Kikripp Artikelkatalog';
        $text = "$anrede\n\n"
            . $w('vielen Dank für Ihre Reservierung aus unserem Artikelkatalog. Anbei erhalten Sie die Rechnung und Ihre Bestellung.',
                 'vielen Dank für deine Reservierung! Anbei findest du die Rechnung und deine Bestellung.',
                 'vielen Dank für eure Reservierung! Anbei findet ihr die Rechnung und eure Bestellung.')
            . "\n\n"
            . $w('Bitte überweisen Sie den Rechnungsbetrag zeitnah unter Angabe der Rechnungsnummer auf das angegebene Konto. '
                 . 'Die Bestellung senden Sie uns bitte unterschrieben per Scan zurück oder unterschreiben sie bei der Abholung.',
                 'Bitte überweise den Rechnungsbetrag zeitnah unter Angabe der Rechnungsnummer auf das angegebene Konto. '
                 . 'Die Bestellung kannst du uns unterschrieben per Scan zurückschicken oder bei der Abholung unterschreiben.',
                 'Bitte überweist den Rechnungsbetrag zeitnah unter Angabe der Rechnungsnummer auf das angegebene Konto. '
                 . 'Die Bestellung schickt ihr uns bitte unterschrieben per Scan zurück oder unterschreibt sie bei der Abholung.')
            . "\n\n"
            . $w('Ihr', 'Dein', 'Euer') . " Abholtermin: $termin\n"
            . "Der Termin ist mit dem Zahlungseingang bestätigt – die Ware geben wir erst nach Zahlungseingang heraus.\n\n"
            . ($adresse !== '' ? "Abholadresse: $adresse\n" : '')
            . ($zufahrt !== '' ? "$zufahrt\n" : '')
            . $w('Bitte bringen Sie', 'Bitte bring', 'Bitte bringt') . " ausreichend Helfer, Werkzeug und ein passendes Fahrzeug mit.\n\n"
            . ($privat ? $w('Die Widerrufsbelehrung und das Widerrufsformular finden Sie in der beigefügten Bestellung.',
                            'Die Widerrufsbelehrung und das Widerrufsformular findest du in der beigefügten Bestellung.', '') . "\n\n" : '')
            . $w('Bei Fragen erreichen Sie uns', 'Bei Fragen erreichst du uns', 'Bei Fragen erreicht ihr uns')
            . " unter $tel oder $mail.\n\n$gruss";
        return [$betreff, $text];
    }

    public static function mailto($v, $art = 'rechnung') {
        list($betreff, $text) = self::mail_text($v, $art);
        return 'mailto:' . rawurlencode(trim((string) $v['email'])) . '?subject=' . rawurlencode($betreff)
            . '&body=' . rawurlencode(str_replace("\n", "\r\n", $text));
    }

    // ------------------------------------------------------------ A: Outlook-Termine

    private static function zeitzone() {
        return function_exists('wp_timezone') ? wp_timezone() : new DateTimeZone('Europe/Berlin');
    }

    /** Ortszeit „Y-m-d H:i“ → UTC im iCalendar-Format. */
    public static function ics_zeit($lokal, $plus_min = 0) {
        $d = new DateTime($lokal, self::zeitzone());
        if ($plus_min) { $d->modify("+$plus_min minutes"); }
        $d->setTimezone(new DateTimeZone('UTC'));
        return $d->format('Ymd\THis\Z');
    }

    private static function ics_text($t) {
        return str_replace(["\\", ";", ",", "\r\n", "\n"], ["\\\\", "\\;", "\\,", "\\n", "\\n"], (string) $t);
    }

    /** Zeilen über 75 Zeichen falten (RFC 5545), ohne UTF-8-Zeichen zu zerschneiden. */
    private static function falten($zeile) {
        $out = ''; $rest = $zeile; $erste = true;
        while (strlen($rest) > ($erste ? 75 : 74)) {
            $n = $erste ? 75 : 74;
            while ($n > 0 && (ord($rest[$n]) & 0xC0) === 0x80) { $n--; }
            $out .= ($erste ? '' : ' ') . substr($rest, 0, $n) . "\r\n";
            $rest = substr($rest, $n); $erste = false;
        }
        return $out . ($erste ? '' : ' ') . $rest . "\r\n";
    }

    /**
     * Zwei Termine in einer Datei: die Abholung selbst (Erinnerung 15 Minuten vorher) und
     * „vorbereiten“ am Werktag davor um 14:00 (Erinnerung zur Startzeit). Outlook kennt nur
     * eine Erinnerung je Termin – deshalb zwei Termine. Feste UIDs je Vorgang, damit ein
     * erneuter Import den Termin ersetzt statt ihn zu verdoppeln.
     */
    public static function ics($v) {
        if (!preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/', (string) ($v['abholung'] ?? ''))) { return ''; }
        $id = (int) $v['id'];
        $pos = self::positionen($v);
        $zeilen = [];
        foreach ($pos as $p) { $zeilen[] = "{$p['menge']} × {$p['artnr']} {$p['titel']} – Raum {$p['raum']}"; }
        $bezahlt = $v['status'] === 'bezahlt' ? 'ja' : 'NOCH NICHT BEZAHLT';
        $info = "Vorgang #$id · " . self::wer($v) . "\n"
            . (trim((string) $v['telefon']) !== '' ? 'Telefon: ' . $v['telefon'] . "\n" : '')
            . (trim((string) $v['rechnungsnr']) !== '' ? 'Rechnung: ' . $v['rechnungsnr'] . "\n" : '')
            . "Bezahlt (beim Eintragen in Outlook): $bezahlt\n"
            . (!empty($v['demontage']) ? "Demontage nötig\n" : '')
            . (trim((string) ($v['notiz'] ?? '')) !== '' ? 'Notiz: ' . $v['notiz'] . "\n" : '')
            . "\nArtikel:\n" . implode("\n", $zeilen);
        $ort = (string) get_option('kikripp_abholadresse', '');
        $kurz = self::wer($v) . ' (' . array_sum(array_column($pos, 'menge')) . ' Stück)';
        $tag = substr($v['abholung'], 0, 10);
        $vortag = self::vorheriger_werktag($tag) . ' ' . (get_option('kikripp_erinnerung_zeit', '14:00') ?: '14:00');
        $stempel = gmdate('Ymd\THis\Z');
        $seq = time();
        $ereignis = function ($uid, $start, $dauer, $titel, $alarm) use ($stempel, $seq, $info, $ort) {
            return [
                'BEGIN:VEVENT', "UID:$uid", "DTSTAMP:$stempel", "SEQUENCE:$seq",
                'DTSTART:' . self::ics_zeit($start), 'DTEND:' . self::ics_zeit($start, $dauer),
                'SUMMARY:' . self::ics_text($titel), 'LOCATION:' . self::ics_text($ort),
                'DESCRIPTION:' . self::ics_text($info), 'TRANSP:OPAQUE', 'STATUS:CONFIRMED',
                'BEGIN:VALARM', 'ACTION:DISPLAY', 'DESCRIPTION:' . self::ics_text($titel), "TRIGGER:$alarm", 'END:VALARM',
                'END:VEVENT',
            ];
        };
        $teile = array_merge(
            ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Kikripp GmbH//Artikelkatalog//DE', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH'],
            $ereignis("kikripp-$id-abholung@kikripp.de", $v['abholung'], 30, "Abholung #$id: $kurz", '-PT15M'),
            $ereignis("kikripp-$id-vortag@kikripp.de", $vortag, 15,
                'Vorbereiten: Abholung ' . self::termin_text($v['abholung'], true) . " – #$id $kurz", 'PT0M'),
            ['END:VCALENDAR']
        );
        return implode('', array_map([__CLASS__, 'falten'], $teile));
    }

    public static function ics_url($id) {
        return wp_nonce_url(admin_url('admin-post.php?action=kikripp_ics&id=' . (int) $id), 'kikripp_ics_' . (int) $id);
    }

    public static function ics_herunterladen() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        $id = (int) ($_GET['id'] ?? 0);
        check_admin_referer('kikripp_ics_' . $id);
        $v = Kikripp_DB::vorgang($id);
        $ics = $v ? self::ics($v) : '';
        if ($ics === '') { wp_die('Für diesen Vorgang ist noch kein Abholtermin eingetragen.'); }
        nocache_headers();
        header('Content-Type: text/calendar; charset=utf-8');
        header('Content-Disposition: attachment; filename=abholung-' . $id . '.ics');
        echo $ics;
        exit;
    }

    // ------------------------------------------------------------ A: Abholplan

    /** Anstehende Abholungen: bestellt oder bezahlt, Termin gesetzt, noch nicht abgeholt. */
    public static function anstehend(array $vorgaenge) {
        $liste = array_filter($vorgaenge, function ($v) {
            return in_array($v['status'], ['bestellt', 'bezahlt'], true)
                && preg_match('/^\d{4}-\d{2}-\d{2} /', (string) ($v['abholung'] ?? ''))
                && trim((string) ($v['abgeholt_am'] ?? '')) === '';
        });
        usort($liste, function ($a, $b) { return [$a['abholung'], $a['id']] <=> [$b['abholung'], $b['id']]; });
        return $liste;
    }

    private static function karte($v, $druck = false) {
        $bezahlt = $v['status'] === 'bezahlt';
        $h = '<div class="kik-karte" style="border:1px solid #ccd0d4;border-left:4px solid ' . ($bezahlt ? '#00a32a' : '#d63638')
           . ';background:#fff;padding:10px 14px;margin:0 0 12px;break-inside:avoid">';
        $h .= '<div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">'
            . '<div><strong style="font-size:15px">' . esc_html(substr($v['abholung'], 11)) . ' Uhr · ' . esc_html(self::wer($v)) . '</strong>'
            . ' <span style="color:#555">#' . (int) $v['id'] . '</span><br>'
            . (trim((string) $v['telefon']) !== '' ? 'Tel. ' . esc_html($v['telefon']) . ' · ' : '')
            . 'Rechnung ' . (trim((string) $v['rechnungsnr']) !== '' ? esc_html($v['rechnungsnr']) : '<em>fehlt</em>')
            . (!empty($v['demontage']) ? ' · <strong>Demontage</strong>' : '') . '</div>'
            . '<div style="font-weight:600;color:' . ($bezahlt ? '#00a32a' : '#d63638') . '">'
            . ($bezahlt ? '✓ bezahlt' : '✗ NOCH NICHT BEZAHLT') . '</div></div>';
        if (trim((string) ($v['notiz'] ?? '')) !== '') {
            $h .= '<div style="margin:6px 0;padding:4px 8px;background:#fcf9e8">Notiz: ' . esc_html($v['notiz']) . '</div>';
        }
        $h .= '<table style="width:100%;border-collapse:collapse;margin-top:6px;font-size:13px">'
            . '<tr style="text-align:left;color:#555"><th style="width:28px">☐</th><th>Menge</th><th>Art.-Nr.</th><th>Bezeichnung</th><th>Raum (Post-it)</th></tr>';
        foreach (self::positionen($v) as $p) {
            $h .= '<tr style="border-top:1px solid #eee"><td style="font-size:16px">☐</td><td>' . $p['menge'] . ' ' . esc_html($p['einheit'])
                . '</td><td><strong>' . esc_html($p['artnr']) . '</strong></td><td>' . esc_html($p['titel'])
                . '</td><td>' . esc_html($p['raum']) . '</td></tr>';
        }
        $h .= '</table>';
        if (!$druck) {
            $h .= '<p style="margin:8px 0 0"><a class="button button-small" href="' . esc_url(Kikripp_Admin::aktion_url('abgeholt', $v['id']))
                . '"' . ($bezahlt ? '' : ' onclick="return confirm(\'Noch nicht als bezahlt vermerkt. Trotzdem abgeholt (wird dabei als bezahlt vermerkt)?\')"')
                . '>✓ abgeholt</a> <a class="button button-small" href="' . esc_url(self::ics_url($v['id'])) . '">📅 In Outlook eintragen</a> '
                . '<a class="button button-small" href="' . esc_url(admin_url('admin.php?page=kikripp-reservierungen&reiter=alle#vorgang-' . (int) $v['id']))
                . '">Vorgang öffnen</a></p>';
        }
        return $h . '</div>';
    }

    public static function seite_abholplan() {
        if (!current_user_can('manage_options')) { return; }
        $alle = Kikripp_DB::vorgaenge();
        $heute = self::heute();
        $nach_tag = [];
        foreach (self::anstehend($alle) as $v) { $nach_tag[substr($v['abholung'], 0, 10)][] = $v; }
        echo '<div class="wrap"><h1>Abholplan</h1>';
        echo '<p style="color:#555;max-width:900px">Alle bestellten und bezahlten Vorgänge mit Abholtermin, die noch nicht abgeholt sind. '
           . 'Rot = noch nicht bezahlt. Vor dem Abholtag „Tag drucken“ – das ist die Liste zum Bereitstellen.</p>';
        if (!$nach_tag) { echo '<p>Keine Abholungen geplant.</p>'; }
        foreach ($nach_tag as $tag => $liste) {
            $t = strtotime($tag . ' 12:00:00 UTC');
            $titel = self::WOCHENTAGE[(int) gmdate('N', $t)] . ', ' . self::datum_text($tag);
            if ($tag < $heute) { $titel .= ' – <span style="color:#b32d2e">vorbei, nicht als abgeholt vermerkt</span>'; }
            elseif ($tag === $heute) { $titel .= ' – heute'; }
            elseif ($tag === self::naechster_werktag($heute)) { $titel .= ' – nächster Werktag'; }
            $druck = wp_nonce_url(admin_url('admin-post.php?action=kikripp_abholplan_druck&tag=' . $tag), 'kikripp_druck');
            echo '<h2 style="margin-top:24px">' . $titel . ' <a class="button" style="vertical-align:middle" target="_blank" href="'
               . esc_url($druck) . '">🖨 Tag drucken</a></h2>';
            foreach ($liste as $v) { echo self::karte($v); }
        }
        $ohne = array_filter($alle, function ($v) {
            return in_array($v['status'], ['bestellt', 'bezahlt'], true) && trim((string) ($v['abholung'] ?? '')) === ''
                && trim((string) ($v['abgeholt_am'] ?? '')) === '';
        });
        if ($ohne) {
            echo '<h2 style="margin-top:24px">Noch ohne Abholtermin</h2><ul>';
            foreach ($ohne as $v) {
                echo '<li><a href="' . esc_url(admin_url('admin.php?page=kikripp-reservierungen&reiter=alle#vorgang-' . (int) $v['id'])) . '">#'
                   . (int) $v['id'] . ' ' . esc_html(self::wer($v)) . '</a> – Wunsch: ' . esc_html(Kikripp_Mail::abholung_text($v)) . '</li>';
            }
            echo '</ul>';
        }
        echo '</div>';
    }

    /** Druckansicht eines Tages – die Kommissionierliste. */
    public static function druck() {
        if (!current_user_can('manage_options')) { wp_die('Keine Berechtigung.'); }
        check_admin_referer('kikripp_druck');
        $tag = preg_match('/^\d{4}-\d{2}-\d{2}$/', (string) ($_GET['tag'] ?? '')) ? $_GET['tag'] : self::heute();
        echo self::druck_html($tag);
        exit;
    }

    public static function druck_html($tag) {
        $liste = array_filter(self::anstehend(Kikripp_DB::vorgaenge()), function ($v) use ($tag) {
            return substr($v['abholung'], 0, 10) === $tag;
        });
        $t = strtotime($tag . ' 12:00:00 UTC');
        $titel = 'Abholungen ' . self::WOCHENTAGE[(int) gmdate('N', $t)] . ', ' . self::datum_text($tag);
        $h = '<!doctype html><html lang="de"><head><meta charset="utf-8"><title>' . esc_html($titel) . '</title>'
           . '<style>body{font:13px/1.4 Arial,Helvetica,sans-serif;max-width:900px;margin:20px auto;padding:0 16px;color:#1a1a1a}'
           . 'h1{font-size:20px;border-bottom:3px solid #C8102E;padding-bottom:6px}th{font-size:12px}'
           . '.knopf{background:#C8102E;color:#fff;border:0;padding:8px 14px;font-size:14px;cursor:pointer;border-radius:3px}'
           . '@media print{.knopf{display:none}body{margin:0}}</style></head><body>'
           . '<p><button class="knopf" onclick="window.print()">Drucken</button></p>'
           . '<h1>' . esc_html($titel) . '</h1>';
        if (!$liste) { $h .= '<p>An diesem Tag ist keine Abholung geplant.</p>'; }
        foreach ($liste as $v) { $h .= self::karte($v, true); }
        return $h . '<p style="color:#555;font-size:11px">Stand ' . esc_html(date_i18n('d.m.Y H:i')) . '</p></body></html>';
    }

    // ------------------------------------------------------------ C: Dashboard

    public static function dashboard() {
        if (!current_user_can('manage_options')) { return; }
        wp_add_dashboard_widget('kikripp_zu_tun', 'Artikelkatalog – zu erledigen', [__CLASS__, 'widget']);
    }

    public static function widget() {
        $alle = Kikripp_DB::vorgaenge();
        echo self::aufgaben_html(self::aufgaben($alle), 12);
        $anstehend = self::anstehend($alle);
        $heute = self::heute();
        $morgen = self::naechster_werktag($heute);
        $bald = array_filter($anstehend, function ($v) use ($morgen) { return substr($v['abholung'], 0, 10) <= $morgen; });
        echo '<p style="margin-top:10px"><strong>' . count($bald) . '</strong> Abholung(en) bis zum nächsten Werktag · '
           . '<a href="' . esc_url(admin_url('admin.php?page=kikripp-abholplan')) . '">Abholplan</a> · '
           . '<a href="' . esc_url(admin_url('admin.php?page=kikripp-reservierungen')) . '">Reservierungen</a></p>';
    }
}
