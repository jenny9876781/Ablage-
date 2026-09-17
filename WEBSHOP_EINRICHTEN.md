# Webkatalog einrichten

Der Katalog läuft auf **www.schlabberschnuten.com** — dort hast du Super-Admin-Rechte und
kannst Plugins hochladen. Auf **www.kikripp.de** steht nur ein Knopf, der dorthin führt.
Verkäuferin ist und bleibt die Kikripp GmbH; die Hundeschule stellt ausschließlich den
Speicherplatz. Das steht auch so im Katalog und in der Aktennotiz (`U1`).

Du brauchst drei Dateien aus dem Ordner `ausgabe`: **kikripp-katalog.zip** (das Plugin),
**kikripp-fotos.zip** (die Fotos) und **katalog_import.json** (die Artikel). Rechne mit einer
knappen Stunde, das meiste davon ist Warten beim Hochladen der Fotos.

> **Wichtig zum Verständnis:** Der Katalog speichert auf der Hundeschul-Seite **keine Namen,
> keine Mailadressen, keine Telefonnummern**. Die gehen ausschließlich per Mail an
> `jennyp@kikripp.de` und werden danach sofort aus der Datenbank gelöscht. Diese Mails sind
> damit dein einziges Kontaktarchiv — **bitte nicht löschen.** Leg dir einen Ordner an.

## 1. Plugin installieren

Melde dich auf **www.schlabberschnuten.com/wp-admin** an und geh auf
**Plugins → Installieren → Plugin hochladen**. Wähle `kikripp-katalog.zip`, klick auf
*Jetzt installieren* und danach auf *Plugin aktivieren*. In der linken Leiste erscheint der
Menüpunkt **Artikelkatalog**.

## 2. Fotos in die Mediathek

Entpacke `kikripp-fotos.zip` auf deinem Rechner – du bekommst einen Ordner `fotos` mit
111 Bildern (F-001.jpg bis F-112.jpg). Geh in WordPress auf **Medien → Datei hinzufügen**
und zieh alle Bilder auf einmal in das Feld. Das dauert ein paar Minuten; lass das
Browserfenster offen, bis alle durch sind.

Wichtig: Die Dateinamen dürfen sich nicht ändern. Das Plugin findet die Fotos über den
Namen. Lade sie deshalb bitte nur einmal hoch – lädst du dasselbe Bild zweimal hoch,
hängt WordPress eine `-1` an und der Katalog findet es trotzdem, aber es liegt doppelt
auf dem Server.

## 3. Artikel importieren

Geh auf **Artikelkatalog → Artikel importieren**, wähle `katalog_import.json` und klick
auf Importieren. Danach steht dort, wie viele Artikel angelegt wurden und wie viele
davon kein Foto gefunden haben. Steht dort eine Zahl über null, stimmt bei diesen Fotos
etwas mit dem Dateinamen nicht.

Diesen Schritt wiederholst du jedes Mal, wenn neue Artikel dazukommen oder Preise sich
ändern: neue Datei erzeugen lassen, hochladen, fertig. Bestehende Artikel werden
aktualisiert, neue kommen dazu, und Reservierungen bleiben erhalten.

## 4. Einstellungen prüfen

Nach dem Aktivieren erscheint oben ein gelber Hinweis: es ist noch **kein Passwort vergeben**,
und ohne Passwort kommt niemand in den Katalog — auch du nicht. Das ist Absicht, damit das
Passwort nirgends in einer Datei steht.

Geh auf **Artikelkatalog → Einstellungen** und arbeite die Seite von oben nach unten durch:

| Feld | Was hineingehört |
|---|---|
| Katalog-Passwort | das vereinbarte Passwort, einmal eintragen |
| Verkäuferin (Firma) | `Kikripp GmbH` — steht so im Katalog und im Mailbetreff |
| Reservierungen melden an | `jennyp@kikripp.de` |
| Telefon | die Nummer der Kikripp GmbH |
| **Impressum** | **bitte prüfen** — die Vorgabe `https://www.kikripp.de/impressum/` ist geraten |
| **Datenschutzerklärung** | **ebenfalls prüfen** |
| Abholadresse | erscheint unter dem Katalog |
| Hinweisband | Text über dem Katalog, zum Livegang leeren |
| Reservierung gilt | 7 Tage |
| Umsatzsteuer | 19 % |
| Rechtliche Hinweise | Verkaufsbedingungen, änderbar |

Die beiden Adressen zu Impressum und Datenschutz sind die einzigen Felder, bei denen ich
raten musste — von hier aus ist kikripp.de nicht erreichbar. Öffne die Links einmal und
korrigiere sie, falls die Seiten anders heißen. **Sie müssen funktionieren**, sonst fehlt
im Katalog die Anbieterkennzeichnung.

Lass **Vorschaubetrieb** eingeschaltet, solange ihr testet. Dann werden alle eingehenden
Reservierungen als Testdaten markiert und lassen sich am Ende mit einem Klick löschen.

Und füge noch den Absatz aus **`U2_Datenschutz_Absatz.docx`** in die Datenschutzerklärung
von schlabberschnuten.com ein. Das ist der einzige Papierkram, der nötig ist.

## 5. Seite anlegen und den Knopf setzen

**Auf schlabberschnuten.com:** Geh auf **Seiten → Erstellen**, nenn die Seite
*Kikripp Artikelkatalog* und setz als einzigen Inhalt den Kurzbefehl:

    [kikripp_katalog]

Veröffentlichen. Achte darauf, dass die Adresse sprechend ist — etwa
`www.schlabberschnuten.com/kikripp-artikelkatalog`. Das beruhigt jeden, der den Link
bekommt und sich fragt, warum er auf einer Hundeschul-Seite landet.

Die Seite trägt automatisch ein „nicht indexieren" für Suchmaschinen und taucht nicht bei
Google auf.

**Der Link mit Passwort.** Hängst du `?kik=DASPASSWORT` an die Adresse, öffnet sich der Katalog
direkt — niemand muss etwas eintippen. Das Passwort verschwindet dabei sofort wieder aus der
Adresszeile. Diesen Link verschickst du an die Interessenten:

    https://www.schlabberschnuten.com/kikripp-artikelkatalog/?kik=DASPASSWORT

**Auf kikripp.de:** Dort brauchst du keine Plugin-Rechte, ein Knopf ist nur ein Link. Die
fertige Vorlage liegt in **`U3_Knopf_fuer_kikripp.docx`** (und als `.txt`, falls das Kopieren
aus Word zickt). Seite bearbeiten, Block **Custom HTML** einfügen, Baustein hineinkopieren,
die Adresse eintragen, speichern.

## 6. Einmal selbst durchtesten

Ruf den Link mit Passwort in einem privaten Browserfenster auf. Der Katalog sollte sich
**ohne Passwortabfrage** öffnen. Merk dir zwei Artikel vor und schick eine Reservierung ab.

Du solltest danach sehen:

- **Am Bildschirm** die Bestätigung mit Vorgangsnummer, Positionen, Frist und deinen
  eingetragenen Kontaktdaten. Das ist alles, was der Interessent bekommt — keine Mail.
- **In deinem Postfach** eine Mail „[Kikripp GmbH] Neue Reservierung #1". Antworten geht
  direkt: das Antwort-an steht auf den Interessenten.
- **Unter Artikelkatalog → Reservierungen** den Vorgang — **ohne Namen**, dafür mit dem
  Suchbegriff für dein Postfach.

Kommt keine Mail an, liegt es daran, dass schlabberschnuten.com keine Mails verschicken kann.
Schneller Vorabtest: abmelden, „Passwort vergessen" mit deiner Adresse. Kommt die auch nicht,
sag mir Bescheid — dann bauen wir den Versand über SMTP um.

Zum Schluss: **Artikelkatalog → Einstellungen → Testreservierungen löschen**.

## Was auf schlabberschnuten.com zu beachten ist

Auf der Seite laufen rund fünfzehn Plugins. Fünf davon können dem Katalog in die Quere
kommen. Das Plugin ist darauf vorbereitet, aber drei Kleinigkeiten musst du selbst erledigen.

### Vorher: Sicherung anlegen

Du hast **UpdraftPlus**. Mach einmal *Jetzt sichern* (Datenbank und Dateien), bevor du das
Plugin installierst. Dauert ein paar Minuten und du kannst jeden Schritt zurücknehmen.

### Elementor — die Katalogseite anders anlegen

Die Seite ist mit **Elementor** gebaut (Hello-Theme, Royal Addons, UAE). Der Kurzbefehl
gehört deshalb nicht in einen Block, sondern:

- **Ohne Elementor:** Seite anlegen, `[kikripp_katalog]` in den normalen Inhalt schreiben,
  veröffentlichen — **nicht** auf „Mit Elementor bearbeiten" klicken. Das ist der einfachste
  Weg und der, den ich empfehle.
- **Mit Elementor:** Seite mit Elementor bearbeiten, links nach dem Widget **Shortcode**
  suchen, auf die Seite ziehen und `[kikripp_katalog]` eintragen.

Wähle in beiden Fällen ein **breites Seitenlayout** (Elementor: *Elementor Canvas* oder
*Elementor Full Width*, sonst die Vorlage ohne Seitenleiste). Der Katalog zeigt vier Karten
nebeneinander — in einer schmalen Spalte mit Seitenleiste wird es eng.

### CookieYes — den Zugangs-Keks eintragen

**CookieYes** kann Skripte blockieren, bis jemand zustimmt. Das Katalog-Skript ist im Plugin
ausdrücklich als *notwendig* markiert, es sollte also durchlaufen. Zwei Dinge trag bitte
nachträglich ein:

1. Im CookieYes-Cookie-Verzeichnis den Keks **`kikripp_zugang`** als *notwendig* aufnehmen
   (Zweck: „merkt sich die Anmeldung am Artikelkatalog", Dauer 30 Tage). Er ist technisch
   erforderlich und braucht keine Zustimmung, muss aber aufgeführt sein.
2. Ruf die Katalogseite in einem privaten Fenster auf und **klick den Banner nicht weg**.
   Lädt der Katalog trotzdem? Wenn ja, ist alles gut. Wenn die Seite leer bleibt, sag mir
   Bescheid — dann müssen wir das Skript in CookieYes von der Blockierliste nehmen.

### Cache — nach dem Installieren einmal leeren

Oben in der Leiste hast du **Cache leeren**. Drück das nach der Installation und nach jedem
Artikelimport.

Das Plugin sagt dem Cache selbst, dass die Katalogseite nicht zwischengespeichert werden
darf, und alle Daten kommen mit „nicht zwischenspeichern"-Kennzeichnung. Trotzdem:
**Falls du im Cache-Plugin eine Ausschlussliste findest, trag die Katalogseite dort ein.**
Und wenn es eine Option zum *Zusammenfassen oder Verkleinern von JavaScript* gibt, nimm die
Katalogseite auch davon aus. Das ist die häufigste Ursache, wenn so eine Seite plötzlich leer
bleibt.

### Yoast — die Seite auf „nicht indexieren"

Das Plugin setzt die Angabe selbst und stimmt sich mit **Yoast** ab. Zur Sicherheit: In der
Katalogseite unten im Yoast-Kasten → *Erweitert* → *Erlauben, dass Suchmaschinen diese Seite
anzeigen?* auf **Nein** stellen. Dann ist es doppelt abgesichert.

### Der Hinweis von Popup Maker — den nimm ernst

In deinem Dashboard steht, dass **Popup Maker keine Dateien im Cache-Ordner anlegen kann**.
Das kann ein Eigenleben dieses Plugins sein, es kann aber auch heißen, dass der Webspace
teilweise **nicht beschreibbar** ist. Dann scheitern sowohl der Plugin-Upload als auch die
111 Fotos.

Deshalb der Reihe nach vorgehen:

1. Plugin hochladen. Klappt das, ist `wp-content/plugins` beschreibbar.
2. **Ein einzelnes Foto** in die Mediathek laden — `F-001.jpg` genügt. Klappt das, ist
   `wp-content/uploads` beschreibbar und du kannst den Rest hinterherschieben.
3. Scheitert einer der beiden Schritte mit einer Rechte- oder Verzeichnismeldung, ist es ein
   Fall für den Hoster („Schreibrechte auf wp-content wiederherstellen").

Teste das **bevor** du eine Stunde mit Fotos hochladen verbringst.

### Was unkritisch ist

**WPForms**, **Popup Maker**, **Announcer**, **Font Audit** und **Fonts Plugin** stören den
Katalog nicht. Das Plugin benutzt eigene Tabellen, eigene Einstellungsnamen, einen eigenen
Kurzbefehl und ein Stylesheet, das nur innerhalb des Katalogs gilt. Dass WPForms bei dir
funktioniert, ist übrigens ein gutes Zeichen: dann verschickt die Seite Mails.

---

## Wenn etwas nicht klappt

### „Plugins" steht gar nicht im linken Menü

Auf schlabberschnuten.com solltest du den Punkt sehen. Fehlt er trotzdem: Bist du als
**Administrator** angemeldet? Nur Administratoren sehen „Plugins". Ist die Seite eine
Multisite, liegen Plugins in der **Netzwerkverwaltung** — oben in der schwarzen Leiste über
„Meine Websites". Und manche Hostingpakete sperren das Installieren; dann fehlt auch der
Knopf „Plugin hochladen" (Stichwort für die Hotline: `DISALLOW_FILE_MODS`).

Ausweichweg: `kikripp-katalog.zip` auf dem Rechner entpacken und den Ordner
`kikripp-katalog` über den Dateimanager des Hosters nach `wp-content/plugins/` legen. Danach
steht es unter *Installierte Plugins* und muss nur aktiviert werden.

### Der Link mit `?kik=…` öffnet den Katalog nicht

- **Passwort stimmt nicht.** Groß- und Kleinschreibung zählt. Prüf es unter
  *Artikelkatalog → Einstellungen*, indem du es neu setzt.
- **Zu viele Fehlversuche.** Nach zehn falschen Versuchen macht die Bremse 15 Minuten zu.
  Kurz warten.
- **Sonderzeichen im Passwort.** `&`, `?`, `+` und Leerzeichen brechen die Adresse. Wenn dein
  Passwort so etwas enthält, nimm eines ohne — das jetzige (`2026…`) ist unproblematisch.

### Unter dem Katalog fehlt der Anbieter-Block

Dann ist das Feld „Verkäuferin (Firma)" leer. Eintragen unter
*Artikelkatalog → Einstellungen*.

### Der Impressum-Link geht auf eine Fehlerseite

Die beiden Adressen habe ich geraten, weil kikripp.de von mir aus nicht erreichbar ist.
Öffne die Seite auf kikripp.de, kopier die Adresse aus der Browserzeile und trag sie in den
Einstellungen ein. Das ist wichtig — ohne funktionierenden Impressum-Link fehlt die
Anbieterkennzeichnung.

### Das ZIP wird abgelehnt

- *„Die Datei überschreitet die Höchstgröße"* – unwahrscheinlich, das Paket ist nur 25 KB.
  Kommt die Meldung trotzdem, ist das Hochladen generell gesperrt: Weg von oben nehmen.
- *„Das Paket konnte nicht installiert werden. Keine gültigen Plugins gefunden"* – dann ist
  beim Herunterladen etwas mit der Datei passiert, meistens wurde sie unterwegs entpackt und
  wieder gepackt. Lad sie hier noch einmal herunter und **nicht** vorher entpacken.

### Nach dem Import steht „X Artikel ohne gefundenes Foto"

Die Bilder liegen noch nicht in der Mediathek oder heißen anders. Schau unter **Medien**
nach, ob `F-001.jpg` und die anderen da sind. Lad nach, was fehlt, und starte den Import
einfach noch einmal – das schadet nie.

### Die Mail an jennyp kommt nicht an

Zuerst im Spam-Ordner schauen und die Absenderadresse auf die Whitelist setzen — sie kommt
von schlabberschnuten.com, das kennt dein Postfach noch nicht.

Kommt sie auch dort nicht an, kann WordPress selbst keine Mails verschicken. Dann sag mir
Bescheid, dann bauen wir den Versand über SMTP um. **In der Zwischenzeit gehen keine
Reservierungen verloren:** Sie stehen unter *Artikelkatalog → Reservierungen*, und weil der
Mailversand gescheitert ist, bleiben die Kontaktdaten dort ausnahmsweise sichtbar. Notiere
sie und klick dann auf „notiert – Kontaktdaten löschen".

### Die Katalogseite bleibt leer

Der Rahmen ist da, aber keine Artikel. Drei Ursachen, in dieser Reihenfolge prüfen:

1. **Cache.** Oben *Cache leeren*, Seite neu laden.
2. **JavaScript zusammengefasst oder verkleinert.** Im Cache- oder Optimierungs-Plugin die
   Katalogseite von der JavaScript-Optimierung ausnehmen.
3. **CookieYes blockiert das Skript.** Im privaten Fenster prüfen: Lädt der Katalog, wenn du
   im Banner auf *Alle akzeptieren* klickst, aber nicht ohne? Dann ist es CookieYes.

### Der Katalog sieht gequetscht aus

Die Seite hat eine Seitenleiste oder ein schmales Layout. Seitenvorlage auf *Elementor
Canvas*, *Full Width* oder die Vorlage ohne Seitenleiste umstellen.

### Ich komme nicht weiter

Mach ein Bildschirmfoto vom linken Menü und schreib dazu, welche Adresse oben in der
Browserzeile steht. Damit sehe ich in der Regel sofort, woran es liegt.

---

## Im laufenden Betrieb

Unter **Artikelkatalog → Reservierungen** siehst du alle Vorgänge mit Ablaufdatum — ohne
Namen, dafür mit dem Suchbegriff für dein Postfach. Dort setzt du einen Vorgang auf
*bezahlt* (dann verschwinden die Artikel aus dem Katalog), *stornierst* ihn (dann werden sie
wieder frei) oder *verlängerst die Frist* um weitere sieben Tage. Abgelaufene Reservierungen
geben die Ware von selbst wieder frei, du musst nichts tun.

Für die Buchhaltung exportierst du die Reservierungen als CSV und schickst sie mir. Ich
trage Menge, Preis und Verkaufsdatum in den Artikelstamm ein. **Den Käufernamen trägst du
selbst ein** — im selben Moment, in dem du Rechnungsnummer, Zahlung und Zahlart einträgst.
Der Katalog kennt die Namen nicht.

## Wenn der Verkauf durch ist

Damit auf der Hundeschul-Seite nichts zurückbleibt:

1. Reservierungen als CSV exportieren und mir schicken — danach sind sie entbehrlich.
2. **Artikelkatalog → Einstellungen → Testreservierungen löschen**, falls noch welche da sind.
3. Die Katalogseite löschen.
4. Das Plugin deaktivieren und löschen.
5. Die 111 Fotos aus der Mediathek entfernen.
6. Den Absatz aus der Datenschutzerklärung wieder herausnehmen.
7. Den Knopf auf kikripp.de entfernen.
8. Enddatum in die Aktennotiz (`U1`) eintragen und ablegen.

## Was wohin gehört

Der **Artikelstamm** (die Excel-Datei) ist die Quelle für alles: Artikel, Preise, Rechnungen,
Kasse. Der **Webkatalog** führt allein Buch darüber, was reserviert und was bezahlt ist —
ohne Personendaten. Deine **Mails** sind das Kontaktarchiv. Das **Klinik-Angebot** ist nur
noch ein Dokument zum Anschauen; reserviert wird ausschließlich im Katalog, sonst vergibst du
dasselbe Stück zweimal.

Und die Hundeschule? Die stellt Speicherplatz. Nichts weiter.
