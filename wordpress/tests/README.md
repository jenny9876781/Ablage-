# Tests für das Plugin kikripp-katalog

In dieser Umgebung gibt es kein WordPress und kein MySQL. Beide Tests laufen deshalb
gegen `wp-attrappe.php` – einen Ersatz, der `$wpdb` auf SQLite abbildet und die rund
25 gebrauchten WordPress-Funktionen nachstellt. Getestet wird **der echte Plugin-Code**,
nichts ist nachgebaut.

## Logiktest

```bash
php tests/test-logik.php          # 43 Prüfungen
```

Teil- und Vollreservierung, Überbuchung, Preiseinfrieren, Stornieren, Ablauf und
Verlängerung, Bezahltsetzen, Mailversand samt Fehlerfall, Testdaten löschen, ungültige
Eingaben, stillgelegte Artikel.

## Browsertest

```bash
rm -f /tmp/kikripp-web.sqlite /tmp/kikripp-optionen.json /tmp/kikripp-mails.log
mkdir -p /tmp/kikweb
ln -sf "$PWD/kikripp-katalog/assets" /tmp/kikweb/assets
ln -sf "$PWD/../fotos"               /tmp/kikweb/fotos
cd tests && KIK_TEST_PW=... php -S 127.0.0.1:8801 -t /tmp/kikweb server.php &
python3 tests/browsertest.py       # 36 Prüfungen
```

`server.php` bedient die **echten** REST-Rückrufe über SQLite und schreibt alle Mails
nach `/tmp/kikripp-mails.log`. Der Browsertest steuert Chromium über Playwright:
Anmeldung mit falschem und richtigem Passwort, 142 Artikel mit Fotos, Mengenbegrenzung,
der Knopf „reservieren", die Stückzahl in der Fußleiste, eine vollständige Reservierung
und der Bestand danach. Screenshots landen in `/tmp/kikweb/t0*.png`.

> Ändert sich das Datenbankschema, `SCHEMA_VERSION` hochzählen **und** die Dateien unter
> `/tmp` löschen – die Attrappe kennt kein `ALTER TABLE`.
