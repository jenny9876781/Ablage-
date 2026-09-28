# Webkatalog einrichten

Der Katalog läuft auf **www.kikripp.de** — der eigenen Website der Gesellschaft. Du bist
dort Super-Admin und kannst Plugins installieren. Damit entfällt der Umweg über eine fremde
Website: keine Aktennotiz, kein Knopf von einer Seite zur anderen, keine Erklärung, warum
der Katalog woanders liegt. Verkäuferin, Website und Impressum gehören derselben Firma.

> **kikripp.de ist ein Multisite-Netzwerk** (oben in der Leiste steht „Meine Websites").
> Plugins lassen sich dort nur über die **Netzwerkverwaltung** installieren — deshalb geht
> es nur als Super-Admin. Die einzelnen Schritte stehen unten.

Du brauchst drei Dateien aus dem Ordner `ausgabe`: **kikripp-katalog.zip** (das Plugin),
**kikripp-fotos.zip** (die Fotos) und **katalog_import.json** (die Artikel). Rechne mit zwei
Stunden, das meiste davon ist Warten beim Hochladen der Fotos.

> **Wichtig zum Verständnis:** Der Katalog speichert in WordPress **keine Namen,
> keine Mailadressen, keine Telefonnummern**. Die gehen ausschließlich per Mail an
> `jennyp@kikripp.de` und werden danach sofort aus der Datenbank gelöscht. Diese Mails sind
> damit dein einziges Kontaktarchiv — **bitte nicht löschen.** Leg dir einen Ordner an.

## 1. Plugin installieren

Melde dich auf **www.kikripp.de/wp-admin** an. Weil kikripp.de ein Netzwerk ist, läuft die
Installation in zwei Schritten:

1. Oben links auf **Meine Websites → Netzwerkverwaltung → Plugins**, dann
   **Installieren → Plugin hochladen**. Wähle `kikripp-katalog.zip` und klick auf
   *Jetzt installieren*.
2. **Nicht** „Im Netzwerk aktivieren" wählen. Geh zurück auf die Seite **KIKRIPP**
   (Meine Websites → KIKRIPP → Dashboard), dort auf **Plugins**, und aktiviere
   *Kikripp Artikelkatalog* nur für diese eine Website.

In der linken Leiste erscheint danach der Menüpunkt **Artikelkatalog**.

Warum nicht im Netzwerk aktivieren: der Katalog gehört auf eine Website, nicht auf alle.
Eine Netzwerk-Aktivierung würde ihn auf jeder Seite des Netzwerks einschalten und liesse
sich später nur wieder zentral abschalten.

## 2. Fotos in die Mediathek

Entpacke `kikripp-fotos.zip` auf deinem Rechner – du bekommst einen Ordner `fotos` mit
gut 400 Bildern (rund 80 MB). Geh in WordPress auf **Medien → Datei hinzufügen** und zieh
die Bilder in das Feld — am besten in Paketen von hundert, nicht alle auf einmal. Das
dauert; lass das Browserfenster offen, bis jedes Paket durch ist.

Die genaue Zahl steht in der Meldung von `build_fotopaket.py`, das die Datei erzeugt.

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
| **Impressum** | `https://www.kikripp.de/impressum/` — **die Seite muss veröffentlicht sein**, siehe unten |
| **Datenschutzerklärung** | `https://www.kikripp.de/datenschutz/` — **ebenfalls veröffentlicht**, siehe unten |
| Abholadresse | erscheint unter dem Katalog |
| Hinweisband | Text über dem Katalog, zum Livegang leeren |
| Reservierung gilt | 7 Tage |
| Umsatzsteuer | 19 % |
| Rechtliche Hinweise | Verkaufsbedingungen, änderbar |

**Achtung, das ist der eine Punkt, der den Livegang aufhält:** Impressum und Datenschutz
stehen auf kikripp.de zurzeit als **Entwurf**, sind also öffentlich nicht erreichbar. Ein
Katalog, in dem Ware gegen Geld angeboten wird, braucht beides erreichbar — das Impressum
nach § 5 DDG, die Datenschutzerklärung nach Art. 13 DSGVO, weil das Reservierungsformular
Name, Mailadresse und Telefonnummer entgegennimmt. Beide Seiten also **veröffentlichen**,
bevor der erste Link hinausgeht, und danach die Adressen hier einmal anklicken.

Lass **Vorschaubetrieb** eingeschaltet, solange ihr testet. Dann werden alle eingehenden
Reservierungen als Testdaten markiert und lassen sich am Ende mit einem Klick löschen.

Und füge noch den Absatz aus **`U2_Datenschutz_Absatz.docx`** in die Datenschutzerklärung
von kikripp.de ein. Er beschreibt, was mit den Daten aus dem Reservierungsformular passiert.
Das ist der einzige Papierkram, der nötig ist.

## 5. Seite anlegen

Geh auf **Seiten → Erstellen**, nenn die Seite *Artikelkatalog* und setz als einzigen Inhalt
den Kurzbefehl:

    [kikripp_katalog]

Veröffentlichen. Die Adresse lautet dann `www.kikripp.de/artikelkatalog`. Wähle eine
**breite Vorlage ohne Seitenleiste** — der Katalog zeigt vier Karten nebeneinander, in einer
schmalen Spalte wird es eng.

Die Seite trägt automatisch ein „nicht indexieren" für Suchmaschinen und taucht nicht bei
Google auf.

**Der Wartungsmodus.** Auf kikripp.de ist zurzeit die Seite *Wartung* als Startseite gesetzt
und alles andere steht auf Entwurf. Prüfe, ob ein Wartungs- oder Coming-Soon-Plugin die
Website für Besucher sperrt. Wenn ja, muss die Katalogseite dort als **Ausnahme** eingetragen
werden — sonst sehen die Interessenten die Wartungsseite statt des Katalogs. Am einfachsten
prüfst du das, indem du den fertigen Link in einem privaten Browserfenster öffnest, in dem du
nicht angemeldet bist. Genau das macht Schritt 6.

**Der Link mit Passwort.** Hängst du `?kik=DASPASSWORT` an die Adresse, öffnet sich der Katalog
direkt — niemand muss etwas eintippen. Das Passwort verschwindet dabei sofort wieder aus der
Adresszeile. Diesen Link verschickst du an die Interessenten:

    https://www.kikripp.de/artikelkatalog/?kik=DASPASSWORT

**Ein Knopf im Menü** ist möglich, aber nicht nötig: der Katalog ist ohnehin nur über den
Link mit Passwort erreichbar. Solange kikripp.de im Wartungsmodus ist, würde ein Menüpunkt
auch niemandem angezeigt.

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

Kommt keine Mail an, kann kikripp.de keine Mails verschicken. Schneller Vorabtest: abmelden,
„Passwort vergessen" mit deiner Adresse. Kommt die auch nicht, sag mir Bescheid — dann bauen
wir den Versand über SMTP um. Hier gibt es eine Besonderheit: Absender und Empfänger liegen
beide auf `kikripp.de`. Manche Postfächer sortieren eine Mail, die scheinbar von einem selbst
kommt, in den Spam-Ordner. **Sieh beim ersten Test also auch dort nach.**

Zum Schluss: **Artikelkatalog → Einstellungen → Testreservierungen löschen**.

## Was auf kikripp.de zu beachten ist

Auf der Seite laufen **18 Plugins**, alle netzwerkweit aktiviert bis auf *Maintenance*.
Ich habe die Liste durchgesehen. Das meiste ist unkritisch, und zwei Dinge, die sonst
Handarbeit gewesen wären, erledigt das Katalog-Plugin inzwischen selbst.

### Erledigt sich von allein — Autoptimize und die Verkleinerung

**Autoptimize** und die *Minify*-Funktion von **W3 Total Cache** fassen JavaScript und CSS
aller Seiten zu Sammeldateien zusammen. Genau daran gehen solche Katalogseiten am häufigsten
kaputt: die Seite lädt, bleibt aber leer.

Das musst du **nicht** mehr von Hand eintragen. Das Plugin meldet sich bei Autoptimize selbst
als Ausnahme an (alle seine Dateien heißen `kikripp…`) und setzt auf der Katalogseite die
Kennzeichnung `DONOTMINIFY`, an die sich W3 Total Cache hält. Was du in Autoptimize schon
eingetragen hast, bleibt dabei stehen.

### W3 Total Cache — Cache leeren nach jedem Import

Das Plugin sagt dem Cache, dass die Katalogseite nicht zwischengespeichert werden darf.
Trotzdem: nach der Installation und **nach jedem Artikelimport** einmal oben in der Leiste
*Performance → Purge All Caches*. Sonst siehst du alte Preise, obwohl die neuen schon drin
sind.

> **Beobachtung am Rande, unabhängig vom Katalog:** Autoptimize **und** W3 Total Cache machen
> beide Minify. Zwei Plugins, die dasselbe tun, ist eine bekannt wacklige Kombination. Für den
> Katalog ist das egal — er ist aus beiden ausgenommen. Wenn auf der Seite sonst irgendwann
> etwas seltsam aussieht, ist das der erste Ort zum Nachsehen.

### Really Simple SSL — der erste Verdächtige, wenn der Katalog leer bleibt

Really Simple SSL bringt Härtungsfunktionen mit, darunter Einschränkungen der **REST-
Schnittstelle**. Der Katalog holt seine Artikel genau darüber, und zwar für Besucher, die
**nicht** in WordPress angemeldet sind.

Ich kann von hier aus nicht sehen, welche Härtung bei dir eingeschaltet ist. Deshalb: Bleibt
der Katalog im privaten Fenster leer, obwohl das Passwort stimmt, schau unter
**Einstellungen → Really Simple SSL → Härtung** nach einem Punkt in Richtung *REST-API für
abgemeldete Benutzer deaktivieren* und schalte ihn für den Test ab. Ändert sich nichts, sag
mir Bescheid.

### Maintenance — aus lassen

Das Wartungs-Plugin ist **nicht aktiviert**, und das soll so bleiben, solange der Katalog
läuft. Es würde die ganze Website für abgemeldete Besucher sperren, also auch den Katalog.

Dass auf kikripp.de trotzdem *Wartung* erscheint, liegt nur daran, dass diese Seite als
Startseite eingestellt ist. Andere Seiten sind über ihre eigene Adresse ganz normal
erreichbar — der Katalog also auch. Das ist genau die Situation, die wir brauchen: die
Website wirkt nach außen ruhig, der Katalog ist über seinen Link trotzdem da.

### XML Sitemap Generator — Katalogseite herausnehmen

Der Katalog trägt selbst ein „nicht indexieren", aber der Sitemap-Generator würde die Adresse
trotzdem bei Google anmelden. Nimm die Katalogseite in den Einstellungen des Plugins von der
Sitemap aus. Schlimm wäre es nicht — ohne Passwort sieht Google nur das Anmeldefeld —, aber
sauberer ist es so.

### BackWPup — vorher einmal sichern

Du hast BackWPup. Lass einen Durchgang mit **Datenbank und Dateien** laufen, bevor du das
Plugin installierst. Dann lässt sich jeder Schritt zurücknehmen.

### Bootstrap Blocks — nur anschauen

Das Plugin lädt Bootstrap-Stile. Der Katalog bringt eigene mit, die nur innerhalb des Katalogs
gelten; bei Knöpfen und Bildern kann sich aber trotzdem etwas überlagern. Sieh dir die fertige
Seite einmal an. Sieht etwas schief aus, schick mir ein Bildschirmfoto, das ist schnell
behoben.

### EWWW Image Optimizer und Simply Gallery — unkritisch

**EWWW** verkleinert Bilder beim Hochladen und kann sie verzögert laden. Die Artikelfotos
setzt der Katalog erst nach dem Laden der Seite per JavaScript ein — daran kommt das
verzögerte Laden nicht heran. Wichtig ist nur: **die Dateinamen dürfen sich nicht ändern**,
der Katalog findet die Fotos darüber. EWWW benennt nichts um, das passt.

**Simply Gallery Block & Lightbox** legt sich auf Bilder und öffnet sie groß. Es kann sein,
dass es auch die Artikelfotos anfasst. Das ist kein Schaden — sieh beim Testlauf einfach, ob
ein Klick auf ein Foto sich seltsam verhält.

### Der Rest

**ACF PRO**, **Custom Post Type UI**, **Multisite Post Duplicator**, **NS Cloner**,
**Post Types Order**, **Statify** (beide Teile), **SVG Support** und **Timeline Block** stören
den Katalog nicht. Er benutzt eigene Tabellen, eigene Einstellungsnamen, einen eigenen
Kurzbefehl, einen eigenen REST-Namensraum und ein Stylesheet, das nur innerhalb des Katalogs
gilt.

**CookieYes und Yoast gibt es auf kikripp.de nicht.** Das Plugin bringt für beide
Vorkehrungen mit; sie tun schlicht nichts, wenn das jeweilige Plugin fehlt.

### Schreibrechte kurz prüfen

Bevor du Stunden mit dem Hochladen von Fotos verbringst, der Reihe nach:

1. Plugin hochladen. Klappt das, ist `wp-content/plugins` beschreibbar.
2. **Ein einzelnes Foto** in die Mediathek laden — `F-001.jpg` genügt. Klappt das, ist
   `wp-content/uploads` beschreibbar und du kannst den Rest hinterherschieben.
3. Scheitert einer der beiden Schritte mit einer Rechte- oder Verzeichnismeldung, ist es ein
   Fall für den Hoster („Schreibrechte auf wp-content wiederherstellen").

### WordPress 7.1.2 — vorher aktualisieren

Im Dashboard steht ein Update an. Mach es **vor** der Installation des Katalogs, nicht danach.

---

## Wenn etwas nicht klappt

### „Plugins" steht gar nicht im linken Menü

kikripp.de ist ein Netzwerk, deshalb steht „Plugins" im Menü der einzelnen Website nur zum
Aktivieren — **installiert** wird ausschließlich in der **Netzwerkverwaltung** (oben in der
schwarzen Leiste über „Meine Websites"). Fehlt der Punkt auch dort, sperrt das Hostingpaket
das Installieren; dann fehlt auch der Knopf „Plugin hochladen" (Stichwort für die Hotline:
`DISALLOW_FILE_MODS`).

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

Zuerst im Spam-Ordner schauen und die Absenderadresse auf die Whitelist setzen. Absender und
Empfänger liegen beide auf `kikripp.de`; manche Postfächer sortieren eine Mail, die scheinbar
von einem selbst kommt, aus.

Kommt sie auch dort nicht an, kann WordPress selbst keine Mails verschicken. Dann sag mir
Bescheid, dann bauen wir den Versand über SMTP um. **In der Zwischenzeit gehen keine
Reservierungen verloren:** Sie stehen unter *Artikelkatalog → Reservierungen*, und weil der
Mailversand gescheitert ist, bleiben die Kontaktdaten dort ausnahmsweise sichtbar. Notiere
sie und klick dann auf „notiert – Kontaktdaten löschen".

### Die Katalogseite bleibt leer

Der Rahmen ist da, aber keine Artikel. Auf kikripp.de in dieser Reihenfolge prüfen:

1. **Cache.** *Performance → Purge All Caches*, Seite neu laden. Das ist mit Abstand die
   häufigste Ursache.
2. **Really Simple SSL sperrt die REST-Schnittstelle.** Der Katalog holt seine Artikel
   darüber, und zwar als abgemeldeter Besucher. Unter **Einstellungen → Really Simple SSL →
   Härtung** nach einem Punkt in Richtung *REST-API für abgemeldete Benutzer deaktivieren*
   suchen und für den Test abschalten.
3. **Minify.** Eigentlich abgedeckt — das Plugin nimmt sich bei Autoptimize und W3 Total Cache
   selbst aus. Zur Sicherheit: in **Performance → Minify** die Funktion kurz abschalten und
   neu laden. Ändert das etwas, sag mir Bescheid.

**So findest du Punkt 2 in zehn Sekunden:** Ruf in einem privaten Fenster, ohne angemeldet
zu sein, diese Adresse auf:

    https://www.kikripp.de/wp-json/kikripp/v1/artikel

Du bekommst dort **keine** Artikelliste, das ist richtig so — ohne Passwort antwortet der
Katalog mit einer kurzen Sperrmeldung. Worauf es ankommt, ist **welche** Antwort kommt:

| Was da steht | Was es bedeutet |
|---|---|
| `{"ok":false,"gesperrt":true}` | Die Schnittstelle ist offen, der Katalog antwortet. Ursache liegt woanders — weiter mit Punkt 3. |
| Etwas mit `rest_` und „nicht berechtigt", „disabled" oder „forbidden" | Die REST-Schnittstelle ist gesperrt. Das ist Punkt 2. |
| Eine WordPress-Fehlerseite oder gar nichts | Schick mir einen Bildschirmabzug davon. |

### Der Katalog sieht gequetscht aus

Die Seite hat eine Seitenleiste oder ein schmales Layout. Seitenvorlage auf eine breite
Vorlage ohne Seitenleiste umstellen.

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

Damit auf kikripp.de nichts zurückbleibt:

1. Reservierungen als CSV exportieren und mir schicken — danach sind sie entbehrlich.
2. **Artikelkatalog → Einstellungen → Testreservierungen löschen**, falls noch welche da sind.
3. Die Katalogseite löschen.
4. Das Plugin auf der Website deaktivieren und in der Netzwerkverwaltung löschen.
5. Die Fotos aus der Mediathek entfernen.
6. Den Absatz aus der Datenschutzerklärung wieder herausnehmen.
7. Den Cache einmal leeren (*Performance → Purge All Caches*).

## Was wohin gehört

Der **Artikelstamm** (die Excel-Datei) ist die Quelle für alles: Artikel, Preise, Rechnungen,
Kasse. Der **Webkatalog** führt allein Buch darüber, was reserviert und was bezahlt ist —
ohne Personendaten. Deine **Mails** sind das Kontaktarchiv. Das **Klinik-Angebot** ist nur
noch ein Dokument zum Anschauen; reserviert wird ausschließlich im Katalog, sonst vergibst du
dasselbe Stück zweimal.
