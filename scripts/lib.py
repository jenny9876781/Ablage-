"""Gemeinsame Helfer: Artikeldaten laden, Zahlen aufbereiten, Fotos finden."""
import csv, os

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PFAD = os.path.join(BASIS, "daten", "artikel_kikripp.csv")
FOTO_DIR = os.path.join(BASIS, "fotos")
AUSGABE = os.path.join(BASIS, "ausgabe")

USt_SATZ = 0.19
PAKETRABATT = 0.20          # Vorschlag für das Paketangebot; vom Vorgesetzten anzupassen

FIRMA = "Kinderkrippe kikripp GmbH"
STRASSE = "Musterstraße 1"
ORT = "12345 Musterstadt"
ANSPRECHPARTNER = "J. Preisigke"
TELEFON = "0123 456789"
EMAIL = "info@kikripp.de"
EMPFAENGER = "Klinikum – Einkauf"
ANGEBOT_NR = "ANG-2026-0001"
DATUM = "15.09.2026"
GUELTIG = "15.10.2026"


def zahl(s):
    """'1.200,00' -> 1200.0 ; '' -> None"""
    s = (s or "").strip()
    if not s:
        return None
    return float(s.replace(".", "").replace(",", "."))


def lade_artikel():
    with open(CSV_PFAD, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    out = []
    for r in rows:
        d = {k: (v or "").strip() for k, v in r.items()}
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
