# Excel-Ausgabe-Struktur

> **Version 6.2 (2026-11-05): Reiterstruktur siehe SKILL.md „Version 6.2“ – hat Vorrang.** Ergänzend:
> Rohdaten_Kalender Q / Rohdaten_Fahrten S = Formel „Entscheidung aus Pruefen_Korrigieren“ (per ID in Spalte X),
> Spalte W = Status (Formel). Parameter-Reiter heißt jetzt „Stammdaten“ (Projekte F–H, Partner J–K), der
> Versionsblock steht im Cockpit (Spalten E–F). Zusatzkosten H/I und Manuelle_Zeitbuchungen K/L = Firma/Status.
> Sonderkalk-Reiter: Blöcke K–O bzw. Pauschalen E–J = Projekt/Firma/Status/Mitarbeiter/Hauptaufgabe.
>
> **Stand Version 6.0/6.1 (überholt in den genannten Punkten):**
>
> **Dateiname:** `Projektuebersicht_<Zeitraum>_v<NN>.xlsx` (z.B. `Projektuebersicht_2026-11_v02.xlsx`).
> Die Version im Dateinamen muss zur Version im Parameter-Reiter passen, sonst stoppt die Fortführung.
>
> **Reiter-Reihenfolge:** Abgleich_Vormonate, Pruefliste, Filter_Dashboard, Uebersicht_<Jahr>…,
> Gesamt_Alle_Jahre, Monatstrend, Hauptaufgaben_Verteilung, Interne_Auswertung, Parameter, Zusatzkosten,
> Manuelle_Zeitbuchungen, <Sonderkalk>_Kalk, Plausibilitaets_Check, Rohdaten_Kalender, Rohdaten_Fahrten,
> Listen (versteckt). Die Reiter `Nicht_zugeordnete_Fahrten`, `Partner_Projekt_Zuordnung` und
> `Management_Summary` gibt es nicht mehr.
>
> **Parameter:** A–D Stundensätze (nur Info), km-Satz, MwSt. (B, blau, wird referenziert), Niedermaier-Konditionen
> (Info) · F–H Projekt-Stammliste (grün = neue Projekte, blau = Firma/Status) · J–K Partner → Projekt (blau) ·
> M–N **Berichtsversion**: Version, Vorgänger-Version, Berichtszeitraum, Datenstand bis, Erstellt am,
> Skill-Version, **Freigegeben am / Freigegeben von** (blau, trägt die Nutzerin nach der GF-Prüfung ein).
> Keine Soll-Arbeitszeit mehr.
>
> **Rohdaten_Kalender:** A Jahr · B Monat · C Mitarbeiter · D Kalendertyp · E Projekt (Formel: Korrektur vor
> automatisch) · F Firma · G Hauptaufgabe · H Datum · I Start · J Ende · K Dauer_h (volle Genauigkeit) ·
> L Stundensatz_EUR (fest, zum Datum) · **M Kosten_Zeit_EUR (Formel: 0 bei leerem Projekt, Blocker oder
> Sonderkalkulation, sonst ROUND(K×L;2))** · N Aufgabe · O Mehrtaegig_Blocker · P Ist_Pauschale ·
> Q Manuelle Projekt-Korrektur (blau) · R Projekt (automatisch, intern) · **S Zuordnung_Grund · T Prüfen ·
> U Betreff · V Quelle** („neu“ / „Vorversion vNN“). Gelb = Blocker oder unsicher.
>
> **Rohdaten_Fahrten:** A–S wie Version 5, D Projekt = Korrektur → Partner „Unberücksichtigt“ (gewinnt) →
> Kalender-Match (nicht ignoriert) → Partner-Zuordnung; M Kosten ohne fest eingetragenen Projektnamen
> (aus `sonderkalkulationen…fahrten_kostentechnisch_ausschliessen`) · **T Zuordnung_Grund · U Prüfen · V Quelle**.
> Fahrten zu „Unberücksichtigt“-Partnern bleiben sichtbar (Projekt leer).
>
> **Pruefliste:** offene Punkte (Zähler oben), je Eintrag Bereich, Datum, Mitarbeiter, Betreff/Partner,
> automatisches Projekt, Grund, Rohdaten-Zeile, Status (Formel: erledigt bei Korrektur oder „x“ in Spalte J).
>
> **Abgleich_Vormonate:** A4 Ergebnis („Vormonate unverändert ✔“ / „X Abweichungen“), Tabelle Monat × Projekt
> (Std., Kosten netto, km jeweils alt/neu/Differenz, Ergebnis, automatische Begründung, blaue Spalte
> „Entscheidung / Kommentar“), darunter die betroffenen Einzelzeilen. Statisch (Stand bei Erstellung).


Erzeugt durch `report_lib.build_excel_workbook()`. Reihenfolge und Namen der Sheets
NICHT ändern, ohne die Nutzerin zu informieren — sie ist an dieses Layout gewöhnt.

## Sheet: Parameter
- Stundensätze je Mitarbeiter (blau, editierbar), Kürzel aus der Config
- Kilometersatz (blau, editierbar)
- Je Sonderkalkulations-Projekt (z.B. Niedermaier): eigener Block mit Tagessatz,
  An-/Abfahrtspauschale, Übernachtungspauschale (blau, editierbar)
- Alle Formeln in anderen Sheets referenzieren AUSSCHLIESSLICH diese Zellen (nie
  hartkodierte Zahlen) — Grundregel aus dem `xlsx`-Skill

## Sheet: Rohdaten_Kalender
Spalten: `Mitarbeiter | Kalendertyp | Projekt | Datum | Start | Ende | Dauer_h | Aufgabe | Mehrtaegig_Blocker`
- Eine Zeile je Kalendertermin mit erkanntem Projekt (auch ignorierte Projektnamen bleiben
  hier sichtbar, siehe `matching_und_kalkulation.md`)
- Mehrtägige Blocker (>20h) gelb hinterlegt, Spalte `Mehrtaegig_Blocker` = "JA - Klärung nötig"

## Sheet: Rohdaten_Fahrten
Spalten: `Datum | Start | Ende | Projekt | Distanz (km) | Dauer_h | Start-Adresse | End-Adresse | Partner (Autolog) | Zweck`
- Nur Fahrten, die einem Projekt zugeordnet werden konnten (auch bei Tagessatz-Projekten,
  dort aber ohne Kostenwirkung)

## Sheet: Nicht_zugeordnete_Fahrten
Spalten: `Datum | Start | Ende | Distanz (km) | Start-Adresse | End-Adresse | Partner (Autolog) | Zweck`
- Alle Fahrten außerhalb jedes Matching-Fensters — rot hervorgehobener Titel, zur
  manuellen Prüfung durch die Nutzerin

## Sheet je Sonderkalkulations-Projekt (z.B. "Spedition_Niedermaier_Kalk")
Spalten: `Start | Ende | Tage (Vor-Ort) | Nächte | Tagessätze (€) | An-/Abfahrtspauschale (€) | Übernachtung (€) | Kosten Block (€)`
- Eine Zeile je Buchungszeitraum/Kalenderblock, GESAMT-Zeile am Ende
- Wird automatisch für jeden Eintrag in `sonderkalkulationen` mit `typ: tagessatz_block` erzeugt

## Sheet: Übersicht (zweites Sheet, direkt nach Parameter)
Spalten: `Projekt | Firma | Status | Std. <Kürzel 1> | Std. <Kürzel 2> | ... | Std. gesamt |
Kosten Zeit (€) | Distanz gesamt (km) | Kosten Fahrt (€) | Fahrdauer gesamt (h, informativ) |
Gesamtkosten (€) | Hinweis`

- `Firma` / `Status` werden aus `projekt_stammliste` in der Config vorbelegt (leer/TBD, falls
  noch nicht bekannt) — NICHT von Formeln überschrieben, die Nutzerin kann diese Felder direkt
  in Excel nachtragen
- Stunden je Mitarbeiter: `SUMIFS` auf Rohdaten_Kalender, filtert zusätzlich
  `Mehrtaegig_Blocker = ""` (schließt Blocker-Einträge aus)
- Normale Projekte: `Kosten Zeit` = Summe (Std. je Mitarbeiter × Stundensatz aus Parameter);
  `Kosten Fahrt` = km × Kilometersatz aus Parameter
- Tagessatz-Projekte: `Kosten Zeit` verweist per Formel auf die GESAMT-Zelle des zugehörigen
  Sonderkalkulations-Sheets; `Kosten Fahrt` = 0 (fest, siehe Hinweis-Spalte); km/Fahrdauer
  trotzdem angezeigt (informativ)
- `Gesamtkosten` = `Kosten Zeit + Kosten Fahrt`
- Letzte Zeile: `GESAMT` mit Summenformeln über alle Projekte

## Formatierung (gemäß `xlsx`-Skill, hier verbindlich)
- Schriftart durchgehend Arial
- Kopfzeilen: dunkelblauer Fond (`1F3864`), weiße fette Schrift, zentriert
- Eingabezellen (Parameter): blaue Schrift (`0000FF`)
- Währungsformat `#,##0.00 €`, Stunden/km-Format `#,##0.0`
- Nach jedem Bau-Lauf: `recalc.py` aus dem `xlsx`-Skill ausführen, bis `total_errors: 0`

## Dateiname-Konvention
- Monatsbericht: `Projektuebersicht_[Zeitraum].xlsx`, z.B. `Projektuebersicht_2026-07.xlsx`
- Einzelprojekt-Bericht: `Projektbericht_[Projektname]_[Erstellungsdatum].xlsx`

## Ab Version 6.4: TransCare-Reiter
Reihenfolge: Cockpit, Uebersicht, Interne_Auswertung, Pruefen_Korrigieren, Abgleich_Vormonate, **TC_Bericht**,
**TC_Stand**, **Zahlungen**, **Berichtshistorie**, Zusatzkosten, Manuelle_Zeitbuchungen, Stammdaten,
Rohdaten_Kalender, Rohdaten_Fahrten, Sonderkalk, Listen.
- TC_Stand: Eingabe gemeldeter Stand je Position + Schalter B6 (`korrigiert (Füxle)` / `wie gemeldet`).
- Zahlungen: Rechnung, Zeitraum, Betrag brutto, Anmerkung; Summe wird in TC_Bericht abgezogen.
- Berichtshistorie: Protokoll jeder Meldung an TransCare.
- TC_Bericht: Formeln (SUMIFS), Auswahl per „x“, Druckbereich gesetzt; Teile Projekte / Allgemein / Abrechnung.
