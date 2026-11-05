"""Automatische Tests für Skill-Version 6 (erfundene Testdaten, siehe testdaten.py).

Aufruf:  python -m pytest tests -v
"""
import shutil
from datetime import datetime

import openpyxl
import pandas as pd
import pytest

from conftest import (BASIS_ENDE, BASIS_START, NOV_ENDE, config, freigeben, lade_v5, rl, td,
                      uebersicht_summen)


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
    pl = wb['Pruefliste']
    eintraege = [r for r in pl.iter_rows(min_row=6, values_only=True) if r[0]]
    assert len(eintraege) == 4        # + Fahrt mit zwei Projekten im Zeitfenster
    assert any('weitere Projekte im Fenster' in (e[6] or '') for e in eintraege)


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
    pl = openpyxl.load_workbook(szenario['v02']['pfad'])['Pruefliste']
    assert any(r[1] and 'Nachtrag Vormonat' in r[1] for r in pl.iter_rows(min_row=6, values_only=True))


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
    ws = openpyxl.load_workbook(szenario['v01']['pfad'])['Parameter']
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
    s5, s6 = uebersicht_summen(rc5), uebersicht_summen(rc6)
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
    pl = openpyxl.load_workbook(r['pfad'])['Pruefliste']
    assert any(x[1] == 'Fahrt nicht klassifiziert' for x in pl.iter_rows(min_row=6, values_only=True))


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
    pl = openpyxl.load_workbook(r['pfad'])['Pruefliste']
    assert any(x[1] == 'Korrektur aus Chat nicht anwendbar' for x in pl.iter_rows(min_row=6, values_only=True))
