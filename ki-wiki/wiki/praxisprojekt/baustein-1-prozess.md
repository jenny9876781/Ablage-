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

## Ist-Kette (Rollen statt Namen) – Schwachstellen = ⚠
| # | Schritt | Rolle | Werkzeug | Wartezeit / Problem |
|---|---|---|---|---|
| 1 | Termin mit „Projektname“ im Betreff eintragen | GF, Berater | Outlook | ⚠ **S1** Termine fehlen oder Projekt uneinheitlich benannt (Kurzformen) |
| 2 | Fahrt wird aufgezeichnet | GF, Berater | Fahrtenbuch-App | ⚠ **S2** Fahrer falsch zugeordnet, Kennzeichen uneinheitlich |
| 3 | Monatsende: Kalender je Postfach + Fahrtenbuch exportieren | Assistenz | Outlook, App | wartet ggf. auf Zugriff/Export |
| 4 | Bericht erzeugen (Matching Fahrt↔Termin, Kosten je Zeile) | Assistenz | Claude-Skill → Excel | – |
| 5 | Unklare Fälle prüfen (unbekannte Projekte, nicht zugeordnete Fahrten, Plausibilität) | Assistenz | Excel | ⚠ **S3** Rückfrage-Schleife: Antworten kommen spät |
| 6 | Fehlende Zeiten / Zusatzkosten nachtragen | Assistenz nach Info von GF/Berater | Excel | ⚠ S3 (gleiche Schleife), Gefahr Doppelzählung |
| 7 | Zuordnungstabellen pflegen (Partner → Projekt) | Assistenz | Excel | – |
| 8 | Freigabe | GF | Excel/Mail | ⚠ **S4** Freigabe-Stau, GF unterwegs |
| 9 | Bericht an Partnerfirma / Abrechnung | Assistenz | Mail | – |

Swimlane (Kurzform):
```
GF/Berater : [1 Termin] [2 Fahrt] ......(Antwort S3)...... [8 Freigabe S4]
Assistenz  : ............ [3 Export] [4 Bericht] [5 Prüfen S3] [6 Nachtragen] [7 Pflege] ........ [9 Versand]
Partnerfirma:                                                                                    [empfängt]
```

## Zahl zum Prozess
- Takt: 12 Berichte/Jahr + Jahresbericht.
- Aufwand je Bericht **vorher (manuell)**: [offen] h · **heute (mit Skill)**: [offen] h · davon Rückfragen: [offen] h
- Anteil Fahrten ohne Projektzuordnung je Monat: [offen] % · Zahl Rückfragen je Monat: [offen]
