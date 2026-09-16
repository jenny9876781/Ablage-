# Webshop auf kikripp.de einrichten

Du brauchst dafür drei Dateien aus dem Ordner `ausgabe`: **kikripp-katalog.zip** (das
Plugin), **kikripp-fotos.zip** (die 111 Fotos) und **katalog_import.json** (die Artikel).
Rechne mit einer knappen Stunde, das meiste davon ist Warten beim Hochladen der Fotos.

## 1. Plugin installieren

Melde dich in WordPress an und geh auf **Plugins → Installieren → Plugin hochladen**.
Wähle `kikripp-katalog.zip`, klick auf *Jetzt installieren* und danach auf *Plugin
aktivieren*. In der linken Leiste erscheint jetzt der Menüpunkt **Artikelkatalog**.

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

Nach dem Aktivieren erscheint oben ein gelber Hinweis: es ist noch **kein Passwort
vergeben**, und ohne Passwort kommt niemand in den Katalog – auch du nicht. Das ist Absicht,
damit das Passwort nirgends in einer Datei steht.

Geh auf **Artikelkatalog → Einstellungen**, trag oben bei *Katalog-Passwort* das vereinbarte
Passwort ein und speichere. Der gelbe Hinweis verschwindet dann.

Auf derselben Seite stehen die Mailadresse für Reservierungen (`jennyp@kikripp.de`), das
Hinweisband über dem Katalog, die Reservierungsfrist von sieben Tagen, der Umsatzsteuersatz,
die Abholadresse und die rechtlichen Hinweise. Schau einmal drüber; ändern musst du dort
erst einmal nichts.

Willst du das Passwort später wechseln, trägst du hier einfach ein neues ein. Alle, die schon
angemeldet waren, müssen sich danach neu anmelden – praktisch, falls das Passwort mal
weitergereicht wurde.

Lass **Vorschaubetrieb** eingeschaltet, solange ihr testet. Dann werden alle
eingehenden Reservierungen als Testdaten markiert und lassen sich am Ende mit einem
Klick wieder löschen. Zum echten Start schaltest du den Haken aus.

## 5. Seite anlegen

Geh auf **Seiten → Erstellen**, nenn die Seite *Artikelkatalog* und setz als einzigen
Inhalt den Kurzbefehl:

    [kikripp_katalog]

Veröffentlichen. Die Seite trägt automatisch ein „nicht indexieren“ für Suchmaschinen,
sie taucht also nicht bei Google auf – nur wer den Link und das Passwort hat, kommt rein.

Damit unter **www.kikripp.de** direkt der Katalog erscheint, geh auf
**Einstellungen → Lesen**, wähl bei *Deine Homepage zeigt* die Option *Eine statische
Seite* und dort als Homepage die neue Katalogseite. Speichern. Fertig – wer kikripp.de
eintippt, landet jetzt im Katalog.

Setz über den Kurzbefehl noch ein paar Zeilen, damit jemand, der ohne Passwort kommt,
weiß worum es geht. Der Inhalt der Seite sieht dann so aus:

    Artikelkatalog aus der Betriebsauflösung

    Wir lösen unseren Kindergarten auf und geben die komplette Einrichtung ab – Möbel,
    Spielmaterial, Küche, Technik und Dekoration. Den vollständigen Katalog mit Fotos,
    Preisen und tagesaktueller Verfügbarkeit öffnen Sie mit dem Passwort, das Sie von uns
    erhalten haben. Sie haben noch keins? Schreiben Sie uns kurz an jennyp@kikripp.de.

    Abholung nach Terminvereinbarung in Villingen-Schwenningen.

    [kikripp_katalog]

Die alte Startseite ist damit nicht weg, sie ist nur nicht mehr die erste Seite. Willst du
sie weiter erreichbar halten, nimm sie ins Menü auf (**Design → Menüs**).

## 6. Einmal selbst durchtesten

Ruf die Seite in einem privaten Browserfenster auf, melde dich mit dem Passwort an,
merk dir zwei Artikel vor und schick eine Reservierung ab. Dann solltest du zwei Mails
bekommen: die Benachrichtigung an `jennyp@kikripp.de` und eine Bestätigung an die
Adresse, die du im Formular eingetragen hast.

Kommt keine Mail an, liegt das fast immer daran, dass WordPress selbst keine Mails
verschicken kann. Das Kontaktformular auf der alten Seite hat funktioniert, also sollte
es gehen – falls doch nicht, sag mir Bescheid, dann bauen wir den Versand über einen
SMTP-Zugang um.

Zum Schluss: **Artikelkatalog → Einstellungen → Testreservierungen löschen**.

## Wenn etwas nicht klappt

### „Plugins" steht gar nicht im linken Menü

Geh die vier Punkte der Reihe nach durch, es ist fast immer der erste oder der zweite.

**1. Bist du als Administrator angemeldet?** Nur Administratoren sehen „Plugins".
Als Redakteurin oder Autorin ist der Punkt unsichtbar. Klick oben rechts auf deinen Namen
→ *Profil*. Wenn dort keine Rolle steht oder du unter **Benutzer** deinen eigenen Eintrag
nicht bearbeiten kannst, bist du nicht Administratorin. Dann braucht es die Person, die den
Zugang eingerichtet hat.

**2. Läuft die Seite auf wordpress.com?** Schau auf die Adresse in der Browserzeile, während
du im Backend bist. Steht dort `wordpress.com`, ist es die gehostete Variante – dort sind
Plugins erst ab dem Business-Tarif erlaubt, vorher gibt es den Menüpunkt schlicht nicht.
Steht dort `kikripp.de/wp-admin`, ist alles in Ordnung und es liegt an etwas anderem.

**3. Ist es eine Multisite?** Dann liegen Plugins nicht in deiner Seite, sondern eine Ebene
darüber. Oben in der schwarzen Leiste erscheint dann *Meine Websites* oder
*Netzwerkverwaltung* – dort ist der Menüpunkt.

**4. Hat der Hoster es gesperrt?** Manche Pakete mit „verwaltetem WordPress" schalten das
Installieren ab. Dann fehlt der Punkt ebenfalls. Das lässt sich nur beim Hoster freischalten
oder umgehen, indem der Ordner von Hand hochgeladen wird (siehe unten).

### „Plugins" ist da, aber es fehlt „Installieren" oder „Plugin hochladen"

Gleiche Ursache wie Punkt 4: Der Hoster hat das Ändern von Dateien gesperrt. Zwei Wege:

- Beim Hoster anrufen und um Freischaltung bitten. Das Stichwort für die Hotline lautet
  `DISALLOW_FILE_MODS` in der `wp-config.php`.
- Oder das Plugin von Hand hochladen: `kikripp-katalog.zip` auf deinem Rechner entpacken,
  dann über den Dateimanager des Hosters (oder FTP) den entstandenen Ordner
  `kikripp-katalog` nach `wp-content/plugins/` legen. Danach steht es unter **Plugins →
  Installierte Plugins** und muss nur noch aktiviert werden.

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

### Die Testmail kommt nicht an

Schau zuerst in den Spam-Ordner. Kommt sie auch dort nicht an, kann WordPress selbst keine
Mails verschicken. Sag mir Bescheid, dann bauen wir den Versand über einen SMTP-Zugang um;
die Reservierungen sind in der Zwischenzeit trotzdem gespeichert und unter
**Artikelkatalog → Reservierungen** sichtbar.

### Ich komme nicht weiter

Mach ein Bildschirmfoto vom linken Menü und schreib dazu, welche Adresse oben in der
Browserzeile steht. Damit sehe ich in der Regel sofort, woran es liegt.

---

## Im laufenden Betrieb

Unter **Artikelkatalog → Reservierungen** siehst du alle Vorgänge mit Ablaufdatum. Dort
setzt du einen Vorgang auf *bezahlt* (dann verschwinden die Artikel aus dem Katalog),
*stornierst* ihn (dann werden sie wieder frei) oder *verlängerst die Frist* um weitere
sieben Tage. Abgelaufene Reservierungen geben die Ware von selbst wieder frei, du musst
nichts tun.

Für die Buchhaltung exportierst du die Reservierungen als CSV und liest sie mit

    python3 scripts/reservierungen_einlesen.py <exportdatei.csv> --schreiben

in den Artikelstamm ein. Danach `python3 scripts/build_artikelstamm_xlsx.py`, und
Verkaufsübersicht, DATEV-Liste und Kassenbuch sind auf Stand. Rechnungsnummer, Zahlung
und Zahlart trägst du weiterhin selbst ein, sobald die Rechnung aus DATEV vorliegt.

## Was wohin gehört

Der **Artikelstamm** (die Excel-Datei) ist die Quelle für alles: Artikel, Preise,
Rechnungen, Kasse. Der **Webshop** führt allein Buch darüber, was reserviert und was
bezahlt ist. Das **Klinik-Angebot** ist nur noch ein Dokument zum Anschauen – reserviert
wird ausschließlich im Webshop, sonst vergibst du dasselbe Stück zweimal.
