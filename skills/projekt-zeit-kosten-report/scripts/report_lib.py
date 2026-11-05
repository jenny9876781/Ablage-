"""
report_lib.py — Kernlogik für den Neininger Projekt-Zeit-/Kosten-Report.

Version 2 (2026-07-22): Mehrjahres-Auswertung (2024ff.), Satzhistorie mit
Gültig-ab-Datum, Hauptaufgaben-Kategorien, automatische Wochenpauschale,
manuelle Zusatzkosten, Plausibilitätscheck, MwSt.-Ausweis, Filter-Dashboard.

Version 6 (2026-11): Absicherung (Welle 1). Versionsregel + Stopp bei
veralteter Vorlage, feste Fortführungs-Funktion, Prüfblatt "Abgleich_Vormonate",
Spalte "Zuordnung_Grund" + gelbe Markierung + Reiter "Pruefliste", reparierte
Lade-Funktionen, Kosten je Kalenderzeile als Formel, Soll-Arbeitszeit entfernt.
Einstieg für den Monatsablauf: neuaufbau() bzw. fortfuehrung() (ganz unten).

Diese Bibliothek wird von Jahr/Monat zu Jahr/Monat wiederverwendet. Nur
config/projekt_konfiguration.json und die hochgeladenen Rohdateien ändern sich.
"""
SKILL_VERSION = '6.0'
HINWEIS_STATISCH = ('ACHTUNG (bekannte Einschränkung, Version 6 nur markiert): statische Werte - enthalten auch mehrtägige Blöcke und ignorierte Termine, berücksichtigen keine manuellen Korrekturen. Für Freigabe/Abrechnung nur Uebersicht_<Jahr> bzw. Gesamt_Alle_Jahre verwenden.')

import json
import re
import warnings
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
ANFUEHRUNGSZEICHEN = '"\u201c\u201d\u201e\u00ab\u00bb'   # " “ ” „ « »
_QUOTE_RE = re.compile(r'[%s]\s*([^%s]+?)\s*[%s]' % ((ANFUEHRUNGSZEICHEN,) * 3))


def _norm(s):
    return re.sub(r'\s+', ' ', str(s)).strip().casefold()


def erkenne_projekt(betreff, config):
    """Erkennt das Projekt im Kalender-Betreff UND begründet die Zuordnung.

    Rückgabe dict: projekt, rest, grund, unsicher (bool).
    unsicher=True heißt: zugeordnet bzw. nicht zugeordnet, aber bitte prüfen
    (gelb in Rohdaten_Kalender + Eintrag in der Pruefliste). Es wird NICHT geraten:
    ein unquotierter, nur 'möglicher' Projektbezug wird NICHT zugeordnet, nur gemeldet.
    """
    pe = config.get('projektname_erkennung', {})
    fixed_names = pe.get('feste_namen_ohne_anfuehrungszeichen', [])
    ignore = list(pe.get('ignorieren', []))
    aliase = {k: v for k, v in pe.get('aliase', {}).items() if not k.startswith('_')}
    stamm = {k for k, v in config.get('projekt_stammliste', {}).items()
             if not k.startswith('_') and isinstance(v, dict)}
    out = {'projekt': None, 'rest': betreff, 'grund': 'Kein Projektname erkannt', 'unsicher': False}
    if not isinstance(betreff, str):
        return out

    treffer = list(_QUOTE_RE.finditer(betreff))
    if treffer:
        m = treffer[0]
        roh = re.sub(r'\s+', ' ', m.group(1).strip())
        typografisch = m.group(0)[0] != '"' or m.group(0)[-1] != '"'
        rest = (betreff[:m.start()] + betreff[m.end():]).strip(' -/')
        unsicher = False
        if roh in aliase:
            proj, grund = aliase[roh], f'Alias {roh} \u2192 {aliase[roh]}'
        elif roh in stamm or roh in ignore or roh in fixed_names:
            proj, grund = roh, 'Projektname im Betreff'
        else:
            # abweichende Schreibweise (Groß/Klein, Leerzeichen) eines bekannten Namens?
            bekannt = {_norm(a): (a, z) for a, z in aliase.items()}
            for n in list(stamm) + ignore + list(fixed_names):
                bekannt.setdefault(_norm(n), (n, n))
            if _norm(roh) in bekannt:
                quelle, proj = bekannt[_norm(roh)]
                grund = f'Schreibweise angeglichen: "{roh}" \u2192 {proj} (bitte bestätigen)'
                unsicher = True
            else:
                proj = roh
                grund = 'Unbekannter Projektname (nicht in Stammliste) - bitte bestätigen'
                unsicher = True
        if proj in ignore or _norm(proj) in {_norm(x) for x in ignore}:
            grund = 'Ignoriert lt. Config (kein Projekt)'
        elif typografisch and not unsicher:
            grund += ' (typografische Anführungszeichen)'
        weitere = {aliase.get(re.sub(r'\s+', ' ', t.group(1).strip()), re.sub(r'\s+', ' ', t.group(1).strip()))
                   for t in treffer[1:]} - {proj}
        if weitere:
            grund += f'; weitere Namen im Betreff: {", ".join(sorted(weitere))} - bitte prüfen'
            unsicher = True
        return {'projekt': proj, 'rest': rest, 'grund': grund, 'unsicher': unsicher}

    for fixed in fixed_names:
        if fixed.lower() in betreff.lower():
            rest = re.sub(re.escape(fixed), '', betreff, flags=re.I).strip(' -/')
            return {'projekt': fixed, 'rest': rest,
                    'grund': f'Fester Name ohne Anführungszeichen ({fixed})', 'unsicher': False}

    # Kein Projekt erkannt: möglicher unquotierter Bezug nur MELDEN, nicht zuordnen
    ausnahmen = {_norm(x) for x in pe.get('keine_hinweise_fuer', [])}
    kandidaten = {}
    for n in list(stamm) + list(aliase.keys()):
        if _norm(n) in ausnahmen or len(n) < 3:
            continue
        if re.search(r'(?<!\w)' + re.escape(n) + r'(?!\w)', betreff, flags=re.I):
            kandidaten[aliase.get(n, n)] = True
    if kandidaten:
        out['grund'] = ('Kein Projekt in Anführungszeichen - möglicher Bezug: '
                        + ', '.join(sorted(kandidaten)) + ' (NICHT zugeordnet, bitte prüfen)')
        out['unsicher'] = True
    return out


def extract_project(betreff, fixed_names, ignore_names=None, aliase=None):
    """Kompatibilitäts-Wrapper (alte Signatur) um erkenne_projekt()."""
    cfg = {'projektname_erkennung': {'feste_namen_ohne_anfuehrungszeichen': fixed_names,
                                     'ignorieren': ignore_names or [], 'aliase': aliase or {}}}
    r = erkenne_projekt(betreff, cfg)
    return r['projekt'], r['rest']


def _enrich_calendar_df(df, mitarbeiter, kalendertyp, config):
    """Gemeinsame Anreicherung für alle Kalenderquellen: erwartet df mit Spalten
    Betreff, Start, Ende, Ort (Start/Ende als echte datetime). Fügt Mitarbeiter,
    Kalendertyp, Projekt, Aufgabe, Hauptaufgabe, Dauer_h, Mehrtaegig, Jahr,
    Ist_Urlaub, Ist_Pauschale hinzu."""
    df = df.copy()
    df['Mitarbeiter'] = mitarbeiter
    df['Kalendertyp'] = kalendertyp

    erk = df['Betreff'].apply(lambda b: erkenne_projekt(b, config))
    df['Projekt'] = erk.apply(lambda e: e['projekt'])
    df['Aufgabe'] = erk.apply(lambda e: e['rest'])
    df['Zuordnung_Grund'] = erk.apply(lambda e: e['grund'])
    df['Unsicher'] = erk.apply(lambda e: e['unsicher'])
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
                'Jahr', 'Ist_Urlaub', 'Ist_Pauschale', 'Zuordnung_Grund', 'Unsicher']]


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
                'Zuordnung_Grund': 'Automatische Wochenpauschale', 'Unsicher': False,
            })
        else:
            rows.append({
                'Mitarbeiter': mitarbeiter, 'Kalendertyp': 'Pauschale',
                'Betreff': cfg['bezeichnung'],
                'Start': monday, 'Ende': monday + timedelta(hours=stunden), 'Ort': None,
                'Projekt': cfg['bezeichnung'], 'Aufgabe': cfg['bezeichnung'],
                'Hauptaufgabe': cfg['kategorie'], 'Dauer_h': float(stunden), 'Mehrtaegig': False,
                'Jahr': monday.year, 'Ist_Urlaub': False, 'Ist_Pauschale': True,
                'Zuordnung_Grund': 'Automatische Wochenpauschale', 'Unsicher': False,
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
def _partner_mapping(config):
    return {k: v for k, v in config.get('partner_projekt_zuordnung', {}).items()
            if not str(k).startswith('_') and v not in (None, '', 0)}


def apply_partner_zuordnung(trips_df, config):
    """Ermittelt das wirksame Projekt je Fahrt - exakt dieselbe Logik wie die
    Excel-Formel in Rohdaten_Fahrten (Version 6):

    1. Manuelle Projekt-Korrektur (Spalte 'Korrektur', falls vorhanden) hat Vorrang.
    2. Partner = 'Unberücksichtigt' gewinnt vor dem Kalender-Match (Nutzerin
       2026-11-04). Die Fahrt bleibt aber SICHTBAR in Rohdaten_Fahrten (Projekt leer),
       sie wird nicht mehr gelöscht - so kann die Zuordnung live geändert werden.
    3. Kalender-Match (Spalte 'Projekt_Kalender'), sofern kein ignoriertes Projekt.
    4. Partner -> Projekt als Fallback.
    Idempotent: kann mehrfach aufgerufen werden (rechnet immer aus Projekt_Kalender)."""
    mapping = _partner_mapping(config)
    ignore = set(config.get('projektname_erkennung', {}).get('ignorieren', []))
    df = trips_df.copy()
    if 'Projekt_Kalender' not in df.columns:
        df['Projekt_Kalender'] = df['Projekt'] if 'Projekt' in df.columns else None
    if 'Korrektur' not in df.columns:
        df['Korrektur'] = None
    if 'Zuordnung_Grund' not in df.columns:
        df['Zuordnung_Grund'] = ''
    if 'Unsicher' not in df.columns:
        df['Unsicher'] = False

    def wirksam(row):
        korr = row['Korrektur']
        grund_kal = row['Zuordnung_Grund'] or ''
        if isinstance(korr, str) and korr.strip():
            if korr == 'Unberücksichtigt':
                return None, 'Manuelle Korrektur', 'Manuelle Korrektur: Unberücksichtigt', False
            return korr, 'Manuelle Korrektur', f'Manuelle Korrektur: {korr}', False
        partner = row.get('Partner')
        ziel = mapping.get(partner) if isinstance(partner, str) else None
        kal = row['Projekt_Kalender']
        kal = kal if isinstance(kal, str) and kal else None
        if ziel == 'Unberücksichtigt':
            g = f'Partner "{partner}" = Unberücksichtigt (hat Vorrang)'
            if kal:
                g += f'; Kalender-Match wäre {kal} gewesen'
            return None, 'Unberücksichtigt (Partner)', g, False
        if kal and kal not in ignore:
            return kal, 'Kalender-Matching', grund_kal, bool(row['Unsicher'])
        if ziel:
            g = f'Partner-Zuordnung: {partner} \u2192 {ziel}'
            if kal:
                g = f'Kalender-Match nur mit ignoriertem Termin ({kal}); ' + g
            return ziel, 'Partner-Zuordnung (automatisch)', g, False
        if kal:
            return None, 'Kalender-Match (ignoriertes Projekt)', grund_kal or f'Match mit ignoriertem Termin ({kal})', False
        return None, '', 'Nicht zugeordnet (kein Termin im Zeitfenster, kein Partner)', False

    if len(df) == 0:
        df['Projekt'] = None
        df['Zuordnungsart'] = ''
        return df
    res = df.apply(wirksam, axis=1, result_type='expand')
    df['Projekt'] = res[0]
    df['Zuordnungsart'] = res[1]
    df['Zuordnung_Grund_wirksam'] = res[2]
    df['Unsicher_wirksam'] = res[3]
    return df


def match_trips_to_calendar(trips_df, calendar_df, mitarbeiter,
                             window_before=timedelta(hours=36),
                             window_after=timedelta(hours=4), config=None):
    """Ordnet Fahrten per Zeitfenster dem nächstgelegenen Projekttermin zu
    (Spalte 'Projekt' = 'Projekt_Kalender'). Version 6: zusätzlich
    'Zuordnung_Grund' und 'Unsicher' - unsicher, wenn mehrere VERSCHIEDENE
    Projekte im Fenster liegen oder der Treffer ein mehrtägiger Block eines
    normalen Projekts ist. Die Wahl selbst (nächster Termin) bleibt unverändert."""
    cal = calendar_df[
        (calendar_df['Mitarbeiter'] == mitarbeiter) & (calendar_df['Projekt'].notna()) &
        (~calendar_df['Ist_Pauschale'].astype(bool))
    ].copy()
    sonderkalk = set()
    if config:
        sonderkalk = {p for p, c in config.get('sonderkalkulationen', {}).items()
                      if not p.startswith('_') and isinstance(c, dict)}
    trips = trips_df.copy()
    trips['Projekt'] = None
    trips['Zuordnung_Grund'] = 'Nicht zugeordnet (kein Termin im Zeitfenster)'
    trips['Unsicher'] = False
    for ti, trip in trips.iterrows():
        candidates = cal[
            (trip['Start'] >= cal['Start'] - window_before) &
            (trip['Start'] <= cal['Ende'] + window_after)
        ]
        if len(candidates) == 0:
            continue
        candidates = candidates.copy()
        candidates['delta'] = (candidates['Start'] - trip['Start']).abs()
        candidates = candidates.sort_values('delta', kind='stable')
        best = candidates.iloc[0]
        trips.at[ti, 'Projekt'] = best['Projekt']
        grund = f"Zeitfenster-Match mit Termin {best['Start']:%d.%m.%Y %H:%M} ({best['Projekt']})"
        unsicher = False
        andere = [p for p in dict.fromkeys(candidates['Projekt']) if p != best['Projekt']]
        if andere:
            grund += '; weitere Projekte im Fenster: ' + ', '.join(map(str, andere)) + ' - bitte prüfen'
            unsicher = True
        mehrt = bool(best.get('Mehrtaegig', False))
        if mehrt and best['Projekt'] not in sonderkalk:
            grund += '; Treffer ist ein mehrtägiger Block - bitte prüfen'
            unsicher = True
        trips.at[ti, 'Zuordnung_Grund'] = grund
        trips.at[ti, 'Unsicher'] = unsicher
    trips['Projekt_Kalender'] = trips['Projekt']
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
    df = markiere_pruefpunkte_kalender(df, config)
    return df


def _kalendertage(start, ende):
    """Überspannte Kalendertage (gleiche Konvention wie adjust_dauer)."""
    if start.hour == 0 and start.minute == 0 and ende.hour == 0 and ende.minute == 0:
        return max((ende.date() - start.date()).days, 1)
    return (ende.date() - start.date()).days + 1


def markiere_pruefpunkte_kalender(df, config):
    """Version 6: markiert (NICHT korrigiert) Kalenderzeilen, die geprüft werden
    sollten. Zahlen bleiben unverändert - Entscheidung trifft die Nutzerin.
    - Kurztermin bei Tagessatz-Projekt (löst die Anfahrtspauschale der KW aus)
    - Tagessatz-Block, bei dem die gerundete Tageszahl von den Kalendertagen abweicht
    - mehrtägiger Block (>20 h) eines normalen Projekts (zählt mit 0 Std.)"""
    df = df.copy()
    for col, default in (('Zuordnung_Grund', ''), ('Unsicher', False)):
        if col not in df.columns:
            df[col] = default
    df['Zuordnung_Grund'] = df['Zuordnung_Grund'].fillna('')
    df['Unsicher'] = df['Unsicher'].fillna(False).astype(bool)
    tb = {p for p, c in config.get('sonderkalkulationen', {}).items()
          if not p.startswith('_') and isinstance(c, dict) and c.get('typ') == 'tagessatz_block'}
    ganztag = {p for p in config.get('ganztagespauschale', {}) if not p.startswith('_')}
    for idx, r in df.iterrows():
        if r.get('Ist_Pauschale', False) or pd.isna(r['Projekt']):
            continue
        zusatz = None
        if r['Projekt'] in tb:
            if not r['Mehrtaegig']:
                zusatz = ('Kurztermin bei Tagessatz-Projekt: löst die Anfahrtspauschale der '
                          'Kalenderwoche aus - bitte prüfen')
            else:
                gerundet = round((r['Ende'] - r['Start']).total_seconds() / 86400.0)
                kal = _kalendertage(r['Start'], r['Ende'])
                if gerundet != kal:
                    zusatz = (f'Tageszählung prüfen: berechnet {gerundet} Tage, '
                              f'überspannt {kal} Kalendertage')
        elif r['Mehrtaegig'] and r['Projekt'] not in ganztag:
            zusatz = 'Mehrtägiger Block (> 20 h) - zählt mit 0 Std., bitte klären'
        if zusatz:
            g = r['Zuordnung_Grund']
            df.at[idx, 'Zuordnung_Grund'] = f'{g}; {zusatz}' if g else zusatz
            df.at[idx, 'Unsicher'] = True
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
        # Version 6: Zeilen aus der Vorversion behalten ihren Satz (eingefroren)
        if 'KmSatz_EUR' in r.index and pd.notna(r['KmSatz_EUR']):
            return r['KmSatz_EUR']
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
def _wb(path_or_wb):
    """Öffnet eine Ausgabedatei (nur Werte). Fehler werden NICHT verschluckt."""
    if hasattr(path_or_wb, 'sheetnames'):
        return path_or_wb
    from openpyxl import load_workbook
    return load_workbook(path_or_wb, data_only=True)


def _finde_zelle(ws, text, max_row=80, max_col=40, rechts=None):
    """Sucht eine Zelle mit exakt diesem Text (optional: rechter Nachbar = rechts)."""
    for row in ws.iter_rows(min_row=1, max_row=min(ws.max_row, max_row), max_col=max_col):
        for c in row:
            if isinstance(c.value, str) and c.value.strip() == text:
                if rechts is None or ws.cell(row=c.row, column=c.column + 1).value == rechts:
                    return c.row, c.column
    return None


def _tabelle_ab_kopf(ws, kopf_text, n_spalten):
    """Liest Zeilen unterhalb der Kopfzeile (Spalte A == kopf_text). Version 6:
    sucht die Kopfzeile, statt eine feste Startzeile anzunehmen (Bugfix: die
    alte start_row=6 hat die erste Datenzeile in Zeile 5 übersprungen)."""
    pos = _finde_zelle(ws, kopf_text, max_col=1)
    if pos is None:
        raise ValueError(f'Reiter {ws.title}: Kopfzeile "{kopf_text}" nicht gefunden')
    rows = []
    for row in ws.iter_rows(min_row=pos[0] + 1, max_col=n_spalten, values_only=True):
        if not row or row[0] is None or (isinstance(row[0], str) and not row[0].strip()):
            continue
        rows.append(list(row) + [None] * (n_spalten - len(row)))
    return rows


def load_zusatzkosten_from_workbook(path, sheet_name='Zusatzkosten', start_row=None):
    """Liest erfasste Zusatzkosten aus einer früheren Ausgabedatei."""
    cols = ['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR', 'Anmerkung']
    wb = _wb(path)
    if sheet_name not in wb.sheetnames:
        warnings.warn(f'Reiter {sheet_name} fehlt in der Vorlage - keine Zusatzkosten übernommen')
        return pd.DataFrame(columns=cols)
    rows = _tabelle_ab_kopf(wb[sheet_name], 'Datum', 5)
    return pd.DataFrame([r[:5] for r in rows], columns=cols)


def load_manuelle_zeitbuchungen_from_workbook(path, sheet_name='Manuelle_Zeitbuchungen', start_row=None):
    """Liest manuelle Zeitbuchungen aus einer früheren Ausgabedatei."""
    cols = ['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe', 'Stunden', 'Anmerkung']
    wb = _wb(path)
    if sheet_name not in wb.sheetnames:
        warnings.warn(f'Reiter {sheet_name} fehlt in der Vorlage - keine Zeitbuchungen übernommen')
        return pd.DataFrame(columns=cols)
    rows = _tabelle_ab_kopf(wb[sheet_name], 'Datum', 6)
    return pd.DataFrame([r[:6] for r in rows], columns=cols)


def load_partner_zuordnung_from_workbook(path, sheet_name='Parameter', start_row=None):
    """Liest die Partner->Projekt-Zuordnung. Version 6: sucht die Tabelle im
    Parameter-Reiter (dort liegt sie seit Version 4; die alte Funktion suchte den
    nicht mehr existierenden Reiter 'Partner_Projekt_Zuordnung' und lieferte still {})."""
    wb = _wb(path)
    if sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        pos = _finde_zelle(ws, 'Partner (Autolog)')
        if pos is not None:
            result = {}
            for row in ws.iter_rows(min_row=pos[0] + 1, min_col=pos[1], max_col=pos[1] + 1,
                                    values_only=True):
                if row[0] is not None and row[1] not in (None, '', 0):
                    result[row[0]] = row[1]
            return result
    if 'Partner_Projekt_Zuordnung' in wb.sheetnames:   # sehr alte Dateien (Version 3)
        ws = wb['Partner_Projekt_Zuordnung']
        pos = _finde_zelle(ws, 'Partner (Autolog)') or (4, 1)
        return {r[0]: r[1] for r in ws.iter_rows(min_row=pos[0] + 1, max_col=2, values_only=True)
                if r[0] is not None and r[1] not in (None, '', 0)}
    raise ValueError('Partner-Zuordnung in der Vorlage nicht gefunden (weder im Parameter-Reiter '
                     'noch als eigener Reiter)')


def load_stammliste_from_workbook(path):
    """Liest die im Parameter-Reiter gepflegte Projekt-Stammliste (inkl. grün
    nachgetragener Projekte). Rückgabe: {Projekt: {'firma', 'status'}}."""
    wb = _wb(path)
    ws = wb['Parameter']
    pos = _finde_zelle(ws, 'Projekt', rechts='Firma')
    if pos is None:
        raise ValueError('Projekt-Stammliste im Parameter-Reiter nicht gefunden')
    out = {}
    for row in ws.iter_rows(min_row=pos[0] + 1, min_col=pos[1], max_col=pos[1] + 2, values_only=True):
        proj, firma, status = row
        if not proj or proj == 'Unberücksichtigt' or firma == 'Ignoriert / kein Projekt':
            continue
        if isinstance(firma, str) and '(intern, nicht projektbezogen)' in firma:
            continue
        out[proj] = {'firma': firma or 'TBD', 'status': status or 'TBD'}
    return out


# ---------------------------------------------------------------- Version 6 ---
VERSION_FELDER = [('Version', 'version'), ('Vorgänger-Version', 'vorgaenger'),
                  ('Berichtszeitraum', 'zeitraum'), ('Datenstand bis', 'datenstand_bis'),
                  ('Erstellt am', 'erstellt_am'), ('Skill-Version', 'skill_version'),
                  ('Freigegeben am', 'freigegeben_am'), ('Freigegeben von', 'freigegeben_von')]


class VorlageFehler(Exception):
    """Die gelieferte Vorlage darf NICHT für die Fortführung verwendet werden.
    Claude muss stoppen und bei der Nutzerin nachfragen (nicht still weiterrechnen)."""


def _versionsnummer(v):
    if v is None:
        return None
    m = re.search(r'(\d+)', str(v))
    return int(m.group(1)) if m else None


def versionstext(n):
    return f'v{int(n):02d}'


def dateiname_fuer_version(period_label, version, praefix='Projektuebersicht'):
    """z.B. Projektuebersicht_2026-11_v02.xlsx"""
    return f'{praefix}_{period_label}_{versionstext(_versionsnummer(version))}.xlsx'


def lese_berichtsversion(path):
    """Liest den Versionsblock aus dem Parameter-Reiter. Dateien vor Version 6
    haben keinen Block -> {'legacy': True}."""
    wb = _wb(path)
    if 'Parameter' not in wb.sheetnames:
        raise VorlageFehler('Datei hat keinen Parameter-Reiter - ist das wirklich ein Projektbericht?')
    ws = wb['Parameter']
    pos = _finde_zelle(ws, 'Berichtsversion')
    if pos is None:
        return {'legacy': True, 'version': None}
    meta = {'legacy': False}
    labels = dict(VERSION_FELDER)
    for r in range(pos[0] + 1, pos[0] + 1 + len(VERSION_FELDER) + 2):
        lab = ws.cell(row=r, column=pos[1]).value
        if lab in labels:
            meta[labels[lab]] = ws.cell(row=r, column=pos[1] + 1).value
    meta['version_nr'] = _versionsnummer(meta.get('version'))
    db = meta.get('datenstand_bis')
    if isinstance(db, str):
        db = datetime.strptime(db.strip(), '%d.%m.%Y')
    if db is not None:
        db = pd.Timestamp(db).normalize() + pd.Timedelta(hours=23, minutes=59, seconds=59)
    meta['datenstand_bis'] = db
    return meta


def pruefe_vorlage(path, erwartete_version):
    """Versionsregel (gegen S1). Stoppt mit VorlageFehler, wenn
    - die Datei keinen Versionsstempel hat (vor Skill 6 -> Neuaufbau nötig),
    - Version im Dateinamen und im Parameter-Reiter nicht übereinstimmen,
    - die Version älter (oder neuer) ist als die von der Nutzerin genannte
      zuletzt freigegebene Version,
    - kein Freigabevermerk (Freigegeben am/von) eingetragen ist.
    Rückgabe: Versions-Metadaten der Vorlage."""
    import os
    erwartet = _versionsnummer(erwartete_version)
    if erwartet is None:
        raise VorlageFehler('Keine zuletzt freigegebene Version angegeben - bitte bei der Nutzerin erfragen.')
    meta = lese_berichtsversion(path)
    name = os.path.basename(str(path))
    if meta['legacy']:
        raise VorlageFehler(f'{name}: kein Versionsstempel (Datei vor Skill-Version 6). '
                            'Fortführung nicht zulässig - zuerst Neuaufbau (Basis) erstellen.')
    m = re.search(r'_v(\d+)\.xlsx$', name, flags=re.I)
    if not m or int(m.group(1)) != meta['version_nr']:
        raise VorlageFehler(f'{name}: Version im Dateinamen passt nicht zur Version im Parameter-Reiter '
                            f'({meta.get("version")}). Datei wurde evtl. umbenannt - bitte klären.')
    if meta['version_nr'] < erwartet:
        raise VorlageFehler(f'{name} ist {versionstext(meta["version_nr"])} und damit ÄLTER als die zuletzt '
                            f'freigegebene {versionstext(erwartet)}. Gestoppt - bitte die richtige Datei hochladen.')
    if meta['version_nr'] > erwartet:
        raise VorlageFehler(f'{name} ist {versionstext(meta["version_nr"])} und damit NEUER als die genannte '
                            f'{versionstext(erwartet)}. Gestoppt - bitte bestätigen, welche Version freigegeben ist.')
    if not meta.get('freigegeben_am') or not meta.get('freigegeben_von'):
        raise VorlageFehler(f'{name}: kein Freigabevermerk (Parameter-Reiter, "Freigegeben am/von"). '
                            'Nur freigegebene Versionen dürfen fortgeführt werden.')
    if meta.get('datenstand_bis') is None:
        raise VorlageFehler(f'{name}: "Datenstand bis" fehlt im Versionsblock.')
    return meta


def waehle_vorlage(kandidaten, erwartete_version):
    """Mehrere hochgeladene/gefundene Dateien: genau EINE muss die Versionsregel
    erfüllen, sonst Stopp mit Liste der Gründe."""
    ok, gruende = [], []
    for k in kandidaten:
        try:
            pruefe_vorlage(k, erwartete_version)
            ok.append(k)
        except VorlageFehler as e:
            gruende.append(str(e))
    if len(ok) != 1:
        raise VorlageFehler(f'{len(ok)} passende Vorlagen gefunden (erwartet: genau 1). ' + ' | '.join(gruende))
    return ok[0]


def _parse_dt(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return pd.NaT
    if isinstance(v, datetime):
        return pd.Timestamp(v)
    return pd.to_datetime(str(v).strip(), format='%d.%m.%Y %H:%M', errors='coerce')


def _sheet_records(ws):
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    kopf = [h for h in rows[0]]
    return [dict(zip(kopf, r)) for r in rows[1:] if any(v is not None for v in r)]


def load_rohdaten_from_workbook(path, config):
    """Liest Rohdaten_Kalender und Rohdaten_Fahrten einer Vorversion (ab Version 5)
    zurück in DataFrames - inkl. der Spalten 'Manuelle Projekt-Korrektur' (-> 'Korrektur').
    Liest nur WERT-Zellen (automatisch erkanntes Projekt, Korrektur, Dauer, Satz),
    nie Formel-Ergebnisse - funktioniert daher auch, wenn die Datei nie in Excel
    geöffnet wurde."""
    wb = _wb(path)
    ganztag = {p for p in config.get('ganztagespauschale', {}) if not p.startswith('_')}
    cal_rows = []
    for rec in _sheet_records(wb['Rohdaten_Kalender']):
        start, ende = _parse_dt(rec.get('Start')), _parse_dt(rec.get('Ende'))
        if pd.isna(start):
            continue
        proj = rec.get('Projekt (automatisch erkannt, intern)') or None
        ist_p = rec.get('Ist_Pauschale') == 'JA'
        mehrt = (ende - start) > timedelta(hours=20)
        dauer = rec.get('Dauer_h')
        kosten = rec.get('Kosten_Zeit_EUR')
        cal_rows.append({
            'Mitarbeiter': rec.get('Mitarbeiter'), 'Kalendertyp': rec.get('Kalendertyp'),
            'Betreff': rec.get('Betreff'), 'Start': start, 'Ende': ende, 'Ort': None,
            'Projekt': proj, 'Aufgabe': rec.get('Aufgabe'), 'Hauptaufgabe': rec.get('Hauptaufgabe'),
            'Dauer_h': float(dauer) if dauer is not None else 0.0,
            'Dauer_h_roh': (ende - start).total_seconds() / 3600.0,
            'Mehrtaegig': mehrt, 'Jahr': start.year, 'Ist_Urlaub': False, 'Ist_Pauschale': ist_p,
            'Ist_Ganztagespauschale': bool(mehrt and proj in ganztag),
            'Stundensatz_EUR': rec.get('Stundensatz_EUR'),
            'Kosten_Zeit_EUR': kosten if isinstance(kosten, (int, float)) else None,
            'Firma': _projekt_firma(proj, config) if proj else '',
            'Korrektur': rec.get('Manuelle Projekt-Korrektur') or None,
            'Zuordnung_Grund': rec.get('Zuordnung_Grund') or '',
            'Unsicher': str(rec.get('Prüfen') or '').startswith('JA'),
            'Quelle': rec.get('Quelle') or 'Vorversion',
        })
    cal = pd.DataFrame(cal_rows)
    if len(cal):
        fehlend = cal['Kosten_Zeit_EUR'].isna()
        cal.loc[fehlend, 'Kosten_Zeit_EUR'] = cal[fehlend].apply(lambda r: _kosten_zeit_zeile(r, config), axis=1)
    trip_rows = []
    for rec in _sheet_records(wb['Rohdaten_Fahrten']):
        start, ende = _parse_dt(rec.get('Start')), _parse_dt(rec.get('Ende'))
        if pd.isna(start):
            continue
        kal = rec.get('Projekt (Kalender-Match, intern)') or None
        trip_rows.append({
            'Fahrer': rec.get('Mitarbeiter'), 'Start': start, 'Ende': ende, 'Jahr': start.year,
            'Distanz (km)': rec.get('Distanz_km'), 'KmSatz_EUR': rec.get('KmSatz_EUR'),
            'Start-Adresse': rec.get('Start-Adresse'), 'End-Adresse': rec.get('End-Adresse'),
            'Partner': rec.get('Partner (Autolog)'), 'Zweck': rec.get('Zweck'),
            'Projekt_Kalender': kal, 'Projekt': kal,
            'Korrektur': rec.get('Manuelle Projekt-Korrektur') or None,
            'Zuordnung_Grund': rec.get('Zuordnung_Grund') or (f'Zeitfenster-Match ({kal})' if kal else ''),
            'Unsicher': str(rec.get('Prüfen') or '').startswith('JA'),
            'Quelle': rec.get('Quelle') or 'Vorversion',
        })
    trips = pd.DataFrame(trip_rows)
    return cal, trips


def lade_vorlage(path, config):
    """Alles, was aus der Vorversion übernommen werden muss, in EINEM Aufruf."""
    wb = _wb(path)
    cal, trips = load_rohdaten_from_workbook(wb, config)
    return {
        'meta': lese_berichtsversion(wb),
        'kalender': cal, 'fahrten': trips,
        'zusatzkosten': load_zusatzkosten_from_workbook(wb),
        'manuelle_zeitbuchungen': load_manuelle_zeitbuchungen_from_workbook(wb),
        'partner_zuordnung': load_partner_zuordnung_from_workbook(wb),
        'stammliste': load_stammliste_from_workbook(wb),
    }


# ==========================================================================
# Excel-Report bauen (Version 3: Dashboard mit SUMIFS, Hauptaufgabe/Monat,
# Partner-Zuordnung, Management-Summary, Monatstrend, Auslastung)
# ==========================================================================
def build_excel_workbook(calendar_df, trips_df, config, period_label, output_path,
                          zusatzkosten_vorbelegt=None, manuelle_zeitbuchungen_vorbelegt=None,
                          partner_zuordnung_vorbelegt=None, version_info=None):
    """Baut die komplette Mehrjahres-Ausgabe-Excel (Version 3).

    calendar_df: durch compute_kalender_kosten() gelaufen (inkl. Wochenpauschale-Zeilen).
    trips_df: durch match_trips_to_calendar() -> apply_partner_zuordnung() ->
              compute_fahrten_kosten() gelaufen (ALLE Fahrten, inkl. weiterhin
              unzugeordneter - der Split in zugeordnet/nicht zugeordnet passiert
              hier intern anhand der Spalte 'Projekt').
    partner_zuordnung_vorbelegt: dict Partner -> Projekt/'Unberücksichtigt', wird
              mit config['partner_projekt_zuordnung'] zusammengeführt (Vorversion
              hat Vorrang, falls vorhanden).
    version_info: dict (version, vorgaenger, datenstand_bis, zeitraum) für den
              Versionsblock im Parameter-Reiter (Version 6, Versionsregel gegen S1).
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
                f'wird separat ausgewiesen. Blau hinterlegt = hier anpassbar. Stundensätze/km-Sätze nur '
                f'zur Info - Änderung über die Config + neuen Bericht-Lauf (Kosten werden je Zeile zum Datum berechnet).')
    ws['A2'].font = sub_font
    ws.append([])
    # Version 6: keine Soll-Arbeitszeit mehr (Auslastung entfernt, Datenschutz).
    ws.append(['Mitarbeiter', 'Kürzel', 'Gültig ab', 'Stundensatz (€, netto)'])
    style_header_row(ws, 4, 4)
    r = 5
    for ma in mitarbeiter_liste:
        info = config['mitarbeiter_satzhistorie'][ma]
        for satz in info['saetze']:
            ws.append([ma, info['kuerzel'], satz['gueltig_ab'], satz['stundensatz_eur']])
            for c in range(1, 5):
                ws.cell(row=r, column=c).font = normal
                ws.cell(row=r, column=c).border = border
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
        c2.font = normal
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
            c2.font = normal
            r += 1
    autosize(ws, [30, 10, 14, 18, 3])

    # ---------------- Projekt-Stammliste (in Parameter integriert, live editierbar) ----------------
    stamm = config.get('projekt_stammliste', {})
    stamm = {k: v for k, v in stamm.items() if not k.startswith('_') and isinstance(v, dict)}
    wp_cfg = config.get('wochenpauschale', {})
    ws.cell(row=3, column=6,
            value='Blau hinterlegt = hier kannst du Werte anpassen. Grün hinterlegt = hier neue Projekte eintragen.').font = sub_font
    ws.cell(row=4, column=6, value='Projekt-Stammliste (hier editieren, wirkt überall live)').font = bold
    ws.cell(row=5, column=6, value='Projekt')
    ws.cell(row=5, column=7, value='Firma')
    ws.cell(row=5, column=8, value='Status')
    style_header_row(ws, 5, 0)
    for c in (6, 7, 8):
        cell = ws.cell(row=5, column=c)
        cell.fill = hdr_fill; cell.font = hdr_font; cell.border = border
    stamm_start = 6

    # Fixzeilen: "Unberücksichtigt" (fuer Dropdowns) und die Wochenpauschale
    ws.cell(row=stamm_start, column=6, value='Unberücksichtigt').font = normal
    ws.cell(row=stamm_start, column=7, value='-').font = normal
    ws.cell(row=stamm_start, column=8, value='-').font = normal
    wp_bez_name = wp_cfg.get('bezeichnung')
    ws.cell(row=stamm_start + 1, column=6, value=wp_bez_name).font = normal
    ws.cell(row=stamm_start + 1, column=7, value=wp_cfg.get('firma', 'TBD') + ' (intern, nicht projektbezogen)').font = normal
    ws.cell(row=stamm_start + 1, column=8, value='laufend').font = normal
    for row in (stamm_start, stamm_start + 1):
        for c in (6, 7, 8):
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
        ws.cell(row=row, column=6, value=proj).font = normal
        ws.cell(row=row, column=6).fill = green_fill
        f_cell = ws.cell(row=row, column=7, value=meta.get('firma', 'TBD'))
        f_cell.font = normal; f_cell.fill = blue_fill
        s_cell = ws.cell(row=row, column=8, value=meta.get('status', 'TBD'))
        s_cell.font = normal; s_cell.fill = blue_fill
        for c in (6, 7, 8):
            ws.cell(row=row, column=c).border = border
    stamm_last = echte_projekte_start + max(len(alle_projekte_fuer_stamm) - 1, 0)

    # Grüne Vorrats-Zeilen zum Ergänzen neuer Projekte
    NEUE_PROJEKTE_PUFFER = 20
    neue_start = stamm_last + 1
    for i in range(NEUE_PROJEKTE_PUFFER):
        row = neue_start + i
        p_cell = ws.cell(row=row, column=6, value=None)
        p_cell.fill = green_fill; p_cell.border = border
        f_cell = ws.cell(row=row, column=7, value=None)
        f_cell.fill = blue_fill; f_cell.border = border
        s_cell = ws.cell(row=row, column=8, value=None)
        s_cell.fill = blue_fill; s_cell.border = border
    stamm_last_mit_puffer = neue_start + NEUE_PROJEKTE_PUFFER - 1

    ignorierte_in_daten = sorted(set(calendar_df[calendar_df['Projekt'].notna()]['Projekt'].unique()) &
                                   ignore_names_set)
    for i, proj in enumerate(ignorierte_in_daten):
        row = stamm_last_mit_puffer + 1 + i
        ws.cell(row=row, column=6, value=proj).font = normal
        ws.cell(row=row, column=7, value='Ignoriert / kein Projekt').font = normal
        ws.cell(row=row, column=8, value='-').font = normal
        for c in (6, 7, 8):
            ws.cell(row=row, column=c).border = border
    stamm_last_mit_ignoriert = stamm_last_mit_puffer + len(ignorierte_in_daten)

    dv_firma = DataValidation(type="list", formula1='"Neininger GmbH,TransCare"', allow_blank=True)
    dv_status = DataValidation(type="list", formula1='"aktiv,beendet"', allow_blank=True)
    ws.add_data_validation(dv_firma); ws.add_data_validation(dv_status)
    dv_firma.add(f'G{echte_projekte_start}:G{stamm_last_mit_puffer}')
    dv_status.add(f'H{echte_projekte_start}:H{stamm_last_mit_puffer}')
    ws.auto_filter.ref = f"F5:H{stamm_last_mit_ignoriert}"
    ws.column_dimensions['F'].width = 30
    ws.column_dimensions['G'].width = 16
    ws.column_dimensions['H'].width = 12

    # ---------------- Partner-Zuordnung (in Parameter integriert, live editierbar) ----------------
    ws.cell(row=4, column=10, value='Partner → Projekt-Zuordnung (Autolog)').font = bold
    ws.cell(row=5, column=10, value='Partner (Autolog)')
    ws.cell(row=5, column=11, value='Zuordnung')
    for c in (10, 11):
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
        ws.cell(row=row, column=10, value=partner).font = normal
        z_cell = ws.cell(row=row, column=11, value=merged_zuordnung.get(partner, ''))
        z_cell.font = normal; z_cell.fill = blue_fill
        for c in (10, 11):
            ws.cell(row=row, column=c).border = border
    pz_last_padded = max(pz_last, pz_start + 50)
    for row in range(pz_last + 1, pz_last_padded + 1):
        ws.cell(row=row, column=11).fill = blue_fill
        ws.cell(row=row, column=11).border = border
        ws.cell(row=row, column=10).border = border
    dv_partner = DataValidation(
        type="list", formula1=f'=Parameter!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_partner)
    dv_partner.add(f'K{pz_start}:K{pz_last_padded}')
    ws.column_dimensions['J'].width = 26
    ws.column_dimensions['K'].width = 30
    ws.cell(row=pz_last_padded + 2, column=10,
            value=('Hinweis: Änderungen hier wirken sich SOFORT auf "Rohdaten_Fahrten" (Spalte Projekt/'
                   'Firma) und damit auch auf Übersicht/Dashboard aus - kein erneuter Bericht-Lauf nötig.')
            ).font = sub_font

    # ---------------- Versionsblock (Version 6, Versionsregel gegen S1) ----------------
    vi = dict(version_info or {})
    ws.cell(row=4, column=13, value='Berichtsversion').font = bold
    ws.cell(row=4, column=13).fill = hdr_fill
    ws.cell(row=4, column=13).font = hdr_font
    ws.cell(row=4, column=14).fill = hdr_fill
    db = vi.get('datenstand_bis')
    werte = {
        'version': versionstext(_versionsnummer(vi['version'])) if vi.get('version') else 'ohne',
        'vorgaenger': (versionstext(_versionsnummer(vi['vorgaenger'])) if vi.get('vorgaenger')
                       else vi.get('vorgaenger_text', '- (Neuaufbau)')),
        'zeitraum': vi.get('zeitraum', period_label),
        'datenstand_bis': pd.Timestamp(db).strftime('%d.%m.%Y') if db is not None else '',
        'erstellt_am': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'skill_version': SKILL_VERSION,
        'freigegeben_am': None, 'freigegeben_von': None,
    }
    for k_, (lab, key) in enumerate(VERSION_FELDER):
        rr = 5 + k_
        ws.cell(row=rr, column=13, value=lab).font = normal
        c_ = ws.cell(row=rr, column=14, value=werte[key])
        c_.font = normal
        for cc in (13, 14):
            ws.cell(row=rr, column=cc).border = border
        if key in ('freigegeben_am', 'freigegeben_von'):
            c_.fill = blue_fill
    ws.cell(row=5 + len(VERSION_FELDER), column=13,
            value=('Freigabe: nach Prüfung durch die GF hier Datum + Name eintragen und speichern. '
                   'Nur freigegebene Versionen dürfen fortgeführt werden.')).font = sub_font
    ws.column_dimensions['L'].width = 3
    ws.column_dimensions['M'].width = 20
    ws.column_dimensions['N'].width = 22

    # Referenz-Strings für spaetere Formeln merken
    stamm_range = f"Parameter!$F${stamm_start}:$H${stamm_last_mit_ignoriert}"
    partner_range = f"Parameter!$J${pz_start}:$K${pz_last_padded}"

    sonderkalk_alle = [p_ for p_, c_ in config.get('sonderkalkulationen', {}).items()
                       if not p_.startswith('_') and isinstance(c_, dict)]
    fahrt_ohne_kosten = [p_ for p_ in sonderkalk_alle
                         if config['sonderkalkulationen'][p_].get('fahrten_kostentechnisch_ausschliessen')]

    def _or_gleich(zelle, namen):
        if not namen:
            return 'FALSE'
        return 'OR(' + ','.join(f'{zelle}="{n_}"' for n_ in namen) + ')'

    # ---------------- Rohdaten_Kalender ----------------
    # Spalten A-R wie Version 5 (Formeln anderer Reiter hängen an den Buchstaben!),
    # S-V neu in Version 6.
    ws = wb.create_sheet('Rohdaten_Kalender')
    ws.freeze_panes = 'A2'
    cols = ['Jahr', 'Monat', 'Mitarbeiter', 'Kalendertyp', 'Projekt', 'Firma', 'Hauptaufgabe',
            'Datum', 'Start', 'Ende', 'Dauer_h', 'Stundensatz_EUR', 'Kosten_Zeit_EUR', 'Aufgabe',
            'Mehrtaegig_Blocker', 'Ist_Pauschale', 'Manuelle Projekt-Korrektur',
            'Projekt (automatisch erkannt, intern)', 'Zuordnung_Grund', 'Prüfen', 'Betreff', 'Quelle']
    ws.append(cols)
    style_header_row(ws, 1, len(cols))
    cal_all_rows = calendar_df.copy()
    for col_, dflt in (('Korrektur', None), ('Zuordnung_Grund', ''), ('Unsicher', False),
                       ('Quelle', 'neu'), ('Betreff', None)):
        if col_ not in cal_all_rows.columns:
            cal_all_rows[col_] = dflt
    cal_all_rows['Monat'] = cal_all_rows['Start'].dt.strftime('%Y-%m')
    wp_bez = wp_cfg.get('bezeichnung')
    cal_xlrow = {}
    for i, (idx_, r_) in enumerate(cal_all_rows.sort_values(['Jahr', 'Start'], kind='stable').iterrows()):
        row = i + 2
        cal_xlrow[idx_] = row
        auto_projekt = r_['Projekt'] if pd.notna(r_['Projekt']) else ''
        korr = r_['Korrektur'] if isinstance(r_['Korrektur'], str) and r_['Korrektur'] else None
        unsicher = bool(r_['Unsicher']) and not korr
        ws.append([r_['Jahr'], r_['Monat'], r_['Mitarbeiter'], r_['Kalendertyp'], None, None,
                    r_['Hauptaufgabe'], r_['Start'].strftime('%d.%m.%Y'), r_['Start'].strftime('%d.%m.%Y %H:%M'),
                    r_['Ende'].strftime('%d.%m.%Y %H:%M'), float(r_['Dauer_h']), r_['Stundensatz_EUR'],
                    None, r_['Aufgabe'],
                    'JA - Klärung nötig' if (r_['Mehrtaegig'] and not r_['Ist_Pauschale']
                                              and not r_.get('Ist_Ganztagespauschale', False)) else '',
                    'JA' if r_['Ist_Pauschale'] else '', korr, auto_projekt,
                    r_['Zuordnung_Grund'] or '', 'JA - bitte prüfen' if unsicher else '',
                    r_['Betreff'] if isinstance(r_['Betreff'], str) else None, r_['Quelle']])
        ws.cell(row=row, column=5,
                value=(f'=IF(Q{row}<>"",IF(Q{row}="Unberücksichtigt","",Q{row}),IF(R{row}="","",R{row}))'))
        ws.cell(row=row, column=6,
                value=f'=IF(E{row}="","",IFERROR(VLOOKUP(E{row},{stamm_range},2,FALSE),"TBD"))')
        # Version 6: Kosten live je Zeile (Korrektur wirkt jetzt auch auf die Kosten)
        ws.cell(row=row, column=13,
                value=(f'=IF(OR(E{row}="",O{row}<>"",{_or_gleich(f"E{row}", sonderkalk_alle)}),0,'
                       f'ROUND(K{row}*N(L{row}),2))'))
        ws.cell(row=row, column=17).fill = blue_fill
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = normal
            cell.border = border
        if row[14].value or row[19].value:
            for cell in row:
                cell.fill = warn_fill
        row[16].fill = blue_fill
        row[10].number_format = '0.00'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    autosize(ws, [8, 10, 20, 12, 24, 22, 32, 12, 16, 16, 9, 12, 12, 40, 18, 12, 26, 24, 50, 16, 40, 14])
    ws.freeze_panes = 'A2'
    dv_korrektur_kalender = DataValidation(
        type="list", formula1=f'=Parameter!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_korrektur_kalender)
    dv_korrektur_kalender.add(f'Q2:Q{max(ws.max_row, 2)}')
    n_cal_rows = max(ws.max_row, 2)

    # ---------------- Rohdaten_Fahrten ----------------
    ws = wb.create_sheet('Rohdaten_Fahrten')
    cols = ['Jahr', 'Monat', 'Mitarbeiter', 'Projekt', 'Firma', 'Herkunft', 'Datum', 'Start', 'Ende',
            'Distanz_km', 'Dauer_h', 'KmSatz_EUR', 'Kosten_Fahrt_EUR', 'Start-Adresse', 'End-Adresse',
            'Partner (Autolog)', 'Zweck', 'Projekt (Kalender-Match, intern)', 'Manuelle Projekt-Korrektur',
            'Zuordnung_Grund', 'Prüfen', 'Quelle']
    ws.append(cols)
    style_header_row(ws, 1, len(cols))
    tdf = trips_df.copy()
    if 'Projekt_Kalender' not in tdf.columns:
        tdf['Projekt_Kalender'] = tdf['Projekt']
    for col_, dflt in (('Korrektur', None), ('Zuordnung_Grund', ''), ('Unsicher', False), ('Quelle', 'neu')):
        if col_ not in tdf.columns:
            tdf[col_] = dflt
    tdf['Monat'] = tdf['Start'].dt.strftime('%Y-%m')
    trip_xlrow = {}
    for i, (idx_, r_) in enumerate(tdf.sort_values(['Jahr', 'Start'], kind='stable').iterrows()):
        row = i + 2
        trip_xlrow[idx_] = row
        dauer_h = round((r_['Ende'] - r_['Start']).total_seconds() / 3600.0, 2)
        kal_match = r_['Projekt_Kalender'] if isinstance(r_['Projekt_Kalender'], str) else ''
        korr = r_['Korrektur'] if isinstance(r_['Korrektur'], str) and r_['Korrektur'] else None
        grund = r_.get('Zuordnung_Grund_wirksam') if isinstance(r_.get('Zuordnung_Grund_wirksam'), str) \
            else (r_['Zuordnung_Grund'] or '')
        unsicher = bool(r_.get('Unsicher_wirksam', r_['Unsicher'])) and not korr
        ws.append([r_['Jahr'], r_['Monat'], r_['Fahrer'], None, None, None,
                    r_['Start'].strftime('%d.%m.%Y'), r_['Start'].strftime('%d.%m.%Y %H:%M'),
                    r_['Ende'].strftime('%d.%m.%Y %H:%M'), r_['Distanz (km)'], dauer_h, r_['KmSatz_EUR'],
                    None, r_['Start-Adresse'], r_['End-Adresse'], r_['Partner'], r_['Zweck'], kal_match, korr,
                    grund, 'JA - bitte prüfen' if unsicher else '', r_['Quelle']])
        pv = f'VLOOKUP(P{row},{partner_range},2,FALSE)'
        r_gueltig = f'AND(R{row}<>"",IFERROR(VLOOKUP(R{row},{stamm_range},2,FALSE),"")<>"Ignoriert / kein Projekt")'
        # Version 6: Partner "Unberücksichtigt" gewinnt vor dem Kalender-Match (Nutzerin 2026-11-04)
        p_unber = f'IFERROR({pv}="Unberücksichtigt",FALSE)'
        partner_proj = f'IFERROR(IF(OR({pv}="Unberücksichtigt",{pv}=0),"",{pv}),"")'
        ws.cell(row=row, column=4,
                value=(f'=IF(S{row}<>"",IF(S{row}="Unberücksichtigt","",S{row}),'
                       f'IF({p_unber},"",IF({r_gueltig},R{row},{partner_proj})))'))
        ws.cell(row=row, column=5,
                value=f'=IF(D{row}="","",IFERROR(VLOOKUP(D{row},{stamm_range},2,FALSE),"TBD"))')
        ws.cell(row=row, column=6,
                value=(f'=IF(S{row}<>"","Manuelle Korrektur",IF({p_unber},"Unberücksichtigt (Partner)",'
                       f'IF({r_gueltig},"Kalender-Match",'
                       f'IF(D{row}<>"","Partner-Zuordnung",IF(R{row}<>"","Kalender-Match (ignoriertes Projekt)",'
                       f'"Nicht zugeordnet")))))'))
        ws.cell(row=row, column=13,
                value=f'=IF(D{row}="","",IF({_or_gleich(f"D{row}", fahrt_ohne_kosten)},0,J{row}*L{row}))')
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = normal
            cell.border = border
        if row[20].value:
            for cell in row:
                cell.fill = warn_fill
        row[18].fill = blue_fill
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    dv_korrektur_fahrten = DataValidation(
        type="list", formula1=f'=Parameter!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_korrektur_fahrten)
    dv_korrektur_fahrten.add(f'S2:S{max(ws.max_row, 2)}')
    autosize(ws, [8, 10, 20, 24, 30, 30, 12, 16, 16, 11, 10, 11, 14, 45, 45, 18, 20, 22, 26, 55, 16, 14])
    n_trip_rows = max(ws.max_row, 2)

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
        ws.cell(row=rr, column=7, value=f'=IF(A{rr}="","",YEAR(A{rr})&"-"&TEXT(MONTH(A{rr}),"00"))')
        for c in range(1, 8):
            ws.cell(row=rr, column=c).font = normal
            ws.cell(row=rr, column=c).border = border
        for c in (1, 2, 3, 4, 5):
            ws.cell(row=rr, column=c).fill = blue_fill
    dv_zk_projekt = DataValidation(
        type="list", formula1=f'=Parameter!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
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
        ws.cell(row=rr, column=10, value=f'=IF(A{rr}="","",YEAR(A{rr})&"-"&TEXT(MONTH(A{rr}),"00"))')
        for c in range(1, 11):
            ws.cell(row=rr, column=c).font = normal
            ws.cell(row=rr, column=c).border = border
        for c in (1, 2, 3, 4, 5, 6, 8):
            ws.cell(row=rr, column=c).fill = blue_fill
    dv_mz_projekt = DataValidation(
        type="list", formula1=f'=Parameter!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
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
        'stamm_range': stamm_range, 'cal_xlrow': cal_xlrow, 'trip_xlrow': trip_xlrow,
        'warn_fill': warn_fill, 'flag_fill': flag_fill, 'blue_fill': blue_fill, 'green_fill': green_fill,
        'version_info': vi,
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


def finalize_workbook(wb, ctx, calendar_df, trips_df, config, mitarbeiter_liste=None,
                      abgleich=None, pruef_extra=None):
    """Fügt Übersicht_<Jahr>-Sheets, Gesamtsicht, Monatstrend, interne
    Detailauswertung, Filter-Dashboard und (Version 6) die Reiter "Pruefliste" und
    "Abgleich_Vormonate" hinzu und speichert.
    abgleich: Ergebnis von vergleiche_versionen() (oder None beim ersten Aufbau
    ohne Vergleichsdatei). pruef_extra: Liste zusätzlicher Prüfpunkte (dicts)."""
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
    korr_proj = set()
    for df_ in (calendar_df, trips_df):
        if 'Korrektur' in df_.columns:
            korr_proj |= {k for k in df_['Korrektur'].dropna().unique()
                          if isinstance(k, str) and k and k != 'Unberücksichtigt'}
    projects = sorted(
        (set(cal_proj['Projekt'].unique()) | set(trips_proj['Projekt'].dropna().unique()) | korr_proj)
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
    ws['A3'] = HINWEIS_STATISCH
    ws['A3'].font = Font(name=FONT, italic=True, size=9, color='C00000')
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
    ws2['A2'] = HINWEIS_STATISCH
    ws2['A2'].font = Font(name=FONT, italic=True, size=9, color='C00000')
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
    ws3['A3'] = HINWEIS_STATISCH
    ws3['A3'].font = Font(name=FONT, italic=True, size=9, color='C00000')
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
                      f'{cal_rng("E")},"?*",{cal_rng("F")},"<>Ignoriert / kein Projekt")')
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


    # ================= Version 6: Pruefliste + Abgleich_Vormonate =================
    _build_pruefliste_sheet(wb, ctx, calendar_df, trips_df, pruef_extra or [])
    _build_abgleich_sheet(wb, ctx, abgleich)

    # ================= Reihenfolge der Reiter (nutzerfreundlich) =================
    sonderkalk_sheet_names = [ref['sheet'] for ref in ctx['sonderkalk_refs'].values()]
    front = (['Abgleich_Vormonate', 'Pruefliste', 'Filter_Dashboard'] +
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


# ==========================================================================
# Version 6: wirksame Zuordnung, Summen, Versionsvergleich
# ==========================================================================
def _ist_blocker(r):
    return bool(r['Mehrtaegig']) and not bool(r['Ist_Pauschale']) and \
        not bool(r.get('Ist_Ganztagespauschale', False))


def _wirksames_projekt_kalender(r):
    k = r.get('Korrektur')
    if isinstance(k, str) and k:
        return None if k == 'Unberücksichtigt' else k
    p = r['Projekt']
    return p if isinstance(p, str) and p else None


def _kosten_zeit_zeile(r, config):
    """Gleiche Logik wie die Excel-Formel in Rohdaten_Kalender!M (Version 6)."""
    sonderkalk = {p for p in config.get('sonderkalkulationen', {}) if not p.startswith('_')}
    proj = _wirksames_projekt_kalender(r)
    if proj is None or _ist_blocker(r) or proj in sonderkalk:
        return 0.0
    satz = r['Stundensatz_EUR']
    satz = float(satz) if satz is not None and not pd.isna(satz) else 0.0
    return round(float(r['Dauer_h']) * satz, 2)


def summen_je_monat_projekt(daten, config, statische_kosten=False):
    """Summen je Monat x Projekt (Stunden, km, Kosten netto) aus Rohdaten,
    Zusatzkosten, manuellen Zeitbuchungen und Sonderkalkulationen - mit derselben
    Logik wie die Übersichts-Reiter. daten: dict wie lade_vorlage()."""
    ignore = set(config.get('projektname_erkennung', {}).get('ignorieren', []))
    teile = []
    cal = daten['kalender']
    if len(cal):
        c = cal.copy()
        c['P'] = c.apply(_wirksames_projekt_kalender, axis=1)
        c['Monat'] = c['Start'].dt.strftime('%Y-%m')
        c['Std'] = c.apply(lambda r: 0.0 if _ist_blocker(r) else float(r['Dauer_h']), axis=1)
        if statische_kosten:
            c['K'] = c.apply(lambda r: r['Kosten_Zeit_EUR'] if pd.notna(r.get('Kosten_Zeit_EUR'))
                             else _kosten_zeit_zeile(r, config), axis=1)
        else:
            c['K'] = c.apply(lambda r: _kosten_zeit_zeile(r, config), axis=1)
        c['km'] = 0.0
        teile.append(c[['Monat', 'P', 'Std', 'K', 'km']])
        # Sonderkalkulationen (wie Excel: nach automatisch erkanntem Projekt)
        for proj, sk in config.get('sonderkalkulationen', {}).items():
            if proj.startswith('_') or not isinstance(sk, dict) or sk.get('typ') != 'tagessatz_block':
                continue
            res = calc_tagessatz_block_kosten(cal, proj, config['sonderkalkulationen'])
            for _, b in res['bloecke'].iterrows():
                teile.append(pd.DataFrame([{'Monat': b['Start'].strftime('%Y-%m'), 'P': proj, 'Std': 0.0,
                                            'K': float(b['Kosten_Block_EUR']), 'km': 0.0}]))
            for _, w in res['pauschalen'].iterrows():
                teile.append(pd.DataFrame([{'Monat': w['Woche_ab'].strftime('%Y-%m'), 'P': proj, 'Std': 0.0,
                                            'K': float(w['Anfahrtspauschale_EUR']), 'km': 0.0}]))
    tr = daten['fahrten']
    if len(tr):
        t = apply_partner_zuordnung(tr, config)
        ohne = {p for p, sk in config.get('sonderkalkulationen', {}).items()
                if not p.startswith('_') and isinstance(sk, dict) and sk.get('fahrten_kostentechnisch_ausschliessen')}
        t['P'] = t['Projekt']
        t['Monat'] = t['Start'].dt.strftime('%Y-%m')
        t['km'] = pd.to_numeric(t['Distanz (km)'], errors='coerce').fillna(0.0)
        t['K'] = t.apply(lambda r: 0.0 if r['P'] in ohne else r['km'] * float(r['KmSatz_EUR'] or 0), axis=1)
        t['Std'] = 0.0
        teile.append(t[['Monat', 'P', 'Std', 'K', 'km']])
    zk = daten.get('zusatzkosten')
    if zk is not None and len(zk):
        z = zk.copy()
        z['Monat'] = pd.to_datetime(z['Datum'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m')
        z['P'] = z['Projekt']
        z['K'] = pd.to_numeric(z['Betrag_EUR'], errors='coerce').fillna(0.0)
        z['Std'] = 0.0
        z['km'] = 0.0
        teile.append(z[['Monat', 'P', 'Std', 'K', 'km']])
    mz = daten.get('manuelle_zeitbuchungen')
    if mz is not None and len(mz):
        m = prepare_manuelle_zeitbuchungen(mz, config)
        m['Monat'] = m['Datum'].dt.strftime('%Y-%m')
        m['P'] = m['Projekt']
        m['Std'] = m['Stunden'].astype(float)
        m['K'] = m['Kosten_Zeit_EUR']
        m['km'] = 0.0
        teile.append(m[['Monat', 'P', 'Std', 'K', 'km']])
    if not teile:
        return pd.DataFrame(columns=['Monat', 'Projekt', 'Std', 'Kosten', 'km'])
    alle = pd.concat(teile, ignore_index=True)
    alle = alle[alle['P'].notna() & ~alle['P'].isin(ignore)]
    g = alle.groupby(['Monat', 'P'])[['Std', 'K', 'km']].sum().reset_index()
    return g.rename(columns={'P': 'Projekt', 'K': 'Kosten'})


def _kal_key(r):
    return (r['Mitarbeiter'], pd.Timestamp(r['Start']).floor('min'), pd.Timestamp(r['Ende']).floor('min'),
            _norm(r['Projekt'] or '') if isinstance(r['Projekt'], str) else '',
            _norm(r['Aufgabe']) if isinstance(r['Aufgabe'], str) else '')


def _kal_key_grob(r):
    return (r['Mitarbeiter'], pd.Timestamp(r['Start']).floor('min'), pd.Timestamp(r['Ende']).floor('min'))


def _trip_key(r):
    km = pd.to_numeric(r['Distanz (km)'], errors='coerce')
    return (r['Fahrer'], pd.Timestamp(r['Start']).floor('min'), pd.Timestamp(r['Ende']).floor('min'),
            round(float(km), 1) if pd.notna(km) else None)


def uebertrage_korrekturen(neu_df, alt_df, art):
    """Übernimmt 'Manuelle Projekt-Korrektur' aus der Vorversion auf passende
    Zeilen. Erst exakter Schlüssel, sonst (Mitarbeiter, Start, Ende), wenn eindeutig.
    Rückgabe: (neu_df, Liste nicht übertragbarer Korrekturen als Prüfpunkte)."""
    neu = neu_df.copy()
    if 'Korrektur' not in neu.columns:
        neu['Korrektur'] = None
    rest = []
    if alt_df is None or len(alt_df) == 0 or 'Korrektur' not in alt_df.columns:
        return neu, rest
    keyf = _kal_key if art == 'kalender' else _trip_key
    grobf = _kal_key_grob if art == 'kalender' else _trip_key
    exakt, grob = {}, {}
    for idx, r in neu.iterrows():
        exakt.setdefault(keyf(r), []).append(idx)
        grob.setdefault(grobf(r), []).append(idx)
    for _, a in alt_df[alt_df['Korrektur'].notna() & (alt_df['Korrektur'] != '')].iterrows():
        ziel = exakt.get(keyf(a)) or []
        if len(ziel) != 1:
            ziel = grob.get(grobf(a)) or []
        if len(ziel) == 1:
            neu.at[ziel[0], 'Korrektur'] = a['Korrektur']
        else:
            wer = a['Mitarbeiter'] if art == 'kalender' else a['Fahrer']
            text = (a.get('Betreff') or a.get('Aufgabe') or '') if art == 'kalender' else (a.get('Partner') or '')
            rest.append({'Bereich': 'Korrektur nicht übertragbar', 'Datum': a['Start'], 'Mitarbeiter': wer,
                         'Text': text, 'Projekt': a['Korrektur'],
                         'Grund': (f'Korrektur "{a["Korrektur"]}" aus der Vorversion passt auf '
                                   f'{len(ziel)} Zeilen der neuen Daten - bitte neu eintragen')})
    return neu, rest


def vergleiche_versionen(alt, neu, config_alt, config_neu, bis=None, alt_label='Vorversion'):
    """Prüfblatt-Logik (gegen S1): Summen je Monat x Projekt alt vs. neu für alle
    Monate bis 'bis' (Datenstand der Vorversion) + betroffene Einzelzeilen."""
    s_alt = summen_je_monat_projekt(alt, config_alt, statische_kosten=True)
    s_neu = summen_je_monat_projekt(neu, config_neu)
    if bis is not None:
        grenze = pd.Timestamp(bis).strftime('%Y-%m')
    else:
        grenze = s_alt['Monat'].max() if len(s_alt) else '0000-00'
    s_alt = s_alt[s_alt['Monat'] <= grenze]
    s_neu = s_neu[s_neu['Monat'] <= grenze]
    m = s_alt.merge(s_neu, on=['Monat', 'Projekt'], how='outer', suffixes=('_alt', '_neu')).fillna(0.0)
    tol = 0.005
    m['Abweichung'] = ((m['Std_alt'] - m['Std_neu']).abs() > tol) | \
                      ((m['Kosten_alt'] - m['Kosten_neu']).abs() > tol) | \
                      ((m['km_alt'] - m['km_neu']).abs() > tol)

    # Einzelzeilen
    zeilen = []

    def monat_ok(ts):
        return pd.notna(ts) and pd.Timestamp(ts).strftime('%Y-%m') <= grenze

    def kal_index(df):
        d = {}
        for _, r in df.iterrows():
            if monat_ok(r['Start']):
                d.setdefault(_kal_key(r), []).append(r)
        return d
    ka, kn = kal_index(alt['kalender']), kal_index(neu['kalender'])
    # Zeilen, deren Schlüssel sich nur durch das erkannte Projekt unterscheidet
    # (z.B. "sand" -> Sandformation), über (Mitarbeiter, Start, Ende) paaren
    nur_a = {k: v for k, v in ka.items() if k not in kn and len(v) == 1}
    nur_n = {k: v for k, v in kn.items() if k not in ka and len(v) == 1}
    grob_a, grob_n = {}, {}
    for k in nur_a:
        grob_a.setdefault(k[:3], []).append(k)
    for k in nur_n:
        grob_n.setdefault(k[:3], []).append(k)
    for g, ks in grob_a.items():
        if len(ks) == 1 and len(grob_n.get(g, [])) == 1:
            kn[ks[0]] = kn.pop(grob_n[g][0])
    for k in set(ka) | set(kn):
        ra, rn = ka.get(k, []), kn.get(k, [])
        for i in range(max(len(ra), len(rn))):
            a = ra[i] if i < len(ra) else None
            n = rn[i] if i < len(rn) else None
            r0 = a if a is not None else n
            pa = _wirksames_projekt_kalender(a) if a is not None else None
            pn = _wirksames_projekt_kalender(n) if n is not None else None
            sa = (0.0 if _ist_blocker(a) else float(a['Dauer_h'])) if a is not None else 0.0
            sn = (0.0 if _ist_blocker(n) else float(n['Dauer_h'])) if n is not None else 0.0
            if a is None:
                art = 'Nur in neuer Version'
            elif n is None:
                art = 'Nur in alter Version'
            elif pa != pn:
                art = 'Projekt geändert'
            elif abs(sa - sn) > tol:
                art = 'Stunden geändert'
            else:
                continue
            zeilen.append({'Bereich': 'Kalender', 'Art': art, 'Monat': r0['Start'].strftime('%Y-%m'),
                           'Datum': r0['Start'], 'Mitarbeiter': r0['Mitarbeiter'],
                           'Text': r0.get('Betreff') or r0.get('Aufgabe') or '',
                           'Projekt_alt': pa, 'Projekt_neu': pn, 'Wert_alt': sa, 'Wert_neu': sn,
                           'Einheit': 'Std.',
                           'Grund_neu': (n.get('Zuordnung_Grund') if n is not None else '') or ''})

    def trip_index(df, cfg):
        d = {}
        if len(df) == 0:
            return d
        t = apply_partner_zuordnung(df, cfg)
        for _, r in t.iterrows():
            if monat_ok(r['Start']):
                d.setdefault(_trip_key(r), []).append(r)
        return d
    ta, tn = trip_index(alt['fahrten'], config_alt), trip_index(neu['fahrten'], config_neu)
    for k in set(ta) | set(tn):
        ra, rn = ta.get(k, []), tn.get(k, [])
        for i in range(max(len(ra), len(rn))):
            a = ra[i] if i < len(ra) else None
            n = rn[i] if i < len(rn) else None
            r0 = a if a is not None else n
            pa = a['Projekt'] if a is not None else None
            pn = n['Projekt'] if n is not None else None
            pa = pa if isinstance(pa, str) else None
            pn = pn if isinstance(pn, str) else None
            if a is not None and n is not None and pa == pn:
                continue
            if pa is None and pn is None:
                continue        # nicht zugeordnet bleibt nicht zugeordnet: keine Summenwirkung
            art = 'Nur in neuer Version' if a is None else ('Nur in alter Version' if n is None else 'Projekt geändert')
            km = pd.to_numeric(r0['Distanz (km)'], errors='coerce')
            zeilen.append({'Bereich': 'Fahrt', 'Art': art, 'Monat': r0['Start'].strftime('%Y-%m'),
                           'Datum': r0['Start'], 'Mitarbeiter': r0['Fahrer'], 'Text': r0.get('Partner') or '',
                           'Projekt_alt': pa, 'Projekt_neu': pn,
                           'Wert_alt': float(km) if a is not None and pa else 0.0,
                           'Wert_neu': float(km) if n is not None and pn else 0.0, 'Einheit': 'km',
                           'Grund_neu': (n.get('Zuordnung_Grund_wirksam') if n is not None else '') or ''})

    def einfach(df, felder, bereich, einheit, wertfeld):
        out = {}
        if df is None:
            return out
        for _, r in df.iterrows():
            d = pd.to_datetime(r['Datum'], dayfirst=True, errors='coerce')
            if not monat_ok(d):
                continue
            out.setdefault(tuple(str(r[f]) for f in felder), []).append(r)
        return out
    for bereich, key, felder, wertfeld, einheit in (
            ('Zusatzkosten', 'zusatzkosten', ['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR'], 'Betrag_EUR', '€'),
            ('Manuelle Zeitbuchung', 'manuelle_zeitbuchungen', ['Datum', 'Mitarbeiter', 'Projekt', 'Stunden'],
             'Stunden', 'Std.')):
        ea, en = einfach(alt.get(key), felder, bereich, einheit, wertfeld), einfach(neu.get(key), felder, bereich, einheit, wertfeld)
        for k in set(ea) | set(en):
            na, nn = len(ea.get(k, [])), len(en.get(k, []))
            if na == nn:
                continue
            r0 = (ea.get(k) or en.get(k))[0]
            d = pd.to_datetime(r0['Datum'], dayfirst=True, errors='coerce')
            zeilen.append({'Bereich': bereich, 'Art': 'Nur in alter Version' if na > nn else 'Nur in neuer Version',
                           'Monat': d.strftime('%Y-%m'), 'Datum': d, 'Mitarbeiter': r0.get('Mitarbeiter', ''),
                           'Text': r0.get('Kostenart', '') or r0.get('Anmerkung', '') or '',
                           'Projekt_alt': r0['Projekt'] if na else None, 'Projekt_neu': r0['Projekt'] if nn else None,
                           'Wert_alt': float(r0[wertfeld] or 0) * na, 'Wert_neu': float(r0[wertfeld] or 0) * nn,
                           'Einheit': einheit, 'Grund_neu': ''})
    zdf = pd.DataFrame(zeilen)

    def begruendung(row):
        if len(zdf) == 0:
            return ''
        sel = zdf[(zdf['Monat'] == row['Monat']) &
                  ((zdf['Projekt_alt'] == row['Projekt']) | (zdf['Projekt_neu'] == row['Projekt']))]
        if len(sel) == 0:
            return 'Ursache nicht automatisch erkennbar (z.B. Sonderkalkulation) - bitte begründen'
        teile = [f'{n}× {art} ({ber})' for (art, ber), n in sel.groupby(['Art', 'Bereich']).size().items()]
        return '; '.join(teile)
    m['Begruendung'] = m.apply(lambda r: begruendung(r) if r['Abweichung'] else '', axis=1)
    m = m.sort_values(['Abweichung', 'Monat', 'Projekt'], ascending=[False, True, True]).reset_index(drop=True)
    return {'summen': m, 'zeilen': zdf, 'n_abweichungen': int(m['Abweichung'].sum()),
            'alt_label': alt_label, 'bis': bis, 'grenze_monat': grenze}


# ==========================================================================
# Version 6: Reiter Pruefliste und Abgleich_Vormonate
# ==========================================================================
def _build_pruefliste_sheet(wb, ctx, calendar_df, trips_df, extra):
    from openpyxl.styles import Font
    normal, bold, border = ctx['normal'], ctx['bold'], ctx['border']
    ws = wb.create_sheet('Pruefliste')
    ws['A1'] = 'Prüfliste – unsichere Zuordnungen und offene Punkte'
    ws['A1'].font = ctx['title_font']
    ws['A2'] = ('Gelb in den Rohdaten = unsicher. Erledigt, sobald in der Rohdaten-Zeile eine "Manuelle '
                'Projekt-Korrektur" eingetragen ist ODER hier in Spalte J ein "x" (= automatisch ist richtig) steht. '
                'Enthält nur Zeilen dieser Version (Vormonate wurden bei der letzten Freigabe geprüft).')
    ws['A2'].font = ctx['sub_font']
    hdr = ['Nr', 'Bereich', 'Datum', 'Mitarbeiter', 'Betreff / Partner', 'Projekt (automatisch)',
           'Grund', 'Rohdaten-Zeile', 'Status', 'Bestätigt (x)']
    hr = 5
    for c, h in enumerate(hdr, start=1):
        ws.cell(row=hr, column=c, value=h)
    for c in range(1, len(hdr) + 1):
        cell = ws.cell(row=hr, column=c)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = border
    eintraege = []
    neu_q = lambda q: not (isinstance(q, str) and q.startswith('Vorversion'))
    for idx, r in calendar_df.iterrows():
        k = r.get('Korrektur')
        if bool(r.get('Unsicher', False)) and neu_q(r.get('Quelle', 'neu')) and not (isinstance(k, str) and k):
            eintraege.append(('Kalender', r['Start'], r['Mitarbeiter'], r.get('Betreff') or r.get('Aufgabe'),
                              r['Projekt'] if isinstance(r['Projekt'], str) else '', r.get('Zuordnung_Grund', ''),
                              'Rohdaten_Kalender', ctx['cal_xlrow'].get(idx), 'Q'))
    for idx, r in trips_df.iterrows():
        k = r.get('Korrektur')
        uns = r.get('Unsicher_wirksam', r.get('Unsicher', False))
        if bool(uns) and neu_q(r.get('Quelle', 'neu')) and not (isinstance(k, str) and k):
            eintraege.append(('Fahrt', r['Start'], r['Fahrer'], r.get('Partner'),
                              r['Projekt'] if isinstance(r['Projekt'], str) else '',
                              r.get('Zuordnung_Grund_wirksam') or r.get('Zuordnung_Grund', ''),
                              'Rohdaten_Fahrten', ctx['trip_xlrow'].get(idx), 'S'))
    for e in extra:
        eintraege.append((e.get('Bereich'), e.get('Datum'), e.get('Mitarbeiter'), e.get('Text'),
                          e.get('Projekt') or '', e.get('Grund'), None, None, None))
    eintraege.sort(key=lambda e: (pd.Timestamp(e[1]) if pd.notna(e[1]) else pd.Timestamp.min))
    for i, (ber, dat, ma, text, proj, grund, blatt, xlrow, kcol) in enumerate(eintraege):
        row = hr + 1 + i
        ws.cell(row=row, column=1, value=i + 1)
        ws.cell(row=row, column=2, value=ber)
        ws.cell(row=row, column=3, value=pd.Timestamp(dat).strftime('%d.%m.%Y %H:%M') if pd.notna(dat) else '')
        ws.cell(row=row, column=4, value=ma)
        ws.cell(row=row, column=5, value=text if isinstance(text, str) else '')
        ws.cell(row=row, column=6, value=proj)
        ws.cell(row=row, column=7, value=grund)
        if blatt and xlrow:
            ws.cell(row=row, column=8, value=f'{blatt} Zeile {xlrow}')
            ws.cell(row=row, column=9,
                    value=f'=IF(OR({blatt}!{kcol}{xlrow}<>"",J{row}<>""),"erledigt","offen")')
        else:
            ws.cell(row=row, column=9, value=f'=IF(J{row}<>"","erledigt","offen")')
        ws.cell(row=row, column=10).fill = ctx['blue_fill']
        for c in range(1, len(hdr) + 1):
            ws.cell(row=row, column=c).font = normal
            ws.cell(row=row, column=c).border = border
            if c < 10:
                ws.cell(row=row, column=c).fill = ctx['warn_fill']
    last = hr + max(len(eintraege), 1)
    ws['A3'] = 'Offene Punkte:'
    ws['A3'].font = bold
    ws['C3'] = f'=COUNTIF(I{hr + 1}:I{last},"offen")' if eintraege else 0
    ws['C3'].font = Font(name=ctx['FONT'], bold=True, size=12, color='C00000')
    if not eintraege:
        ws.cell(row=hr + 1, column=1, value='Keine unsicheren Zuordnungen in dieser Version.').font = normal
    ws.auto_filter.ref = f'A{hr}:J{last}'
    for i, w in enumerate([5, 22, 16, 18, 40, 22, 70, 24, 10, 12], start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    ws.freeze_panes = f'A{hr + 1}'
    return ws


def _build_abgleich_sheet(wb, ctx, abgleich):
    from openpyxl.styles import Font, PatternFill
    normal, bold, border = ctx['normal'], ctx['bold'], ctx['border']
    rot = PatternFill('solid', fgColor='FFC7CE')
    gruen = PatternFill('solid', fgColor='C6EFCE')
    ws = wb.create_sheet('Abgleich_Vormonate')
    ws['A1'] = 'Abgleich Vormonate – alte gegen neue Version'
    ws['A1'].font = ctx['title_font']
    if abgleich is None:
        ws['A2'] = 'Kein Vergleich: Neuaufbau ohne Vergleichsdatei.'
        ws['A2'].font = ctx['sub_font']
        ws['A4'] = 'Kein Abgleich durchgeführt'
        ws['A4'].font = Font(name=ctx['FONT'], bold=True, size=14, color='808080')
        return ws
    bis = abgleich.get('bis')
    ws['A2'] = (f'Vergleich mit {abgleich["alt_label"]} für alle Monate bis {abgleich["grenze_monat"]}'
                f'{" (Datenstand " + pd.Timestamp(bis).strftime("%d.%m.%Y") + ")" if bis is not None else ""}. '
                'Summen je Monat und Projekt: Stunden (inkl. manueller Buchungen), km, Kosten netto (Zeit, Fahrt, '
                'Zusatzkosten, Sonderkalkulation). Stand bei Erstellung dieser Datei.')
    ws['A2'].font = ctx['sub_font']
    n = abgleich['n_abweichungen']
    if n == 0:
        ws['A4'] = 'Vormonate unverändert ✔'
        ws['A4'].font = Font(name=ctx['FONT'], bold=True, size=16, color='006100')
        ws['A4'].fill = gruen
    else:
        ws['A4'] = f'{n} Abweichungen – rot markiert, Einzelzeilen weiter unten'
        ws['A4'].font = Font(name=ctx['FONT'], bold=True, size=16, color='9C0006')
        ws['A4'].fill = rot
    hdr = ['Monat', 'Projekt', 'Std. alt', 'Std. neu', 'Diff. Std.', 'Kosten netto alt (€)',
           'Kosten netto neu (€)', 'Diff. Kosten (€)', 'km alt', 'km neu', 'Diff. km', 'Ergebnis',
           'Begründung (automatisch)', 'Entscheidung / Kommentar']
    hr = 6
    for c, h in enumerate(hdr, start=1):
        cell = ws.cell(row=hr, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = border
    m = abgleich['summen']
    for i, (_, r) in enumerate(m.iterrows()):
        row = hr + 1 + i
        vals = [r['Monat'], r['Projekt'], round(r['Std_alt'], 2), round(r['Std_neu'], 2), None,
                round(r['Kosten_alt'], 2), round(r['Kosten_neu'], 2), None,
                round(r['km_alt'], 1), round(r['km_neu'], 1), None,
                'ABWEICHUNG' if r['Abweichung'] else 'unverändert ✔', r['Begruendung'], None]
        for c, v in enumerate(vals, start=1):
            ws.cell(row=row, column=c, value=v)
        ws.cell(row=row, column=5, value=f'=D{row}-C{row}')
        ws.cell(row=row, column=8, value=f'=G{row}-F{row}')
        ws.cell(row=row, column=11, value=f'=J{row}-I{row}')
        for c in range(1, len(hdr) + 1):
            cell = ws.cell(row=row, column=c)
            cell.font = normal; cell.border = border
            if c in (6, 7, 8):
                cell.number_format = '#,##0.00 €'
            elif c in (3, 4, 5, 9, 10, 11):
                cell.number_format = '#,##0.00'
            if r['Abweichung'] and c <= 13:
                cell.fill = rot
        ws.cell(row=row, column=14).fill = ctx['blue_fill']
    z0 = hr + len(m) + 3
    ws.cell(row=z0, column=1, value='Betroffene Einzelzeilen (nur bei Abweichungen)').font = bold
    zh = ['Bereich', 'Art', 'Monat', 'Datum', 'Mitarbeiter', 'Betreff / Partner / Kostenart',
          'Projekt alt', 'Projekt neu', 'Wert alt', 'Wert neu', 'Einheit', 'Zuordnung_Grund (neu)']
    for c, h in enumerate(zh, start=1):
        cell = ws.cell(row=z0 + 1, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = border
    zdf = abgleich['zeilen']
    if len(zdf):
        zdf = zdf.sort_values(['Monat', 'Bereich', 'Datum'])
        for i, (_, r) in enumerate(zdf.iterrows()):
            row = z0 + 2 + i
            vals = [r['Bereich'], r['Art'], r['Monat'],
                    pd.Timestamp(r['Datum']).strftime('%d.%m.%Y %H:%M') if pd.notna(r['Datum']) else '',
                    r['Mitarbeiter'], r['Text'], r['Projekt_alt'] or '', r['Projekt_neu'] or '',
                    round(r['Wert_alt'], 2), round(r['Wert_neu'], 2), r['Einheit'], r['Grund_neu']]
            for c, v in enumerate(vals, start=1):
                cell = ws.cell(row=row, column=c, value=v)
                cell.font = normal; cell.border = border; cell.fill = rot
    else:
        ws.cell(row=z0 + 2, column=1, value='Keine abweichenden Einzelzeilen.').font = normal
    for i, w in enumerate([10, 26, 10, 10, 10, 16, 16, 14, 10, 10, 10, 16, 60, 30], start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    ws.freeze_panes = f'A{hr + 1}'
    return ws


# ==========================================================================
# Version 6: feste Abläufe (NICHT mehr frei improvisieren!)
# ==========================================================================
def _merge_config(config, vorlage):
    """Config + Stand aus der freigegebenen Vorlage (Partner-Zuordnung und
    Stammliste der Vorlage haben Vorrang - dort pflegt die Nutzerin live)."""
    import copy
    cfg = copy.deepcopy(config)
    hinweise = []
    if vorlage is None:
        return cfg, hinweise
    pz = cfg.setdefault('partner_projekt_zuordnung', {})
    for k, v in vorlage['partner_zuordnung'].items():
        if pz.get(k) != v:
            hinweise.append(f'Partner-Zuordnung aus Vorlage: {k} -> {v} (Config: {pz.get(k, "-")})')
        pz[k] = v
    st = cfg.setdefault('projekt_stammliste', {})
    for k, v in vorlage['stammliste'].items():
        alt = st.get(k, {})
        if not alt and (not v['firma'] or v['firma'] == 'TBD'):
            # automatisch erkannter, nie gepflegter Name (z.B. Phantom "sand") - NICHT übernehmen
            continue
        if not alt:
            hinweise.append(f'Neues Projekt aus Vorlage-Stammliste übernommen: {k} ({v["firma"]})')
        elif alt.get('firma') != v['firma'] or alt.get('status') != v['status']:
            hinweise.append(f'Stammliste aus Vorlage: {k} Firma/Status {v["firma"]}/{v["status"]} '
                            f'(Config: {alt.get("firma")}/{alt.get("status")})')
        st[k] = {**alt, 'firma': v['firma'], 'status': v['status']}
    return cfg, hinweise


def _lade_fahrten(autolog_specs, config, period_start, period_end):
    """autolog_specs: Liste {path, kennzeichen}. Fahrer kommt aus der Config."""
    zuordnung = config.get('fahrzeug_fahrer_zuordnung', {})
    zuord_norm = {re.sub(r'\s+', '', k).upper(): v for k, v in zuordnung.items() if not k.startswith('_')}
    frames = []
    for spec in autolog_specs:
        kz = spec['kennzeichen']
        fahrer = zuord_norm.get(re.sub(r'\s+', '', kz).upper())
        if fahrer is None:
            raise ValueError(f'Kennzeichen {kz} steht nicht in fahrzeug_fahrer_zuordnung - Nutzerin fragen')
        if str(fahrer).upper().startswith('IGNORIEREN'):
            continue
        frames.append(load_autolog_csv(spec['path'], kz, fahrer, period_start, period_end))
    if not frames:
        return pd.DataFrame(columns=['Fahrer', 'Start', 'Ende', 'Jahr', 'Distanz (km)', 'Partner', 'Zweck',
                                     'Start-Adresse', 'End-Adresse'])
    return pd.concat(frames, ignore_index=True)


def offene_fahrten(autolog_specs, config, period_start, period_end):
    """Fahrten, die weder 'Geschäftlich' noch 'Privat' sind (z.B. 'Offen' = in Autolog
    noch nicht klassifiziert). Sie fließen NICHT ein, kommen aber auf die Prüfliste
    (früher fielen sie still heraus)."""
    zuord = {re.sub(r'\s+', '', k).upper(): v for k, v in config.get('fahrzeug_fahrer_zuordnung', {}).items()
             if not k.startswith('_')}
    out = []
    for spec in autolog_specs:
        fahrer = zuord.get(re.sub(r'\s+', '', spec['kennzeichen']).upper())
        if fahrer is None or str(fahrer).upper().startswith('IGNORIEREN'):
            continue
        df = load_autolog_csv(spec['path'], spec['kennzeichen'], fahrer, period_start, period_end,
                              nur_geschaeftlich=False)
        for _, r in df[~df['Fahrtart'].isin(['Geschäftlich', 'Privat'])].iterrows():
            out.append({'Bereich': 'Fahrt nicht klassifiziert', 'Datum': r['Start'], 'Mitarbeiter': fahrer,
                        'Text': f"{r.get('Start-Adresse')} \u2192 {r.get('End-Adresse')} ({r['Distanz (km)']} km)",
                        'Projekt': '',
                        'Grund': (f'Fahrtart "{r["Fahrtart"]}" - fließt NICHT ein. In Autolog als geschäftlich/privat '
                                  'einstufen und neu exportieren, oder als Zusatzkosten erfassen.')})
    return out


def _match_alle(trips, cal, config):
    teile = []
    for fahrer in trips['Fahrer'].dropna().unique():
        teile.append(match_trips_to_calendar(trips[trips['Fahrer'] == fahrer], cal, fahrer, config=config))
    if not teile:
        t = trips.copy()
        t['Projekt'] = None
        t['Projekt_Kalender'] = None
        t['Zuordnung_Grund'] = ''
        t['Unsicher'] = False
        return t
    return pd.concat(teile, ignore_index=True)


def _markiere_dubletten(cal):
    """Exakt gleiche Termine (Mitarbeiter, Start, Ende, Betreff) in ZWEI
    verschiedenen Kalendern derselben Person: nicht still addieren, sondern die
    zweite Zeile als 'mögliche Dublette' markieren (Entscheidung: Nutzerin).
    Identische Zeilen aus DEMSELBEN Kalender (doppelt exportiert) werden entfernt."""
    cal = cal.drop_duplicates(subset=['Mitarbeiter', 'Kalendertyp', 'Start', 'Ende', 'Betreff']).copy()
    dup = cal.duplicated(subset=['Mitarbeiter', 'Start', 'Ende', 'Betreff'], keep='first') & cal['Projekt'].notna()
    for idx in cal[dup].index:
        g = cal.at[idx, 'Zuordnung_Grund']
        cal.at[idx, 'Zuordnung_Grund'] = (g + '; ' if g else '') + \
            'Mögliche Dublette: gleicher Termin in einem anderen Kalender derselben Person - bitte prüfen'
        cal.at[idx, 'Unsicher'] = True
    return cal


def _speichern_und_berichten(cal, trips, cfg, period_label, output_dir, version_info, zk, mz,
                            abgleich, extra):
    import os
    os.makedirs(output_dir, exist_ok=True)
    pfad = os.path.join(output_dir, dateiname_fuer_version(period_label, version_info['version']))
    if os.path.exists(pfad):
        raise FileExistsError(f'{pfad} existiert schon - Versionsnummer nicht doppelt vergeben')
    cal = cal.reset_index(drop=True)
    trips = trips.reset_index(drop=True)
    wb, ctx = build_excel_workbook(cal, trips, cfg, period_label, pfad,
                                   zusatzkosten_vorbelegt=zk, manuelle_zeitbuchungen_vorbelegt=mz,
                                   partner_zuordnung_vorbelegt=_partner_mapping(cfg),
                                   version_info=version_info)
    finalize_workbook(wb, ctx, cal, trips, cfg, abgleich=abgleich, pruef_extra=extra)
    n_unsicher = int(cal.apply(lambda r: bool(r.get('Unsicher')) and not (isinstance(r.get('Korrektur'), str)
                                                                          and r.get('Korrektur'))
                               and not str(r.get('Quelle', 'neu')).startswith('Vorversion'), axis=1).sum()) \
        if len(cal) else 0
    n_unsicher += int(trips.apply(lambda r: bool(r.get('Unsicher_wirksam', False))
                                  and not str(r.get('Quelle', 'neu')).startswith('Vorversion'), axis=1).sum()) \
        if len(trips) else 0
    return {'pfad': pfad, 'version': versionstext(version_info['version']), 'n_unsicher': n_unsicher,
            'n_extra': len(extra), 'abgleich': abgleich, 'kalender': cal, 'fahrten': trips, 'config': cfg}


def neuaufbau(calendar_specs, autolog_specs, config, period_start, period_end, period_label, output_dir,
              vergleichsdatei=None, version=1, neue_manuelle_zeitbuchungen=None, neue_zusatzkosten=None):
    """Kompletter Neuaufbau aus allen Rohdaten (z.B. 'Basis v01').
    vergleichsdatei: die zuletzt freigegebene ALTE Ausgabe (auch Version 5 ohne
    Stempel erlaubt). Daraus werden Zusatzkosten, manuelle Zeitbuchungen,
    Partner-Zuordnung, Stammliste und Korrekturen übernommen; das Prüfblatt
    vergleicht alt gegen neu für alle Monate der alten Datei."""
    import os
    alt = lade_vorlage(vergleichsdatei, config) if vergleichsdatei else None
    cfg, hinweise = _merge_config(config, alt)
    extra = [{'Bereich': 'Hinweis Übernahme', 'Datum': None, 'Mitarbeiter': '', 'Text': h, 'Projekt': '',
              'Grund': 'aus der Vergleichsdatei übernommen - bitte kurz bestätigen'} for h in hinweise]

    cal_all = load_multiple_calendars(calendar_specs, cfg, period_start, period_end)
    pausch = generate_wochenpauschale_rows(cal_all, cfg, period_start, period_end)
    cal = pd.concat([cal_all, pausch], ignore_index=True) if len(pausch) else cal_all
    cal = compute_kalender_kosten(cal, cfg)
    cal = _markiere_dubletten(cal)
    cal['Quelle'] = 'neu'
    trips = _lade_fahrten(autolog_specs, cfg, period_start, period_end)
    extra += offene_fahrten(autolog_specs, cfg, period_start, period_end)
    trips = _match_alle(trips, cal, cfg)
    trips['Quelle'] = 'neu'
    zk = alt['zusatzkosten'] if alt else pd.DataFrame(columns=['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR', 'Anmerkung'])
    mz = alt['manuelle_zeitbuchungen'] if alt else pd.DataFrame(
        columns=['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe', 'Stunden', 'Anmerkung'])
    if neue_zusatzkosten is not None and len(neue_zusatzkosten):
        zk = pd.concat([zk, neue_zusatzkosten], ignore_index=True)
    if neue_manuelle_zeitbuchungen is not None and len(neue_manuelle_zeitbuchungen):
        mz = pd.concat([mz, neue_manuelle_zeitbuchungen], ignore_index=True)
    if alt:
        cal, r1 = uebertrage_korrekturen(cal, alt['kalender'], 'kalender')
        trips, r2 = uebertrage_korrekturen(trips, alt['fahrten'], 'fahrten')
        extra += r1 + r2
    trips = apply_partner_zuordnung(trips, cfg)
    trips = compute_fahrten_kosten(trips, cfg)

    abgleich = None
    if alt:
        neu = {'kalender': cal, 'fahrten': trips, 'zusatzkosten': zk, 'manuelle_zeitbuchungen': mz}
        cfg_alt, _ = _merge_config(config, alt)
        meta = alt['meta']
        label = (f'{os.path.basename(vergleichsdatei)}'
                 + (f' ({versionstext(meta["version_nr"])})' if meta.get('version_nr') else ' (ohne Versionsstempel)'))
        abgleich = vergleiche_versionen(alt, neu, cfg_alt, cfg, bis=meta.get('datenstand_bis'), alt_label=label)
    vi = {'version': version, 'vorgaenger': None,
          'vorgaenger_text': ('- (Neuaufbau, Vergleich: ' + os.path.basename(vergleichsdatei) + ')')
          if vergleichsdatei else '- (Neuaufbau)',
          'datenstand_bis': period_end, 'zeitraum': period_label}
    return _speichern_und_berichten(cal, trips, cfg, period_label, output_dir, vi, zk, mz, abgleich, extra)


def fortfuehrung(vorlage, erwartete_version, calendar_specs, autolog_specs, config, period_end,
                 period_label, output_dir, neue_manuelle_zeitbuchungen=None, neue_zusatzkosten=None):
    """Monatliche Fortführung (gegen S1). Ablauf:
    1. pruefe_vorlage(): nur die zuletzt FREIGEGEBENE Version, sonst Stopp (VorlageFehler).
    2. Alle Zeilen der Vorlage bis 'Datenstand bis' werden EINGEFROREN übernommen
       (inkl. Korrekturen, Zusatzkosten, manuelle Buchungen, Partner, Stammliste).
    3. Aus den neuen Rohdaten kommen nur Zeilen NACH 'Datenstand bis' dazu.
       Neue Rohdaten-Zeilen in Vormonaten (Nachträge) oder in Outlook geänderte/
       gelöschte alte Termine werden NICHT still übernommen, sondern auf die Pruefliste gesetzt.
    4. Abgleich_Vormonate muss danach 'unverändert ✔' zeigen."""
    import os
    meta = pruefe_vorlage(vorlage, erwartete_version)
    bis = meta['datenstand_bis']
    period_end = pd.Timestamp(period_end)
    if period_end <= bis:
        raise VorlageFehler(f'Berichtsende {period_end:%d.%m.%Y} liegt nicht nach dem Datenstand der Vorlage '
                            f'({bis:%d.%m.%Y}) - nichts fortzuführen.')
    alt = lade_vorlage(vorlage, config)
    cfg, hinweise = _merge_config(config, alt)
    vtext = versionstext(meta['version_nr'])
    extra = []

    alt_cal = alt['kalender'].copy()
    alt_cal['Quelle'] = f'Vorversion {vtext}'
    alt_trips = alt['fahrten'].copy()
    alt_trips['Quelle'] = f'Vorversion {vtext}'

    # --- Kalender
    cal_export = load_multiple_calendars(calendar_specs, cfg, None, period_end)
    cal_export = cal_export[cal_export['Start'].notna()]
    inc = cal_export[cal_export['Start'] > bis].copy()
    vergangen = cal_export[cal_export['Start'] <= bis]
    alt_keys = {_kal_key(r) for _, r in alt_cal.iterrows()}
    for _, r in vergangen.iterrows():
        if _kal_key(r) not in alt_keys and (pd.notna(r['Projekt']) or r['Unsicher']):
            extra.append({'Bereich': 'Nachtrag Vormonat (nicht übernommen)', 'Datum': r['Start'],
                          'Mitarbeiter': r['Mitarbeiter'], 'Text': r['Betreff'], 'Projekt': r['Projekt'] or '',
                          'Grund': ('Termin steht im neuen Export, aber nicht in der freigegebenen Vorversion. '
                                    'Vormonate bleiben unverändert - falls er zählen soll: als manuelle '
                                    'Zeitbuchung im aktuellen Monat erfassen.')})
    quellen = {(sp['mitarbeiter'], sp['kalendertyp']) for sp in calendar_specs}
    min_start = cal_export.groupby(['Mitarbeiter', 'Kalendertyp'])['Start'].min().to_dict()
    neu_keys = {_kal_key(r) for _, r in vergangen.iterrows()}
    for _, a in alt_cal[~alt_cal['Ist_Pauschale'].astype(bool)].iterrows():
        q = (a['Mitarbeiter'], a['Kalendertyp'])
        if q in quellen and q in min_start and a['Start'] >= min_start[q] and _kal_key(a) not in neu_keys \
                and isinstance(a['Projekt'], str):
            extra.append({'Bereich': 'In Outlook geändert/gelöscht', 'Datum': a['Start'],
                          'Mitarbeiter': a['Mitarbeiter'], 'Text': a.get('Betreff') or a.get('Aufgabe'),
                          'Projekt': a['Projekt'],
                          'Grund': 'Termin der Vorversion fehlt im neuen Export. Vorversion bleibt gültig - bitte prüfen.'})
    pausch = generate_wochenpauschale_rows(cal_export, cfg, bis + pd.Timedelta(seconds=1), period_end)
    inc = pd.concat([inc, pausch], ignore_index=True) if len(pausch) else inc
    inc = compute_kalender_kosten(inc, cfg) if len(inc) else inc
    inc = _markiere_dubletten(inc) if len(inc) else inc
    inc['Quelle'] = 'neu'
    cal = pd.concat([alt_cal, inc], ignore_index=True)

    # --- Fahrten
    t_export = _lade_fahrten(autolog_specs, cfg, None, period_end)
    t_export = t_export[t_export['Start'].notna()].drop_duplicates(
        subset=['Fahrer', 'Start', 'Ende', 'Distanz (km)', 'Partner'])
    t_inc = t_export[t_export['Start'] > bis].copy()
    alt_tkeys = {_trip_key(r) for _, r in alt_trips.iterrows()}
    for _, r in t_export[t_export['Start'] <= bis].iterrows():
        if _trip_key(r) not in alt_tkeys:
            extra.append({'Bereich': 'Fahrt-Nachtrag Vormonat (nicht übernommen)', 'Datum': r['Start'],
                          'Mitarbeiter': r['Fahrer'], 'Text': r.get('Partner'), 'Projekt': '',
                          'Grund': 'Fahrt fehlt in der freigegebenen Vorversion - Vormonate bleiben unverändert.'})
    extra += offene_fahrten(autolog_specs, cfg, bis + pd.Timedelta(seconds=1), period_end)
    t_inc = _match_alle(t_inc, cal, cfg)
    t_inc['Quelle'] = 'neu'
    trips = pd.concat([alt_trips, t_inc], ignore_index=True)
    trips = apply_partner_zuordnung(trips, cfg)
    trips = compute_fahrten_kosten(trips, cfg)

    zk, mz = alt['zusatzkosten'], alt['manuelle_zeitbuchungen']
    if neue_zusatzkosten is not None and len(neue_zusatzkosten):
        zk = pd.concat([zk, neue_zusatzkosten], ignore_index=True)
    if neue_manuelle_zeitbuchungen is not None and len(neue_manuelle_zeitbuchungen):
        mz = pd.concat([mz, neue_manuelle_zeitbuchungen], ignore_index=True)
    # Abweichungen Config <-> freigegebene Vorlage NICHT auf die Prüfliste (sonst jeden Monat
    # dieselben Punkte); sie kommen als 'config_hinweise' zurück -> Claude schlägt vor, die
    # Config im Skill-ZIP zu aktualisieren.

    neu = {'kalender': cal, 'fahrten': trips, 'zusatzkosten': zk, 'manuelle_zeitbuchungen': mz}
    abgleich = vergleiche_versionen(alt, neu, cfg, cfg, bis=bis,
                                    alt_label=f'{os.path.basename(str(vorlage))} ({vtext})')
    vi = {'version': meta['version_nr'] + 1, 'vorgaenger': meta['version_nr'],
          'datenstand_bis': period_end, 'zeitraum': period_label}
    erg = _speichern_und_berichten(cal, trips, cfg, period_label, output_dir, vi, zk, mz, abgleich, extra)
    erg['config_hinweise'] = hinweise
    return erg
