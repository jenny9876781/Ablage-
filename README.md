# Auflösung Kinderkrippe – Artikelverwaltung und Verkauf

Dieses Repository enthält den **Beispielaufbau** (Stand: Muster mit erfundenen Artikeln).
Es zeigt, wie aus einer einzigen gepflegten Artikelliste alle benötigten Unterlagen entstehen.

## Grundidee

```
                     daten/artikel.csv  bzw.  Artikelstamm.xlsx
                     (die einzige Quelle der Wahrheit)
                                   │
        ┌──────────────┬───────────┼────────────┬───────────────────┐
        ▼              ▼           ▼            ▼                   ▼
  Angebot Klinik   PDF-Katalog  Webkatalog   eBay- / Kleinanzeigen-  Verkaufsübersicht
  (Excel)          (zum Mailen) (kikripp.de)  Texte & Importdateien   für Buchhaltung
```

Alles wird **einmal** erfasst. Preise, Status und Verkäufe werden nur an einer Stelle gepflegt.
Kein Nachhalten in mehreren Listen, keine doppelt verkauften Artikel.

## Ordner

| Ordner | Inhalt |
|---|---|
| `daten/` | Artikelstammdaten (CSV, semikolongetrennt, Excel-kompatibel) |
| `fotos/` | Artikelfotos, Dateiname = Artikelnummer (`K-001.jpg`) |
| `scripts/` | Generatoren – erzeugen aus den Daten die Ausgabedateien |
| `ausgabe/` | Die fertigen Dateien zum Verschicken |

## Ausgabedateien

| Datei | Zweck |
|---|---|
| `01_Artikelstamm_BEISPIEL.xlsx` | Arbeitsdatei: alle Artikel, Preise, Status, Verkäufe, Rechnungen. Blatt „Verkaufsübersicht" rechnet Umsatz, offene Rechnungen und Restbestand automatisch aus. |
| `02_Angebot_Klinik_BEISPIEL.xlsx` | Auswahlliste für einen Interessenten: Fotos, Preise, gelbe Spalten für Wunschmenge. Zurückgeschickt = Bestellung. |
| `03_Katalog_Klinik_BEISPIEL.pdf` | Bildkatalog zum Mailen, mit Positionsübersicht und Verkaufsbedingungen. |
| `04_Webkatalog_MOCKUP.html` | Klickbares Muster des passwortgeschützten Katalogs für kikripp.de (Filter, Vormerken, Reservierungsanfrage). |

## Neu erzeugen

```bash
python3 scripts/make_placeholder_fotos.py    # nur für das Beispiel
python3 scripts/build_artikelstamm_xlsx.py
python3 scripts/build_angebot_xlsx.py
python3 scripts/build_katalog_pdf.py
python3 scripts/build_webkatalog_mockup.py
```

Voraussetzungen: `python3`, `openpyxl`, `Pillow`, Chromium (für die PDF-Ausgabe).

## Hinweise zum Echtbetrieb

- **Preise netto** pflegen. Gegenüber Firmen wird netto angeboten, gegenüber Privatpersonen
  muss der Bruttopreis ausgewiesen werden (Preisangabenverordnung).
- **Anlagennummer** je Artikel eintragen, damit der Steuerberater den Anlagenabgang zuordnen kann.
- **Barzahlungen** müssen bei einer GmbH zusätzlich ins Kassenbuch (GoBD) – die Rechnung mit
  dem Vermerk „bar erhalten" allein genügt nicht.
- **Etiketten** mit der Artikelnummer an die Gegenstände im Haus kleben, damit Liste und
  Realität zusammenpassen.
