# Auflösung Kinderkrippe kikripp – Artikelverwaltung und Verkauf

Alle Verkaufsunterlagen entstehen aus **einer** gepflegten Artikelliste.

```
                     daten/artikel_kikripp.csv  →  Artikelstamm.xlsx (OneDrive)
                                   │
        ┌──────────────┬───────────┴───────────┬───────────────────┐
        ▼              ▼                       ▼                   ▼
  Angebot Klinik   katalog_import.json    Webkatalog          Verkaufsübersicht
  (Excel, nur      →  Webshop auf         (HTML, offline)     + DATEV-Abtippliste
   zum Anschauen)     kikripp.de                              + Kassenbuch
                           │
                           └─ CSV-Export der Reservierungen  →  zurück in die Datenbasis
```

**Reserviert wird ausschließlich im Webshop.** Der Artikelstamm führt Artikel, Preise,
Rechnungen und Kasse; der Webshop führt Buch über Verfügbarkeit und Interessenten; das
Klinik-Angebot ist ein reines Dokument ohne eigene Datenhaltung.

## Stand (17.09.2026)

| | |
|---|---|
| Artikelnummern | `<Raumcode>-NN`, z. B. `BE10-07` — Gebäude, Ebene, Raum, laufende Nummer |
| Räume | 62 aus den Wohnflächenplänen; erfasst sind bisher 19 |
| Positionen | 87 aktiv (55 auf „entfällt" gesetzt, Zeilen bleiben erhalten) |
| Fotos | 111 (aus HEIC konvertiert, gedreht, verkleinert, ohne GPS-Daten) |
| Gesamtwert zu Einzelpreisen | 19.653,00 € netto (Schätzwerte) |
| Paketpreis Vorschlag (−20 %) | 15.722,40 € netto |

Alle Preise sind **Schätzwerte auf Basis der Fotos** und zur Überarbeitung gedacht.
Maße fehlen durchgängig – die Spalte `Maße` ist dafür vorbereitet.

## Ordner

| Ordner | Inhalt |
|---|---|
| `daten/` | `artikel_kikripp.csv` (Artikelstamm), `raeume.csv` (62 Räume aus den Bauplänen) und `design.csv` (Farben, Firmendaten, Konditionen) |
| `assets/` | Bollenhut-Signet als SVG und PNG, Kopflogo |
| `.claude/skills/sale4kids/` | Skill: Stichwort „sale4kids“ löst den ganzen Ablauf aus |
| `fotos/` | Artikelfotos `F-001.jpg` … `F-112.jpg`, sortiert nach Aufnahmezeit |
| `scripts/` | Generatoren – erzeugen aus den Daten die Ausgabedateien |
| `wordpress/` | das Plugin `kikripp-katalog` samt Tests und Paketierskript |
| `ausgabe/` | Die fertigen Dateien |

## Ausgabedateien

| Datei | Zweck |
|---|---|
| `01_Artikelstamm_kikripp.xlsx` | Arbeitsdatei für OneDrive. Blätter: Anleitung · Artikelstamm · Verkaufsübersicht · Rechnungen (DATEV) · Kasse |
| `02_Angebot_Klinik.xlsx` | Übersichtsliste für die Klinik: Fotos, Einzelpositionen, Paketangebot. Ohne Eingabefelder – reserviert wird im Webshop. |
| `katalog_import.json` | Artikel für den Webshop, wird in WordPress hochgeladen |
| `kikripp-katalog.zip` | das WordPress-Plugin |
| `kikripp-fotos.zip` | die 111 Fotos für die Mediathek |
| `T1_Tuerschilder.docx` | Türschilder für 62 Räume, fünf je A4-Blatt |
| `T2_Erfassungsblaetter.docx` | ein Erfassungsblatt je Raum für den Rundgang |
| `T3_Erfassungsliste.xlsx` | dieselben Nummern zum Abtippen der Stückzahlen |
| `U1_Aktennotiz_Speicherplatz.docx` | Aktennotiz zur Nutzung fremden Speicherplatzes |
| `U2_Datenschutz_Absatz.docx` | Textbaustein für die Datenschutzerklärung |
| `U3_Knopf_fuer_kikripp.docx` / `.txt` | HTML-Baustein für den Knopf auf kikripp.de |
| `04_Webkatalog_MOCKUP.html` | Muster des Katalogs, offline lauffähig, ohne Verschlüsselung |
| `06_Webkatalog_geschuetzt.html` | dieselbe Seite mit AES-verschlüsselten Daten – Zwischenlösung, bis der Webshop live ist |

Der **PDF-Katalog ist entfallen**; der Webshop hat ihn abgelöst.

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
python3 scripts/build_katalog_import.py                        # Importdatei für den Webshop
python3 scripts/build_webkatalog.py --geschuetzt 'PASSWORT'    # Passwort bewusst nicht im Repo
python3 scripts/build_anleitungen_pdf.py                       # Anleitungen als PDF
python3 scripts/build_erfassung.py                             # Türschilder und Erfassungsblätter
python3 scripts/build_unterlagen_docx.py                       # Aktennotiz, Datenschutz, Knopf

# 4. Vor der Übergabe prüfen – meldet Fehler und rechnet die Summen nach:
python3 scripts/pruefen.py
```

Verkäufe aus dem Webshop kommen über den CSV-Export zurück:

```bash
python3 scripts/reservierungen_einlesen.py <export.csv>              # Probelauf
python3 scripts/reservierungen_einlesen.py <export.csv> --schreiben  # übernehmen
python3 scripts/build_artikelstamm_xlsx.py
```

Am Plugin gearbeitet? Dann vorher:

```bash
php wordpress/tests/test-logik.php     # 76 Prüfungen, muss 0 Fehler melden
php wordpress/tests/test-kette.php     # Datenbasis -> Import -> Katalog
cd wordpress && ./paketieren.sh        # erzeugt ausgabe/kikripp-katalog.zip
```

Kürzer geht es über den Skill: **„sale4kids"** in Claude Code eingeben. Der Skill kennt den
ganzen Ablauf, die Konventionen und die Prüfschritte.

`rueckeinlesen.py` übernimmt Bezeichnung, Beschreibung, Kategorie, Raum, Menge, Einheit,
Zustand, Maße, Wertklasse, Preis, Preisbasis, Versand und Bemerkungen sowie alle Werte des
Design-Blattes. Gelöschte Zeilen werden **nicht** entfernt, sondern auf `Aktiv = entfällt`
gesetzt; selbst ergänzte Zeilen werden übernommen (dann ohne Foto).

Voraussetzungen: `python3`, `openpyxl`, `Pillow`, `pillow-heif`, Chromium (für Screenshots),
`php` (für die Plugin-Tests).

## Webkatalog

Das WordPress-Plugin in `wordpress/kikripp-katalog/` bringt den Katalog ins Netz:
Zugang über einen Link mit eingebautem Passwort (`?kik=…`, wird sofort aus der Adresse
entfernt), Reservierung mit Mailbenachrichtigung an
`jennyp@kikripp.de`, geteilter Reserviert-Status für alle Besucher, Teilmengen
(„5 von 10 verfügbar"), sieben Tage Frist, Stornieren und Bezahltsetzen in der Verwaltung.

Er läuft auf **schlabberschnuten.com**, weil auf kikripp.de keine Plugins installierbar sind
(Multisite ohne Netzwerkrechte). Auf kikripp.de steht nur ein Knopf. Verkäuferin ist die
Kikripp GmbH — der Katalog nennt sie als Anbieterin und verlinkt ihr Impressum.

**Der Katalog speichert keine personenbezogenen Daten.** Name, Mail und Telefon gehen per
Mail an die Kikripp GmbH und werden unmittelbar danach aus der Datenbank gelöscht. In der
Datenbank bleiben nur Artikelnummer, Menge, Preis und Frist. Interessenten erhalten **keine**
Bestätigungsmail, sondern einen Beleg am Bildschirm.

## Anleitungen

| Datei | Inhalt |
|---|---|
| `WEBSHOP_EINRICHTEN.md` | Plugin installieren, Fotos hochladen, Artikel importieren, Seite anlegen, testen |
| `ARTIKEL_VERWALTEN.md` | Artikel streichen, Preise und Mengen ändern, Verkäufe zurückholen, was in WordPress und was in der Excel gemacht wird |
| `FOTOGRAFIEREN.md` | Etikettieren, Aufnahmen, Datenschutz, was auf den Zettel gehört |

Alle vier gibt es auch als PDF in `ausgabe/` (`A1`–`A4`) – Markdown lässt sich unter Windows
nicht ohne Weiteres öffnen. Erzeugt werden sie mit `scripts/build_anleitungen_pdf.py`.
| `ARBEITSANWEISUNG.md` | eine Seite Fließtext über den ganzen Ablauf |

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
