# Matching-Logik & Sonderkalkulationen

> **Version 6 (2026-11):**
> - Das Matching wählt weiterhin den zeitlich nächsten Termin. **Neu:** Liegen mehrere VERSCHIEDENE Projekte im
>   Fenster oder ist der Treffer ein mehrtägiger Block eines normalen Projekts, wird die Fahrt gelb markiert
>   und kommt auf die Pruefliste (`Zuordnung_Grund` nennt die anderen Projekte). Die Wahl selbst bleibt.
> - **Reihenfolge der wirksamen Zuordnung** (Python `apply_partner_zuordnung()` und Excel-Formel identisch):
>   1. Manuelle Korrektur → 2. Partner = „Unberücksichtigt“ (gewinnt, Nutzerin 2026-11-04) → 3. Kalender-Match,
>   sofern kein ignoriertes Projekt → 4. Partner → Projekt → 5. nicht zugeordnet.
>   Fahrten zu „Unberücksichtigt“ werden nicht mehr gelöscht, sondern bleiben mit leerem Projekt sichtbar.
> - `Nicht_zugeordnete_Fahrten` gibt es nicht mehr – offene Fälle über `Rohdaten_Fahrten`, Spalte Herkunft.
> - **Niedermaier – nur markiert, nicht geändert:** (a) Ein Kurztermin (< 20 h) zählt als Block mit 0 Tagen,
>   löst aber die Anfahrtspauschale der Kalenderwoche aus. (b) Die Tage werden mit `round(Dauer/24 h)` gezählt
>   (Mo 08:00–Do 16:00 = 3 statt 4 Tage). Beide Fälle sind gelb + Pruefliste; die Regel klärt die Nutzerin
>   mit dem Kunden, erst dann `calc_tagessatz_block_kosten()` ändern.


## Fahrten ↔ Kalendertermine

### Matching-Fenster

Eine Fahrt gilt als einem Projekt zugeordnet, wenn ihr Start innerhalb von
`[Termin-Start − 36h, Termin-Ende + 4h]` liegt. Bei mehreren passenden Terminen gewinnt
der zeitlich nächstgelegene (kleinster Abstand zwischen Fahrt-Start und Termin-Start).

**Warum 36h vor dem Termin?** Deckt den Fall ab, dass am Vorabend zum Kunden angereist,
vor Ort übernachtet und erst am nächsten Morgen der eigentliche Termin wahrgenommen wird.
Eine Anreise am Vortag gegen Mittag/Abend + Übernachtung + Termin am Folgetag früh liegt
damit noch im Fenster.

**Warum nur 4h danach?** Rückfahrten im Anschluss an den Termin sollen noch erfasst werden,
ohne dass völlig unabhängige spätere Fahrten fälschlich demselben Projekt zugerechnet werden.

### Wichtige Nebenbedingung: ignorierte Projekte bleiben "echte" Matching-Kandidaten

Kalendereinträge, die in `projektname_erkennung.ignorieren` stehen (z.B. Erstgespräche mit
neuen, noch nicht bestätigten Kontakten), werden beim Extrahieren NICHT auf `Projekt=None`
gesetzt — sie behalten ihren erkannten Namen. Sie werden erst auf der Übersichts-Ebene
ausgeblendet. Grund: Würden sie schon beim Parsen zu `None`, könnten in ihrer zeitlichen Nähe
liegende Fahrten fälschlich dem nächstgelegenen ECHTEN Projekt zugeschlagen werden (getestet
und beobachtet — führte zu falsch zu hohen km-Werten bei benachbarten Projekten). Die Fahrten
zu ignorierten Terminen tauchen dadurch einfach nicht in der Übersicht auf, aber auch nicht
fälschlich bei einem anderen Projekt.

### Was NICHT automatisch gematcht wird

Fahrten außerhalb des Fensters (z.B. rein lokale Botengänge ohne Projektbezug) bleiben
unzugeordnet und landen im Sheet "Nicht_zugeordnete_Fahrten" — bewusst sichtbar für die
manuelle Prüfung, nicht stillschweigend verworfen. Ein hoher Anteil unzugeordneter Fahrten
ist normal (im ersten Testlauf ca. 63 %) und meist unproblematisch (interne/administrative
Fahrten ohne Projektbezug), sollte der Nutzerin aber trotzdem kurz gezeigt werden.

## Mehrtägige Kalenderblöcke — Vorsicht bei der Stundenberechnung

**Wichtige Lektion aus dem ersten Testlauf:** Ein Kalendereintrag kann mehrere Tage
überspannen (z.B. "Spedition Niedermaier", 5.–8.5., ganztägig), OHNE dass das die tatsächliche
Arbeitszeit widerspiegelt — das war ein reiner Reservierungs-/Blocker-Eintrag. Würde man
`Ende − Start` wörtlich als Arbeitsstunden verrechnen, kämen absurde Werte heraus (im Testlauf:
816 Std. für einen einzigen Bereich).

**Regel:** Jeder Kalendereintrag mit einer Dauer > 20 Stunden wird in `Rohdaten_Kalender` als
`Mehrtaegig_Blocker` markiert (gelb hinterlegt) und in der Standard-SUMIFS-Stundenformel der
Übersicht automatisch ausgeschlossen (Kriterium: Spalte "Mehrtaegig_Blocker" ist leer).
Für Projekte, bei denen solche Blöcke die NORMALE Arbeitsweise sind (wie Niedermaier), muss
stattdessen eine Sonderkalkulation angelegt werden (siehe unten) — sonst zeigt die Übersicht
für dieses Projekt dauerhaft 0 Stunden bei den normalen Mitarbeiter-Spalten, was korrekt, aber
ohne Zusatzerklärung verwirrend ist.

## Sonderkalkulation "Tagessatz-Block" (aktuell: Spedition Niedermaier)

Manche Projekte werden nicht über Stundensatz + km-Satz abgerechnet, sondern über feste
Tagessätze/Pauschalen pro mehrtägigem Einsatzblock. Struktur in der Config
(`sonderkalkulationen.<Projektname>`):

```json
{
  "typ": "tagessatz_block",
  "tagessatz_vor_ort_eur": 1750,
  "an_abfahrt_pauschale_eur": 825,
  "uebernachtung_pro_nacht_eur": 150,
  "naechte_regel": "...",
  "fahrten_kostentechnisch_ausschliessen": true,
  "fahrten_km_zeit_informativ_zeigen": true
}
```

### Berechnungslogik je Kalenderblock (ein Kalendereintrag = ein Buchungszeitraum)

1. `Tage` = Blocklänge in vollen Kalendertagen (`round((Ende − Start) / 24h)`)
2. `Nächte` = `Tage` (Annahme: durchgehende Übernachtung vor Ort während des gesamten
   Blocks — mit der Nutzerin am 2026-07-15 für das Niedermaier-Projekt bestätigt; bei einem
   NEUEN Tagessatz-Projekt diese Annahme jedes Mal explizit gegenprüfen, da andere Kunden
   andere Konventionen haben können)
3. `Kosten_Block = Tage × Tagessatz + Pauschale (einmal pro Block) + Nächte × Übernachtungssatz`

### Fahrten bei Tagessatz-Projekten

Wenn `fahrten_kostentechnisch_ausschliessen: true`: die per Zeitfenster zugeordneten Fahrten
fließen NICHT in die Kosten ein (sie sind im Tagessatz enthalten), erscheinen aber weiterhin
informativ in der Übersicht (Spalten "Distanz gesamt (km)" und "Fahrdauer gesamt (h,
informativ)") sowie vollständig in "Rohdaten_Fahrten" — Kostenspalte für diese Fahrten wird
dort bewusst nicht separat ausgewiesen, die Gesamtkosten-Spalte des Projekts entspricht rein
der Tagessatz-Kalkulation.

### Noch nicht automatisiert (Stand 2026-07-15)

Der abweichende km-Satz für Fahrten außerhalb des Standorts (bei Niedermaier: 1,20 €/km für
Termine außerhalb von 94405 Landau a.d. Isar) ist in der Config dokumentiert, aber noch NICHT
in `report_lib.py` implementiert (würde einen Adressabgleich Start-/Zieladresse vs. Standort-PLZ
erfordern). Falls das relevant wird: zuerst mit der Nutzerin klären, wie der Abgleich robust
funktionieren soll (z.B. PLZ-Präfix-Vergleich), dann `calc_tagessatz_block_kosten()` erweitern.

### Vorlage für künftige, ähnliche Sonderfälle

Für ein neues Tagessatz-Projekt: einfach einen weiteren Eintrag unter `sonderkalkulationen`
in der Config mit `"typ": "tagessatz_block"` und den passenden Sätzen anlegen —
`build_excel_workbook()` erstellt automatisch ein eigenes Kalkulations-Sheet dafür und bindet
es in die Übersicht ein, ohne Codeänderung.
