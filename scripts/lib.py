"""Artikeldaten laden und aufbereiten. Design und Stammdaten kommen aus design.py."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from design import *                                   # noqa: F401,F403  (Farben, Firmendaten)

CSV_PFAD = os.path.join(BASIS, "daten", "artikel_kikripp.csv")   # noqa: F405
FOTO_DIR = os.path.join(BASIS, "fotos")                          # noqa: F405
AUSGABE  = os.path.join(BASIS, "ausgabe")                        # noqa: F405


def zahl(s):
    s = (s or "").strip()
    return float(s.replace(".", "").replace(",", ".")) if s else None


def lade_artikel(nur_aktive=True):
    with open(CSV_PFAD, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    out = []
    for r in rows:
        d = {k: (v or "").strip() for k, v in r.items()}
        # "entfällt" = nie verkauft worden, "nein" = nicht mehr vorhanden.
        # Beides zählt nicht zum Bestand und darf nicht in Summen oder Angebote.
        if nur_aktive and (d.get("Aktiv") or "ja").lower() in ("entfällt", "nein"):
            continue
        # Geld- und Mengenfelder müssen Zahlen sein, sonst rechnen die Excel-Formeln nicht
        for feld in ("Preis_netto", "Anschaffungswert_netto", "Verkaufspreis_netto"):
            d[feld] = zahl(d.get(feld))
        d["Menge"] = int(d["Menge"]) if d.get("Menge", "").isdigit() else 0
        d["Verkauft_Menge"] = int(d["Verkauft_Menge"]) if d.get("Verkauft_Menge", "").isdigit() else None
        d["Positionswert"] = (d["Preis_netto"] or 0) * d["Menge"]
        out.append(d)
    return out


def foto(name):
    p = os.path.join(FOTO_DIR, str(name) + ".jpg")
    return p if os.path.exists(p) else None


def eur(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------------------------------------------------------- Kasse (seit 15.10.2026)
# Das Blatt „Kasse“ der Arbeitsmappe ist Buchführung der Nutzerin. Es hat eine eigene Datenbasis,
# damit ein Neubau der Mappe es nie wieder leer überschreibt (Fehler vom 13./14.10.2026).
KASSE_PFAD = os.path.join(BASIS, "daten", "kasse.csv")                  # noqa: F405
KASSE_FELDER = ["Datum", "Beleg_Nr", "Vorgang_Kaeufer", "Einnahme", "Ausgabe"]
KASSE_ANFANG = "Anfangsbestand Kasse"


def lade_kasse():
    """-> (anfangsbestand: float, buchungen: [dict]) aus daten/kasse.csv"""
    if not os.path.exists(KASSE_PFAD):
        return 0.0, []
    with open(KASSE_PFAD, encoding="utf-8") as f:
        zeilen = list(csv.DictReader(f, delimiter=";"))
    anfang, buchungen = 0.0, []
    for z in zeilen:
        if z["Vorgang_Kaeufer"] == KASSE_ANFANG and not z["Datum"]:
            anfang = zahl(z["Einnahme"]) or 0.0
        else:
            buchungen.append(z)
    return anfang, buchungen


def _geld(v):
    if v in (None, ""):
        return ""
    if isinstance(v, (int, float)):
        return f"{float(v):.2f}".replace(".", ",")
    return str(v).strip()


def kasse_aus_mappe(wb):
    """Liest das Blatt „Kasse“ einer geladenen Arbeitsmappe (data_only=True) -> (anfang, buchungen)."""
    import datetime as _dt
    if "Kasse" not in wb.sheetnames:
        return None
    ws = wb["Kasse"]
    anfang = ws.cell(row=5, column=8).value
    buchungen = []
    for r in range(6, ws.max_row + 1):
        datum, beleg, wer, ein, aus = (ws.cell(row=r, column=c).value for c in (1, 2, 3, 4, 7))
        if all(v in (None, "") for v in (datum, beleg, wer, ein, aus)):
            continue
        if isinstance(datum, (_dt.datetime, _dt.date)):
            datum = datum.strftime("%Y-%m-%d")
        if isinstance(beleg, float) and beleg.is_integer():
            beleg = int(beleg)
        buchungen.append({"Datum": str(datum or "").strip(), "Beleg_Nr": str(beleg or "").strip(),
                          "Vorgang_Kaeufer": str(wer or "").strip(), "Einnahme": _geld(ein), "Ausgabe": _geld(aus)})
    return (float(anfang) if isinstance(anfang, (int, float)) else 0.0), buchungen


def schreibe_kasse(anfang, buchungen):
    with open(KASSE_PFAD, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=KASSE_FELDER, delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerow({"Datum": "", "Beleg_Nr": "", "Vorgang_Kaeufer": KASSE_ANFANG, "Einnahme": _geld(anfang), "Ausgabe": ""})
        w.writerows(buchungen)
