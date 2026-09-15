"""Erzeugt Platzhalter-Fotos fuer das Beispiel (wird spaeter durch echte Fotos ersetzt)."""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont

FARBEN = {
    "Moebel": (214, 224, 236), "Spielmaterial": (230, 224, 240),
    "Kuechentechnik": (216, 232, 224), "Buero": (236, 230, 214),
    "Verbrauchsmaterial": (240, 224, 224), "Aussenbereich": (222, 238, 214),
    "Musik": (238, 226, 236), "IT": (220, 228, 238),
}
os.makedirs("fotos", exist_ok=True)

def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

from lib import lade_artikel
if True:
    for r in lade_artikel():
        W, H = 800, 600
        img = Image.new("RGB", (W, H), FARBEN.get(r["Kategorie"], (228, 228, 228)))
        d = ImageDraw.Draw(img)
        d.rectangle([12, 12, W - 12, H - 12], outline=(255, 255, 255), width=6)
        d.text((W // 2, H // 2 - 70), r["ArtNr"], font=font(72), fill=(90, 100, 115), anchor="mm")
        txt = r["Bezeichnung"]
        if len(txt) > 30:
            txt = txt[:29] + "..."
        d.text((W // 2, H // 2 + 20), txt, font=font(30), fill=(110, 120, 135), anchor="mm")
        d.text((W // 2, H - 60), "PLATZHALTER - hier kommt euer Foto hin",
               font=font(22), fill=(140, 148, 160), anchor="mm")
        img.save(f"fotos/{r['ArtNr']}.jpg", quality=88)
print("Platzhalter-Fotos erzeugt:", len(os.listdir("fotos")))
