# Auftrag: Skill „projekt-zeit-kosten-report“ prüfen und absichern

> **So nutzt du diese Datei:** Öffne einen neuen Chat mit Claude Code und schreib:
> „Lies `ki-wiki/AUFTRAG_SKILL_PRUEFUNG.md` im Repo Ablage- und arbeite den Auftrag ab.“
> Wenn das Repo dort nicht verfügbar ist, kopier den Inhalt ab der nächsten Überschrift in den Chat.

---

## 1. Worum es geht

Ich bin Assistenz der Geschäftsführung einer kleinen Beratungsfirma. Jeden Monat erstelle ich mit dem
Claude-Skill **`projekt-zeit-kosten-report`** einen Excel-Bericht: Outlook-Kalenderexporte und
Fahrtenbuch-Export (Autolog) werden zu Stunden, km und Kosten je Projekt zusammengeführt
(Mehrjahres-Auswertung, Filter-Dashboard, monatliche Fortführung).

Der Skill spart viel Zeit (früher 12–16 h, heute ca. 1 h). **Aber die Geschäftsführung vertraut dem
Bericht nicht**, weil Fehler auftreten. Ziel ist: **genauer, nicht schneller.**

Das ist Welle 1 (Einsatzstellen E1 und E2) meines Praxisprojekts der KI-Schulung. Geplanter Aufwand: **ca. 8 Stunden.**

## 2. Wo der Skill liegt

- In Claude-Code-Sitzungen meist unter `~/.claude/skills/synced/<…>/projekt-zeit-kosten-report/`
  mit `SKILL.md`, `config/projekt_konfiguration.json`, `references/*.md` und `scripts/report_lib.py`.
- Findest du ihn nicht: Sag es mir. Ich lade ihn dann als ZIP hoch (claude.ai → Einstellungen → Skills).
- **Arbeite an einer Kopie** (z. B. `skills/projekt-zeit-kosten-report/` im Repo, auf einem eigenen Branch),
  nie direkt am Original.

## 3. Die bekannten Fehler (bitte Ursache finden, nicht nur Symptom)

| Nr. | Fehler | Was ich beobachtet habe |
|---|---|---|
| S1 | **Falsche Vorlage** | Bei der monatlichen Fortführung wurde nicht meine zuletzt bearbeitete Excel als Grundlage genommen, sondern eine ältere gespeicherte Version. Dadurch weichen Vormonate ab. |
| S2 | **Falsche Zuordnungen** | Termine oder Fahrten landeten teils beim falschen Projekt und wurden erst bei erneuter Prüfung korrigiert. |
| S3 | **Unübersichtlich** | Der Bericht hat zu viele Reiter. Die GF sieht bei der Freigabe nicht schnell, ob er stimmt. |
| – | **Auslastung je Mitarbeiter** | Die Auswertung „Auslastung je Mitarbeiter gegenüber Soll“ soll **raus** (Datenschutz, GF braucht sie nicht). Stunden je Mitarbeiter **und Projekt** bleiben, weil die Kostenrechnung sie braucht. |

## 4. Was du tun sollst – in dieser Reihenfolge

**Schritt 1 – Prüfen, nichts ändern.**
Lies den Skill komplett (SKILL.md, Config, References, `report_lib.py`). Schreib mir dann einen kurzen Befund:
- die wahrscheinliche Ursache für S1 und S2 (mit Stelle im Code bzw. in der Anleitung)
- weitere Schwachstellen, die dir auffallen (Logik, Formeln, Reihenfolge, fehlende Tests)
- deinen Plan für Schritt 2, mit Aufwandsschätzung

**Warte auf mein Okay**, bevor du etwas änderst.

**Schritt 2 – Absichern (nach meinem Okay).**
1. **Versionsregel (gegen S1):** Die Fortführung darf nur von der zuletzt freigegebenen Datei ausgehen.
   Vorschlag: Version und Stand im Dateinamen und im Parameter-Reiter. Ist die gelieferte Datei älter als
   der letzte bekannte Stand, wird gestoppt und nachgefragt, statt still weiterzurechnen.
2. **Prüfblatt „Abgleich Vormonate“ (gegen S1):** Neuer Reiter, der Summen je Monat und Projekt der alten
   und der neuen Version vergleicht. Abweichungen werden rot markiert und begründet, oben steht ein
   klares Ergebnis: „Vormonate unverändert ✔“ oder „X Abweichungen“.
3. **Spalte „Zuordnung_Grund“ (gegen S2):** Jede Kalender- und Fahrtzeile bekommt eine Begründung
   (z. B. „Projektname im Betreff“, „Alias Sand → Sandformation“, „Partner-Zuordnung“,
   „Zeitfenster-Match mit Termin“). Unsichere Fälle werden **gelb markiert** statt still zugeordnet
   und erscheinen auf einer Prüfliste.
4. **Auslastung je Mitarbeiter entfernen**, alles andere unverändert lassen.
5. **Optional, nur wenn Zeit bleibt (E3):** Eine Übersichtsseite für die GF ganz vorne:
   5 Kennzahlen, Ergebnis des Prüfblatts und „Was hat sich zum Vormonat geändert?“. Vorher mit mir abstimmen.
6. SKILL.md und References an die Änderungen anpassen. Die Regeln aus SKILL.md gelten weiter:
   - SUMIFS statt SUMPRODUCT
   - Kosten pro Zeile
   - Reihenfolge Wochenpauschale/Matching/Partner-Zuordnung
   - nichts raten

**Schritt 3 – Testen.**
- Automatische Tests mit **erfundenen Testdaten** für alle Fälle oben, also falsche Vorlage, Alias, unsichere
  Zuordnung und Dubletten bei der Fortführung.
- Danach ein Testlauf mit echten Daten (Oktober- und Novemberbericht). **Vorher fragen**, denn echte Kalender- und
  Fahrtdaten sind personenbezogen. Das machen wir erst mit dem Firmen-Account (Claude Team mit AVV) oder
  mit pseudonymisierten Daten. Das entscheide ich.
- Excel-Formeln neu berechnen und auf Fehler prüfen (0 Fehler).

## 5. Was ich am Ende von dir erwarte

1. **Neue Skill-Version als ZIP**, die ich in claude.ai hochladen kann, mit erhöhter Versionsnummer.
2. **Änderungsprotokoll als Word-Datei** (1–2 Seiten): was geändert wurde, warum, und welcher Fehler (S1/S2/S3) damit behoben ist.
3. **Testprotokoll:** welche Tests gelaufen sind und mit welchem Ergebnis.
4. **Kurzanleitung als Word-Datei** (1 Seite) für meine Kollegin als Vertretung: welche Dateien sie hochlädt, was sie prüft und wann sie stoppt.
5. **Tatsächlicher Zeitaufwand** in Stunden. Den brauche ich für Baustein 4 meines Praxisprojekts (geplant: 8 h).

## 6. Abnahmekriterien

- Eine ältere Vorlage wird **erkannt und gestoppt**, nicht still verwendet.
- Das Prüfblatt zeigt bei unveränderten Vormonaten „unverändert ✔“ und bei jeder Abweichung die betroffene Zeile.
- Jede Zuordnung hat einen Grund. Unsichere Fälle sind gelb und stehen auf der Prüfliste.
- Die Auslastung je Mitarbeiter ist weg, die Summen je Projekt sind **identisch** zur bisherigen Version (Regressionstest).
- 0 Formelfehler in Excel.

## 7. So arbeite ich gern

- Deutsch, kurze Antworten, Fragen **gebündelt** stellen.
- Erst Befund und Plan, dann mein Okay, dann umsetzen. Nichts ohne Rückfrage löschen.
- Nicht raten: Unklares transparent markieren.
- **Widersprich mir**, wenn etwas schiefläuft oder ich etwas Unsinniges will.
- Ergebnisse als Word oder Excel, nicht als .md oder .pdf.

## 8. Was ich mitbringe

- die **zuletzt freigegebene Ausgabe-Excel** (Stand Oktober 2026)
- falls vorhanden die **fehlerhafte Version**, in der Vormonate abwichen
- die **Rohdaten** des neuen Monats: Kalenderexporte je Postfach und Autolog-CSV
- meine Notizen, welche Zuordnungen falsch waren
