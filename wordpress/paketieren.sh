#!/bin/sh
# Packt das Plugin zu einer ZIP-Datei, wie WordPress sie beim Hochladen erwartet.
set -e
cd "$(dirname "$0")"
ziel="../ausgabe/kikripp-katalog.zip"
rm -f "$ziel"
zip -r -q "$ziel" kikripp-katalog -x '*.DS_Store' -x '__MACOSX/*'
echo "geschrieben: $(cd .. && pwd)/ausgabe/kikripp-katalog.zip"
unzip -l "$ziel" | tail -3
