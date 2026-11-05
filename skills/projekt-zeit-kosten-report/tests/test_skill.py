"""Automatische Tests für Skill-Version 6 (erfundene Testdaten, siehe testdaten.py).

Aufruf:  python -m pytest tests -v
"""
import shutil
from datetime import datetime

import openpyxl
import pandas as pd
import pytest

from conftest import (BASIS_ENDE, BASIS_START, NOV_ENDE, config, entscheide, freigeben, lade_v5,
                      pruefliste, rl, td, uebersicht_summen)


# --------------------------------------------------------------- S2: Erkennung
@pytest.mark.parametrize('betreff, projekt, unsicher, grund_teil', [
    ('"Koko" Dokumentenerstellung', 'Koko', False, 'Projektname im Betreff'),
    ('"Sand" Abstimmung', 'Sandformation', False, 'Alias Sand'),
    ('"sand" Abstimmung', 'Sandformation', True, 'Schreibweise angeglichen'),
    ('„Koko“ Unterlagen', 'Koko', False, 'typografische'),
    ('“Koko” Unterlagen', 'Koko', False, 'typografische'),
    ('"Fantasia" Kennenlernen', 'Fantasia', True, 'Unbekannter Projektname'),
    ('"Koko" und "Cool" gemeinsam', 'Koko', True, 'weitere Namen'),
    ('Spedition Niedermaier Woche', 'Spedition Niedermaier', False, 'Fester Name'),
    ('"Auf Herdenen" Treffen', 'Auf Herdenen', False, 'Ignoriert'),
    ('Abstimmung Zeppelin Unterlagen', None, True, 'NICHT zugeordnet'),
    ('Urlaub Juli', None, False, 'Kein Projektname erkannt'),
    ('Termin Hessenmühle', None, False, 'Kein Projektname erkannt'),
])
def test_erkennung_mit_grund(betreff, projekt, unsicher, grund_teil):
    r = rl.erkenne_projekt(betreff, config())
    assert r['projekt'] == projekt
    assert r['unsicher'] is unsicher
    assert grund_teil in r['grund']


def test_jede_zeile_hat_einen_grund(szenario):
    for key in ('v01', 'v02'):
        ws = openpyxl.load_workbook(szenario[key]['pfad'])['Rohdaten_Kalender']
        kopf = [c.value for c in ws[1]]
        g = kopf.index('Zuordnung_Grund')
        assert all(r[g] for r in ws.iter_rows(min_row=2, values_only=True)), key
        ws = openpyxl.load_workbook(szenario[key]['pfad'])['Rohdaten_Fahrten']
        kopf = [c.value for c in ws[1]]
        g = kopf.index('Zuordnung_Grund')
        assert all(r[g] for r in ws.iter_rows(min_row=2, values_only=True)), key


def test_unsichere_faelle_gelb_und_auf_pruefliste(szenario):
    wb = openpyxl.load_workbook(szenario['v01']['pfad'])
    rk = wb['Rohdaten_Kalender']
    kopf = [c.value for c in rk[1]]
    p = kopf.index('Prüfen')
    gelbe = [r for r in range(2, rk.max_row + 1) if rk.cell(row=r, column=p + 1).value]
    assert len(gelbe) == 3            # Niedermaier-Block, Kurztermin, "Fantasia"
    for r in gelbe:
        assert rk.cell(row=r, column=1).fill.fgColor.rgb.endswith('FFE699')
    offen = [e for e in pruefliste(szenario['v01']['pfad']) if e['Thema'] == 'unsicher - bitte entscheiden']
    assert len(offen) == 4            # + Fahrt mit zwei Projekten fast gleich nah
    assert any('ähnlich nah' in (e['Grund'] or '') for e in offen)
    assert offen[0]['Wirkung (€)'] >= offen[-1]['Wirkung (€)']     # teuerste zuerst


def test_fahrt_mehrdeutig_wird_markiert_nicht_geaendert(szenario):
    t = szenario['v01']['fahrten']
    r = t[t['Partner'] == 'Forst Partner'].iloc[0]
    assert r['Projekt'] == 'Forst' and bool(r['Unsicher_wirksam'])


def test_unberuecksichtigt_gewinnt_und_bleibt_sichtbar(szenario):
    t = szenario['v01']['fahrten']
    r = t[t['Partner'] == 'Vermietung'].iloc[0]
    assert pd.isna(r['Projekt']) and r['Projekt_Kalender'] == 'Hentzen'
    assert 'hat Vorrang' in r['Zuordnung_Grund_wirksam']


def test_niedermaier_nur_markiert_zahlen_unveraendert(szenario, recalced):
    res, pfad = recalced(szenario['v01']['pfad'])
    s = uebersicht_summen(pfad)
    # 3 Tage x 1750 + 3 Nächte x 150 + 2 x 825 Anfahrtspauschale (Block-KW + Telefonat-KW) = wie Version 5
    assert s['Spedition Niedermaier']['kosten'] == pytest.approx(7350.0)


# --------------------------------------------------------------- S1: Versionsregel
def test_dateiname_und_versionsblock(szenario):
    assert szenario['v01']['pfad'].endswith('Füxle_2026-10_v01.xlsx')
    assert szenario['v02']['pfad'].endswith('Füxle_2026-11_v02.xlsx')
    m = rl.lese_berichtsversion(szenario['v02']['pfad'])
    assert m['version'] == 'v02' and m['vorgaenger'] == 'v01'
    assert m['datenstand_bis'].date() == NOV_ENDE.date()


def test_aeltere_vorlage_wird_gestoppt(szenario):
    freigeben(szenario['v02']['pfad'])
    with pytest.raises(rl.VorlageFehler, match='ÄLTER'):
        rl.pruefe_vorlage(szenario['v01']['pfad'], 'v02')
    with pytest.raises(rl.VorlageFehler, match='ÄLTER'):
        rl.fortfuehrung(szenario['v01']['pfad'], 'v02', szenario['cs_n'], szenario['al_n'], szenario['cfg'],
                        datetime(2026, 12, 31, 23, 59), '2026-12', str(szenario['dir'] / 'stopp'))
    assert not (szenario['dir'] / 'stopp').exists()      # nichts still weitergerechnet


def test_neuere_als_genannte_vorlage_wird_gestoppt(szenario):
    with pytest.raises(rl.VorlageFehler, match='NEUER'):
        rl.pruefe_vorlage(szenario['v02']['pfad'], 'v01')


def test_ohne_freigabe_gestoppt(tmp_path):
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'))
    with pytest.raises(rl.VorlageFehler, match='Freigabevermerk'):
        rl.pruefe_vorlage(r['pfad'], 'v01')


def test_umbenannte_datei_gestoppt(szenario, tmp_path):
    falsch = tmp_path / 'Füxle_2026-10_v05.xlsx'
    shutil.copy(szenario['v01']['pfad'], falsch)
    with pytest.raises(rl.VorlageFehler, match='Dateinamen'):
        rl.pruefe_vorlage(falsch, 'v05')


def test_alte_datei_ohne_stempel_gestoppt(tmp_path):
    v5 = lade_v5()
    pfad = _baue_v5(v5, tmp_path)
    with pytest.raises(rl.VorlageFehler, match='kein Versionsstempel'):
        rl.pruefe_vorlage(pfad, 'v01')


def test_mehrere_kandidaten_nur_die_richtige(szenario):
    assert rl.waehle_vorlage([szenario['v01']['pfad'], szenario['v02']['pfad']], 'v02') == szenario['v02']['pfad']
    with pytest.raises(rl.VorlageFehler):
        rl.waehle_vorlage([szenario['v01']['pfad']], 'v02')


# --------------------------------------------------------------- S1: Fortführung + Prüfblatt
def test_abgleich_vormonate_unveraendert(szenario):
    ab = szenario['v02']['abgleich']
    assert ab['n_abweichungen'] == 0
    ws = openpyxl.load_workbook(szenario['v02']['pfad'])['Abgleich_Vormonate']
    assert ws['A4'].value == 'Vormonate unverändert ✔'


def test_keine_dubletten_bei_fortfuehrung(szenario):
    cal = szenario['v02']['kalender']
    echte = cal[cal['Kalendertyp'] != 'Pauschale']
    assert not echte.duplicated(subset=['Mitarbeiter', 'Start', 'Ende', 'Aufgabe']).any()
    assert len(echte) == len(szenario['v01']['kalender'][szenario['v01']['kalender']['Kalendertyp'] != 'Pauschale']) + 2
    t = szenario['v02']['fahrten']
    assert len(t) == len(td.FAHRTEN_BASIS) + 1          # Okt-Überlappung + doppelte Nov-Zeile nicht doppelt
    pa = szenario['v02']['kalender']
    assert (pa['Kalendertyp'] == 'Pauschale').sum() == 8 + 5   # Sep/Okt 8 Montage + Nov 5 Montage (2.,9.,16.,23.,30.)


def test_nachtrag_im_vormonat_nicht_still_uebernommen(szenario):
    cal = szenario['v02']['kalender']
    assert not (cal['Start'] == pd.Timestamp('2026-10-30 09:00')).any()
    assert any('Nachtrag Vormonat' in (e['Thema'] or '') for e in pruefliste(szenario['v02']['pfad']))


def test_handeintraege_bleiben_erhalten(szenario):
    alt = rl.lade_vorlage(szenario['v01']['pfad'], szenario['cfg'])
    neu = rl.lade_vorlage(szenario['v02']['pfad'], szenario['cfg'])
    assert len(alt['zusatzkosten']) == 2 and len(neu['zusatzkosten']) == 2   # früher: erste Zeile weg
    assert len(neu['manuelle_zeitbuchungen']) == 1                           # früher: 0
    assert neu['partner_zuordnung'].get('Koko Partner') == 'Koko'            # früher: {}
    k = neu['kalender']
    assert k.loc[k['Aufgabe'] == 'Montagssitzung intern', 'Korrektur'].iloc[0] == 'Cool'


def test_korrektur_wirkt_auf_kosten(szenario, recalced):
    """Bug Version 5: korrigierter unerkannter Termin -> Stunden ja, Kosten 0 €."""
    res, pfad = recalced(szenario['v02']['pfad'])
    ws = openpyxl.load_workbook(pfad, data_only=True)['Rohdaten_Kalender']
    for r in ws.iter_rows(min_row=2, values_only=True):
        if r[13] == 'Montagssitzung intern':
            assert r[4] == 'Cool' and r[12] == pytest.approx(200.0)
            break
    else:
        pytest.fail('Zeile nicht gefunden')


def test_abweichung_wird_gezeigt_mit_zeile(szenario, tmp_path):
    """Neuaufbau mit einem zusätzlichen September-Termin gegen v01: Prüfblatt rot + Einzelzeile."""
    cfg = config()
    extra = ('"Koko" Zusatztermin', '2026-09-09 09:00', '2026-09-09 10:00')
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS + [extra])
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'),
                     vergleichsdatei=szenario['v01']['pfad'], version=1)
    ab = r['abgleich']
    abw = ab['summen'][ab['summen']['Abweichung']]
    # 2026-09/Koko (Zusatztermin) und 2026-10/Cool (Korrektur aus v01 wird übertragen -> gleich)
    assert set(zip(abw['Monat'], abw['Projekt'])) == {('2026-09', 'Koko')}
    z = ab['zeilen']
    assert len(z) == 1 and z.iloc[0]['Art'] == 'Nur in neuer Version' and 'Zusatztermin' in z.iloc[0]['Text']
    ws = openpyxl.load_workbook(r['pfad'])['Abgleich_Vormonate']
    assert ws['A4'].value.startswith('1 Abweichungen')


# --------------------------------------------------------------- Auslastung entfernt
def test_auslastung_entfernt(szenario):
    assert 'soll_arbeitszeit_pro_woche' not in config()
    wb = openpyxl.load_workbook(szenario['v01']['pfad'])
    for ws in wb.worksheets:
        for row in ws.iter_rows(values_only=True):
            for v in row:
                assert not (isinstance(v, str) and ('Soll-Std' in v or 'Auslastung' in v)), (ws.title, v)
    assert 'Interne_Auswertung' in wb.sheetnames          # Stunden je Person bleiben (Nutzerin)


def test_stundensaetze_im_parameter_nicht_ueberschrieben(szenario):
    ws = openpyxl.load_workbook(szenario['v01']['pfad'])['Stammdaten']
    assert [ws.cell(row=r, column=4).value for r in (5, 6, 7)] == [200, 150, 150]


# --------------------------------------------------------------- Formeln + Konsistenz
@pytest.mark.parametrize('key', ['v01', 'v02'])
def test_null_formelfehler(szenario, recalced, key):
    res, _ = recalced(szenario[key]['pfad'])
    assert res.get('status') == 'success' and res['total_errors'] == 0, res


@pytest.mark.parametrize('key', ['v01', 'v02'])
def test_excel_summen_gleich_python_summen(szenario, recalced, key):
    """Übersicht (Excel-Formeln) == summen_je_monat_projekt (Python, Grundlage des Prüfblatts)."""
    res, pfad = recalced(szenario[key]['pfad'])
    excel = uebersicht_summen(pfad)
    r = szenario[key]
    daten = rl.lade_vorlage(r['pfad'], r['config'])
    py = rl.summen_je_monat_projekt(daten, r['config']).groupby('Projekt')[['Std', 'Kosten', 'km']].sum()
    for proj, w in excel.items():
        p = py.loc[proj] if proj in py.index else {'Std': 0, 'Kosten': 0, 'km': 0}
        assert w['std'] == pytest.approx(p['Std'], abs=0.01), proj
        assert w['kosten'] == pytest.approx(p['Kosten'], abs=0.01), proj
        assert w['km'] == pytest.approx(p['km'], abs=0.01), proj


# --------------------------------------------------------------- Regression gegen Version 5
def _baue_v5(v5, verz, marius=td.MARIUS_BASIS):
    cfg = v5.load_config(str(rl.__file__).replace('scripts/report_lib.py', 'tests/referenz/config_v5.json'))
    cs, al = td.specs(verz, marius, tag='v5')
    cal = v5.load_multiple_calendars(cs, cfg, BASIS_START, BASIS_ENDE)
    cal = pd.concat([cal, v5.generate_wochenpauschale_rows(cal, cfg, BASIS_START, BASIS_ENDE)], ignore_index=True)
    cal = v5.compute_kalender_kosten(cal, cfg)
    trips = v5.load_autolog_csv(al[0]['path'], 'VS MN 1000', td.MN, BASIS_START, BASIS_ENDE)
    trips = v5.match_trips_to_calendar(trips, cal, td.MN)
    trips = v5.apply_partner_zuordnung(trips, cfg)
    trips = v5.compute_fahrten_kosten(trips, cfg)
    pfad = str(verz / 'Projektuebersicht_2026-10.xlsx')
    wb, ctx = v5.build_excel_workbook(cal, trips, cfg, '2026-10', pfad)
    v5.finalize_workbook(wb, ctx, cal, trips, cfg)
    return pfad


def test_regression_summen_je_projekt_wie_version5(szenario, recalced, tmp_path):
    pfad5 = _baue_v5(lade_v5(), tmp_path)
    res5, rc5 = recalced(pfad5)
    assert res5['total_errors'] == 0
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS, tag='v6')
    r6 = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'v6'))
    res6, rc6 = recalced(r6['pfad'])
    s5, s6 = uebersicht_summen(rc5, 'Gesamt_Alle_Jahre'), uebersicht_summen(rc6)
    assert set(s5) == set(s6)
    for proj in s5:
        assert s6[proj]['kosten'] == pytest.approx(s5[proj]['kosten'], abs=0.005), proj
        assert s6[proj]['km'] == pytest.approx(s5[proj]['km'], abs=0.005), proj
        # Version 5 hat Dauer_h auf 2 Nachkommastellen gerundet abgelegt (0,33 statt 0,333 h)
        assert s6[proj]['std'] == pytest.approx(s5[proj]['std'], abs=0.01), proj


def test_neuaufbau_gegen_version5_datei(tmp_path, recalced):
    """Basis-Szenario: alte Datei (Version 5) als Vergleich -> Übernahme + Abgleich funktionieren."""
    pfad5 = _baue_v5(lade_v5(), tmp_path, td.MARIUS_BASIS + td.MARIUS_FEHLERFAELLE)
    wb = openpyxl.load_workbook(pfad5)
    zk = wb['Zusatzkosten']
    for c, v in enumerate([datetime(2026, 9, 3), 'Cool', 'Hotel', 120.0, 'x'], start=1):
        zk.cell(row=5, column=c, value=v)
    wb.save(pfad5)
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS + td.MARIUS_FEHLERFAELLE, tag='basis6')
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'),
                     vergleichsdatei=pfad5)
    ab = r['abgleich']
    assert len(rl.lade_vorlage(r['pfad'], cfg)['zusatzkosten']) == 1
    # Abweichungen NUR durch die behobenen Fehler: typografisch -> Koko (Version 5: kein Projekt),
    # "sand" -> Sandformation (Version 5: Phantomprojekt "sand")
    abw = set(zip(ab['summen'][ab['summen']['Abweichung']]['Monat'],
                  ab['summen'][ab['summen']['Abweichung']]['Projekt']))
    assert abw == {('2026-10', 'Koko'), ('2026-10', 'Sandformation'), ('2026-10', 'sand')}
    z = ab['zeilen']
    assert set(z['Art']) == {'Projekt geändert'} and len(z) == 2
    res, _ = recalced(r['pfad'])
    assert res['total_errors'] == 0


def test_dublette_zwischen_zwei_kalendern_markiert(tmp_path):
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS, jennifer=td.JENNIFER_BASIS + [td.JENNIFER_DUBLETTE],
                      jennifer2=[td.JENNIFER_DUBLETTE])
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'))
    c = r['kalender']
    d = c[c['Aufgabe'] == 'Projektplanung']
    assert len(d) == 2 and d['Unsicher'].sum() == 1
    assert 'Mögliche Dublette' in d[d['Unsicher']].iloc[0]['Zuordnung_Grund']


def test_monat_formel_ohne_yyyy(szenario):
    """Bug Füxle-Datei: TEXT(..;"YYYY-MM") liefert in deutschem Excel "YYYY-05"."""
    wb = openpyxl.load_workbook(szenario['v01']['pfad'])
    for blatt in ('Zusatzkosten', 'Manuelle_Zeitbuchungen'):
        for row in wb[blatt].iter_rows():
            for c in row:
                assert not (isinstance(c.value, str) and 'YYYY' in c.value), (blatt, c.coordinate)


def test_offene_fahrt_kommt_auf_pruefliste(tmp_path):
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    with open(al[0]['path'], 'a', encoding='utf-8') as f:
        f.write('VS MN 1000;30.09.26 11:52;30.09.26 15:19;333;Offen;;;;Landau;Überlingen\n')
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'))
    assert any(e['Thema'] == 'Fahrt nicht klassifiziert' for e in pruefliste(r['pfad']))


def test_sonderkalk_nur_fuer_marius():
    cfg = config()
    assert rl.sonderkalk_gilt('Spedition Niedermaier', td.MN, cfg)
    assert not rl.sonderkalk_gilt('Spedition Niedermaier', td.FS, cfg)
    r = {'Projekt': 'Spedition Niedermaier', 'Korrektur': None, 'Mitarbeiter': td.FS, 'Mehrtaegig': False,
         'Ist_Pauschale': False, 'Dauer_h': 0.25, 'Stundensatz_EUR': 150}
    assert rl._kosten_zeit_zeile(r, cfg) == pytest.approx(37.5)
    assert rl.erkenne_projekt('Telefonat Kochtrans "Niedermaier"', cfg)['projekt'] == 'Spedition Niedermaier'


def test_urlaub_nur_eigener():
    cfg = config()
    assert rl.ist_eigener_urlaub('Marius Urlaub', td.MN, cfg)
    assert rl.ist_eigener_urlaub('Urlaub', td.MN, cfg)
    assert not rl.ist_eigener_urlaub('Felix Urlaub', td.MN, cfg)
    assert not rl.ist_eigener_urlaub('Heidi Urlaub', td.MN, cfg)


def test_wochenpauschale_endet():
    cfg = config()
    cfg['wochenpauschale']['bis'] = rl.load_config(
        str(rl.__file__).replace('scripts/report_lib.py', 'config/projekt_konfiguration.json'))['wochenpauschale']['bis']
    cal = pd.DataFrame(columns=['Mitarbeiter', 'Ist_Urlaub', 'Start', 'Ende'])
    p = rl.generate_wochenpauschale_rows(cal, cfg, datetime(2026, 8, 1), datetime(2026, 9, 30, 23, 59))
    assert p['Start'].max() <= pd.Timestamp('2026-08-31') and len(p) == 5


def test_korrektur_aus_chat(tmp_path):
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    k = [{'bereich': 'kalender', 'mitarbeiter': td.MN, 'start': '2026-10-20 09:00', 'text': 'Montagssitzung',
          'korrektur': 'Cool'},
         {'bereich': 'kalender', 'mitarbeiter': td.MN, 'start': '2026-10-21 09:00', 'korrektur': 'Cool'}]
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'), korrekturen=k)
    c = r['kalender']
    assert c.loc[c['Aufgabe'] == 'Montagssitzung intern', 'Korrektur'].iloc[0] == 'Cool'
    assert r['pfad'].endswith('Füxle_2026-10_v01.xlsx')
    assert any(e['Thema'] == 'Korrektur aus Chat nicht anwendbar' for e in pruefliste(r['pfad']))


def test_urlaub_in_fremdem_kalender_mit_namen():
    cfg = config()
    cal = pd.DataFrame([{'Mitarbeiter': td.JP, 'Betreff': 'Urlaub MN 29.03.-06.04.2024', 'Ist_Urlaub': True,
                         'Start': pd.Timestamp('2024-03-29'), 'Ende': pd.Timestamp('2024-04-06')}])
    p = rl.generate_wochenpauschale_rows(cal, cfg, datetime(2024, 3, 25), datetime(2024, 4, 14, 23, 59))
    assert list(p['Dauer_h']) == [0.0, 0.0, 5.0]


# --------------------------------------------------------------- Version 6.2
def test_reiterstruktur(szenario):
    wb = openpyxl.load_workbook(szenario['v02']['pfad'])
    assert wb.sheetnames[:5] == ['Cockpit', 'Uebersicht', 'Interne_Auswertung', 'Pruefen_Korrigieren',
                                 'Abgleich_Vormonate']
    for weg in ('Filter_Dashboard', 'Monatstrend', 'Hauptaufgaben_Verteilung', 'Plausibilitaets_Check',
                'Pruefliste', 'Gesamt_Alle_Jahre', 'Parameter'):
        assert weg not in wb.sheetnames
    assert wb['Listen'].sheet_state == 'hidden'


@pytest.mark.parametrize('key', ['v01', 'v02'])
def test_cockpit_alle_gleich_uebersicht(szenario, recalced, key):
    res, pfad = recalced(szenario[key]['pfad'])
    wb = openpyxl.load_workbook(pfad, data_only=True)
    ue = sum(v['kosten'] for v in uebersicht_summen(pfad).values())
    ck = wb['Cockpit']
    netto = [r[1] for r in ck.iter_rows(min_row=10, max_row=22, max_col=2, values_only=True) if r[0] == 'Gesamtkosten NETTO'][0]
    assert netto == pytest.approx(ue, abs=0.01)
    assert any(r[1] == '0 Fehler ✔' for r in ck.iter_rows(min_col=5, max_col=6, values_only=True))
    # Projektliste im Cockpit = Übersicht je Projekt
    ue_p = uebersicht_summen(pfad)
    for r in ck.iter_rows(min_row=25, max_col=5, values_only=True):
        if r[0] in ue_p:
            assert r[4] == pytest.approx(ue_p[r[0]]['kosten'], abs=0.01), r[0]


def test_interne_auswertung_summe_gleich_stunden(szenario, recalced):
    res, pfad = recalced(szenario['v01']['pfad'])
    wb = openpyxl.load_workbook(pfad, data_only=True)
    ia = wb['Interne_Auswertung']
    gesamt = [r for r in ia.iter_rows(min_row=12, max_row=20, values_only=True) if r[0] == 'GESAMT'][0]
    std_ue = sum(v['std'] for v in uebersicht_summen(pfad).values())
    # Interne Auswertung = Übersichtsstunden + informative Niedermaier-Stunden (8,5 h/Tag)
    info = sum(rl.calc_tagessatz_block_kosten(szenario['v01']['kalender'], 'Spedition Niedermaier',
                                              szenario['cfg']['sonderkalkulationen'])['bloecke']['Tage']) * 8.5
    n_ha = len(szenario['v01']['config']['hauptaufgaben_kategorien']) - 2
    assert gesamt[1 + n_ha] == pytest.approx(std_ue + info, abs=0.01)


def test_entscheidung_passt_und_kommentar_bleiben(szenario):
    wb = openpyxl.load_workbook(szenario['v02']['pfad'])
    eintraege = pruefliste(szenario['v02']['pfad'])
    e = [x for x in eintraege if x['Thema'] == 'Entscheidung' and x['Entscheidung'] == 'Cool']
    assert e and e[0]['Kommentar'] == 'Test: Montagssitzung gehört zu Cool'


def test_passt_bestaetigt_ohne_korrektur(tmp_path):
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'))
    freigeben(r['pfad'], zusatz=lambda wb: [entscheide(wb, e['ID'], rl.PASST)
                                            for e in pruefliste(r['pfad']) if e['Thema'].startswith('unsicher')])
    alt = rl.lade_vorlage(r['pfad'], cfg)
    k = alt['kalender']
    fant = k[k['Projekt'] == 'Fantasia'].iloc[0]
    assert fant['Entscheidung'] == rl.PASST and pd.isna(fant['Korrektur'])


def test_ausmisten():
    cfg = config()
    cal = pd.DataFrame({'Projekt': [None, 'Koko', 'Koko', None], 'Korrektur': ['Unberücksichtigt', 'Koko', 'Cool', 'Cool']})
    trips = pd.DataFrame(columns=['Projekt', 'Korrektur'])
    c, t, n = rl.ausmisten(cal, trips, cfg)
    assert n == 2 and [None if pd.isna(x) else x for x in c['Korrektur']] == [None, None, 'Cool', 'Cool']


def test_regel_vorschlag_und_uebernahme(tmp_path):
    cfg = config()
    termine = td.MARIUS_BASIS + [(f'Termin Grafschaft {i}', f'2026-10-{10 + i} 09:00', f'2026-10-{10 + i} 10:00')
                                 for i in range(3)]
    cs, al = td.specs(tmp_path, termine)
    k = [{'bereich': 'kalender', 'mitarbeiter': td.MN, 'start': f'2026-10-{10 + i} 09:00', 'korrektur': 'Frutania'}
         for i in range(3)]
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'), korrekturen=k)
    vor = rl.regel_vorschlaege(r['kalender'], r['config'])
    assert any(v['Stichwort'] == 'grafschaft' and v['Projekt'] == 'Frutania' for v in vor)
    wb = openpyxl.load_workbook(r['pfad'])
    ws = wb[rl.PRUEF]
    for row in range(7, ws.max_row + 1):
        if ws.cell(row=row, column=15).value == 'grafschaft':
            ws.cell(row=row, column=20, value='x')
    wb.save(r['pfad'])
    alt = rl.lade_vorlage(r['pfad'], cfg)
    cfg2, hinweise = rl._merge_config(cfg, alt)
    assert cfg2['projektname_erkennung']['stichwort_regeln']['grafschaft'] == 'Frutania'
    e = rl.erkenne_projekt('M. Neininger Grafschaft', cfg2)
    assert e['projekt'] == 'Frutania' and 'Regel' in e['grund']


def test_neue_manuelle_zeile_holt_stundensatz(szenario, recalced, tmp_path):
    import shutil
    p = tmp_path / 'Füxle_2026-10_v01.xlsx'
    shutil.copy(szenario['v01']['pfad'], p)
    wb = openpyxl.load_workbook(p)
    mz = wb['Manuelle_Zeitbuchungen']
    for c, v in enumerate([datetime(2026, 10, 9), td.JP, 'Koko', 'Projektbetreuung', 2, 'neu'], start=1):
        mz.cell(row=7, column=c, value=v)
    wb.save(p)
    res, pfad = recalced(str(p))
    ws = openpyxl.load_workbook(pfad, data_only=True)['Manuelle_Zeitbuchungen']
    assert ws.cell(row=7, column=8).value == 150 and ws.cell(row=7, column=9).value == 300


def test_projekt_nur_in_eingaben_steht_in_uebersicht(tmp_path, recalced):
    """Bug alte Berichte: Projekte nur aus manuellen Zeiten/Zusatzkosten fehlten in der Übersicht."""
    cfg = config()
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    mz = pd.DataFrame([{'Datum': '2026-09-15', 'Mitarbeiter': td.MN, 'Projekt': 'Wackler',
                        'Hauptaufgabe': 'Projektbetreuung', 'Stunden': 3, 'Anmerkung': 'nur manuell'}])
    zk = pd.DataFrame([{'Datum': datetime(2026, 9, 16), 'Projekt': 'Süssmilch', 'Kostenart': 'Hotel',
                        'Betrag_EUR': 264.0, 'Anmerkung': 'nur Zusatzkosten'}])
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'),
                     neue_manuelle_zeitbuchungen=mz, neue_zusatzkosten=zk)
    res, pfad = recalced(r['pfad'])
    ue = uebersicht_summen(pfad)
    assert ue['Wackler']['kosten'] == pytest.approx(600) and ue['Süssmilch']['kosten'] == pytest.approx(264)
    ck = openpyxl.load_workbook(pfad, data_only=True)['Cockpit']
    netto = [r_[1] for r_ in ck.iter_rows(min_row=10, max_row=22, max_col=2, values_only=True)
             if r_[0] == 'Gesamtkosten NETTO'][0]
    assert netto == pytest.approx(sum(v['kosten'] for v in ue.values()), abs=0.01)


# --------------------------------------------------------------- Version 6.3: Kundenbericht
def test_kundenbericht_summen_und_regeln(szenario, tmp_path):
    cfg = szenario['cfg']
    pfad = szenario['v01']['pfad']          # freigegeben (conftest)
    proj = ['Koko', 'Cool', 'Zeppelin', 'Forst', 'Sandformation']
    wp = 'Allgemeine Vertriebszeit (automatische Wochenpauschale)'
    b = rl.erstelle_kundenbericht(pfad, cfg, proj, str(tmp_path), interne=[wp], pdf=False)
    daten = rl.lade_vorlage(pfad, cfg)
    soll = rl.summen_je_monat_projekt(daten, rl._merge_config(cfg, daten)[0], statische_kosten=True)
    soll = soll[soll['Monat'] <= '2026-10'].groupby('Projekt')['Kosten'].sum()
    x = b['positionen'].groupby('Projekt')['Netto'].sum()
    for p_ in proj + [wp]:
        assert x[p_] == pytest.approx(soll[p_], abs=0.01), p_
    # Pauschale als EINE Zeile je Projekt (Standard b)
    pp = b['positionen'][b['positionen']['Zeit'] == 'Pauschale']
    assert len(pp) == 1 and '7 Wochen' in pp.iloc[0]['Leistung'] and 'KW' in pp.iloc[0]['Leistung']
    b2 = rl.erstelle_kundenbericht(pfad, cfg, proj, str(tmp_path / 'einzeln'), interne=[wp], pdf=False,
                                   pauschale_einzeln=True)
    assert (b2['positionen']['Zeit'] == 'Pauschale').sum() == 7
    # nur Werte, keine Formeln, keine internen Reiter
    wb = openpyxl.load_workbook(b['xlsx'])
    assert wb.sheetnames == ['Übersicht', 'Leistungsnachweis']
    assert not any(isinstance(c.value, str) and c.value.startswith('=') for ws in wb for row in ws.iter_rows() for c in row)
    assert '_ENTWURF' not in b['xlsx']


def test_kundenbericht_stoppt(szenario, tmp_path):
    cfg = szenario['cfg']
    with pytest.raises(ValueError, match='gehört zu'):
        rl.erstelle_kundenbericht(szenario['v01']['pfad'], cfg, ['Koko', 'Barrierefrei'], str(tmp_path), pdf=False)
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'))
    with pytest.raises(rl.VorlageFehler, match='FREIGEGEBENEN'):
        rl.erstelle_kundenbericht(r['pfad'], cfg, ['Koko'], str(tmp_path), pdf=False)
    e = rl.erstelle_kundenbericht(r['pfad'], cfg, ['Koko'], str(tmp_path / 'e'), pdf=False, nur_freigegeben=False)
    assert e['xlsx'].endswith('_ENTWURF.xlsx')


def test_kw_bereiche():
    m = [pd.Timestamp(x) for x in ('2024-01-29', '2024-02-05', '2024-02-12', '2024-03-25', '2025-07-21')]
    assert rl._kw_bereiche(m) == 'KW 5–7/2024, 13/2024, 30/2025'


# --------------------------------------------------------------- Version 6.4: TransCare-Abrechnung
def _tc_datei(szenario, tmp_path, modus=None):
    cfg = szenario['cfg']
    cs, al = td.specs(tmp_path, td.MARIUS_BASIS)
    r0 = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'ohne_tc'))
    d0 = rl.lade_vorlage(r0['pfad'], cfg)
    s0 = rl.summen_je_monat_projekt(d0, rl._merge_config(cfg, d0)[0])
    koko_sep = round(float(s0[(s0['Projekt'] == 'Koko') & (s0['Monat'] == '2026-09')]['Kosten'].sum()), 2)
    zeilen = pd.DataFrame([
        {'Position': 'Koko', 'Bereich': 'Projekt', 'Std': 0, 'km': 0, 'Kosten_Zeit': koko_sep + 500,
         'Kosten_Fahrt': 0, 'Sonstige': 0, 'Netto': koko_sep + 500, 'Hinweis': None},
        {'Position': 'Vor-Ort Termine i. Auftrag TC', 'Bereich': 'Allgemein', 'Std': 5, 'km': 0,
         'Kosten_Zeit': 1000, 'Kosten_Fahrt': 0, 'Sonstige': 0, 'Netto': 1000, 'Hinweis': None}])
    tc = {'firma': 'TransCare', 'stichtag': pd.Timestamp('2026-09-30'), 'datum': '05.10.2026',
          'modus': modus or rl.MODUS_KORR, 'zeilen': zeilen}
    zahl = pd.DataFrame([{'Datum': None, 'Rechnung': 'RG 1', 'Zeitraum': '09/26', 'Betrag_brutto': 1190.0,
                          'Anmerkung': None},
                         {'Datum': None, 'Rechnung': 'RG 2', 'Zeitraum': '10/26', 'Betrag_brutto': None,
                          'Anmerkung': None}])
    r = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(tmp_path / 'o'), tc_stand=tc,
                     zahlungen=zahl)
    return r, koko_sep


def _live_wert(pfad_recalc, label):
    ws = openpyxl.load_workbook(pfad_recalc, data_only=True)['TC_Bericht']
    for row in ws.iter_rows():
        for c in row:
            if c.value == label:
                return ws.cell(row=c.row, column=c.column + 1).value
    raise KeyError(label)


def test_tc_abrechnung_live_gleich_bericht(szenario, tmp_path, recalced):
    cfg = szenario['cfg']
    r, koko_sep = _tc_datei(szenario, tmp_path)
    js, kopie = recalced(r['pfad'])
    assert js['total_errors'] == 0
    b = rl.erstelle_kundenbericht(r['pfad'], cfg, ['Koko'], str(tmp_path / 'b'), pdf=False, nur_freigegeben=False,
                                  interne=['Vor-Ort Termine i. Auftrag TC'])
    z = b['rechnung']['Koko']
    assert z['korrektur'] == pytest.approx(-500, abs=0.01)           # Füxle korrigiert die Aufstellung
    assert z['basis']['Netto'] == pytest.approx(koko_sep, abs=0.01)
    assert b['rechnung']['Vor-Ort Termine i. Auftrag TC']['basis']['Netto'] == pytest.approx(1000)  # immer gemeldet
    assert b['zahlungen'] == pytest.approx(1190)
    assert b['offen'] == pytest.approx(b['brutto'] - 1190, abs=0.01)
    # Live-Blatt (Formeln, alle Positionen mit x) - nur Koko + Vor-Ort haben Werte bis Stichtag
    assert _live_wert(kopie, 'abzüglich Zahlungen (brutto)') == pytest.approx(-1190, abs=0.01)
    wb = openpyxl.load_workbook(b['xlsx'])
    assert wb.sheetnames == ['Übersicht', 'Leistungsnachweis']
    assert not any(isinstance(c.value, str) and c.value.startswith('=') for ws in wb for row in ws.iter_rows() for c in row)
    # Prüfpunkt: Zahlung ohne Betrag
    wbf = openpyxl.load_workbook(r['pfad'])
    assert any(isinstance(c.value, str) and 'Zahlung ohne Betrag' in c.value
               for ws in wbf for row in ws.iter_rows() for c in row)


def test_tc_schalter_wie_gemeldet(szenario, tmp_path):
    cfg = szenario['cfg']
    r, koko_sep = _tc_datei(szenario, tmp_path)
    wb = openpyxl.load_workbook(r['pfad'])
    assert wb['TC_Stand']['B6'].value == rl.MODUS_KORR
    wb['TC_Stand']['B6'] = rl.MODUS_GEMELDET                         # Nutzerin schaltet um
    wb.save(r['pfad'])
    b = rl.erstelle_kundenbericht(r['pfad'], cfg, ['Koko'], str(tmp_path / 'g'), pdf=False, nur_freigegeben=False)
    z = b['rechnung']['Koko']
    assert z['korrektur'] == 0 and z['basis']['Netto'] == pytest.approx(koko_sep + 500, abs=0.01)
    # Leistungsnachweis: eine Zeile "Stand lt. Aufstellung", danach nur Leistungen ab Stichtag
    ln = openpyxl.load_workbook(b['xlsx'])['Leistungsnachweis']
    texte = [c.value for c in ln['D'] if isinstance(c.value, str)]
    assert any(t.startswith('Stand lt. Aufstellung vom 05.10.2026') for t in texte)
