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

## 1b. Das Raumschema

`daten/raeume.csv` ist die Raumstammdatei, abgeleitet aus den Wohnflächenplänen von Karl Altmann
(2019): **62 Räume**. Der Code sagt Gebäude und Ebene:

| Präfix | Bereich | Räume |
|---|---|---|
| `NU` | Neubau, Untergeschoss | 7 — hier liegt auch der Eingang / die Elternlounge (`NU01`) |
| `NE` | Neubau, Erdgeschoss | 8 |
| `BU` | Bestandsgebäude, Untergeschoss | 14 |
| `BE` | Bestandsgebäude, Erdgeschoss | 17 |
| `BA` | Bestandsgebäude, Attika | 13 |
| `TE` | Terrassen | `TE01` ebenerdig (drei zusammengefasst), `TE02` Dachterrasse |
| `GA` | Gartenanlage | 1 |

Die Umstellung von `K-###` auf dieses Schema ist am 17.09.2026 mit
`scripts/umnummerieren.py` gelaufen und **läuft nur einmal**; das Skript bricht ab, wenn
`Alt_ArtNr` schon gefüllt ist. Die Zuordnung der alten Raumnamen steht dort als Tabelle
`ZUORDNUNG` — sie ist vom Nutzer bestätigt und dokumentiert, welcher alte Sammelname wohin ging.

> Entfallene Positionen behalten ihre alte `K-###`-Nummer. Sie sollen im Raum keine Nummer
> verbrauchen, sonst beginnt das Erfassungsblatt mit einer Lücke.

### Unterlagen für den Rundgang

```bash
python3 scripts/build_erfassung.py
```

Erzeugt drei Dateien in `ausgabe/`:

| Datei | Zweck |
|---|---|
| `T1_Tuerschilder.docx` | fünf Räume je A4-Blatt, zum Ausschneiden und an die Tür kleben |
| `T2_Erfassungsblaetter.docx` | ein Blatt je Raum; bereits erfasste Artikel stehen grau hinterlegt oben mit ihrer Nummer, darunter freie Nummern |
| `T3_Erfassungsliste.xlsx` | dieselben Nummern zum Abtippen der Stückzahlen, kommt zum Einlesen zurück |

Zeilen je Raum nach Fläche: unter 5 m² fünf, bis 20 m² fünfzehn, bis 40 m² fünfundzwanzig,
darüber vierzig — mindestens aber die schon erfassten Artikel plus zehn Reserve.

**Das Türschild ist gleichzeitig das Raumblatt zum Fotografieren.** Ein eigenes Raumblatt
braucht es nicht mehr.

---

### Raumname im Katalog ≠ Raumbezeichnung im Haus

Seit dem 24.09.2026 zeigt der Katalog **Funktionsnamen ohne Geschoss**: „Gruppenraum",
„Schlafraum", „Flur", „Küche". Mehrere Räume dürfen denselben Namen tragen — das
Auswahlfeld „Alle Räume" baut sich aus den *verschiedenen* Namen und bündelt sie dann
zu einem Eintrag. Aus 36 Einträgen wurden so 24, und ein Käufer sucht ohnehin nach
„Sachen aus einem Gruppenraum", nicht nach „Gruppenraum 5 im Neubau-Untergeschoss".

Zugeordnet wird über den **Raumcode**, der in jeder Artikelnummer steckt. Der Code ist
die Arbeitsebene, der Name die Außenwirkung. Wer einen Raum umbenennt, ändert
`daten/raeume.csv` **und** die Spalte `Raum` in jeder Artikelzeile — `pruefen.py`
prüft, dass beide zusammenpassen.

Nicht in den Katalog gehören: interne Nummerierungen („Gruppenraum 5"), Bauwörter
(„Attika") und Bezeichnungen, die nach außen schief wirken („Klassenzimmer" in einer
Kinderkrippe → „Lernraum").

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
Portraits, Teamfotos in Vitrinen —, dann in `daten/fotos_beschnitt.csv` eine Zeile ergänzen,
`prepare_fotos.py` erneut laufen lassen und das Ergebnis **ansehen**, bis niemand mehr erkennbar
ist. Kinderfotos dürfen unter keinen Umständen in eine Ausgabedatei.

Spalten: `Foto;Anteil_oben;Maske;Grund`

| Mittel | wann |
|---|---|
| `Anteil_oben` | die Person steht am oberen Bildrand — ein Streifen fällt weg |
| `Maske` | die Person steckt **mitten** im Bild: ein gerahmtes Foto in der Vitrine, eine Spiegelung in der Gerätescheibe. Rechtecke `x1/y1/x2/y2`, Werte 0..1 bezogen auf das **fertige** Bild, mehrere durch Leerzeichen. Die Fläche wird zum Mosaik gerechnet und dann weichgezeichnet — nicht umkehrbar. |

> Beides greift auch bei Fotos, die schon auf der Platte liegen: der Index merkt sich eine
> Signatur der Vorgabe, und weicht sie ab, wird das Bild aus der Quelldatei neu erzeugt. Die
> Fotonummer bleibt. Fehlt die Quelldatei, warnt das Skript und ändert nichts.
>
> **Glas spiegelt.** Bei Geräten, Vitrinen und Bilderrahmen immer zweimal hinsehen — in F-119
> war ein Kinderfoto nur als Spiegelung in der Waschmaschinenscheibe zu sehen.

### A3. Artikel anlegen

Neue Zeilen an `daten/artikel_kikripp.csv` anhängen. Die Artikelnummer ergibt sich aus dem Raum:
`<Raumcode>-NN`, fortlaufend ab der höchsten im Raum vorhandenen Nummer. Nummern nie neu vergeben,
auch nicht für entfallene Positionen.

Steht die Nummer schon auf einem Post-it im Foto, gilt **die vom Post-it** — nicht selbst
weiterzählen. Die Erfassungsblätter (`T2`) geben die Nummern vor.

Spalten und Konventionen:

| Spalte | Regel |
|---|---|
| `ArtNr` | `<Raumcode>-NN`, z. B. `BE10-07` — die laufende Nummer je Raum aus `daten/raeume.csv` |
| `Alt_ArtNr` | nur gefüllt bei Positionen aus der alten `K-###`-Zählung; nie ändern |
| `Bündel` | **Sammlung über Räume hinweg.** Ein Textkennzeichen, z. B. `Schwarzwald`. Es steht als rotes Schild in der Kachel und liegt im Suchtext: wer „Schwarzwald" eintippt, bekommt die ganze Gruppe auf einen Schlag, egal in welchem Raum sie steht. Anders als `Weitere_ArtNr` wird **nichts zusammengelegt** — die Positionen bleiben einzeln reservierbar. Gedacht für Interessenten, die ein Thema komplett wollen. |
| `Weitere_ArtNr` | **Zusammenfassung über Räume.** Steht derselbe Artikel in mehreren Räumen, wird daraus **eine** Zeile: die Nummer des Raums, in dem er zuerst erfasst wurde, die **Gesamtmenge** in `Menge`, die Post-it-Nummern der anderen Räume hier (mit Komma getrennt) und die Aufteilung im Klartext im `Mengenhinweis` („2 im Gruppenraum, 2 im Gruppenraum 5"). So lebt jede Menge genau einmal — Verfügbarkeit, Reservierung und Rückeinlesen bleiben eindeutig. `pruefen.py` beanstandet eine Nummer, die hier **und** als eigene Zeile steht. Nur zusammenfassen, was wirklich gleich ist: andere Farbe oder deutlich anderer Zustand bleibt getrennt. |
| `Raumcode` | Code aus `daten/raeume.csv`; bestimmt die Artikelnummer |
| `Bezeichnung` | kurz und verkäuflich, ohne Marketingsprache |
| `Beschreibung` | Material, Ausführung, Besonderheiten. Marke nur nennen, wenn im Bild belegt oder vom Nutzer bestätigt. |
| `Kategorie` | Möbel · Designmöbel · Kita-Ausstattung · Büro · Küchentechnik · Leuchten · Deko · Kunst · Uhren · Textilien · Pflanzen · Garten · Verbrauchsmaterial · Technik · Sonstiges |
| `Marke` | **nur wenn belegt** — Typenschild, Aufdruck oder Aussage der Nutzerin. Steuert das rote Markenschild am Bild im Katalog und den Filter „nur Markenware". Leer lassen, wo die Marke nur vermutet ist: das Schild ist eine Zusicherung. Bisher belegt: Vitra, USM Haller, Kartell, Biohort, Weber, LG, Miele, Candy, Mr Maria, IKEA. |
| `Raum` | **nicht frei wählen** — der Raumname aus `daten/raeume.csv` zum jeweiligen `Raumcode` |
| `Menge` | erkennbare Stückzahl |
| `Einheit` | Stück · Karton · Set · Palette · Konvolut |
| `Zustand` | neuwertig · gut · gebraucht · stark gebraucht · defekt |
| `Maße` | **leer lassen** — trägt der Mensch ein |
| `Foto` | `F-xxx` |
| `Wertklasse` | `A` über 150 € oder Markenware · `B` 30–150 € · `C` darunter. **Nur interne Triage** — sie steuert das Markenschild im Katalog nicht (mehr). Bis 22.09. hing das Etikett „Designstück" an dieser Spalte und klebte damit auf einer Waschmaschine; seitdem trägt `Marke` das. |
| `Aktiv` | `ja` |
| `Preis_netto` | Schätzung netto, deutsches Format (`1.200,00`) |
| `Preisbasis` | `Fix` oder `VHB` |
| `Versand` | `nur Abholung` · `Versand möglich` · `Spedition` |
| `Mengenhinweis` | **immer ausfüllen:** was auf dem Foto zu sehen ist, z. B. „ca. 8 Stück im Bild – bitte nachzählen" |
| `Status` | `verfügbar` |
| `Kanal` | **leer lassen** — trägt erst der tatsächliche Verkauf ein; das Rückeinlesen setzt `Webkatalog` |
| `Im_Katalog` | `ja` für Möbel und große Dekostücke (**Welle 1**, gehen zuerst online). `nein` für Spielzeug und Konvolute (**Welle 2**) — die Zeile steht dann im Artikelstamm, aber nicht im Webkatalog und nicht im Muster-HTML. |
| `Klinik_Markierung` | `ja` färbt die Zeile im Klinik-Angebot hellblau ein (`D6E3F0`). Ohne Bedeutung im System — die Nutzerin markiert damit Positionen für sich. |
| übrige Verkaufsspalten | leer |

> **`Mengenhinweis` ist Käufertext, `Bemerkung` ist Arbeitsnotiz.** Seit dem 24.09.2026
> erscheint der Mengenhinweis im Katalog unter der Beschreibung. Dort gehört hinein, was
> ein Käufer wissen muss: was **nicht** dabei ist, dass ein Foto nur eines von mehreren
> Stücken zeigt, wie sich die Stückzahl verteilt, wer abbaut. Nicht hinein gehören
> Fotonummern, Post-it-Nummern und Notizen an uns („bitte nachzählen") — die stehen in
> der `Bemerkung`, die nirgends veröffentlicht wird.

### A4. Preise schätzen

Netto, konservativ, in realistischen Stufen. Anhaltspunkt: gebrauchte Möbel 10–30 % vom
Neupreis, Markenware deutlich höher. Bei Unsicherheit lieber niedriger ansetzen und im Bericht
darauf hinweisen — der Vorgesetzte legt ohnehin final fest.

> **Möbel sind grundsätzlich `gebraucht`, nicht `gut`.** Angabe der Nutzerin (22.09.):
> „die Möbel sind alle in gebrauchtem Zustand und abgelebt von den Kindern." Auf dem Foto
> sieht ein weiß beschichtetes Kita-Möbel makellos aus — das täuscht. `gut` nur im
> Personal- und Bürobereich, und auch dort nur nach Rückfrage. Geräte mit Typenschild
> (Waschmaschine, Trockner) und Kunststoffdeko sind davon nicht betroffen.

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

**Vor dem Schreiben immer ein Probelauf.** `rueckeinlesen.py` schreibt sofort. Bei einer
zurückkommenden Mappe deshalb zuerst mit einem kurzen Wegwerf-Skript gegen
`daten/artikel_kikripp.csv` vergleichen und die Liste der Abweichungen lesen — erst dann
einlesen. Danach ein zweiter Vergleich gegen `git show HEAD:daten/artikel_kikripp.csv`
trennt die sachlichen Änderungen (Preis, Menge, Aktiv, Bezeichnung) von den redaktionellen
und macht sie berichtsfähig.

**Worauf beim Bericht besonders zu achten ist:** ob ein geleerter `Mengenhinweis` einen
Ausschluss mitgenommen hat („Der Inhalt gehört nicht dazu"). Das ist Käufertext mit
rechtlicher Wirkung — steht er weder im Hinweis noch in der Beschreibung, zeigt das Foto
mehr, als verkauft wird. Nicht selbst zurückschreiben, sondern ansprechen.

Zeilenumbrüche aus Excel (Alt+Enter) landen als `\n` in der CSV. Katalog und Muster-HTML
machen daraus ein `<br>` — maskiert wird **vor** der Umwandlung, nie danach.

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
python3 scripts/build_katalog_import.py        # Importdatei für den Webshop
python3 scripts/build_fotopaket.py             # Fotos für die Mediathek (kikripp-fotos.zip)
python3 scripts/build_webkatalog.py            # + --geschuetzt PASSWORT für die Fassung zum Veröffentlichen
python3 scripts/build_anleitungen_pdf.py       # nur wenn sich eine Anleitung geändert hat
python3 scripts/build_erfassung.py             # nur wenn sich Räume oder erfasste Artikel geändert haben
```

> Die Nutzerin kann **keine .md-Dateien öffnen** (Windows). Anleitungen deshalb immer als
> PDF mitschicken, nicht als Markdown.

Der **PDF-Katalog ist entfallen** (Entscheidung des Nutzers, September 2026); der Webshop auf
kikripp.de hat ihn abgelöst. `build_katalog_pdf.py` gibt es nicht mehr.

Am Webshop-Plugin geändert? Dann zusätzlich:

```bash
php wordpress/tests/test-logik.php             # 76 Prüfungen, muss 0 Fehler melden
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

> LibreOffice läuft in dieser Umgebung **überhaupt nicht** — es lädt nicht einmal eine leere
> `.docx`. Word-Dateien deshalb strukturell prüfen (python-docx wieder öffnen, Zeilen, Nummern
> und Vorbelegung zählen) und für die Optik eine HTML-Nachbildung mit Chromium rendern.
> Dasselbe gilt für Excel: `recalc.py` scheitert selbst an einer
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
| Artikelnummern nie wiederverwenden, auch nicht die alten `K-xxx` | Etiketten kleben physisch am Objekt |
| `Raumcode` und Artikelnummer müssen zusammenpassen | `pruefen.py` beanstandet das sonst |
| Raumnamen nur in `daten/raeume.csv` ändern | sonst driften Katalog, Blätter und Schilder auseinander |
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

## 7b. Die Arbeitsmappe `01_Artikelstamm_kikripp.xlsx`

Blatt **Artikelstamm**, Spalte A ist **Bild**: je Zeile ein Miniaturfoto des Artikels, dasselbe
Bild wie im Webkatalog. Damit lässt sich der Preis am Stück beurteilen, ohne die Fotos daneben
zu öffnen. Drei Dinge hängen daran zusammen und dürfen nicht einzeln geändert werden:

* `BILD_PX = 130` bestimmt Kantenlänge, Zeilenhöhe (`ZEILE_PT`) und Spaltenbreite. Die
  Miniaturen liegen in `ausgabe/.miniaturen/` (gitignoriert) und werden zwischengespeichert;
  ein zweiter Lauf ist dadurch schnell. Die Mappe wächst dadurch auf rund 1,5 MB.
* Die Bilder hängen an einem **`TwoCellAnchor` mit `editAs="twoCell"`**. Nur so wird ein Bild
  beim Filtern zusammen mit seiner Zeile ausgeblendet. Ein `OneCellAnchor` (das, was
  `ws.add_image(bild, "A3")` erzeugt) bliebe stehen und stünde dann beim falschen Artikel.
* **Sortieren ist im Blatt gesperrt** (`ws.protection.sort = True`). Excel ordnet beim
  Sortieren die Zeilen um, lässt die Bilder aber stehen — danach passt kein Foto mehr zu
  seiner Zeile. Filtern ist erlaubt und erledigt dasselbe. Steht in der Anleitung.

Fixierung ist **G3**: Bild, ArtNr, Raumcode, Raum, Bezeichnung, Menge bleiben stehen. Die
Detailspalten `Kategorie` bis `Maße` sind eine zugeklappte Gruppe, damit `Preis_netto` ohne
langes Scrollen neben dem Bild steht; die Verkaufsspalten sind wie bisher zugeklappt.

Zwei Prüfungen halten die **Anleitung** mit der Wirklichkeit im Gleichstand, weil beides schon
einmal auseinandergelaufen ist:

* `pruefen.py`, Abschnitt **4b**: die Zahlen in `WEBSHOP_EINRICHTEN.md` (Fotos, MB, „417 neu",
  sichtbare Positionen) müssen zu den Daten passen. Die Nutzerin liest sie beim Aufbau als
  Sollwert ab — veraltet schicken sie sie auf eine Fehlersuche, die es nicht gibt.
* `pruefe_uebergabe.py`, Abschnitt **4**: jedes Feld der Einstellungsseite aus
  `class-kikripp-admin.php` muss in der Anleitung vorkommen. Die Tabelle dort steht in
  **derselben Reihenfolge wie das Formular** — das ist Absicht, die Nutzerin arbeitet sie
  daneben ab.

Nach jedem Umbau der Mappe **zwei Proben**: der Rundlauf (`rueckeinlesen.py`-Logik gegen die
frisch gebaute Datei, erwartet 0 Abweichungen) und die Bildzuordnung (Prüfsumme des
eingebetteten Bildes gegen die erwartete Miniatur, Zeile für Zeile). LibreOffice kann in
dieser Umgebung **keine** xlsx laden — auch keine triviale. Das ist kein Fehler der Datei;
geprüft wird deshalb über das Zip und die Zeichnungs-XML, nicht über eine Bildschirmansicht.

---

## 8. Der Webkatalog

Seit September 2026 läuft der Verkauf über ein eigenes WordPress-Plugin in
`wordpress/kikripp-katalog/`. Es ersetzt den PDF-Katalog und die Wunschmengen-Spalten im
Klinik-Angebot. **Es gibt genau einen Reservierungsweg: den Katalog.** Wer daneben noch
eine zweite Schiene einbaut, vergibt Ware doppelt.

### Wo er läuft, und warum das wichtig ist

Der Katalog liegt seit dem **28.09.2026** auf **www.kikripp.de/artikelkatalog** — der eigenen
Website der Gesellschaft. Die Nutzerin ist dort **Super-Admin**; die frühere Annahme, die
Netzwerkverwaltung sei ihr gesperrt, war falsch. Damit sind die Zwischenlösung über
schlabberschnuten.com, die Aktennotiz `U1` und der Knopf `U3` **gegenstandslos** — die beiden
Unterlagen werden nicht mehr erzeugt.

kikripp.de ist ein **Multisite-Netzwerk**. Das Plugin wird über die **Netzwerkverwaltung**
installiert und danach **nur auf der Seite KIKRIPP** aktiviert, nicht im Netzwerk: der
Katalog gehört auf eine Website, nicht auf alle.

Was trotzdem so bleibt, wie es ist:

| Regel | Grund |
|---|---|
| Der Firmenname kommt aus `kikripp_firma`, **nie** aus `get_bloginfo('name')` | der Seitenname im Netzwerk ist nicht zwingend die Firmierung, und im Mailbetreff muss die Firma stehen |
| Unter dem Katalog steht ein **Anbieter-Block** mit Kikripp-Adresse und Links auf Impressum und Datenschutz | Anbieterkennzeichnung am Angebot selbst; sie bleibt richtig, auch wenn die Seite später umzieht |
| **Keine personenbezogenen Daten** in der Datenbank | war ursprünglich wegen des fremden Speicherplatzes so gebaut. Der Grund ist weggefallen, die Regel bleibt: weniger gespeicherte Daten sind weniger Risiko, und die Mails sind das Kontaktarchiv. **Nicht zurückbauen.** |

> **Offen und blockierend für den Livegang:** Auf kikripp.de stehen **Impressum und
> Datenschutz als Entwurf** (Stand 28.09.2026), sind also öffentlich nicht erreichbar. Der
> Katalog verlinkt beide. Ohne Veröffentlichung geht kein Link hinaus — § 5 DDG und
> Art. 13 DSGVO. Außerdem ist die Startseite auf *Wartung* gesetzt; ob ein Wartungsplugin
> Besucher aussperrt, ist noch zu prüfen.

### Der Ablauf einer Reservierung

1. Reservieren läuft in einer Transaktion mit Sperre; reicht der Bestand nicht, wird nichts
   gespeichert und der Browser lädt neu.
2. Gespeichert werden Vorgang (Frist, Status) und Positionen mit **eingefrorenem Preis**.
3. **Eine** Mail geht an `kikripp_mail_an`, mit Antwort-an auf den Interessenten.
4. War der Versand erfolgreich, ruft `Kikripp_Mail::reservierung()` sofort
   `Kikripp_DB::kontakt_loeschen()` — Name, Mail, Telefon und Nachricht sind damit aus der
   Datenbank verschwunden, `kontakt_weg = 1`.
5. Scheiterte der Versand, **bleiben** die Kontaktdaten liegen. Die Verwaltung zeigt sie mit
   Warnung und einem Knopf zum Löschen. Ohne dieses Netz wäre ein Kontakt endgültig verloren.
6. Der Interessent bekommt **keine Mail**, sondern einen Beleg am Bildschirm mit
   Vorgangsnummer, Positionen, Frist und seinen Kontaktdaten zum Gegenlesen.

> Die Benachrichtigungsmails sind das **einzige Kontaktarchiv**. Das gehört in jeden Bericht
> an die Nutzerin, wenn es um Reservierungen geht.

### Passwort im Link

`…/katalog/?kik=PASSWORT` schaltet frei. `Kikripp_Zugang::link_einloesen()` läuft auf `init`,
also **vor** jeder Ausgabe, setzt den Keks und leitet auf dieselbe Adresse ohne den Parameter
um. So steht das Passwort nicht in der Adresszeile, nicht im Verlauf und kann über keinen
Verweis nach außen gelangen (dazu `<meta name="referrer" content="same-origin">`). Die Bremse
gegen Durchprobieren greift auch hier.

Der Parametername steht in `Kikripp_Zugang::LINK_PARAMETER` und ist bewusst **nicht** `k`:
auf einer Seite mit fünfzehn Plugins ist ein einzelner Buchstabe zu wahrscheinlich schon
belegt, und wir würden ihn fremden Plugins wegnehmen. Der Haken greift nur bei normalen
Seitenaufrufen — REST, AJAX, Cron und Feeds sind ausgenommen, sonst löste er dort eine
Weiterleitung aus.

### Verträglichkeit mit der Umgebung auf kikripp.de

Dort laufen **18 Plugins**, alle netzwerkweit aktiviert außer *Maintenance* (aus, soll aus
bleiben). Relevant sind vier davon:

| Plugin | Warum es zählt |
|---|---|
| **Autoptimize 3.1.8** | bündelt JS und CSS aller Seiten. Das Plugin trägt sich über `autoptimize_filter_js_exclude` / `_css_exclude` **selbst** in die Ausschlussliste ein — keine Handarbeit in den Einstellungen mehr. |
| **W3 Total Cache 2.4** | Seiten-Cache **und** Minify. `DONOTCACHEPAGE` und `DONOTMINIFY` werden auf der Katalogseite gesetzt, W3TC hält sich an beide. Cache trotzdem nach jedem Import leeren. |
| **Really Simple SSL 7.0.8** | Härtungsfunktionen, darunter Einschränkungen der REST-Schnittstelle. **Erster Verdacht, wenn der Katalog leer bleibt** — die Artikel kommen über REST, und zwar für abgemeldete Besucher. Nicht aus dem Plugin heraus überschreiben, sondern die Nutzerin die Einstellung prüfen lassen. |
| **Maintenance 4.07** | aus. Würde die ganze Website für Abgemeldete sperren. Dass *Wartung* erscheint, liegt nur daran, dass die Seite als Startseite gesetzt ist — andere Seiten sind über ihre Adresse erreichbar. |

Unkritisch: ACF PRO, BackWPup (Sicherung vorher), Bootstrap Blocks (Stile können sich
überlagern, nur anschauen), CPT UI, EWWW Image Optimizer (benennt nichts um; die Artikelfotos
setzt der Katalog per JavaScript ein, verzögertes Laden greift dort nicht), Multisite Post
Duplicator, NS Cloner, Post Types Order, Simply Gallery Block & Lightbox (beobachten),
Statify, SVG Support, Timeline Block, XML Sitemap Generator (Katalogseite dort ausnehmen).

**CookieYes und Yoast gibt es auf kikripp.de nicht**, ebenso wenig Elementor — die Seite ist
mit dem Block-Editor gebaut. Was das Plugin von sich aus tut:

| Maßnahme | Wogegen |
|---|---|
| `DONOTCACHEPAGE` auf der Katalogseite und bei `?kik=` plus `nocache_headers()` | ein Seiten-Cache würde den Zugangszustand eines Fremden ausliefern oder den Link-Einlöser gar nicht ausführen |
| `wpseo_robots` und `wpseo_robots_array` gefiltert, eigenes `noindex` nur wenn Yoast fehlt | zwei robots-Angaben auf einer Seite sind unzuverlässig |
| `data-cookieyes="cookieyes-necessary"` am eigenen Skript (`script_loader_tag`) | Zustimmungsbanner blockieren sonst das Skript und die Seite bleibt leer |
| `autoptimize_filter_js_exclude` und `_css_exclude` um `kikripp` ergänzt | Autoptimize bündelt sonst unser Skript mit und der Katalog bleibt leer. Die Eintragungen der Nutzerin bleiben erhalten; sieben Tests in `test-logik.php` decken das ab |
| `DONOTMINIFY` auf der Katalogseite | W3 Total Cache verkleinert sonst das Skript |
| alles mit `kikripp_` benannt: Optionen, Tabellen, Hooks, Kurzbefehl, REST-Namensraum, Menü, CSS-Klasse | Namenskollisionen |

Die Filter für **Yoast** und **CookieYes** bleiben drin, auch wenn auf kikripp.de weder das
eine noch das andere zu sehen ist: sie tun nichts, wenn das Plugin fehlt, und kosten nichts.

Was die Nutzerin selbst erledigen muss, steht in `A1` unter „Was auf kikripp.de zu beachten
ist": Cache nach jedem Import leeren, breite Seitenvorlage ohne Seitenleiste, Katalogseite aus
der Sitemap nehmen, WordPress vorher aktualisieren, Sicherung mit BackWPup. Autoptimize und
Minify erledigt das Plugin selbst.

**Multisite-Speicherplatz.** Jede Website im Netzwerk hat ein Platzkonto, Standard 100 MB.
Die Fotos brauchen 68 MB, und auf kikripp.de liegen schon Bilder. Reicht es nicht, bricht das
Hochladen mittendrin ab. Steht als Punkt 0a in `A1`: Netzwerkverwaltung → Einstellungen →
Upload-Einstellungen, Begrenzung abschalten oder auf mindestens 500 MB. Das größte Foto hat
623 KB, die Einzeldateigrenze (Standard 1.500 KB) reicht also.

Bleibt der Katalog leer, gilt diese Reihenfolge (steht auch in `A1`): Cache — Really Simple
SSL — Minify. Der schnelle Test auf den mittleren Punkt ist ein Aufruf von
`/wp-json/kikripp/v1/artikel` im privaten Fenster: **`{"ok":false,"gesperrt":true}` ist die
richtige Antwort** (ohne Passwort gibt es keine Artikel), eine `rest_…`-Fehlermeldung dagegen
heißt, dass die Schnittstelle gesperrt ist.

> Vor dem Hochladen von 350 Fotos steht in der Anleitung weiterhin: erst **ein** Foto
> hochladen. Klappt das, ist `wp-content/uploads` beschreibbar. Das kostet eine Minute und
> spart im Zweifel zwei Stunden.

### Der Import — was geprüft ist

`Kikripp_Admin::import()` macht nur noch das Formular-Drumherum. Der eigentliche Import steckt
in **`Kikripp_Admin::einspielen(array $liste)`** und gibt einen Bericht zurück (neu, geaendert,
ohne_bild, fehlende_fotos, verschwunden, reserviert_entfernt); `import_meldung()` baut daraus
den Satz für die Nutzerin. **Der Kettentest ruft `einspielen()` direkt auf** — vorher hatte er
die Importlogik nachgebaut, und eine Abweichung zwischen Test und Wirklichkeit wäre unsichtbar
geblieben. Die Mediathek ist dort eine Attrappe aus den echten Fotonamen; geprüft werden auch
die drei Fälle, die in der Praxis stolpern lassen: Foto zweimal hochgeladen (`-1`), `.JPG`
statt `.jpg`, und ein fehlendes Foto (muss beim Namen genannt werden).

`einspielen()` löscht die Bildkarte **am Anfang und am Ende**. Nur am Ende genügte nicht: nach
einem abgebrochenen Lauf bliebe eine Stunde lang eine veraltete Karte liegen und frisch
hochgeladene Fotos würden übersehen.

Die Bildkarte holt die Anhänge **ohne** `'fields' => 'ids'`. WordPress legt dann Beiträge und
Zusatzfelder in zwei Abfragen in den Zwischenspeicher; mit `ids` wären es zwei Abfragen je
Bild. Gemessen: 417 Artikel gegen eine Mediathek mit 1.219 Bildern in **rund einer Sekunde**.

### Was es nicht mehr gibt

- **Keine Bestätigungsmail an Interessenten** — `Kikripp_Mail::bestaetigung()` ist entfernt,
  ein Test prüft, dass die Methode nicht wiederkehrt.
- **Kein Wunschtermin-Feld** — wird telefonisch geklärt.
- **Keine IP-Adresse** am Vorgang.
- **Telefon ist Pflichtfeld**, mindestens sechs Ziffern — ohne Bestätigungsmail fällt ein
  Tippfehler in der Adresse sonst niemandem auf.

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
| Fotos kommen aus der Mediathek, nicht ins ZIP | sonst wird das Plugin 25 MB groß (24 MB gegen 2 MB Upload-Grenze — geprüft und verworfen) |
| Nach erfolgreichem Mailversand Kontaktdaten löschen | der Speicherplatz gehört einem anderen Unternehmen |
| Käufernamen nie aus dem CSV-Export schreiben, wenn er leer ist | der Katalog kennt keine Namen mehr |

### Prüfen

```bash
php wordpress/tests/test-logik.php      # 87 Prüfungen gegen eine SQLite-Attrappe
php wordpress/tests/test-kette.php      # ganze Kette mit der echten Importdatei
python3 wordpress/tests/browsertest.py       # 53 Prüfungen im echten Chromium
python3 wordpress/tests/browsertest_mobil.py # 16 Prüfungen in Telefonbreite (375 px)
python3 scripts/pruefe_uebergabe.py          # die drei Dateien, die nach WordPress gehen
```

`pruefe_uebergabe.py` schaut sich an, was beim Einspielen schiefgehen kann, bevor es
jemand im Browser merkt: Aufbau der beiden ZIP-Dateien, PHP-Syntax jeder Plugin-Datei,
Lesbarkeit jedes Fotos, Vollständigkeit der Felder in `katalog_import.json` — und es
stellt die Zuordnung Foto → Mediathek nach, die `Kikripp_Admin::bild_schluessel()`
vornimmt. Genau dort steckte bis zum 24.09.2026 ein Fehler: `preg_replace('/-\d+$/', …)`
sollte den Zusatz `-1` abschneiden, den WordPress bei Namensgleichheit anhängt, hat aber
aus `F-540` ein `F` gemacht. Damit landeten alle Fotos unter demselben Schlüssel und
**kein einziger Artikel** hätte ein Bild bekommen.

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
>
> Für den Browsertest **beide** Zustandsdateien löschen: `/tmp/kikripp-web.sqlite` **und**
> `/tmp/kikripp-optionen.json`. Nur eine zu löschen ergibt einen leeren Katalog bei
> gültigem Passwort — der Testserver spielt die Artikel inzwischen selbst nach, wenn die
> Tabelle leer ist, und der Browsertest bricht mit klarer Meldung ab, wenn der Server fehlt.
>
> **Falle:** `pkill -f "php -S …"` trifft die eigene Shell mit, weil das Muster in deren
> Kommandozeile steht — der Befehl stirbt, und das `rm` dahinter läuft nie. Erst löschen, dann
> beenden, oder ein Muster wählen, das sich nicht selbst trifft. Zwei Testläufe schienen
> deshalb Artikel zu verlieren („96 von 98"); in Wahrheit waren es Reservierungen aus dem
> Lauf davor, die der Filter „nur verfügbare" ausblendete.
>
> Den Server mit `KIK_TEST_PW=2026sales4kids` starten — `server.php` nimmt sonst
> `test-passwort`, und der Browsertest kommt nicht an der Sperrseite vorbei.

### Ausliefern

```bash
cd wordpress && ./paketieren.sh           # ausgabe/kikripp-katalog.zip
python3 scripts/build_fotopaket.py        # ausgabe/kikripp-fotos.zip
python3 scripts/build_unterlagen_docx.py  # Aktennotiz, Datenschutz-Absatz, Knopf
```

> Das Fotopaket enthält **nur** die Bilder, auf die eine sichtbare Katalogposition zeigt,
> plus die, die in einem Mengenhinweis als weitere Ansicht genannt sind. Es wird bei jedem
> Livegang neu erzeugt — ein altes Paket lädt zu wenige Fotos hoch, und das Plugin meldet
> dann „X Artikel ohne gefundenes Foto".

Zusammen mit `ausgabe/katalog_import.json` schicken. Die Einrichtung steht in
`WEBSHOP_EINRICHTEN.md` (als PDF: `A1`). Dazu gehören:

| Datei | Zweck |
|---|---|
| `U2_Datenschutz_Absatz.docx` | Textbaustein für die Datenschutzerklärung von kikripp.de |

`U1` (Aktennotiz) und `U3` (Knopf) sind mit dem Umzug auf kikripp.de entfallen.

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

## 8b. Das Klinik-Angebot — ruht

Die Nutzerin hat das Angebot an Mediclin am 22.09.2026 zurückgestellt und am 24.09.2026
entschieden, die Klinik-Spalte aus dem Artikelstamm zu nehmen. Seitdem gilt:

* `scripts/build_angebot_xlsx.py` bleibt liegen und wird **nicht mehr in Ablauf C
  aufgerufen**; `ausgabe/02_Angebot_Klinik.xlsx` ist gelöscht, `pruefen.py` prüft es
  nicht mehr.
* Die Spalte `Klinik_Markierung` steht weiter in der Datenbasis, erscheint aber weder
  in der Arbeitsmappe noch beim Zurücklesen.
* Wird die Klinik wieder aktuell, gilt die alte Reihenfolge erneut: **erst die Klinik,
  dann der Webkatalog**, und was die Klinik nimmt, muss vor dem Livegang auf
  `Im_Katalog = nein` stehen. Sonst wird dasselbe Stück zweimal angeboten.

## 9. Der Mailversand ist tot — und was daraus folgt

**Am 29.09.2026 beim echten Einrichten festgestellt: der Webserver von kikripp.de
verschickt keine Mails.** `wp_mail()` meldet Erfolg, die Mail verschwindet. Geprüft mit
zwei Empfängern — `saldi4kids@outlook.com` und `jennyp@kikripp.de`, beide extern und
domaineigen. Nichts kam an, auch nicht im Junk-Ordner. Ursache ist nicht die
Absenderadresse allein: der Host liefert überhaupt nicht aus.

**Die Reservierung stand danach ohne Kontaktdaten in der Verwaltung** — denn bis dahin
löschte `Kikripp_Mail::reservierung()` die Kontaktdaten, sobald `wp_mail()` Erfolg
meldete. Die Mail galt als der einzige Ort, an dem sie stehen. Damit wäre jeder
Interessent unwiederbringlich verloren gewesen, ohne dass es jemand merkt.

**Umgestellt:** Die Kontaktdaten **bleiben in der Datenbank**, bis ein Mensch auf
*„erledigt – Kontaktdaten löschen"* klickt. Dazu:

* Die Verwaltungsseite zeigt Name, Mailadresse, Telefon und Nachricht, anklickbar.
* Der Menüpunkt trägt eine **Zähler-Blase** mit der Zahl der offenen Vorgänge (wie bei
  Plugin-Updates). Das ersetzt die Benachrichtigungsmail: die Nutzerin sieht es beim
  Einloggen, ohne daran denken zu müssen.
* Die Mail wird weiter versucht und trägt jetzt einen echten **Absender**
  (`From: <Firma> <kikripp_mail_an>`). Wird später SMTP nachgerüstet, läuft sie sofort.
* `U2_Datenschutz_Absatz.docx` ist neu formuliert: Speicherung, Löschung nach Abwicklung,
  keine Weitergabe. **Die Nutzerin musste den Absatz in der Datenschutzerklärung
  ersetzen** — das gehört zu dieser Umstellung dazu und darf nicht vergessen werden.

**Die ursprüngliche Nicht-Speicherung war eine Vorsichtsmaßnahme für fremden
Speicherplatz.** Dieser Grund ist mit dem Umzug auf kikripp.de entfallen; Speicherung auf
der eigenen Seite ist über Art. 6 Abs. 1 lit. b DSGVO gedeckt und völlig normal.
**Nicht zurückbauen**, solange kein Mailversand existiert.

Abschnitt 17, 17b und 17c in `test-logik.php` halten das fest: die Kontaktdaten müssen auf
der Verwaltungsseite stehen, der Menüpunkt muss die Zahl tragen, und nach dem Löschen darf
nichts mehr zu sehen sein. Die Attrappe legt ihre Helfer nur per `function_exists()` an —
der Testserver bringt einige selbst mit und bricht sonst mit „Cannot redeclare" ab.

## 9b. Stand am 29.09.2026, abends — der Katalog ist online

**Der Webkatalog läuft.** Er wurde an diesem Tag gemeinsam mit der Nutzerin Schritt für
Schritt in WordPress eingerichtet, sie hat nach jedem Schritt einen Bildschirmabzug
geschickt. Technisch ist alles fertig; offen ist nur noch Inhalt.

### Was in WordPress steht

| | |
|---|---|
| Adresse | `www.kikripp.de/artikelkatalog` (Seite „Artikelkatalog", Block mit `[kikripp_katalog]`) |
| Passwort | `2026sales4kids` — Link dazu: `…/artikelkatalog/?kik=2026sales4kids` |
| Plugin | über die Netzwerkverwaltung installiert, **nur auf der Seite KIKRIPP** aktiviert |
| Mediathek | **711 Elemente** (343 vorher + 368 Katalogfotos) |
| Import | 443 Artikel, **379 im Katalog sichtbar**, jede sichtbare Position mit Bild |
| Vorschaubetrieb | **an** — Testreservierungen sind markiert und am Ende löschbar |
| Hinweisband | leer |

**Die Speicherplatzbegrenzung des Netzwerks ist abgeschaltet** (Häkchen nicht gesetzt),
maximale Uploadgröße 16.000 KB. Der Punkt, vor dem in `A1` gewarnt wird, ist hier also
keiner.

### Was die Nutzerin gerade macht

Sie geht den Katalog durch und sammelt:

* **Fehlende Artikel** — Positionen, zu denen es schon Fotos gibt, die aber nie in den
  Artikelstamm gekommen sind. Kommt als Word mit Artikel und zugehöriger **F-Nummer**
  (die liest sie in der Mediathek ab).
* **Zustand und Beschreibungen** — Änderungen direkt in `01_Artikelstamm_kikripp.xlsx`.
* Fotos, die nicht zum Artikel passen.

Sie vergibt **keine Artikelnummern selbst**, sondern schreibt `RAUMCODE-NEU1`,
`-NEU2` usw. Grund: `BA04-08` und `BA04-09` waren bereits als zusammengefasste
Post-it-Nummern von `NU04-17` und `BA02-08` belegt, und das fiel erst bei `pruefen.py`
auf. **Vor jeder neuen Nummer prüfen, ob sie in einem `Weitere_ArtNr` steht.**

### Kleinigkeiten, die noch offen sind

* **`Reservierungen melden an` steht auf `jennyp@kikripp.de`** — Rest vom Mailtest. Das
  Feld ist zugleich die Adresse, die Interessenten im Anbieter-Block und in der
  Bestätigung sehen. Muss zurück auf **`saldi4kids@outlook.com`**.
* **Plugin-Aktualisierung liegt bereit** (doppelt angezeigte Nachricht behoben) — rein
  kosmetisch, kann bei Gelegenheit eingespielt werden.
* **Testreservierung #3 ist offen** und wird beim Livegang über *Einstellungen →
  Testreservierungen löschen* entfernt.
* **Preise von `BU09-04` (250 €) und `BU09-05` (180 € je Schrank)** sind Schätzwerte,
  als `OFFEN:` vermerkt und von der Nutzerin nicht bestätigt.
* **WordPress 7.1.2** steht noch aus, und die Katalogseite gehört aus der Sitemap des
  XML Sitemap Generators genommen. Beides bewusst zurückgestellt.

### Was noch kommt

1. Die Nutzerin schickt Word und Excel → einlesen, neue Artikel anlegen, neue Fotos
   aufnehmen, Importdatei und Arbeitsmappe neu erzeugen.
2. Sie lädt die neuen Fotos hoch und importiert einmal.
3. **Livegang:** Testreservierungen löschen · Vorschaubetrieb aus · Cache leeren ·
   im privaten Fenster gegenlesen · **dann erst** den Link verschicken.

**Solange der Link nicht verschickt ist, sieht den Katalog niemand.** Das ist der Satz,
der die Nutzerin bei jedem Zwischenstand beruhigt — und er stimmt.

## 10. Was die Nutzerin nicht mag

- **Keine `.md`-Dateien** — sie kann sie unter Windows nicht öffnen. Anleitungen immer als
  PDF, Formulare als Word oder Excel.
- **Keine PDFs, wo Word oder Excel geht.** Ausdrücklich gewünscht: „ich möchte bitte keine
  pdf. wenn dann word und excel." Für Anleitungen zum Lesen ist PDF in Ordnung, für alles
  zum Ausfüllen nicht.
- **Keine langen Anleitungen.** Eine frühere 14-seitige Fassung wurde abgelehnt. Fließtext,
  kurz, ohne Fachsprache.
- **Keine Verträge, wenn es auch eine Aktennotiz tut.**
- Sie will **Widerspruch**, wenn etwas schiefläuft — ausdrücklich und mehrfach erbeten.
  Bedenken benennen, Empfehlung geben, dann ihre Entscheidung umsetzen.
