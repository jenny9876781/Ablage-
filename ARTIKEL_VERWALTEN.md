# Artikel pflegen — was wo geändert wird

Kurz vorweg, weil das deine eigentliche Frage war: **Ja.** Du änderst alles in der
Artikelstammliste. Ich erzeuge daraus eine neue Importdatei, du lädst sie in WordPress hoch,
und der Katalog zieht nach — Artikel verschwinden, Preise ändern sich, Fotos wechseln.
Automatisch passiert es nicht, es braucht diesen einen Upload. Das ist Absicht: so
entscheidest du, wann eine Änderung nach außen sichtbar wird, und kannst vorher in Ruhe
zehn Sachen ändern statt jede einzeln.

---

## Der Ablauf, immer derselbe

1. Du änderst etwas in `01_Artikelstamm_kikripp.xlsx` (in OneDrive, direkt in der Datei).
2. Du schickst mir die Datei mit dem Stichwort **sale4kids**.
3. Ich lese sie ein, erzeuge alles neu und schicke dir `katalog_import.json` zurück.
4. Du lädst die Datei unter **Artikelkatalog → Artikel importieren** hoch.
5. WordPress meldet, was neu ist, was aktualisiert wurde und was aus dem Katalog geflogen ist.

Der Import ist gutmütig: du kannst ihn beliebig oft laufen lassen. Bestehende Artikel werden
aktualisiert, neue kommen dazu, **Reservierungen bleiben immer erhalten**.

---

## Artikel aus dem Katalog nehmen

Es gibt zwei Fälle, und sie brauchen unterschiedliche Spalten.

### Fall 1: Der Artikel existiert nicht oder war ein Fehler

Spalte **`Aktiv`** auf `entfällt` setzen.

Der Artikel verschwindet dann aus dem Webkatalog, aus dem Klinik-Angebot und aus allen
Summen. In der Artikelstammliste bleibt die Zeile stehen — grau hinterlegt, damit man sieht,
dass es sie mal gab. Die Artikelnummer wird nie wieder vergeben.

### Fall 2: Der Artikel wird doch nicht verkauft, bleibt aber im Bestand

Spalte **`Im_Katalog`** auf `nein` setzen.

Er verschwindet aus dem Webkatalog, zählt aber weiter zum Bestand und taucht in der
Verkaufsübersicht auf. Nimm das für Sachen, die ihr behaltet, verschenkt oder erst später
anbietet. Später wieder auf `ja` setzen, und er ist zurück.

### Und wenn du die Zeile einfach löschst?

Dann fängt das die Rückeinlese-Logik ab: gelöschte Zeilen werden nicht wirklich entfernt,
sondern auf `Aktiv = entfällt` gesetzt — Fall 1 also. Und falls doch mal ein Artikel gar
nicht mehr in der Importdatei steht, nimmt ihn WordPress beim nächsten Import von selbst
aus dem Katalog und sagt dir in der Meldung, welche Nummern das waren.

**Gelöscht wird nie etwas.** Auch nicht in WordPress. An einem Artikel können Reservierungen
und Verkäufe hängen, und die brauchst du für die Buchhaltung.

---

## Was passiert mit dem Foto?

Nichts, und das ist gut so. Das Bild bleibt in der Mediathek liegen, wird aber nirgends mehr
angezeigt. Du musst es nicht löschen.

Löschen solltest du es nur, wenn darauf etwas ist, das nicht online sein darf. Dann aber
vorher prüfen, ob ein anderer Artikel dasselbe Foto benutzt — das kommt vor, zum Beispiel
zeigt `F-002` gleich zwei Positionen. Sag mir in dem Fall Bescheid, ich sehe nach.

---

## Preise ändern

Spalte `Preis_netto` in der Artikelstammliste, immer **netto**. Den Bruttopreis rechnet der
Katalog selbst und zeigt ihn groß an, netto steht klein darunter.

Beim nächsten Import gilt der neue Preis für alle, die ab dann reservieren. **Schon
bestehende Reservierungen behalten ihren alten Preis** — sonst würde sich ein Vorgang
rückwirkend ändern, den jemand längst bestätigt bekommen hat. Das ist geprüft.

---

## Mengen ändern

Spalte `Menge`. Vorsicht beim Verkleinern: Steht ein Artikel auf 10 Stück, sind 6 reserviert,
und du setzt auf 3 — dann ist mehr vergeben als vorhanden. Der Katalog zeigt dann 0 frei und
niemand kann mehr reservieren, aber die sechs bestehenden Reservierungen bleiben bestehen.
Du müsstest dich dann bei den Leuten melden. Also beim Verkleinern lieber vorher unter
**Artikelkatalog → Reservierungen** nachsehen.

---

## Neue Artikel dazunehmen

Genau wie am Anfang: fotografieren (siehe `FOTOGRAFIEREN.md`), Fotos mit dem Stichwort
**sale4kids** hochladen. Ich lege die Artikel an, vergebe die nächsten freien Nummern und
erzeuge alles neu. Du bekommst zurück:

- eine neue `katalog_import.json` → hochladen unter *Artikel importieren*
- die neuen Fotos → in die **Mediathek** hochladen, **vor** dem Import

Die Reihenfolge ist wichtig: Erst die Fotos, dann der Import. Sonst findet der Import die
Bilder noch nicht und meldet „X Artikel ohne gefundenes Foto". Schlimm ist das nicht — du
lädst die Fotos nach und startest den Import einfach noch einmal.

---

## Verkäufe zurück in die Buchhaltung

Alle ein, zwei Wochen: **Artikelkatalog → Reservierungen → Alle Reservierungen als CSV
exportieren**. Die Datei schickst du mir mit **sale4kids**. Ich trage in den Artikelstamm
ein, was zu welchem Preis wann verkauft wurde, und erzeuge Verkaufsübersicht, DATEV-Liste
und Kassenbuch neu.

Was **du** danach noch einträgst, sobald die Rechnung aus DATEV vorliegt:

| Spalte | Inhalt |
|---|---|
| `Käufer` | Name aus der Benachrichtigungsmail — der Katalog speichert ihn nicht |
| `Rechnungsnr` | Nummer aus DATEV |
| `Zahlung` | `offen` oder `bezahlt` |
| `Zahlart` | `bar` oder `Überweisung` |

Den Käufer findest du über den Suchbegriff, den die Verwaltung bei jedem Vorgang anzeigt —
zum Beispiel `[Kikripp GmbH] Neue Reservierung #14`. Damit im Postfach suchen.

Bei Barzahlung muss der Betrag zusätzlich **am selben Tag** ins Blatt „Kasse". Der Vermerk
„bar bezahlt" auf der Rechnung reicht bei einer GmbH nicht.

Die Spalte `Status` steht danach auf `verkauft`, wenn alles weg ist, oder auf `teilverkauft`,
wenn von zehn Stühlen erst vier raus sind. Beide Zustände zählen in der Übersicht bei
„Rechnungen noch zu schreiben" mit.

---

## Im Katalog selbst zu erledigen

Das machst du direkt in WordPress, nicht in der Excel:

| Wann | Wo | Was |
|---|---|---|
| Ware ist abgeholt und bezahlt | Artikelkatalog → Reservierungen | auf **bezahlt** setzen — der Artikel verschwindet aus dem Katalog |
| Jemand springt ab | dieselbe Seite | **stornieren** — die Ware ist sofort wieder frei |
| Jemand braucht länger | dieselbe Seite | **Frist verlängern** — sieben Tage obendrauf |
| Vorschauphase vorbei | Einstellungen | Haken *Vorschaubetrieb* raus, dann Testreservierungen löschen |
| Hinweisband soll weg | Einstellungen | Feld *Hinweisband* leeren |

Abgelaufene Reservierungen geben die Ware **von selbst** wieder frei. Da musst du nichts tun.

---

## Zwei Regeln, die du nicht brechen solltest

**Reserviert wird nur im Webkatalog.** Trag Reservierungen nie zusätzlich von Hand in die
Excel ein. Der Katalog weiß dann nichts davon und vergibt denselben Schrank ein zweites Mal.
Wenn jemand telefonisch reserviert, leg ihm die Reservierung selbst im Katalog an — du hast
ja das Passwort.

**Die Benachrichtigungsmails sind dein Kontaktarchiv.** Der Katalog speichert keine Namen,
Mailadressen oder Telefonnummern — die stehen ausschließlich in den Mails an
jennyp@kikripp.de. Leg dir dafür einen Ordner an und lösche dort nichts.

**Artikelnummern werden nie wiederverwendet.** Auch nicht die von entfallenen Positionen.
Die Etiketten kleben physisch an den Sachen; eine zweitvergebene Nummer führt garantiert
irgendwann dazu, dass jemand das Falsche einlädt.
