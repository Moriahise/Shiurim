# Quellenanbindung · Sanhedrin und Sefaria

**Stand: 16.10.2026.** Die Verbindung ist ausschließlich lesend. Geändert wird nur `Moriahise/Shiurim`; die Repositories Sanhedrin und sefaria-studio sowie ihre Daten und Workflows werden nicht verändert.

## Was angeschlossen ist

1. **Sanhedrin:** der veröffentlichte versionierte Export unter `https://shekhina.org/`, mit Rückfalladresse `https://moriahise.github.io/Sanhedrin/`. Die aktuelle Messung meldet 70.875 Datensätze. Die Suche erfasst Titel, Fragen und Antworten über dieselben Token-Shards wie das Originalfrontend. Volltexte werden einzeln anhand der dauerhaften öffentlichen ID geladen.
2. **Sefaria:** der öffentliche Google-Cloud-Storage-Export `https://storage.googleapis.com/sefaria-export/`. Die Vorarbeit in `Moriahise/sefaria-studio` wurde geprüft und ihre exakten Export-URL-Strukturen übernommen. Es handelt sich um Google Cloud Storage, nicht um Google Docs.
3. **Sefaria-Werkkatalog:** aktuell 6.464 unterschiedliche Werke, mit verfügbaren englischen/hebräischen Exportfassungen. Das sind Werke, nicht die Zahl aller Versionen oder Einzelabschnitte. Die genaue Zahl und das Katalogdatum werden im lokalen Katalog gespeichert. Hebräische Titel stammen aus dem offiziellen Sefaria-Inhaltsverzeichnis.
4. **Genaue Sefaria-Fundstellen:** die offizielle Text-API löst Referenzen wie `Rashi on Genesis 6:9:1` auf. Verwendet wird die tatsächlich zurückgegebene kanonische Referenz samt benannter Textversion und Lizenzangabe.

Der aktuelle offizielle Sefaria-Index hat Vorrang. Die vorbereitete `books.json` aus `Moriahise/sefaria-studio` ist Rückfallquelle. Die geprüfte Studio-Vorarbeit stammt aus Commit `2ec0d90ad4905ade342e575a218038b6becd08cf`; die dortige Indexkopie vom Juli ist älter als der aktuell erreichbare offizielle Oktober-Index. Der Einsatz einer neueren Indexfassung verändert das Studio nicht.

## Quellenansicht im Browser

Unter `sources/` gibt es eine eigene EN/HE-Quellenansicht:

- Gemeinsame Abfrage mit Auswahl beider oder einer einzelnen Bibliothek.
- Sanhedrin: Volltextsuche, Gewichtung und kontrollierte Synonyme, hebräische Suche ohne Niqqud. Es werden bis zu zwölf Ergebnisse je Bibliothek angezeigt; die Trefferzahl bezieht sich auf die gesamte gefundenen Menge.
- Sefaria: Suche nach englischen und hebräischen Werktiteln und Kategorien. Dies ist keine Volltextsuche über den gesamten externen Sefaria-Korpus.
- Ein ausgewähltes Ergebnis lässt sich in der Seite lesen. Alle vorhandenen Sanhedrin-Antworten und ihre Zuordnung bleiben im Dossier erhalten.
- Sefaria wie im Studio durchblättern: Kategorie wählen, alle zugehörigen Bücher sehen und bei Bedarf nach englischen oder hebräischen Titeln filtern. Die Liste ist nicht auf zwölf Treffer begrenzt. Nach der Buchauswahl erscheinen Kapitel, Talmudseiten oder benannte Werkteile automatisch. Optionale weitere Auswahllisten grenzen bis zum Vers oder Kommentar ein; die Referenz entsteht automatisch. Die manuelle Eingabe bleibt ausklappbar verfügbar.
- Die Auswahl liest `/api/shape/` und `/api/v2/raw/index/` ausschließlich per GET. Die Werkstruktur bestimmt die Adressierung, einschließlich `2a`/`2b` für Talmud und Kommentare. Bei fehlender Strukturinformation, Sonderadressierung oder Offsets bleiben benannte Werkteile auswählbar; es werden keine Zahlenreferenzen geraten. Strukturfehler haben eine sichtbare Wiederholungsoption.
- Die gewünschte Textsprache wählen und den ausgewählten Abschnitt lesen. Tatsächlich aufgelöste Fundstelle und Version werden angezeigt.
- Direkter Link zur ausgewählten Google-Exportdatei. Der Browser muss hierfür keinen CORS-Zugriff auf den Bucket erhalten. Der integrierte Sefaria-Leser verwendet die Referenz-API; bei fehlendem Text erscheint eine Fehlermeldung. Der direkte Exportlink bleibt nach der Buchauswahl auch bei einem Ausfall der Abschnitts- oder Text-API verfügbar.
- Quellen-Dossier als JSON herunterladen, mit Text, Herkunft, Autor-/Antwortzuordnung, Version, Lizenz, Abrufdatum und Textprüfsumme.

Die Oberfläche benötigt JavaScript für die externe Recherche. Veröffentlichte Schiʿurim und bereits eingebaute Quellen bleiben davon unabhängig lesbar. Ein Netz- oder CORS-Fehler wird sichtbar gemeldet und nicht als „keine Quellen vorhanden“ ausgegeben.

## Nutzung in der Redaktion

Die Python-Adapter stehen ebenfalls dem Erstellungsprozess zur Verfügung:

```bash
# Offizielle Werkliste aktualisieren; geprüfte vorhandene Kopie bei Ausfall erhalten
python tools/source_hub.py sync

# Erreichbarkeit von Sanhedrin und eines Google-Exportbuchs prüfen
python tools/source_hub.py health

# Fragen und Antworten im Sanhedrin-Volltext suchen
python tools/source_hub.py search --provider sanhedrin --query "Noah"
python tools/source_hub.py search --provider sanhedrin --query "מוקצה"

# Sefaria nach Werktiteln durchsuchen
python tools/source_hub.py search --provider sefaria --query "Ben Yehoyada" --language Hebrew

# Einen vollständigen Sanhedrin-Datensatz für die Redaktion sichern
python tools/source_hub.py capture --provider sanhedrin --id ye-28010

# Eine präzise Sefaria-Fundstelle sichern
python tools/source_hub.py capture --provider sefaria --ref "Rashi on Genesis 6:9:1" --language Hebrew
```

Recherchekopien werden ausschließlich unter dem ignorierten lokalen Verzeichnis `drafts/sources/` abgelegt. Sie werden nicht in den Website-Export kopiert und nicht automatisch in eine Ausgabe aufgenommen. Das Browser-Dossier wird lediglich auf den Rechner des Nutzers heruntergeladen.

Für die tatsächliche Verwendung im Schiʿur prüft die Redaktion Text, Kontext, Relevanz, Zuordnung der Meinungen und Nutzungsbedingungen. Eine ausgewählte Quelle kann danach unter `content/sources/` aufgenommen und in den passenden `source_ids`/Abschnittsverweisen einer Ausgabe eingetragen werden. Der Quellenvalidator unterstützt nun sowohl die bisherigen hebräischen Primärtexte als auch eindeutig zugeordnete EN/HE-Quellen aus den angeschlossenen Bibliotheken.

Der Quellenanschluss allein erzeugt keinen neuen Lehrtext und stellt keine fachliche Freigabe dar. Die vorhandene Pilot-Ausgabe wurde durch den Anschluss nicht inhaltlich umgeschrieben.

## Sicherheit und Betrieb

- Externe Requests sind ausschließlich `GET`; keine Schreib- oder Administrationsschnittstelle zu Sanhedrin oder Sefaria wird verwendet.
- Festgelegte HTTPS-Hosts und Pfadbereiche; Redirects außerhalb dieser Bereiche werden im Python-Adapter abgewiesen.
- Größen-, Laufzeit- und Requestbudgets begrenzen Abrufe. Es wird nicht der gesamte externe Textkorpus heruntergeladen.
- Eine Sanhedrin-Abfrage bleibt innerhalb desselben `data_base`-Release. Fehlende Release-Dateien führen zu einem erkennbaren Fehler statt einer unbemerkten Vermischung von Versionen.
- Externes HTML wird zu Klartext verarbeitet. Die Browseransicht setzt Texte mit `textContent`, nicht mit fremdem `innerHTML`, ein.
- Ursprüngliche IDs, URLs, Autoren, unterschiedliche Antworten und Lizenzangaben bleiben im Dossier erhalten. Unbekannte Lizenzen bleiben `unrecorded`.
- Zusammengeführte Sefaria-Exportfassungen dienen der Recherche. Für ein Zitat wird die genaue Referenz einschließlich Textversion aus der API erfasst; eine beliebige Position im Export wird nicht als erfundene talmudische Daf-Adresse ausgegeben.
- Der komprimierte eigene Werkkatalog ist als letzte geprüfte Kopie im Shiurim-Repository enthalten. Beim Build wird nur diese Metadatenliste für den Browser entpackt. Die eigentlichen Bücher verbleiben beim Anbieter.
- Der Publish-Workflow aktualisiert die Metadaten und schreibt einen Verbindungsbericht, bevor er den bisherigen normalen Build ausführt. Scheitern externe Indexabrufe, bleibt der vorhandene gültige Katalog erhalten. Ein Quellenausfall löscht keine veröffentlichte Ausgabe.
- `automatic_publication` bleibt unverändert auf `false`; die Anbindung schaltet keine reguläre Wochenveröffentlichung und keinen KI-Autor ein.

## Tatsächlich geprüft

33 automatisierte Tests einschließlich der bisherigen Publikationsprüfungen. Neue Prüfungen decken GET-only-Transport, Request- und Größenlimits, URL-Grenzen, hebräische Suchnormalisierung, Suchschnittmengen, Synonyme, Release-Bindung, Rückfalladresse, vollständige Antworten, Autorzuordnung, falsche Locator-Pfade, exakte Exportlinks, präzise Sefaria-Referenzen und unbekannte Lizenzen ab.

Reale Leseproben: Sanhedrin-Suche nach `Noah`, Übernahme des Datensatzes `ye-28010`, genaue Fundstelle `Rashi on Genesis 6:9:1`, offizieller Oktober-Werkkatalog und hebräischer Genesis-Export aus Google Cloud Storage. Die beiden Forschungsdossiers verbleiben lokal und wurden nicht veröffentlicht. Eine vollständige Browserabnahme steht mangels unterstützter Browser-Testumgebung weiterhin aus.

## Prüfung der Kategorienauswahl

`node --test tests/test_sefaria_navigation.cjs tests/test_source_picker.cjs` prüft die Referenzbildung für Kapitel und Verse, Talmudblätter, verschachtelte Kommentare, komplexe benannte/default Werkteile und den sicheren Rückfall bei fehlender oder nicht unterstützter Adressinformation. Zusätzliche Zustandsprüfungen decken vollständige Trefferlisten, hebräische Suche, überholte asynchrone Antworten und Wiederholung nach einem Fehler ab. Reale GET-Leseproben bestätigten `Genesis 6:9`, `Shabbat 2a:1`, `Rashi on Genesis 6:9:1`, `Rashi on Shabbat 2a:1:1` und `Ben Ish Hai, Introduction 1` als kanonische Referenzen. Eine vollständige visuelle Browserabnahme ist damit nicht ersetzt. Beide GitHub-Workflows führen diese Prüfungen zusätzlich zu den bisherigen Python-Prüfungen aus.
