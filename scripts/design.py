"""Zentrale Design- und Stammdaten. Alle Werte stehen in daten/design.csv."""
import csv, os

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PFAD = os.path.join(BASIS, "daten", "design.csv")


def _lade():
    with open(PFAD, encoding="utf-8") as f:
        return {r["Schluessel"]: (r["Wert"] or "").strip()
                for r in csv.DictReader(f, delimiter=";") if r.get("Schluessel")}


D = _lade()

FIRMA        = D["Firma"]
STRASSE      = D["Strasse"]
PLZ_ORT      = D["PLZ_Ort"]
ANSPRECH     = D["Ansprechpartner"]
TELEFON      = D["Telefon"]
EMAIL        = D["Email"]
EMPF_FIRMA   = D["Empfaenger_Firma"]
EMPF_PERSON  = D["Empfaenger_Person"]
ANGEBOT_NR   = D["Angebot_Nr"]
DATUM        = D["Angebot_Datum"]
GUELTIG      = D["Angebot_Gueltig_bis"]
USt_SATZ     = float(D["USt_Satz_Prozent"]) / 100
PAKETRABATT  = float(D["Paketrabatt_Prozent"]) / 100

ROT      = D["Farbe_Rot"]
SCHWARZ  = D["Farbe_Schwarz"]
PAPIER   = D["Farbe_Papier"]
GRAU     = D["Farbe_Grau"]
LINIE    = D["Farbe_Linie"]
FELD_KLINIK = D["Feld_Klinik"]
FELD_INTERN = D["Feld_Intern"]
ZEILE    = D["Zeile_Wechsel"]
FONT     = D["Schrift_Excel"]
WEBFONT  = D["Schrift_Web"]

ABSENDER = f"{FIRMA} · {STRASSE} · {PLZ_ORT} · {ANSPRECH} · {TELEFON} · {EMAIL}"
EMPFAENGER = f"{EMPF_FIRMA}, {EMPF_PERSON}"
ASSETS = os.path.join(BASIS, "assets")


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
