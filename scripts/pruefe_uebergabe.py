"""Prüft die drei Dateien, die in WordPress hochgeladen werden.

    python3 scripts/pruefe_uebergabe.py

Geprüft wird, was beim Einspielen schiefgehen kann, bevor es jemand im Browser merkt:
Aufbau der beiden ZIP-Dateien, Lesbarkeit jedes Fotos, und ob die Importdatei genau
die Felder mitbringt, die der Import im Plugin ausliest. Zum Schluss wird dieselbe
Zuordnung Foto -> Mediathek nachgestellt, die das Plugin vornimmt.
"""
import io, json, os, re, subprocess, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import AUSGABE, BASIS
from PIL import Image

PLUGIN = os.path.join(AUSGABE, "kikripp-katalog.zip")
FOTOS = os.path.join(AUSGABE, "kikripp-fotos.zip")
IMPORT = os.path.join(AUSGABE, "katalog_import.json")

fehler, hinweise = [], []
def F(t): fehler.append(t);   print(f"  FEHLER   {t}")
def W(t): hinweise.append(t); print(f"  Hinweis  {t}")
def OK(t): print(f"  ok       {t}")


def pruefe_plugin():
    print("\n== 1. kikripp-katalog.zip ==")
    if not os.path.exists(PLUGIN):
        F("Datei fehlt"); return
    with zipfile.ZipFile(PLUGIN) as z:
        namen = z.namelist()
        wurzeln = {n.split("/")[0] for n in namen}
        if wurzeln != {"kikripp-katalog"}:
            F(f"WordPress erwartet genau einen Ordner im Archiv, gefunden: {sorted(wurzeln)}")
        else:
            OK("genau ein Ordner kikripp-katalog/ im Archiv")
        muell = [n for n in namen if "__MACOSX" in n or n.endswith(".DS_Store")]
        if muell: F(f"Reste im Archiv: {muell[:5]}")
        else:     OK("keine Betriebssystem-Reste im Archiv")
        haupt = "kikripp-katalog/kikripp-katalog.php"
        if haupt not in namen:
            F("die Hauptdatei kikripp-katalog.php fehlt"); return
        kopf = z.read(haupt).decode("utf-8", "replace")[:1500]
        for feld in ("Plugin Name:", "Version:", "Description:"):
            if feld not in kopf: F(f"im Plugin-Kopf fehlt „{feld}“")
        if all(f in kopf for f in ("Plugin Name:", "Version:", "Description:")):
            v = re.search(r"Version:\s*([0-9.]+)", kopf)
            OK(f"Plugin-Kopf vollständig, Version {v.group(1) if v else '?'}")
        php = [n for n in namen if n.endswith(".php")]
        kaputt = []
        for n in php:
            r = subprocess.run(["php", "-l"], input=z.read(n), capture_output=True)
            if r.returncode != 0: kaputt.append(n)
        if kaputt: F(f"PHP-Syntaxfehler in: {kaputt}")
        else:      OK(f"alle {len(php)} PHP-Dateien fehlerfrei")
        for pflicht in ("kikripp-katalog/assets/katalog.js", "kikripp-katalog/assets/katalog.css"):
            if pflicht not in namen: F(f"{pflicht} fehlt im Archiv")
        OK(f"{len(namen)} Einträge, {os.path.getsize(PLUGIN)//1024} KB")


def fotos_im_paket():
    with zipfile.ZipFile(FOTOS) as z:
        return {os.path.basename(n): z.getinfo(n) for n in z.namelist() if n.endswith(".jpg")}


def pruefe_fotos():
    print("\n== 2. kikripp-fotos.zip ==")
    if not os.path.exists(FOTOS):
        F("Datei fehlt"); return {}
    with zipfile.ZipFile(FOTOS) as z:
        namen = [n for n in z.namelist() if not n.endswith("/")]
        falsch = [n for n in namen if not re.fullmatch(r"fotos/F-\d{3}\.jpg", n)]
        if falsch: F(f"unerwartete Einträge: {falsch[:5]}")
        else:      OK(f"alle {len(namen)} Einträge heißen fotos/F-xxx.jpg")
        basis = [os.path.basename(n) for n in namen]
        doppelt = {n for n in basis if basis.count(n) > 1}
        if doppelt: F(f"Dateiname doppelt im Archiv: {sorted(doppelt)}")
        else:       OK("kein Dateiname doppelt")
        schlecht, gross = [], []
        for n in namen:
            roh = z.read(n)
            try:
                im = Image.open(io.BytesIO(roh)); im.verify()
                im = Image.open(io.BytesIO(roh))
                if max(im.size) > 2560: gross.append(n)
            except Exception:
                schlecht.append(n)
        if schlecht: F(f"nicht lesbar: {schlecht[:5]}")
        else:        OK("jedes Bild ist als JPEG lesbar")
        if gross:
            W(f"{len(gross)} Bilder über 2560 px – WordPress legt dann zusätzlich eine "
              f"Datei mit -scaled an; der Import findet trotzdem das Original")
        else:
            OK("kein Bild über 2560 px, WordPress benennt nichts um")
        mb = os.path.getsize(FOTOS) / 1024 / 1024
        OK(f"{len(namen)} Fotos, {mb:.0f} MB im Paket")
        if mb > 64:
            W(f"{mb:.0f} MB sind zu viel für einen einzelnen Upload – die Anleitung sagt "
              f"deshalb: entpacken und in Paketen von hundert in die Mediathek ziehen")
    return {os.path.basename(n): None for n in namen}


def bild_schluessel(dateiname):
    """Dieselbe Zuordnung wie Kikripp_Admin::bild_schluessel()."""
    name = re.sub(r"\.[a-zA-Z0-9]+$", "", os.path.basename(dateiname)).upper()
    t = re.fullmatch(r"(F-\d{3,})-\d+", name)
    return (t.group(1), False) if t else (name, True)


def pruefe_import(vorhanden):
    print("\n== 3. katalog_import.json ==")
    if not os.path.exists(IMPORT):
        F("Datei fehlt"); return
    with io.open(IMPORT, encoding="utf-8") as f:
        try:
            liste = json.load(f)
        except Exception as e:
            F(f"keine gültige JSON-Datei: {e}"); return
    if not isinstance(liste, list):
        F("die Datei enthält keine Liste"); return
    OK(f"gültiges JSON, {len(liste)} Zeilen, {os.path.getsize(IMPORT)//1024} KB")

    PFLICHT = ["nr", "titel", "beschr", "kat", "raum", "zustand", "masse", "menge",
               "einheit", "preis", "basis", "versand", "marke", "buendel", "foto",
               "sortierung", "aktiv", "im_katalog", "mengenhinweis"]
    fehlt = {k for a in liste for k in PFLICHT if k not in a}
    if fehlt: F(f"Feld fehlt in mindestens einer Zeile: {sorted(fehlt)}")
    else:     OK("jede Zeile bringt alle Felder mit, die der Import ausliest")

    nummern = [a["nr"] for a in liste]
    doppelt = sorted({n for n in nummern if nummern.count(n) > 1})
    if doppelt: F(f"Artikelnummer doppelt: {doppelt}")
    else:       OK("keine Artikelnummer doppelt")
    leer = [i for i, a in enumerate(liste) if not str(a.get("nr") or "").strip()]
    if leer: F(f"{len(leer)} Zeilen ohne Artikelnummer – der Import überspringt sie")
    else:    OK("keine Zeile ohne Artikelnummer")

    sichtbar = [a for a in liste if a["aktiv"] and a["im_katalog"]]
    OK(f"{len(sichtbar)} Positionen werden im Katalog angezeigt")

    krumm = [a["nr"] for a in sichtbar if not isinstance(a["preis"], (int, float)) or a["preis"] <= 0]
    if krumm: F(f"Preis fehlt oder ist null: {krumm[:8]}")
    else:     OK("jede sichtbare Position hat einen Preis größer null")
    ohne = [a["nr"] for a in sichtbar if not isinstance(a["menge"], int) or a["menge"] < 1]
    if ohne: F(f"Menge kleiner eins: {ohne[:8]}")
    else:    OK("jede sichtbare Position hat eine Menge ab eins")
    lang = [a["nr"] for a in liste if len(str(a["titel"])) > 200]
    if lang: W(f"{len(lang)} sehr lange Bezeichnungen")
    ohne_titel = [a["nr"] for a in sichtbar if not str(a["titel"]).strip()]
    if ohne_titel: F(f"ohne Bezeichnung: {ohne_titel[:8]}")
    else:          OK("jede sichtbare Position hat eine Bezeichnung")

    # --- die Zuordnung, an der es im Plugin schon einmal gehakt hat ---
    karte = {}
    for datei in vorhanden:
        basis, genau = bild_schluessel(datei)
        if genau or basis not in karte:
            karte[basis] = datei
    fehlend = sorted({a["foto"] for a in sichtbar if a["foto"] and a["foto"].upper() not in karte})
    if fehlend:
        F(f"{len(fehlend)} Fotos werden nach dem Hochladen nicht gefunden: {fehlend[:10]}")
    else:
        OK("jedes Foto einer sichtbaren Position wird in der Mediathek gefunden")
    ohne_foto = [a["nr"] for a in sichtbar if not a["foto"]]
    if ohne_foto:
        W(f"{len(ohne_foto)} sichtbare Positionen ohne Fotoverweis: {ohne_foto[:8]}")
    else:
        OK("jede sichtbare Position hat einen Fotoverweis")

    ueberzaehlig = sorted(set(vorhanden) - {karte[b] for b in karte if any(
        a["foto"].upper() == b for a in sichtbar)})
    if ueberzaehlig:
        W(f"{len(ueberzaehlig)} Fotos im Paket, auf die keine sichtbare Position direkt zeigt "
          f"– das sind die im Text genannten weiteren Ansichten")


def main():
    print("== Übergabeprüfung: die drei Dateien für WordPress ==")
    pruefe_plugin()
    vorhanden = pruefe_fotos()
    pruefe_import(vorhanden)
    print(f"\n== Ergebnis: {len(fehler)} Fehler, {len(hinweise)} Hinweise ==")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
