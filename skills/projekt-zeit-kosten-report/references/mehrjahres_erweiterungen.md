# Mehrjahres-Erweiterungen (Version 2, Stand 2026-07-22)

> **Version 6 (2026-11):** Die Filter-Dashboard-Beschreibung unten (SUMPRODUCT) ist überholt – seit Version 3
> gilt SUMIFS + Helper-Spalte (siehe SKILL.md). Zusatzkosten/Manuelle Zeitbuchungen/Partner-Zuordnung/
> Stammliste/Korrekturen übernimmt `lade_vorlage()` bzw. `fortfuehrung()` automatisch; die Lade-Funktionen
> suchen die Kopfzeile (die alte feste Startzeile 6 hat die erste Datenzeile verloren). Die Soll-Arbeitszeit
> (`soll_arbeitszeit_pro_woche`) ist entfernt.


Ergänzt `excel_ausgabe_struktur.md` um alle seit dem Umbau vom 22.07.2026 hinzugekommenen
Bausteine. Auslöser war der Wunsch der Nutzerin nach Jahresauswertungen ab 2024, mehreren
Auswertungsdimensionen (Mitarbeiter/Projekt/Firma/Jahr) und einer Reihe neuer Geschäftsregeln.

## Satzhistorie statt fixer Sätze

`config.mitarbeiter_satzhistorie[<Name>].saetze` ist eine Liste von
`{gueltig_ab, stundensatz_eur}`. `report_lib.get_rate_for_date()` liefert den zum jeweiligen
Datum gültigen Satz (letzter Satz mit `gueltig_ab <= Datum`). Genauso `km_satz_historie` für
den Kilometersatz. **Wichtig:** Kosten werden deshalb pro Kalender-/Fahrtzeile berechnet
(`compute_kalender_kosten`, `compute_fahrten_kosten`), nicht als Stunden-Summe × ein fixer
Satz — sonst würde eine künftige Satzänderung alle historischen Jahre verzerren.

Aktueller Stand: Alle Sätze (MN 200 €, FS/JP je 150 €, km-Satz 1,20 € inkl. Fahrzeit) gelten
laut Nutzerin einheitlich rückwirkend ab 2024-01-01 — die Historie hat also aktuell nur einen
Eintrag pro Mitarbeiter, ist aber für künftige Änderungen vorbereitet (einfach einen weiteren
Eintrag mit neuem `gueltig_ab` ergänzen, nichts anderes anfassen).

## MwSt.-Ausweis

Alle Sätze sind netto (`preise_sind_netto: true`). Jede Übersichtszeile bekommt zusätzlich zu
"Gesamtkosten Netto" die Spalten "MwSt. (€)" (= Netto × `mwst_satz_prozent`/100) und
"Gesamtkosten Brutto (€)". Der Prozentsatz steht editierbar im Parameter-Sheet.

## Hauptaufgaben-Kategorien

`config.hauptaufgaben_kategorien` ordnet die Aufgabenbeschreibung (Text nach dem Projektnamen)
einer von vier Kategorien zu, per Keyword-Suche (`classify_hauptaufgabe()`):

- Verhandlungen / Kundentermine
- Vertrieb / Akquisition
- Projektorganisation / Terminvereinbarungen
- Projektadministration / Dokumentation

Nicht zuordenbare Texte bekommen bewusst `"Nicht eindeutig - bitte prüfen"` statt einer
geratenen Kategorie. **Die Keyword-Listen sind ein erster Entwurf und noch nicht mit echten
Mehrjahres-Daten geprüft** — nach dem ersten echten Lauf mit der Nutzerin durchgehen, wie viele
Einträge in "Nicht eindeutig" landen, und die Listen bei Bedarf ergänzen/korrigieren
(`config.hauptaufgaben_kategorien`, einfach neue Keywords in die passende Liste eintragen).

## Automatische Wochenpauschale

`config.wochenpauschale` beschreibt eine automatisch erzeugte Zeile pro Kalenderwoche
(`generate_wochenpauschale_rows()`): 5 Std./Woche für Marius Neininger, Kategorie
"Vertrieb / Akquisition", NICHT einem Kundenprojekt zugeordnet (eigene Pseudo-Projekt-Zeile
"Allgemeine Vertriebszeit (automatische Wochenpauschale)" in der Übersicht).

**Urlaubs-Ausnahme:** Enthält der Kalender der Person an irgendeinem Tag der Woche einen
Termin mit dem Stichwort "Urlaub", wird die GESAMTE Woche ausgesetzt (konservative Annahme,
auch bei nur teilweisem Urlaub in der Woche) und als "AUSGESETZT" markiert, statt einfach
gar nicht zu erscheinen — so bleibt sichtbar, dass die Aussetzung bewusst passiert ist.

**Zwei wichtige Bugs aus der Selbstprüfung, die hier behoben wurden (beim Erweitern der
Bibliothek nicht erneut einbauen):**
1. Die synthetischen Pauschale-Zeilen dürfen NIEMALS als Matching-Kandidaten für die
   Fahrten-Zuordnung dienen (hätte reale Fahrten von echten Projekten abgezogen). Abgesichert
   über den Filter `~calendar_df['Ist_Pauschale']` in `match_trips_to_calendar()`.
2. Wenn `period_start` nicht auf einen Montag fällt, darf KEINE zusätzliche Woche vor
   `period_start` ergänzt werden (das hätte eine Pauschale ins Vorjahr/den Vormonat "lecken"
   lassen). `generate_wochenpauschale_rows()` beginnt bewusst erst beim ersten Montag AB
   `period_start`.

## Zusatzkosten (manuelle Einzelposten)

Eigenes Sheet "Zusatzkosten" in der Ausgabedatei (Datum, Projekt, Kostenart, Betrag netto,
Anmerkung). Die Nutzerin trägt dort direkt in Excel ein, was selten anfällt (z.B. eine
Übernachtung im Ausnahmefall). Fließt automatisch über SUMIFS in die Projekt-Gesamtkosten
der jeweiligen Übersicht ein (nach Projekt und – bei Jahresübersichten – nach Jahr gefiltert).

**Wichtig beim Neu-Aufbau:** Da die Datei bei jedem Lauf neu erzeugt wird, würden händisch
eingetragene Zusatzkosten sonst verloren gehen. Vor dem nächsten Lauf `load_zusatzkosten_from_workbook()`
auf die vorherige Version der Ausgabedatei anwenden (falls die Nutzerin sie mitschickt) und das
Ergebnis als `zusatzkosten_vorbelegt=` an `build_excel_workbook()` übergeben.

## Plausibilitätscheck

Automatisch erzeugtes Sheet "Plausibilitaets_Check": listet jede Mitarbeiter/ISO-Kalenderwoche-
Kombination mit mehr als `config.plausibilitaets_check.max_stunden_pro_person_pro_woche`
(Standard 60) Stunden. Grund: der erste Testlauf hatte durch einen falsch interpretierten
mehrtägigen Kalenderblock 816 Std. in einer Woche errechnet — dieser Check soll solche Fälle
künftig VOR der Auslieferung sichtbar machen, ohne automatisch etwas zu verändern.

## Mehrjahres-Struktur & Filter-Dashboard

- `Rohdaten_Kalender` und `Rohdaten_Fahrten` enthalten jetzt eine `Jahr`-Spalte und alle Jahre
  gemeinsam (nicht mehr eine Datei pro Jahr).
- Für jedes in den Daten vorkommende Jahr wird automatisch ein Sheet `Uebersicht_<Jahr>`
  erzeugt, plus ein `Gesamt_Alle_Jahre`-Sheet ohne Jahresfilter. Beide nutzen dieselbe
  Projektliste, damit Jahre vergleichbar bleiben (ein Projekt ohne Aktivität in einem Jahr
  zeigt dort einfach 0).
- `Filter_Dashboard`-Sheet: vier Dropdowns (Jahr, Mitarbeiter, Projekt, Firma, jeweils mit
  "(Alle)"-Option) steuern per SUMPRODUCT-Formeln (Wildcard-Muster
  `IF(Auswahl="(Alle)",1,(Bereich=Auswahl))`) eine automatische Zusammenfassung (Stunden,
  Kosten Zeit, km, Kosten Fahrt, Zusatzkosten, Gesamt Netto/MwSt./Brutto).
- **Bekannte Einschränkung:** Das Dashboard-Ergebnis für "(Alle)" schließt auch Zeilen zu
  bewusst ignorierten "Projektnamen" (`projektname_erkennung.ignorieren`) mit ein, da diese in
  den Rohdaten-Sheets stehen bleiben. Die Summe der sichtbaren Übersichtszeilen kann dadurch
  geringfügig niedriger sein als das Dashboard-"(Alle)"-Ergebnis — kein Fehler, sondern
  gewollte Transparenz in den Rohdaten. Der Nutzerin bei Bedarf erklären.
- **Ebenfalls bekannte Einschränkung:** Firma/Status je Projekt sind in JEDER Jahresübersicht
  identisch (aus der aktuellen Config, nicht historisch differenziert). Ein Projekt, das z.B.
  erst 2025 startete, kann in der 2024er-Übersicht ggf. trotzdem mit Status "aktiv" erscheinen,
  wenn kein Enddatum in der Projektliste gepflegt ist. Bei Bedarf künftig erweitern (Firma/Status
  anhand von Start-/Enddatum pro Jahr ableiten statt statisch übernehmen).
