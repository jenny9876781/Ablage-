# Auflösung Kinderkrippe kikripp – Artikelverwaltung und Verkauf

Alle Verkaufsunterlagen entstehen aus **einer** gepflegten Artikelliste.

```
                     daten/artikel_kikripp.csv  →  Artikelstamm.xlsx (OneDrive)
                                   │
        ┌──────────────┬───────────┼────────────┬───────────────────┐
        ▼              ▼           ▼            ▼                   ▼
  Angebot Klinik   PDF-Katalog  Webkatalog   eBay- / Kleinanzeigen-  Verkaufsübersicht
  (Excel)          (zum Mailen) (kikripp.de)  Texte & Importdateien   + DATEV-Abtippliste
```

## Stand

| | |
|---|---|
| Positionen | 142 |
| Einheiten | 234 |
| Fotos | 112 (aus HEIC konvertiert, gedreht, verkleinert, ohne GPS-Daten) |
| Gesamtwert zu Einzelpreisen | 24.031,00 € netto (Schätzwerte) |
| Paketpreis Vorschlag (−20 %) | 19.224,80 € netto |

Alle Preise sind **Schätzwerte auf Basis der Fotos** und zur Überarbeitung gedacht.
Maße fehlen durchgängig – die Spalte `Maße` ist dafür vorbereitet.

## Ordner

| Ordner | Inhalt |
|---|---|
| `daten/` | Artikelstammdaten (CSV, semikolongetrennt, Excel-kompatibel) |
| `fotos/` | Artikelfotos `F-001.jpg` … `F-112.jpg`, sortiert nach Aufnahmezeit |
| `scripts/` | Generatoren – erzeugen aus den Daten die Ausgabedateien |
| `ausgabe/` | Die fertigen Dateien |

## Ausgabedateien

| Datei | Zweck |
|---|---|
| `01_Artikelstamm_kikripp.xlsx` | Arbeitsdatei für OneDrive. Blätter: Anleitung · Artikelstamm · Verkaufsübersicht · Rechnungen (DATEV) · Kasse |
| `02_Angebot_Klinik.xlsx` | Auswahlliste für die Klinik: Fotos, Einzelpositionen mit Wunschmengen-Spalten, Paketangebot |
| `03_Katalog_Klinik.pdf` | Bildkatalog nach Räumen, 23 Seiten, mit Positionsübersicht und Verkaufsbedingungen |
| `04_Webkatalog_MOCKUP.html` | Muster für den passwortgeschützten Katalog auf kikripp.de |

## Neu erzeugen

```bash
python3 scripts/prepare_fotos.py            # HEIC-Uploads -> fotos/F-xxx.jpg
python3 scripts/build_artikelstamm_xlsx.py
python3 scripts/build_angebot_xlsx.py
python3 scripts/build_katalog_pdf.py
python3 scripts/build_webkatalog_mockup.py
```

Voraussetzungen: `python3`, `openpyxl`, `Pillow`, `pillow-heif`, Chromium (für die PDF-Ausgabe).

## Offene Punkte

- **Maße** bei allen Möbeln ergänzen
- **Label-Fotos** für Vitra, USM Haller (3 Teile), Kartell, Weber, Biohort und die große Kuckucksuhr
- **Stückzahlen** nachzählen, wo im Feld `Mengenhinweis` „bitte nachzählen“ steht
- **Anlagennummern** aus dem Anlagenverzeichnis ergänzen
- Preise durch den Vorgesetzten freigeben, Rabattregel festlegen

## Hinweise zum Echtbetrieb

- Preise werden **netto** gepflegt. Firmen bekommen Nettopreise, Privatpersonen müssen den Bruttopreis
  sehen (Preisangabenverordnung).
- **Barzahlungen** müssen bei einer GmbH zusätzlich ins Kassenbuch (GoBD) – Blatt „Kasse“.
- Die **Rechnung selbst** wird ausschließlich in DATEV erstellt. Das Blatt „Rechnungen (DATEV)“ ist nur
  die Abtippliste, damit es kein zweites Rechnungsdokument gibt.
- Die Artikeldatei liegt in OneDrive und wird **direkt dort** bearbeitet – nicht herunterladen,
  bearbeiten, wieder hochladen.
