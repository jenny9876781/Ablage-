"""Gemeinsame Helfer: Beispieldaten laden, Zahlen/Umlaute aufbereiten."""
import csv, re, os

BASIS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PFAD = os.path.join(BASIS, "daten", "artikel_beispiel.csv")
FOTO_DIR = os.path.join(BASIS, "fotos")

# Die Beispiel-CSV ist ASCII-sicher abgelegt; hier werden die Umlaute zurueckgesetzt.
_UML = [
    ("Gewerbespuelmaschine", "Gewerbespülmaschine"), ("Untertischgeraet", "Untertischgerät"),
    ("Kuechentechnik", "Küchentechnik"), ("Ablagefaecher", "Ablagefächer"),
    ("Datenloeschung", "Datenlöschung"), ("Datentraeger", "Datenträger"),
    ("hoehenverstellbare", "höhenverstellbare"), ("hoehenverstellbar", "höhenverstellbar"),
    ("trapezfoermig", "trapezförmig"), ("abschliessbar", "abschließbar"),
    ("Ordnerhoehen", "Ordnerhöhen"), ("Sitzhoehe", "Sitzhöhe"), ("Weiss", "Weiß"),
    ("Fuer ", "Für "),
    ("Aussenbereich", "Außenbereich"), ("Bodenhuelsen", "Bodenhülsen"),
    ("Strassenverkehr", "Straßenverkehr"), ("Ueberweisung", "Überweisung"),
    ("Reserviert_fuer", "Reserviert_für"), ("vollstaendig", "vollständig"),
    ("Klangstaebe", "Klangstäbe"), ("ungeoeffnet", "ungeöffnet"),
    ("verfuegbar", "verfügbar"), ("Spuelmaschine", "Spülmaschine"),
    ("gepruefte", "geprüfte"), ("geprueft", "geprüft"), ("geloescht", "gelöscht"),
    ("Plaetze", "Plätze"), ("moeglich", "möglich"), ("Kaeufer", "Käufer"),
    ("Stueck", "Stück"), ("Moebel", "Möbel"), ("Kueche", "Küche"), ("Buero", "Büro"),
    ("Fuesse", "Füße"), ("Hoehe", "Höhe"), ("Faecher", "Fächer"), ("gross", "groß"),
    (" a 500 ml", " à 500 ml"),
]

def _uml(s):
    for a, b in _UML:
        s = s.replace(a, b)
    return s

def zahl(s):
    """'3.200,00' -> 3200.0 ; '' -> None"""
    s = (s or "").strip()
    if not s:
        return None
    return float(s.replace(".", "").replace(",", "."))

def lade_artikel():
    with open(CSV_PFAD, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    out = []
    for r in rows:
        d = {_uml(k): _uml(v or "") for k, v in r.items()}
        for feld in ("Anschaffungswert_netto", "Preis_netto", "Verkaufspreis_netto"):
            d[feld] = zahl(d.get(feld))
        for feld in ("Menge", "Verkauft_Menge"):
            v = (d.get(feld) or "").strip()
            d[feld] = int(v) if v.isdigit() else None
        out.append(d)
    return out

def foto(artnr):
    p = os.path.join(FOTO_DIR, artnr + ".jpg")
    return p if os.path.exists(p) else None

USt_SATZ = 0.19
