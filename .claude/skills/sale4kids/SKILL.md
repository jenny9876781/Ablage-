---
name: sale4kids
description: "Arbeitsablauf für die Auflösung und den Verkauf des Inventars der Kikripp GmbH (Kinderkrippe Villingen-Schwenningen). Auslösen bei dem Stichwort 'sale4kids', beim Hochladen neuer Artikelfotos (HEIC/JPG aus dem Haus), bei Rückgabe einer überarbeiteten Datei 01_Artikelstamm_kikripp.xlsx, oder bei Bitten wie 'neue Artikel aufnehmen', 'Angebot für die Klinik aktualisieren', 'Katalog neu erzeugen', 'Preise eingearbeitet', 'Fotos sind da'. Nicht verwenden für andere Verkaufs- oder Inventarprojekte."
---

# sale4kids — Inventarauflösung Kikripp GmbH

Die Kikripp GmbH (Kinderkrippe, Hermann-Schwer-Str. 1, 78048 Villingen-Schwenningen) löst ihren
Betrieb auf und verkauft das gesamte Inventar. Erster Interessent ist Mediclin Königsfeld
(Frau Jessica Rose). Ansprechpartnerin im Haus: Jenny Preisigke.

**Grundprinzip: `daten/artikel_kikripp.csv` ist die einzige Quelle der Wahrheit.** Alle
Ausgabedateien werden daraus erzeugt und sind jederzeit wegwerfbar. Die Datenbasis nie umgehen.

---

## 1. Was der Nutzer will, und was zu tun ist

| Situation | Ablauf |
|---|---|
| **Neue Fotos hochgeladen** | Ablauf A (erfassen) |
| **Überarbeitete `01_Artikelstamm_kikripp.xlsx` hochgeladen** | Ablauf B (zurücklesen) |
| **Beides** | erst B, dann A |
| **Nur „sale4kids" ohne Anhang** | nachfragen, was ansteht; im Zweifel nur neu erzeugen (Ablauf C) |

Immer endend mit **Ablauf C** (erzeugen, prüfen, ausliefern).

---

## 2. Ablauf A — neue Fotos erfassen

### A1. Fotos aufbereiten

```bash
python3 scripts/prepare_fotos.py
```

Das Skript liest die Upload-Ordner, vergibt **dauerhafte** Nummern `F-xxx`, dreht nach EXIF,
verkleinert auf 1400 px, entfernt alle Metadaten (inkl. GPS) und überspringt inhaltsgleiche
Doppel. Es gibt aus, welche neuen Fotonummern entstanden sind.

> **Niemals `daten/fotos_index.csv` löschen und neu aufbauen.** Die Zuordnung Artikel → Foto
> hängt daran. Wird neu nummeriert, zeigen alle Artikel auf falsche Bilder.

### A2. Personen prüfen

Jedes neue Foto ansehen. Sind Personen erkennbar — auch Spiegelungen in Scheiben, gerahmte
Portraits, Teamfotos in Vitrinen —, dann in `daten/fotos_beschnitt.csv` eine Zeile ergänzen
(`Foto;Anteil_oben;Grund`), `prepare_fotos.py` erneut laufen lassen und das Ergebnis **ansehen**,
bis niemand mehr erkennbar ist. Kinderfotos dürfen unter keinen Umständen in eine Ausgabedatei.

### A3. Artikel anlegen

Neue Zeilen an `daten/artikel_kikripp.csv` anhängen. Artikelnummern **fortlaufend** ab der
höchsten vorhandenen `K-xxx` — vorhandene Nummern nie neu vergeben, auch nicht für entfallene
Positionen.

Spalten und Konventionen:

| Spalte | Regel |
|---|---|
| `ArtNr` | `K-###`, fortlaufend |
| `Bezeichnung` | kurz und verkäuflich, ohne Marketingsprache |
| `Beschreibung` | Material, Ausführung, Besonderheiten. Marke nur nennen, wenn im Bild belegt oder vom Nutzer bestätigt. |
| `Kategorie` | Möbel · Designmöbel · Kita-Ausstattung · Büro · Küchentechnik · Leuchten · Deko · Kunst · Uhren · Textilien · Pflanzen · Garten · Verbrauchsmaterial · Technik · Sonstiges |
| `Raum` | wie vom Nutzer benannt, Schreibweise bestehender Räume übernehmen |
| `Menge` | erkennbare Stückzahl |
| `Einheit` | Stück · Karton · Set · Palette · Konvolut |
| `Zustand` | neuwertig · gut · gebraucht · stark gebraucht · defekt |
| `Maße` | **leer lassen** — trägt der Mensch ein |
| `Foto` | `F-xxx` |
| `Wertklasse` | `A` über 150 € oder Markenware · `B` 30–150 € · `C` darunter |
| `Aktiv` | `ja` |
| `Preis_netto` | Schätzung netto, deutsches Format (`1.200,00`) |
| `Preisbasis` | `Fix` oder `VHB` |
| `Versand` | `nur Abholung` · `Versand möglich` · `Spedition` |
| `Mengenhinweis` | **immer ausfüllen:** was auf dem Foto zu sehen ist, z. B. „ca. 8 Stück im Bild – bitte nachzählen" |
| `Status` | `verfügbar` |
| `Kanal` | `Klinik` |
| übrige Verkaufsspalten | leer |

### A4. Preise schätzen

Netto, konservativ, in realistischen Stufen. Anhaltspunkt: gebrauchte Möbel 10–30 % vom
Neupreis, Markenware deutlich höher. Bei Unsicherheit lieber niedriger ansetzen und im Bericht
darauf hinweisen — der Vorgesetzte legt ohnehin final fest.

**Markenware immer als solche benennen** (Vitra, USM Haller, Kartell, Weber, Biohort). Diese
Positionen bekommen Wertklasse `A`; sie haben einen eigenen Gebrauchtmarkt und dürfen nicht im
Sammelpreis untergehen. Bereits bestätigt: Vitra Alcove und USM Haller sind echt.

Kunst: Die Acrylbilder sind **Eigenarbeiten einer Privatperson**, die Schwarzwald-Trachtenmotive
sind **Kaufware**. Das gehört in die Beschreibung.

---

## 3. Ablauf B — überarbeitete Datei zurücklesen

```bash
python3 scripts/rueckeinlesen.py [pfad/zur/01_Artikelstamm_kikripp.xlsx]
```

Ohne Pfad wird `ausgabe/01_Artikelstamm_kikripp.xlsx` genommen. Das Skript legt vorher eine
Sicherung an, übernimmt die inhaltlichen Spalten und das Blatt „Design" und meldet jede
Änderung im Klartext.

Gelöschte Zeilen werden **nicht entfernt**, sondern auf `Aktiv = entfällt` gesetzt. Selbst
ergänzte Zeilen werden übernommen (dann ohne Foto).

Den Änderungsbericht durchsehen und auffällige Werte ansprechen — etwa ein Preis, der um eine
Größenordnung abweicht, oder eine Menge, die auf 0 gesetzt wurde.

---

## 4. Ablauf C — erzeugen, prüfen, ausliefern

```bash
python3 scripts/make_signet.py                # nur wenn sich Farbe_Rot geändert hat
python3 scripts/build_artikelstamm_xlsx.py
python3 scripts/build_angebot_xlsx.py
python3 scripts/build_katalog_pdf.py
python3 scripts/build_webkatalog_mockup.py
python3 scripts/build_arbeitsanweisung_pdf.py   # nur wenn ARBEITSANWEISUNG.md geändert wurde
```

### Pflichtprüfung vor der Übergabe

```bash
python3 scripts/pruefen.py
```

Prüft doppelte Artikelnummern, fehlende Fotodateien, fehlende Preise, den Fotoindex, die
Blattstruktur, **alle Formelbezüge der Verkaufsübersicht gegen die Spaltenüberschriften**,
Text in Zahlenspalten und die Größe der Ausgabedateien; danach werden die Summen unabhängig
nachgerechnet. Endet mit Code 1, wenn etwas beanstandet wird. **Nicht übergeben, solange
Fehler gemeldet werden.**

Zusätzlich von Hand:

- **Webkatalog** mit Chromium als Screenshot rendern und ansehen.
- **Neue Fotos** einzeln ansehen (Personen, Lesbarkeit, Schieflage).
- Nach einem Rückeinlesen stichprobenartig prüfen, dass eine als verkauft markierte Position
  noch Käufer, Rechnungsnummer und Zahlungsstatus trägt.

> LibreOffice läuft in dieser Umgebung nicht durch — `recalc.py` scheitert selbst an einer
> Tabelle mit zwei Zellen. Formeln deshalb **strukturell** prüfen (Spaltenbezüge auflösen) und
> die Erwartungswerte in Python nachrechnen. Nicht als „geprüft" ausgeben, was nicht geprüft wurde.

### Ausliefern

Dateien mit `SendUserFile` schicken, committen und auf den Arbeitsbranch pushen. Im Bericht
angeben:

- wie viele Positionen neu, geändert, entfallen
- neuer Gesamtwert und Paketpreis
- **was noch fehlt**: Maße, Stückzahlen zum Nachzählen, Typenschilder, Anlagennummern
- alles, wo die Einschätzung unsicher war

---

## 5. Unverrückbare Regeln

| Regel | Grund |
|---|---|
| Fotonummern `F-xxx` nie neu vergeben | die Artikel-Foto-Zuordnung bricht |
| Artikelnummern `K-xxx` nie wiederverwenden | Etiketten kleben physisch am Objekt |
| Verkaufsdaten nie überschreiben | Umsatz, Rechnungen und Zahlungen gingen verloren |
| Entfallene Positionen nie löschen, nur `Aktiv = entfällt` | sonst verschwindet Ware unbemerkt |
| Keine Personen in Ausgabedateien | Datenschutz, besonders Kinder |
| Preise immer netto pflegen | Firmen netto, Privatpersonen brutto (PAngV) |
| Marken nur nennen, wenn belegt | falsche Markenangabe ist eine Zusicherung |
| Keine Rechnungs-PDFs erzeugen | Rechnungen entstehen ausschließlich in DATEV |
| Farben und Firmendaten nur in `daten/design.csv` ändern | sonst driften die Dateien auseinander |
| Bei Unsicherheit im Bericht benennen, nicht kaschieren | der Mensch entscheidet |

---

## 6. Gestaltung

Rot `#C8102E` (Bollenhut), Schwarz `#1A1A1A`, Weiß, Papier `#F7F5F2`. **Rot nie flächig** — es
markiert Preise, Eingabefelder und das Paketangebot. Statusfarben bewusst neutral (Grautöne),
damit Rot der Marke gehört und nicht „verkauft" bedeutet. Eingabefelder grau, **kein Gelb**.
Das Bollenhut-Signet liegt in `assets/`.

Alle Werte stehen in `daten/design.csv` und im Blatt „Design" der Arbeitsmappe.

---

## 7. Offene Punkte (Stand 15.09.2026)

- **Logo:** liegt nur als Bildschirmbild vor. Der Schriftzug „KIKRIPP" ist derzeit gesetzter Text,
  das Signet ist nachgebaut. Sobald eine Logodatei kommt: `assets/kopflogo.png` ersetzen und
  `Farbe_Rot` aus dem Original übernehmen.
- **Maße** fehlen bei fast allen Positionen.
- **Label-Fotos** ausstehend: Vitra-Sofa, drei USM-Haller-Teile, Kartell-Stühle, Weber-Grill,
  Biohort-Boxen, große Kuckucksuhr.
- **Foto F-110** (antike Vitrine) ist wegen zweier Teamfotos stark beschnitten — ein neues Foto
  ohne die gerahmten Bilder wäre besser.
- **kikripp.de** ist aus dieser Umgebung nicht erreichbar (Netzwerkrichtlinie). Für
  Gestaltungsabgleiche Screenshots erbitten.
- Der **PDF-Katalog** ist bewusst noch im alten Layout; das Redesign wurde zurückgestellt.
