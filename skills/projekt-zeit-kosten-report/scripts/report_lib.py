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
SKILL_VERSION = '6.2'
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

    # Version 6.2: von der Nutzerin bestätigte Stichwort-Regeln (aus Regel-Vorschlägen)
    for wort, ziel in pe.get('stichwort_regeln', {}).items():
        if str(wort).startswith('_'):
            continue
        if re.search(r'(?<!\w)' + re.escape(wort) + r'(?!\w)', betreff, flags=re.I):
            return {'projekt': ziel, 'rest': betreff, 'grund': f'Regel: Stichwort "{wort}" \u2192 {ziel}',
                    'unsicher': False}

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


def ist_eigener_urlaub(betreff, mitarbeiter, config):
    """Urlaubstermin der Kalender-Inhaberin/des -Inhabers selbst? Version 6: Urlaub
    ANDERER Personen im eigenen Kalender ("Felix Urlaub", "Heidi Urlaub" bei Marius)
    zählt nicht (Nutzerin 2026-11-05). Andere Person = Vorname eines anderen
    Mitarbeiters oder ein Name aus wochenpauschale.urlaub_fremde_namen."""
    wp = config.get('wochenpauschale', {})
    if not isinstance(betreff, str) or wp.get('urlaub_erkennung_keyword', 'urlaub') not in betreff.lower():
        return False
    eigene = str(mitarbeiter).split()[0].lower() if mitarbeiter else ''
    fremde = {m.split()[0].lower() for m in config.get('mitarbeiter_satzhistorie', {}) if not m.startswith('_')}
    fremde |= {n.lower() for n in wp.get('urlaub_fremde_namen', [])}
    fremde.discard(eigene)
    worte = set(re.findall(r'\w+', betreff.lower()))
    return not (worte & fremde)


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
    df['Ist_Urlaub'] = df['Betreff'].apply(lambda b: ist_eigener_urlaub(b, mitarbeiter, config))
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
    # eigener Urlaub im eigenen Kalender ODER ausdrücklich benannter Urlaub in einem
    # anderen Kalender (z.B. "Urlaub MN 29.03.-06.04." im Kalender der Assistenz)
    kw = cfg.get('urlaub_erkennung_keyword', 'urlaub')
    kuerzel = config.get('mitarbeiter_satzhistorie', {}).get(mitarbeiter, {}).get('kuerzel', '')
    namen = {mitarbeiter.split()[0].lower(), str(kuerzel).lower()} - {''}
    betreffe = calendar_df_all['Betreff'] if 'Betreff' in calendar_df_all.columns else \
        pd.Series([''] * len(calendar_df_all), index=calendar_df_all.index)
    benannt = betreffe.apply(
        lambda b: isinstance(b, str) and kw in b.lower() and bool(set(re.findall(r'\w+', b.lower())) & namen)
    ).astype(bool)
    urlaub_rows = calendar_df_all[
        ((calendar_df_all['Mitarbeiter'] == mitarbeiter) & (calendar_df_all['Ist_Urlaub'])) | benannt
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
    if cfg.get('bis'):   # Version 6: Pauschale endet (Nutzerin: ab September 2026 entfallen)
        period_end_ts = min(period_end_ts, pd.Timestamp(cfg['bis']) + pd.Timedelta(hours=23, minutes=59))
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
            # Version 6.1: nur unsicher, wenn ein ANDERES Projekt zeitlich fast gleich nah liegt
            # (Übergänge wie "auf dem Weg zu Niedermaier noch NicLas" sind normal - Nutzerin 2026-11-05)
            schwelle = timedelta(hours=(config or {}).get('matching', {}).get('unsicher_wenn_abstand_unter_h', 2))
            naechstes_anderes = candidates[candidates['Projekt'] != best['Projekt']]['delta'].min()
            if naechstes_anderes - best['delta'] < schwelle:
                grund += ('; ähnlich nah: ' + ', '.join(map(str, andere)) + ' - bitte prüfen')
                unsicher = True
            else:
                grund += '; weitere Projekte im Fenster (deutlich weiter weg): ' + ', '.join(map(str, andere))
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
def sonderkalk_gilt(projekt, mitarbeiter, config):
    """True, wenn die Sonderkalkulation (z.B. Tagessatz Niedermaier) für diese Zeile
    gilt. Version 6: nur für den in der Config genannten Mitarbeiter - andere
    Personen (z.B. Felix' Telefonate zu Niedermaier) werden normal mit Stundensatz
    abgerechnet (Nutzerin 2026-11-05)."""
    sk = config.get('sonderkalkulationen', {}).get(projekt) if isinstance(projekt, str) else None
    if not isinstance(sk, dict):
        return False
    return not sk.get('mitarbeiter') or sk.get('mitarbeiter') == mitarbeiter


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

    def _eff(r):
        k = r.get('Korrektur') if 'Korrektur' in r.index else None
        if isinstance(k, str) and k:
            return None if k == 'Unberücksichtigt' else k
        return r['Projekt']

    def adjust_dauer(r):
        # Version 6: wirksames Projekt (inkl. manueller Korrektur), sonst zählen von Hand
        # Frutania zugeordnete Blöcke ("M. Neininger Grafschaft") mit 0 h
        if r['Mehrtaegig'] and _eff(r) in ganztag_cfg:
            r = r.copy(); r['Projekt'] = _eff(r)
            if r['Start'].time().hour == 0 and r['Start'].time().minute == 0 and \
               r['Ende'].time().hour == 0 and r['Ende'].time().minute == 0:
                # Klassische "ganztägig"-Konvention: Ende-Datum ist exklusiv
                tage = max((r['Ende'].date() - r['Start'].date()).days, 1)
            else:
                # z.B. "08:00 Tag 1 bis 16:00 Tag 2" -> beide Kalendertage zaehlen
                tage = (r['Ende'].date() - r['Start'].date()).days + 1
            return tage * ganztag_cfg[r['Projekt']]['stunden_pro_tag']
        return r['Dauer_h']

    if 'Dauer_h_roh' in df.columns:          # erneuter Aufruf (z.B. nach Korrektur-Übernahme)
        df['Dauer_h'] = df['Dauer_h_roh'].where(df['Dauer_h_roh'].notna(), df['Dauer_h'])
    df['Dauer_h_roh'] = df['Dauer_h']
    df['Dauer_h'] = df.apply(adjust_dauer, axis=1)
    df['Ist_Ganztagespauschale'] = df.apply(lambda r: bool(r['Mehrtaegig']) and _eff(r) in ganztag_cfg, axis=1)

    def row_kosten(r):
        if pd.isna(r['Projekt']) or r['Projekt'] is None:
            return 0.0
        if sonderkalk_gilt(r['Projekt'], r['Mitarbeiter'], config):
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
        if r['Projekt'] in tb and sonderkalk_gilt(r['Projekt'], r['Mitarbeiter'], config):
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
        if zusatz and zusatz in (r['Zuordnung_Grund'] or ''):
            continue
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
        if isinstance(cfg, dict) and cfg.get('fahrten_kostentechnisch_ausschliessen') \
                and sonderkalk_gilt(r['Projekt'], r.get('Fahrer'), config):
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
    # Version 6: wirksames Projekt (inkl. manueller Korrektur), z.B. "Niedermaier Spedition ..."
    if 'Korrektur' in calendar_df.columns:
        wirksam = calendar_df['Korrektur'].where(
            calendar_df['Korrektur'].notna() & (calendar_df['Korrektur'] != ''), calendar_df['Projekt'])
    else:
        wirksam = calendar_df['Projekt']
    blocks = calendar_df[wirksam == projekt]
    if cfg.get('mitarbeiter'):
        blocks = blocks[blocks['Mitarbeiter'] == cfg['mitarbeiter']]
    blocks = blocks.sort_values('Start').copy()

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


def _stammblatt(wb):
    return wb['Stammdaten'] if 'Stammdaten' in wb.sheetnames else wb['Parameter']


def load_partner_zuordnung_from_workbook(path, sheet_name=None, start_row=None):
    """Liest die Partner->Projekt-Zuordnung. Version 6: sucht die Tabelle im
    Parameter-Reiter (dort liegt sie seit Version 4; die alte Funktion suchte den
    nicht mehr existierenden Reiter 'Partner_Projekt_Zuordnung' und lieferte still {})."""
    wb = _wb(path)
    if 'Stammdaten' in wb.sheetnames or 'Parameter' in wb.sheetnames:
        ws = _stammblatt(wb)
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
    ws = _stammblatt(wb)
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
    kandidaten = [n for n in ('Cockpit', 'Stammdaten', 'Parameter') if n in wb.sheetnames]
    if not kandidaten:
        raise VorlageFehler('Datei hat weder Cockpit- noch Parameter-Reiter - ist das wirklich ein Projektbericht?')
    ws, pos = None, None
    for n in kandidaten:
        pos = _finde_zelle(wb[n], 'Berichtsversion')
        if pos is not None:
            ws = wb[n]
            break
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
        raise VorlageFehler(f'{name}: kein Freigabevermerk (Cockpit, "Freigegeben am/von"). '
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
    entsch = lade_entscheidungen(wb)

    def _korr(rec):
        id_ = rec.get('ID')
        if entsch is not None:
            e = entsch.get(id_, {}) if id_ else {}
            roh = e.get('Entscheidung')
            return (None if roh in (None, '', PASST) else roh), roh, e.get('Kommentar'), e.get('Quelle')
        roh = rec.get('Manuelle Projekt-Korrektur') or rec.get('Entscheidung (aus Prüfen & Korrigieren)') or None
        return roh, roh, None, None
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
            'Ist_Ganztagespauschale': (bool(mehrt) and not ist_p and not rec.get('Mehrtaegig_Blocker'))
            if 'Mehrtaegig_Blocker' in rec else bool(mehrt and proj in ganztag),
            'Stundensatz_EUR': rec.get('Stundensatz_EUR'),
            'Kosten_Zeit_EUR': kosten if isinstance(kosten, (int, float)) else None,
            'Firma': _projekt_firma(proj, config) if proj else '',
            'Zuordnung_Grund': rec.get('Zuordnung_Grund') or '',
            'Unsicher': str(rec.get('Prüfen') or '').startswith('JA'),
            'Quelle': rec.get('Quelle') or 'Vorversion', 'ID': rec.get('ID'),
        })
        k_, roh_, kom_, q_ = _korr(rec)
        cal_rows[-1].update({'Korrektur': k_, 'Entscheidung': roh_, 'Entscheidung_Kommentar': kom_,
                             'Entscheidung_Quelle': q_})
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
            'Zuordnung_Grund': rec.get('Zuordnung_Grund') or (f'Zeitfenster-Match ({kal})' if kal else ''),
            'Unsicher': str(rec.get('Prüfen') or '').startswith('JA'),
            'Quelle': rec.get('Quelle') or 'Vorversion', 'ID': rec.get('ID'),
        })
        k_, roh_, kom_, q_ = _korr(rec)
        trip_rows[-1].update({'Korrektur': k_, 'Entscheidung': roh_, 'Entscheidung_Kommentar': kom_,
                              'Entscheidung_Quelle': q_})
    trips = pd.DataFrame(trip_rows)
    return cal, trips


def lade_entscheidungen(wb):
    """Version 6.2: Entscheidungen aus der Liste Pruefen_Korrigieren (ID -> Entscheidung,
    Kommentar, Quelle). None, wenn die Datei die Liste noch nicht hat (ältere Version)."""
    if 'Pruefen_Korrigieren' not in wb.sheetnames:
        return None
    ws = wb['Pruefen_Korrigieren']
    pos = _finde_zelle(ws, 'ID', max_col=1)
    out = {}
    for r in ws.iter_rows(min_row=(pos[0] if pos else 6) + 1, max_col=13, values_only=True):
        if r[0] and isinstance(r[0], str) and r[0][:2] in ('K-', 'F-'):
            out[r[0].strip()] = {'Entscheidung': r[9] if r[9] not in ('', 0) else None,
                                 'Kommentar': r[10], 'Quelle': r[11]}
    return out


def lade_regeln(wb):
    """Angenommene Regel-Vorschläge (Spalte T = x) -> {Stichwort: Projekt}."""
    if 'Pruefen_Korrigieren' not in wb.sheetnames:
        return {}
    ws = wb['Pruefen_Korrigieren']
    out = {}
    for r in ws.iter_rows(min_row=7, min_col=15, max_col=20, values_only=True):
        if r[0] and r[1] and str(r[5] or '').strip().lower() in ('x', 'ja', '✔'):
            out[str(r[0])] = str(r[1])
    return out


def lade_vorlage(path, config):
    """Alles, was aus der Vorversion übernommen werden muss, in EINEM Aufruf."""
    wb = _wb(path)
    cal, trips = load_rohdaten_from_workbook(wb, config)
    return {
        'regeln': lade_regeln(wb),
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
    ws.title = 'Stammdaten'
    ws['A1'] = 'Stammdaten – Projekte, Partner, Sätze'
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
        type="list", formula1=f'=Stammdaten!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
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
    # Version 6.2: Versionsblock steht im Cockpit (wird in finalize_workbook geschrieben)
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

    # Referenz-Strings für spaetere Formeln merken
    stamm_range = f"Stammdaten!$F${stamm_start}:$H${stamm_last_mit_ignoriert}"
    partner_range = f"Stammdaten!$J${pz_start}:$K${pz_last_padded}"

    sonderkalk_alle = [p_ for p_, c_ in config.get('sonderkalkulationen', {}).items()
                       if not p_.startswith('_') and isinstance(c_, dict)]

    def _sk_bedingung(zp, zm):
        teile = []
        for p_ in sonderkalk_alle:
            m_ = config['sonderkalkulationen'][p_].get('mitarbeiter')
            teile.append(f'AND({zp}="{p_}",{zm}="{m_}")' if m_ else f'{zp}="{p_}"')
        return 'OR(' + ','.join(teile) + ')' if teile else 'FALSE'
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
            'Mehrtaegig_Blocker', 'Ist_Pauschale', 'Entscheidung (aus Prüfen & Korrigieren)',
            'Projekt (automatisch erkannt, intern)', 'Zuordnung_Grund', 'Prüfen', 'Betreff', 'Quelle',
            'Status', 'ID']
    ws.append(cols)
    style_header_row(ws, 1, len(cols))
    cal_all_rows = calendar_df.copy()
    for col_, dflt in (('Korrektur', None), ('Zuordnung_Grund', ''), ('Unsicher', False),
                       ('Quelle', 'neu'), ('Betreff', None)):
        if col_ not in cal_all_rows.columns:
            cal_all_rows[col_] = dflt
    cal_all_rows = setze_ids(cal_all_rows, 'kalender')
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
                    'JA' if r_['Ist_Pauschale'] else '', None, auto_projekt,
                    r_['Zuordnung_Grund'] or '', 'JA - bitte prüfen' if unsicher else '',
                    r_['Betreff'] if isinstance(r_['Betreff'], str) else None, r_['Quelle'], None, r_['ID']])
        # Version 6.2: Entscheidung kommt aus der EINEN Liste "Pruefen_Korrigieren" (Schlüssel = ID)
        ws.cell(row=row, column=17, value=_entscheidung_formel(f'X{row}'))
        ws.cell(row=row, column=23,
                value=f'=IF(E{row}="","",IFERROR(VLOOKUP(E{row},{stamm_range},3,FALSE),"TBD"))')
        ws.cell(row=row, column=5,
                value=(f'=IF(Q{row}<>"",IF(Q{row}="Unberücksichtigt","",Q{row}),IF(R{row}="","",R{row}))'))
        ws.cell(row=row, column=6,
                value=f'=IF(E{row}="","",IFERROR(VLOOKUP(E{row},{stamm_range},2,FALSE),"TBD"))')
        # Version 6: Kosten live je Zeile (Korrektur wirkt jetzt auch auf die Kosten)
        ws.cell(row=row, column=13,
                value=(f'=IF(OR(E{row}="",O{row}<>"",{_sk_bedingung(f"E{row}", f"C{row}")}),0,'
                       f'ROUND(K{row}*N(L{row}),2))'))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = normal
            cell.border = border
        if row[14].value or row[19].value:
            for cell in row:
                cell.fill = warn_fill
        row[10].number_format = '0.00'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    autosize(ws, [8, 10, 20, 12, 24, 22, 32, 12, 16, 16, 9, 12, 12, 40, 18, 12, 26, 24, 50, 16, 40, 14, 10, 13])
    ws.freeze_panes = 'A2'
    for col_ in 'DGLPRSV':   # technische Spalten einklappen (Version 6.2)
        ws.column_dimensions[col_].outlineLevel = 1
        ws.column_dimensions[col_].hidden = True
    n_cal_rows = max(ws.max_row, 2)

    # ---------------- Rohdaten_Fahrten ----------------
    ws = wb.create_sheet('Rohdaten_Fahrten')
    cols = ['Jahr', 'Monat', 'Mitarbeiter', 'Projekt', 'Firma', 'Herkunft', 'Datum', 'Start', 'Ende',
            'Distanz_km', 'Dauer_h', 'KmSatz_EUR', 'Kosten_Fahrt_EUR', 'Start-Adresse', 'End-Adresse',
            'Partner (Autolog)', 'Zweck', 'Projekt (Kalender-Match, intern)',
            'Entscheidung (aus Prüfen & Korrigieren)', 'Zuordnung_Grund', 'Prüfen', 'Quelle', 'Status', 'ID']
    ws.append(cols)
    style_header_row(ws, 1, len(cols))
    tdf = trips_df.copy()
    if 'Projekt_Kalender' not in tdf.columns:
        tdf['Projekt_Kalender'] = tdf['Projekt']
    for col_, dflt in (('Korrektur', None), ('Zuordnung_Grund', ''), ('Unsicher', False), ('Quelle', 'neu')):
        if col_ not in tdf.columns:
            tdf[col_] = dflt
    tdf['Monat'] = tdf['Start'].dt.strftime('%Y-%m')
    tdf = setze_ids(tdf, 'fahrten')
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
                    None, r_['Start-Adresse'], r_['End-Adresse'], r_['Partner'], r_['Zweck'], kal_match, None,
                    grund, 'JA - bitte prüfen' if unsicher else '', r_['Quelle'], None, r_['ID']])
        ws.cell(row=row, column=19, value=_entscheidung_formel(f'X{row}'))
        ws.cell(row=row, column=23,
                value=f'=IF(D{row}="","",IFERROR(VLOOKUP(D{row},{stamm_range},3,FALSE),"TBD"))')
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
                value=(f'=IF(D{row}="","",IF(OR(' + ','.join(
                    [f'AND(D{row}="{p_}",C{row}="{config["sonderkalkulationen"][p_].get("mitarbeiter")}")'
                     if config["sonderkalkulationen"][p_].get("mitarbeiter") else f'D{row}="{p_}"'
                     for p_ in fahrt_ohne_kosten] or ['FALSE']) + f'),0,J{row}*L{row}))'))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.font = normal
            cell.border = border
        if row[20].value:
            for cell in row:
                cell.fill = warn_fill
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f"A1:{get_column_letter(len(cols))}{ws.max_row}"
    autosize(ws, [8, 10, 20, 24, 30, 30, 12, 16, 16, 11, 10, 11, 14, 45, 45, 18, 20, 22, 26, 55, 16, 14, 10, 13])
    for col_ in 'GKLNOQRV':
        ws.column_dimensions[col_].outlineLevel = 1
        ws.column_dimensions[col_].hidden = True
    n_trip_rows = max(ws.max_row, 2)

    # ---------------- Zusatzkosten ----------------
    ws = wb.create_sheet('Zusatzkosten')
    ws['A1'] = 'Zusatzkosten (manuell erfassen)'
    ws['A1'].font = title_font
    ws['A2'] = 'Datum eintragen, Projektname EXAKT wie im Kalender, Betrag netto in €. Jahr/Monat automatisch.'
    ws['A2'].font = sub_font
    cols = ['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR (netto)', 'Anmerkung', 'Jahr (auto)', 'Monat (auto)',
            'Firma (auto)', 'Status (auto)']
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
        ws.cell(row=rr, column=8, value=f'=IF(B{rr}="","",IFERROR(VLOOKUP(B{rr},{stamm_range},2,FALSE),"TBD"))')
        ws.cell(row=rr, column=9, value=f'=IF(B{rr}="","",IFERROR(VLOOKUP(B{rr},{stamm_range},3,FALSE),"TBD"))')
        for c in range(1, 10):
            ws.cell(row=rr, column=c).font = normal
            ws.cell(row=rr, column=c).border = border
        for c in (1, 2, 3, 4, 5):
            ws.cell(row=rr, column=c).fill = blue_fill
    dv_zk_projekt = DataValidation(
        type="list", formula1=f'=Stammdaten!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
    ws.add_data_validation(dv_zk_projekt)
    dv_zk_projekt.add(f'B{zk_start_row}:B{zk_last_row}')
    ws.auto_filter.ref = f"A{zk_hdr_row}:I{zk_last_row}"
    autosize(ws, [14, 24, 22, 18, 40, 12, 12, 18, 10])

    # ---------------- Manuelle_Zeitbuchungen ----------------
    ws = wb.create_sheet('Manuelle_Zeitbuchungen')
    ws['A1'] = 'Manuelle Zeitbuchungen (Termine, die noch nicht im Kalender stehen)'
    ws['A1'].font = title_font
    ws['A2'] = ('Datum, Mitarbeiter, Projekt (exakt wie im Kalender), Hauptaufgabe-Kategorie, Stunden. '
                'Stundensatz/Kosten/Jahr/Monat werden automatisch berechnet.')
    ws['A2'].font = sub_font
    mz_cols = ['Datum', 'Mitarbeiter', 'Projekt', 'Hauptaufgabe', 'Stunden', 'Anmerkung',
               'Jahr (auto)', 'Stundensatz_EUR', 'Kosten_Zeit_EUR (auto)', 'Monat (auto)',
               'Firma (auto)', 'Status (auto)']
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
    ma_range = f'Stammdaten!$A$5:$D${4 + sum(len(config["mitarbeiter_satzhistorie"][m]["saetze"]) for m in mitarbeiter_liste)}'
    for rr in range(r, mz_last_row + 1):
        # Version 6.2: neue Zeilen holen den Stundensatz selbst (vorher blieb er leer -> 0 €)
        ws.cell(row=rr, column=8, value=f'=IF(B{rr}="","",IFERROR(VLOOKUP(B{rr},{ma_range},4,FALSE),""))')
    for rr in range(mz_start_row, mz_last_row + 1):
        ws.cell(row=rr, column=11, value=f'=IF(C{rr}="","",IFERROR(VLOOKUP(C{rr},{stamm_range},2,FALSE),"TBD"))')
        ws.cell(row=rr, column=12, value=f'=IF(C{rr}="","",IFERROR(VLOOKUP(C{rr},{stamm_range},3,FALSE),"TBD"))')
        ws.cell(row=rr, column=7, value=f'=IF(A{rr}="","",YEAR(A{rr}))')
        ws.cell(row=rr, column=9, value=f'=IF(A{rr}="","",E{rr}*N(H{rr}))')
        ws.cell(row=rr, column=10, value=f'=IF(A{rr}="","",YEAR(A{rr})&"-"&TEXT(MONTH(A{rr}),"00"))')
        for c in range(1, 13):
            ws.cell(row=rr, column=c).font = normal
            ws.cell(row=rr, column=c).border = border
        for c in (1, 2, 3, 4, 5, 6, 8):
            ws.cell(row=rr, column=c).fill = blue_fill
    dv_mz_projekt = DataValidation(
        type="list", formula1=f'=Stammdaten!$F${stamm_start}:$F${stamm_last_mit_puffer}', allow_blank=True)
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
    ws.auto_filter.ref = f"A{mz_hdr_row}:L{mz_last_row}"
    autosize(ws, [14, 20, 22, 32, 10, 35, 12, 14, 18, 12, 18, 10])

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
                    'Übernachtung (€)', 'Kosten Block (€)', 'Informative Std. (für interne Auswertung)',
                    'Projekt', 'Firma', 'Status', 'Mitarbeiter', 'Hauptaufgabe'])
        b_hdr = 4
        style_header_row(ws, b_hdr, 15)
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
            ws.cell(row=row, column=11, value=projekt)
            ws.cell(row=row, column=12, value=f'=IFERROR(VLOOKUP(K{row},{stamm_range},2,FALSE),"TBD")')
            ws.cell(row=row, column=13, value=f'=IFERROR(VLOOKUP(K{row},{stamm_range},3,FALSE),"TBD")')
            ws.cell(row=row, column=14, value=cfg.get('mitarbeiter'))
            ws.cell(row=row, column=15, value=cfg.get('hauptaufgabe'))
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
        for c_, h_ in enumerate(['Monat', 'Projekt', 'Firma', 'Status', 'Mitarbeiter', 'Hauptaufgabe'], start=5):
            ws.cell(row=p_hdr, column=c_, value=h_)
        style_header_row(ws, p_hdr, 10)
        p_start = p_hdr + 1
        for i, (_, r_) in enumerate(pausch_df.iterrows()):
            row = p_start + i
            ws.cell(row=row, column=1, value=int(r_['Jahr']))
            ws.cell(row=row, column=2, value=int(r_['KW']))
            ws.cell(row=row, column=3, value=r_['Woche_ab'].strftime('%d.%m.%Y'))
            ws.cell(row=row, column=4, value=r_['Anfahrtspauschale_EUR'])
            ws.cell(row=row, column=5, value=r_['Woche_ab'].strftime('%Y-%m'))
            ws.cell(row=row, column=6, value=projekt)
            ws.cell(row=row, column=7, value=f'=IFERROR(VLOOKUP(F{row},{stamm_range},2,FALSE),"TBD")')
            ws.cell(row=row, column=8, value=f'=IFERROR(VLOOKUP(F{row},{stamm_range},3,FALSE),"TBD")')
            ws.cell(row=row, column=9, value=cfg.get('mitarbeiter'))
            ws.cell(row=row, column=10, value=cfg.get('hauptaufgabe'))
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
        autosize(ws, [10, 10, 18, 18, 14, 10, 16, 16, 16, 22, 20, 16, 10, 18, 22])

        sonderkalk_refs[projekt] = {
            'sheet': sheet_name,
            'block_jahr_col': 'A', 'block_monat_col': 'B', 'block_kosten_col': 'I',
            'block_std_col': 'J', 'block_start': b_start, 'block_last': max(b_last, b_start),
            'pausch_jahr_col': 'A', 'pausch_kosten_col': 'D', 'pausch_start': p_start,
            'pausch_last': max(p_last, p_start),
            'has_blocks': len(block_df) > 0, 'has_pauschalen': len(pausch_df) > 0,
            'mitarbeiter': cfg.get('mitarbeiter'), 'hauptaufgabe': cfg.get('hauptaufgabe'),
        }

    # Version 6.2: kein eigener Reiter mehr - Auffälligkeiten kommen als Hinweis in Pruefen_Korrigieren
    flagged, threshold = plausibility_check(calendar_df, config)

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
        'version_info': vi, 'version_werte': werte, 'plausi': (flagged, threshold),
        'stamm_start': stamm_start, 'stamm_last_mit_puffer': stamm_last_mit_puffer,
        'mitarbeiter_range': ma_range, 'ganztag_info': None,
        # Version 6.2: Projekte, die NUR in Zusatzkosten/manuellen Zeiten vorkommen, gehören auch in die Übersicht
        'eingabe_projekte': {p_ for p_ in list(vor.get('Projekt', pd.Series(dtype=str)).dropna()) +
                             list(mz_vor['Projekt'].dropna()) if isinstance(p_, str) and p_.strip()},
    }


# ==========================================================================
# Version 6.2: IDs, Entscheidungs-Liste, Cockpit, Übersicht, Interne Auswertung
# ==========================================================================
PRUEF = 'Pruefen_Korrigieren'
PASST = '✔ passt'
TAB_FARBEN = {'gruen': '70AD47', 'gelb': 'FFC000', 'blau': '4472C4', 'grau': 'A6A6A6'}


def _entscheidung_formel(idzelle):
    """Rohdaten holen die Entscheidung per ID aus der EINEN Liste Pruefen_Korrigieren
    (Spalte J). '✔ passt' und leere Zellen ergeben "" (VLOOKUP-Leer-gibt-0-Falle beachtet)."""
    v = f'VLOOKUP({idzelle},{PRUEF}!$A:$J,10,FALSE)'
    return f'=IFERROR(IF({v}=0,"",IF({v}="{PASST}","",{v})),"")'


def setze_ids(df, art):
    """Stabile ID je Kalender-/Fahrtzeile (bleibt von Monat zu Monat gleich, solange sich
    der Termin bzw. die Fahrt nicht ändert). Vorhandene IDs (aus der Vorversion) bleiben."""
    import hashlib
    df = df.copy()
    if 'ID' not in df.columns:
        df['ID'] = None
    gesehen = set(x for x in df['ID'] if isinstance(x, str))
    for idx, r in df.iterrows():
        if isinstance(r['ID'], str) and r['ID']:
            continue
        if art == 'kalender':
            txt = r.get('Betreff') if isinstance(r.get('Betreff'), str) else \
                f"{r.get('Projekt') or ''} {r.get('Aufgabe') or ''}"
            basis = f"{r['Mitarbeiter']}|{r.get('Kalendertyp')}|{r['Start']:%Y%m%d%H%M}|{r['Ende']:%Y%m%d%H%M}|{_norm(txt)}"
            pre = 'K'
        else:
            basis = f"{r['Fahrer']}|{r['Start']:%Y%m%d%H%M}|{r['Ende']:%Y%m%d%H%M}|{r.get('Distanz (km)')}"
            pre = 'F'
        i_ = pre + '-' + hashlib.sha1(basis.encode('utf-8')).hexdigest()[:10]
        k_, n_ = i_, 2
        while k_ in gesehen:
            k_, n_ = f'{i_}-{n_}', n_ + 1
        gesehen.add(k_)
        df.at[idx, 'ID'] = k_
    return df


def _quellen(ctx):
    """Datenquellen für die Filter-Summen (Spaltenbuchstaben je Merkmal)."""
    n_cal, n_trip = ctx['n_cal_rows'], ctx['n_trip_rows']
    q = {
        'kal': dict(sheet='Rohdaten_Kalender', r1=2, r2=n_cal,
                    k=dict(jahr='A', monat='B', mitarbeiter='C', projekt='E', firma='F', hauptaufgabe='G', status='W'),
                    fix=[('E', '"?*"'), ('F', '"<>Ignoriert / kein Projekt"')]),
        'fahrt': dict(sheet='Rohdaten_Fahrten', r1=2, r2=n_trip,
                      k=dict(jahr='A', monat='B', mitarbeiter='C', projekt='D', firma='E', status='W'),
                      fix=[('D', '"?*"'), ('E', '"<>Ignoriert / kein Projekt"')]),
        'zk': dict(sheet='Zusatzkosten', r1=ctx['zk_start_row'], r2=ctx['zk_last_row'],
                   k=dict(jahr='F', monat='G', projekt='B', firma='H', status='I'), fix=[('B', '"?*"')]),
        'mz': dict(sheet='Manuelle_Zeitbuchungen', r1=ctx['mz_start_row'], r2=ctx['mz_last_row'],
                   k=dict(jahr='G', monat='J', mitarbeiter='B', projekt='C', hauptaufgabe='D', firma='K', status='L'),
                   fix=[('C', '"?*"')]),
    }
    sk = []
    for ref in ctx['sonderkalk_refs'].values():
        if ref['has_blocks']:
            sk.append(('skb', dict(sheet=ref['sheet'], r1=ref['block_start'], r2=ref['block_last'],
                                   k=dict(jahr='A', monat='B', projekt='K', firma='L', status='M',
                                          mitarbeiter='N', hauptaufgabe='O'), fix=[])))
        if ref['has_pauschalen']:
            sk.append(('skp', dict(sheet=ref['sheet'], r1=ref['pausch_start'], r2=ref['pausch_last'],
                                   k=dict(jahr='A', monat='E', projekt='F', firma='G', status='H',
                                          mitarbeiter='I', hauptaufgabe='J'), fix=[])))
    return q, sk


def _sumifs(src, wertspalte, sel, extra=None):
    """SUMIFS über eine Quelle; Merkmale, die die Quelle nicht kennt (z.B. Mitarbeiter bei
    Zusatzkosten), schließen sie aus (-> 0), statt falsch zu summieren."""
    if src['r2'] < src['r1']:
        return '0'
    for key, expr in sel.items():
        if expr is not None and key not in src['k']:
            return '0'
    sh, r1, r2 = src['sheet'], src['r1'], src['r2']
    rng = lambda c: f"{sh}!${c}${r1}:${c}${r2}"
    teile = [rng(wertspalte)]
    for c, crit in src['fix'] + list(extra or []):
        teile += [rng(c), crit]
    for key, expr in sel.items():
        if expr is not None:
            teile += [rng(src['k'][key]), expr]
    return 'SUMIFS(' + ','.join(teile) + ')'


def _formeln(ctx, sel):
    """Kennzahlen-Formeln (ohne '=') für eine Filterauswahl - gleiche Logik wie Übersicht und
    summen_je_monat_projekt() (alle Bestandteile: Kalender, manuelle Zeiten, Sonderkalk., Fahrten, Zusatzkosten)."""
    q, sk = _quellen(ctx)
    std = '+'.join([_sumifs(q['kal'], 'K', sel, [('O', '""')]), _sumifs(q['mz'], 'E', sel)])
    kzeit = '+'.join([_sumifs(q['kal'], 'M', sel), _sumifs(q['mz'], 'I', sel)] +
                     [_sumifs(src, 'I' if art == 'skb' else 'D', sel) for art, src in sk])
    info = '+'.join([_sumifs(src, 'J', sel) for art, src in sk if art == 'skb'] or ['0'])
    return {
        'std': std, 'kzeit': kzeit, 'km': _sumifs(q['fahrt'], 'J', sel),
        'kfahrt': _sumifs(q['fahrt'], 'M', sel), 'fdauer': _sumifs(q['fahrt'], 'K', sel),
        'zk': _sumifs(q['zk'], 'D', sel), 'infostd': info,
    }


def _netto(f):
    return f"({f['kzeit']})+({f['kfahrt']})+({f['zk']})"


def _filterblock(ws, ctx, start_row, felder, listen_spalten, titel='Filter'):
    """Dropdown-Filter (Spalte B, blau) + Hilfszelle (Spalte C, Wildcard für SUMIFS)."""
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.styles import Font
    ws.cell(row=start_row - 1, column=1, value=titel).font = ctx['bold']
    refs = {}
    for i, (label, key) in enumerate(felder):
        r = start_row + i
        ws.cell(row=r, column=1, value=label).font = ctx['bold']
        c = ws.cell(row=r, column=2, value='(Alle)')
        c.font = ctx['normal']; c.fill = ctx['blue_fill']; c.border = ctx['border']
        helper = f'=IF(B{r}="(Alle)",">=0",B{r})' if key == 'jahr' else f'=IF(B{r}="(Alle)","*",B{r})'
        h = ws.cell(row=r, column=3, value=helper)
        h.font = Font(name=ctx['FONT'], size=7, color='BFBFBF')
        sp, n = listen_spalten[key]
        dv = DataValidation(type='list', formula1=f'=Listen!${sp}$2:${sp}${n + 2}', allow_blank=False)
        ws.add_data_validation(dv)
        dv.add(f'B{r}')
        refs[key] = f'$C${r}'
    return refs


def _build_listen(wb, ctx, jahre, monate, projekte, firmen, config):
    ws = wb.create_sheet('Listen')
    werte = {
        'A': ('Jahr', jahre), 'B': ('Monat', monate), 'C': ('Mitarbeiter', ctx['mitarbeiter_liste']),
        'D': ('Projekt', projekte), 'E': ('Firma', firmen), 'F': ('Status', ['aktiv', 'beendet', 'laufend', 'TBD']),
        'G': ('Hauptaufgabe', ctx['hauptaufgaben_liste']),
    }
    spalten = {}
    for sp, (kopf, liste) in werte.items():
        ws[f'{sp}1'] = kopf
        ws[f'{sp}2'] = '(Alle)'
        for i, v in enumerate(liste):
            ws[f'{sp}{3 + i}'] = v
        spalten[kopf.lower()] = (sp, len(liste))
    # Auswahl für Entscheidungen
    entsch = ['Unberücksichtigt', PASST] + list(projekte)
    ws['H1'] = 'Entscheidung'
    for i, v in enumerate(entsch):
        ws[f'H{2 + i}'] = v
    ctx['entscheid_range'] = f'Listen!$H$2:$H${1 + len(entsch)}'
    ws.sheet_state = 'hidden'
    return spalten


def _build_uebersicht(wb, ctx, projekte, listen_sp, config):
    from openpyxl.styles import Alignment
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet('Uebersicht')
    ws['A1'] = 'Projektübersicht'
    ws['A1'].font = ctx['title_font']
    refs = _filterblock(ws, ctx, 3, [('Jahr', 'jahr')], listen_sp, titel='Jahr wählen ("(Alle)" = alle Jahre):')
    jahr = refs['jahr']
    mas = ctx['mitarbeiter_liste']
    kopf = (['Projekt', 'Firma', 'Status'] +
            [f"Std. {config['mitarbeiter_satzhistorie'][m]['kuerzel']}" for m in mas] +
            ['Std. gesamt', 'Kosten Zeit Netto (€)', 'Distanz gesamt (km)', 'Kosten Fahrt Netto (€)',
             'Fahrdauer (h, informativ)', 'Zusatzkosten Netto (€)', 'Gesamtkosten Netto (€)', 'MwSt. (€)',
             'Gesamtkosten Brutto (€)', 'Hinweis'])
    hr = 5
    for c, h in enumerate(kopf, start=1):
        cell = ws.cell(row=hr, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = ctx['border']
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    n_ma = len(mas)
    c_std = 4 + n_ma
    wp_bez = config.get('wochenpauschale', {}).get('bezeichnung')
    mwst = f"Stammdaten!$B${ctx['mwst_param_row']}"
    for i, proj in enumerate(projekte):
        row = hr + 1 + i
        sel = {'jahr': jahr, 'projekt': f'$A{row}'}
        f = _formeln(ctx, sel)
        ws.cell(row=row, column=1, value=proj)
        ws.cell(row=row, column=2, value=f'=IFERROR(VLOOKUP($A{row},{ctx["stamm_range"]},2,FALSE),"TBD")')
        ws.cell(row=row, column=3, value=f'=IFERROR(VLOOKUP($A{row},{ctx["stamm_range"]},3,FALSE),"TBD")')
        for j, ma in enumerate(mas):
            fm = _formeln(ctx, {**sel, 'mitarbeiter': f'"{ma}"'})
            ws.cell(row=row, column=4 + j, value='=' + fm['std'])
        L = get_column_letter
        ws.cell(row=row, column=c_std, value=f'=SUM({L(4)}{row}:{L(3 + n_ma)}{row})')
        ws.cell(row=row, column=c_std + 1, value='=' + f['kzeit'])
        ws.cell(row=row, column=c_std + 2, value='=' + f['km'])
        ws.cell(row=row, column=c_std + 3, value='=' + f['kfahrt'])
        ws.cell(row=row, column=c_std + 4, value='=' + f['fdauer'])
        ws.cell(row=row, column=c_std + 5, value='=' + f['zk'])
        a, b, c_ = L(c_std + 1), L(c_std + 3), L(c_std + 5)
        ws.cell(row=row, column=c_std + 6, value=f'={a}{row}+{b}{row}+{c_}{row}')
        g = L(c_std + 6)
        ws.cell(row=row, column=c_std + 7, value=f'={g}{row}*{mwst}/100')
        ws.cell(row=row, column=c_std + 8, value=f'={g}{row}+{L(c_std + 7)}{row}')
        hinweis = ''
        if proj in ctx['sonderkalk_refs']:
            hinweis = 'Sonderkalkulation (Tagessätze/Pauschalen); Fahrten nur informativ.'
        elif proj == wp_bez:
            hinweis = 'Automatische Wochenpauschale, nicht kundenprojektbezogen.'
        ws.cell(row=row, column=c_std + 9, value=hinweis)
    last = hr + len(projekte)
    sum_row = last + 1
    ws.cell(row=sum_row, column=1, value='GESAMT')
    for col in range(4, c_std + 9):
        Lc = get_column_letter(col)
        ws.cell(row=sum_row, column=col, value=f'=SUM({Lc}{hr + 1}:{Lc}{last})')
    for row in ws.iter_rows(min_row=hr + 1, max_row=sum_row, max_col=len(kopf)):
        for cell in row:
            cell.font = ctx['bold'] if cell.row == sum_row else ctx['normal']
            cell.border = ctx['border']
            if cell.column in (c_std + 1, c_std + 3, c_std + 5, c_std + 6, c_std + 7, c_std + 8):
                cell.number_format = '#,##0.00 €'
            elif cell.column >= 4 and cell.column < c_std + 9:
                cell.number_format = '#,##0.0'
    ws.auto_filter.ref = f'A{hr}:{get_column_letter(len(kopf))}{last}'
    for i, w in enumerate([24, 16, 10] + [9] * n_ma + [10, 15, 12, 14, 12, 14, 16, 12, 16, 40], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = f'B{hr + 1}'
    ctx['uebersicht_sum_row'] = sum_row
    ctx['uebersicht_netto_col'] = get_column_letter(c_std + 6)
    return ws


def _build_cockpit(wb, ctx, projekte, listen_sp, config, berichtsjahr):
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
    from openpyxl.formatting.rule import CellIsRule
    ws = wb.create_sheet('Cockpit', 0)
    ws['A1'] = 'Cockpit – Projektkosten'
    ws['A1'].font = ctx['title_font']
    ws['A2'] = ('Filter wählen (blau). Alle Zahlen enthalten Kalenderzeiten, manuelle Zeiten, Sonderkalkulation, '
                'Fahrten und Zusatzkosten – identisch zur Übersicht.')
    ws['A2'].font = ctx['sub_font']
    sel = _filterblock(ws, ctx, 5, [('Jahr', 'jahr'), ('Monat', 'monat'), ('Firma', 'firma'),
                                    ('Projekt', 'projekt'), ('Status', 'status')], listen_sp)
    f = _formeln(ctx, sel)
    mwst = f"Stammdaten!$B${ctx['mwst_param_row']}"
    r0 = 12
    ws.cell(row=r0 - 1, column=1, value='Ergebnis für die Auswahl').font = ctx['bold']
    zeilen = [('Stunden', f['std'], '#,##0.0'), ('Kosten Zeit netto', f['kzeit'], '#,##0.00 €'),
              ('Distanz (km)', f['km'], '#,##0'), ('Kosten Fahrt netto', f['kfahrt'], '#,##0.00 €'),
              ('Zusatzkosten netto', f['zk'], '#,##0.00 €')]
    for i, (lab, form, fmt) in enumerate(zeilen):
        ws.cell(row=r0 + i, column=1, value=lab).font = ctx['normal']
        c = ws.cell(row=r0 + i, column=2, value='=' + form)
        c.number_format = fmt; c.font = ctx['normal']
    rn = r0 + len(zeilen)
    for i, (lab, form) in enumerate([('Gesamtkosten NETTO', f'=B{r0 + 1}+B{r0 + 3}+B{r0 + 4}'),
                                     ('MwSt.', f'=B{rn}*{mwst}/100'), ('Gesamtkosten BRUTTO', f'=B{rn}+B{rn + 1}')]):
        ws.cell(row=rn + i, column=1, value=lab).font = ctx['bold']
        c = ws.cell(row=rn + i, column=2, value=form)
        c.number_format = '#,##0.00 €'; c.font = ctx['bold']; c.fill = ctx['kpi_fill']
    ctx['cockpit_netto'] = f'B{rn}'

    # ---- Status (rechts): Versionsblock + Prüfstatus + Monatsabschluss
    w = ctx['version_werte']
    ws.cell(row=4, column=5, value='Berichtsversion').font = ctx['hdr_font']
    ws.cell(row=4, column=5).fill = ctx['hdr_fill']
    ws.cell(row=4, column=6).fill = ctx['hdr_fill']
    for k_, (lab, key) in enumerate(VERSION_FELDER):
        rr = 5 + k_
        ws.cell(row=rr, column=5, value=lab).font = ctx['normal']
        c_ = ws.cell(row=rr, column=6, value=w[key])
        c_.font = ctx['normal']
        for cc in (5, 6):
            ws.cell(row=rr, column=cc).border = ctx['border']
        if key in ('freigegeben_am', 'freigegeben_von'):
            c_.fill = ctx['blue_fill']
    rs = 5 + len(VERSION_FELDER) + 1
    ws.cell(row=rs, column=5, value='Prüfstatus').font = ctx['bold']
    ws.cell(row=rs + 1, column=5, value='Abgleich Vormonate')
    ws.cell(row=rs + 1, column=6, value='=Abgleich_Vormonate!A4')
    ws.cell(row=rs + 2, column=5, value='Offene Prüfpunkte')
    ws.cell(row=rs + 2, column=6, value=f'={PRUEF}!C3&" (+ "&COUNTIF({PRUEF}!M:M,"Hinweis offen")&" Hinweise)"')
    ws.cell(row=rs + 3, column=5, value='Formel-Check')
    ws.cell(row=rs + 3, column=6,
            value=(f'=IF(ISERROR(Uebersicht!{ctx["uebersicht_netto_col"]}{ctx["uebersicht_sum_row"]}+{ctx["cockpit_netto"]}),'
                   f'"FEHLER - nicht ausliefern","0 Fehler ✔")'))
    ws.cell(row=rs + 5, column=5, value='Monatsabschluss (abhaken mit x)').font = ctx['bold']
    for i, t in enumerate(['Neue Daten geladen', 'Prüfliste: offen = 0', 'Abgleich Vormonate ✔ bzw. begründet',
                           'GF hat geprüft (Freigabe oben eintragen)']):
        ws.cell(row=rs + 6 + i, column=5, value=t)
        ws.cell(row=rs + 6 + i, column=6).fill = ctx['blue_fill']
        ws.cell(row=rs + 6 + i, column=6).border = ctx['border']

    # ---- Projektliste der Auswahl + Top 5
    pr0 = 24
    ws.cell(row=pr0 - 1, column=1, value='Projekte der Auswahl (0 € = grau)').font = ctx['bold']
    for c, h in enumerate(['Projekt', 'Firma', 'Status', 'Stunden', 'Netto (€)', 'Brutto (€)'], start=1):
        cell = ws.cell(row=pr0, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = ctx['border']
    for i, proj in enumerate(projekte):
        row = pr0 + 1 + i
        s2 = {**sel, 'projekt': f'$A{row}'}
        fp = _formeln(ctx, s2)
        bedingung = f'OR({sel["projekt"]}="*",{sel["projekt"]}=$A{row})'
        ws.cell(row=row, column=1, value=proj)
        ws.cell(row=row, column=2, value=f'=IFERROR(VLOOKUP($A{row},{ctx["stamm_range"]},2,FALSE),"TBD")')
        ws.cell(row=row, column=3, value=f'=IFERROR(VLOOKUP($A{row},{ctx["stamm_range"]},3,FALSE),"TBD")')
        ws.cell(row=row, column=4, value=f'=IF({bedingung},{fp["std"]},0)').number_format = '#,##0.0'
        ws.cell(row=row, column=5, value=f'=IF({bedingung},{_netto(fp)},0)').number_format = '#,##0.00 €'
        ws.cell(row=row, column=6, value=f'=E{row}*(1+{mwst}/100)').number_format = '#,##0.00 €'
        ws.cell(row=row, column=8, value=f'=E{row}+ROW()/1000000000')     # Hilfsspalte Top 5
        for c in range(1, 7):
            ws.cell(row=row, column=c).border = ctx['border']
    pl = pr0 + len(projekte)
    grau = PatternFill('solid', fgColor='F2F2F2')
    from openpyxl.formatting.rule import FormulaRule
    ws.conditional_formatting.add(f'A{pr0 + 1}:F{pl}',
                                  FormulaRule(formula=[f'$E{pr0 + 1}=0'], fill=grau, font=Font(color='A6A6A6')))
    ws.column_dimensions['H'].hidden = True
    ws.auto_filter.ref = f'A{pr0}:F{pl}'
    t0 = pr0
    ws.cell(row=t0 - 1, column=10, value='Top 5 der Auswahl').font = ctx['bold']
    for c, h in enumerate(['Rang', 'Projekt', 'Netto (€)'], start=10):
        cell = ws.cell(row=t0, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']
    for k in range(1, 6):
        row = t0 + k
        ws.cell(row=row, column=10, value=k)
        big = f'LARGE($H${pr0 + 1}:$H${pl},{k})'
        ws.cell(row=row, column=11, value=f'=IFERROR(IF({big}<0.001,"",INDEX($A${pr0 + 1}:$A${pl},MATCH({big},$H${pr0 + 1}:$H${pl},0))),"")')
        ws.cell(row=row, column=12, value=f'=IFERROR(IF(K{row}="","",INDEX($E${pr0 + 1}:$E${pl},MATCH({big},$H${pr0 + 1}:$H${pl},0))),"")').number_format = '#,##0.00 €'
    # Monatsverlauf
    m0 = t0 + 8
    ws.cell(row=m0 - 1, column=10, value='Monatsverlauf netto (gewähltes Jahr, sonst Berichtsjahr)').font = ctx['bold']
    for c, h in enumerate(['Monat', 'Netto (€)'], start=10):
        cell = ws.cell(row=m0, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']
    jahr_txt = f'IF($B$5="(Alle)",{berichtsjahr},$B$5)'
    for mth in range(1, 13):
        row = m0 + mth
        ws.cell(row=row, column=10, value=f'={jahr_txt}&"-"&TEXT({mth},"00")')
        sm = {**sel, 'monat': f'J{row}', 'jahr': None}
        fm = _formeln(ctx, sm)
        ws.cell(row=row, column=11, value='=' + _netto(fm)).number_format = '#,##0.00 €'
    for i, wdt in enumerate([26, 16, 10, 12, 30, 22, 2, 2, 2, 10, 24, 16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = wdt
    ws.column_dimensions['C'].width = 3
    ws.print_area = f'A1:L{max(pl, m0 + 12)}'
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddHeader.center.text = 'Füxle Cockpit – Auswahl: &[Tab]'
    return ws


def _build_interne_auswertung(wb, ctx, listen_sp, config, berichtsjahr):
    from openpyxl.utils import get_column_letter
    ws = wb.create_sheet('Interne_Auswertung')
    ws['A1'] = 'Interne Auswertung (GF) – Stunden und Kosten je Mitarbeiter'
    ws['A1'].font = ctx['title_font']
    ws['A2'] = ('Live gerechnet, inkl. manueller Zeiten. Niedermaier-Tagessätze als informative Stunden '
                f'({config.get("sonderkalkulationen", {}).get("Spedition Niedermaier", {}).get("tagessatz_enthaltene_stunden", 8.5)} h/Tag).')
    ws['A2'].font = ctx['sub_font']
    sel = _filterblock(ws, ctx, 5, [('Jahr', 'jahr'), ('Monat', 'monat'), ('Firma', 'firma'),
                                    ('Projekt', 'projekt'), ('Mitarbeiter', 'mitarbeiter')], listen_sp)
    mas, has = ctx['mitarbeiter_liste'], ctx['hauptaufgaben_liste']
    sel_ohne_ma = {k: v for k, v in sel.items() if k != 'mitarbeiter'}
    h0 = 12
    ws.cell(row=h0 - 1, column=1, value='Stunden je Mitarbeiter × Hauptaufgabe').font = ctx['bold']
    kopf = ['Mitarbeiter'] + has + ['Std. gesamt', 'Kosten Zeit (€)']
    for c, h in enumerate(kopf, start=1):
        cell = ws.cell(row=h0, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = ctx['border']
    for i, ma in enumerate(mas):
        row = h0 + 1 + i
        ws.cell(row=row, column=1, value=ma)
        bed = f'OR({sel["mitarbeiter"]}="*",{sel["mitarbeiter"]}="{ma}")'
        for j, ha in enumerate(has):
            fx = _formeln(ctx, {**sel_ohne_ma, 'mitarbeiter': f'"{ma}"', 'hauptaufgabe': f'"{ha}"'})
            ws.cell(row=row, column=2 + j, value=f'=IF({bed},{fx["std"]}+{fx["infostd"]},0)').number_format = '#,##0.0'
        L = get_column_letter
        ws.cell(row=row, column=2 + len(has), value=f'=SUM(B{row}:{L(1 + len(has))}{row})').number_format = '#,##0.0'
        fk = _formeln(ctx, {**sel_ohne_ma, 'mitarbeiter': f'"{ma}"'})
        ws.cell(row=row, column=3 + len(has), value=f'=IF({bed},{fk["kzeit"]},0)').number_format = '#,##0.00 €'
    sr = h0 + 1 + len(mas)
    ws.cell(row=sr, column=1, value='GESAMT').font = ctx['bold']
    for c in range(2, 4 + len(has)):
        L = get_column_letter(c)
        ws.cell(row=sr, column=c, value=f'=SUM({L}{h0 + 1}:{L}{sr - 1})').font = ctx['bold']
    # Monat × Mitarbeiter (Stunden) für das gewählte Jahr
    m0 = sr + 3
    ws.cell(row=m0 - 1, column=1, value='Stunden je Monat und Mitarbeiter (gewähltes Jahr, sonst Berichtsjahr)').font = ctx['bold']
    for c, h in enumerate(['Monat'] + mas, start=1):
        cell = ws.cell(row=m0, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']
    jahr_txt = f'IF($B$5="(Alle)",{berichtsjahr},$B$5)'
    for mth in range(1, 13):
        row = m0 + mth
        ws.cell(row=row, column=1, value=f'={jahr_txt}&"-"&TEXT({mth},"00")')
        for j, ma in enumerate(mas):
            fx = _formeln(ctx, {**sel_ohne_ma, 'jahr': None, 'monat': f'$A{row}', 'mitarbeiter': f'"{ma}"'})
            bed = f'OR({sel["mitarbeiter"]}="*",{sel["mitarbeiter"]}="{ma}")'
            ws.cell(row=row, column=2 + j, value=f'=IF({bed},{fx["std"]}+{fx["infostd"]},0)').number_format = '#,##0.0'
    for i, wdt in enumerate([22] + [16] * (len(has) + 2), start=1):
        ws.column_dimensions[get_column_letter(i)].width = wdt
    ws.column_dimensions['C'].width = 16
    return ws


def _wirkung(r, art):
    try:
        if art == 'kalender':
            if _ist_blocker(r):
                return 0.0
            return round(float(r['Dauer_h']) * float(r['Stundensatz_EUR'] or 0), 2)
        km = pd.to_numeric(r.get('Distanz (km)'), errors='coerce')
        return round(float(km if pd.notna(km) else 0) * float(r.get('KmSatz_EUR') or 0), 2)
    except (TypeError, ValueError):
        return 0.0


STOPPWORTE = set('''abstimmung termin termine projekt projekte besprechung telefonat unterlagen gespräch gespraech
mit und der die das für fuer von zum zur bei per via neu weitere weiteres vorgehen intern interne teams meeting
call anrufen marius neininger jenny jennifer felix seltmann mail mails versand erstellung prüfung pruefung
nachfassen info infos update abstimmungstermin nachbereitung vorbereitung kunde kunden herr frau'''.split())


def regel_vorschlaege(cal, config, mindestens=3):
    """Wiederkehrende Handkorrekturen -> Vorschlag für eine Stichwort-Regel (Version 6.2).
    Nur Stichwörter, die IMMER zum selben Projekt korrigiert wurden."""
    if 'Korrektur' not in cal.columns:
        return []
    bekannt = {_norm(x) for x in list(config.get('projekt_stammliste', {}).keys())
               + list(config.get('projektname_erkennung', {}).get('aliase', {}).keys())}
    bestehend = {_norm(k) for k in config.get('projektname_erkennung', {}).get('stichwort_regeln', {})}
    zaehler, ziele, beispiele = {}, {}, {}
    korr = cal[cal['Korrektur'].notna() & (cal['Korrektur'] != 'Unberücksichtigt') &
               (cal['Projekt'].isna() | (cal['Projekt'] != cal['Korrektur'])) & (~cal['Ist_Pauschale'].astype(bool))]
    for _, r in korr.iterrows():
        text = r.get('Betreff') if isinstance(r.get('Betreff'), str) else str(r.get('Aufgabe') or '')
        for w in set(re.findall(r'[A-Za-zÄÖÜäöüß]{4,}', text)):
            wn = w.casefold()
            if wn in STOPPWORTE or wn in bekannt or wn in bestehend:
                continue
            ziele.setdefault(wn, set()).add(r['Korrektur'])
            zaehler[(wn, r['Korrektur'])] = zaehler.get((wn, r['Korrektur']), 0) + 1
            beispiele.setdefault((wn, r['Korrektur']), text)
    ohne = cal[cal['Korrektur'].isna() & cal['Projekt'].isna()]
    texte_ohne = [str(b).casefold() for b in ohne.get('Betreff', ohne.get('Aufgabe', pd.Series(dtype=str))).fillna('')]
    out = []
    for (wn, proj), n in zaehler.items():
        if n >= mindestens and len(ziele[wn]) == 1:
            weitere = sum(1 for t in texte_ohne if re.search(r'(?<!\w)' + re.escape(wn) + r'(?!\w)', t))
            out.append({'Stichwort': wn, 'Projekt': proj, 'Anzahl': n, 'weitere': weitere,
                        'Beispiel': beispiele[(wn, proj)]})
    return sorted(out, key=lambda x: -x['Anzahl'])[:25]


def _build_pruefen_korrigieren(wb, ctx, calendar_df, trips_df, extra, config):
    from openpyxl.styles import Font, Alignment
    from openpyxl.worksheet.datavalidation import DataValidation
    ws = wb.create_sheet(PRUEF)
    ws['A1'] = 'Prüfen & Korrigieren – die EINE Liste'
    ws['A1'].font = ctx['title_font']
    ws['A2'] = ('Oben: offene Punkte (teuerste zuerst). In Spalte J entscheiden: Projekt, "Unberücksichtigt" oder '
                f'"{PASST}". Darunter alle bisherigen Entscheidungen, dann freie Zeilen (ID aus den Rohdaten, Spalte X, '
                'eintragen) und zuletzt Hinweise. Entscheidungen wirken sofort in Rohdaten, Übersicht und Cockpit.')
    ws['A2'].font = ctx['sub_font']
    ws['A2'].alignment = Alignment(wrap_text=True)
    ws.merge_cells('A2:M2')
    ws.row_dimensions[2].height = 42
    ws['A3'] = 'Offene Punkte:'
    ws['A3'].font = ctx['bold']
    kopf = ['ID', 'Art', 'Thema', 'Datum', 'Person', 'Betreff / Partner', 'Automatisch', 'Grund',
            'Wirkung (€)', 'Entscheidung', 'Kommentar', 'Quelle', 'Status']
    hr = 6
    for c, h in enumerate(kopf, start=1):
        cell = ws.cell(row=hr, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']; cell.border = ctx['border']
    neu_q = lambda q: not str(q or 'neu').startswith('Vorversion')
    offen, entschieden = [], []
    for art, df in (('kalender', calendar_df), ('fahrten', trips_df)):
        for _, r in df.iterrows():
            ent = r.get('Entscheidung') if isinstance(r.get('Entscheidung'), str) and r.get('Entscheidung') else None
            if ent is None and isinstance(r.get('Korrektur'), str) and r.get('Korrektur'):
                ent = r['Korrektur']
            uns = bool(r.get('Unsicher_wirksam', r.get('Unsicher', False))) if art == 'fahrten' else bool(r.get('Unsicher', False))
            grund = (r.get('Zuordnung_Grund_wirksam') if art == 'fahrten' else None) or r.get('Zuordnung_Grund') or ''
            auto = r.get('Projekt_Kalender') if art == 'fahrten' else r.get('Projekt')
            eintrag = [r['ID'], 'Kalender' if art == 'kalender' else 'Fahrt', None, r['Start'],
                       r['Mitarbeiter'] if art == 'kalender' else r['Fahrer'],
                       (r.get('Betreff') or r.get('Aufgabe')) if art == 'kalender' else r.get('Partner'),
                       auto if isinstance(auto, str) else '', grund, _wirkung(r, art), ent,
                       r.get('Entscheidung_Kommentar') if isinstance(r.get('Entscheidung_Kommentar'), str) else None,
                       r.get('Entscheidung_Quelle') if isinstance(r.get('Entscheidung_Quelle'), str) else r.get('Quelle')]
            if ent:
                eintrag[2] = 'Entscheidung'
                entschieden.append(eintrag)
            elif uns and neu_q(r.get('Quelle')):
                eintrag[2] = 'unsicher - bitte entscheiden'
                offen.append(eintrag)
    offen.sort(key=lambda e: -(e[8] or 0))
    entschieden.sort(key=lambda e: pd.Timestamp(e[3]))
    hinweise = []
    for e in extra:
        hinweise.append([None, 'Hinweis', e.get('Bereich'), e.get('Datum'), e.get('Mitarbeiter'), e.get('Text'),
                         e.get('Projekt') or '', e.get('Grund'), None, None, None, 'Bericht-Lauf'])
    flagged, thr = ctx.get('plausi', (pd.DataFrame(), 60))
    for _, f_ in flagged.iterrows():
        hinweise.append([None, 'Hinweis', f'Woche > {thr} h', None, f_['Mitarbeiter'],
                         f"KW {int(f_['ISO_KW'])}/{int(f_['ISO_Jahr'])}: {round(f_['Dauer_h'], 1)} h", '',
                         'Plausibilitätscheck - Kalender prüfen', None, None, None, 'Bericht-Lauf'])
    row = hr + 1
    bereiche = {}

    def schreibe(eintraege, typ, frei=0):
        nonlocal row
        start = row
        for e in eintraege:
            for c, v in enumerate(e, start=1):
                if c == 4 and v is not None and pd.notna(v):
                    v = pd.Timestamp(v).strftime('%d.%m.%Y %H:%M')
                ws.cell(row=row, column=c, value=v if not (isinstance(v, float) and pd.isna(v)) else None)
            row += 1
        for _ in range(frei):
            for c in (1, 10, 11):
                ws.cell(row=row, column=c).fill = ctx['blue_fill']
            ws.cell(row=row, column=3, value='frei (ID eintragen)')
            row += 1
        bereiche[typ] = (start, row - 1)
    schreibe(offen, 'offen')
    schreibe(entschieden, 'entschieden', frei=200)
    schreibe(hinweise, 'hinweis')
    last = max(row - 1, hr + 1)
    for rr in range(hr + 1, last + 1):
        ws.cell(row=rr, column=13,
                value=(f'=IF(AND(A{rr}="",B{rr}=""),"",IF(J{rr}<>"",IF(B{rr}="Hinweis","erledigt","entschieden"),'
                       f'IF(OR(C{rr}="Entscheidung",C{rr}="frei (ID eintragen)"),"",'
                       f'IF(B{rr}="Hinweis","Hinweis offen","offen"))))'))
        for c in range(1, 14):
            cell = ws.cell(row=rr, column=c)
            cell.font = ctx['normal']; cell.border = ctx['border']
        ws.cell(row=rr, column=9).number_format = '#,##0.00 €'
        ws.cell(row=rr, column=10).fill = ctx['blue_fill']
        ws.cell(row=rr, column=11).fill = ctx['blue_fill']
    o1, o2 = bereiche['offen']
    for rr in range(o1, o2 + 1):
        for c in range(1, 10):
            ws.cell(row=rr, column=c).fill = ctx['warn_fill']
    h1, h2 = bereiche['hinweis']
    for rr in range(h1, h2 + 1):
        ws.row_dimensions[rr].outlineLevel = 1
    ws['C3'] = f'=COUNTIF(M{hr + 1}:M{last},"offen")'
    ws['C3'].font = Font(name=ctx['FONT'], bold=True, size=14, color='C00000')
    ws['E3'] = f'=COUNTIF(M{hr + 1}:M{last},"Hinweis offen")&" Hinweise ab Zeile {h1} (eingeklappt, +/- links) - kurz ansehen, mit {PASST} abhaken"'
    ws['E3'].font = ctx['sub_font']
    dv = DataValidation(type='list', formula1='=' + ctx['entscheid_range'], allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f'J{hr + 1}:J{last}')
    ws.auto_filter.ref = f'A{hr}:M{last}'
    ws.freeze_panes = f'A{hr + 1}'
    for i, w in enumerate([14, 9, 22, 16, 18, 42, 20, 55, 12, 22, 24, 14, 11], start=1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = w
    # Regel-Vorschläge rechts
    vor = regel_vorschlaege(calendar_df, config)
    ws.cell(row=hr - 1, column=15, value='Regel-Vorschläge (ab 3 gleichen Korrekturen) – übernehmen mit x').font = ctx['bold']
    for c, h in enumerate(['Stichwort', 'Projekt', 'korrigiert', 'weitere ohne Korrektur', 'Beispiel', 'übernehmen (x)'],
                          start=15):
        cell = ws.cell(row=hr, column=c, value=h)
        cell.fill = ctx['hdr_fill']; cell.font = ctx['hdr_font']
    for i, v in enumerate(vor):
        rr = hr + 1 + i
        for c, x in enumerate([v['Stichwort'], v['Projekt'], v['Anzahl'], v['weitere'], v['Beispiel']], start=15):
            ws.cell(row=rr, column=c, value=x).font = ctx['normal']
        ws.cell(row=rr, column=20).fill = ctx['blue_fill']
    if not vor:
        ws.cell(row=hr + 1, column=15, value='keine').font = ctx['normal']
    for c, w in zip(range(15, 21), [16, 18, 10, 12, 40, 12]):
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = w
    ctx['pruef_bereiche'] = bereiche
    return ws


def finalize_workbook(wb, ctx, calendar_df, trips_df, config, mitarbeiter_liste=None,
                      abgleich=None, pruef_extra=None):
    """Version 6.2: Cockpit (Filter), Uebersicht (Jahr-Auswahl), Interne_Auswertung (GF, live),
    Pruefen_Korrigieren (eine Liste), Abgleich_Vormonate; Reiter farbig gruppiert; speichert."""
    ignore = set(config.get('projektname_erkennung', {}).get('ignorieren', []))
    cal_proj = calendar_df[calendar_df['Projekt'].notna()]
    trips_proj = apply_partner_zuordnung(trips_df, config)
    trips_proj = trips_proj[trips_proj['Projekt'].notna()]
    korr_proj = set()
    for df_ in (calendar_df, trips_df):
        if 'Korrektur' in df_.columns:
            korr_proj |= {k for k in df_['Korrektur'].dropna().unique()
                          if isinstance(k, str) and k and k != 'Unberücksichtigt'}
    projekte = sorted((set(cal_proj['Projekt'].unique()) | set(trips_proj['Projekt'].dropna().unique()) | korr_proj
                       | set(ctx.get('eingabe_projekte', set()))) - ignore)
    jahre = sorted(set(int(j) for j in cal_proj['Jahr'].unique()) |
                   set(int(j) for j in trips_proj['Jahr'].dropna().unique()))
    monate = sorted(set(calendar_df['Start'].dt.strftime('%Y-%m')) | set(trips_df['Start'].dt.strftime('%Y-%m')))
    firmen = sorted({_projekt_firma(p, config) for p in projekte} | {'Neininger GmbH', 'TransCare'})
    berichtsjahr = int(pd.Timestamp(ctx['version_info'].get('datenstand_bis') or calendar_df['Start'].max()).year)

    listen_sp = _build_listen(wb, ctx, jahre, monate, projekte, firmen, config)
    _build_uebersicht(wb, ctx, projekte, listen_sp, config)
    _build_interne_auswertung(wb, ctx, listen_sp, config, berichtsjahr)
    _build_pruefen_korrigieren(wb, ctx, calendar_df, trips_df, pruef_extra or [], config)
    _build_abgleich_sheet(wb, ctx, abgleich)
    _build_cockpit(wb, ctx, projekte, listen_sp, config, berichtsjahr)

    sk = [ref['sheet'] for ref in ctx['sonderkalk_refs'].values()]
    reihenfolge = (['Cockpit', 'Uebersicht', 'Interne_Auswertung', PRUEF, 'Abgleich_Vormonate',
                    'Zusatzkosten', 'Manuelle_Zeitbuchungen', 'Stammdaten',
                    'Rohdaten_Kalender', 'Rohdaten_Fahrten'] + sk + ['Listen'])
    farben = {'Cockpit': 'gruen', 'Uebersicht': 'gruen', 'Interne_Auswertung': 'gruen', PRUEF: 'gelb',
              'Abgleich_Vormonate': 'gelb', 'Zusatzkosten': 'blau', 'Manuelle_Zeitbuchungen': 'blau',
              'Stammdaten': 'blau', 'Rohdaten_Kalender': 'grau', 'Rohdaten_Fahrten': 'grau'}
    for name in sk:
        farben[name] = 'grau'
    wb._sheets = [wb[n] for n in reihenfolge if n in wb.sheetnames] + \
        [ws for ws in wb.worksheets if ws.title not in reihenfolge]
    for name, fb in farben.items():
        if name in wb.sheetnames:
            wb[name].sheet_properties.tabColor = TAB_FARBEN[fb]
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
    if proj is None or _ist_blocker(r) or sonderkalk_gilt(proj, r['Mitarbeiter'], config):
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
        t['K'] = t.apply(lambda r: 0.0 if (r['P'] in ohne and sonderkalk_gilt(r['P'], r['Fahrer'], config))
                         else r['km'] * float(r['KmSatz_EUR'] or 0), axis=1)
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
    grobf = _kal_key_grob if art == 'kalender' else (
        lambda r: (r['Fahrer'], pd.Timestamp(r['Start']).floor('min'), pd.Timestamp(r['Ende']).floor('min')))
    exakt, grob, tag_text, tag_text_ohne_ma = {}, {}, {}, {}

    def _text(r):
        if art != 'kalender':
            return ''
        b = r.get('Betreff')
        if isinstance(b, str) and b:
            return _norm(re.sub(r'[%s]' % ANFUEHRUNGSZEICHEN, '', b))
        p_, a_ = r.get('Projekt'), r.get('Aufgabe')
        return _norm(' '.join(x for x in (p_ if isinstance(p_, str) else '', a_ if isinstance(a_, str) else '') if x))
    vergeben = set()
    for idx, r in neu.iterrows():
        exakt.setdefault(keyf(r), []).append(idx)
        grob.setdefault(grobf(r), []).append(idx)
        if art == 'kalender':
            tag_text.setdefault((r['Mitarbeiter'], r['Start'].date(), _text(r)), []).append(idx)
            tag_text_ohne_ma.setdefault((r['Start'].date(), _text(r)), []).append(idx)
    alt_k = alt_df[alt_df['Korrektur'].notna() & (alt_df['Korrektur'] != '')]
    # Version 6: gleiche Korrektur für alle Zeilen eines Schlüssels (z.B. Termin, der in
    # der Vorversion bei zwei Personen stand und jetzt zweimal bei einer Person steht)
    stufen = [(exakt, keyf), (grob, grobf)]
    if art == 'kalender':
        stufen += [(tag_text, lambda r: (r['Mitarbeiter'], r['Start'].date(), _text(r))),
                   (tag_text_ohne_ma, lambda r: (r['Start'].date(), _text(r)))]
    offen_idx = list(alt_k.index)
    for index_map, kf in stufen:
        gruppen = {}
        for ai in offen_idx:
            gruppen.setdefault(kf(alt_k.loc[ai]), []).append(ai)
        noch = []
        for key, ais in gruppen.items():
            ziel = [z for z in (index_map.get(key) or []) if z not in vergeben]
            werte = {alt_k.at[a_, 'Korrektur'] for a_ in ais}
            if ziel and len(werte) == 1:
                # höchstens so viele Zeilen wie in der Vorversion (sonst würde ein Termin,
                # der neu in zwei Kalendern steht, doppelt gezählt); gleicher Kalendertyp zuerst
                if art == 'kalender' and 'Kalendertyp' in neu.columns:
                    typen = [alt_k.at[a_, 'Kalendertyp'] for a_ in ais]
                    ziel = sorted(ziel, key=lambda z: 0 if neu.at[z, 'Kalendertyp'] in typen else 1)
                for z in ziel[:len(ais)]:
                    neu.at[z, 'Korrektur'] = next(iter(werte))
                    vergeben.add(z)
            elif ziel and len(ziel) == len(ais) == 1:
                neu.at[ziel[0], 'Korrektur'] = alt_k.at[ais[0], 'Korrektur']
                vergeben.add(ziel[0])
            else:
                noch += ais
        offen_idx = noch
    for ai in offen_idx:
        a = alt_k.loc[ai]
        wer = a['Mitarbeiter'] if art == 'kalender' else a['Fahrer']
        text = (a.get('Betreff') or a.get('Aufgabe') or '') if art == 'kalender' else (a.get('Partner') or '')
        rest.append({'Bereich': 'Korrektur nicht übertragbar', 'Datum': a['Start'], 'Mitarbeiter': wer,
                     'Text': text, 'Projekt': a['Korrektur'],
                     'Grund': (f'Korrektur "{a["Korrektur"]}" aus der Vorversion findet keine eindeutige '
                               'Zeile in den neuen Daten - bitte prüfen/neu eintragen')})
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
    if len(zdf):
        neu_texte = {}
        for _, n in neu['kalender'].iterrows():
            t = _norm(n.get('Betreff') or f"{n.get('Projekt') or ''} {n.get('Aufgabe') or ''}") \
                if isinstance(n.get('Betreff'), str) else _norm(f"{n.get('Projekt') or ''} {n.get('Aufgabe') or ''}")
            neu_texte.setdefault((n['Mitarbeiter'], n['Start']), set()).add(_norm(str(n.get('Aufgabe') or '')))

        def ursache(z):
            txt = str(z['Text'] or '')
            if 'Wochenpauschale' in txt:
                return 'Wochenpauschale (Urlaubs-/Endregel)'
            if z['Bereich'] == 'Fahrt':
                return 'Fahrt neu/anders zugeordnet'
            if z['Bereich'] == 'Zusatzkosten':
                return 'Zusatzkosten geändert'
            if z['Bereich'] == 'Manuelle Zeitbuchung':
                return 'Manuelle Zeitbuchung geändert'
            if z['Art'] == 'Nur in alter Version' and \
                    _norm(txt) in neu_texte.get((z['Mitarbeiter'], z['Datum']), set()):
                return 'Doppelter Termin in Vorversion (jetzt einmal gezählt)'
            if z['Art'] == 'Projekt geändert':
                return 'Zuordnung geändert'
            if z['Art'] == 'Stunden geändert':
                return 'Dauer geändert (z.B. Ganztagespauschale)'
            return 'Termin nur in ' + ('alter' if z['Art'] == 'Nur in alter Version' else 'neuer') + ' Version'
        zdf['Ursache'] = zdf.apply(ursache, axis=1)

    def begruendung(row):
        if len(zdf) == 0:
            return ''
        sel = zdf[(zdf['Monat'] == row['Monat']) &
                  ((zdf['Projekt_alt'] == row['Projekt']) | (zdf['Projekt_neu'] == row['Projekt']))]
        if len(sel) == 0:
            return 'Ursache nicht automatisch erkennbar (z.B. Sonderkalkulation) - bitte begründen'
        teile = [f'{n}× {u}' for u, n in sel.groupby('Ursache').size().items()]
        return '; '.join(teile)
    m['Begruendung'] = m.apply(lambda r: begruendung(r) if r['Abweichung'] else '', axis=1)
    m = m.sort_values(['Abweichung', 'Monat', 'Projekt'], ascending=[False, True, True]).reset_index(drop=True)
    return {'summen': m, 'zeilen': zdf, 'n_abweichungen': int(m['Abweichung'].sum()),
            'alt_label': alt_label, 'bis': bis, 'grenze_monat': grenze}


# ==========================================================================
# Version 6: Reiter Pruefliste und Abgleich_Vormonate
# ==========================================================================
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
    m_alle = abgleich['summen']
    m = m_alle[m_alle['Abweichung']]
    ws.cell(row=5, column=1, value=(f'{int((~m_alle["Abweichung"]).sum())} Monat/Projekt-Kombinationen unverändert ✔ '
                                    '(nicht einzeln aufgeführt). Unten nur die Abweichungen.')).font = ctx['sub_font']
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
    if len(m):
        srow = hr + len(m) + 1
        ws.cell(row=srow, column=1, value='SUMME Abweichungen').font = bold
        for c in (3, 4, 5, 6, 7, 8, 9, 10, 11):
            L = ws.cell(row=1, column=c).column_letter
            cell = ws.cell(row=srow, column=c, value=f'=SUM({L}{hr + 1}:{L}{srow - 1})')
            cell.font = bold
            cell.number_format = '#,##0.00 €' if c in (6, 7, 8) else '#,##0.00'
    z0 = hr + len(m) + 4
    ws.cell(row=z0, column=1, value='Betroffene Einzelzeilen (nur bei Abweichungen)').font = bold
    zh = ['Bereich', 'Art', 'Monat', 'Datum', 'Mitarbeiter', 'Betreff / Partner / Kostenart',
          'Projekt alt', 'Projekt neu', 'Wert alt', 'Wert neu', 'Einheit', 'Ursache', 'Zuordnung_Grund (neu)']
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
                    round(r['Wert_alt'], 2), round(r['Wert_neu'], 2), r['Einheit'], r.get('Ursache', ''),
                    r['Grund_neu']]
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
    regeln = cfg.setdefault('projektname_erkennung', {}).setdefault('stichwort_regeln', {})
    for k, v in vorlage.get('regeln', {}).items():
        if regeln.get(k) != v:
            hinweise.append(f'Neue Stichwort-Regel aus der Prüfliste übernommen: "{k}" -> {v} (in Skill-Config aufnehmen)')
        regeln[k] = v
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
    pfad = os.path.join(output_dir, dateiname_fuer_version(period_label, version_info['version'],
                                                           cfg.get('dateiname_praefix', 'Projektuebersicht')))
    if os.path.exists(pfad):
        raise FileExistsError(f'{pfad} existiert schon - Versionsnummer nicht doppelt vergeben')
    cal = setze_ids(cal.reset_index(drop=True), 'kalender')
    trips = setze_ids(trips.reset_index(drop=True), 'fahrten')
    wb, ctx = build_excel_workbook(cal, trips, cfg, period_label, pfad,
                                   zusatzkosten_vorbelegt=zk, manuelle_zeitbuchungen_vorbelegt=mz,
                                   partner_zuordnung_vorbelegt=_partner_mapping(cfg),
                                   version_info=version_info)
    finalize_workbook(wb, ctx, cal, trips, cfg, abgleich=abgleich, pruef_extra=extra)
    def _hat_ent(r):
        return any(isinstance(r.get(k), str) and r.get(k) for k in ('Korrektur', 'Entscheidung'))
    n_unsicher = int(cal.apply(lambda r: bool(r.get('Unsicher')) and not _hat_ent(r)
                               and not str(r.get('Quelle', 'neu')).startswith('Vorversion'), axis=1).sum()) \
        if len(cal) else 0
    n_unsicher += int(trips.apply(lambda r: bool(r.get('Unsicher_wirksam', False)) and not _hat_ent(r)
                                  and not str(r.get('Quelle', 'neu')).startswith('Vorversion'), axis=1).sum()) \
        if len(trips) else 0
    return {'pfad': pfad, 'version': versionstext(version_info['version']), 'n_unsicher': n_unsicher,
            'n_extra': len(extra), 'abgleich': abgleich, 'kalender': cal, 'fahrten': trips, 'config': cfg}


def ausmisten(cal, trips, config):
    """Version 6.2: Korrekturen ohne Wirkung entfernen - "Unberücksichtigt" bei Zeilen, die
    ohnehin kein Projekt hätten, und Korrekturen, die der automatischen Zuordnung entsprechen."""
    # Bei UNSICHEREN Zeilen ist so eine Korrektur eine echte Bestätigung -> bleibt als "✔ passt".
    cal, trips = cal.copy(), trips.copy()
    n = 0
    for df, auto, uns_col in ((cal, cal['Projekt'] if 'Projekt' in cal.columns else None, 'Unsicher'),
                              (trips, None, 'Unsicher')):
        if 'Korrektur' not in df.columns or len(df) == 0:
            continue
        if auto is None:
            auto = apply_partner_zuordnung(df.assign(Korrektur=None), config)
            uns = auto['Unsicher_wirksam'].astype(bool)
            auto = auto['Projekt']
        else:
            uns = df[uns_col].fillna(False).astype(bool) if uns_col in df.columns else pd.Series(False, index=df.index)
        if 'Entscheidung' not in df.columns:
            df['Entscheidung'] = None
        m = df['Korrektur'].notna() & (((df['Korrektur'] == 'Unberücksichtigt') & auto.isna()) |
                                        (df['Korrektur'] == auto))
        bestaetigt = m & uns
        df.loc[bestaetigt, 'Entscheidung'] = PASST
        n += int((m & ~uns).sum())
        df.loc[m, 'Korrektur'] = None
    return cal, trips, n


def wende_korrekturen_an(df, korrekturen, art):
    """Von der Nutzerin im Chat entschiedene Einzelkorrekturen eintragen (landen sichtbar
    in der Spalte 'Manuelle Projekt-Korrektur'). korrekturen: Liste von dicts
    {bereich: 'kalender'|'fahrten', mitarbeiter, start ('YYYY-MM-DD HH:MM'),
    text (optional, Teil des Betreffs/Partners), korrektur}. Passt ein Eintrag nicht auf
    genau EINE Zeile -> Prüfliste statt raten."""
    df = df.copy()
    if 'Korrektur' not in df.columns:
        df['Korrektur'] = None
    rest = []
    wer_col = 'Mitarbeiter' if art == 'kalender' else 'Fahrer'
    txt_col = 'Betreff' if art == 'kalender' else 'Partner'
    for k in korrekturen or []:
        if k.get('bereich', 'kalender') != art:
            continue
        sel = df[(df[wer_col] == k['mitarbeiter']) & (df['Start'] == pd.Timestamp(k['start']))]
        if k.get('text'):
            sel = sel[sel[txt_col].astype(str).str.contains(k['text'], case=False, regex=False)]
        if len(sel) == 1:
            df.at[sel.index[0], 'Korrektur'] = k['korrektur']
        else:
            rest.append({'Bereich': 'Korrektur aus Chat nicht anwendbar', 'Datum': pd.Timestamp(k['start']),
                         'Mitarbeiter': k['mitarbeiter'], 'Text': k.get('text', ''), 'Projekt': k['korrektur'],
                         'Grund': f'passt auf {len(sel)} Zeilen - bitte von Hand eintragen'})
    return df, rest


def neuaufbau(calendar_specs, autolog_specs, config, period_start, period_end, period_label, output_dir,
              vergleichsdatei=None, version=1, neue_manuelle_zeitbuchungen=None, neue_zusatzkosten=None,
              korrekturen=None, zusatzkosten=None, partner_ueberschreiben=None, fahrten_als_geschaeftlich=None,
              vergleich_bis=None):
    """Kompletter Neuaufbau aus allen Rohdaten (z.B. 'Basis v01').
    vergleichsdatei: die zuletzt freigegebene ALTE Ausgabe (auch Version 5 ohne
    Stempel erlaubt). Daraus werden Zusatzkosten, manuelle Zeitbuchungen,
    Partner-Zuordnung, Stammliste und Korrekturen übernommen; das Prüfblatt
    vergleicht alt gegen neu für alle Monate der alten Datei."""
    import os
    alt = lade_vorlage(vergleichsdatei, config) if vergleichsdatei else None
    cfg, hinweise = _merge_config(config, alt)
    # Entscheidungen der Nutzerin, die die Vorlage übersteuern (z.B. Partner leer statt Unberücksichtigt)
    for k_, v_ in (partner_ueberschreiben or {}).items():
        cfg.setdefault('partner_projekt_zuordnung', {})[k_] = v_
        hinweise.append(f'Partner-Zuordnung lt. Nutzerin: {k_} -> {v_ or "(leer)"}')
    extra = [{'Bereich': 'Hinweis Übernahme', 'Datum': None, 'Mitarbeiter': '', 'Text': h, 'Projekt': '',
              'Grund': 'aus der Vergleichsdatei übernommen - bitte kurz bestätigen'} for h in hinweise]

    cal_all = load_multiple_calendars(calendar_specs, cfg, period_start, period_end)
    pausch = generate_wochenpauschale_rows(cal_all, cfg, period_start, period_end)
    cal = pd.concat([cal_all, pausch], ignore_index=True) if len(pausch) else cal_all
    cal = compute_kalender_kosten(cal, cfg)
    cal = _markiere_dubletten(cal)
    cal['Quelle'] = 'neu'
    trips = _lade_fahrten(autolog_specs, cfg, period_start, period_end)
    offen = offene_fahrten(autolog_specs, cfg, period_start, period_end)
    als_g = {pd.Timestamp(x) for x in (fahrten_als_geschaeftlich or [])}
    if als_g:
        # von der Nutzerin als geschäftlich bestätigte 'Offen'-Fahrten aufnehmen
        roh = [load_autolog_csv(sp['path'], sp['kennzeichen'],
                                {re.sub(r'\s+', '', k).upper(): v for k, v in cfg['fahrzeug_fahrer_zuordnung'].items()
                                 if not k.startswith('_')}.get(re.sub(r'\s+', '', sp['kennzeichen']).upper()),
                                period_start, period_end, nur_geschaeftlich=False) for sp in autolog_specs]
        roh = pd.concat(roh, ignore_index=True)
        dazu = roh[roh['Start'].isin(als_g) & (roh['Fahrtart'] != 'Geschäftlich')]
        trips = pd.concat([trips, dazu], ignore_index=True)
        offen = [o_ for o_ in offen if pd.Timestamp(o_['Datum']) not in als_g]
    extra += offen
    trips = trips.drop_duplicates(subset=['Fahrer', 'Start', 'Ende', 'Distanz (km)', 'Partner']).reset_index(drop=True)
    trips = _match_alle(trips, cal, cfg)
    trips['Quelle'] = 'neu'
    zk = alt['zusatzkosten'] if alt else pd.DataFrame(columns=['Datum', 'Projekt', 'Kostenart', 'Betrag_EUR', 'Anmerkung'])
    if zusatzkosten is not None:
        zk = zusatzkosten
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
    cal, r3 = wende_korrekturen_an(cal, korrekturen, 'kalender')
    trips, r4 = wende_korrekturen_an(trips, korrekturen, 'fahrten')
    extra += r3 + r4
    cal = compute_kalender_kosten(cal, cfg)   # Ganztagespauschale/Kosten mit übernommenen Korrekturen
    cal, trips, n_weg = ausmisten(cal, trips, cfg)
    if n_weg:
        extra.append({'Bereich': 'Hinweis Übernahme', 'Datum': None, 'Mitarbeiter': '', 'Projekt': '',
                      'Text': f'{n_weg} überflüssige Korrekturen entfernt (Unberücksichtigt bei Terminen ohne Projekt '
                              'bzw. Korrektur = automatische Zuordnung)', 'Grund': 'ohne Wirkung auf Summen'})
    trips = apply_partner_zuordnung(trips, cfg)
    trips = compute_fahrten_kosten(trips, cfg)

    abgleich = None
    if alt:
        neu = {'kalender': cal, 'fahrten': trips, 'zusatzkosten': zk, 'manuelle_zeitbuchungen': mz}
        cfg_alt, _ = _merge_config(config, alt)
        meta = alt['meta']
        label = (f'{os.path.basename(vergleichsdatei)}'
                 + (f' ({versionstext(meta["version_nr"])})' if meta.get('version_nr') else ' (ohne Versionsstempel)'))
        bis_ = meta.get('datenstand_bis') or (pd.Timestamp(vergleich_bis) if vergleich_bis else None)
        abgleich = vergleiche_versionen(alt, neu, cfg_alt, cfg, bis=bis_, alt_label=label)
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


# ==========================================================================
# Version 6.3 (Entwurf): externer Kundenbericht (z.B. TransCare) - nur Werte
# ==========================================================================
def _ort(adresse):
    """Nur der Ort aus einer Adresse ('Fuhrmannstraße 10, 94405 Landau an der Isar' -> 'Landau an der Isar')."""
    if not isinstance(adresse, str):
        return '-'
    m = re.search(r'\b\d{4,5}\s+([^,]+)', adresse)
    return m.group(1).strip() if m else '-'


def erstelle_kundenbericht(fuexle_pfad, config, projekte, output_dir, firma='TransCare', interne=None,
                           nur_freigegeben=True, pdf=True):
    """Externer Bericht für einen Kunden: NUR feste Werte, keine Formeln/Rohdaten/internen Infos.
    projekte: Liste der Projekte, die der Kunde sehen soll (je Bericht frei wählbar).
    interne: optional Liste interner Positionen (z.B. 'Vor-Ort Termine i. Auftrag TC'), eigener Block.
    Kumuliert seit Projektbeginn bis zum Datenstand der (freigegebenen) Füxle, plus 'davon im Berichtsmonat'.
    Leistungsnachweis je Projekt: Kalenderzeiten (Hauptaufgabe statt Betreff), manuelle Zeiten,
    Fahrten (nur Orte), Zusatzkosten. Summen werden gegen summen_je_monat_projekt() geprüft."""
    import os
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    meta = lese_berichtsversion(fuexle_pfad)
    if nur_freigegeben and (meta.get('legacy') or not meta.get('freigegeben_am')):
        raise VorlageFehler('Kundenbericht nur aus einer FREIGEGEBENEN Füxle-Datei (Cockpit: Freigegeben am/von).')
    daten = lade_vorlage(fuexle_pfad, config)
    cfg, _ = _merge_config(config, daten)
    bis = meta.get('datenstand_bis')
    bm = pd.Timestamp(bis).strftime('%Y-%m') if bis is not None else None
    interne = list(interne or [])
    auswahl = list(projekte) + interne
    for p_ in projekte:
        f_ = _projekt_firma(p_, cfg)
        if f_ != firma:
            raise ValueError(f'Projekt "{p_}" gehört zu "{f_}", nicht zu {firma} - bitte Auswahl prüfen')
    mwst = cfg.get('mwst_satz_prozent', 19) / 100.0
    kuerzel = {m: v['kuerzel'] for m, v in cfg['mitarbeiter_satzhistorie'].items() if not m.startswith('_')}

    # ---- Einzelpositionen
    pos = []
    cal = daten['kalender'].copy()
    cal['P'] = cal.apply(_wirksames_projekt_kalender, axis=1)
    for _, r in cal[cal['P'].isin(auswahl)].iterrows():
        if _ist_blocker(r) or float(r['Dauer_h']) <= 0 or (bis is not None and r['Start'] > bis):
            continue
        pos.append({'Projekt': r['P'], 'Art': 'Zeit', 'Datum': r['Start'],
                    'Zeit': 'Pauschale' if bool(r['Ist_Pauschale']) else (
                        f"{r['Start']:%H:%M}–{r['Ende']:%H:%M}" if r['Ende'].date() == r['Start'].date() else
                        f"bis {r['Ende']:%d.%m.}"),
                    'Person': kuerzel.get(r['Mitarbeiter'], '?'), 'Leistung': r['Hauptaufgabe'],
                    'Menge': float(r['Dauer_h']), 'Einheit': 'Std.', 'Satz': float(r['Stundensatz_EUR'] or 0),
                    'Netto': _kosten_zeit_zeile(r, cfg)})
    mz = daten.get('manuelle_zeitbuchungen')
    if mz is not None and len(mz):
        m = prepare_manuelle_zeitbuchungen(mz, cfg)
        for _, r in m[m['Projekt'].isin(auswahl)].iterrows():
            if bis is not None and r['Datum'] > bis:
                continue
            pos.append({'Projekt': r['Projekt'], 'Art': 'Zeit', 'Datum': r['Datum'], 'Zeit': 'nachgetragen',
                        'Person': kuerzel.get(r['Mitarbeiter'], '?'), 'Leistung': r['Hauptaufgabe'],
                        'Menge': float(r['Stunden']), 'Einheit': 'Std.', 'Satz': float(r['Stundensatz_EUR']),
                        'Netto': float(r['Kosten_Zeit_EUR'])})
    tr = apply_partner_zuordnung(daten['fahrten'], cfg) if len(daten['fahrten']) else daten['fahrten']
    ohne = {p for p, sk in cfg.get('sonderkalkulationen', {}).items()
            if not p.startswith('_') and isinstance(sk, dict) and sk.get('fahrten_kostentechnisch_ausschliessen')}
    for _, r in (tr[tr['Projekt'].isin(auswahl)].iterrows() if len(tr) else []):
        if bis is not None and r['Start'] > bis:
            continue
        km = pd.to_numeric(r['Distanz (km)'], errors='coerce')
        km = float(km) if pd.notna(km) else 0.0
        satz = float(r['KmSatz_EUR'] or 0)
        netto = 0.0 if (r['Projekt'] in ohne and sonderkalk_gilt(r['Projekt'], r['Fahrer'], cfg)) else km * satz
        pos.append({'Projekt': r['Projekt'], 'Art': 'Fahrt', 'Datum': r['Start'], 'Zeit': f"{r['Start']:%H:%M}",
                    'Person': kuerzel.get(r['Fahrer'], '?'),
                    'Leistung': f"Fahrt {_ort(r.get('Start-Adresse'))} → {_ort(r.get('End-Adresse'))}",
                    'Menge': km, 'Einheit': 'km', 'Satz': satz, 'Netto': round(netto, 2)})
    zk = daten.get('zusatzkosten')
    if zk is not None and len(zk):
        for _, r in zk[zk['Projekt'].isin(auswahl)].iterrows():
            d = pd.to_datetime(r['Datum'], dayfirst=True, errors='coerce')
            if bis is not None and d > bis:
                continue
            pos.append({'Projekt': r['Projekt'], 'Art': 'Zusatzkosten', 'Datum': d, 'Zeit': '', 'Person': '',
                        'Leistung': str(r['Kostenart'] or 'Zusatzkosten'), 'Menge': 1, 'Einheit': 'pauschal',
                        'Satz': float(r['Betrag_EUR'] or 0), 'Netto': float(r['Betrag_EUR'] or 0)})
    pdf_ = pd.DataFrame(pos)
    if len(pdf_) == 0:
        raise ValueError('Für die Auswahl gibt es keine Positionen bis zum Datenstand.')
    pdf_['Monat'] = pdf_['Datum'].dt.strftime('%Y-%m')
    pdf_ = pdf_.sort_values(['Projekt', 'Datum', 'Art'])

    # ---- Kontrolle gegen die Füxle-Logik (muss exakt passen)
    s = summen_je_monat_projekt(daten, cfg, statische_kosten=True)
    if bm:
        s = s[s['Monat'] <= bm]
    for p_ in auswahl:
        soll = float(s[s['Projekt'] == p_]['Kosten'].sum())
        ist = float(pdf_[pdf_['Projekt'] == p_]['Netto'].sum())
        if abs(soll - ist) > 0.01:
            raise ValueError(f'Kontrolle fehlgeschlagen für {p_}: Bericht {ist:.2f} € ≠ Füxle {soll:.2f} € - nicht versenden')

    # ---- Excel (nur Werte)
    wb = Workbook()
    F = 'Arial'
    hf, hfont = PatternFill('solid', fgColor='1F3864'), Font(name=F, bold=True, color='FFFFFF', size=10)
    nf, bf = Font(name=F, size=10), Font(name=F, size=10, bold=True)
    thin = Side(style='thin', color='BFBFBF')
    brd = Border(left=thin, right=thin, top=thin, bottom=thin)
    sumfill = PatternFill('solid', fgColor='EBF0FA')
    eur = '#,##0.00 €'

    def kopf(ws, row, werte):
        for c, v in enumerate(werte, start=1):
            cell = ws.cell(row=row, column=c, value=v)
            cell.fill = hf; cell.font = hfont; cell.border = brd
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

    ws = wb.active
    ws.title = 'Übersicht'
    ws['A1'] = f'Neininger GmbH – Leistungsübersicht für {firma}'
    ws['A1'].font = Font(name=F, bold=True, size=14, color='1F3864')
    ws['A2'] = (f"Kumuliert seit Projektbeginn bis {pd.Timestamp(bis):%d.%m.%Y}"
                f" · Berichtsmonat {pd.Timestamp(bis):%m/%Y} · Stand {meta.get('version')} vom "
                f"{meta.get('erstellt_am') or ''} · alle Beträge in EUR")
    ws['A2'].font = Font(name=F, italic=True, size=9, color='808080')
    spalten = ['Projekt', 'Beginn', 'Stunden', 'Kosten Zeit (netto)', 'km', 'Kosten Fahrt (netto)',
               'Zusatzkosten (netto)', 'Gesamt netto', f'MwSt. {int(mwst * 100)} %', 'Gesamt brutto',
               'davon im Berichtsmonat (netto)']

    def block(titel, liste, start):
        ws.cell(row=start, column=1, value=titel).font = bf
        kopf(ws, start + 1, spalten)
        r0 = start + 2
        for i, p_ in enumerate(liste):
            d = pdf_[pdf_['Projekt'] == p_]
            row = r0 + i
            zeit, fahrt, zus = (d[d['Art'] == a] for a in ('Zeit', 'Fahrt', 'Zusatzkosten'))
            netto = round(d['Netto'].sum(), 2)
            vals = [p_, d['Datum'].min().strftime('%m/%Y') if len(d) else '-', round(zeit['Menge'].sum(), 2),
                    round(zeit['Netto'].sum(), 2), round(fahrt['Menge'].sum(), 1), round(fahrt['Netto'].sum(), 2),
                    round(zus['Netto'].sum(), 2), netto, round(netto * mwst, 2), round(netto * (1 + mwst), 2),
                    round(d[d['Monat'] == bm]['Netto'].sum(), 2)]
            for c, v in enumerate(vals, start=1):
                cell = ws.cell(row=row, column=c, value=v)
                cell.font = nf; cell.border = brd
                cell.number_format = eur if c in (4, 6, 7, 8, 9, 10, 11) else ('#,##0.00' if c == 3 else '#,##0')
                if c == 1:
                    cell.alignment = Alignment(wrap_text=True, vertical='top')
        sr = r0 + len(liste)
        ws.cell(row=sr, column=1, value='Summe').font = bf
        for c in range(3, len(spalten) + 1):
            vals = [ws.cell(row=r_, column=c).value or 0 for r_ in range(r0, sr)]
            cell = ws.cell(row=sr, column=c, value=round(sum(vals), 2))
            cell.font = bf; cell.fill = sumfill; cell.border = brd
            cell.number_format = eur if c in (4, 6, 7, 8, 9, 10, 11) else '#,##0.00'
        return sr
    ende = block('Projekte', [p_ for p_ in projekte if (pdf_['Projekt'] == p_).any()], 4)
    if interne:
        ende = block('Interne TransCare-Positionen', [p_ for p_ in interne if (pdf_['Projekt'] == p_).any()], ende + 2)
    for i, w in enumerate([30, 9, 10, 16, 9, 16, 14, 15, 13, 15, 16], start=1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.oddFooter.right.text = 'Seite &P von &N'

    # Leistungsnachweis: ein Reiter, je Projekt ein Abschnitt mit Zwischensumme
    ln = wb.create_sheet('Leistungsnachweis')
    ln['A1'] = f'Leistungsnachweis {firma} – bis {pd.Timestamp(bis):%d.%m.%Y}'
    ln['A1'].font = Font(name=F, bold=True, size=13, color='1F3864')
    ln['A2'] = 'Personen: ' + ', '.join(f'{k} = {m}' for m, k in kuerzel.items())
    ln['A2'].font = Font(name=F, italic=True, size=9, color='808080')
    row = 4
    for p_ in [x for x in auswahl if (pdf_['Projekt'] == x).any()]:
        d = pdf_[pdf_['Projekt'] == p_]
        ln.cell(row=row, column=1, value=p_).font = Font(name=F, bold=True, size=11, color='1F3864')
        row += 1
        kopf(ln, row, ['Datum', 'Zeit', 'Person', 'Leistung', 'Menge', 'Einheit', 'Satz', 'Netto'])
        row += 1
        for _, r in d.iterrows():
            vals = [r['Datum'].strftime('%d.%m.%Y'), r['Zeit'], r['Person'], r['Leistung'],
                    round(r['Menge'], 2), r['Einheit'], r['Satz'], round(r['Netto'], 2)]
            for c, v in enumerate(vals, start=1):
                cell = ln.cell(row=row, column=c, value=v)
                cell.font = nf; cell.border = brd
                if c in (7, 8):
                    cell.number_format = eur
            row += 1
        ln.cell(row=row, column=4, value=f'Summe {p_}').font = bf
        c_ = ln.cell(row=row, column=8, value=round(d['Netto'].sum(), 2))
        c_.font = bf; c_.number_format = eur; c_.fill = sumfill
        row += 2
    for i, w in enumerate([11, 12, 7, 52, 9, 8, 11, 13], start=1):
        ln.column_dimensions[get_column_letter(i)].width = w
    ln.page_setup.orientation = 'portrait'
    ln.page_setup.fitToWidth = 1
    ln.page_setup.fitToHeight = 0
    ln.sheet_properties.pageSetUpPr.fitToPage = True
    ln.print_title_rows = '1:2'
    ln.oddFooter.right.text = 'Seite &P von &N'

    os.makedirs(output_dir, exist_ok=True)
    name = f"{cfg.get('dateiname_praefix', 'Projektuebersicht')}_{firma}_{pd.Timestamp(bis):%Y-%m}"
    xlsx = os.path.join(output_dir, name + '.xlsx')
    wb.save(xlsx)
    out = {'xlsx': xlsx, 'pdf': None, 'positionen': pdf_}
    if pdf:
        import subprocess
        subprocess.run(['soffice', '--headless', '--convert-to', 'pdf', '--outdir', output_dir, xlsx],
                       capture_output=True, timeout=180)
        p = os.path.join(output_dir, name + '.pdf')
        out['pdf'] = p if os.path.exists(p) else None
    return out
