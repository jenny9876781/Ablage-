---
type: Praxisprojekt
title: Baustein 1 – Prozess & Ist-Zustand
stand: 2026-11-03
---
# Baustein 1 – Projekt-Zeit-/Kostenbericht

## Entscheidung (Entwurf – von mir zu bestätigen)
Gewählt: **monatlicher Projekt-Zeit-/Kostenbericht** (Arbeitszeit + Fahrten je Projekt → Kosten je Projekt und Firma).
Begründung: einziger Kandidat mit allen 6 Häkchen; läuft jeden Monat; mehrere Rollen;
das Ergebnis (Kosten je Projekt) nutzt die GF direkt für Abrechnung und Steuerung.
Verworfen: Zeiterfassung (Datenlage zu rot, wenig KI-Hebel), M&A (zu selten), Krippe (einmalig).
Besonderheit: Ein Teil läuft schon mit einem Claude-Skill → ich kann **vorher/nachher** messen.

## Ist-Kette (Rollen statt Namen) – Stand 04.11.2026
| # | Schritt | Rolle | Werkzeug | Status |
|---|---|---|---|---|
| 1 | Termin mit Projektname im Betreff eintragen | GF, Berater | Outlook | ⚠ **S1** Termine fehlen → Assistenz trägt händisch nach · ✔ Kurzformen gelöst (Alias-Liste im Skill) |
| 2 | Fahrt wird aufgezeichnet | GF, Berater | Fahrtenbuch-App | ✔ **S2 gelöst**: feste Zuordnung Fahrzeug → Fahrer im Skill |
| 3 | Monatsende: Kalender je Postfach + Fahrten exportieren | Assistenz | Outlook, App | – |
| 4 | Bericht erzeugen (Matching Fahrt↔Termin, Kosten je Zeile) | Assistenz | Claude-Skill → Excel | ⚠ **S5a** falsche Vorlage: ältere gespeicherte Excel statt zuletzt bearbeiteter → Vormonate weichen ab |
| 5 | Unklare Fälle prüfen | Assistenz | Excel | ⚠ **S5b** falsche Zuordnungen, erst bei erneuter Prüfung entdeckt · ✔ **S3 gelöst**: Rückfragen nur noch ca. 15 Min./Monat |
| 6 | Fehlende Zeiten / Zusatzkosten nachtragen | Assistenz | Excel | (S1) |
| 7 | Zuordnungstabellen pflegen | Assistenz | Excel | – |
| 8 | Durchsicht + Freigabe | GF | Excel/Mail | ⚠ **S5c** unübersichtlich, GF unsicher ob es stimmt · ✔ **S4 gelöst**: 15 Min. |
| 9 | Versand an Partnerfirma / Abrechnung | Assistenz | Mail | bis ca. 5. des Folgemonats |

Fazit Ist-Kette: Der Skill hat das **Tempo** gelöst (S2, S3, S4, Kurzformen). Offen ist die **Genauigkeit** (S5a–c) und Restarbeit bei fehlenden Terminen (S1).

Swimlane (Kurzform):
```
GF/Berater : [1 Termin S1] [2 Fahrt] .................................. [8 Freigabe S5c]
Assistenz  : .............. [3 Export] [4 Bericht S5a] [5 Prüfen S5b] [6 Nachtragen S1] [7 Pflege] ... [9 Versand]
Partnerfirma:                                                                                          [empfängt]
```

## Zahl zum Prozess
- Takt: 12 Berichte/Jahr + Jahresbericht.
- Aufwand je Bericht **vorher (manuell)**: ca. 16 h (Schätzung Nutzerin; gerechnet vorsichtig mit **12 h**)
- **heute (mit Skill)**: max. 1 h, davon ca. 15 Min. Rückfragen/Nachtragen · Freigabe GF: 15 Min.
- Versand: meist bis zum 5. des Folgemonats.
