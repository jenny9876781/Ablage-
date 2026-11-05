---
name: projekt-zeit-kosten-report
description: "Use this skill whenever the user (assistant to Neininger management) wants the recurring time/cost report that consolidates Outlook calendar entries (project name in quotes in the subject) with the Autolog vehicle logbook export into a multi-year Excel report: hours, driven km, and costs per project, per task category, per employee, per company (Neininger GmbH / TransCare), with a filterable dashboard, VAT breakdown, a weekly non-project sales-time allowance, manual extra costs, and a plausibility check. Trigger on 'Projektbericht', 'Zeit-/Kostenbericht', 'Autolog', 'Fahrtenbuch', 'Kalenderexport'+'Projekt', 'Jahresauswertung', or requests reconciling calendar time with driving logs into a cost report, any year from 2024 on. Also trigger when calendar/Autolog CSVs are uploaded with a request to consolidate hours/km/costs, including project-specific multi-year reports. Do NOT use for the separate ma-nbo-workflow skill."
---

# Projekt-Zeit-/Kosten-Report (Neininger) — Version 6.5 (abgesichert + vereinfacht + Kundenbericht + TransCare-Abrechnung, 2026-11)

Dieser Skill bildet den wiederkehrenden Workflow ab, bei dem aus Outlook-Kalenderexporten
mehrerer Mitarbeiter/Postfächer und einem Autolog-Fahrtenbuch-Export ein Excel-Bericht mit
Arbeitszeiten, Fahrzeiten/-kosten und Gesamtkosten je Projekt entsteht — als Jahres-/
Monatsbericht über alle Projekte, als Einzelbericht für ein Projekt über mehrere Jahre, und
mit einem Filter-Dashboard für freie Auswertungen nach Mitarbeiter/Projekt/Firma/Jahr.

**Immer zuerst `config/projekt_konfiguration.json` lesen.** Diese Datei enthält Satzhistorie
(mit Gültig-ab-Datum), Mitarbeiterliste, Hauptaufgaben-Kategorien, die Wochenpauschale-Regel,
MwSt.-Satz und die Projektstammliste (wird von der Nutzerin selbst über
`Projektliste_Vorlage.xlsx` gepflegt — bei einer neuen Version dieser Liste den
`projekt_stammliste`-Abschnitt der Config komplett ersetzen).

## VERBINDLICH ab Version 6: Versionsregel, feste Abläufe, Prüfblätter

Ziel von Version 6: **genauer, nicht schneller.** Die Geschäftsführung muss dem Bericht vertrauen können.

**1. Nur zwei Einstiegsfunktionen – nicht mehr selbst zusammenbauen.**
- `neuaufbau(calendar_specs, autolog_specs, config, period_start, period_end, period_label, output_dir, vergleichsdatei=None, version=1)`
  – kompletter Aufbau aus allen Rohdaten (z.B. „Basis v01“). `vergleichsdatei` = zuletzt freigegebene
  alte Ausgabe (auch Version 5 ohne Stempel). Daraus werden Zusatzkosten, manuelle Zeitbuchungen,
  Partner-Zuordnung, gepflegte Stammliste und manuelle Korrekturen übernommen, und das Prüfblatt
  vergleicht alt gegen neu.
- `fortfuehrung(vorlage, erwartete_version, calendar_specs, autolog_specs, config, period_end, period_label, output_dir)`
  – monatliche Fortführung. Pipeline-Schritte (Wochenpauschale → Matching → Partner → Kosten) laufen darin
  in der richtigen Reihenfolge; die Einzelfunktionen weiter unten nur noch zur Fehlersuche benutzen.
- `calendar_specs`: Liste `{path, mitarbeiter, kalendertyp, format?}`; `autolog_specs`: Liste `{path, kennzeichen}`
  (Fahrer kommt aus `fahrzeug_fahrer_zuordnung`, nie aus dem Export).

**2. Versionsregel (gegen S1 „falsche Vorlage“).**
- Dateiname `Füxle_<Zeitraum>_v<NN>.xlsx`; Version, Vorgänger, Datenstand bis, Erstellt am,
  Skill-Version und **Freigegeben am/von** stehen im **Cockpit** (Block „Berichtsversion“).
- **Vor jeder Fortführung die Nutzerin fragen: „Welche Version ist zuletzt freigegeben (z.B. v03)?“** Nie
  selbst aus Dateidatum, Chatverlauf oder Projektdateien ableiten.
- `pruefe_vorlage()` (in `fortfuehrung()` eingebaut) stoppt mit `VorlageFehler`, wenn die Datei älter oder
  neuer als genannt ist, Dateiname und Stempel nicht passen, der Freigabevermerk fehlt oder die Datei keinen
  Stempel hat (Version 5 → erst Neuaufbau). **Bei VorlageFehler: stoppen, Meldung wörtlich an die Nutzerin,
  nachfragen. Nicht weiterrechnen, keinen Workaround bauen.**
- Liegen mehrere Kandidaten vor: `waehle_vorlage(pfade, erwartete_version)`.
- Vormonate werden **eingefroren** übernommen. Neue Rohdaten zählen nur NACH „Datenstand bis“. Nachträge in
  Vormonaten und in Outlook geänderte alte Termine kommen auf die Prüfliste, nicht in die Zahlen.

**3. Prüfblatt „Abgleich_Vormonate“.** Summen je Monat × Projekt alt gegen neu. Oben steht
„Vormonate unverändert ✔“ oder „X Abweichungen“; Abweichungen sind rot, mit automatischer Begründung und
den betroffenen Einzelzeilen. **Bei einer Fortführung muss dort „unverändert ✔“ stehen – sonst nicht
ausliefern, sondern der Nutzerin die Abweichungen zeigen.** Beim Neuaufbau mit Vergleichsdatei sind
Abweichungen erwartbar (behobene Fehler) – jede einzeln mit der Nutzerin klären.

**4. „Zuordnung_Grund“ + „Prüfen“ + Reiter „Pruefen_Korrigieren“ (gegen S2).** Jede Kalender- und Fahrtzeile hat einen
Grund (z.B. „Projektname im Betreff“, „Alias Sand → Sandformation“, „Zeitfenster-Match mit Termin …“,
„Partner-Zuordnung …“, „Partner … = Unberücksichtigt (hat Vorrang)“). Unsichere Fälle sind gelb und stehen auf
der Pruefliste (Status live: erledigt, sobald eine Korrektur oder ein „x“ eingetragen ist). Unsicher sind:
unbekannter Projektname, abweichende Schreibweise eines bekannten Namens, mehrere Namen im Betreff, möglicher
Projektbezug ohne Anführungszeichen (wird NICHT zugeordnet), mehrere Projekte im Fahrt-Zeitfenster, mehrtägiger
Block, mögliche Dublette zwischen zwei Kalendern, Niedermaier-Kurztermin bzw. abweichende Tageszählung.
**Anzahl offener Punkte im Chat nennen.**

**5. Nach dem Lauf, vor der Auslieferung:** `recalc.py` (xlsx-Skill) → nur bei `total_errors: 0` ausliefern;
`Abgleich_Vormonate` und `Pruefliste` kurz im Chat zusammenfassen; die Nutzerin daran erinnern, nach der
GF-Prüfung „Freigegeben am/von“ einzutragen. Gibt `fortfuehrung()` `config_hinweise` zurück (Vorlage weicht
von der Config ab), anbieten, die Config im Skill-ZIP zu aktualisieren – **die Config ändert sich in claude.ai
nicht dauerhaft, nur über ein neues ZIP.**

**6. Entfernt in Version 6:** Soll-Arbeitszeit/„Auslastung je Mitarbeiter“ (Datenschutz). Stunden je Person
(Interne_Auswertung, Dashboard-Kreuztabelle) und je Mitarbeiter **und Projekt** (Übersicht) bleiben.

**7. Tests:** `python -m pytest tests -q` (erfundene Testdaten). Vor jeder Änderung an `report_lib.py` laufen lassen.

## Version 6.5 (2026-11-05): noch einfacher – VERBINDLICH (ersetzt abweichende Angaben in 6.2/6.4)

**Reiter (12 statt 16, inkl. ausgeblendeter Listen):** Cockpit, Interne_Auswertung (grün) · Pruefen_Korrigieren (gelb) · TC_Bericht (grün),
TC_Stand (blau) · Zusatzkosten, Manuelle_Zeitbuchungen (blau) · Stammdaten, Rohdaten_Kalender, Rohdaten_Fahrten,
Sonderkalk (grau) · Listen (ausgeblendet). **Weggefallen:** Uebersicht (= Cockpit mit Filter „(Alle)“; Projektliste
im Cockpit hat jetzt auch km), Abgleich_Vormonate, Zahlungen, Berichtshistorie.

- **Cockpit nur Filter + Zahlen** (Wunsch GF): kein Versionsblock, kein Prüfstatus, keine Monatsabschluss-Liste,
  kein „TransCare offen“.
- **Pruefen_Korrigieren oben (Zeilen 1–13):** links Prüfstatus (offene Entscheidungen, Hinweise offen, Abgleich
  Vorversion mit Link, Formel-Check, Anzahl Regel-Vorschläge, TransCare offen brutto), rechts **Berichtsversion mit
  Freigegeben am/von** (hier liest der Skill Version und Freigabe – ältere Dateien: Cockpit). Kopfzeile der Liste
  = Zeile 14 (`PRUEF_KOPFZEILE`). Reihenfolge: offene Punkte → bisherige Entscheidungen (zugeklappt) → 50 freie
  Zeilen → Hinweise (zugeklappt) → **Abschnitt „Abgleich mit der Vorversion“** ganz unten. Regel-Vorschläge in
  Spalten O–T, zugeklappt.
- **TC_Stand** = alle TC-Eingaben: 1. gemeldeter Stand, 2. Zahlungen, 3. Berichtshistorie (Abschnitte per Titel
  „2. Zahlungen…“, „3. Berichtshistorie…“ – beim Einlesen danach suchen; ältere Dateien: eigene Reiter).
- **Schalter jetzt im TC_Bericht, Zelle J2** (`TC_SCHALTER`). TC_Stand zeigt ihn nur an. In TC_Stand ändern sich
  beim Umschalten keine Zahlen (das ist die Eingabe) – wirksam ist er im TC_Bericht und im externen Bericht.
- **Nichts erstmals rückwirkend zeigen:** allgemeiner Aufwand, der in der Aufstellung NICHT stand, erscheint bis
  zum Stichtag mit 0 und erst ab dem Stichtag (z. B. Allgemeine Vertriebszeit: nur 2.000 € ab 01.08.2026). Laufende
  Projekte erscheinen normal.
- **Keine Hinweise und keine Korrekturspalte im Bericht** (live und extern). Im TC_Bericht stehen „intern: Korrektur“
  und „intern: Hinweis“ in J/K – außerhalb des Druckbereichs B–H. Bei „korrigiert“ sieht TC die bereinigten Zahlen
  ohne Erklärung (von der Nutzerin so gewollt).
- Bericht-Layout: Seite 1 Projekte, Seite 2 allgemeiner Aufwand + Abrechnung + Zahlungen (Summe in der Titelzeile).
  Pauschalwochen werden im Leistungsnachweis getrennt vor/nach dem Stichtag zusammengefasst.

## Version 6.4 (2026-11-05): TransCare-Abrechnung (gemeldeter Stand, Schalter, Zahlungen)

Ausgangslage: Am 05.08.2026 ging eine Aufstellung (Stand 31.07.2026) an TransCare – vor der Füxle, mit
Doppelbuchungen. Die Füxle übernimmt diesen Stand und rechnet ab dem Stichtag weiter.

- **TC_Stand** (Eingabe): Stichtag, Datum der Aufstellung und je Position (Bereich Projekt/Allgemein) die
  gemeldeten Werte (Std, km, Kosten Zeit/Fahrt/Sonstige, Netto, Hinweis). Zelle **B6 = Schalter**:
  `korrigiert (Füxle)` (Standard) oder `wie gemeldet`. Nur per `neuaufbau(..., tc_stand=)` anlegen; danach
  pflegt die Nutzerin selbst.
- Rechenregel (`tc_berechnung`): **Projekte** bis Stichtag = Füxle (korrigiert, Spalte „davon Korrektur ggü.
  Aufstellung“) bzw. gemeldeter Wert (wie gemeldet). **Allgemeiner Aufwand** bis Stichtag = IMMER gemeldeter
  Wert (steht nicht vollständig in der Füxle). Danach immer Füxle. Gesamt = Stand + ab Stichtag.
- **Wochenpauschale** im TC-Bericht = nur die NICHT zugeordneten Restwochen (Position „Allgemeine Vertriebszeit“).
  Fälschlich Neininger-Projekten zugeordnete Pauschalwochen 2025/2026 per Korrektur „automatisch“ zurückbuchen
  (Abgleich-Ursache „Wochenpauschale umgebucht“).
- **Zahlungen** (Rechnung, Zeitraum, Betrag brutto): werden vom Gesamt brutto abgezogen → „Offener Betrag“.
  Zahlung ohne Betrag → Prüfpunkt. **Berichtshistorie**: jede Meldung an TC eintragen (Datum, Stand, Basis, Netto,
  Brutto, Datei) – `erstelle_kundenbericht` liefert den Eintrag als `historie_eintrag`.
- **TC_Bericht** (live, druckfertig, Auswahl mit „x“ in Spalte A): Teil 1 Projekte, Teil 2 allgemeiner
  Aufwand, Teil 3 Abrechnung. Die Nutzerin kann selbst drucken (PDF) – Cockpit-KPI „TransCare offen (brutto)“.
- **Externer Bericht** (`erstelle_kundenbericht`) nutzt automatisch TC_Stand, wenn vorhanden: Übersicht in
  3 Teilen + Zahlungsliste (Seitenumbruch vor Abrechnung), Leistungsnachweis (bei „wie gemeldet“: eine Zeile
  „Stand lt. Aufstellung vom …“, danach nur Leistungen ab Stichtag; bei „korrigiert“: alle Einzelpositionen +
  Hinweis zur Korrektur). Kontrolle: Nachweissumme = Übersicht je Position, sonst Abbruch. Werte müssen mit dem
  Live-Blatt TC_Bericht übereinstimmen.
- Dropdowns: Entscheidung in Pruefen_Korrigieren enthält alle Stammdaten-Projekte inkl. interner TC-Positionen
  und Wochenpauschale; Zusatzkosten-Kostenart aus Config `zusatzkosten_kostenarten` (freie Eingabe erlaubt).
- Erledigt-Häkchen bei Hinweisen werden in Folgeversionen übernommen (gleiches Thema + Text).

## Version 6.3 (2026-11-05): Kundenbericht (z.B. für TransCare)

Anforderung im Chat, z.B. „TransCare-Bericht aus Füxle v03 für Koko, Cool, Zeppelin (+ interne Position
Vor-Ort Termine)“. Die Projektauswahl wird **je Bericht** genannt (keine feste Liste).

- `erstelle_kundenbericht(fuexle_pfad, config, projekte, output_dir, firma='TransCare', interne=None,
  nur_freigegeben=True, pdf=True, pauschale_einzeln=False)` → `Füxle_TransCare_<JJJJ-MM>.xlsx` + `.pdf`.
- **Nur aus einer FREIGEGEBENEN Füxle** (sonst VorlageFehler). Vorschau ohne Freigabe nur mit
  `nur_freigegeben=False` → Titel und Dateiname tragen „ENTWURF“.
- **Kumuliert seit Projektbeginn** bis „Datenstand bis“, netto + MwSt. + brutto, Spalte „davon im Berichtsmonat“.
- Interne TransCare-Positionen (Wochenpauschale, Vor-Ort Termine i. A. TC, Veranstaltungen, MoSI) **nur, wenn
  angefordert** (`interne=`), als eigener Block. Projekte einer anderen Firma → Stopp mit Rückfrage.
- **Leistungsnachweis** je Projekt: Datum, Uhrzeit, Kürzel, **Hauptaufgabe** (nie den Kalender-Betreff!), Menge,
  Satz, netto; Fahrten nur mit Orten; Zusatzkosten mit Kostenart. Den Projekten zugeordnete Wochenpauschalen als
  EINE Zeile je Projekt („Pauschale Projektbetreuung (wöchentlich): N Wochen × 5 Std., KW …“); jede Woche
  einzeln nur, wenn der Kunde es verlangt (`pauschale_einzeln=True`).
- Excel **nur mit Werten** (keine Formeln, keine Rohdaten, keine versteckten Reiter). Vor dem Speichern wird jede
  Projektsumme gegen die Füxle-Logik geprüft – bei Abweichung Abbruch „nicht versenden“.
- **Die Füxle-Datei selbst NIE extern versenden** (enthält Rohdaten, Kommentare, alle Projekte).

## Version 6.2 (2026-11-05): einfachere Bedienung – VERBINDLICHE Struktur

**Reiter (Farbe):** 🟢 `Cockpit` · `Uebersicht` · `Interne_Auswertung` | 🟡 `Pruefen_Korrigieren` ·
`Abgleich_Vormonate` | 🔵 `Zusatzkosten` · `Manuelle_Zeitbuchungen` · `Stammdaten` | ⚪ `Rohdaten_Kalender` ·
`Rohdaten_Fahrten` · `<Sonderkalk>_Kalk` · `Listen` (versteckt). Entfallen: Filter_Dashboard, Uebersicht_<Jahr>,
Gesamt_Alle_Jahre, Monatstrend, Hauptaufgaben_Verteilung, Plausibilitaets_Check, Pruefliste, Parameter.

- **Cockpit:** Filter Jahr/Monat/Firma/Projekt/Status (KEIN Mitarbeiter-Filter – Datenschutz, Nutzerin). Ergebnis
  mit ALLEN Bestandteilen (Kalender, manuelle Zeiten, Sonderkalk., Fahrten, Zusatzkosten), Projektliste der
  Auswahl, Top 5, Monatsverlauf, Versionsblock mit **Freigabe**, Prüfstatus, Monatsabschluss-Checkliste.
  Test: Cockpit „(Alle)“ = Übersicht GESAMT auf den Cent.
- **Uebersicht:** ein Reiter mit Jahr-Auswahl (inkl. „(Alle)“). Projektliste enthält auch Projekte, die nur in
  Zusatzkosten/manuellen Zeiten vorkommen.
- **Interne_Auswertung (GF):** live, Filter inkl. Mitarbeiter; Stunden je Mitarbeiter × Hauptaufgabe (inkl.
  informativer Niedermaier-Stunden) und Monat × Mitarbeiter.
- **Pruefen_Korrigieren = die EINE Liste:** jede Zeile hat eine feste **ID** (Rohdaten Spalte X). Entscheidung in
  Spalte J (Projekt / Unberücksichtigt / „✔ passt“), Kommentar K. Rohdaten holen die Entscheidung per ID
  (`_entscheidung_formel`) – in den Rohdaten wird nichts mehr von Hand eingetragen. Oben offene Punkte (teuerste
  zuerst), darunter alle Entscheidungen, 200 freie Zeilen (ID eintragen), unten eingeklappt die Hinweise.
  Rechts **Regel-Vorschläge** (ab 3 gleichen Korrekturen); mit „x“ angenommene Regeln werden beim nächsten Lauf
  als `projektname_erkennung.stichwort_regeln` übernommen (dann Config im ZIP nachziehen).
- **Ausmisten:** Korrekturen ohne Wirkung („Unberücksichtigt“ bei Terminen ohne Projekt, Korrektur = automatisch)
  werden beim Neuaufbau entfernt; bei unsicheren Zeilen bleiben sie als „✔ passt“ erhalten.
- **Abgleich:** nur Abweichungen + Summenzeile; Einzelzeilen mit Spalte „Ursache“.
- **Manuelle Zeitbuchungen:** neue Zeilen holen den Stundensatz automatisch (vorher leer → 0 €).
- Firma/Status stehen als Formelspalten in allen Quellen (für die Filter).

## Version 6.1 (2026-11-05): Regeln aus dem ersten Echtdaten-Lauf (Basis v01 bis 30.09.2026)

- **Dateiname:** `Füxle_<Zeitraum>_vNN.xlsx` (`config.dateiname_praefix`).
- **Sonderkalkulation nur für den genannten Mitarbeiter** (`sonderkalkulationen.<P>.mitarbeiter`): Zeiten
  anderer Personen zu Niedermaier zählen normal mit Stundensatz (`sonderkalk_gilt()`).
- **Korrekturen wirken überall:** Ganztagespauschale (Frutania 8 h/Tag) und Tagessatz-Blöcke werden auch für
  von Hand zugeordnete Termine gerechnet (z.B. „M. Neininger Grafschaft“, „Niedermaier Spedition …“).
- **Wochenpauschale:** endet am `wochenpauschale.bis` (2026-08-31). Urlaub zählt nur, wenn er die Person selbst
  betrifft: eigener Kalender ohne fremden Namen („Felix Urlaub“ bei Marius zählt NICHT) oder ein anderer
  Kalender, der die Person ausdrücklich nennt („Urlaub MN …“ im Kalender der Assistenz zählt).
- **Fahrten:** nächster Termin gewinnt; gelb nur, wenn ein anderes Projekt weniger als
  `matching.unsicher_wenn_abstand_unter_h` (2 h) weiter weg liegt. Übergänge zwischen Terminen sind normal.
- **Doppelte Termine:** identische Zeilen im selben Kalender werden einmal gezählt (die Augustdatei hatte 32
  Doppelungen = 66 h). Gleicher Termin mit Projekt in zwei Kalendern derselben Person → gelb.
- **`neuaufbau()` zusätzliche Parameter:** `korrekturen` (Einzelentscheidungen aus dem Chat → Spalte
  „Manuelle Projekt-Korrektur“), `zusatzkosten` (bereinigte Liste), `partner_ueberschreiben`,
  `fahrten_als_geschaeftlich` (bestätigte „Offen“-Fahrten), `vergleich_bis` (Vergleichsgrenze bei Dateien ohne
  Stempel). Eine Korrektur, die nicht genau eine Zeile trifft, kommt auf die Prüfliste.
- **Quellen je Zeitraum laden:** Kalenderexporte überschneiden sich (Spesen-Dateien enthalten auch 2026). Jede
  Quelle nur für ihren Zeitraum laden – sonst Doppelzählung (so entstand der doppelte Januar 2026).

## Kernprinzipien

- **Bibliothek statt Neuerfindung.** Die komplette Logik liegt fertig getestet in
  `scripts/report_lib.py`. Diese Funktionen importieren und aufrufen, NICHT jedes Mal neu
  schreiben.
- **Kosten werden pro Zeile berechnet, nicht pro Projekt-Summe.** Wegen der Satzhistorie
  (Sätze können sich zu einem Stichtag ändern) wird der Stundensatz/km-Satz je Kalender-
  bzw. Fahrtzeile anhand IHRES Datums ermittelt (`compute_kalender_kosten`,
  `compute_fahrten_kosten`) — NICHT nachträglich Stunden-Summe × ein einzelner Satz.
- **Config ist lebend – aber nur über ein neues Skill-ZIP dauerhaft.** Neue Projekte, Mitarbeiter, Sätze
  (mit Gültig-ab-Datum!), Sonderkonditionen: in der Config ergänzen UND der Nutzerin eine aktualisierte
  Skill-ZIP anbieten. Live-Pflege (Stammliste, Partner-Zuordnung) passiert im Parameter-Reiter und wird bei der
  Fortführung aus der freigegebenen Vorlage übernommen.
- **Nicht raten bei Unklarheiten.** Neue Projektnamen, nicht eindeutige Hauptaufgaben-
  Kategorien, unplausible Wochen-Stunden (siehe Plausibilitätscheck): transparent zeigen,
  nicht automatisch entscheiden.
- **Reihenfolge beim Bauen der Wochenpauschale beachten:** `generate_wochenpauschale_rows()`
  IMMER vor `match_trips_to_calendar()` in den `calendar_df` einmischen, aber die
  Pauschale-Zeilen dürfen NIE Matching-Kandidaten für Fahrten sein (ist in
  `match_trips_to_calendar()` bereits über `Ist_Pauschale` abgesichert — beim Erweitern der
  Bibliothek nicht versehentlich aufheben, siehe Selbstprüfung vom 2026-07-22, bei der genau
  das ein realer Fehler war).

## Ablauf

### 1. Zeitraum, Jahr(e) & Berichtstyp klären
- Immer explizit fragen: einzelnes Jahr, mehrere Jahre, oder projektbezogen über die volle
  Historie? Kein Standardzeitraum.
- Bei Jahresberichten den Zeitraum als `datetime(JAHR,1,1)` bis `datetime(JAHR,12,31,23,59,59)`
  übergeben — NICHT auf einen Montag "vorspulen" (siehe Bugfix-Hinweis in `report_lib.py`,
  `generate_wochenpauschale_rows`: Wochen vor `period_start` werden bewusst NICHT ergänzt,
  sonst leckt eine Pauschale ins Vorjahr).

### 2. Rohdaten einlesen
- Kalender: `load_multiple_calendars()`. Autolog: `load_autolog_csv()` je Kennzeichen,
  Fahrer-Zuordnung kommt aus der Config, nicht aus dem Export. Kennzeichen-Schreibweise wird
  automatisch normalisiert (z.B. "VS MN 1000" vs. "VSMN1000" im selben Export – realer Fall).
- **Aliase/Kurzformen** (z.B. "Nickles" = "Koko", "Sand" = "Sandformation") stehen unter
  `projektname_erkennung.aliase` und werden von `extract_project()` automatisch aufgelöst.
  Neue Aliase dort ergänzen, sobald die Nutzerin eine Kurzform bestätigt.
- **Manuell nacherfasste Zeiten** (Termine, die noch nicht im Kalender stehen): über
  `prepare_manuelle_zeitbuchungen(df, config)` aufbereiten (df mit Spalten Datum, Mitarbeiter,
  Projekt, Hauptaufgabe, Stunden, Anmerkung) und als `manuelle_zeitbuchungen_vorbelegt=` an
  `build_excel_workbook()` übergeben. Landen im Sheet "Manuelle_Zeitbuchungen" und fließen
  automatisch in Stunden/Kosten der Übersicht ein. Bei Unklarheit zu Datum/Jahr/Stundenzahl
  IMMER nachfragen, nicht schätzen (siehe Vorfall 2026-07-23: Nutzerin hatte Jahr nicht
  angegeben, mehrere Posten unvollständig).
- **Zwei-Kalender-Dubletten-Risiko bei Altdaten:** Wenn mehrere historische Kalenderexporte für
  dieselbe Person vorliegen (z.B. "Kikripp_Kalender" und "Outlook_Kalender" 2024/2025), IMMER
  auf Überschneidung prüfen (gleicher Betreff+Datum), bevor beide als Quelle verwendet werden –
  sonst droht Doppelzählung. Bei Verdacht auf Überlappung: Liste der NUR in der einen Datei
  vorkommenden, projektrelevanten (in Anführungszeichen stehenden) Termine erzeugen und der
  Nutzerin zur Bestätigung vorlegen, statt beide Dateien blind zu addieren.
- Details zu Formaten, Spalten und bekannten Eigenheiten: `references/datenquellen_und_formate.md`.

### 3. Sonderkalkulationen
- Tagessatz-Projekte (z.B. Niedermaier): `calc_tagessatz_block_kosten()` liefert jetzt ZWEI
  Tabellen — Blöcke (Tagessätze/Übernachtung) und eine SEPARATE Liste der betroffenen
  Kalenderwochen (Anfahrtspauschale ist seit 2026-07-22 wochenbasiert, nicht blockbasiert).

### 4. Plausibilitätscheck
- `plausibility_check(calendar_df, config)` läuft automatisch in `build_excel_workbook()` mit
  ein (Sheet "Plausibilitaets_Check"). Ergebnis vor Auslieferung ansehen — Auffälligkeiten
  im Chat kurz erwähnen, nicht nur ins Excel schieben.

### 5. Excel-Report bauen
- `build_excel_workbook(...)` gibt `(wb, ctx)` zurück (speichert NICHT selbst).
- `finalize_workbook(wb, ctx, calendar_df, trips_matched_df, config)` fügt Jahres-Übersichten
  (`Uebersicht_<Jahr>` für jedes in den Daten vorkommende Jahr), eine `Gesamt_Alle_Jahre`-Sicht
  und das `Filter_Dashboard` hinzu und speichert die Datei — diese Funktion IMMER als letzten
  Schritt aufrufen.
- **Zusatzkosten aus einer Vorversion übernehmen:** falls die Nutzerin eine frühere Version
  der Ausgabedatei mitschickt (mit bereits händisch eingetragenen Zusatzkosten), vorher
  `load_zusatzkosten_from_workbook(pfad)` aufrufen und das Ergebnis als
  `zusatzkosten_vorbelegt=` an `build_excel_workbook()` übergeben — sonst gehen händische
  Einträge beim Neuaufbau verloren.
- Nach dem Bauen: **immer** `recalc.py` aus dem `xlsx`-Skill laufen lassen, erst bei
  `total_errors: 0` ausliefern.
- (Version 6: `neuaufbau()`/`fortfuehrung()` erledigen build + finalize + Übernahme aus der Vorversion.)

### 6. Ergebnis vorlegen & Config-Pflege
- Datei(en) nach `/mnt/user-data/outputs`, `present_files`.
- Kurz hinweisen: neue unbekannte Projektnamen, Plausibilitätscheck-Treffer, "Nicht eindeutig -
  bitte prüfen"-Hauptaufgaben, TBD-Firma/Status.
- Bei neuen Infos (Satzänderung MIT Gültig-ab-Datum, neues Projekt, neue Sonderkalkulation):
  `config/projekt_konfiguration.json` sofort aktualisieren.

## Bekannte, bewusste Design-Entscheidungen (aus der Selbstprüfung 2026-07-22)

- Ignorierte "Projektnamen" (`projektname_erkennung.ignorieren`) bleiben in `Rohdaten_Kalender`/
  `Rohdaten_Fahrten` sichtbar und fließen daher in die "(Alle)"-Auswertung des
  Filter-Dashboards mit ein, erscheinen aber NICHT als eigene Zeile in den
  Übersichts-Sheets. Das Dashboard-Gesamtergebnis kann dadurch geringfügig von der Summe der
  sichtbaren Übersichtszeilen abweichen — das ist so gewollt (Transparenz in den Rohdaten),
  aber der Nutzerin bei Bedarf erklären.
- Die Übersicht zeigt Firma/Status je Projekt STATISCH aus der Config, unabhängig vom
  jeweiligen Berichtsjahr. Ein Projekt, das z.B. erst 2025 begann, zeigt in einer 2024er-
  Übersicht ggf. trotzdem "aktiv" an, wenn kein Enddatum gepflegt ist. Falls die Nutzerin
  historisch exakte Status-Werte pro Jahr braucht, müsste das noch erweitert werden
  (aktuell nicht implementiert).
- Tagessatz-/Pauschale-Werte der Sonderkalkulation (z.B. Niedermaier) werden NICHT über
  `Parameter`-Zellen referenziert, sondern als Werte aus der Config direkt eingetragen
  (anders als Stundensatz/km-Satz, die über die Satzhistorie-Funktionen laufen). Bei einer
  Änderung dieser Sätze muss die Config angepasst UND der Bericht neu gebaut werden — ein
  Ändern der Zahl direkt im Parameter-Sheet wirkt sich hier NICHT aus.

## Referenzdateien

- `references/datenquellen_und_formate.md` — Kalender-/Autolog-CSV-Formate.
- `references/matching_und_kalkulation.md` — Matching-Fenster, Übernachtungs-Erkennung,
  Sonderkalkulation-Grundprinzip.
- `references/excel_ausgabe_struktur.md` — Sheet-Struktur (Basis-Version, Std. Ergänzungen
  aus Version 2 siehe `references/mehrjahres_erweiterungen.md`).
- `references/mehrjahres_erweiterungen.md` — NEU: Satzhistorie, MwSt., Hauptaufgaben,
  Wochenpauschale, Zusatzkosten, Plausibilitätscheck, Filter-Dashboard, Mehrjahres-Struktur.
- `config/projekt_konfiguration.json` — lebende Konfiguration.
- `scripts/report_lib.py` — getestete Kernbibliothek.

## Version 3 (2026-07-24): Dashboard-Fix, Partner-Zuordnung, Management-Sicht

- **Dashboard-Bug behoben:** Die SUMPRODUCT+IF-Formeln aus Version 2 zeigten in echtem Excel
  bei manchen Nutzern keine Ergebnisse (funktionierte nur im Testwerkzeug). Das
  `Filter_Dashboard` nutzt jetzt ausschließlich klassische `SUMIFS`-Formeln mit einer
  Helper-Spalte (`=IF(Auswahl="(Alle)","*",Auswahl)` bzw. `">=0"` für die numerische
  Jahres-Spalte) – robust in jeder Excel-Version. **Bei künftigen Änderungen am Dashboard:
  keine SUMPRODUCT+IF-Array-Formeln mehr verwenden, sondern dieses SUMIFS+Helper-Muster.**
- **5. Hauptaufgaben-Kategorie "Projektbetreuung"** ergänzt (Telefonate, laufende Betreuung –
  ausdrücklich KEINE Verhandlungstermine). Mitarbeiter-Fallback (`fallback_je_mitarbeiter` in
  der Config) greift, wenn kein Keyword passt, statt generisch "Nicht eindeutig".
- **Partner_Projekt_Zuordnung-Sheet:** editierbare Tabelle, die jeden Autolog-"Partner" einem
  Projekt oder "Unberücksichtigt" zuordnet. `apply_partner_zuordnung()` MUSS nach
  `match_trips_to_calendar()` und VOR `compute_fahrten_kosten()` aufgerufen werden (Reihenfolge
  wichtig: erst Kalender-Matching mit Vorrang, dann Partner-Fallback für den Rest, dann erst
  Kosten berechnen). "Unberücksichtigt" filtert Fahrten komplett aus (auch aus den
  "Nicht_zugeordnete_Fahrten").
- **Neue Sheets:** `Management_Summary` (in Version 4 wieder entfernt), `Monatstrend` (Tabelle + 2 Liniendiagramme),
  `Hauptaufgaben_Verteilung` (Tabelle + Kreisdiagramm), `Interne_Auswertung` (lange Tabelle
  Monat × Mitarbeiter × Hauptaufgabe, inkl. Niedermaier als informative Stunden).
- **Spaltenlayout von Rohdaten_Kalender/Rohdaten_Fahrten hat sich geändert** (Jahr+Monat jetzt
  vorne, siehe `references/excel_ausgabe_struktur.md` für die aktuelle Reihenfolge) – bei
  Formel-Änderungen die Spaltenbuchstaben nicht aus Version 1/2 übernehmen.

## Monatliche Fortführung

**Ersetzt ab Version 6 durch `fortfuehrung()` (siehe oben).** Die frühere Schritt-für-Schritt-Anleitung
(Rohdaten der alten Datei selbst einlesen, Dubletten selbst prüfen, Loader einzeln aufrufen) war Ursache
für S1: Sie wurde jeden Monat neu improvisiert, die Lade-Funktionen übersprangen die erste Zusatzkosten-/
Zeitbuchungszeile und fanden die Partner-Zuordnung nicht mehr, und Korrekturen gingen verloren.
Nicht mehr verwenden.

## Version 4 (2026-07-24, Fortsetzung): Live-Zuordnung, Reiter-Aufräumen, Auswertungs-Dashboard

- **Management_Summary komplett entfernt** (von der Nutzerin als nicht aussagekräftig bewertet).
- **Partner_Projekt_Zuordnung und Projekt-Stammliste sind jetzt Teil des `Parameter`-Reiters**
  (kein eigener Tab mehr) und **live**: Rohdaten_Fahrten berechnet Projekt/Firma/Herkunft per
  `VLOOKUP`-Formel gegen diese Tabellen — Änderungen dort wirken sich SOFORT auf
  Rohdaten_Fahrten, Übersicht und Filter-Dashboard aus, ohne neuen Bericht-Lauf.
- **Wichtige VLOOKUP-Fallstricke, die dabei gefunden wurden (beim Erweitern nicht wiederholen):**
  - Wenn die Zuordnungs-Zelle in der Partner-Tabelle leer ist, liefert `VLOOKUP` **0** (nicht
    leer!) zurück. Immer explizit auf `=0` prüfen und wie leer behandeln, sonst landet eine "0"
    als Phantom-Projekt in den Daten.
  - `SUMIFS(...,Spalte,"<>")` filtert bei Formelzellen, die "" zurückgeben, NICHT zuverlässig
    (funktioniert nur bei wirklich leeren Zellen). Für "nicht leer" bei Formel-Ergebnissen
    stattdessen den Wildcard `"?*"` (mindestens ein Zeichen) verwenden.
  - Ignorierte Kalender-Matches (z.B. Adressen wie "Am Doniswald", interne Notizen) dürfen bei
    der Fahrten-Zuordnung nicht ungeprüft als "echtes" Projekt durchgereicht werden — vorher
    gegen die Projekt-Stammliste prüfen, ob das gematchte Projekt als "Ignoriert / kein Projekt"
    hinterlegt ist.
- **Separates "Nicht_zugeordnete_Fahrten"-Sheet entfernt** — `Rohdaten_Fahrten` enthält jetzt
  ALLE Fahrten (auch nicht zugeordnete/unberücksichtigte); über die Spalte "Projekt" (leer) bzw.
  "Herkunft" filtern, um offene Fälle zu finden.
- **Filter-Dashboard zur echten Auswertung ausgebaut:** unter den Kennzahlen automatische
  Kreuztabelle Mitarbeiter × Hauptaufgabe (Std. + Kosten Zeit), reagiert auf die
  Jahr/Monat/Projekt/Firma-Filter oben. **Bekannte Einschränkung:** Die Kennzahlen "Stunden
  gesamt"/"Kosten Zeit" im oberen Kennzahlen-Block schließen manuelle Zeitbuchungen und
  Sonderkalkulationen (Niedermaier) NICHT ein (nur echte Kalendereinträge) — für die
  vollständige Summe die Uebersicht_<Jahr>/Gesamt_Alle_Jahre-Sheets nutzen. Bei Bedarf künftig
  nachrüsten.
- **Reiter-Reihenfolge (Version 6: Abgleich_Vormonate und Pruefliste ganz vorne):** Filter_Dashboard, Uebersicht_<Jahr>, Gesamt_Alle_Jahre, Monatstrend,
  Hauptaufgaben_Verteilung, Interne_Auswertung (das, was die Nutzerin braucht) → Parameter,
  Zusatzkosten, Manuelle_Zeitbuchungen, Sonderkalkulations-Sheets, Plausibilitaets_Check
  (Stammdaten/Kosten) → Rohdaten_Kalender, Rohdaten_Fahrten, Listen (Rohdaten, ganz hinten).
  Diese Reihenfolge beim Erweitern beibehalten (`finalize_workbook()`, Abschnitt
  "Reihenfolge der Reiter").

## Version 5 (2026-07-24, Fortsetzung 2): Manuelle Korrektur, Farbcodierung, Ganztagespauschale

- **"Manuelle Projekt-Korrektur"-Spalte** (Dropdown inkl. "Unberücksichtigt") in `Rohdaten_Kalender`
  UND `Rohdaten_Fahrten` ergänzt. Hat in beiden Sheets IMMER Vorrang vor automatischer Erkennung
  (Kalender-Match/Partner-Zuordnung). Wirkt live, kein neuer Bericht-Lauf nötig.
- **Rohdaten_Kalender zeigt jetzt ALLE Kalendertermine**, nicht nur die mit erkanntem Projekt
  (analog zu Rohdaten_Fahrten). Dadurch können bisher unerkannte/unquotierte Projekterwähnungen
  händisch über die Korrektur-Spalte zugeordnet werden.
- **Farbcodierung durchgängig:** Blaue Zellfüllung = editierbar (Sätze, Firma/Status,
  Partner-Zuordnung, beide Korrektur-Spalten, Zusatzkosten, Manuelle Zeitbuchungen). Grüne
  Zellfüllung = hier neue Projekte eintragen (Projekt-Spalte der Stammliste inkl. 20
  Vorrats-Zeilen). Bei Erweiterungen dieses Farbschema konsequent weiterführen.
- **"Ganztagespauschale"-Mechanismus** (`config.ganztagespauschale`) für Projekte, bei denen
  ganztägige/mehrtägige Kalenderblöcke mit X Stunden PRO TAG verrechnet werden (aktuell:
  Frutania, 8 Std./Tag) — Alternative zur kompletten Kostenausschließung bei
  `Mehrtaegig`-Blockern. **Tage-Zählung wichtig:** nicht die rohe Dauer durch 24 runden
  (unterschätzt bei "08:00 Tag 1 – 16:00 Tag 2"-Mustern!), sondern echte überspannte
  Kalendertage zählen, mit Sonderfall exakt Mitternacht-zu-Mitternacht (klassische
  "ganztägig"-Konvention, Ende-Datum exklusiv) vs. andere Uhrzeiten (Start- UND End-Kalendertag
  mitzählen). Siehe `compute_kalender_kosten()`, Funktion `adjust_dauer`.
- **"Frutania" als feste Kurzform ohne Anführungszeichen ergänzt** — Analyse ergab, dass fast
  jedes Projekt gelegentlich unquotiert im Kalender auftaucht, aber nur bei eindeutigen,
  kollisionsarmen Namen (hohe Trefferzahl, keine Fehltreffer bei Stichprobe) automatisch
  ergänzen. **Vorsicht bei generischen Namen** (z.B. "Mühle" traf fälschlich "Hessenmühle",
  "Adler" traf "Hotel Adler", "Juli" ist ein Monatsname) — hier lieber die manuelle
  Korrektur-Spalte nutzen statt automatisches Keyword-Matching zu erweitern.
- **Zwei weitere Excel-Formel-Fallstricke gefunden (zusätzlich zu Version 4):**
  - Ein direkter Zellbezug (`=R5`) auf eine WIRKLICH leere Zelle liefert in Excel **0**, nicht
    leer. Immer `IF(Zelle="","",Zelle)` statt nacktem Zellbezug verwenden, wenn die Zelle leer
    sein kann.
  - Sobald ein Sheet (hier: Rohdaten_Kalender) auch nicht-projektbezogene Zeilen enthält,
    müssen ALLE Dashboard-Aggregat-Formeln (auch die Mitarbeiter×Hauptaufgabe-Kreuztabelle) den
    `"?*"`-Leer-Filter auf die Projekt-Spalte bekommen — sonst werden generische
    Kalendereinträge ohne Projektbezug mitgezählt.
  - Ignorierte Projekte (`projektname_erkennung.ignorieren`) zusätzlich per
    `Firma,"<>Ignoriert / kein Projekt"` aus Dashboard-Summen ausschließen, da sie in den
    Rohdaten bewusst sichtbar bleiben.

## Abgrenzung

- Für Excel-Formatierung/Formel-Mechanik gilt zusätzlich der allgemeine `xlsx`-Skill.
- Ersetzt keine abschließende buchhalterische Prüfung.

## Version 6 (2026-11-04): Absicherung Welle 1 – was geändert wurde und warum

| Änderung | behebt |
|---|---|
| Versionsstempel + Freigabe im Parameter-Reiter, Dateiname `_vNN`, `pruefe_vorlage()` stoppt bei falscher Vorlage | S1 |
| `fortfuehrung()`: Vormonate eingefroren, nur Zeilen nach „Datenstand bis“ neu, Nachträge → Prüfliste | S1 |
| Lade-Funktionen suchen die Kopfzeile (früher `start_row=6` → erste Zusatzkosten- und Zeitbuchungszeile ging bei jeder Fortführung verloren) | S1 |
| `load_partner_zuordnung_from_workbook()` liest den Parameter-Reiter (früher: nicht existierender Reiter → still `{}`) | S2 |
| Manuelle Korrekturen (Kalender + Fahrten) und gepflegte Stammliste werden übernommen | S2 |
| Prüfblatt `Abgleich_Vormonate` | S1/S3 |
| `Zuordnung_Grund`, `Prüfen`, gelbe Markierung, Reiter `Pruefliste` | S2/S3 |
| Typografische Anführungszeichen („Koko“) werden erkannt; abweichende Schreibweise („sand“) → zugeordnet + gelb statt Phantomprojekt | S2 |
| Partner „Unberücksichtigt“ gewinnt vor dem Kalender-Match (Nutzerin 2026-11-04); Fahrt bleibt sichtbar statt gelöscht | S2 |
| `Kosten_Zeit_EUR` in Rohdaten_Kalender ist eine Formel – eine Korrektur wirkt jetzt auch auf die Kosten (früher: Stunden ja, Kosten 0 €) | S2 |
| Parameter-Reiter: Stammliste überschrieb die Stundensätze (Spalte D) → Stammliste F–H, Partner J–K, Version M–N; Sätze nur noch zur Info (nicht blau) | S3 |
| Soll-Arbeitszeit entfernt (Config + Parameter) | Auslastung |
| Dashboard-Kreuztabelle „Kosten Zeit“ schließt ignorierte Projekte aus (wie die übrigen Dashboard-Formeln) | – |
| Nur **markiert**, nicht geändert: Niedermaier-Kurztermin löst 825 € Anfahrtspauschale aus; Tageszählung per `round()`; Monatstrend/Hauptaufgaben/Interne_Auswertung sind statisch und enthalten Blöcke/ignorierte Termine | – (Entscheidung Nutzerin offen) |
| Automatische Tests `tests/` (erfundene Daten, Regressionstest gegen Version 5) | alle |

Bewusst NICHT geändert: SUMIFS statt SUMPRODUCT; Kosten pro Zeile zum Datum; Reihenfolge
Wochenpauschale → Matching → Partner-Zuordnung → Kosten; nichts raten. Spalten A–R (Kalender) bzw. A–S
(Fahrten) behalten ihre Buchstaben; neue Spalten hängen hinten an.
