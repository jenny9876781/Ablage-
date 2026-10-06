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
        'kikripp_ablauftext'       => implode("\n", [
            'Die Artikel bleiben 3 Werktage für Sie reserviert. Nach Eingang Ihrer Reservierung rufen wir Sie an.',
            'Mindestbestellwert: 50,00 €.',
            'Artikel ab 100,00 € können Sie gern vorab besichtigen: donnerstags von 08:00 bis 11:00 Uhr nach Vereinbarung.',
            'Eine Reservierung ist noch kein Kaufvertrag. Der Kaufvertrag kommt mit Ihrer unterschriebenen Bestellung zustande.',
            'Unternehmen erhalten die Rechnung per E-Mail und überweisen vorab auf das angegebene Konto. Privatpersonen unterschreiben die Bestellung bei der Besichtigung oder Abholung und überweisen vor Ort vor der Übergabe. Abgeholt wird in jedem Fall erst nach Zahlungseingang.',
            'Abholzeiten: montags und dienstags von 08:00 bis 11:00 Uhr. Demontage und Abholung nach Vereinbarung auch Freitagnachmittag oder Samstagvormittag. Bitte bringen Sie Werkzeug mit.',
            'Abholung bis spätestens 10.12.2026. Nicht abgeholte Ware geht ohne Erstattung in unser Eigentum zurück.',
        ]),
        'kikripp_rechtstext'       => implode("\n\n", [
            'Gebrauchte Artikel aus Betriebsauflösung. Besichtigung und Funktionsprüfung vor Kauf ausdrücklich erwünscht. '
            . 'Verkauf im vorhandenen Zustand. Abholung durch den Käufer. Gewährleistung gegenüber Unternehmern ausgeschlossen. '
            . 'Gegenüber Verbrauchern gelten die gesetzlichen Bestimmungen; die Verjährungsfrist für Mängelansprüche bei '
            . 'gebrauchten Sachen wird, soweit zulässig, auf ein Jahr verkürzt. Irrtümer und Zwischenverkauf vorbehalten.',
            'Steuerfreie Lieferung gemäß § 4 Nr. 28 UStG. Der veräußerte Gegenstand wurde ausschließlich für Umsätze verwendet, '
            . 'die nach § 4 Nr. 23 UStG steuerfrei waren. Ein Vorsteuerabzug aus der Anschaffung oder den laufenden '
            . 'Aufwendungen war daher ausgeschlossen. Die Veräußerung erfolgt steuerfrei; Umsatzsteuer wird nicht berechnet '
            . 'und nicht ausgewiesen.',
        ]),
    ];
}
