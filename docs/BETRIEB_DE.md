# Betrieb · Shiurim

## Stand der ersten Version

Die Plattform und der Publisher sind implementiert. Die Noach-Ausgabe ist ein öffentlich sichtbarer Pilot mit sechs dokumentierten Originalstellen. Eine unabhängige fachliche Prüfung ist noch offen. Die reguläre Freigabeautomatik steht auf `false`. Es gibt noch keinen unbeaufsichtigten KI-Autor und keine neue OpenAI-Anbindung.

Die ursprüngliche Testdatei bleibt erhalten. Dateien, Einstellungen, Secrets und Publikationswege von Sanhedrin werden nicht verändert.

## Einmalige Pages-Aktivierung

Nur im neuen Repository `Moriahise/Shiurim`:

1. **Settings → Pages** öffnen.
2. Bei **Build and deployment → Source** **GitHub Actions** auswählen.
3. **Actions → Publish Shiurim → Run workflow** starten.
4. Nach erfolgreichem Deployment erscheint die Adresse im Deployment-Job.

Ohne diese Einstellung baut und prüft der Workflow trotzdem die Website und stellt sie als Artifact bereit. Ein erfolgreiches Build bedeutet noch keine aktivierte öffentliche Website.

## Eine neue Ausgabe vorbereiten

1. Datei unter `content/editions/<stabile-id>.json` anlegen, zunächst `status: draft`.
2. EN/HE-Titel, Leitfrage, Lernziel, Abschnitte und Fragen vollständig ausarbeiten. Absatzanzahl und Abschnitts-IDs stimmen überein.
3. Jede tragende Quelle unter `content/sources/` mit Textversion, URL, Lizenz, Abrufzeit und SHA-256 sichern. Keine erfundenen Fundstellen oder nur aus Suchtreffern übernommenen Belege.
4. `target_shabbat` ist das tatsächliche Samstagsdatum. `parashah` entspricht exakt den vom Kalender ausgegebenen EN/HE-Werten; auf Festschabbat steht die Festlesung. `python tools/shiurim.py calendar` zeigt die nächsten 52 Wochen.
5. `publish_at` enthält eine eindeutige Zeitzone. Rund um Feiertage wird die Veröffentlichung früh genug vorgezogen. Der gegenwärtige Schutz blockiert ganze Freitage, Samstage, Jom-Tov-Tage und deren Vortage; er berechnet keine minutengenauen Sonnenuntergangsgrenzen.
6. `python tools/shiurim.py validate` prüft Struktur, Quellenidentität, Kalender und Freigaben. Diese Prüfung beurteilt nicht zuverlässig, ob eine Interpretation sachlich richtig ist.
7. Erst nach tatsächlicher fachlicher Durchsicht wird die Freigabe dokumentiert. Der Prüfer muss die Bedeutung der Quellen, die Tragfähigkeit der Schlussfolgerungen und beide Sprachfassungen prüfen.

## Tatsächliche Freigabe dokumentieren

Vor der Freigabe `python tools/shiurim.py review-digest --id <id>` ausführen. Der Digest umfasst den vollständigen Inhalt und die Prüfsummen der verwendeten Quellen.

Nach tatsächlicher Prüfung werden `review.scholarly_review: approved`, `review.reviewer` (wirkliche Person), `review.reviewed_revision` und `review.content_sha256` gesetzt. Dann kann `status: scheduled` gesetzt werden. Wird ein inhaltliches Feld später geändert, ist die gespeicherte Freigabe ungültig und muss erneuert werden.

Diese Felder sind ein transparentes redaktionelles Protokoll, keine kryptografische Identitätsprüfung eines Rabbiners. Schreibrechte und Branch-Regeln sichern organisatorisch, wer sie setzen darf. Niemals eine Person als Prüfer eintragen, die die Ausgabe nicht geprüft hat.

## Wochenautomatik aktivieren

Erst nach Pilot-Abnahme wird `automatic_publication` in `config/site.json` auf `true` gesetzt. Der Timer prüft alle vier Stunden, ob eine geplante Ausgabe freigegeben und fällig ist. Der Donnerstagstermin ist eine Fälligkeitsgrenze, keine sekundengenaue SLA. Der nächste zulässige Lauf veröffentlicht; Startverzögerungen sind möglich.

Ein bereits veröffentlichter Datensatz bleibt über das persistierte Publikationsregister sichtbar, auch wenn die Automatik später ausgeschaltet wird. Ein fehlender neuer Text erzeugt keine erfundene Ausgabe. Kalenderzeilen sind ausschließlich Kalenderdaten und werden auch so bezeichnet.

GitHub kann öffentliche Schedules nach 60 Tagen ohne Repository-Aktivität deaktivieren. Regelmäßig Actions und das Datenfeld `built_at` unter `data/status.json` kontrollieren. Ein unabhängiger externer Ausfallmelder ist in dieser Version nicht eingerichtet. Bei Bedarf manuell denselben Workflow starten, keinen zweiten parallelen Publisher anlegen.

## Rücksprung und Wiederherstellung

Alle maßgeblichen Quelltexte, Ausgaben und das Publikationsregister liegen in Git. Sie sind der dauerhaft rekonstruierbare Zustand. Workflow-Artefakte sind nur zusätzliche zeitlich begrenzte Buildkopien.

Bei einem technischen Fehler bleibt der zuletzt erfolgreich veröffentlichte Pages-Stand verfügbar. Für einen Rücksprung die bekannten guten Projektdateien aus einem überprüften früheren Commit in einem neuen Commit wiederherstellen und den Publish-Workflow ausführen. Kein Force-Push und keine Änderung am Sanhedrin-Repository.

Eine bereits im Publikationsregister erfasste Ausgabe darf nicht still verändert werden: Der aktuelle Validator blockiert veränderte Inhalte oder Revisionen. Ein ausgebauter Korrektur-/Revisionsprozess mit mehreren erhaltenen Revisionen unter derselben öffentlichen ID ist noch ein Folgeschritt. Bis dahin wird eine notwendige inhaltliche Korrektur ausdrücklich redaktionell behandelt und das Register nicht ohne archivierte Vorfassung überschrieben.

Lokale Builds heben alte Stände unter `reports/previous-site-*` auf. Das Verzeichnis ist nicht öffentlich und wird nicht eingecheckt. Ein nach Prozessabbruch zurückgebliebenes `reports/publisher.lock` darf erst entfernt werden, wenn sichergestellt ist, dass kein Publisher mehr läuft.

## Grenzen der technischen Prüfung

16 automatisierte Tests prüfen u. a. Kalenderabweichung Israel/Diaspora, Festlesung, Doppelparascha, Jahreswechsel, Sommerzeit, Quellenänderung, Absatzgleichheit, falsche Freigabe, wiederholte Veröffentlichung, Sperrtage, Entwurfausschluss, HTML-Escaping, vollständige Links und Bestandserhalt bei Fehlern.

Eine echte Browser- und Druckansichtsabnahme steht aus, wenn keine unterstützte Browser-Testumgebung verfügbar ist. Ebenso ausstehend sind eine unabhängige fachliche Abnahme, die vierteilige Pilotphase, unbeaufsichtigte KI-Entwurfserstellung und ein eigenständiger externer Überwachungsdienst. Die Website behauptet keine dieser Leistungen als bereits vorhanden.
