"""
report_lib.py — Kernlogik für den Neininger Projekt-Zeit-/Kosten-Report.

Version 2 (2026-07-22): Mehrjahres-Auswertung (2024ff.), Satzhistorie mit
Gültig-ab-Datum, Hauptaufgaben-Kategorien, automatische Wochenpauschale,
manuelle Zusatzkosten, Plausibilitätscheck, MwSt.-Ausweis, Filter-Dashboard.

Diese Bibliothek wird von Jahr/Monat zu Jahr/Monat wiederverwendet. Nur
config/projekt_konfiguration.json und die hochgeladenen Rohdateien ändern sich.
"""
import json
import re
from datetime import timedelta, datetime

import pandas as pd


# ==========================================================================
# Konfiguration
# ==========================================================================
def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _parse_date(s):
    return datetime.strptime(s, '%Y-%m-%d')


def get_rate_for_date(config, mitarbeiter, date):
    """Stundensatz für mitarbeiter am angegebenen Datum (letzter gültige Satz)."""
    saetze = config['mitarbeiter_satzhistorie'][mitarbeiter]['saetze']
    gueltige = [s for s in saetze if _parse_date(s['gueltig_ab']) <= date]
    if not gueltige:
        # kein Satz vor diesem Datum gueltig -> aeltesten nehmen, aber auffaellig machen
        return sorted(saetze, key=lambda s: s['gueltig_ab'])[0]['stundensatz_eur']
    return sorted(gueltige, key=lambda s: s['gueltig_ab'])[-1]['stundensatz_eur']


def get_kmrate_for_date(config, date):
    historie = config['km_satz_historie']
    gueltige = [s for s in historie if _parse_date(s['gueltig_ab']) <= date]
    if not gueltige:
        return sorted(historie, key=lambda s: s['gueltig_ab'])[0]['satz_eur_pro_km']
    return sorted(gueltige, key=lambda s: s['gueltig_ab'])[-1]['satz_eur_pro_km']


def classify_hauptaufgabe(aufgabe_text, kategorien_config, mitarbeiter=None):
    """Keyword-basierte Zuordnung zu einer Hauptaufgaben-Kategorie. Wenn kein
    Keyword passt UND ein mitarbeiter übergeben wird, greift der in
    'fallback_je_mitarbeiter' hinterlegte Standard (typische Hauptrolle der
    Person) statt eine generische 'Nicht eindeutig'-Meldung."""
    fallback_map = kategorien_config.get('fallback_je_mitarbeiter', {})
    default = 'Nicht eindeutig - bitte prüfen'
    if mitarbeiter and mitarbeiter in fallback_map:
        default = fallback_map[mitarbeiter]
    if not isinstance(aufgabe_text, str) or not aufgabe_text.strip():
        return default
    text = aufgabe_text.lower()
    for kategorie, keywords in kategorien_config.items():
        if kategorie.startswith('_') or kategorie == 'fallback_je_mitarbeiter':
            continue
        for kw in keywords:
            if kw.lower() in text:
                return kategorie
    return default


# ==========================================================================
# Kalender laden & Projektname extrahieren
# ==========================================================================
def extract_project(betreff, fixed_names, ignore_names=None, aliase=None):
    """Extrahiert Projektname aus Kalender-Betreff. Siehe Modul-Docstring frueherer
    Version: ignore_names wird NICHT zu None umgewandelt (Matching-Sicherheit).
    aliase: dict Kurzform -> offizieller Projektname (z.B. {'Nickles': 'Koko'})."""
    if not isinstance(betreff, str):
        return None, betreff
    aliase = aliase or {}

    def resolve(name):
        return aliase.get(name, name)

    m = re.search(r'"\s*([^"]+?)\s*"', betreff)
    if m:
        proj = re.sub(r'\s+', ' ', m.group(1).strip())
        proj = resolve(proj)
        rest = (betreff[:m.start()] + betreff[m.end():]).strip(' -/')
        return proj, rest
    for fixed in fixed_names:
        if fixed.lower() in betreff.lower():
            rest = betreff.replace(fixed, '').strip(' -/')
            return fixed, rest
    return None, betreff


def _enrich_calendar_df(df, mitarbeiter, kalendertyp, config):
    """Gemeinsame Anreicherung für alle Kalenderquellen: erwartet df mit Spalten
    Betreff, Start, Ende, Ort (Start/Ende als echte datetime). Fügt Mitarbeiter,
    Kalendertyp, Projekt, Aufgabe, Hauptaufgabe, Dauer_h, Mehrtaegig, Jahr,
    Ist_Urlaub, Ist_Pauschale hinzu."""
    df = df.copy()
    df['Mitarbeiter'] = mitarbeiter
    df['Kalendertyp'] = kalendertyp

    fixed_names = config['projektname_erkennung']['feste_namen_ohne_anfuehrungszeichen']
    ignore_names = config['projektname_erkennung']['ignorieren']
    aliase = config['projektname_erkennung'].get('aliase', {})
    aliase = {k: v for k, v in aliase.items() if not k.startswith('_')}
    df[['Projekt', 'Aufgabe']] = df['Betreff'].apply(
        lambda b: pd.Series(extract_project(b, fixed_names, ignore_names, aliase)))
    df['Dauer_h'] = (df['Ende'] - df['Start']).dt.total_seconds() / 3600.0
    df['Mehrtaegig'] = (df['Ende'] - df['Start']) > timedelta(hours=20)
    df['Hauptaufgabe'] = df['Aufgabe'].apply(
        lambda a: classify_hauptaufgabe(a, config.get('hauptaufgaben_kategorien', {}), mitarbeiter))
    df['Jahr'] = df['Start'].dt.year
    df['Ist_Urlaub'] = df['Betreff'].astype(str).str.lower().str.contains(
        config.get('wochenpauschale', {}).get('urlaub_erkennung_keyword', 'urlaub'))
    df['Ist_Pauschale'] = False
    return df[['Mitarbeiter', 'Kalendertyp', 'Betreff', 'Start', 'Ende', 'Ort',
                'Projekt', 'Aufgabe', 'Hauptaufgabe', 'Dauer_h', 'Mehrtaegig',
                'Jahr', 'Ist_Urlaub', 'Ist_Pauschale']]


def load_calendar_csv(path, mitarbeiter, kalendertyp, config,
                       period_start=None, period_end=None):
    """Lädt einen Outlook-CSV-Kalenderexport (deutsche Spaltennamen), extrahiert
    Projekt + Hauptaufgabe."""
    df = pd.read_csv(path)
    df = df[['Betreff', 'Beginnt am', 'Beginnt um', 'Endet am', 'Endet um', 'Ort']].copy()
    df['Start'] = pd.to_datetime(
        df['Beginnt am'].str.strip() + ' ' + df['Beginnt um'],
        format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df['Ende'] = pd.to_datetime(
        df['Endet am'].str.strip() + ' ' + df['Endet um'],
        format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df = _enrich_calendar_df(df, mitarbeiter, kalendertyp, config)
    if period_start is not None:
        df = df[df['Start'] >= period_start]
    if period_end is not None:
        df = df[df['Start'] <= period_end]
    return df


def load_calendar_csv_en(path, mitarbeiter, kalendertyp, config,
                          period_start=None, period_end=None):
    """Lädt einen Outlook-CSV-Kalenderexport mit ENGLISCHEN Spaltennamen
    (Subject, Start Date, Start Time, End Date, End Time, Location) - z.B. Export
    von Felix Seltmann."""
    df = pd.read_csv(path)
    df = df[['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Location']].copy()
    df = df.rename(columns={'Subject': 'Betreff', 'Location': 'Ort'})
    df['Start'] = pd.to_datetime(
        df['Start Date'].astype(str).str.strip() + ' ' + df['Start Time'].astype(str),
        format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df['Ende'] = pd.to_datetime(
        df['End Date'].astype(str).str.strip() + ' ' + df['End Time'].astype(str),
        format='%d.%m.%Y %H:%M:%S', errors='coerce')
    df = _enrich_calendar_df(df, mitarbeiter, kalendertyp, config)
    if period_start is not None:
        df = df[df['Start'] >= period_start]
    if period_end is not None:
        df = df[df['Start'] <= period_end]
    return df


def load_calendar_ical_xlsx(path, sheet, mitarbeiter, kalendertyp, config,
                             period_start=None, period_end=None):
    """Lädt einen iCal-Stil-Export als xlsx (Spalten Summary, Start Date, Start
    Time, End Date, End Time, Location, ...) - z.B. die 2024/2025-Spesenabrechnungs-
    Exporte. Start Date/End Date sind bereits echte Timestamps, Start/End Time
    separate Strings."""
    d = pd.read_excel(path, sheet_name=sheet)
    d = d.dropna(how='all')
    df = pd.DataFrame()
    df['Betreff'] = d['Summary']
    df['Ort'] = d.get('Location')

    def combine(date_col, time_col):
        dt = pd.to_datetime(d[date_col])
        t = pd.to_timedelta(d[time_col].astype(str), errors='coerce')
        return dt + t.fillna(pd.Timedelta(0))

    df['Start'] = combine('Start Date', 'Start Time')
    df['Ende'] = combine('End Date', 'End Time')
    df = _enrich_calendar_df(df, mitarbeiter, kalendertyp, config)
    if period_start is not None:
        df = df[df['Start'] >= period_start]
    if period_end is not None:
        df = df[df['Start'] <= period_end]
    return df


def build_outlook_nachtrag_rows(mitarbeiter, kalendertyp, config):
    """Die 9 Termine, die nur im alten 'Outlook_Kalender'-Export (2024/2025)
    stehen und nicht im 'Kikripp_Kalender' (Dubletten-Bereinigung, siehe
    references/mehrjahres_erweiterungen.md). Datum für die beiden "Aufstieg"-
    Termine per Nutzerangabe auf 30.09.2024 korrigiert (Rohwert der Datei war
    nachweislich falsch, siehe Chatverlauf 2026-07-23)."""
    rows = [
        ('Teaser "Koko"', '2024-07-31 16:30', '2024-07-31 17:30'),
        ('Unterlagen "Koko"', '2024-10-28 16:30', '2024-10-28 18:30'),
        ('Nickles - Abstimmung "Koko"', '2024-11-11 10:30', '2024-11-11 11:30'),
        ('Unterlagen "Koko"', '2024-11-11 10:30', '2024-11-11 11:30'),
        ('Teaser und NDA - Target "Juli"', '2024-07-18 12:00', '2024-07-18 13:30'),
        ('Unterlagen Target "Aufstieg"', '2024-11-18 14:30', '2024-11-18 15:30'),
        ('Roman Mayer - Teaser "Aufstieg"', '2024-09-30 17:00', '2024-09-30 17:30'),
        ('Christoph Heuel - NDA "Aufstieg"', '2024-09-30 17:30', '2024-09-30 18:00'),
        ('Projekt "Cool"', '2025-07-25 16:00', '2025-07-25 18:00'),
    ]
    df = pd.DataFrame(rows, columns=['Betreff', 'Start', 'Ende'])
    df['Start'] = pd.to_datetime(df['Start'])
    df['Ende'] = pd.to_datetime(df['Ende'])
    df['Ort'] = None
    return _enrich_calendar_df(df, mitarbeiter, kalendertyp, config)


def load_multiple_calendars(calendar_specs, config, period_start=None, period_end=None):
    """calendar_specs: Liste von dicts {path, mitarbeiter, kalendertyp, format?}.
    format: 'de' (Standard, default), 'en' (englische Spalten), 'ical_xlsx'
    (zusätzlich 'sheet' angeben), 'outlook_nachtrag' (kein path nötig)."""
    frames = []
    for spec in calendar_specs:
        fmt = spec.get('format', 'de')
        if fmt == 'de':
            frames.append(load_calendar_csv(spec['path'], spec['mitarbeiter'], spec['kalendertyp'],
                                              config, period_start, period_end))
        elif fmt == 'en':
            frames.append(load_calendar_csv_en(spec['path'], spec['mitarbeiter'], spec['kalendertyp'],
                                                 config, period_start, period_end))
        elif fmt == 'ical_xlsx':
            frames.append(load_calendar_ical_xlsx(spec['path'], spec['sheet'], spec['mitarbeiter'],
                                                    spec['kalendertyp'], config, period_start, period_end))
        elif fmt == 'outlook_nachtrag':
            df = build_outlook_nachtrag_rows(spec['mitarbeiter'], spec['kalendertyp'], config)
            if period_start is not None:
                df = df[df['Start'] >= period_start]
            if period_end is not None:
                df = df[df['Start'] <= period_end]
            frames.append(df)
        else:
            raise ValueError(f'Unbekanntes Kalenderformat: {fmt}')
    return pd.concat(frames, ignore_index=True)


# ==========================================================================
# Wöchentliche Pauschale (z.B. 5h Vertriebszeit Marius, außer in Urlaubswochen)
# ==========================================================================
def generate_wochenpauschale_rows(calendar_df_all, config, period_start, period_end):
    """Erzeugt synthetische Kalenderzeilen für die automatische Wochenpauschale.

    Eine Zeile pro ISO-Kalenderwoche im Zeitraum, außer die Woche enthält
    (an irgendeinem Tag, in irgendeinem Kalender der Person) einen Termin mit
    dem Urlaubs-Stichwort — dann wird die GANZE Woche ausgesetzt (konservative
    Annahme, siehe Config-Hinweis) und stattdessen eine Hinweiszeile mit 0h
    erzeugt (damit die ausgesetzte Woche sichtbar bleibt).
    """
    cfg = config.get('wochenpauschale')
    if not cfg:
        return pd.DataFrame()

    mitarbeiter = cfg['mitarbeiter']
    stunden = cfg['stunden_pro_woche']

    urlaubswochen = set()
    urlaub_rows = calendar_df_all[
        (calendar_df_all['Mitarbeiter'] == mitarbeiter) & (calendar_df_all['Ist_Urlaub'])
    ]
    for _, r in urlaub_rows.iterrows():
        d = r['Start']
        end = r['Ende']
        cur = d
        while cur <= end:
            iso = cur.isocalendar()
            urlaubswochen.add((iso[0], iso[1]))
            cur += timedelta(days=1)

    rows = []
    period_start_ts = pd.Timestamp(period_start)
    period_end_ts = pd.Timestamp(period_end)
    # Nur Montage AB period_start (keine Woche vor dem Zeitraum anhängen -
    # sonst "leckt" eine Pauschale in den Vormonat/-jahr, siehe Selbstpruefung 2026-07-22)
    weeks = pd.date_range(period_start_ts, period_end_ts, freq='W-MON')
    for monday in weeks:
        if monday > period_end_ts:
            continue
        iso = monday.isocalendar()
        key = (iso[0], iso[1])
        if key in urlaubswochen:
            rows.append({
                'Mitarbeiter': mitarbeiter, 'Kalendertyp': 'Pauschale',
                'Betreff': f"{cfg['bezeichnung']} - AUSGESETZT (Urlaub in KW{iso[1]}/{iso[0]})",
                'Start': monday, 'Ende': monday, 'Ort': None,
                'Projekt': cfg['bezeichnung'], 'Aufgabe': 'Ausgesetzt wegen Urlaub',
                'Hauptaufgabe': cfg['kategorie'], 'Dauer_h': 0.0, 'Mehrtaegig': False,
                'Jahr': monday.year, 'Ist_Urlaub': False, 'Ist_Pauschale': True,
            })
        else:
            rows.append({
                'Mitarbeiter': mitarbeiter, 'Kalendertyp': 'Pauschale',
                'Betreff': cfg['bezeichnung'],
                'Start': monday, 'Ende': monday + timedelta(hours=stunden), 'Ort': None,
                'Projekt': cfg['bezeichnung'], 'Aufgabe': cfg['bezeichnung'],
                'Hauptaufgabe': cfg['kategorie'], 'Dauer_h': float(stunden), 'Mehrtaegig': False,
                'Jahr': monday.year, 'Ist_Urlaub': False, 'Ist_Pauschale': True,
            })
    return pd.DataFrame(rows)


# ==========================================================================
# Autolog-Fahrtenbuch laden
# ==========================================================================
def load_autolog_csv(path, kennzeichen, fahrer_name, period_start=None, period_end=None,
                      nur_geschaeftlich=True):
    """Lädt ein Autolog-Fahrtenbuch-CSV für EIN Kennzeichen.

    Unterstützt zwei bekannte Export-Varianten:
    - alt: Spalten 'Start'/'Ende' als kombiniertes Datum+Uhrzeit ('dd.mm.yy HH:MM'), Spalte 'Fahrer'.
    - neu (ab 2025): getrennte Spalten 'Start'/'Startuhrzeit' bzw. 'Ende'/'Enduhrzeit', KEINE
      'Fahrer'-Spalte.

    Kennzeichen-Schreibweise wird normalisiert (Leerzeichen entfernt), da Autolog dasselbe
    Fahrzeug uneinheitlich exportiert (z.B. 'VS MN 1000' und 'VSMN1000' im selben Export).

    WICHTIG: 'Fahrer'-Wert im (alten) Export ist nicht vertrauenswürdig — fahrer_name wird
    explizit übergeben und überschreibt/ersetzt die Spalte.
    """
    df = pd.read_csv(path, sep=';', encoding='utf-8-sig')
    kennzeichen_norm = re.sub(r'\s+', '', kennzeichen).upper()
    df = df[df['Kennzeichen'].astype(str).str.replace(r'\s+', '', regex=True).str.upper()
            == kennzeichen_norm].copy()
    if nur_geschaeftlich:
        df = df[df['Fahrtart'] == 'Geschäftlich'].copy()
    df['Fahrer'] = fahrer_name

    if 'Startuhrzeit' in df.columns:
        df['Start'] = pd.to_datetime(df['Start'].astype(str) + ' ' + df['Startuhrzeit'].astype(str),
                                       format='%d.%m.%y %H:%M', errors='coerce')
        df['Ende'] = pd.to_datetime(df['Ende'].astype(str) + ' ' + df['Enduhrzeit'].astype(str),
                                      format='%d.%m.%y %H:%M', errors='coerce')
    else:
        df['Start'] = pd.to_datetime(df['Start'], format='%d.%m.%y %H:%M', errors='coerce')
        df['Ende'] = pd.to_datetime(df['Ende'], format='%d.%m.%y %H:%M', errors='coerce')
    df['Distanz (km)'] = pd.to_numeric(df['Distanz (km)'], errors='coerce')
    df['Jahr'] = df['Start'].dt.year

    if period_start is not None:
        df = df[df['Start'] >= period_start]
    if period_end is not None:
        df = df[df['Start'] <= period_end]
    return df


# ==========================================================================
# Fahrten <-> Kalendertermine abgleichen
# ==========================================================================
def apply_partner_zuordnung(trips_df, config):
    """Wendet die Partner->Projekt/Unberücksichtigt-Zuordnung an:
    1. Fahrten mit Partner='Unberücksichtigt' werden KOMPLETT entfernt (weder
       zugeordnet noch in 'nicht zugeordnet' sichtbar).
    2. Für nach dem Kalender-Matching weiterhin unzugeordnete Fahrten: falls der
       Partner einem Projekt zugeordnet ist, wird dieses Projekt als Fallback
       übernommen (Herkunft wird in 'Zuordnungsart' vermerkt).
    Erwartet trips_df MIT bereits durchgeführtem Kalender-Matching (Spalte
    'Projekt', ggf. None). Gibt trips_df zurück (gefiltert + ergänzt)."""
    mapping = {k: v for k, v in config.get('partner_projekt_zuordnung', {}).items()
               if not k.startswith('_')}
    df = trips_df.copy()
    df['Zuordnungsart'] = df['Projekt'].apply(lambda p: 'Kalender-Matching' if pd.notna(p) else '')

    unberuecksichtigt_partner = {k for k, v in mapping.items() if v == 'Unberücksichtigt'}
    df = df[~df['Partner'].isin(unberuecksichtigt_partner)].copy()

    def fallback(row):
        if pd.notna(row['Projekt']):
            return row['Projekt'], row['Zuordnungsart']
        ziel = mapping.get(row['Partner'])
        if ziel and ziel != 'Unberücksichtigt':
            return ziel, 'Partner-Zuordnung (automatisch)'
        return row['Projekt'], row['Zuordnungsart']

    result = df.apply(fallback, axis=1, result_type='expand')
    df['Projekt'] = result[0]
    df['Zuordnungsart'] = result[1]
    return df


def match_trips_to_calendar(trips_df, calendar_df, mitarbeiter,
                             window_before=timedelta(hours=36),
                             window_after=timedelta(hours=4)):
    cal = calendar_df[
        (calendar_df['Mitarbeiter'] == mitarbeiter) & (calendar_df['Projekt'].notna()) &
        (~calendar_df['Ist_Pauschale'])
    ].copy()
    trips = trips_df.copy()
    trips['Projekt'] = None
    for ti, trip in trips.iterrows():
        candidates = cal[
            (trip['Start'] >= cal['Start'] - window_before) &
            (trip['Start'] <= cal['Ende'] + window_after)
        ]
        if len(candidates) == 0:
            continue
        candidates = candidates.copy()
        candidates['delta'] = (candidates['Start'] - trip['Start']).abs()
        best = candidates.sort_values('delta').iloc[0]
        trips.at[ti, 'Projekt'] = best['Projekt']
    return trips


# ==========================================================================
# Kosten je Kalenderzeile / Fahrt berechnen (rate-history-aware)
# ==========================================================================
def _projekt_firma(projekt, config):
    stamm = config.get('projekt_stammliste', {})
    if projekt in stamm:
        return stamm[projekt].get('firma', 'TBD')
    wp = config.get('wochenpauschale', {})
    if projekt == wp.get('bezeichnung'):
        return wp.get('firma', 'TBD') + ' (intern, nicht projektbezogen)'
    ignore_names = set(config.get('projektname_erkennung', {}).get('ignorieren', []))
    if projekt in ignore_names:
        return 'Ignoriert / kein Projekt'
    return 'TBD'


def compute_kalender_kosten(calendar_df, config):
    """Fügt Stundensatz_EUR und Kosten_Zeit_EUR pro Zeile hinzu (rate zum Datum
    der Zeile). Mehrtägige Blocker (>20h) und Sonderkalkulations-Projekte werden
    mit Kosten_Zeit_EUR=0 markiert (dort gilt die jeweilige Sonderkalkulation
    bzw. es wird explizit nachgefragt statt automatisch verrechnet) - AUSSER bei
    Projekten mit 'ganztagespauschale' in der Config (z.B. Frutania): dort wird
    die Dauer eines mehrtägigen Blocks auf (Tage × Std./Tag) angepasst und ganz
    normal verrechnet, statt auf 0 gesetzt zu werden."""
    df = calendar_df.copy()
    sonderkalk_projekte = set(
        p for p, c in config.get('sonderkalkulationen', {}).items()
        if not p.startswith('_') and isinstance(c, dict)
    )
    ganztag_cfg = {p: c for p, c in config.get('ganztagespauschale', {}).items()
                   if not p.startswith('_') and isinstance(c, dict)}
    mitarbeiter_bekannt = set(k for k in config['mitarbeiter_satzhistorie'].keys() if not k.startswith('_'))

    def row_rate(r):
        if r['Mitarbeiter'] not in mitarbeiter_bekannt:
            return None
        return get_rate_for_date(config, r['Mitarbeiter'], r['Start'])

    df['Stundensatz_EUR'] = df.apply(row_rate, axis=1)

    # Ganztagespauschale: Dauer fuer betroffene mehrtaegige Bloecke anpassen
    df['Ist_Ganztagespauschale'] = False

    def adjust_dauer(r):
        if r['Mehrtaegig'] and r['Projekt'] in ganztag_cfg:
            if r['Start'].time().hour == 0 and r['Start'].time().minute == 0 and \
               r['Ende'].time().hour == 0 and r['Ende'].time().minute == 0:
                # Klassische "ganztägig"-Konvention: Ende-Datum ist exklusiv
                tage = max((r['Ende'].date() - r['Start'].date()).days, 1)
            else:
                # z.B. "08:00 Tag 1 bis 16:00 Tag 2" -> beide Kalendertage zaehlen
                tage = (r['Ende'].date() - r['Start'].date()).days + 1
            return tage * ganztag_cfg[r['Projekt']]['stunden_pro_tag']
        return r['Dauer_h']

    df['Dauer_h_roh'] = df['Dauer_h']
    df['Dauer_h'] = df.apply(adjust_dauer, axis=1)
    df.loc[df['Mehrtaegig'] & df['Projekt'].isin(ganztag_cfg.keys()), 'Ist_Ganztagespauschale'] = True

    def row_kosten(r):
        if pd.isna(r['Projekt']) or r['Projekt'] is None:
            return 0.0
        if r['Projekt'] in sonderkalk_projekte:
            return 0.0
        if r['Mehrtaegig'] and not r['Ist_Pauschale'] and not r['Ist_Ganztagespauschale']:
            return 0.0
        if r['Stundensatz_EUR'] is None:
            return 0.0
        return round(r['Dauer_h'] * r['Stundensatz_EUR'], 2)

    df['Kosten_Zeit_EUR'] = df.apply(row_kosten, axis=1)
    df['Firma'] = df['Projekt'].apply(lambda p: _projekt_firma(p, config) if pd.notna(p) else '')
    return df


def prepare_manuelle_zeitbuchungen(df, config):
    """Ergänzt Datum-geparste Zeitbuchungen (Datum,Mitarbeiter,Projekt,Hauptaufgabe,
    Stunden,Anmerkung) um Jahr, Stundensatz_EUR (zum jeweiligen Datum) und
    Kosten_Zeit_EUR. Für manuell nacherfasste Termine, die (noch) nicht im
    Kalenderexport stehen."""
    if df is None or len(df) == 0:
        return pd.DataFrame(columns=['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe',
                                       'Stunden', 'Anmerkung', 'Jahr', 'Stundensatz_EUR',
                                       'Kosten_Zeit_EUR'])
    out = df.copy()
    out['Datum'] = pd.to_datetime(out['Datum'])
    out['Jahr'] = out['Datum'].dt.year
    out['Stundensatz_EUR'] = out.apply(
        lambda r: get_rate_for_date(config, r['Mitarbeiter'], r['Datum']), axis=1)
    out['Kosten_Zeit_EUR'] = (out['Stunden'].astype(float) * out['Stundensatz_EUR']).round(2)
    return out


def compute_fahrten_kosten(trips_df, config):
    """Fügt KmSatz_EUR und Kosten_Fahrt_EUR hinzu. Fahrten zu Sonderkalkulations-
    Projekten mit fahrten_kostentechnisch_ausschliessen=True bekommen Kosten=0
    (km/Dauer bleiben trotzdem in den Daten, für die informative Anzeige)."""
    df = trips_df.copy()
    sonderkalk = config.get('sonderkalkulationen', {})

    def row_kmrate(r):
        return get_kmrate_for_date(config, r['Start'])

    df['KmSatz_EUR'] = df.apply(row_kmrate, axis=1)

    def row_kosten(r):
        if pd.isna(r['Projekt']) or r['Projekt'] is None:
            return 0.0
        cfg = sonderkalk.get(r['Projekt'])
        if isinstance(cfg, dict) and cfg.get('fahrten_kostentechnisch_ausschliessen'):
            return 0.0
        km = r['Distanz (km)'] if pd.notna(r['Distanz (km)']) else 0.0
        return round(km * r['KmSatz_EUR'], 2)

    df['Kosten_Fahrt_EUR'] = df.apply(row_kosten, axis=1)
    return df


# ==========================================================================
# Sonderkalkulation: Tagessatz-Block + wöchentliche Anfahrtspauschale
# ==========================================================================
def calc_tagessatz_block_kosten(calendar_df, projekt, sonderkalk_config):
    """Berechnet Blockkosten (Tagessätze, Übernachtung) je Buchungszeitraum
    UND die Anfahrtspauschale separat pro betroffener Kalenderwoche (Stand
    2026-07-22: Pauschale ist wochenbasiert, nicht mehr blockbasiert).

    Rückgabe: dict mit 'bloecke' (DataFrame je Block) und 'pauschalen'
    (DataFrame je betroffener Kalenderwoche).
    """
    cfg = sonderkalk_config[projekt]
    blocks = calendar_df[calendar_df['Projekt'] == projekt].sort_values('Start').copy()

    block_rows = []
    wochen = set()
    for _, r in blocks.iterrows():
        tage = round((r['Ende'] - r['Start']).total_seconds() / 86400.0)
        naechte = tage
        tagessaetze = tage * cfg['tagessatz_vor_ort_eur']
        uebernachtung = naechte * cfg['uebernachtung_pro_nacht_eur']
        block_rows.append({
            'Start': r['Start'], 'Ende': r['Ende'], 'Tage': tage, 'Naechte': naechte,
            'Tagessaetze_EUR': tagessaetze, 'Uebernachtung_EUR': uebernachtung,
            'Kosten_Block_EUR': tagessaetze + uebernachtung,
        })
        cur = r['Start']
        while cur <= r['Ende']:
            iso = cur.isocalendar()
            wochen.add((iso[0], iso[1], cur - timedelta(days=cur.weekday())))
            cur += timedelta(days=1)

    pauschale_rows = []
    for jahr, kw, montag in sorted(wochen, key=lambda x: x[2]):
        pauschale_rows.append({
            'Jahr': jahr, 'KW': kw, 'Woche_ab': montag,
            'Anfahrtspauschale_EUR': cfg['anfahrtspauschale_eur'],
        })

    return {
        'bloecke': pd.DataFrame(block_rows),
        'pauschalen': pd.DataFrame(pauschale_rows),
    }


# ==========================================================================
# Plausibilitätscheck
# ==========================================================================
def plausibility_check(calendar_df_with_kosten, config):
    """Listet Mitarbeiter/ISO-Woche-Kombinationen, deren Gesamtstunden (inkl.
    Wochenpauschale) den konfigurierten Schwellwert überschreiten. Mehrtägige
    Blocker (z.B. Tagessatz-Sonderkalkulationen wie Niedermaier) werden
    ausgeschlossen, da deren Dauer bewusst NICHT als normale Arbeitsstunden
    gilt (sonst dauerhafte Falschmeldungen für bekannte Blocker)."""
    threshold = config.get('plausibilitaets_check', {}).get('max_stunden_pro_person_pro_woche', 60)
    df = calendar_df_with_kosten.copy()
    df = df[df['Projekt'].notna() & (~df['Mehrtaegig'] | df['Ist_Pauschale'])]
    df['ISO_Jahr'] = df['Start'].apply(lambda d: d.isocalendar()[0])
    df['ISO_KW'] = df['Start'].apply(lambda d: d.isocalendar()[1])
    grouped = df.groupby(['Mitarbeiter', 'ISO_Jahr', 'ISO_KW'])['Dauer_h'].sum().reset_index()
    flagged = grouped[grouped['Dauer_h'] > threshold].sort_values('Dauer_h', ascending=False)
    return flagged, threshold


# ==========================================================================
# Zusatzkosten aus einer frueheren Version der Ausgabedatei übernehmen
# ==========================================================================
def load_zusatzkosten_from_workbook(path, sheet_name='Zusatzkosten', start_row=6):
    """Liest bereits erfasste Zusatzkosten aus einer frueher generierten
    Ausgabedatei, damit sie beim Neu-Aufbau nicht verloren gehen."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True)
        if sheet_name not in wb.sheetnames:
            return pd.DataFrame(columns=['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR', 'Anmerkung'])
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(min_row=start_row, values_only=True):
            if not row or row[0] is None:
                continue
            rows.append({'Datum': row[0], 'Projekt': row[1], 'Kostenart': row[2],
                         'Betrag_EUR': row[3], 'Anmerkung': row[4] if len(row) > 4 else ''})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR', 'Anmerkung'])


def load_manuelle_zeitbuchungen_from_workbook(path, sheet_name='Manuelle_Zeitbuchungen', start_row=6):
    """Liest bereits erfasste manuelle Zeitbuchungen aus einer frueher generierten
    Ausgabedatei, damit sie beim Neu-Aufbau nicht verloren gehen."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True)
        if sheet_name not in wb.sheetnames:
            return pd.DataFrame(columns=['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe', 'Stunden', 'Anmerkung'])
        ws = wb[sheet_name]
        rows = []
        for row in ws.iter_rows(min_row=start_row, values_only=True):
            if not row or row[0] is None:
                continue
            rows.append({'Datum': row[0], 'Mitarbeiter': row[1], 'Projekt': row[2],
                         'Hauptaufgabe': row[3], 'Stunden': row[4],
                         'Anmerkung': row[5] if len(row) > 5 else ''})
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame(columns=['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe', 'Stunden', 'Anmerkung'])


def load_partner_zuordnung_from_workbook(path, sheet_name='Partner_Projekt_Zuordnung', start_row=5):
    """Liest bereits erfasste Partner->Projekt-Zuordnungen aus einer frueher
    generierten Ausgabedatei, damit sie beim Neu-Aufbau nicht verloren gehen."""
    try:
        from openpyxl import load_workbook
        wb = load_workbook(path, data_only=True)
        if sheet_name not in wb.sheetnames:
            return {}
        ws = wb[sheet_name]
        result = {}
        for row in ws.iter_rows(min_row=start_row, values_only=True):
            if not row or row[0] is None:
                continue
            if len(row) > 1 and row[1]:
                result[row[0]] = row[1]
        return result
    except Exception:
        return {}


# ==========================================================================
# Excel-Report bauen (Version 3: Dashboard mit SUMIFS, Hauptaufgabe/Monat,
# Partner-Zuordnung, Management-Summary, Monatstrend, Auslastung)
# ==========================================================================
def build_excel_workbook(calendar_df, trips_df, config, period_label, output_path,
                          zusatzkosten_vorbelegt=None, manuelle_zeitbuchungen_vorbelegt=None,
                          partner_zuordnung_vorbelegt=None):
    """Baut die komplette Mehrjahres-Ausgabe-Excel (Version 3).

    calendar_df: durch compute_kalender_kosten() gelaufen (inkl. Wochenpauschale-Zeilen).
    trips_df: durch match_trips_to_calendar() -> apply_partner_zuordnung() ->
              compute_fahrten_kosten() gelaufen (ALLE Fahrten, inkl. weiterhin
              unzugeordneter - der Split in zugeordnet/nicht zugeordnet passiert
              hier intern anhand der Spalte 'Projekt').
    partner_zuordnung_vorbelegt: dict Partner -> Projekt/'Unberücksichtigt', wird
              mit config['partner_projekt_zuordnung'] zusammengeführt (Vorversion
              hat Vorrang, falls vorhanden).
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference

    FONT = 'Arial'
    hdr_fill = PatternFill('solid', fgColor='1F3864')
    hdr_font = Font(name=FONT, bold=True, color='FFFFFF', size=10)
    title_font = Font(name=FONT, bold=True, size=14, color='1F3864')
    sub_font = Font(name=FONT, italic=True, size=9, color='808080')
    blue_input = Font(name=FONT, color='0000FF', size=10)
    normal = Font(name=FONT, size=10)
    bold = Font(name=FONT, bold=True, size=10)
    warn_fill = PatternFill('solid', fgColor='FFE699')
    flag_fill = PatternFill('solid', fgColor='FFC7CE')
    kpi_fill = PatternFill('solid', fgColor='EBF0FA')
    blue_fill = PatternFill('solid', fgColor='DCE6F7')
    green_fill = PatternFill('solid', fgColor='E2F0D9')
    thin = Side(style='thin', color='BFBFBF')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    def style_header_row(ws, row, ncols):
        for c in range(1, ncols + 1):
            cell = ws.cell(row=row, column=c)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border

    def autosize(ws, widths):
        for i, w in enumerate(widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

    wb = Workbook()
    mwst_satz = config.get('mwst_satz_prozent', 19) / 100.0
    mitarbeiter_liste = [k for k in config['mitarbeiter_satzhistorie'].keys() if not k.startswith('_')]
    hauptaufgaben_liste = [k for k in config.get('hauptaufgaben_kategorien', {}).keys()
                            if not k.startswith('_') and k != 'fallback_je_mitarbeiter']

    # ---------------- Parameter ----------------
    ws = wb.active
    ws.title = 'Parameter'
    ws['A1'] = 'Parameter, Sätze & Historie'
    ws['A1'].font = title_font
    ws['A2'] = (f'Zeitraum: {period_label} · Preise netto, MwSt. {config.get("mwst_satz_prozent",19)}% '
                f'wird separat ausgewiesen. Blau hinterlegt = hier anpassbar.')
    ws['A2'].font = sub_font
    ws.append([])
    ws.append(['Mitarbeiter', 'Kürzel', 'Gültig ab', 'Stundensatz (€, netto)', 'Soll-Std./Woche'])
    style_header_row(ws, 4, 5)
    r = 5
    soll = config.get('soll_arbeitszeit_pro_woche', {})
    for ma in mitarbeiter_liste:
        info = config['mitarbeiter_satzhistorie'][ma]
        for satz in info['saetze']:
            ws.append([ma, info['kuerzel'], satz['gueltig_ab'], satz['stundensatz_eur'], soll.get(ma, '')])
            for c in range(1, 6):
                ws.cell(row=r, column=c).font = normal
                ws.cell(row=r, column=c).border = border
            ws.cell(row=r, column=4).fill = blue_fill
            ws.cell(row=r, column=5).fill = blue_fill
            r += 1
    r += 1
    ws.cell(row=r, column=1, value='Kilometersatz-Historie (inkl. Arbeitszeit/Fahrzeit)').font = bold
    r += 1
    ws.append(['Gültig ab', 'Satz (€/km, netto)'])
    hdr_km_row = r + 1
    style_header_row(ws, hdr_km_row, 2)
    r = hdr_km_row + 1
    for satz in config['km_satz_historie']:
        ws.cell(row=r, column=1, value=satz['gueltig_ab']).font = normal
        c2 = ws.cell(row=r, column=2, value=satz['satz_eur_pro_km'])
        c2.font = normal; c2.fill = blue_fill
        r += 1
    r += 1
    ws.cell(row=r, column=1, value='MwSt.-Satz (%)').font = normal
    mwst_cell = ws.cell(row=r, column=2, value=config.get('mwst_satz_prozent', 19))
    mwst_cell.font = normal; mwst_cell.fill = blue_fill
    mwst_param_row = r
    r += 2
    ws.cell(row=r, column=1, value='Spedition Niedermaier – Sonderkonditionen (informativ)').font = bold
    r += 1
    nb_cfg = config.get('sonderkalkulationen', {}).get('Spedition Niedermaier', {})
    if nb_cfg:
        for label, key in [('Tagessatz Vor-Ort (€/Tag)', 'tagessatz_vor_ort_eur'),
                            ('Anfahrtspauschale (€/Woche)', 'anfahrtspauschale_eur'),
                            ('Übernachtungspauschale (€/Nacht)', 'uebernachtung_pro_nacht_eur')]:
            ws.cell(row=r, column=1, value=label).font = normal
            c2 = ws.cell(row=r, column=2, value=nb_cfg.get(key))
            c2.font = normal; c2.fill = blue_fill
            r += 1
    autosize(ws, [30, 10, 14, 18, 14])

    # ---------------- Projekt-Stammliste (in Parameter integriert, live editierbar) ----------------
    stamm = config.get('projekt_stammliste', {})
    stamm = {k: v for k, v in stamm.items() if not k.startswith('_') and isinstance(v, dict)}
    wp_cfg = config.get('wochenpauschale', {})
    ws.cell(row=3, column=4,
            value='Blau hinterlegt = hier kannst du Werte anpassen. Grün hinterlegt = hier neue Projekte eintragen.').font = sub_font
    ws.cell(row=4, column=4, value='Projekt-Stammliste (hier editieren, wirkt überall live)').font = bold
    ws.cell(row=5, column=4, value='Projekt')
    ws.cell(row=5, column=5, value='Firma')
    ws.cell(row=5, column=6, value='Status')
    style_header_row(ws, 5, 0)
    for c in (4, 5, 6):
        cell = ws.cell(row=5, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
    stamm_start = 6

    # Fixzeilen: "Unberücksichtigt" (fuer Dropdowns) und die Wochenpauschale
    ws.cell(row=stamm_start, column=4, value='Unberücksichtigt').font = normal
    ws.cell(row=stamm_start, column=5, value='-').font = normal
    ws.cell(row=stamm_start, column=6, value='-').font = normal
    wp_bez_name = wp_cfg.get('bezeichnung')
    ws.cell(row=stamm_start + 1, column=4, value=wp_bez_name).font = normal
    ws.cell(row=stamm_start + 1, column=5, value=wp_cfg.get('firma', 'TBD') + ' (intern, nicht projektbezogen)').font = normal
    ws.cell(row=stamm_start + 1, column=6, value='laufend').font = normal
    for row in (stamm_start, stamm_start + 1):
        for c in (4, 5, 6):
            ws.cell(row=row, column=c).border = border
    echte_projekte_start = stamm_start + 2

    ignore_names_set = set(config.get('projektname_erkennung', {}).get('ignorieren', []))
    alle_projekte_fuer_stamm = sorted(set(stamm.keys()) |
                                        set(calendar_df[calendar_df['Projekt'].notna()]['Projekt'].unique()) -
                                        ignore_names_set -
                                        {wp_bez_name})
    for i, proj in enumerate(alle_projekte_fuer_stamm):
        row = echte_projekte_start + i
        meta = stamm.get(proj, {})
        ws.cell(row=row, column=4, value=proj).font = normal
        ws.cell(row=row, column=4).fill = green_fill
        f_cell = ws.cell(row=row, column=5, value=meta.get('firma', 'TBD'))
        f_cell.font = normal; f_cell.fill = blue_fill
        s_cell = ws.cell(row=row, column=6, value=meta.get('status', 'TBD'))
        s_cell.font = normal; s_cell.fill = blue_fill
        for c in (4, 5, 6):
            ws.cell(row=row, column=c).border = border
    stamm_last = echte_projekte_start + max(len(alle_projekte_fuer_stamm) - 1, 0)

    # Grüne Vorrats-Zeilen zum Ergänzen neuer Projekte
    NEUE_PROJEKTE_PUFFER = 20
    neue_start = stamm_last + 1
    for i in range(NEUE_PROJEKTE_PUFFER):
        row = neue_start + i
        p_cell = ws.cell(row=row, column=4, value=None)
        p_cell.fill = green_fill; p_cell.border = border
        f_cell = ws.cell(row=row, column=5, value=None)
        f_cell.fill = blue_fill; f_cell.border = border
        s_cell = ws.cell(row=row, column=6, value=None)
        s_cell.fill = blue_fill; s_cell.border = border
    stamm_last_mit_puffer = neue_start + NEUE_PROJEKTE_PUFFER - 1

    ignorierte_in_daten = sorted(set(calendar_df[calendar_df['Projekt'].notna()]['Projekt'].unique()) &
                                   ignore_names_set)
    for i, proj in enumerate(ignorierte_in_daten):
        row = stamm_last_mit_puffer + 1 + i
        ws.cell(row=row, column=4, value=proj).font = normal
        ws.cell(row=row, column=5, value='Ignoriert / kein Projekt').font = normal
        ws.cell(row=row, column=6, value='-').font = normal
        for c in (4, 5, 6):
            ws.cell(row=row, column=c).border = border
    stamm_last_mit_ignoriert = stamm_last_mit_puffer + len(ignorierte_in_daten)

    dv_firma = DataValidation(type="list", formula1='"Neininger GmbH,TransCare"', allow_blank=True)
    dv_status = DataValidation(type="list", formula1='"aktiv,beendet"', allow_blank=True)
    ws.add_data_validation(dv_firma); ws.add_data_validation(dv_status)
    dv_firma.add(f'E{echte_projekte_start}:E{stamm_last_mit_puffer}')
    dv_status.add(f'F{echte_projekte_start}:F{stamm_last_mit_puffer}')
    ws.auto_filter.ref = f"D5:F{stamm_last_mit_ignoriert}"
    ws.column_dimensions['D'].width = 30
    ws.column_dimensions['E'].width = 16
    ws.column_dimensions['F'].width = 12

    # ---------------- Partner-Zuordnung (in Parameter integriert, live editierbar) ----------------
    ws.cell(row=4, column=8, value='Partner → Projekt-Zuordnung (Autolog)').font = bold
    ws.cell(row=5, column=8, value='Partner (Autolog)')
    ws.cell(row=5, column=9, value='Zuordnung')
    for c in (8, 9):
        cell = ws.cell(row=5, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
    pz_start = 6
    merged_zuordnung = dict(config.get('partner_projekt_zuordnung', {}))
    merged_zuordnung = {k: v for k, v in merged_zuordnung.items() if not k.startswith('_')}
    if partner_zuordnung_vorbelegt:
        merged_zuordnung.update(partner_zuordnung_vorbelegt)
    alle_partner = sorted(set(trips_df['Partner'].dropna().unique()) | set(merged_zuordnung.keys()))
    pz_last = pz_start + max(len(alle_partner) - 1, 0)
    for i, partner in enumerate(alle_partner):
        row = pz_start + i
        ws.cell(row=row, column=8, value=partner).font = normal
        z_cell = ws.cell(row=row, column=9, value=merged_zuordnung.get(partner, ''))
        z_cell.font = normal; z_cell.fill = blue_fill
        for c in (8, 9):
            ws.cell(row=row, column=c).border = border
    pz_last_padded = max(pz_last, pz_start + 50)
    for row in range(pz_last + 1, pz_last_padded + 1):
        ws.cell(row=row, column=9).fill = blue_fill
        ws.cell(row=row, column=9).border = border
        ws.cell(row=row, column=8).border = border
    dv_partner = DataValidation(
        type="list", formula1=f'=Parameter!$D${stamm_start}:$D${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_partner)
    dv_partner.add(f'I{pz_start}:I{pz_last_padded}')
    ws.column_dimensions['H'].width = 26
    ws.column_dimensions['I'].width = 30
    ws.cell(row=pz_last_padded + 2, column=8,
            value=('Hinweis: Änderungen hier wirken sich SOFORT auf "Rohdaten_Fahrten" (Spalte Projekt/'
                   'Firma) und damit auch auf Übersicht/Dashboard aus - kein erneuter Bericht-Lauf nötig.')
            ).font = sub_font

    # Referenz-Strings für spaetere Formeln merken
    stamm_range = f"Parameter!$D${stamm_start}:$F${stamm_last_mit_ignoriert}"
    partner_range = f"Parameter!$H${pz_start}:$I${pz_last_padded}"

    # ---------------- Rohdaten_Kalender ----------------
    ws = wb.create_sheet('Rohdaten_Kalender')
    ws.freeze_panes = 'A2'
    cols = ['Jahr', 'Monat', 'Mitarbeiter', 'Kalendertyp', 'Projekt', 'Firma', 'Hauptaufgabe',
            'Datum', 'Start', 'Ende', 'Dauer_h', 'Stundensatz_EUR', 'Kosten_Zeit_EUR', 'Aufgabe',
            'Mehrtaegig_Blocker', 'Ist_Pauschale', 'Manuelle Projekt-Korrektur',
            'Projekt (automatisch erkannt, intern)']
    ws.append(cols)
    style_header_row(ws, 1, len(cols))
    cal_all_rows = calendar_df.copy()
    cal_all_rows['Monat'] = cal_all_rows['Start'].dt.strftime('%Y-%m')
    wp_bez = wp_cfg.get('bezeichnung')
    for i, (_, r_) in enumerate(cal_all_rows.sort_values(['Jahr', 'Start']).iterrows()):
        row = i + 2
        auto_projekt = r_['Projekt'] if pd.notna(r_['Projekt']) else ''
        ws.append([r_['Jahr'], r_['Monat'], r_['Mitarbeiter'], r_['Kalendertyp'], None, None,
                    r_['Hauptaufgabe'], r_['Start'].strftime('%d.%m.%Y'), r_['Start'].strftime('%d.%m.%Y %H:%M'),
                    r_['Ende'].strftime('%d.%m.%Y %H:%M'), round(r_['Dauer_h'], 2), r_['Stundensatz_EUR'],
                    r_['Kosten_Zeit_EUR'], r_['Aufgabe'],
                    'JA - Klärung nötig' if (r_['Mehrtaegig'] and not r_['Ist_Pauschale']
                                              and not r_.get('Ist_Ganztagespauschale', False)) else '',
                    'JA' if r_['Ist_Pauschale'] else '', None, auto_projekt])
        ws.cell(row=row, column=5,
                value=(f'=IF(Q{row}<>"",IF(Q{row}="Unberücksichtigt","",Q{row}),IF(R{row}="","",R{row}))'))
        if r_['Projekt'] == wp_bez:
            ws.cell(row=row, column=6,
                    value=f'=IF(E{row}="","",IFERROR(VLOOKUP(E{row},{stamm_range},2,FALSE),"TBD"))')
        else:
            ws.cell(row=row, column=6,
                    value=f'=IF(E{row}="","",IFERROR(VLOOKUP(E{row},{stamm_range},2,FALSE),"TBD"))')
        ws.cell(row=row, column=17).fill = blue_fill
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = normal
            cell.border = border
        if row[14].value:
            for cell in row:
                cell.fill = warn_fill
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    autosize(ws, [8, 10, 20, 12, 24, 22, 32, 12, 16, 16, 9, 12, 12, 40, 18, 12, 26, 24])
    ws.freeze_panes = 'A2'
    dv_korrektur_kalender = DataValidation(
        type="list", formula1=f'=Parameter!$D${stamm_start}:$D${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_korrektur_kalender)
    dv_korrektur_kalender.add(f'Q2:Q{ws.max_row}')
    n_cal_rows = ws.max_row

    # ---------------- Rohdaten_Fahrten ----------------
    ws = wb.create_sheet('Rohdaten_Fahrten')
    cols = ['Jahr', 'Monat', 'Mitarbeiter', 'Projekt', 'Firma', 'Herkunft', 'Datum', 'Start', 'Ende',
            'Distanz_km', 'Dauer_h', 'KmSatz_EUR', 'Kosten_Fahrt_EUR', 'Start-Adresse', 'End-Adresse',
            'Partner (Autolog)', 'Zweck', 'Projekt (Kalender-Match, intern)', 'Manuelle Projekt-Korrektur']
    ws.append(cols)
    style_header_row(ws, 1, len(cols))
    tdf = trips_df.copy()
    tdf['Monat'] = tdf['Start'].dt.strftime('%Y-%m')
    for i, (_, r_) in enumerate(tdf.sort_values(['Jahr', 'Start']).iterrows()):
        row = i + 2
        dauer_h = round((r_['Ende'] - r_['Start']).total_seconds() / 3600.0, 2)
        kal_match = r_['Projekt'] if pd.notna(r_['Projekt']) else ''
        ws.append([r_['Jahr'], r_['Monat'], r_['Fahrer'], None, None, None,
                    r_['Start'].strftime('%d.%m.%Y'), r_['Start'].strftime('%d.%m.%Y %H:%M'),
                    r_['Ende'].strftime('%d.%m.%Y %H:%M'), r_['Distanz (km)'], dauer_h, r_['KmSatz_EUR'],
                    None, r_['Start-Adresse'], r_['End-Adresse'], r_['Partner'], r_['Zweck'], kal_match, None])
        r_gueltig = f'AND(R{row}<>"",IFERROR(VLOOKUP(R{row},{stamm_range},2,FALSE),"")<>"Ignoriert / kein Projekt")'
        auto_projekt = (f'IF({r_gueltig},R{row},IFERROR(IF(OR(VLOOKUP(P{row},{partner_range},2,FALSE)='
                         f'"Unberücksichtigt",VLOOKUP(P{row},{partner_range},2,FALSE)=0),"",'
                         f'VLOOKUP(P{row},{partner_range},2,FALSE)),""))')
        ws.cell(row=row, column=4,
                value=f'=IF(S{row}<>"",IF(S{row}="Unberücksichtigt","",S{row}),{auto_projekt})')
        ws.cell(row=row, column=5,
                value=f'=IF(D{row}="","",IFERROR(VLOOKUP(D{row},{stamm_range},2,FALSE),"TBD"))')
        ws.cell(row=row, column=6,
                value=(f'=IF(S{row}<>"","Manuelle Korrektur",IF({r_gueltig},"Kalender-Match",'
                       f'IF(R{row}<>"","Kalender-Match (ignoriertes Projekt, siehe Spalte R)",'
                       f'IFERROR(IF(VLOOKUP(P{row},{partner_range},2,FALSE)="Unberücksichtigt",'
                       f'"Unberücksichtigt (ausgeblendet)",IF(VLOOKUP(P{row},{partner_range},2,FALSE)=0,'
                       f'"Nicht zugeordnet","Partner-Zuordnung")),"Nicht zugeordnet"))))'))
        ws.cell(row=row, column=13,
                value=f'=IF(D{row}="","",IF(D{row}="Spedition Niedermaier",0,J{row}*L{row}))')
        ws.cell(row=row, column=19).fill = blue_fill
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = normal
            cell.border = border
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    dv_korrektur_fahrten = DataValidation(
        type="list", formula1=f'=Parameter!$D${stamm_start}:$D${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_korrektur_fahrten)
    dv_korrektur_fahrten.add(f'S2:S{ws.max_row}')
    autosize(ws, [8, 10, 20, 24, 30, 30, 12, 16, 16, 11, 10, 11, 14, 45, 45, 18, 20, 22, 26])
    n_trip_rows = ws.max_row

    # ---------------- Zusatzkosten ----------------
    ws = wb.create_sheet('Zusatzkosten')
    ws['A1'] = 'Zusatzkosten (manuell erfassen)'
    ws['A1'].font = title_font
    ws['A2'] = 'Datum eintragen, Projektname EXAKT wie im Kalender, Betrag netto in €. Jahr/Monat automatisch.'
    ws['A2'].font = sub_font
    cols = ['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR (netto)', 'Anmerkung', 'Jahr (auto)', 'Monat (auto)']
    ws.append([])
    ws.append(cols)
    zk_hdr_row = 4
    style_header_row(ws, zk_hdr_row, len(cols))
    zk_start_row = zk_hdr_row + 1
    zk_last_row = zk_start_row + 300
    vor = zusatzkosten_vorbelegt if zusatzkosten_vorbelegt is not None else pd.DataFrame()
    r = zk_start_row
    for _, row_ in vor.iterrows():
        if pd.isna(row_.get('Datum')):
            continue
        ws.cell(row=r, column=1, value=row_.get('Datum'))
        ws.cell(row=r, column=2, value=row_.get('Projekt'))
        ws.cell(row=r, column=3, value=row_.get('Kostenart'))
        ws.cell(row=r, column=4, value=row_.get('Betrag_EUR'))
        ws.cell(row=r, column=5, value=row_.get('Anmerkung'))
        r += 1
    for rr in range(zk_start_row, zk_last_row + 1):
        ws.cell(row=rr, column=6, value=f'=IF(A{rr}="","",YEAR(A{rr}))')
        ws.cell(row=rr, column=7, value=f'=IF(A{rr}="","",TEXT(A{rr},"YYYY-MM"))')
        for c in range(1, 8):
            ws.cell(row=rr, column=c).font = normal
            ws.cell(row=rr, column=c).border = border
        for c in (1, 2, 3, 4, 5):
            ws.cell(row=rr, column=c).fill = blue_fill
    dv_zk_projekt = DataValidation(
        type="list", formula1=f'=Parameter!$D${stamm_start}:$D${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_zk_projekt)
    dv_zk_projekt.add(f'B{zk_start_row}:B{zk_last_row}')
    ws.auto_filter.ref = f"A{zk_hdr_row}:G{zk_last_row}"
    autosize(ws, [14, 24, 22, 18, 40, 12, 12])

    # ---------------- Manuelle_Zeitbuchungen ----------------
    ws = wb.create_sheet('Manuelle_Zeitbuchungen')
    ws['A1'] = 'Manuelle Zeitbuchungen (Termine, die noch nicht im Kalender stehen)'
    ws['A1'].font = title_font
    ws['A2'] = ('Datum, Mitarbeiter, Projekt (exakt wie im Kalender), Hauptaufgabe-Kategorie, Stunden. '
                'Stundensatz/Kosten/Jahr/Monat werden automatisch berechnet.')
    ws['A2'].font = sub_font
    mz_cols = ['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe', 'Stunden', 'Anmerkung',
               'Jahr (auto)', 'Stundensatz_EUR', 'Kosten_Zeit_EUR (auto)', 'Monat (auto)']
    ws.append([])
    ws.append(mz_cols)
    mz_hdr_row = 4
    style_header_row(ws, mz_hdr_row, len(mz_cols))
    mz_start_row = mz_hdr_row + 1
    mz_last_row = mz_start_row + 300
    mz_vor = prepare_manuelle_zeitbuchungen(manuelle_zeitbuchungen_vorbelegt, config)
    r = mz_start_row
    for _, row_ in mz_vor.iterrows():
        c1 = ws.cell(row=r, column=1, value=row_['Datum'])
        c1.number_format = 'DD.MM.YYYY'
        ws.cell(row=r, column=2, value=row_['Mitarbeiter'])
        ws.cell(row=r, column=3, value=row_['Projekt'])
        ws.cell(row=r, column=4, value=row_['Hauptaufgabe'])
        ws.cell(row=r, column=5, value=row_['Stunden'])
        ws.cell(row=r, column=6, value=row_.get('Anmerkung', ''))
        ws.cell(row=r, column=8, value=row_['Stundensatz_EUR'])
        r += 1
    for rr in range(mz_start_row, mz_last_row + 1):
        ws.cell(row=rr, column=7, value=f'=IF(A{rr}="","",YEAR(A{rr}))')
        ws.cell(row=rr, column=9, value=f'=IF(A{rr}="","",E{rr}*H{rr})')
        ws.cell(row=rr, column=10, value=f'=IF(A{rr}="","",TEXT(A{rr},"YYYY-MM"))')
        for c in range(1, 11):
            ws.cell(row=rr, column=c).font = normal
            ws.cell(row=rr, column=c).border = border
        for c in (1, 2, 3, 4, 5, 6, 8):
            ws.cell(row=rr, column=c).fill = blue_fill
    dv_mz_projekt = DataValidation(
        type="list", formula1=f'=Parameter!$D${stamm_start}:$D${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_mz_projekt)
    dv_mz_projekt.add(f'C{mz_start_row}:C{mz_last_row}')
    dv_mz_ha = DataValidation(
        type="list", formula1='"' + ','.join(hauptaufgaben_liste) + '"', allow_blank=True)
    ws.add_data_validation(dv_mz_ha)
    dv_mz_ha.add(f'D{mz_start_row}:D{mz_last_row}')
    dv_mz_ma = DataValidation(
        type="list", formula1='"' + ','.join(mitarbeiter_liste) + '"', allow_blank=True)
    ws.add_data_validation(dv_mz_ma)
    dv_mz_ma.add(f'B{mz_start_row}:B{mz_last_row}')
    ws.auto_filter.ref = f"A{mz_hdr_row}:J{mz_last_row}"
    autosize(ws, [14, 20, 22, 32, 10, 35, 12, 14, 18, 12])

    # ---------------- Sonderkalkulations-Sheets ----------------
    sonderkalk_refs = {}
    for projekt, cfg in config.get('sonderkalkulationen', {}).items():
        if projekt.startswith('_') or not isinstance(cfg, dict) or cfg.get('typ') != 'tagessatz_block':
            continue
        result = calc_tagessatz_block_kosten(calendar_df, projekt, config['sonderkalkulationen'])
        block_df, pausch_df = result['bloecke'], result['pauschalen']
        sheet_name = re.sub(r'[^A-Za-z0-9_]', '_', projekt)[:20] + '_Kalk'
        ws = wb.create_sheet(sheet_name)
        ws['A1'] = f'{projekt} – Sonderkalkulation'
        ws['A1'].font = title_font
        ws['A2'] = (f"Tagessätze/Übernachtung je Buchungszeitraum; Anfahrtspauschale pro Kalenderwoche. "
                    f"Hauptaufgabe für die interne Auswertung: {cfg.get('hauptaufgabe','-')} "
                    f"(Mitarbeiter: {cfg.get('mitarbeiter','-')}).")
        ws['A2'].font = sub_font

        ws.append([])
        ws.append(['Jahr', 'Monat', 'Start', 'Ende', 'Tage (Vor-Ort)', 'Nächte', 'Tagessätze (€)',
                    'Übernachtung (€)', 'Kosten Block (€)', 'Informative Std. (für interne Auswertung)'])
        b_hdr = 4
        style_header_row(ws, b_hdr, 10)
        b_start = b_hdr + 1
        enthaltene_std = cfg.get('tagessatz_enthaltene_stunden', 8.5)
        for i, (_, r_) in enumerate(block_df.iterrows()):
            row = b_start + i
            ws.cell(row=row, column=1, value=r_['Start'].year)
            ws.cell(row=row, column=2, value=r_['Start'].strftime('%Y-%m'))
            ws.cell(row=row, column=3, value=r_['Start'].strftime('%d.%m.%Y %H:%M'))
            ws.cell(row=row, column=4, value=r_['Ende'].strftime('%d.%m.%Y %H:%M'))
            ws.cell(row=row, column=5, value=int(r_['Tage']))
            ws.cell(row=row, column=6, value=int(r_['Naechte']))
            ws.cell(row=row, column=7, value=r_['Tagessaetze_EUR'])
            ws.cell(row=row, column=8, value=r_['Uebernachtung_EUR'])
            ws.cell(row=row, column=9, value=r_['Kosten_Block_EUR'])
            ws.cell(row=row, column=10, value=round(int(r_['Tage']) * enthaltene_std, 2))
        b_last = b_start + max(len(block_df) - 1, 0)
        b_sum_row = b_last + 1
        if len(block_df) > 0:
            ws.cell(row=b_sum_row, column=3, value='GESAMT Blöcke').font = bold
            for col in [7, 8, 9, 10]:
                letter = get_column_letter(col)
                ws.cell(row=b_sum_row, column=col, value=f'=SUM({letter}{b_start}:{letter}{b_last})')
        for row in ws.iter_rows(min_row=b_start, max_row=b_sum_row, min_col=1, max_col=10):
            for cell in row:
                cell.font = normal
                cell.border = border
                if cell.column in (7, 8, 9):
                    cell.number_format = '#,##0.00 €'

        p_hdr = b_sum_row + 3
        ws.cell(row=p_hdr - 1, column=1, value='Anfahrtspauschale je betroffener Kalenderwoche').font = bold
        ws.cell(row=p_hdr, column=1, value='Jahr')
        ws.cell(row=p_hdr, column=2, value='KW')
        ws.cell(row=p_hdr, column=3, value='Woche ab')
        ws.cell(row=p_hdr, column=4, value='Anfahrtspauschale (€)')
        style_header_row(ws, p_hdr, 4)
        p_start = p_hdr + 1
        for i, (_, r_) in enumerate(pausch_df.iterrows()):
            row = p_start + i
            ws.cell(row=row, column=1, value=int(r_['Jahr']))
            ws.cell(row=row, column=2, value=int(r_['KW']))
            ws.cell(row=row, column=3, value=r_['Woche_ab'].strftime('%d.%m.%Y'))
            ws.cell(row=row, column=4, value=r_['Anfahrtspauschale_EUR'])
        p_last = p_start + max(len(pausch_df) - 1, 0)
        p_sum_row = p_last + 1
        if len(pausch_df) > 0:
            ws.cell(row=p_sum_row, column=3, value='GESAMT Pauschalen').font = bold
            ws.cell(row=p_sum_row, column=4, value=f'=SUM(D{p_start}:D{p_last})')
        for row in ws.iter_rows(min_row=p_start, max_row=p_sum_row, min_col=1, max_col=4):
            for cell in row:
                cell.font = normal
                cell.border = border
                if cell.column == 4:
                    cell.number_format = '#,##0.00 €'
        autosize(ws, [10, 10, 18, 18, 14, 10, 16, 16, 16, 22])

        sonderkalk_refs[projekt] = {
            'sheet': sheet_name,
            'block_jahr_col': 'A', 'block_monat_col': 'B', 'block_kosten_col': 'I',
            'block_std_col': 'J', 'block_start': b_start, 'block_last': max(b_last, b_start),
            'pausch_jahr_col': 'A', 'pausch_kosten_col': 'D', 'pausch_start': p_start,
            'pausch_last': max(p_last, p_start),
            'has_blocks': len(block_df) > 0, 'has_pauschalen': len(pausch_df) > 0,
            'mitarbeiter': cfg.get('mitarbeiter'), 'hauptaufgabe': cfg.get('hauptaufgabe'),
        }

    # ---------------- Plausibilitäts_Check ----------------
    flagged, threshold = plausibility_check(calendar_df, config)
    ws = wb.create_sheet('Plausibilitaets_Check')
    ws['A1'] = f'Plausibilitätscheck – Wochen mit mehr als {threshold} Std. je Person'
    ws['A1'].font = Font(name=FONT, bold=True, size=12, color='C00000')
    ws['A2'] = ('Automatisch erzeugt, VOR Auslieferung prüfen. Mehrtägige Sonderkalkulations-Blocker '
                '(z.B. Niedermaier) sind hier bewusst ausgeschlossen.')
    ws['A2'].font = sub_font
    ws.append([])
    ws.append(['Mitarbeiter', 'ISO-Jahr', 'ISO-KW', 'Stunden gesamt'])
    style_header_row(ws, 4, 4)
    for i, (_, r_) in enumerate(flagged.iterrows()):
        row = 5 + i
        ws.cell(row=row, column=1, value=r_['Mitarbeiter'])
        ws.cell(row=row, column=2, value=int(r_['ISO_Jahr']))
        ws.cell(row=row, column=3, value=int(r_['ISO_KW']))
        ws.cell(row=row, column=4, value=round(r_['Dauer_h'], 1))
        for c in range(1, 5):
            ws.cell(row=row, column=c).font = normal
            ws.cell(row=row, column=c).border = border
            ws.cell(row=row, column=c).fill = flag_fill
    if len(flagged) == 0:
        ws['A5'] = 'Keine Auffälligkeiten gefunden.'
        ws['A5'].font = normal
    autosize(ws, [22, 10, 10, 16])

    return wb, {
        'n_cal_rows': n_cal_rows, 'n_trip_rows': n_trip_rows,
        'zk_start_row': zk_start_row, 'zk_last_row': zk_last_row,
        'mz_start_row': mz_start_row, 'mz_last_row': mz_last_row,
        'pz_start': pz_start, 'pz_last': max(pz_last, pz_start + 50),
        'sonderkalk_refs': sonderkalk_refs, 'mwst_param_row': mwst_param_row,
        'mitarbeiter_liste': mitarbeiter_liste, 'hauptaufgaben_liste': hauptaufgaben_liste,
        'FONT': FONT, 'title_font': title_font, 'sub_font': sub_font, 'normal': normal,
        'bold': bold, 'border': border, 'hdr_fill': hdr_fill, 'hdr_font': hdr_font,
        'kpi_fill': kpi_fill, 'output_path': output_path, 'period_label': period_label,
        'stamm_range': stamm_range,
    }


def _sonderkalk_kosten_formula(ref, jahr_filter):
    parts = []
    if ref['has_blocks']:
        rng = f"{ref['sheet']}!{ref['block_kosten_col']}{ref['block_start']}:{ref['block_kosten_col']}{ref['block_last']}"
        if jahr_filter is not None:
            jrng = f"{ref['sheet']}!{ref['block_jahr_col']}{ref['block_start']}:{ref['block_jahr_col']}{ref['block_last']}"
            parts.append(f"SUMIFS({rng},{jrng},{jahr_filter})")
        else:
            parts.append(f"SUM({rng})")
    if ref['has_pauschalen']:
        rng = f"{ref['sheet']}!{ref['pausch_kosten_col']}{ref['pausch_start']}:{ref['pausch_kosten_col']}{ref['pausch_last']}"
        if jahr_filter is not None:
            jrng = f"{ref['sheet']}!{ref['pausch_jahr_col']}{ref['pausch_start']}:{ref['pausch_jahr_col']}{ref['pausch_last']}"
            parts.append(f"SUMIFS({rng},{jrng},{jahr_filter})")
        else:
            parts.append(f"SUM({rng})")
    return '+'.join(parts) if parts else '0'


def _build_uebersicht_sheet(wb, sheet_name, title_label, jahr_filter, projects,
                             mitarbeiter_liste, config, ctx, position=None):
    from openpyxl.styles import Alignment
    from openpyxl.utils import get_column_letter

    normal, bold = ctx['normal'], ctx['bold']
    title_font, sub_font = ctx['title_font'], ctx['sub_font']
    border = ctx['border']
    n_cal, n_trip = ctx['n_cal_rows'], ctx['n_trip_rows']
    zk_s, zk_e = ctx['zk_start_row'], ctx['zk_last_row']
    mz_s, mz_e = ctx['mz_start_row'], ctx['mz_last_row']
    mwst_row = ctx['mwst_param_row']
    sonderkalk_refs = ctx['sonderkalk_refs']

    ws = wb.create_sheet(sheet_name, position) if position is not None else wb.create_sheet(sheet_name)
    ws['A1'] = title_label
    ws['A1'].font = title_font
    ws['A2'] = 'Firma/Status je Projekt bitte in Spalte B/C ergänzen, falls noch TBD (siehe Projektliste_Vorlage.xlsx)'
    ws['A2'].font = sub_font

    n_ma = len(mitarbeiter_liste)
    headers = (['Projekt', 'Firma', 'Status'] +
               [f"Std. {config['mitarbeiter_satzhistorie'][m]['kuerzel']}" for m in mitarbeiter_liste] +
               ['Std. gesamt', 'Kosten Zeit Netto (€)', 'Distanz gesamt (km)', 'Kosten Fahrt Netto (€)',
                'Fahrdauer gesamt (h, informativ)', 'Zusatzkosten Netto (€)', 'Gesamtkosten Netto (€)',
                'MwSt. (€)', 'Gesamtkosten Brutto (€)', 'Hinweis'])
    hdr_row = 4
    ws.append([])
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(row=hdr_row, column=c)
        cell.fill = ctx['hdr_fill']
        cell.font = ctx['hdr_font']
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = border

    col_std0 = 4
    col_std_gesamt = col_std0 + n_ma
    col_kzeit = col_std_gesamt + 1
    col_km = col_kzeit + 1
    col_kfahrt = col_km + 1
    col_fdauer = col_kfahrt + 1
    col_zk = col_fdauer + 1
    col_gnetto = col_zk + 1
    col_mwst = col_gnetto + 1
    col_gbrutto = col_mwst + 1
    col_hinweis = col_gbrutto + 1

    start_row = hdr_row + 1
    stamm = config.get('projekt_stammliste', {})
    wp_bez = config.get('wochenpauschale', {}).get('bezeichnung')
    for i, proj in enumerate(projects):
        row = start_row + i
        ws.cell(row=row, column=1, value=proj)
        meta = stamm.get(proj, {})
        if proj == wp_bez:
            firma = config.get('wochenpauschale', {}).get('firma', '')
            status = 'laufend'
            ws.cell(row=row, column=2, value=firma)
            ws.cell(row=row, column=3, value=status)
        else:
            ws.cell(row=row, column=2,
                    value=f'=IFERROR(VLOOKUP($A{row},{ctx["stamm_range"]},2,FALSE),"TBD")')
            ws.cell(row=row, column=3,
                    value=f'=IFERROR(VLOOKUP($A{row},{ctx["stamm_range"]},3,FALSE),"TBD")')

        jahr_crit = f',Rohdaten_Kalender!$A$2:$A${n_cal},{jahr_filter}' if jahr_filter is not None else ''
        jahr_crit_trip = f',Rohdaten_Fahrten!$A$2:$A${n_trip},{jahr_filter}' if jahr_filter is not None else ''
        jahr_crit_zk = f',Zusatzkosten!$F${zk_s}:$F${zk_e},{jahr_filter}' if jahr_filter is not None else ''
        jahr_crit_mz = f',Manuelle_Zeitbuchungen!$G${mz_s}:$G${mz_e},{jahr_filter}' if jahr_filter is not None else ''

        for j, ma in enumerate(mitarbeiter_liste):
            col = col_std0 + j
            f = (f'=SUMIFS(Rohdaten_Kalender!$K$2:$K${n_cal},'
                 f'Rohdaten_Kalender!$E$2:$E${n_cal},$A{row},'
                 f'Rohdaten_Kalender!$C$2:$C${n_cal},"{ma}",'
                 f'Rohdaten_Kalender!$O$2:$O${n_cal},""{jahr_crit})'
                 f'+SUMIFS(Manuelle_Zeitbuchungen!$E${mz_s}:$E${mz_e},'
                 f'Manuelle_Zeitbuchungen!$C${mz_s}:$C${mz_e},$A{row},'
                 f'Manuelle_Zeitbuchungen!$B${mz_s}:$B${mz_e},"{ma}"{jahr_crit_mz})')
            ws.cell(row=row, column=col, value=f)
        letters = [get_column_letter(col_std0 + j) for j in range(n_ma)]
        ws.cell(row=row, column=col_std_gesamt, value=f'=SUM({letters[0]}{row}:{letters[-1]}{row})')

        base_kzeit = (f'SUMIFS(Rohdaten_Kalender!$M$2:$M${n_cal},'
                      f'Rohdaten_Kalender!$E$2:$E${n_cal},$A{row}{jahr_crit})'
                      f'+SUMIFS(Manuelle_Zeitbuchungen!$I${mz_s}:$I${mz_e},'
                      f'Manuelle_Zeitbuchungen!$C${mz_s}:$C${mz_e},$A{row}{jahr_crit_mz})')
        if proj in sonderkalk_refs:
            sk_formula = _sonderkalk_kosten_formula(sonderkalk_refs[proj], jahr_filter)
            ws.cell(row=row, column=col_kzeit, value=f'={base_kzeit}+{sk_formula}')
        else:
            ws.cell(row=row, column=col_kzeit, value=f'={base_kzeit}')

        ws.cell(row=row, column=col_km,
                value=f'=SUMIFS(Rohdaten_Fahrten!$J$2:$J${n_trip},Rohdaten_Fahrten!$D$2:$D${n_trip},$A{row}{jahr_crit_trip})')
        ws.cell(row=row, column=col_kfahrt,
                value=f'=SUMIFS(Rohdaten_Fahrten!$M$2:$M${n_trip},Rohdaten_Fahrten!$D$2:$D${n_trip},$A{row}{jahr_crit_trip})')
        ws.cell(row=row, column=col_fdauer,
                value=f'=SUMIFS(Rohdaten_Fahrten!$K$2:$K${n_trip},Rohdaten_Fahrten!$D$2:$D${n_trip},$A{row}{jahr_crit_trip})')
        ws.cell(row=row, column=col_zk,
                value=f'=SUMIFS(Zusatzkosten!$D${zk_s}:$D${zk_e},Zusatzkosten!$B${zk_s}:$B${zk_e},$A{row}{jahr_crit_zk})')

        Lk, Lf, Lz = get_column_letter(col_kzeit), get_column_letter(col_kfahrt), get_column_letter(col_zk)
        ws.cell(row=row, column=col_gnetto, value=f'={Lk}{row}+{Lf}{row}+{Lz}{row}')
        Lg = get_column_letter(col_gnetto)
        ws.cell(row=row, column=col_mwst, value=f'={Lg}{row}*Parameter!$B${mwst_row}/100')
        Lm = get_column_letter(col_mwst)
        ws.cell(row=row, column=col_gbrutto, value=f'={Lg}{row}+{Lm}{row}')

        hinweis = ''
        if proj in sonderkalk_refs:
            hinweis = 'Sonderkalkulation (siehe eigenes Sheet). Fahrten-km/-dauer nur informativ.'
        elif proj == wp_bez:
            hinweis = 'Automatische Wochenpauschale, nicht kundenprojektbezogen.'
        ws.cell(row=row, column=col_hinweis, value=hinweis)

    last_row = start_row + len(projects) - 1
    sum_row = last_row + 1
    ws.cell(row=sum_row, column=1, value='GESAMT').font = bold
    for col in range(col_std0, col_gbrutto + 1):
        letter = get_column_letter(col)
        ws.cell(row=sum_row, column=col, value=f'=SUM({letter}{start_row}:{letter}{last_row})')

    for row in ws.iter_rows(min_row=start_row, max_row=sum_row, min_col=1, max_col=col_hinweis):
        for cell in row:
            cell.font = normal
            cell.border = border
            if cell.column in (col_kzeit, col_kfahrt, col_zk, col_gnetto, col_mwst, col_gbrutto):
                cell.number_format = '#,##0.00 €'
            if cell.column in list(range(col_std0, col_std_gesamt + 1)) + [col_fdauer]:
                cell.number_format = '#,##0.0'
            if cell.column == col_km:
                cell.number_format = '#,##0.0'
    for cell in ws[sum_row]:
        cell.font = bold

    ws.auto_filter.ref = f"A{hdr_row}:{get_column_letter(col_hinweis)}{sum_row}"
    widths = [22, 16, 12] + [9] * n_ma + [11, 16, 15, 15, 18, 15, 16, 12, 16, 45]
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    return ws, start_row, last_row, sum_row, {
        'col_std0': col_std0, 'col_std_gesamt': col_std_gesamt, 'col_kzeit': col_kzeit,
        'col_km': col_km, 'col_kfahrt': col_kfahrt, 'col_gnetto': col_gnetto,
        'col_gbrutto': col_gbrutto,
    }


def finalize_workbook(wb, ctx, calendar_df, trips_df, config, mitarbeiter_liste=None):
    """Fügt Übersicht_<Jahr>-Sheets, Gesamtsicht, Management-Summary, Monatstrend,
    interne Detailauswertung und das Filter-Dashboard hinzu und speichert."""
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.styles import Font, Alignment, PatternFill

    FONT = ctx['FONT']
    normal, bold, title_font, sub_font = ctx['normal'], ctx['bold'], ctx['title_font'], ctx['sub_font']
    border, hdr_fill, hdr_font, kpi_fill = ctx['border'], ctx['hdr_fill'], ctx['hdr_font'], ctx['kpi_fill']

    if mitarbeiter_liste is None:
        mitarbeiter_liste = ctx['mitarbeiter_liste']
    hauptaufgaben_liste = ctx['hauptaufgaben_liste']

    ignore_names = set(config.get('projektname_erkennung', {}).get('ignorieren', []))
    cal_proj = calendar_df[calendar_df['Projekt'].notna()]
    trips_proj = apply_partner_zuordnung(trips_df, config)
    trips_proj = trips_proj[trips_proj['Projekt'].notna()]
    projects = sorted(
        (set(cal_proj['Projekt'].unique()) | set(trips_proj['Projekt'].dropna().unique()))
        - ignore_names
    )
    jahre = sorted(set(int(j) for j in cal_proj['Jahr'].unique()) |
                   set(int(j) for j in trips_proj['Jahr'].dropna().unique()))

    year_refs = {}
    for jahr in jahre:
        sheet_name = f'Uebersicht_{jahr}'
        _, s_row, l_row, sum_row, cols = _build_uebersicht_sheet(
            wb, sheet_name, f'Projektübersicht {jahr}', jahr, projects, mitarbeiter_liste, config, ctx)
        year_refs[jahr] = {'sheet': sheet_name, 'sum_row': sum_row, 'cols': cols,
                             'start_row': s_row, 'last_row': l_row}

    _, g_start, g_last, g_sum, g_cols = _build_uebersicht_sheet(
        wb, 'Gesamt_Alle_Jahre', 'Projektübersicht – alle Jahre kumuliert',
        None, projects, mitarbeiter_liste, config, ctx)

    # ================= Monatstrend (Python-aggregiert, statisch) =================
    cal_cost = cal_proj.copy()
    cal_cost['Monat'] = cal_cost['Start'].dt.strftime('%Y-%m')
    monat_kosten_kal = cal_cost.groupby('Monat')['Kosten_Zeit_EUR'].sum()
    monat_std_kal = cal_cost.groupby('Monat')['Dauer_h'].sum()

    trips_cost = trips_proj.copy()
    trips_cost['Monat'] = trips_cost['Start'].dt.strftime('%Y-%m')
    monat_kosten_fahrt = trips_cost.groupby('Monat')['Kosten_Fahrt_EUR'].sum()
    monat_km = trips_cost.groupby('Monat')['Distanz (km)'].sum()

    alle_monate = sorted(set(monat_kosten_kal.index) | set(monat_kosten_fahrt.index))

    ws = wb.create_sheet('Monatstrend')
    ws['A1'] = 'Monatstrend – Stunden & Kosten'
    ws['A1'].font = title_font
    ws['A2'] = ('Automatisch aus den Rohdaten aggregiert (Stand bei Erstellung dieser Datei). '
                'Änderungen an der Partner-Zuordnung (Parameter-Reiter) NACH Erstellung wirken sich in '
                'Übersicht/Filter-Dashboard sofort aus, hier im Monatstrend erst beim nächsten Bericht-Lauf.')
    ws['A2'].font = sub_font
    ws.append([])
    ws.append(['Monat', 'Stunden gesamt', 'Kosten Zeit (€)', 'Distanz (km)', 'Kosten Fahrt (€)', 'Kosten gesamt (€)'])
    mt_hdr = 4
    for c in range(1, 7):
        cell = ws.cell(row=mt_hdr, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
        cell.alignment = Alignment(horizontal='center')
    mt_start = mt_hdr + 1
    for i, monat in enumerate(alle_monate):
        row = mt_start + i
        std = float(monat_std_kal.get(monat, 0))
        kz = float(monat_kosten_kal.get(monat, 0))
        km = float(monat_km.get(monat, 0))
        kf = float(monat_kosten_fahrt.get(monat, 0))
        ws.cell(row=row, column=1, value=monat)
        ws.cell(row=row, column=2, value=round(std, 2))
        ws.cell(row=row, column=3, value=round(kz, 2))
        ws.cell(row=row, column=4, value=round(km, 2))
        ws.cell(row=row, column=5, value=round(kf, 2))
        ws.cell(row=row, column=6, value=round(kz + kf, 2))
        for c in range(1, 7):
            ws.cell(row=row, column=c).font = normal
            ws.cell(row=row, column=c).border = border
            if c in (3, 5, 6):
                ws.cell(row=row, column=c).number_format = '#,##0.00 €'
    mt_last = mt_start + max(len(alle_monate) - 1, 0)
    ws.column_dimensions['A'].width = 12
    for col in 'BCDEF':
        ws.column_dimensions[col].width = 16

    if len(alle_monate) > 0:
        chart = LineChart()
        chart.title = 'Kosten gesamt pro Monat (€)'
        chart.y_axis.title = '€'
        chart.x_axis.title = 'Monat'
        data = Reference(ws, min_col=6, min_row=mt_hdr, max_row=mt_last)
        cats = Reference(ws, min_col=1, min_row=mt_start, max_row=mt_last)
        chart.add_data(data, titles_from_data=True)
        chart.set_categories(cats)
        chart.width, chart.height = 22, 10
        ws.add_chart(chart, f'H{mt_hdr}')

        chart2 = LineChart()
        chart2.title = 'Stunden gesamt pro Monat'
        chart2.y_axis.title = 'Std.'
        data2 = Reference(ws, min_col=2, min_row=mt_hdr, max_row=mt_last)
        chart2.add_data(data2, titles_from_data=True)
        chart2.set_categories(cats)
        chart2.width, chart2.height = 22, 10
        ws.add_chart(chart2, f'H{mt_hdr + 20}')

    # ================= Hauptaufgaben-Verteilung (Python-aggregiert) =================
    ha_std = cal_proj.groupby('Hauptaufgabe')['Dauer_h'].sum().sort_values(ascending=False)
    ws2 = wb.create_sheet('Hauptaufgaben_Verteilung')
    ws2['A1'] = 'Verteilung der Arbeitszeit nach Hauptaufgabe'
    ws2['A1'].font = title_font
    ws2.append([])
    ws2.append(['Hauptaufgabe', 'Stunden gesamt'])
    for c in range(1, 3):
        cell = ws2.cell(row=3, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
    ha_start = 4
    for i, (kat, std) in enumerate(ha_std.items()):
        row = ha_start + i
        ws2.cell(row=row, column=1, value=kat).font = normal
        ws2.cell(row=row, column=2, value=round(float(std), 2)).font = normal
    ha_last = ha_start + max(len(ha_std) - 1, 0)
    ws2.column_dimensions['A'].width = 38
    ws2.column_dimensions['B'].width = 16
    if len(ha_std) > 0:
        pie = PieChart()
        pie.title = 'Zeitverteilung nach Hauptaufgabe (alle Mitarbeiter, alle Jahre)'
        data = Reference(ws2, min_col=2, min_row=3, max_row=ha_last)
        cats = Reference(ws2, min_col=1, min_row=ha_start, max_row=ha_last)
        pie.add_data(data, titles_from_data=True)
        pie.set_categories(cats)
        pie.width, pie.height = 16, 10
        ws2.add_chart(pie, 'D3')

    # ================= Interne Detailauswertung: Monat x Mitarbeiter x Hauptaufgabe =================
    detail_rows = (cal_proj.groupby(['Start', 'Mitarbeiter', 'Hauptaufgabe'])['Dauer_h'].sum()
                   if False else None)
    tmp = cal_proj.copy()
    tmp['Monat'] = tmp['Start'].dt.strftime('%Y-%m')
    grouped = tmp.groupby(['Monat', 'Mitarbeiter', 'Hauptaufgabe']).agg(
        Stunden=('Dauer_h', 'sum'), Kosten_Zeit_EUR=('Kosten_Zeit_EUR', 'sum')).reset_index()
    # Niedermaier informative Stunden ergänzen
    nb_cfg = config.get('sonderkalkulationen', {}).get('Spedition Niedermaier')
    if nb_cfg:
        nb_blocks = cal_proj[cal_proj['Projekt'] == 'Spedition Niedermaier'].copy()
        if len(nb_blocks) > 0:
            nb_blocks['Monat'] = nb_blocks['Start'].dt.strftime('%Y-%m')
            nb_blocks['Tage'] = ((nb_blocks['Ende'] - nb_blocks['Start']).dt.total_seconds() / 86400).round()
            nb_blocks['InfoStd'] = nb_blocks['Tage'] * nb_cfg.get('tagessatz_enthaltene_stunden', 8.5)
            nb_grouped = nb_blocks.groupby('Monat')['InfoStd'].sum().reset_index()
            nb_grouped['Mitarbeiter'] = nb_cfg.get('mitarbeiter')
            nb_grouped['Hauptaufgabe'] = nb_cfg.get('hauptaufgabe')
            nb_grouped['Kosten_Zeit_EUR'] = 0
            nb_grouped = nb_grouped.rename(columns={'InfoStd': 'Stunden'})
            grouped = pd.concat([grouped, nb_grouped[['Monat', 'Mitarbeiter', 'Hauptaufgabe', 'Stunden', 'Kosten_Zeit_EUR']]],
                                  ignore_index=True)
    grouped = grouped.sort_values(['Monat', 'Mitarbeiter', 'Hauptaufgabe'])

    ws3 = wb.create_sheet('Interne_Auswertung')
    ws3['A1'] = 'Interne Detailauswertung – Monat × Mitarbeiter × Hauptaufgabe'
    ws3['A1'].font = title_font
    ws3['A2'] = ('Eine Zeile je Kombination. Über AutoFilter/PivotTable in Excel selbst weiter '
                 'auswertbar (z.B. nach Mitarbeiter oder Monat filtern). Enthält Niedermaier als '
                 'informative Stunden (keine Kostenwirkung hier, siehe eigenes Sonderkalkulations-Sheet).')
    ws3['A2'].font = sub_font
    ws3.append([])
    ws3.append(['Monat', 'Mitarbeiter', 'Hauptaufgabe', 'Stunden', 'Kosten Zeit (€, ohne Sonderkalk.)'])
    ia_hdr = 4
    for c in range(1, 6):
        cell = ws3.cell(row=ia_hdr, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
    ia_start = ia_hdr + 1
    for i, (_, r_) in enumerate(grouped.iterrows()):
        row = ia_start + i
        ws3.cell(row=row, column=1, value=r_['Monat'])
        ws3.cell(row=row, column=2, value=r_['Mitarbeiter'])
        ws3.cell(row=row, column=3, value=r_['Hauptaufgabe'])
        ws3.cell(row=row, column=4, value=round(float(r_['Stunden']), 2))
        ws3.cell(row=row, column=5, value=round(float(r_['Kosten_Zeit_EUR']), 2))
        for c in range(1, 6):
            ws3.cell(row=row, column=c).font = normal
            ws3.cell(row=row, column=c).border = border
    ia_last = ia_start + max(len(grouped) - 1, 0)
    ws3.auto_filter.ref = f"A{ia_hdr}:E{ia_last}"
    autosize_widths = [12, 20, 32, 12, 26]
    for i, w in enumerate(autosize_widths, start=1):
        ws3.column_dimensions[get_column_letter(i)].width = w

    # ================= Listen (versteckt) =================
    ws = wb.create_sheet('Listen')
    headers_listen = ['Jahr', 'Monat', 'Mitarbeiter', 'Projekt', 'Firma', 'Hauptaufgabe']
    for i, h in enumerate(headers_listen, start=1):
        ws.cell(row=1, column=i, value=h)
        ws.cell(row=2, column=i, value='(Alle)')
    for i, j in enumerate(jahre):
        ws.cell(row=3 + i, column=1, value=j)
    for i, m in enumerate(alle_monate):
        ws.cell(row=3 + i, column=2, value=m)
    for i, m in enumerate(mitarbeiter_liste):
        ws.cell(row=3 + i, column=3, value=m)
    for i, p in enumerate(projects):
        ws.cell(row=3 + i, column=4, value=p)
    firmen = sorted({config.get('projekt_stammliste', {}).get(p, {}).get('firma', 'TBD') for p in projects}
                    | {'Neininger GmbH', 'TransCare'})
    for i, f in enumerate(firmen):
        ws.cell(row=3 + i, column=5, value=f)
    for i, h in enumerate(hauptaufgaben_liste):
        ws.cell(row=3 + i, column=6, value=h)
    ws.sheet_state = 'hidden'

    # ================= Filter-Dashboard (SUMIFS, robust) =================
    ws = wb.create_sheet('Filter_Dashboard', 1)
    ws['A1'] = 'Filter-Dashboard'
    ws['A1'].font = title_font
    ws['A2'] = ('Dropdowns wählen ("(Alle)" = keine Einschränkung). Ergebnis unten aktualisiert sich automatisch. '
                'Hinweis: "Stunden/Kosten Zeit" hier stammen nur aus echten Kalendereinträgen (ohne manuelle '
                'Zeitbuchungen und ohne Sonderkalkulationen wie Spedition Niedermaier) - für die vollständige '
                'Summe inkl. dieser Posten die Uebersicht_<Jahr>- bzw. Gesamt_Alle_Jahre-Sheets verwenden.')
    ws['A2'].font = sub_font

    filter_defs = [
        ('Jahr', 'A', True), ('Monat', 'B', False), ('Mitarbeiter', 'C', False),
        ('Projekt', 'D', False), ('Firma', 'E', False), ('Hauptaufgabe', 'F', False),
    ]
    dv_rows = {}
    for i, (label, listen_col, is_numeric) in enumerate(filter_defs):
        r = 4 + i
        ws.cell(row=r, column=1, value=label).font = bold
        ws.cell(row=r, column=2, value='(Alle)').font = normal
        if is_numeric:
            helper = f'=IF(B{r}="(Alle)",">=0",B{r})'
        else:
            helper = f'=IF(B{r}="(Alle)","*",B{r})'
        ws.cell(row=r, column=3, value=helper).font = Font(name=FONT, size=8, italic=True, color='999999')
        n_vals = len({'Jahr': jahre, 'Monat': alle_monate, 'Mitarbeiter': mitarbeiter_liste,
                      'Projekt': projects, 'Firma': firmen, 'Hauptaufgabe': hauptaufgaben_liste}[label]) + 1
        dv = DataValidation(type="list", formula1=f'=Listen!${listen_col}$2:${listen_col}${1+n_vals}', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f'B{r}')
        dv_rows[label] = r
    ws.column_dimensions['C'].width = 2
    ws.cell(row=4, column=3).font = Font(size=1)
    for lbl in filter_defs:
        pass

    sel_jahr = f'$C${dv_rows["Jahr"]}'
    sel_monat = f'$C${dv_rows["Monat"]}'
    sel_ma = f'$C${dv_rows["Mitarbeiter"]}'
    sel_proj = f'$C${dv_rows["Projekt"]}'
    sel_firma = f'$C${dv_rows["Firma"]}'
    sel_ha = f'$C${dv_rows["Hauptaufgabe"]}'

    n_cal, n_trip = ctx['n_cal_rows'], ctx['n_trip_rows']
    zk_s, zk_e = ctx['zk_start_row'], ctx['zk_last_row']
    mwst_row = ctx['mwst_param_row']

    cal_rng = lambda col: f"Rohdaten_Kalender!${col}$2:${col}${n_cal}"
    trip_rng = lambda col: f"Rohdaten_Fahrten!${col}$2:${col}${n_trip}"
    zk_rng = lambda col: f"Zusatzkosten!${col}${zk_s}:${col}${zk_e}"

    row0 = 12
    ws.cell(row=row0, column=1, value='Ergebnis für die Auswahl:').font = bold
    labels_res = ['Stunden gesamt', 'Kosten Zeit Netto (€)', 'Distanz gesamt (km)',
                  'Kosten Fahrt Netto (€)', 'Zusatzkosten Netto (€, nur Jahr/Monat/Projekt)',
                  'Gesamtkosten Netto (€)', 'MwSt. (€)', 'Gesamtkosten Brutto (€)']
    for i, lab in enumerate(labels_res):
        ws.cell(row=row0 + 1 + i, column=1, value=lab).font = normal

    stunden_f = (f'=SUMIFS({cal_rng("K")},{cal_rng("O")},"",{cal_rng("A")},{sel_jahr},'
                 f'{cal_rng("B")},{sel_monat},{cal_rng("C")},{sel_ma},{cal_rng("E")},{sel_proj},'
                 f'{cal_rng("F")},{sel_firma},{cal_rng("G")},{sel_ha},{cal_rng("E")},"?*",'
                 f'{cal_rng("F")},"<>Ignoriert / kein Projekt")')
    kzeit_f = (f'=SUMIFS({cal_rng("M")},{cal_rng("A")},{sel_jahr},{cal_rng("B")},{sel_monat},'
               f'{cal_rng("C")},{sel_ma},{cal_rng("E")},{sel_proj},{cal_rng("F")},{sel_firma},'
               f'{cal_rng("G")},{sel_ha},{cal_rng("E")},"?*",'
               f'{cal_rng("F")},"<>Ignoriert / kein Projekt")')
    km_f = (f'=SUMIFS({trip_rng("J")},{trip_rng("A")},{sel_jahr},{trip_rng("B")},{sel_monat},'
            f'{trip_rng("C")},{sel_ma},{trip_rng("D")},{sel_proj},{trip_rng("E")},{sel_firma},'
            f'{trip_rng("D")},"?*")')
    kfahrt_f = (f'=SUMIFS({trip_rng("M")},{trip_rng("A")},{sel_jahr},{trip_rng("B")},{sel_monat},'
                f'{trip_rng("C")},{sel_ma},{trip_rng("D")},{sel_proj},{trip_rng("E")},{sel_firma},'
                f'{trip_rng("D")},"?*")')
    zk_f = (f'=SUMIFS({zk_rng("D")},{zk_rng("F")},{sel_jahr},{zk_rng("G")},{sel_monat},{zk_rng("B")},{sel_proj})')

    ws.cell(row=row0 + 1, column=2, value=stunden_f)
    ws.cell(row=row0 + 2, column=2, value=kzeit_f)
    ws.cell(row=row0 + 3, column=2, value=km_f)
    ws.cell(row=row0 + 4, column=2, value=kfahrt_f)
    ws.cell(row=row0 + 5, column=2, value=zk_f)
    ws.cell(row=row0 + 6, column=2, value=f'=B{row0+2}+B{row0+4}+B{row0+5}')
    ws.cell(row=row0 + 7, column=2, value=f'=B{row0+6}*Parameter!$B${mwst_row}/100')
    ws.cell(row=row0 + 8, column=2, value=f'=B{row0+6}+B{row0+7}')

    for i in range(1, 9):
        c = ws.cell(row=row0 + i, column=2)
        c.font = bold
        c.number_format = '#,##0.0' if i in (1, 3) else '#,##0.00 €'
    ws.column_dimensions['A'].width = 42
    ws.column_dimensions['B'].width = 20

    # ---- Aufschlüsselung nach Mitarbeiter x Hauptaufgabe (für aktuelle Auswahl oben) ----
    row_x0 = row0 + 11
    ws.cell(row=row_x0, column=1, value='Aufschlüsselung nach Mitarbeiter × Hauptaufgabe (Std.), für die Auswahl oben').font = bold
    hdr_x = row_x0 + 1
    ws.cell(row=hdr_x, column=1, value='Mitarbeiter').fill = hdr_fill
    ws.cell(row=hdr_x, column=1).font = hdr_font
    ws.cell(row=hdr_x, column=1).border = border
    for j, ha in enumerate(hauptaufgaben_liste):
        c = ws.cell(row=hdr_x, column=2 + j, value=ha)
        c.fill = hdr_fill; c.font = hdr_font; c.border = border
        c.alignment = Alignment(wrap_text=True, horizontal='center')
    col_gesamt_x = 2 + len(hauptaufgaben_liste)
    col_kosten_x = col_gesamt_x + 1
    for c, lbl in [(col_gesamt_x, 'Std. gesamt'), (col_kosten_x, 'Kosten Zeit (€)')]:
        cell = ws.cell(row=hdr_x, column=c, value=lbl)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
        cell.alignment = Alignment(wrap_text=True, horizontal='center')

    for i, ma in enumerate(mitarbeiter_liste):
        row = hdr_x + 1 + i
        ws.cell(row=row, column=1, value=ma).font = normal
        ws.cell(row=row, column=1).border = border
        row_letters = []
        for j, ha in enumerate(hauptaufgaben_liste):
            col = 2 + j
            f = (f'=SUMIFS({cal_rng("K")},{cal_rng("O")},"",{cal_rng("A")},{sel_jahr},'
                 f'{cal_rng("B")},{sel_monat},{cal_rng("C")},"{ma}",{cal_rng("E")},{sel_proj},'
                 f'{cal_rng("F")},{sel_firma},{cal_rng("G")},"{ha}",{cal_rng("E")},"?*",'
                 f'{cal_rng("F")},"<>Ignoriert / kein Projekt")')
            ws.cell(row=row, column=col, value=f)
            ws.cell(row=row, column=col).number_format = '#,##0.0'
            ws.cell(row=row, column=col).border = border
            row_letters.append(get_column_letter(col))
        ws.cell(row=row, column=col_gesamt_x,
                value=f'=SUM({row_letters[0]}{row}:{row_letters[-1]}{row})')
        ws.cell(row=row, column=col_gesamt_x).font = bold
        ws.cell(row=row, column=col_gesamt_x).number_format = '#,##0.0'
        ws.cell(row=row, column=col_gesamt_x).border = border
        kzeit_ma_f = (f'=SUMIFS({cal_rng("M")},{cal_rng("A")},{sel_jahr},{cal_rng("B")},{sel_monat},'
                      f'{cal_rng("C")},"{ma}",{cal_rng("E")},{sel_proj},{cal_rng("F")},{sel_firma},'
                      f'{cal_rng("E")},"?*")')
        ws.cell(row=row, column=col_kosten_x, value=kzeit_ma_f)
        ws.cell(row=row, column=col_kosten_x).number_format = '#,##0.00 €'
        ws.cell(row=row, column=col_kosten_x).border = border

    sum_row_x = hdr_x + 1 + len(mitarbeiter_liste)
    ws.cell(row=sum_row_x, column=1, value='GESAMT').font = bold
    for c in range(2, col_kosten_x + 1):
        letter = get_column_letter(c)
        ws.cell(row=sum_row_x, column=c, value=f'=SUM({letter}{hdr_x+1}:{letter}{sum_row_x-1})')
        ws.cell(row=sum_row_x, column=c).font = bold
        ws.cell(row=sum_row_x, column=c).number_format = '#,##0.0' if c < col_kosten_x else '#,##0.00 €'
    ws.cell(row=sum_row_x + 2, column=1,
            value=('Hinweis: Diese Tabelle berücksichtigt nur die Filter Jahr/Monat/Projekt/Firma von oben '
                   '(Mitarbeiter und Hauptaufgabe werden hier je Zeile/Spalte einzeln aufgeschlüsselt).')
            ).font = sub_font

    for j in range(len(hauptaufgaben_liste)):
        ws.column_dimensions[get_column_letter(2 + j)].width = 15
    ws.column_dimensions[get_column_letter(col_gesamt_x)].width = 13
    ws.column_dimensions[get_column_letter(col_kosten_x)].width = 16


    # ================= Reihenfolge der Reiter (nutzerfreundlich) =================
    sonderkalk_sheet_names = [ref['sheet'] for ref in ctx['sonderkalk_refs'].values()]
    front = (['Filter_Dashboard'] +
             [f'Uebersicht_{j}' for j in jahre] +
             ['Gesamt_Alle_Jahre', 'Monatstrend', 'Hauptaufgaben_Verteilung', 'Interne_Auswertung'])
    mitte = (['Parameter', 'Zusatzkosten', 'Manuelle_Zeitbuchungen'] +
             sonderkalk_sheet_names + ['Plausibilitaets_Check'])
    hinten = ['Rohdaten_Kalender', 'Rohdaten_Fahrten', 'Listen']
    desired_order = [s for s in front + mitte + hinten if s in wb.sheetnames]
    fehlend = [s for s in wb.sheetnames if s not in desired_order]
    wb._sheets = [wb[name] for name in desired_order + fehlend]
    wb.active = 0

    wb.save(ctx['output_path'])
    return ctx['output_path']
