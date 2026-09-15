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
| `daten/` | `artikel_kikripp.csv` (Artikelstamm) und `design.csv` (Farben, Firmendaten, Konditionen) |
| `assets/` | Bollenhut-Signet als SVG und PNG, Kopflogo |
| `.claude/skills/sale4kids/` | Skill: Stichwort „sale4kids“ löst den ganzen Ablauf aus |
| `fotos/` | Artikelfotos `F-001.jpg` … `F-112.jpg`, sortiert nach Aufnahmezeit |
| `scripts/` | Generatoren – erzeugen aus den Daten die Ausgabedateien |
| `ausgabe/` | Die fertigen Dateien |

## Ausgabedateien

| Datei | Zweck |
|---|---|
| `01_Artikelstamm_kikripp.xlsx` | Arbeitsdatei für OneDrive. Blätter: Anleitung · Artikelstamm · Verkaufsübersicht · Rechnungen (DATEV) · Kasse |
| `02_Angebot_Klinik.xlsx` | Auswahlliste für die Klinik: Fotos, Einzelpositionen mit Wunschmengen-Spalten, Paketangebot |
| `03_Katalog_Klinik.pdf` | Bildkatalog nach Räumen, 23 Seiten, mit Positionsübersicht und Verkaufsbedingungen |
| `04_Webkatalog_MOCKUP.html` | Muster des Katalogs, offline lauffähig, ohne Verschlüsselung |
| `06_Webkatalog_geschuetzt.html` | dieselbe Seite mit AES-verschlüsselten Daten – als Artifact veröffentlicht |

## Design

Farben, Firmendaten und Konditionen stehen ausschließlich in `daten/design.csv` und im Blatt
„Design" der Arbeitsmappe. Wer dort etwas ändert und neu erzeugt, ändert es überall.

| Rolle | Wert | Einsatz |
|---|---|---|
| Bollenhut-Rot | `#C8102E` | nur als Akzent: Preise, Paketangebot, Eingabefelder, Signet |
| Schwarz | `#1A1A1A` | Kopfbalken, Struktur, Text |
| Papier | `#F7F5F2` | ruhige Flächen |
| Feld Klinik / intern | `#E4E4E4` / `#F2F2F2` | Ausfüllfelder |

Die Statusfarben im Artikelstamm sind bewusst neutral gehalten (Grautöne), damit Rot
eindeutig der Marke gehört und nicht „verkauft" bedeutet.

## Ablauf beim Überarbeiten

```bash
# 1. Artikelstamm in OneDrive überarbeiten (Preise, Maße, Mengen, Blatt „Design“)
# 2. Datei zurückspielen und einlesen – legt vorher eine Sicherung an:
python3 scripts/rueckeinlesen.py [pfad/zur/Artikelstamm.xlsx]

# 3. Alles neu erzeugen:
python3 scripts/prepare_fotos.py            # nur wenn neue Fotos dazugekommen sind
python3 scripts/make_signet.py              # nur wenn sich die Markenfarbe geändert hat
python3 scripts/build_artikelstamm_xlsx.py
python3 scripts/build_angebot_xlsx.py
python3 scripts/build_katalog_pdf.py
python3 scripts/build_webkatalog.py --geschuetzt 'sale4kids_2026'

# 4. Vor der Übergabe prüfen – meldet Fehler und rechnet die Summen nach:
python3 scripts/pruefen.py
```

Kürzer geht es über den Skill: **„sale4kids"** in Claude Code eingeben. Der Skill kennt den
ganzen Ablauf, die Konventionen und die Prüfschritte.

`rueckeinlesen.py` übernimmt Bezeichnung, Beschreibung, Kategorie, Raum, Menge, Einheit,
Zustand, Maße, Wertklasse, Preis, Preisbasis, Versand und Bemerkungen sowie alle Werte des
Design-Blattes. Gelöschte Zeilen werden **nicht** entfernt, sondern auf `Aktiv = entfällt`
gesetzt; selbst ergänzte Zeilen werden übernommen (dann ohne Foto).

Voraussetzungen: `python3`, `openpyxl`, `Pillow`, `pillow-heif`, Chromium (für die PDF-Ausgabe).

## Arbeitsanweisung

`ARBEITSANWEISUNG.md` — eine Seite Fließtext: Etikettieren, Fotografieren, Übergabe an Claude,
Preisfreigabe, Verkauf eintragen, Rechnungen und Kasse.

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
