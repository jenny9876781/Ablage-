# Datenquellen & Formate

> **Version 6 (2026-11):**
> - Projektnamen werden auch in **typografischen Anführungszeichen** erkannt („Koko“, “Koko”, «Koko») –
>   Outlook setzt diese per Autokorrektur.
> - Abweichende Schreibweise eines bekannten Namens/Alias (z.B. `"sand"`) wird zugeordnet, aber gelb markiert
>   (früher entstand ein Phantomprojekt „sand“). Neue Aliase nach Bestätigung in die Config eintragen.
> - Ein bekannter Projektname OHNE Anführungszeichen (ganzes Wort) wird **nicht** zugeordnet, sondern nur als
>   „möglicher Bezug“ gemeldet. Ausnahmen (z.B. Monatsname „Juli“): `projektname_erkennung.keine_hinweise_fuer`.
> - Der Outlook-Export enthält immer den ganzen Kalender. Bei der Fortführung zählen deshalb nur Termine NACH
>   „Datenstand bis“ der freigegebenen Vorlage; ältere Termine, die in der Vorlage fehlen, kommen auf die Pruefliste.
> - Gleicher Termin (Mitarbeiter, Start, Ende, Betreff) in zwei Kalendern derselben Person → zweite Zeile
>   gelb als „mögliche Dublette“; identische Zeilen aus demselben Kalender (doppelt exportiert) werden entfernt.
>   Identische Autolog-Zeilen (überlappende Exporte) werden ebenfalls entfernt.


## 1. Outlook-Kalenderexport (je Postfach/Mitarbeiter eine CSV)

### Export-Anleitung (an die Nutzerin weitergeben, falls sie fragt oder ein Export
fehlerhaft/unvollständig aussieht)

1. Outlook Desktop-App: Datei → Öffnen & Exportieren → Importieren/Exportieren
2. "In Datei exportieren" → weiter
3. "Kommagetrennte Werte" (CSV) auswählen → weiter
4. Gewünschten Kalenderordner auswählen (bei freigegebenen Kalendern vorher unter
   "Kalender hinzufügen" in die eigene Ansicht holen, dann erscheint er in dieser Liste)
5. Zieldatei/-ordner wählen
6. Bei "Benutzerdefinierte Felder zuordnen" NICHTS ändern — Standardzuordnung reicht
7. Fertig stellen

Wichtig: Der klassische Export filtert NICHT nach Datum — er exportiert immer den
gesamten Kalender. Das ist gewollt: lieber zu viel exportieren und hier zeitlich
filtern lassen, als am Rand Termine zu verlieren.

### Erwartete Spalten (Standard-Outlook-CSV, viele weitere Spalten sind vorhanden
und werden ignoriert — das ist kein Fehler)

| Spalte | Verwendung |
|---|---|
| `Betreff` | Enthält Projektname in "Anführungszeichen" + Aufgabe, z.B. `"Koko" Dokumentenerstellung NBO` |
| `Beginnt am` / `Beginnt um` | Datum (`d.m.yyyy`) + Uhrzeit (`H:M:S`), zusammen als Start geparst |
| `Endet am` / `Endet um` | analog für Ende |
| `Ort` | Nur informativ (Unterscheidung Vor-Ort- vs. Teams-Termin), fließt nicht direkt in die Kalkulation ein |

Alle anderen Spalten (Teilnehmer, Teams-Link, Beschreibung, Kategorien, ...) werden
nicht ausgewertet.

### Bekannte Eigenheiten

- **Projektname ohne Anführungszeichen:** Einzelne Mitarbeiter/Kalender (bisher: Marius'
  interner Kalender) schreiben manche feste Projektnamen ohne Anführungszeichen
  (z.B. "Spedition Niedermaier"). Diese stehen explizit in der Config unter
  `projektname_erkennung.feste_namen_ohne_anfuehrungszeichen` und werden per Volltextsuche
  erkannt. Neue Fälle dieser Art: in der Config ergänzen, nicht Betreff für Betreff neu raten.
- **Schreibvarianten/Tippfehler:** z.B. `"Koko "Dokumentenerstellung` (Leerzeichen vor der
  zweiten Anführung) oder Tippfehler in der Aufgabenbeschreibung (nicht im Projektnamen selbst)
  — werden durch Whitespace-Normalisierung abgefangen. Bei neuen, bisher unbekannten Varianten
  kurz mit der Nutzerin abgleichen, ob es sich wirklich um dasselbe Projekt handelt.
- **Ein-off-Termine, die wie Projekte aussehen** (z.B. Erstgespräche mit neuen Kontakten in
  Anführungszeichen): NICHT automatisch als neues Projekt in die Übersicht aufnehmen. Der
  Nutzerin die neuen Namen zeigen und explizit fragen (siehe `projektname_erkennung.ignorieren`
  in der Config für bereits geklärte Fälle).
- **Mehrere Kalender pro Mitarbeiter:** Manche Mitarbeiter haben getrennte Kalender für
  TransCare und intern (Neininger). Diese immer BEIDE einlesen und mit `kalendertyp`
  unterscheiden (nur zur Transparenz, hat aktuell keine Auswirkung auf die Kalkulation außer
  bei den Sonderkalkulationen).
- **Ein gemeinsamer Kalender für beide Firmen:** mindestens ein Mitarbeiter nutzt EINEN
  Kalender für TransCare- und Neininger-Projekte gemeinsam — Firmenzuordnung ergibt sich dann
  rein aus dem Projektnamen (Projektstammliste in der Config), nicht aus dem Kalender selbst.

## 2. Autolog-Fahrtenbuch-Export

CSV, Semikolon-getrennt, UTF-8 mit BOM (`encoding='utf-8-sig'` beim Einlesen verwenden).

| Spalte | Verwendung |
|---|---|
| `Kennzeichen` | Zur Filterung auf das relevante Fahrzeug — Zuordnung zu Fahrer/in kommt aus der Config, NICHT aus `Fahrer` |
| `Start` / `Ende` | Format `dd.mm.yy HH:MM` — ACHTUNG: bei manchen `Fahrtart=Privat`-Zeilen fehlt die Uhrzeit (nur Datum). Deshalb immer ERST nach `Fahrtart` filtern, DANN Datum parsen (siehe `report_lib.load_autolog_csv`) |
| `Distanz (km)` | Nach `pd.to_numeric(..., errors='coerce')` konvertieren — wird sonst als String eingelesen und ergibt beim Summieren Unsinn |
| `Fahrtart` | Nur `Geschäftlich` fließt in die Projektauswertung ein |
| `Fahrer` | **Nicht vertrauenswürdig** — im Bestand mind. ein Fall, wo ein Fahrzeug fälschlich auf die falsche Person ausgestellt war. Immer die Config-Zuordnung `fahrzeug_fahrer_zuordnung` verwenden |
| `Partner`, `Zweck` | Nur informativ/zur Plausibilisierung, keine Projektzuordnung daraus ableiten |

### Mehrere Fahrzeuge/Fahrer

Der Gesamt-Autolog-Export kann mehrere Kennzeichen/Fahrer in einer Datei enthalten. Immer
explizit klären, welche Kennzeichen für den aktuellen Bericht relevant sind (Config-Eintrag
`fahrzeug_fahrer_zuordnung` kann auch "IGNORIEREN" als Wert enthalten — solche Kennzeichen
komplett auslassen).
