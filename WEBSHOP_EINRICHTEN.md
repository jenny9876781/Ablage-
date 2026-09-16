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
