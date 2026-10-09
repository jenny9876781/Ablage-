<?php
if (!defined('ABSPATH')) { exit; }

/**
 * Verkaufsbedingungen ab Fassung 1.2.0 (Vorgaben der Kikripp GmbH vom 05.10.2026):
 * keine Umsatzsteuer, frei zugänglich, 3 Werktage Reservierung, Mindestbestellwert,
 * Besichtigung ab 100 € Stückpreis, Abholung bis 10.12.2026.
 */
function kikripp_vorgaben_120() {
    return [
        'kikripp_passwortschutz'   => 0,
        'kikripp_ust_prozent'      => 0,
        'kikripp_steuerhinweis'    => 'Endpreise · umsatzsteuerfrei gemäß § 4 Nr. 28 UStG',
        'kikripp_frist_werktage'   => 3,
        'kikripp_mindestwert'      => 50,
        'kikripp_besichtigung_ab'  => 100,
        'kikripp_abholschluss'     => '2026-12-10',
        'kikripp_ablauftext'       => kikripp_ablauf_123(),
        'kikripp_rechtstext'       => kikripp_rechtstext_123(),
    ];
}

/** Kaufbedingungen bis 1.2.2 – nur um sie beim Umstellen wiederzuerkennen. */
function kikripp_rechtstext_120() {
    return implode("\n\n", [
            'Gebrauchte Artikel aus Betriebsauflösung. Besichtigung und Funktionsprüfung vor Kauf ausdrücklich erwünscht. '
            . 'Verkauf im vorhandenen Zustand. Abholung durch den Käufer. Gewährleistung gegenüber Unternehmern ausgeschlossen. '
            . 'Gegenüber Verbrauchern gelten die gesetzlichen Bestimmungen; die Verjährungsfrist für Mängelansprüche bei '
            . 'gebrauchten Sachen wird, soweit zulässig, auf ein Jahr verkürzt. Irrtümer und Zwischenverkauf vorbehalten.',
            'Steuerfreie Lieferung gemäß § 4 Nr. 28 UStG. Der veräußerte Gegenstand wurde ausschließlich für Umsätze verwendet, '
            . 'die nach § 4 Nr. 23 UStG steuerfrei waren. Ein Vorsteuerabzug aus der Anschaffung oder den laufenden '
            . 'Aufwendungen war daher ausgeschlossen. Die Veräußerung erfolgt steuerfrei; Umsatzsteuer wird nicht berechnet '
            . 'und nicht ausgewiesen.',
        ]);
}

/**
 * 1.2.3: Seit 07.10.2026 zahlen auch Privatpersonen per Rechnung vor der Abholung. Der Vertrag
 * kommt dann ohne persönliches Treffen zustande, Verbraucher haben ein Widerrufsrecht. Die
 * Belehrung steht in der Bestellung für Privatpersonen; hier nur der Hinweis darauf.
 */
function kikripp_rechtstext_123() {
    return kikripp_rechtstext_120() . "\n\n" . 'Verbrauchern steht ein gesetzliches Widerrufsrecht zu. '
        . 'Die Widerrufsbelehrung und das Muster-Widerrufsformular erhalten Sie mit der Bestellung.';
}

/** Ablauftext 1.2.3 – Wortlaut der Nutzerin vom 07.10.2026: Bezahlung generell gegen Rechnung. */
function kikripp_ablauf_123() {
    return 'Ihre Auswahl bleibt 3 Werktage reserviert, nach Eingang melden wir uns bei Ihnen. '
        . 'Mindestbestellwert 50 €. Artikel ab 100 € können Sie donnerstags von 8 bis 11 Uhr nach '
        . 'Vereinbarung besichtigen. Der Kaufvertrag kommt mit der unterschriebenen Bestellung zustande.' . "\n"
        . 'Bezahlung: generell per Überweisung gegen Rechnung vor der Abholung. Abholung montags und dienstags '
        . 'von 8 bis 11 Uhr, Demontage nach Vereinbarung auch freitagnachmittags oder samstagvormittags (bitte '
        . 'Werkzeug mitbringen). Abholung spätestens bis 10.12.2026, danach geht nicht abgeholte Ware ohne '
        . 'Erstattung in unser Eigentum zurück.';
}

/** Ablauf als Fließtext (Fassung 1.2.2, Wunsch 06.10.2026: kürzer, „melden wir uns“). */
function kikripp_ablauf_122() {
    return 'Ihre Auswahl bleibt 3 Werktage reserviert, nach Eingang melden wir uns bei Ihnen. '
        . 'Mindestbestellwert 50 €. Artikel ab 100 € können Sie donnerstags von 8 bis 11 Uhr nach '
        . 'Vereinbarung besichtigen. Der Kaufvertrag kommt mit der unterschriebenen Bestellung zustande. '
        . 'Bezahlt wird per Überweisung vor der Abholung – Unternehmen nach Rechnung, Privatpersonen vor '
        . 'Ort bei der Übergabe. Abholung montags und dienstags von 8 bis 11 Uhr, Demontage nach '
        . 'Vereinbarung auch freitagnachmittags oder samstagvormittags (bitte Werkzeug mitbringen). '
        . 'Abholung spätestens bis 10.12.2026, danach geht nicht abgeholte Ware ohne Erstattung in unser '
        . 'Eigentum zurück.';
}

/** Der Ablauftext, den Fassung 1.2.0 eingetragen hat – nur um ihn beim Umstellen wiederzuerkennen. */
function kikripp_ablauf_120() {
    return implode("\n", [
            'Die Artikel bleiben 3 Werktage für Sie reserviert. Nach Eingang Ihrer Reservierung rufen wir Sie an.',
            'Mindestbestellwert: 50,00 €.',
            'Artikel ab 100,00 € können Sie gern vorab besichtigen: donnerstags von 08:00 bis 11:00 Uhr nach Vereinbarung.',
            'Eine Reservierung ist noch kein Kaufvertrag. Der Kaufvertrag kommt mit Ihrer unterschriebenen Bestellung zustande.',
            'Unternehmen erhalten die Rechnung per E-Mail und überweisen vorab auf das angegebene Konto. Privatpersonen unterschreiben die Bestellung bei der Besichtigung oder Abholung und überweisen vor Ort vor der Übergabe. Abgeholt wird in jedem Fall erst nach Zahlungseingang.',
            'Abholzeiten: montags und dienstags von 08:00 bis 11:00 Uhr. Demontage und Abholung nach Vereinbarung auch Freitagnachmittag oder Samstagvormittag. Bitte bringen Sie Werkzeug mit.',
            'Abholung bis spätestens 10.12.2026. Nicht abgeholte Ware geht ohne Erstattung in unser Eigentum zurück.',
        ]);
}

/** Vorgaben 1.3.0 (Abwicklung): nur setzen, was noch fehlt. */
function kikripp_vorgaben_130() {
    return [
        'kikripp_zufahrt'         => 'Die Zufahrt ist nur über die Peterzeller Straße 8 möglich: am Firmengelände vorbei '
                                   . 'bis ans Ende durchfahren, das Gebäude liegt auf der rechten Seite.',
        'kikripp_mail_name'       => 'Jenny Preisigke',
        'kikripp_erinnerung_zeit' => '11:00',
        'kikripp_termin_zusatz'   => 'Barrierefrei',
        'kikripp_zahlung_tage'    => 5,
    ];
}
