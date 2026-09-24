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

## 8. Der Webkatalog

Seit September 2026 läuft der Verkauf über ein eigenes WordPress-Plugin in
`wordpress/kikripp-katalog/`. Es ersetzt den PDF-Katalog und die Wunschmengen-Spalten im
Klinik-Angebot. **Es gibt genau einen Reservierungsweg: den Katalog.** Wer daneben noch
eine zweite Schiene einbaut, vergibt Ware doppelt.

### Wo er läuft, und warum das wichtig ist

Der Katalog liegt auf **www.schlabberschnuten.com** — der Website der Hundeschule der
Nutzerin, weil sie dort Super-Admin-Rechte hat. Auf **kikripp.de** steht nur ein Knopf, der
dorthin verweist (Vorlage: `ausgabe/U3_Knopf_fuer_kikripp.docx`). Auf kikripp.de selbst ist
kein Plugin installierbar: Multisite, und die Netzwerkverwaltung ist der Nutzerin gesperrt.

Daraus folgen drei Dinge, die man nicht wegoptimieren darf:

| Regel | Grund |
|---|---|
| Der Firmenname kommt aus `kikripp_firma`, **nie** aus `get_bloginfo('name')` | sonst steht „Schlabberschnuten" im Katalog und im Mailbetreff |
| Unter dem Katalog steht ein **Anbieter-Block** mit Kikripp-Adresse und Links auf Impressum und Datenschutz von kikripp.de | die Seite selbst hat das Impressum der Hundeschule — ohne den Block wäre das ein Impressumsverstoß |
| **Keine personenbezogenen Daten** in der Datenbank | fremder Speicherplatz; ohne Speicherung braucht es keinen Auftragsverarbeitungsvertrag |

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

### Verträglichkeit mit der Umgebung auf schlabberschnuten.com

Dort laufen rund fünfzehn Plugins. Was das Plugin deshalb von sich aus tut:

| Maßnahme | Wogegen |
|---|---|
| `DONOTCACHEPAGE` auf der Katalogseite und bei `?kik=` plus `nocache_headers()` | ein Seiten-Cache würde den Zugangszustand eines Fremden ausliefern oder den Link-Einlöser gar nicht ausführen |
| `wpseo_robots` und `wpseo_robots_array` gefiltert, eigenes `noindex` nur wenn Yoast fehlt | zwei robots-Angaben auf einer Seite sind unzuverlässig |
| `data-cookieyes="cookieyes-necessary"` am eigenen Skript (`script_loader_tag`) | Zustimmungsbanner blockieren sonst das Skript und die Seite bleibt leer |
| alles mit `kikripp_` benannt: Optionen, Tabellen, Hooks, Kurzbefehl, REST-Namensraum, Menü, CSS-Klasse | Namenskollisionen |

Was die Nutzerin selbst erledigen muss, steht in `A1` unter „Was auf schlabberschnuten.com
zu beachten ist": Elementor-Seite mit dem **Shortcode-Widget** oder ganz ohne Elementor,
breites Seitenlayout, Cache leeren, Katalogseite von der JavaScript-Optimierung ausnehmen,
`kikripp_zugang` in CookieYes als notwendig eintragen, Sicherung mit UpdraftPlus.

> **Popup Maker meldet auf der Seite, dass es keine Cache-Dateien schreiben kann.** Das kann
> heißen, dass Teile des Webspace nicht beschreibbar sind — dann scheitern Plugin-Upload und
> Fotos. Deshalb steht in der Anleitung: erst **ein** Foto hochladen, dann die restlichen 110.

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
python3 wordpress/tests/browsertest.py  # 53 Prüfungen im echten Chromium
python3 scripts/pruefe_uebergabe.py     # die drei Dateien, die nach WordPress gehen
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
| `U1_Aktennotiz_Speicherplatz.docx` | dokumentiert die Nutzung fremden Speicherplatzes; die Nutzerin wollte **keinen** Vertrag |
| `U2_Datenschutz_Absatz.docx` | Textbaustein für die Datenschutzerklärung von schlabberschnuten.com |
| `U3_Knopf_fuer_kikripp.docx` / `.txt` | der HTML-Baustein für den Knopf auf kikripp.de |

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

## 8b. Das Klinik-Angebot

**Reihenfolge, seit 17.09.2026:** Die Klinik geht **zuerst**, der Webkatalog erst danach online.
Mediclin hat Vorrang. Damit ist das alte Problem der zwei Reservierungswege entschärft — sie
laufen nicht mehr gleichzeitig.

> **Der entscheidende Übergabeschritt:** Was die Klinik nimmt, muss **vor** dem Livegang des
> Webkatalogs aus dem Katalog verschwinden — `Im_Katalog = nein` oder als verkauft eintragen,
> dann `build_katalog_import.py` und importieren. Sonst wird dasselbe Stück zweimal angeboten.

Die Klinik trägt selbst ein, in drei grau hinterlegten Spalten:

| Spalte | Verhalten |
|---|---|
| `Interesse` | Auswahlliste ja/nein, mit Eingabeprüfung |
| `Stückzahl` | ganze Zahl > 0, **leer = volle verfügbare Menge** |
| `Ihre Bemerkung` | freier Text |
| `Wert netto` | rechnet selbst: `=IF(Interesse<>"ja","", IF(Stückzahl="",Verfügbar,Stückzahl)*Einzelpreis)` |

Zeilen mit „ja" färben sich über eine bedingte Formatierung grünlich ein.

**Die Sprache ist Absicht:** „Interesse" und „Wert Ihrer Auswahl", nicht „Wunschmenge" und
nicht „Reservierung". Im Hinweiskasten und in den Verkaufsbedingungen steht ausdrücklich, dass
die Eintragungen eine **Interessenbekundung** sind und die Zuteilung erst mit schriftlicher
Bestätigung verbindlich wird. Das nicht verwässern — sonst entsteht ein Anspruch auf Ware, die
parallel online weggehen könnte.

Aufbau der Summen: **A · Ihre Auswahl** (leer, solange nichts eingetragen ist) · **B ·
Gesamtbestand** · **C · Paketangebot** mit dem Nachlass aus `daten/design.csv`
(`Paketrabatt_Prozent`, seit 17.09. **15 %**). C rechnet auf B, B auf den Zeilen — jede Zahl
steht nur einmal in der Datei.

Preise stehen **netto und brutto** je Position. Netto führt (die Klinik ist ein Unternehmen),
brutto steht daneben in Grau.

`pruefen.py` prüft das alles bei jedem Lauf: Spalten vorhanden, Brutto- und Wertformeln in
jeder Zeile, Markierung deckungsgleich mit der Datenbasis, beide Eingabeprüfungen da, und
**keine beschädigten eingebetteten Bilder**.

> Eine von der Nutzerin zurückgeschickte Fassung hatte zwei **defekte Bilddateien**
> (`Bad CRC-32`), wodurch vier Positionen ohne Bild dastanden. Meine erzeugte Fassung war
> sauber — der Schaden entsteht unterwegs (Download, Excel-Speichern, Cloud-Abgleich). Bei
> „Bild fehlt" also immer zuerst `zipfile.ZipFile(...).testzip()` laufen lassen, bevor man in
> den Daten sucht.

> **Das Klinik-Angebot ist eine erzeugte Datei.** Hand-Markierungen darin überleben keinen
> Neuaufbau. Deshalb lebt die Markierung in `Klinik_Markierung` in der Datenbasis. Wenn die
> Nutzerin von Hand färbt, die Farben auslesen (bei beschädigten Dateien direkt aus
> `xl/worksheets/sheet1.xml` plus `xl/styles.xml`) und in die Spalte übertragen.

---

## 9. Offene Punkte (Stand 22.09.2026)

- **Die Klinik hat abgesagt.** Damit fällt die Vorrangregel weg, alle Artikel gehen in den
  Webkatalog, und `Kanal` ist bei allen Zeilen leer — er trägt erst den tatsächlichen
  Verkaufsweg ein. Das Klinik-Angebot bleibt erzeugt, wird aber nicht weiter überarbeitet;
  es soll später ein allgemeines Händlerangebot werden.
- **Wellen:** Möbel und große Dekostücke zuerst (`Im_Katalog = ja`), Spielzeug und Konvolute
  später (`nein`). Für die 88 Positionen der alten Klinikauswahl gilt die Trennung **nicht** —
  die stehen alle im Katalog. Sie greift für die rund 900 noch zu erfassenden Artikel.

### Offene Punkte stehen an der Ware, nicht in einer Merkliste

Wartet eine Position noch auf etwas, beginnt ihre `Bemerkung` mit **`OFFEN:`**. `pruefen.py`
listet diese Zeilen bei **jedem** Lauf einzeln auf, mit Artikelnummer und Text. Damit hängt
nichts an einer handgepflegten Liste und nichts an meinem Gedächtnis: der Hinweis klebt an der
Ware und verschwindet erst, wenn ihn jemand entfernt.

Zwei Sorten kommen laufend vor:

| Sorte | Vorgehen |
|---|---|
| **`OFFEN: wächst noch`** | Derselbe Artikel steht in weiteren, noch nicht erfassten Räumen — Betten, Hochstühle, Kunststoffstühle. Die Position bleibt bei der bisher gezählten Menge stehen. **Am Ende des Rundgangs** auf die Gesamtzahl bringen und die Post-it-Nummern der anderen Räume in `Weitere_ArtNr`. |
| **`OFFEN: buendeln am Schluss`** | Die Nutzerin will Sammlungen erst bilden, **wenn der Rundgang durch ist** — es kommt noch viel. Bis dahin nur vormerken, nicht schon Spalten füllen. Steht eine Gruppe erkennbar zusammen (Schwarzwald, Kindergarderoben, Spielküche und Kaufladen, Sitzbänke mit Stauraum), im Bericht erwähnen und weitergehen. |
| **`OFFEN: NICHT VEROEFFENTLICHEN`** | `Im_Katalog = nein`, weil eine Angabe fehlt, die den Preis um eine Größenordnung verschiebt. Aktuell `NU02-18`: Form und Signaturplättchen sprechen für einen Vitra Eames Elephant (gebraucht 150–280 € je Stück) gegen 20–40 € für einen Nachbau. Erst nach der Nahaufnahme entscheiden, dann `ja`. Der kleinere schwarze wird dabei eine **eigene Position**, weil Vitra zwei Größen baut. |

> Die Nutzerin sammelt fehlende Fotos bewusst und liefert sie **in einem Zug am Ende** nach.
> Nicht vorher drängen, aber auch nichts abschließen, solange `pruefen.py` noch `OFFEN:`-Zeilen
> meldet.
- **Der Katalog ist noch nicht installiert.** Plugin, Fotos, Importdatei und die drei
  Begleitunterlagen liegen in `ausgabe/`. Die Nutzerin richtet ihn auf
  **schlabberschnuten.com** ein (Anleitung `A1`). Danach fragen, ob die Benachrichtigungsmail
  angekommen ist — sonst muss SMTP dazu.
- **Impressum- und Datenschutz-Adresse sind geraten** (`https://www.kikripp.de/impressum/`
  und `/datenschutz/`), weil kikripp.de aus dieser Umgebung gesperrt ist. Die Nutzerin prüft
  sie in den Plugin-Einstellungen. **Ohne funktionierenden Impressum-Link fehlt die
  Anbieterkennzeichnung** — das nach der Einrichtung nachfragen.
- **kikripp.de bleibt gesperrt.** Multisite, Netzwerkverwaltung nicht zugänglich. Eine
  Anfrage an die Betreuung ist raus (Super-Admin für `anna`). Kommt sie durch, wäre
  `katalog.kikripp.de` die schönere Adresse — empfohlen, aber verworfen zugunsten der
  schnelleren Lösung.
- **Rundgang läuft.** Türschilder, Erfassungsblätter und Erfassungsliste sind ausgeliefert
  und ausgedruckt. Zurück kommen `T3_Erfassungsliste.xlsx` mit Stückzahlen und die Fotos je
  Raum. Die Nummer auf dem Post-it im Foto ist maßgeblich.
- **Sieben Positionen wurden inhaltlich umgewidmet** (Vitrine → Dekoration darin, Regal →
  Rattankörbe, Tonkartonschrank → buntes Papier, Hängeleuchte → Pflanze, Wandspiegel →
  Trachtenportrait, Pflanzkübel Beton → Plastik, Gartentisch → inkl. Stühle). Ihre Fotos
  zeigen teils noch das nicht mehr verkaufte Möbel — beim Rundgang neu fotografieren.
  Besonders `BA04-01`: das Foto zeigt vor allem die antike Vitrine, die nicht mitgeht.
- **Drei Positionen mit offener Stückzahl:** `NE05-01`, `NU04-04`, `BA09-04` — nachzählen.
- **Eine Annahme, nicht bestätigt:** Der alte Sammelraum „UG" mit fünf Positionen liegt bei
  `BU04`. Die Aufnahmereihenfolge spricht dafür; sicher ist es nicht.
- **Maße** fehlen bei allen Positionen; von der Nutzerin bewusst zurückgestellt.
- **Anlagennummern und Anschaffungswerte** fehlen komplett (Anlagenabgang bei einer GmbH).
  Anlagenverzeichnis beim Steuerberater erbitten.
- **Versand:** Empfehlung steht — alles auf Abholung, Versand nur für Designstücke und nur
  an Gewerbe, weil Versand an Verbraucher ein 14-tägiges Widerrufsrecht auslöst. Die Nutzerin
  arbeitet die Spalte `Versand` selbst ein.
- **Logo:** liegt nur als Bildschirmbild vor; Signet nachgebaut.
- **Foto F-110** ist wegen zweier Teamfotos stark beschnitten.
- **Rechtstexte, Aktennotiz und Datenschutz-Absatz** sind von mir formuliert, nicht
  anwaltlich geprüft. Das steht auch in den Dokumenten selbst.

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
