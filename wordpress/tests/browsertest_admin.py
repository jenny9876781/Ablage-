"""Browsertest Reservierungsliste 1.10.0: Live-Suche, Filter „kommissioniert“, Häkchen im Hintergrund.

Die Seite erzeugt test-logik.php (Abschnitt 49):

    KIK_SEITE_HTML=/tmp/kik-seite.html php test-logik.php
    python3 browsertest_admin.py /tmp/kik-seite.html
"""
import sys, json, re
from playwright.sync_api import sync_playwright

CHROME = '/opt/pw-browsers/chromium'
html = open(sys.argv[1], encoding='utf-8').read()
seite = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + html + '</body></html>'
fehler = 0


def pruefe(text, ist, soll):
    global fehler
    ok = ist == soll
    fehler += 0 if ok else 1
    print(('  ok   ' if ok else '  FEHL ') + text + ('' if ok else f'   ist: {ist!r}  soll: {soll!r}'))


aufrufe = []
def antwort(route):
    url = route.request.url
    aufrufe.append(url)
    an = '&an=1' in url
    route.fulfill(status=200, content_type='application/json',
                  body=json.dumps({'ok': True, 'stand': 'ja' if an else 'teilweise', 'x': 1, 'y': 1,
                                   'text': '📦 kommissioniert' if an else '📦 teilweise (0/1)'}))


with sync_playwright() as p:
    b = p.chromium.launch(executable_path=CHROME)
    s = b.new_page()
    s.route('https://kikripp.de/wp-admin/admin.php*', lambda r: r.fulfill(status=200, content_type='text/html; charset=utf-8', body=seite))
    s.route('https://kikripp.de/wp-admin/admin-post.php*', antwort)
    s.route('https://kikripp.de/favicon.ico', lambda r: r.fulfill(status=404, body=''))
    js_fehler = []
    s.on('pageerror', lambda e: js_fehler.append(str(e)))
    s.goto('https://kikripp.de/wp-admin/admin.php?page=kikripp-reservierungen&reiter=abholung')

    def sichtbar():
        return s.eval_on_selector_all('#kik-tabelle tr.kik-zeile', 'zs => zs.filter(z => z.style.display !== "none").map(z => z.dataset.id)')

    anfang = sichtbar()
    pruefe('Reiter zeigt Vorgänge', len(anfang) > 0, True)
    mueller = s.eval_on_selector('tr[data-such*="mueller"]', 'z => z.dataset.id')
    s.fill('#kik-suche', 'Mueller')
    treffer = sichtbar()
    pruefe('Tippen „Mueller“ findet Frau Müller', mueller in treffer and all('mueller' in s.get_attribute(f'#vorgang-{i}', 'data-such') for i in treffer), True)
    pruefe('Trefferzeile', f'in allen Reitern: {len(treffer)}' in s.inner_text('#kik-treffer'), True)
    pruefe('Reiter und Telefon sichtbar', s.is_visible(f'#vorgang-{mueller} .kik-such'), True)
    pruefe('kein Reiter aktiv beim Suchen', s.eval_on_selector_all('.nav-tab-active', 'a => a.length'), 0)
    s.fill('#kik-suche', 'GARDEROBE')
    pruefe('Suche nach Bezeichnung', mueller in sichtbar(), True)
    s.fill('#kik-suche', 'storno kunde')
    pruefe('Vorgang aus anderem Reiter gefunden', len(sichtbar()), 1)
    s.fill('#kik-suche', 'xyzgibtsnicht')
    pruefe('nichts gefunden → Hinweis', s.is_visible('#kik-leer'), True)
    s.press('#kik-suche', 'Escape')
    pruefe('Esc setzt zurück', sichtbar(), anfang)
    pruefe('Reiter wieder aktiv', s.eval_on_selector_all('.nav-tab-active', 'a => a.length'), 1)
    s.select_option('#kik-kommi', 'nein')
    pruefe('Filter „noch nicht“ blendet Müller aus', mueller in sichtbar(), False)
    pruefe('Filter steht in der Adresse', 'kommi=nein' in s.url, True)
    pruefe('Filter geht in die Reiter-Links', 'kommi=nein' in s.get_attribute('#kik-reiter a[data-reiter="alle"]', 'href'), True)
    s.select_option('#kik-kommi', 'ja')
    pruefe('Filter „ja“ zeigt Müller', mueller in sichtbar(), True)
    s.select_option('#kik-kommi', '')
    # Häkchen
    s.click(f'#auf-{mueller}')
    box = s.locator(f'input.kik-kommi-{mueller}').first
    war = box.is_checked()
    box.click()
    s.wait_for_timeout(300)
    pruefe('Häkchen ruft im Hintergrund auf', len(aufrufe), 1)
    pruefe('… mit Position und ajax', bool(re.search(r'was=kommi.*&pid=\d+&an=' + ('0' if war else '1') + '&ajax=1', aufrufe[-1])), True)
    pruefe('Kennzeichen aktualisiert', s.inner_text(f'#kommi-badge-{mueller}'), '📦 teilweise (0/1)' if war else '📦 kommissioniert')
    pruefe('Zeile kennt den neuen Stand', s.get_attribute(f'#vorgang-{mueller}', 'data-kommi'), 'teilweise' if war else 'ja')
    pruefe('keine JavaScript-Fehler', js_fehler, [])
    b.close()

print(f'\n== Browsertest Liste: {fehler} Fehler ==')
sys.exit(1 if fehler else 0)
