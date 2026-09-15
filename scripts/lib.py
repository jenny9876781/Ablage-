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
        if nur_aktive and d.get("Aktiv", "ja").lower() == "entfällt":
            continue
        d["Preis_netto"] = zahl(d.get("Preis_netto"))
        d["Menge"] = int(d["Menge"]) if d.get("Menge", "").isdigit() else 0
        d["Positionswert"] = (d["Preis_netto"] or 0) * d["Menge"]
        out.append(d)
    return out


def foto(name):
    p = os.path.join(FOTO_DIR, str(name) + ".jpg")
    return p if os.path.exists(p) else None


def eur(v):
    return f"{v:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
