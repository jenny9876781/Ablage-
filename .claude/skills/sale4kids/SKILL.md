---
name: sale4kids
description: "Arbeitsablauf für die Auflösung und den Verkauf des Inventars der Kikripp GmbH (Kinderkrippe Villingen-Schwenningen). Auslösen bei dem Stichwort 'sale4kids', beim Hochladen neuer Artikelfotos (HEIC/JPG aus dem Haus), bei Rückgabe einer überarbeiteten Datei 01_Artikelstamm_kikripp.xlsx, bei einem Reservierungs-Export aus WordPress, bei Arbeiten am WordPress-Plugin kikripp-katalog, oder bei Bitten wie 'neue Artikel aufnehmen', 'Angebot für die Klinik aktualisieren', 'Katalog neu erzeugen', 'Webshop aktualisieren', 'Preise eingearbeitet', 'Fotos sind da', 'Reservierungen einlesen'. Nicht verwenden für andere Verkaufs- oder Inventarprojekte."
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
| **Reservierungs-Export aus WordPress (CSV)** | Ablauf D (Verkäufe zurückholen) |
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
| `Kanal` | `Klinik` bei Neuaufnahme; das Rückeinlesen setzt später `Webkatalog` |
| `Im_Katalog` | `ja`, wenn der Artikel im Webshop erscheinen soll, sonst `nein` |
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

## 4. Ablauf D — Verkäufe aus dem Webshop zurückholen

Der Nutzer lädt in WordPress unter **Artikelkatalog → Reservierungen** eine CSV-Datei
herunter und schickt sie her.

```bash
python3 scripts/reservierungen_einlesen.py <datei.csv>              # Probelauf
python3 scripts/reservierungen_einlesen.py <datei.csv> --schreiben  # übernehmen
```

Übernommen werden `Status`, `Käufer`, `Reserviert_für`, `Verkauft_Menge`,
`Verkaufspreis_netto` (als **Stückpreis** — der Artikelstamm multipliziert mit der Menge!),
`Verkaufsdatum` und `Kanal`. **Rechnungsnummer, Zahlung und Zahlart bleiben unberührt** —
die trägt der Mensch ein, sobald die Rechnung aus DATEV vorliegt.

Ist ein Artikel nur teilweise verkauft, wird `Status = teilverkauft` gesetzt. Meldet das
Skript überbuchte Artikel oder unbekannte Artikelnummern, **nicht schreiben**, sondern
nachfragen — dann stimmt etwas zwischen Webshop und Datenbasis nicht.

Danach immer Ablauf C.

---

## 5. Ablauf C — erzeugen, prüfen, ausliefern

```bash
python3 scripts/make_signet.py                # nur wenn sich Farbe_Rot geändert hat
python3 scripts/build_artikelstamm_xlsx.py
python3 scripts/build_angebot_xlsx.py
python3 scripts/build_katalog_import.py        # Importdatei für den Webshop
python3 scripts/build_webkatalog.py            # + --geschuetzt PASSWORT für die Fassung zum Veröffentlichen
```

Der **PDF-Katalog ist entfallen** (Entscheidung des Nutzers, September 2026); der Webshop auf
kikripp.de hat ihn abgelöst. `build_katalog_pdf.py` gibt es nicht mehr.

Am Webshop-Plugin geändert? Dann zusätzlich:

```bash
php wordpress/tests/test-logik.php             # 51 Prüfungen, muss 0 Fehler melden
php wordpress/tests/test-kette.php             # Datenbasis -> Import -> Katalog
cd wordpress && ./paketieren.sh                # erzeugt ausgabe/kikripp-katalog.zip
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

## 6. Unverrückbare Regeln

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

## 7. Gestaltung

Rot `#C8102E` (Bollenhut), Schwarz `#1A1A1A`, Weiß, Papier `#F7F5F2`. **Rot nie flächig** — es
markiert Preise, Eingabefelder und das Paketangebot. Statusfarben bewusst neutral (Grautöne),
damit Rot der Marke gehört und nicht „verkauft" bedeutet. Eingabefelder grau, **kein Gelb**.
Das Bollenhut-Signet liegt in `assets/`.

Alle Werte stehen in `daten/design.csv` und im Blatt „Design" der Arbeitsmappe.

---

## 8. Der Webshop auf kikripp.de

Seit September 2026 läuft der Verkauf über ein eigenes WordPress-Plugin in
`wordpress/kikripp-katalog/`. Es ersetzt den PDF-Katalog und die Wunschmengen-Spalten im
Klinik-Angebot. **Es gibt genau einen Reservierungsweg: den Webshop.** Wer daneben noch
eine zweite Schiene einbaut, vergibt Ware doppelt.

### Aufbau

| Datei | Aufgabe |
|---|---|
| `kikripp-katalog.php` | Plugin-Kopf, Tabellen anlegen, Vorgabewerte |
| `includes/class-kikripp-db.php` | drei Tabellen, Verfügbarkeit, Reservierung mit Sperre |
| `includes/class-kikripp-zugang.php` | gemeinsames Passwort, signierter Keks |
| `includes/class-kikripp-mail.php` | Benachrichtigung und Bestätigung |
| `includes/class-kikripp-rest.php` | `/zugang`, `/artikel`, `/reservierung` |
| `includes/class-kikripp-admin.php` | Reservierungen, Import, Einstellungen, CSV-Export |
| `includes/class-kikripp-frontend.php` | Kurzbefehl `[kikripp_katalog]` |
| `assets/katalog.css`, `assets/katalog.js` | Oberfläche |

### Was man dabei nicht kaputt machen darf

| Regel | Grund |
|---|---|
| Verfügbarkeit immer **rechnen**, nie mitzählen | ein mitgeführter Zähler läuft irgendwann aus dem Ruder |
| Reservieren nur in einer Transaktion mit `SELECT … FOR UPDATE` | sonst überbuchen zwei gleichzeitige Besucher |
| Preis beim Reservieren **einfrieren** | sonst ändert eine Preispflege rückwirkend den Vorgang |
| Alle Antworten mit `Cache-Control: no-store` | das Cache-Plugin der Seite würde sonst alte Bestände ausliefern |
| Die Katalogseite liefert nur eine statische Hülle | damit der Seiten-Cache nichts Veraltetes zeigt |
| Bezahlte Artikel fallen aus dem Katalog, nicht aus der Datenbank | die Verkaufsdaten werden gebraucht |
| Artikel, die nicht mehr in der Importdatei stehen, werden stillgelegt statt gelöscht | an ihnen hängen Reservierungen und Verkäufe |
| `build_katalog_import.py` lädt mit `nur_aktive=False` | sonst erfährt WordPress nie, dass eine Position entfallen ist |
| Fotos kommen aus der Mediathek, nicht ins ZIP | sonst wird das Plugin 25 MB groß |

### Prüfen

```bash
php wordpress/tests/test-logik.php     # 51 Prüfungen gegen eine SQLite-Attrappe
php wordpress/tests/test-kette.php     # ganze Kette mit der echten Importdatei
```

Deckt ab: Teil- und Vollreservierung, Überbuchung, Preiseinfrieren, Stornieren, Ablauf und
Verlängerung, Bezahltsetzen, Mailversand samt Fehlerfall, Testdaten löschen, ungültige
Eingaben, stillgelegte Artikel.

Für die Oberfläche gibt es einen echten Browsertest:

```bash
rm -f /tmp/kikripp-web.sqlite /tmp/kikripp-optionen.json
cd wordpress/tests && php -S 127.0.0.1:8801 -t /tmp/kikweb server.php &
python3 <browsertest.py>       # Chromium: /opt/pw-browsers/chromium-1194/chrome-linux/chrome
```

`/tmp/kikweb` braucht die Verweise `assets` → `wordpress/kikripp-katalog/assets` und
`fotos` → `fotos`. Der Testserver bedient die **echten** REST-Rückrufe über SQLite und
schreibt alle Mails nach `/tmp/kikripp-mails.log`.

> Ändert sich das Datenbankschema, `SCHEMA_VERSION` in `class-kikripp-db.php` hochzählen
> **und** die Testdatenbanken unter `/tmp` löschen — die SQLite-Attrappe kennt kein `ALTER TABLE`.

### Ausliefern

```bash
cd wordpress && ./paketieren.sh        # ausgabe/kikripp-katalog.zip
```

Zusammen mit `ausgabe/katalog_import.json` schicken. Die Einrichtung steht in
`WEBSHOP_EINRICHTEN.md`.

### Das Passwort

`2026sales4kids`, gesetzt beim Aktivieren des Plugins. **Es steht bewusst in keiner Datei
des Projekts** (ein älterer Stand hatte es im README — das ist in der Git-Historie noch zu
finden, deshalb wurde es gewechselt). Wo ein Skript es braucht, kommt es aus der Umgebung:
`export KIKRIPP_KATALOG_PW=…`.

### Die alte Fassung als Artifact

`scripts/build_webkatalog.py --geschuetzt PASSWORT` erzeugt weiterhin
`ausgabe/06_Webkatalog_geschuetzt.html` (AES-256-GCM, PBKDF2 mit 210.000 Runden). Das war
die Zwischenlösung, bevor der Webshop stand; aktuelle Adresse
https://claude.ai/artifact/HdDGxJMQAWQ96Sy6z6Po4d. **Sobald der Webshop live ist, wird sie
nicht mehr gepflegt** — sie kennt keine Reservierungen und würde veraltete Bestände zeigen.
`04_Webkatalog_MOCKUP.html` bleibt als Datei zum Offline-Weiterleiten.

## 9. Offene Punkte (Stand 16.09.2026)

- **Webshop ist noch nicht installiert.** Plugin, Fotos und Importdatei liegen in `ausgabe/`,
  die Einrichtung übernimmt der Nutzer nach `WEBSHOP_EINRICHTEN.md`. Danach erfragen, ob der
  Mailversand aus WordPress funktioniert hat — sonst muss ein SMTP-Zugang dazu.
- **Startseite:** Der Nutzer will den Katalog unter www.kikripp.de. Meine Empfehlung steht in
  der Anleitung: Startseite behalten, Katalog auf `/katalog`, damit nicht jeder Besucher der
  Firmenseite vor einer Passwortabfrage steht. Entscheidung offen.
- **Noch nicht alle Artikel erfasst.** Es kommen weitere Fotos und Kategorien dazu. Der Import
  ist darauf ausgelegt: neue Datei erzeugen, hochladen, bestehende Reservierungen bleiben.
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
- **Rechtstexte** im Webshop sind von mir formuliert, nicht anwaltlich geprüft. Sie stehen in
  den Plugin-Einstellungen und lassen sich dort jederzeit ersetzen.
