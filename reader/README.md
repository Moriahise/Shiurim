# Rabbiner-Porträts für Shiurim

Die öffentliche Pages-Erstellung ergänzt jede veröffentlichte Ausgabe um ein dauerhaft zugeordnetes Porträt mit dem Namen aus der Sanhedrin-Sammlung. Das Bild erscheint auf der Startseite, in der Sammlung, am Lehrtext und am Quellenblatt. Die Bildunterschrift lautet „Rabbi portrait / דיוקן רב“; die redaktionelle Verfasserzeile „Shiurim“ bleibt erhalten.

Die Sammlung stammt aus `Moriahise/Sanhedrin/Rav`, Quellstand siehe `rabbis.json`. 71 Originaldateien enthalten 70 unterschiedliche Bilder: Die zwei Dateien von Refael Toledano sind identisch. Das Doppelbild wird nicht zweimal verwendet. Die Bilder werden lokal als WebP ausgeliefert; Originaldateiname, Git-Blob-Prüfsumme und Prüfsumme der Web-Datei sind im Manifest festgehalten.

Die Reihenfolge des Manifests ist fest. Tora-Abschnitte erhalten die festen Plätze 1–54; Doppelparaschot verwenden den Platz ihres ersten Abschnitts. Feiertage erhalten getrennte Plätze. Der folgende Jahreszyklus beginnt an einer anderen Stelle in der Sammlung. Vorhandene Veröffentlichungen oder später eingefügte frühere Ausgaben verschieben die Zuordnung nicht. Für die 55 Ausgaben des Zyklus 5787 sind 55 unterschiedliche Porträts vorgesehen.

`portraits.py` verarbeitet die Leserkopie aus `site/` und schreibt eine getrennte Veröffentlichungskopie nach `_site/`. Es fügt Bildkomponenten und eine eigene CSS-Datei hinzu. Lehrtext, Quellen und vorhandene Kopfelemente bleiben erhalten; nur das dekorative Ornament der hervorgehobenen Startseitenkarte wird durch das Porträt ersetzt. Die Datei `site/data/catalogue.json` bleibt unverändert.

Weitere Aktualisierungen verwalten ausschließlich `site/`. Deshalb bleibt diese Darstellung bei jeder weiteren Übertragung aktiv. Die vorhandene Prüfung der Eingabedateien bleibt vor dem Porträt-Schritt bestehen. Veröffentlicht wird ausschließlich `_site/`, nicht dieses Manifest, die Werkzeuge oder Tests.

Prüfen: `python3 -m unittest discover -s reader/tests -q`

Erstellen: `python3 reader/portraits.py --source site --output _site`
