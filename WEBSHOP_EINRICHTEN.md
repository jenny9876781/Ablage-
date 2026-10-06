# Webkatalog einrichten

Der Katalog läuft auf **www.kikripp.de** — der eigenen Website der Gesellschaft. Du bist
dort Super-Admin und kannst Plugins installieren. Damit entfällt der Umweg über eine fremde
Website: keine Aktennotiz, kein Knopf von einer Seite zur anderen, keine Erklärung, warum
der Katalog woanders liegt. Verkäuferin, Website und Impressum gehören derselben Firma.

> **kikripp.de ist ein Multisite-Netzwerk** (oben in der Leiste steht „Meine Websites").
> Plugins lassen sich dort nur über die **Netzwerkverwaltung** installieren — deshalb geht
> es nur als Super-Admin. Die einzelnen Schritte stehen unten.

Du brauchst aus dem Ordner `ausgabe`: **kikripp-katalog.zip** (das Plugin), die drei
Fotopakete **kikripp-fotos-1von3.zip** bis **-3von3.zip** und **katalog_import.json**
(die Artikel). Rechne mit zwei
Stunden, das meiste davon ist Warten beim Hochladen der Fotos.

> **Wichtig zum Verständnis:** Der Webserver von kikripp.de verschickt **keine Mails** — das
> ist beim Einrichten am 29.09.2026 geprüft und bestätigt worden. Die Reservierungen stehen
> deshalb in WordPress unter **Artikelkatalog → Reservierungen**, mit Name, Mailadresse und
> Telefonnummer. Neben dem Menüpunkt erscheint eine Zahl, sobald etwas offen ist — so siehst
> du es beim Einloggen, ohne daran denken zu müssen. **Schau einmal am Tag hinein.**
>
> Ist ein Vorgang abgewickelt, klick bei der Reservierung auf *„erledigt – Kontaktdaten
> löschen"*. Dann bleiben nur noch Artikelnummer, Menge und Preis stehen. So liegt nichts
> länger herum als nötig — und genau so steht es auch in der Datenschutzerklärung.

## 0. Fünf Minuten Vorarbeit, die zwei Stunden Ärger sparen

Bitte diese fünf Punkte **vor** dem ersten Klick abhaken. Jeder einzelne davon würde dich
sonst mitten im Aufbau erwischen.

**a) Speicherplatz der Website prüfen — der wichtigste Punkt.**
In einem Multisite-Netzwerk hat jede Website ein Platzkonto, standardmäßig **100 MB**. Die
Fotos brauchen **83 MB**, und auf kikripp.de liegen schon Bilder der bestehenden Seite. Reicht
das Konto nicht, bricht das Hochladen mittendrin ab mit einer Meldung über die
Speicherplatzbegrenzung — und du weißt nicht, welche Bilder durch sind.

Geh auf **Meine Websites → Netzwerkverwaltung → Einstellungen** und such den Abschnitt
*Upload-Einstellungen*. Dort stehen zwei Zahlen:

| Einstellung | Was sie sein muss |
|---|---|
| *Speicherplatz pro Website begrenzen* | entweder abschalten, oder auf mindestens **500 MB** setzen |
| *Maximale Größe der Upload-Datei* | mindestens **1000 KB** (unser größtes Foto hat 623 KB) |

Als Super-Admin darfst du das ändern. Wenn du unsicher bist: die Begrenzung ganz abschalten
ist für eine Seite, die dir selbst gehört, unbedenklich.

**b) WordPress aktualisieren.** Im Dashboard steht 7.1.2 an. Mach das jetzt, nicht später.

**c) Sicherung anlegen.** Du hast BackWPup. Einmal *Datenbank und Dateien* durchlaufen lassen.

**d) Impressum und Datenschutz veröffentlichen.** Beide stehen bei dir auf *Entwurf* und sind
damit öffentlich nicht erreichbar. Der Katalog verlinkt sie unter jedem Angebot. Ohne sie darf
kein Link hinausgehen.

**e) Nichts am Wartungs-Plugin ändern.** *Maintenance* ist aus — das ist richtig so und muss
so bleiben. Die Wartungsseite, die Besucher auf kikripp.de sehen, ist nur deine eingestellte
Startseite; alle anderen Seiten sind über ihre eigene Adresse erreichbar.

---

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

Ein Passwort braucht es seit Fassung 1.2.0 nicht mehr — der Katalog ist frei zugänglich.

Warum nicht im Netzwerk aktivieren: der Katalog gehört auf eine Website, nicht auf alle.
Eine Netzwerk-Aktivierung würde ihn auf jeder Seite des Netzwerks einschalten und liesse
sich später nur wieder zentral abschalten.

## 2. Fotos in die Mediathek

Du bekommst die Fotos in **vier Paketen** (`kikripp-fotos-1von4.zip` bis `-4von4.zip`),
weil 83 MB auf einmal für den Versand zu viel sind. Entpacke sie auf deinem Rechner — alle
vier in denselben Ordner `fotos`. Zusammen sind es genau **412 Bilder, 83 MB**. Geh in WordPress auf **Medien → Datei hinzufügen** und
zieh die Bilder in das Feld — am besten in Paketen von hundert, nicht alle auf einmal. Das
dauert; lass das Browserfenster offen, bis jedes Paket durch ist.

**So prüfst du, ob alles angekommen ist:** Geh auf **Medien → Mediathek** und schalte oben
rechts auf die Listenansicht. Unten steht die Gesamtzahl der Einträge. Sie muss um 412
gestiegen sein.

Und falls doch etwas fehlt: **das ist kein Problem und du musst nicht suchen.** Der Import im
nächsten Schritt sagt dir die fehlenden Bilder beim Namen. Die lädst du dann einzeln nach und
importierst noch einmal.

Die Dateinamen dürfen sich nicht ändern — das Plugin findet die Fotos darüber. Lädst du
versehentlich dasselbe Bild zweimal hoch, hängt WordPress eine `-1` an; der Katalog findet es
trotzdem, es liegt dann nur doppelt auf dem Server.

## 3. Artikel importieren

Geh auf **Artikelkatalog → Artikel importieren**, wähle `katalog_import.json` und klick
auf Importieren. Der Import dauert **ein paar Sekunden**, nicht Minuten.

Danach steht oben eine Meldung. **So muss sie aussehen:**

    Import abgeschlossen: 497 neu, 0 aktualisiert.

Kein weiterer Satz dahinter — das heißt: jeder Artikel hat sein Foto gefunden. Im Katalog
sichtbar sind davon **415**; die übrigen stehen bewusst auf „nicht im Katalog".

Steht dahinter noch *„… Artikel ohne gefundenes Foto"*, nennt die Meldung die fehlenden
Bilder beim Namen. Die lädst du in die Mediathek nach und importierst einfach noch einmal.
Mehrfaches Importieren schadet nie.

Diesen Schritt wiederholst du jedes Mal, wenn neue Artikel dazukommen oder Preise sich
ändern: neue Datei erzeugen lassen, hochladen, fertig. Bestehende Artikel werden
aktualisiert, neue kommen dazu, und Reservierungen bleiben erhalten.

## 4. Einstellungen prüfen

Seit Fassung 1.2.0 (Oktober 2026) ist der Katalog **ohne Passwort** erreichbar. Bei Google
erscheint er trotzdem nicht: die Seite trägt „noindex“, und ohne den Link findet ihn niemand.

Geh auf **Artikelkatalog → Einstellungen** und arbeite die Seite von oben nach unten durch:

> **Warum zwei Mailadressen?** Der Webserver von kikripp.de verschickt Mails nur
> unzuverlässig — an ein Postfach auf der eigenen Domain kommen sie mit Stunden
> Verzögerung und im Spam-Ordner an, an Outlook gar nicht. Deshalb ist die **interne
> Meldeadresse** eine auf kikripp.de, während Interessenten die **Verkaufsadresse**
> sehen. Verlass dich aber nicht auf die Mail: Die Reservierungen stehen vollständig
> unter *Artikelkatalog → Reservierungen*, und eine Zahl am Menüpunkt zeigt dir, wenn
> etwas offen ist.

Die Tabelle steht in **derselben Reihenfolge wie das Formular** — du kannst sie einfach
danebenlegen und abarbeiten. Beim Einspielen von Fassung 1.2.0 werden die Verkaufsregeln
automatisch eingetragen; du prüfst sie nur.

| Feld (in dieser Reihenfolge) | Was hineingehört |
|---|---|
| Passwortschutz | **aus** — der Katalog ist frei zugänglich |
| Katalog-Passwort | leer lassen; gilt nur, wenn der Passwortschutz wieder eingeschaltet wird |
| Reservierungen melden an | `jennyp@kikripp.de` — **interne** Meldung. Auf kikripp.de kommt nur hier etwas an, und auch das verzögert und im Spam-Ordner |
| Kontaktadresse für Interessenten | `saldi4kids@outlook.com` — diese Adresse **sehen die Käufer** im Anbieter-Block und in der Bestätigung |
| Hinweisband | Text über dem Katalog, derzeit die Ankündigung zum Spielzeug im November |
| Reservierung gilt | 3 Werktage (Montag bis Freitag) |
| Mindestbestellwert | 50 € |
| Besichtigung ab | 100 € Stückpreis |
| Abholung bis | 10.12.2026 |
| So läuft es ab | der Kasten über den Artikeln; jede Zeile ein Punkt |
| Umsatzsteuer | 0 % — steuerfreie Lieferung |
| Steuerhinweis | „Endpreise · umsatzsteuerfrei gemäß § 4 Nr. 28 UStG“ |
| Verkäuferin (Firma) | `Kikripp GmbH` — steht so im Katalog, im Mailbetreff und auf der Bestellung |
| Telefon | die Nummer der Kikripp GmbH |
| **Impressum** | `https://www.kikripp.de/impressum/` — die Seite muss veröffentlicht sein |
| **Datenschutzerklärung** | `https://www.kikripp.de/datenschutz/` — ebenfalls veröffentlicht |
| Abholadresse | erscheint unter dem Katalog und auf der Bestellung |
| Rechtliche Hinweise | die Kaufbedingungen mit dem Steuerabsatz; stehen unter dem Katalog und auf jeder Bestellung |
| Fußzeile ausblenden | **an** — die Fußzeile der Website erscheint auf der Katalogseite nicht; Impressum und Datenschutz stehen im Anbieter-Block |
| Vorschaubetrieb | **eingeschaltet lassen**, solange ihr testet |

Zu **Vorschaubetrieb**: Solange der Haken gesetzt ist, werden alle eingehenden Reservierungen
als Testdaten markiert und lassen sich am Ende mit einem Klick gemeinsam löschen. Erst zum
Livegang nimmst du ihn heraus.

Zu **Impressum und Datenschutz**: Das sind die beiden Adressen aus Punkt 0d. Klick sie hier
einmal an, nachdem du die Seiten veröffentlicht hast — sie müssen sich öffnen. Der Katalog
verlinkt sie unter jedem Angebot; das Impressum verlangt § 5 DDG, die Datenschutzerklärung
Art. 13 DSGVO, weil das Reservierungsformular Name, Anschrift, Mailadresse und Telefonnummer
entgegennimmt.

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

**Zum Wartungsmodus — das ist geklärt und kein Problem.** Auf kikripp.de zeigt die Startseite
*Wartung*, weil diese Seite als Startseite eingestellt ist. Das Plugin *Maintenance*, das die
ganze Website sperren würde, ist **ausgeschaltet**. Andere Seiten sind deshalb über ihre eigene
Adresse ganz normal erreichbar — die Katalogseite also auch. Nur: *Maintenance* bitte nicht
einschalten, solange der Katalog läuft. Schritt 6 prüft das ohnehin mit.

**Der Link.** Diesen Link verschickst du an die Interessenten — ohne Passwort:

    https://www.kikripp.de/artikelkatalog/

**Ein Knopf im Menü** ist möglich, aber nicht nötig: Bei Google erscheint der Katalog nicht,
und solange die Startseite die Wartungsseite ist, findet ihn niemand von selbst.

## 6. Einmal selbst durchtesten

Ruf den Link in einem privaten Browserfenster auf. Der Katalog sollte sich
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

## 7. Livegang — die letzten fünf Handgriffe

Erst wenn Schritt 6 sauber durchgelaufen ist. Der Reihe nach:

1. **Artikelkatalog → Einstellungen → Testreservierungen löschen.** Damit sind alle Vorgänge
   aus der Testphase weg und die Nummerierung beginnt bei den echten Interessenten.
2. **Vorschaubetrieb ausschalten.** Ab jetzt sind eingehende Reservierungen echt.
3. **Hinweisband leeren.** Der Testhinweis über dem Katalog verschwindet damit.
4. **Cache leeren** (*Performance → Purge All Caches*).
5. **Noch einmal im privaten Fenster ansehen.** Kein Testhinweis mehr, Preise stimmen,
   alle Artikel da. Dann erst den Link verschicken.

**Sicherheitsnetz:** Sollte an diesem Punkt doch etwas nicht stimmen, nimm einfach den
Vorschaubetrieb wieder an und schreib mir. Der Katalog ist über den Link ohne Passwort für
niemanden erreichbar — es kann dir also nichts „entwischen", solange du den Link nicht
verschickt hast.

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
Sitemap aus. Seit der Katalog ohne Passwort erreichbar ist, ist das wichtiger als vorher:
das „nicht indexieren“ hält Google zwar aus den Suchergebnissen, die Sitemap würde die
Adresse aber trotzdem melden.

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

Gilt nur, wenn der Passwortschutz wieder eingeschaltet ist.

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

Ohne Passwortschutz bekommst du dort die Artikelliste (beginnt mit `{"ok":true`) — dann
ist die Schnittstelle offen und die Ursache liegt woanders. Ist der Passwortschutz
eingeschaltet, kommt stattdessen eine kurze Sperrmeldung. Worauf es ankommt, ist **welche**
Antwort kommt:

| Was da steht | Was es bedeutet |
|---|---|
| `{"ok":true,…` oder `{"ok":false,"gesperrt":true}` | Die Schnittstelle ist offen, der Katalog antwortet. Ursache liegt woanders — weiter mit Punkt 3. |
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

Unter **Artikelkatalog → Reservierungen** siehst du alle Vorgänge mit Kontaktdaten, Anschrift,
Besichtigungs- und Abholwunsch. Der Ablauf:

1. **reserviert** — läuft nach 3 Werktagen von selbst ab. Du rufst an.
2. **bestellt** — nach dem Anruf anklicken. Ab dann läuft die Reservierung nicht mehr ab.
3. **Bestellung erstellen** — *Unternehmen* oder *Privatperson* wählen, drucken oder als PDF
   speichern, unterschreiben lassen (Unternehmen per Scan, Privatpersonen vor Ort).
4. Rechnung aus DATEV, Abholtermin im Feld daneben eintragen.
5. **bezahlt** — nach Zahlungseingang. Die Artikel verschwinden aus dem Katalog.

Nimmt jemand nur einen Teil, stornierst du die übrigen Positionen einzeln — sie sind sofort
wieder im Katalog. *Frist verlängern* gibt weitere 3 Werktage.

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
