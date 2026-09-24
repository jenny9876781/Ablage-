"""Packt die Fotos, die der Webkatalog braucht, zu ausgabe/kikripp-fotos.zip.

Das Plugin findet ein Bild über den Dateinamen in der Mediathek (F-123.jpg). In das
Paket gehören deshalb genau die Fotos, auf die eine im Katalog sichtbare Position
zeigt - und zusaetzlich die, die in einem Mengenhinweis als weitere Ansicht genannt
sind ("ist auf Foto F-456 zu sehen"). Alles andere wuerde die Mediathek unnoetig
fuellen und das Hochladen verlaengern.

    python3 scripts/build_fotopaket.py
"""
import os, re, sys, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import lade_artikel, AUSGABE, FOTO_DIR

ZIEL = os.path.join(AUSGABE, "kikripp-fotos.zip")
VERWEIS = re.compile(r"\bF-\d{3}\b")


def gebraucht():
    namen = set()
    for a in lade_artikel():
        if (a.get("Im_Katalog") or "ja").strip().lower() != "ja":
            continue
        if a["Foto"]:
            namen.add(a["Foto"].strip())
        # weitere Ansichten, die im Text genannt sind
        namen |= set(VERWEIS.findall(a.get("Mengenhinweis") or ""))
    return sorted(namen)


def main():
    namen = gebraucht()
    fehlt = [n for n in namen if not os.path.exists(os.path.join(FOTO_DIR, n + ".jpg"))]
    if fehlt:
        raise SystemExit("Fotodatei fehlt: " + ", ".join(fehlt))
    if os.path.exists(ZIEL):
        os.remove(ZIEL)
    with zipfile.ZipFile(ZIEL, "w", zipfile.ZIP_STORED) as z:   # JPEG ist schon komprimiert
        for n in namen:
            z.write(os.path.join(FOTO_DIR, n + ".jpg"), f"fotos/{n}.jpg")
    kb = os.path.getsize(ZIEL) // 1024
    print(f"geschrieben: {ZIEL}  ({len(namen)} Fotos, {kb//1024} MB)")
    print(f"             {namen[0]} bis {namen[-1]}")


if __name__ == "__main__":
    main()
