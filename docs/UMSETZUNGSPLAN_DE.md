# Schiʿurim · שיעורים
## Umsetzungs- und Redaktionsplan v1.0

**Projekt:** neue englisch-hebräische Lehrabteilung im Umfeld von shekhina.org / Sanhedrin  
**Stand:** 16. Oktober 2026  
**Status:** Planung; keine Website, Repository-Einstellung, Datenbank oder Automation verändert.

## 1. Empfohlene Entscheidung

Eine eigenständige Abteilung **Weekly Shiur · שיעור השבוע** mit genau einer neuen zweisprachigen Lehreinheit pro Woche. Die Parascha bildet den zeitlichen Rahmen; Feiertage haben redaktionell Vorrang. Innerhalb dieses Rahmens wechseln Textauslegung, Halacha, Mussar und Mikdash. Jede Einheit verfolgt eine klare Frage, entwickelt einen belegten Gedankengang und bietet zusammengehörige englische und hebräische Fassungen.

Für den Bestandsschutz empfehle ich ein eigenes Repository mit eigenem Datenbestand, eigenen Zugangsdaten und eigenem Veröffentlichungsweg. Die bestehende Responsa-Plattform liefert bei Bedarf ausschließlich lesbare, versionierte Quellenkopien. Der neue Dienst bekommt keine Schreibberechtigung auf Sanhedrin.

Die erste Ausbaustufe ist eine hochwertige Text- und Quellenplattform. Tonaufnahmen und Video sind spätere Erweiterungen. Der Begriff Schiʿur verpflichtet nicht dazu, von Anfang an eine künstliche Vortragsperson oder Videoproduktion einzuführen.

**Zielbild:** ein redaktionell durchdachtes digitales Beit Midrash, dessen wöchentlicher Betrieb nach einem erprobten Start weitgehend selbständig läuft. Bei belegbaren technischen oder inhaltlichen Problemen unterbleibt die neue Veröffentlichung; die letzte geprüfte Ausgabe bleibt lesbar.

## 2. Was tatsächlich geprüft wurde

### Vorhandene Unterlagen

Gelesen wurden die einschlägigen Architektur-, Speicher-, Integrations- und Uploadbeschreibungen aus den beigefügten Q&A-Vorarbeiten sowie README und ausgewählte Dienste des ZIP-Archivs `HebrewTranscriptStudio_v2.1_ProjectHistory.zip`. Die Dateistruktur des ZIPs wurde geprüft. Die Anwendungen und Migrationsskripte wurden nicht ausgeführt.

Die Q&A-Unterlagen vom Juli 2026 dokumentieren ältere Entwicklungsstände. Teile der Berichte beschreiben Testbestände. Solche Ergebnisse sind keine Bestätigung des heutigen Produktionszustands.

### Aktueller Repository-Stand

Zusätzlich wurden `README.md`, `docs/architecture.md`, `docs/operations.md` und die Root-`index.html` von `Moriahise/Sanhedrin` lesend abgerufen.

Die aktuellen Unterlagen beschreiben eine modernisierte Plattform mit SQLite als dauerhaftem Publikationszustand, geprüften Wiederherstellungssicherungen über GitHub Releases und einem statischen Export nach `dist`. Ein bestehender Publisher übernimmt Sammlung, Prüfung, Sicherung und Veröffentlichung. Die ursprünglichen Root-HTML-Dateien dienen laut Dokumentation als Rückfallweg.

**Folgerung:** Eine Änderung der Root-`index.html` allein wäre kein nachgewiesener Eingriff in die produktiv erzeugte Startseite. Ebenso darf ein zweiter Pages-Publisher im selben bestehenden Projekt nicht unabhängig eine Teilwebsite veröffentlichen: Er könnte den vollständigen bisherigen Veröffentlichungsstand ersetzen.

Der direkte Abruf von `https://shekhina.org/teshuva.html` über den Webzugriff war nicht möglich; der Dateiabruf `teshuva.html` im Repository-Root lieferte 404. Daraus folgt weder, dass die Live-Seite fehlt, noch dass ihre Funktion defekt ist. Ihre tatsächlich erzeugte Vorlage und der aktive Deployment-Stand müssen vor einer späteren visuellen Integration ermittelt werden.

## 3. Nutzung deiner Vorarbeiten

| Vorbereitung | Nutzbarer Beitrag | Umgang im neuen Projekt |
|---|---|---|
| Q&A-Architektur und Datenstruktur | kleine Indizes, getrennte Inhalte, stabile Identitäten, zweisprachige Metadaten | Prinzipien übernehmen; eigenes Schiʿur-Schema entwickeln |
| Leselogik und Suchfunktionen | bedarfsgesteuertes Laden, Sprachbehandlung, Suchnormalisierung | gezielt neu kapseln; keine vorhandenen globalen Skripte verändern |
| Upload- und Validierungskonzepte | Duplikatprüfung, Konsistenz, begrenzte Schreibbereiche | eigener Validator und ausschließlich eigene Speicherziele |
| Transcript Studio: Projekt- und Versionsdienst | unveränderliche Bearbeitungsstände, Manifest, Exporte | Konzept für Ausgaben und Korrekturen übernehmen; veröffentlichte Revisionen erhalten |
| Transcript Studio: Übersetzungsdienst | Abschnittsverarbeitung, Hinweise, gezielte Nachbearbeitung | für EN/HE adaptieren; Lehrtexte erfordern zusätzliche Quellen- und Argumentationsprüfung |
| Transcript Studio: YouTube/Audio/SRT | Transkriptbezug und späterer Medienexport | optionale spätere Medienbrücke |
| Migration und Cleanup | historische Bestandsarbeiten | für den Schiʿur-Aufbau nicht ausführen |

Das ZIP ist eine lokal betriebene Python-Webanwendung zur Transkriptbearbeitung. Es enthält keine fertige wöchentliche Lehrredaktion. Sein Server und seine schreibbaren Projektordner werden nicht in den öffentlichen Responsa-Betrieb eingebaut. Vor jeder späteren Codeübernahme werden Lizenz, Abhängigkeiten, Schlüsselbehandlung und tatsächliche Modellverfügbarkeit geprüft; vorhandene Modellnamen werden nicht ungeprüft als gültige Konfiguration übernommen.

## 4. Schutz des Bestands und Einbindung

### Empfohlene Betriebsgrenze

Neues Repository, vorgeschlagener Name: `Moriahise/Shiurim`. Vorgeschlagene erste Adresse: `https://moriahise.github.io/Shiurim/`. Beides ist ein Planungsname, noch nicht angelegt oder veröffentlicht.

Für eine spätere Markenadresse kommt beispielsweise `shiurim.shekhina.org` infrage. Dies erfordert eigene DNS- und Hosting-Konfiguration und ist kein Bestandteil der gegenwärtigen Planungsausführung.

| Bereich | Geplante Grenze |
|---|---|
| bestehende Website und Teshuva | keine Codeänderung während Entwicklung und Pilotbetrieb |
| bestehende Datenbanken, Sicherungen und Imports | weder Migration noch Schreibzugriff durch Schiʿurim |
| vorhandene Workflows und Secrets | keine Wiederverwendung ihrer Schreibrechte; eigene Konfiguration |
| neue Quellenanbindung | nur lesend; bevorzugt geprüfte Exportkopien statt Zugriff auf die aktive Datenbank |
| neue Veröffentlichung | ausschließlich eigenes Ziel, eigene Sicherungen und eigener Rücksprung |
| Gestaltung | Farben und Typografie aufnehmen, benötigte Stile lokal kapseln |
| Fehler im neuen System | letzte geprüfte Ausgabe erhalten; keine Aktion am Sanhedrin-Publisher |

Repository-Berechtigungen werden auf das neue Projekt begrenzt. Eine reine Codekonvention genügt nicht: Die technische Zugangskonfiguration soll Änderungen am alten Repository ausschließen. Gemeinsame Anbieter- oder Kontostörungen bleiben möglich; technische Trennung ist keine Garantie gegen jede externe Störung.

**Einbindung bedeutet eine bewusste Ausnahme von „nichts verändern“:** Wenn die bestehende Startseite einen neuen sichtbaren Abteilungslink erhalten soll, muss ihre aktive Vorlage gezielt ergänzt werden. Bei absolut null Änderungen bleibt die neue Abteilung über ihre eigene Adresse erreichbar. Im Plan gilt zunächst diese strenge Variante. Eine spätere Navigationskarte ist ein eigener, kleiner und rücknehmbarer Änderungsschritt.

Falls später zwingend `shekhina.org/shiurim/` gewünscht wird, muss der bestehende alleinige Publisher die geprüften neuen Dateien in seinen vollständigen Export aufnehmen. Das wäre eine gesonderte Integrationsentscheidung mit Bestandsprüfungen. Ein neuer unabhängiger Pages-Deployment-Job im alten Repository ist dafür ungeeignet.

## 5. Themenkonzept: geordneter Mix mit Parascha-Rahmen

| Modell | Stärke | Grenze |
|---|---|---|
| ausschließlich Parascha | erkennbarer Wochenbezug, natürlicher Jahresgang | wichtige systematische Themen können zu kurz kommen |
| freie Themenfolge | große Vielfalt | schwächerer Zusammenhang und Wiederholungsgefahr |
| Parascha und Jahreskreis mit Schwerpunktwechsel | Orientierung, Abwechslung und Lernfortschritt | braucht einen kuratierten Themenplan |

**Empfehlung:** das dritte Modell. Pro Woche gibt es einen Hauptgedanken und einen Hauptschwerpunkt. Ein Zusammenhang zur Parascha wird nur verwendet, wenn die Quellen ihn tragen.

Die regulären Ausgaben wechseln zwischen:

1. **Tanach und Auslegung:** eine textnahe Frage und ausgewählte klassische Kommentare.
2. **Halacha und Sugya:** ein begrenzter Begriff oder eine klar abgegrenzte Streitfrage mit nachvollziehbarer Quellenentwicklung.
3. **Mussar und Avodat HaShem:** Charakter, Verantwortung, Gebet oder zwischenmenschliches Handeln.
4. **Mikdash und jüdisches Gemeinwesen:** Textgrundlagen, Avodah, Jerusalem, Recht und öffentliche Verantwortung.

Feiertagsausgaben ersetzen einen regulären Slot; danach wird die Rotation fortgesetzt. Feiertage erzeugen keine zusätzliche zweite Wochenausgabe. Vertiefte Kabbalah gehört in eine ausdrücklich gekennzeichnete spätere Reihe mit geeigneter fachlicher Betreuung.

### Auswahlregeln

- Ein vorab kuratierter Jahresrahmen enthält Saison, Schwerpunkt, Lernziel und geeignete Quellenfelder. Ein rollierender Acht-Wochen-Plan konkretisiert Titel und Quellen; die nächsten zwei Ausgaben sind möglichst bereits geprüft.
- Kommender Feiertag und tatsächlich bevorstehende Lesung haben Vorrang vor einer starren Monatszählung.
- Israel ist der vorgeschlagene redaktionelle Hauptkalender. Ein abweichender Diaspora-Leseplan wird sichtbar ausgewiesen, ohne automatisch eine zweite Lehreinheit zu erzeugen.
- Doppelparaschijot, Schaltjahre, Schabbat mit Festlesung und die Wochen um Simchat Torah werden ausdrücklich behandelt. Eine Festlesung darf nicht durch eine erfundene Wochenparascha ersetzt werden.
- Die Wiederholung desselben Hauptthemas wird anhand von Themen-ID und Lernziel erkannt. Jahresübergreifende Wiederaufnahme ist mit neuer Fragestellung möglich.
- Geprüfte Quellenverfügbarkeit ist ein Auswahlkriterium. Ein attraktiver Titel ohne belastbare Quellen wird nicht produziert.

### Zwölf mögliche Pilotfragen

Diese Fragen sind illustrative Kandidaten, kein datierter Kalender und noch keine geprüften Quellendossiers:

| Schwerpunkt | Mögliche Leitfrage |
|---|---|
| Textauslegung | Was bedeutet Verantwortung für den Mitmenschen? |
| Halacha | Wie unterscheiden sich Mitzvah, Minhag und persönliche Praxis? |
| Mussar | Wie wird aus guter Absicht verlässliches Handeln? |
| Mikdash | Welche Aufgabe haben Reinheit und Vorbereitung im Tempeldienst? |
| Textauslegung | Wie werden Bund und Verpflichtung im Text entfaltet? |
| Halacha | Wie entsteht aus einer Sugya eine halachische Einordnung? |
| Mussar | Welche Bedeutung hat Kavvanah im Gebet? |
| Gemeinwesen | Was verlangt gerechtes Richten? |
| Textauslegung | Was macht eine Gemeinschaft zu einer verantwortlichen Gemeinschaft? |
| Halacha | Wie werden unterschiedliche überlieferte Auffassungen dargestellt? |
| Mussar | Wie hängen Lernen und Handeln zusammen? |
| Mikdash | Welche Bedeutung hat Jerusalem als Ort des Lernens und Dienstes? |

Erst nach Kalender- und Quellenprüfung werden passende Wochen zugeordnet. Für die tatsächliche erste Ausgabe wird die dann bevorstehende Lesung ermittelt.

## 6. Aufbau einer Lehreinheit

Zielgruppe zum Start: interessierte Erwachsene mit unterschiedlichen Vorkenntnissen. Fachbegriffe werden bei erster Verwendung knapp erklärt; Vertiefungen bleiben zugänglich, ohne den Hauptgedankengang zu unterbrechen.

**Redaktioneller Zielumfang:** ungefähr 1.500–2.200 englische Wörter; die hebräische Fassung folgt demselben Inhalt in natürlichem rabbinischem Hebräisch. Die tatsächliche Lesezeit wird je Sprache berechnet. Wortzahl und Dauer sind Qualitätsziele, kein Grund für künstliche Fülltexte.

1. EN/HE-Titel, Ausgabe, Zielschabbat, Parascha beziehungsweise Fest und Lernziel.
2. Eine präzise Leitfrage mit verständlichem Einstieg.
3. Der zentrale Primärtext im Original mit genauer Referenz und gekennzeichneter Übersetzung.
4. Eine strukturierte Entwicklung über wenige gut gewählte weitere Quellen.
5. Abweichende Auffassungen mit korrekter Zuordnung und klaren Geltungsgrenzen.
6. Eine verständliche Synthese und ausdrücklich unterschiedene praktische beziehungsweise ethische Folgerungen.
7. Drei Wiederholungs- oder Gesprächsfragen.
8. Ein zweisprachiges Quellenblatt und weiterführende Literatur.

Richtwert: fünf bis acht tragende Quellen. Entscheidend ist ihr Beitrag zum Argument; die Mindestzahl darf keine künstlichen Belege erzeugen.

EN und HE bilden **eine Ausgabe mit gemeinsamer ID**. Jeder Abschnitt erhält einen stabilen Schlüssel. Beide Fassungen müssen dieselben Quellen, Einschränkungen und Schlussfolgerungen enthalten. Die Übersetzung darf keine zusätzliche Rechtsaussage einführen.

## 7. Quellen- und Qualitätsstandard

Die vorhandene Responsa-Sammlung kann geeignete Fundstellen erschließen. Ein Suchtreffer oder Exzerpt ist noch kein ausreichender Nachweis für eine Lehraussage. Für tragende Aussagen wird der passende Originalabschnitt überprüft und mit Werk, Stelle, Ausgabe beziehungsweise Textversion sowie Herkunft verknüpft.

### Pro Quelle zu speichern

Stabile Quellen-ID, präzise Fundstelle, ursprünglicher Autor, Werk, Textversion, Original-URL, Abrufzeit, verwendeter Ausschnitt, Textprüfsumme, Rechte-/Attributionsangaben und die zugehörigen Aussagen im Schiʿur. Wenn eine externe Quelle ausfällt, bleibt das bereits rechtmäßig gesicherte geprüfte Dossier nachvollziehbar.

### Redaktionelle Regeln

- Wörtliche Zitate, Übersetzungen, Paraphrasen und eigene Synthese bleiben unterscheidbar.
- Ein funktionierender Link beweist weder die Richtigkeit des Zitats noch die Tragfähigkeit einer Schlussfolgerung.
- Zitatabgleich erfolgt am gesicherten Text; eine zusätzliche Prüfung beurteilt, ob der Beleg die Aussage tatsächlich trägt.
- Meinungen werden nicht stillschweigend zu einer allgemeinen Halacha zusammengeführt. Abweichende Minhagim und relevante Voraussetzungen werden genannt.
- Lerntexte beanspruchen keine persönliche rabbinische Entscheidung. Besonders folgenreiche praktische Fragen werden für fachliche Prüfung angehalten.
- Kein Rabbiner wird als Autor, Sprecher oder Prüfer genannt, wenn er diese konkrete Rolle nicht tatsächlich innehat. Eine KI-Stimme oder ein Porträt darf keine persönliche Beteiligung suggerieren.
- Für EN wird ein verbindliches Glossar geführt, einschließlich HaShem, Berakhah, Halacha und Kavvanah; hebräische Originalzitate bleiben erhalten. Die genaue Namenskonvention wird im Pilot redaktionell festgelegt.

Automatische Prüfungen können Vollständigkeit, Format und viele Inkonsistenzen feststellen. Auch ein zweiter KI-Prüflauf ersetzt keine fachkundige Prüfung und garantiert keine fehlerfreie Halacha. Diese Grenze bestimmt die Freigabestufen.

## 8. Weg zum selbständigen Wochenbetrieb

### Stufe A · erprobter Pilot

Vier Ausgaben werden vollständig erzeugt, zweisprachig und fachlich geprüft. Veröffentlichung zunächst nach konkreter Freigabe. Dadurch werden Themenauswahl, Stil, Quellentiefe und Sprachqualität an echten Ergebnissen kalibriert.

### Stufe B · automatische Vorbereitung

Kalender, Quellenbeschaffung, Entwurf, Übersetzung und Prüfbericht laufen selbständig. Freigabe und Veröffentlichungsstatus bleiben nachvollziehbar. Fehler und begründete Zweifel führen in eine interne Prüfliste.

### Stufe C · kontrollierter autonomer Betrieb

Ausgaben aus vorab geprüften Themenplänen und Quelldossiers können nach bestandenen technischen und redaktionellen Kontrollen automatisch erscheinen. Neu erschlossene kontroverse oder praktisch folgenreiche Schlussfolgerungen bleiben prüfpflichtig. Bei Bedarf sichert eine bereits fachlich freigegebene Ersatzausgabe den Wochenrhythmus; sie darf als allgemeine Lehre gekennzeichnet werden und keine falsche Parascha-Zuordnung erhalten.

Zwei Betriebsziele sind zu unterscheiden: Automatisch neue Lehrtexte erzeugen bietet große Flexibilität, benötigt aber inhaltliche Ausnahmen und Überprüfung. Automatisch aus einem vorab fachlich geprüften Vorrat veröffentlichen bietet die höchste redaktionelle Verlässlichkeit. Für den Start empfehle ich den geprüften Vorrat mit anschließender schrittweiser Erweiterung.

## 9. Wochenablauf und Terminlogik

| Zeitpunkt, vorgeschlagen | Automatischer Arbeitsschritt |
|---|---|
| Sonntag | Zielschabbat, Festbezug und Themenplan bestimmen; Quelldossier vorbereiten |
| Montag/Dienstag | Hauptfassung erstellen, Quellenbezüge prüfen, zweite Sprache ausarbeiten |
| Mittwoch | EN/HE-Abgleich, Qualitätskontrollen und gegebenenfalls fachliche Freigabe |
| Donnerstag, ab 18:17 Uhr Israelzeit | genau eine freigegebene Ausgabe veröffentlichen |
| danach | Erreichbarkeit, Quellenverweise und Veröffentlichungszustand kontrollieren |

Diese Uhrzeiten sind Vorschläge. Bei Festtagen und einem vorher festgelegten publikationsfreien Zeitfenster wird rechtzeitig vorgezogen. Maßgeblich sind eine benannte Kalenderregion und geprüfte Zeitgrenzen; die Zeitzone allein bestimmt keine religiöse Tagesgrenze.

Die Logik verwendet `Asia/Jerusalem`. Der Ausgabenschlüssel hängt am Zielschabbat beziehungsweise der festgelegten Wochenperiode, nicht allein an der Parascha oder einer gregorianischen Wochennummer. Wiederholte Aufrufe erzeugen keine zweite öffentliche Ausgabe.

Der Zeitgeber prüft regelmäßig, ob eine Ausgabe fällig und bereits veröffentlicht ist. Ein begrenzter Nachhollauf verarbeitet verspätete Starts. GitHub dokumentiert mögliche Verzögerungen oder Ausfälle geplanter Läufe und die Deaktivierung öffentlicher Repository-Schedules nach 60 Tagen ohne Aktivität. Deshalb werden Aktualität überwacht und manuelle Wiederaufnahme sowie später bei Bedarf ein unabhängiger Zeitgeber vorgesehen. Es bleibt stets ein alleiniger Schreiber für den Veröffentlichungszustand.

## 10. Technischer Entwurf

### Eigene Bestandteile

| Bestandteil | Aufgabe |
|---|---|
| Kalenderadapter | zukünftige Lesung, Feste, Region und Zeitbezug ermitteln |
| Redaktionsplan | Jahresrahmen, Acht-Wochen-Vorschau, Rotation und Sperrthemen |
| Quellenadapter | zugelassene lokale beziehungsweise externe Texte lesend übernehmen |
| Dossier und Belegregister | gesicherte Textstellen mit Aussagen verbinden |
| Schreib- und Übersetzungsdienst | gemeinsame Gliederung, EN/HE-Fassungen und Glossar |
| Validatoren | Schema, Belege, Sprachgleichheit, Rechte, HTML und Publikationsregeln prüfen |
| statischer Export | Überblick, Einzelausgaben, Archiv und kompakte Suchdaten erzeugen |
| Publisher und Sicherung | vollständigen geprüften Stand veröffentlichen und Rücksprung ermöglichen |

Kalenderdaten können über Hebcal bezogen oder mit einer lokal eingebundenen Kalenderbibliothek ermittelt werden. Die offiziell dokumentierte Trennung zwischen Israel und Diaspora wird ausdrücklich genutzt. Version und Ergebnis werden im Ausgabedossier gespeichert. Für die Leser benötigt eine bereits veröffentlichte Ausgabe weder Kalender-API noch KI-Aufruf.

### Datenaufteilung

Ein interner Bereich enthält Themenpläne, Quellensicherungen, Entwürfe und Prüfberichte. Ein ausdrücklich freigegebener Export enthält nur veröffentlichte Ausgaben, Quellenblatt, erlaubte Medien und kleine Suchindizes. Ungeprüfte Entwürfe gelangen nicht durch versteckte Links oder mitkopierte Dateien in den öffentlichen Build. Falls das neue Repository öffentlich ist, müssen vertrauliche Redaktionsdaten in einen getrennten privaten Speicher.

Ein Ausgabedatensatz umfasst mindestens: Schema-Version, stabile ID, Revision, Zielschabbat, Kalenderregion, Parascha-/Fest-IDs, Thema, Lernziel, EN/HE-Titel, Abschnittspaare, Quellenregister, Prüfstatus, tatsächliche Prüferrollen, geplanten und tatsächlichen Veröffentlichungstermin sowie Erzeugungsparameter. Modell und Prompt-Version werden intern nachvollziehbar protokolliert.

Eine kleine Startdatei und ein kompakter Archivindex verweisen auf einzelne Ausgaben. Volltexte werden bedarfsgesteuert geladen. Für die Suche ist ein eigener kompakter Index vorgesehen, ohne das Responsa-Archiv im Browser zusätzlich herunterzuladen.

### Sicher veröffentlichen

Ein Lauf erstellt zuerst einen vollständigen Kandidaten. Veröffentlichung erfolgt erst nach bestandenen Prüfungen und gesicherter Wiederherstellungsfassung. Inhalt und dazugehöriger Index werden gemeinsam als ein geprüfter Stand ausgeliefert. Ein Lauf-Lock und eine erneute Statusprüfung verhindern Doppelpublikation. Veraltete parallele Läufe dürfen keinen neueren Stand überschreiben.

Korrekturen erhalten eine neue Revision unter derselben öffentlichen Identität; frühere Fassungen und das Änderungsprotokoll bleiben nachvollziehbar. Ein Schalter stoppt Erzeugung oder Veröffentlichung der neuen Abteilung. Der bestehende Sanhedrin-Betrieb wird dazu nicht angefasst.

### Schlüssel und Kosten

KI-Aufrufe finden ausschließlich im geschützten Erzeugungsprozess statt. Keine API-Schlüssel im Browser, Quelltext, Export oder öffentlichen Protokoll. Eigene Zugangsdaten und begrenzte Berechtigungen trennen den Dienst von bestehenden OpenAI-Funktionen.

Pro Ausgabe werden Token-, Laufzeit- und Kostenlimits sowie eine feste Obergrenze für Reparaturversuche definiert. Nach deren Erreichen wird angehalten. Die Webansicht veröffentlicht vorhandene Inhalte auch ohne laufenden KI-Dienst. Eine vorhandene freigegebene Ausgabe kann ohne neue KI-Verarbeitung terminiert erscheinen.

Ein belastbarer Eurobetrag wird erst nach Wahl verfügbarer Modelle und Messung der Pilotläufe festgelegt. Die Kalkulation umfasst Quelleinlesung, Entwurf, Übersetzung, Prüfung, begrenzte Wiederholungen, Hosting und gegebenenfalls spätere Audioverarbeitung. Fachliche Redaktionszeit wird getrennt ausgewiesen.

## 11. Oberfläche und Lesererlebnis

Die neue Abteilung erhält eine ruhige, hochwertige Buch- und Beit-Midrash-Gestaltung im Umfeld der bestehenden Marke. Zweisprachige Bedienung, gute Lesbarkeit und belastbare Quellenführung haben Vorrang vor Dekoration.

Auf der Einstiegsseite stehen die aktuelle Ausgabe, Leitfrage, Parascha/Fest, Datum, Lesezeit und der direkte Einstieg. Es folgen Archiv und Reihen. Filter umfassen Parascha, Thema, Jahr und Niveau. Jede Ausgabe besitzt eine stabile teilbare Adresse.

Der Lesebereich bietet EN, עברית und eine parallele Ansicht mit gekoppelten Abschnitten. Auf Mobilgeräten wird zwischen den Sprachfassungen desselben Abschnitts gewechselt; beide Sprachen bleiben direkt erreichbar. Die URL kann Sprache und Abschnitt mitführen. Quellenausschnitte sind aufklappbar, vollständige Belege bleiben zugänglich. Druckansicht und PDF-Quellenblatt unterstützen gemeinsames Lernen.

Prüfkriterien sind korrekte RTL/LTR-Mischung, Tastaturbedienung, sichtbarer Fokus, ausreichender Kontrast, skalierbare Schrift, verständliche Fehlermeldungen und gute Darstellung auf kleinen Bildschirmen. Für veröffentlichten Text sind statische lesbare Seiten vorgesehen, damit Grundinhalt und Quellen auch ohne komplexe JavaScript-Oberfläche zugänglich bleiben.

Audio, SRT und eine Verbindung zum Transcript Studio sind Erweiterungen nach dem stabilen Textbetrieb. Es werden keine Stimmen geklont oder Rabbiner als künstliche Vortragende dargestellt. Benachrichtigungen, Newsletter und automatische YouTube-Veröffentlichung gehören nicht zum ersten Umfang.

## 12. Umsetzungsphasen und Abnahme

| Phase | Konkretes Ergebnis | Voraussetzung für den nächsten Schritt |
|---|---|---|
| 1 · Bestandsgrenze | aktive Veröffentlichung und gewünschte Einstiegsmöglichkeit dokumentiert; Rechte getrennt | kein Schreibpfad zum Altbestand |
| 2 · Redaktion | Kalenderregel, Glossar, Ausgabenstruktur und Acht-Wochen-Plan | eine vollständig geprüfte Musterausgabe EN/HE |
| 3 · eigenständige Oberfläche | aktuelle Ausgabe, Archiv, Lesemodi, Quellen- und Druckansicht | Mobil-, Sprach- und Zugänglichkeitsprüfung |
| 4 · Produktion | Erzeugung, Übersetzung, Prüfbericht, Sicherung und Wiederaufnahme | Wiederholung und Ausfallfälle ohne Doppelpublikation bestanden |
| 5 · Pilot | vier geprüfte Ausgaben mit gemessener Qualität und Kosten | dokumentierte fachliche und technische Abnahme |
| 6 · autonomer Betrieb | Wochenplan, Überwachung, Vorrat und definierte Prüfausnahmen | neue Abteilung allein abschalt- und wiederherstellbar |
| 7 · optionaler Einstieg | gezielte Navigationskarte in der aktiven Hauptseitenvorlage | gesonderter Auftrag für diese bestehende Datei/Integration |

Eine seriöse Aufwandsschätzung folgt nach Phase 1 und der ersten Musterausgabe. Die genannten Phasen sind Arbeitspakete, keine Zusage bestimmter Kalendertage.

### Verbindliche Abnahmefälle

1. Keine Schreibberechtigung des neuen Produktionsdienstes auf das bestehende Repository und seine Datenhaltung.
2. Ein simuliert fehlerhafter Schiʿur-Build beeinflusst die bestehende Website nicht.
3. Jede veröffentlichte Einheit besitzt vollständige EN/HE-Abschnitte mit übereinstimmenden Quellen und Aussagen.
4. Nicht vorhandene Fundstelle, falsches Zitat oder nicht belegte Schlussfolgerung führt zur Sperre beziehungsweise fachlichen Prüfung.
5. Doppelparaschijot, Festschabbat, Israel/Diaspora-Abweichung, Jahreswechsel und Zeitumstellung sind geprüft.
6. Derselbe Wochenlauf kann wiederholt werden, ohne eine zweite Ausgabe oder doppelte Kosten durch unbegrenzte Wiederholungen zu erzeugen.
7. KI-Ausfall, Kalenderfehler, Budgetüberschreitung und Deployment-Abbruch erhalten den letzten geprüften Stand.
8. Nicht freigegebene Entwürfe, Zugangsdaten und interne Prüfberichte fehlen im öffentlichen Export.
9. Wiederherstellung einer früheren Ausgabe und einer vollständigen Site-Version wurde praktisch erprobt.
10. Quellenblatt, Suchfilter, EN/HE-Wechsel, Direktlinks, Mobilansicht und Druckausgabe funktionieren.

## 13. Empfohlene Startvorgaben

**Name:** Shiurim · שיעורים.  
**Aktuelle Ausgabe:** Weekly Shiur · שיעור השבוע.  
**Rhythmus:** eine gemeinsame EN/HE-Ausgabe je Woche.  
**Themen:** Parascha und Jahreskreis mit fachlich begründetem Schwerpunktwechsel.  
**Hauptkalender:** Israel; Diaspora-Abweichung sichtbar.  
**Publikationsziel:** Donnerstag ab 18:17 Uhr `Asia/Jerusalem`, mit rechtzeitigem Vorziehen bei definierten Fest-/Sperrzeiten.  
**Erste Medienform:** vollständiger Text mit Quellenblatt und Druckansicht.  
**Technik:** eigenes Repository, eigene Veröffentlichung, lesender Quellenbezug.  
**Qualität:** vier fachlich geprüfte Pilot-Ausgaben, danach schrittweise autonome Veröffentlichung aus geprüftem Vorrat und klar geregelten neuen Inhalten.  
**Bestandsschutz:** keine Änderung während Entwicklung; ein späterer Homepage-Link ist ein ausdrücklich getrennter Integrationsschritt.

Damit ist der nächste Umsetzungsschritt konkret: eine eigenständige Musterausgabe samt Quellenblatt und EN/HE-Leseansicht entwickeln, während das bestehende System unverändert weiterläuft.

## Quellen und Prüfgrundlage

- Beigefügte Projektunterlagen, besonders Architektur, Datenstruktur, Leselogik, Uploadlogik und Suchbeschreibung; historische Dokumente und Testberichte, keine automatische Bestätigung des aktuellen Live-Zustands.
- Beigefügtes `HebrewTranscriptStudio_v2.1_ProjectHistory.zip`: Dateiliste, README, Text-/Projektservice und ausgewählte API-/KI-Konfigurationsstellen.
- Aktuelle Repository-Dokumentation, am 16.10.2026 lesend abgerufen: [README](https://github.com/Moriahise/Sanhedrin/blob/main/README.md), [Architektur](https://github.com/Moriahise/Sanhedrin/blob/main/docs/architecture.md), [Betrieb und Wiederherstellung](https://github.com/Moriahise/Sanhedrin/blob/main/docs/operations.md). Aussagen über Betrieb beziehen sich auf diese Dokumentation; keine unabhängige vollständige Live-Abnahme.
- [Hebcal Jewish Calendar REST API](https://www.hebcal.com/home/195/jewish-calendar-rest-api): Parascha-/Festdaten, Israel-/Diaspora-Parameter und Attribution.
- [Hebcal-Kalenderbibliothek](https://github.com/hebcal/hebcal-es6): mögliche lokal eingebundene Kalenderberechnung.
- [GitHub Actions: schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule): Zeitplanung, Zeitzonen, mögliche Verzögerung und Deaktivierung bei Inaktivität.
- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages): statische Veröffentlichung als Grundlage des vorgeschlagenen Lesebetriebs.
