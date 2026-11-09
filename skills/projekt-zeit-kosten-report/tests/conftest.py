import glob
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import openpyxl
import pandas as pd
import pytest

SKILL = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(SKILL / 'scripts'), str(SKILL / 'tests')]
import report_lib as rl  # noqa: E402
import testdaten as td   # noqa: E402

BASIS_START = datetime(2026, 9, 1)
BASIS_ENDE = datetime(2026, 10, 31, 23, 59, 59)
NOV_ENDE = datetime(2026, 11, 30, 23, 59, 59)


def _recalc_script():
    kandidaten = glob.glob('/mnt/skills/public/xlsx/scripts/recalc.py') + \
        glob.glob(os.path.expanduser('~/.claude/skills/synced/*/xlsx/scripts/recalc.py'))
    return kandidaten[0] if kandidaten else None


def recalc(pfad):
    """Rechnet eine KOPIE mit LibreOffice neu (xlsx-Skill) und liefert (json, kopie)."""
    script = _recalc_script()
    if script is None:
        pytest.skip('recalc.py (xlsx-Skill) nicht gefunden')
    kopie = str(pfad).replace('.xlsx', '_recalc.xlsx')
    shutil.copy(pfad, kopie)
    out = subprocess.run([sys.executable, script, kopie, '180'], capture_output=True, text=True, timeout=400)
    return json.loads(out.stdout), kopie


def freigeben(pfad, wer='GF Test', zusatz=None):
    """Simuliert die Nutzerin in Excel: Freigabevermerk + händische Einträge."""
    wb = openpyxl.load_workbook(pfad)
    ws = wb[rl.PRUEF]                    # ab 6.5: Freigabe oben in Pruefen_Korrigieren
    pos = rl._finde_zelle(ws, 'Freigegeben am')
    ws.cell(row=pos[0], column=pos[1] + 1, value='05.11.2026')
    ws.cell(row=pos[0] + 1, column=pos[1] + 1, value=wer)
    if zusatz:
        zusatz(wb)
    wb.save(pfad)


def config():
    """Echte Config. Die Testdaten liegen Sep.-Nov. 2026 - also NACH dem Ende der
    Wochenpauschale (31.08.2026). Damit die Pauschale-Logik weiter mitgetestet wird,
    wird 'bis' hier entfernt; test_wochenpauschale_endet prüft das Ende separat."""
    c = rl.load_config(SKILL / 'config' / 'projekt_konfiguration.json')
    c['wochenpauschale'].pop('bis', None)
    return c


def lade_v5():
    spec = importlib.util.spec_from_file_location('report_lib_v5', SKILL / 'tests' / 'referenz' / 'report_lib_v5.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def handeintraege(wb):
    """Zusatzkosten (2), manuelle Buchung (1), Korrektur, Partner-Zuordnung."""
    zk = wb['Zusatzkosten']
    for i, (d, p, art, b) in enumerate([(datetime(2026, 9, 3), 'Cool', 'Hotel', 120.0),
                                         (datetime(2026, 9, 4), 'Koko', 'Bahn', 80.0)]):
        for c, v in enumerate([d, p, art, b, 'Test'], start=1):
            zk.cell(row=5 + i, column=c, value=v)
    mz = wb['Manuelle_Zeitbuchungen']
    for c, v in enumerate([datetime(2026, 10, 2), td.FS, 'Begamis', 'Projektbetreuung', 2, 'nachgetragen'], start=1):
        mz.cell(row=5, column=c, value=v)
    mz.cell(row=5, column=8, value=150)
    rk = wb['Rohdaten_Kalender']
    for row in range(2, rk.max_row + 1):
        if rk.cell(row=row, column=14).value == 'Montagssitzung intern':
            entscheide(wb, rk.cell(row=row, column=24).value, 'Cool', 'Test: Montagssitzung gehört zu Cool')
    pa = wb['Stammdaten']
    pos = rl._finde_zelle(pa, 'Partner (Autolog)')
    for row in range(pos[0] + 1, pa.max_row + 1):
        if pa.cell(row=row, column=pos[1]).value == 'Koko Partner':
            pa.cell(row=row, column=pos[1] + 1, value='Koko')


def entscheide(wb, id_, entscheidung, kommentar=None):
    """Wie die Nutzerin: in Pruefen_Korrigieren die Zeile mit der ID suchen (oder eine freie
    Zeile nehmen) und in Spalte J entscheiden."""
    ws = wb[rl.PRUEF]
    frei = None
    for r in range(rl.PRUEF_KOPFZEILE + 1, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == rl.ABGL_TITEL:
            break
        if ws.cell(row=r, column=1).value == id_:
            frei = r
            break
        if frei is None and ws.cell(row=r, column=3).value == 'frei (ID eintragen)':
            frei = r
    ws.cell(row=frei, column=1, value=id_)
    ws.cell(row=frei, column=10, value=entscheidung)
    ws.cell(row=frei, column=11, value=kommentar)


def pruefliste(pfad):
    ws = openpyxl.load_workbook(pfad)[rl.PRUEF]
    hr = rl.PRUEF_KOPFZEILE
    kopf = [c.value for c in ws[hr]]
    out = []
    for r in ws.iter_rows(min_row=hr + 1, values_only=True):
        if r[0] == rl.ABGL_TITEL:
            break
        if r[1]:
            out.append(dict(zip(kopf, r)))
    return out


def abgleich_status(pfad):
    ws = openpyxl.load_workbook(pfad)[rl.PRUEF]
    for row in ws.iter_rows(max_col=1):
        if row[0].value == rl.ABGL_TITEL:
            return ws.cell(row=row[0].row + 3, column=1).value
    raise KeyError('Abgleich-Abschnitt fehlt')


@pytest.fixture(scope='session')
def szenario(tmp_path_factory):
    d = tmp_path_factory.mktemp('szenario')
    cfg = config()
    cs, al = td.specs(d, td.MARIUS_BASIS)
    v01 = rl.neuaufbau(cs, al, cfg, BASIS_START, BASIS_ENDE, '2026-10', str(d / 'out'))
    freigeben(v01['pfad'], zusatz=handeintraege)
    # November: kompletter Kalender (inkl. Sep/Okt + ein Okt-Nachtrag), überlappender Autolog-Export
    cs_n, al_n = td.specs(d, td.MARIUS_BASIS + [td.MARIUS_NACHTRAG_OKT] + td.MARIUS_NOV,
                          fahrten=td.FAHRTEN_BASIS[-2:] + td.FAHRTEN_NOV + td.FAHRTEN_NOV, tag='nov')
    v02 = rl.fortfuehrung(v01['pfad'], 'v01', cs_n, al_n, cfg, NOV_ENDE, '2026-11', str(d / 'out'))
    return {'dir': d, 'cfg': cfg, 'v01': v01, 'v02': v02, 'cs': cs, 'al': al, 'cs_n': cs_n, 'al_n': al_n}


_recalc_cache = {}


@pytest.fixture(scope='session')
def recalced():
    def _get(pfad):
        if pfad not in _recalc_cache:
            _recalc_cache[pfad] = recalc(pfad)
        return _recalc_cache[pfad]
    return _get


def uebersicht_summen(pfad, blatt='Cockpit'):
    """Summen je Projekt: ab 6.5 Projektliste im Cockpit (Filter (Alle)); Version-5-Dateien: Gesamt_Alle_Jahre."""
    ws = openpyxl.load_workbook(pfad, data_only=True)[blatt]
    if blatt == 'Cockpit':
        out, an = {}, False
        for r in ws.iter_rows(max_col=7, values_only=True):
            if r[0] == 'Projekt' and r[3] == 'Stunden':
                an = True
                continue
            if an and r[0]:
                out[r[0]] = {'std': r[3], 'kosten': r[5], 'km': r[4]}
        return out
    hr = 5 if blatt == 'Uebersicht' else 4
    kopf = [c.value for c in ws[hr]]
    out = {}
    for r in ws.iter_rows(min_row=hr + 1, values_only=True):
        if r[0] in (None, 'GESAMT'):
            continue
        d = dict(zip(kopf, r))
        out[r[0]] = {'std': d['Std. gesamt'], 'kosten': d['Gesamtkosten Netto (€)'],
                     'km': d['Distanz gesamt (km)']}
    return out
