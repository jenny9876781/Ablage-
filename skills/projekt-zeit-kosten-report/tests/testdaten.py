"""Erfundene Testdaten (keine echten Termine/Fahrten). Nur die Mitarbeiter-
namen kommen aus der Config, weil Sätze und Fahrzeugzuordnung daran hängen.

Szenario: Basis-Bericht Sep–Okt 2026 (v01), Fortführung November 2026 (v02).
"""
import csv
from datetime import datetime

MN, FS, JP = 'Marius Neininger', 'Felix Seltmann', 'Jennifer Preisigke'

# (Betreff, Start, Ende)  – Format 'YYYY-MM-DD HH:MM'
MARIUS_BASIS = [
    ('"Koko" Dokumentenerstellung NBO', '2026-09-01 09:00', '2026-09-01 11:00'),
    ('"Sand" Abstimmung Unterlagen', '2026-09-02 14:00', '2026-09-02 15:30'),           # Alias
    ('"Cool" Kundentermin vor Ort', '2026-09-03 10:00', '2026-09-03 12:00'),            # Fahrt-Match
    ('"Zeppelin" Telefonat', '2026-09-07 09:00', '2026-09-07 09:30'),                   # 2 Projekte im Fenster
    ('"Forst" Termin bei Kunde', '2026-09-07 13:00', '2026-09-07 15:00'),
    ('"Hentzen" Termin vor Ort', '2026-09-15 10:00', '2026-09-15 12:00'),               # Partner Unberücks.
    ('Spedition Niedermaier', '2026-09-21 08:00', '2026-09-24 16:00'),                  # Block, Tageszählung
    ('"Spedition Niedermaier" Telefonat', '2026-09-28 10:00', '2026-09-28 10:30'),      # Kurztermin
    ('Urlaub', '2026-10-05 00:00', '2026-10-10 00:00'),                                 # Pauschale aussetzen
    ('"Barrierefrei" Erstgespräch', '2026-10-14 10:00', '2026-10-14 11:20'),            # 1,333 h
    ('"Fantasia" Kennenlernen', '2026-10-16 14:00', '2026-10-16 15:00'),                # unbekannt
    ('Montagssitzung intern', '2026-10-20 09:00', '2026-10-20 10:00'),                  # kein Projekt
    ('"Koko" Due Diligence Unterlagen sichten', '2026-10-22 09:00', '2026-10-22 12:00'),
    ('"Auf Herdenen" Treffen', '2026-10-29 10:00', '2026-10-29 11:00'),                 # ignoriert
]
FELIX_BASIS = [
    ('"Begamis" Akquise Anruf', '2026-09-02 10:00', '2026-09-02 10:20'),                # 0,333 h
    ('"Begamis" Angebot erstellen', '2026-09-10 13:00', '2026-09-10 16:00'),
    ('"Roadster" Vertragsdurchsicht Kaufvertrag', '2026-10-15 09:00', '2026-10-15 11:00'),
]
JENNIFER_BASIS = [
    ('"Koko" Terminvereinbarung', '2026-09-08 09:00', '2026-09-08 09:45'),
    ('MOSI "Cool"', '2026-10-20 08:00', '2026-10-20 09:00'),
]
# Nur in den v6-Fehlerfall-Tests (ändern bewusst die Zuordnung gegenüber Version 5)
MARIUS_FEHLERFAELLE = [
    ('„Koko“ Unterlagen', '2026-10-27 09:00', '2026-10-27 10:00'),          # typografisch
    ('"sand" Rückfragen', '2026-10-27 14:00', '2026-10-27 15:00'),                      # Kleinschreibung
    ('Abstimmung Zeppelin Unterlagen', '2026-10-28 09:00', '2026-10-28 10:00'),         # ohne Anführungsz.
]
JENNIFER_DUBLETTE = ('"Cool" Projektplanung', '2026-10-26 10:00', '2026-10-26 11:00')

# November (Fortführung) – Export enthält wie in echt den GANZEN Kalender
MARIUS_NOV = [
    ('"Koko" Kaufvertrag Entwurf', '2026-11-03 09:00', '2026-11-03 12:00'),
    ('"Zeppelin" Verhandlung vor Ort', '2026-11-10 10:00', '2026-11-10 13:00'),
]
MARIUS_NACHTRAG_OKT = ('"Forst" Nachbesprechung', '2026-10-30 09:00', '2026-10-30 10:00')

# (Start, Ende, km, Partner)
FAHRTEN_BASIS = [
    ('2026-09-03 08:30', '2026-09-03 09:40', 40.0, 'Cool Partner GmbH'),
    ('2026-09-07 11:30', '2026-09-07 12:40', 60.0, 'Forst Partner'),
    ('2026-09-12 10:00', '2026-09-12 11:00', 30.0, 'Frutania GmbH'),        # nur Partner-Zuordnung
    ('2026-09-15 08:00', '2026-09-15 09:00', 50.0, 'Vermietung'),           # Unberücksichtigt gewinnt
    ('2026-09-21 06:00', '2026-09-21 08:00', 200.0, 'Niedermaier'),         # Sonderkalk., Kosten 0
    ('2026-10-22 07:30', '2026-10-22 08:45', 80.0, 'Koko Partner'),
    ('2026-10-29 09:00', '2026-10-29 09:40', 20.0, 'Kikripp GmbH'),
]
FAHRTEN_NOV = [
    ('2026-11-10 08:00', '2026-11-10 09:30', 90.0, 'Zeppelin Partner'),
]


def schreibe_outlook(path, termine):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['Betreff', 'Beginnt am', 'Beginnt um', 'Endet am', 'Endet um', 'Ganztägiges Ereignis', 'Ort'])
        for betreff, s, e in termine:
            s, e = datetime.strptime(s, '%Y-%m-%d %H:%M'), datetime.strptime(e, '%Y-%m-%d %H:%M')
            w.writerow([betreff, f'{s.day}.{s.month}.{s.year}', s.strftime('%H:%M:%S'),
                        f'{e.day}.{e.month}.{e.year}', e.strftime('%H:%M:%S'), 'Aus', ''])
    return str(path)


def schreibe_autolog(path, fahrten, kennzeichen='VS MN 1000'):
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['Kennzeichen', 'Start', 'Ende', 'Distanz (km)', 'Fahrtart', 'Fahrer', 'Partner', 'Zweck',
                    'Start-Adresse', 'End-Adresse'])
        for s, e, km, partner in fahrten:
            s, e = datetime.strptime(s, '%Y-%m-%d %H:%M'), datetime.strptime(e, '%Y-%m-%d %H:%M')
            w.writerow([kennzeichen, s.strftime('%d.%m.%y %H:%M'), e.strftime('%d.%m.%y %H:%M'),
                        str(km), 'Geschäftlich', 'Falscher Name', partner, 'Termin',
                        'Musterstraße 1, 78000 Musterstadt', 'Kundenweg 2, 70000 Kundenstadt'])
        # Privatfahrt ohne Uhrzeit (bekannte Eigenheit) – muss ignoriert werden
        w.writerow([kennzeichen, '13.09.26', '13.09.26', '12', 'Privat', '', '', '', '', ''])
    return str(path)


def specs(verz, marius, felix=FELIX_BASIS, jennifer=JENNIFER_BASIS, jennifer2=None, fahrten=FAHRTEN_BASIS,
          tag='basis'):
    """Schreibt die CSVs und liefert (calendar_specs, autolog_specs)."""
    cs = [
        {'path': schreibe_outlook(verz / f'mn_{tag}.csv', marius), 'mitarbeiter': MN, 'kalendertyp': 'intern'},
        {'path': schreibe_outlook(verz / f'fs_{tag}.csv', felix), 'mitarbeiter': FS, 'kalendertyp': 'intern'},
        {'path': schreibe_outlook(verz / f'jp_{tag}.csv', jennifer), 'mitarbeiter': JP, 'kalendertyp': 'intern'},
    ]
    if jennifer2:
        cs.append({'path': schreibe_outlook(verz / f'jp2_{tag}.csv', jennifer2), 'mitarbeiter': JP,
                   'kalendertyp': 'TransCare'})
    al = [{'path': schreibe_autolog(verz / f'autolog_{tag}.csv', fahrten), 'kennzeichen': 'VSMN1000'}]
    return cs, al
