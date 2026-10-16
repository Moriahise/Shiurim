# Automatische inhaltliche Vorprüfung

**Eingerichtet am 16.10.2026.** Die Vorprüfung ergänzt die bisherige Strukturvalidierung. Sie vergibt niemals eine fachliche oder rabbinische Freigabe und ändert weder Lehrtext noch Prüfernamen oder Veröffentlichungsfreigaben.

## Zwei Ebenen

| Ebene | Tatsächliche Prüfung | Grenze |
|---|---|---|
| Nachvollziehbare Regeln | Absatz-/Belegregister, Quellenidentität, exakte Textanker, auffällige Zitate, Zahlen, Negationsformulierungen, mögliche praktische Entscheidungen und nicht zugeordnete Autorennamen | Wortlautabgleich beweist keine inhaltliche Folgerung; Sprachindikatoren können Fehlalarme erzeugen |
| KI-Prüfung in zwei getrennten Durchgängen | 1. Tragfähigkeit der bereitgestellten Quellen für die Aussagen; 2. Bedeutungsgleichheit von Englisch und Hebräisch | Kann falsch urteilen; keine unabhängige rabbinische Entscheidung |

Ohne konfigurierten Prüfschlüssel und Prüfmodell laufen nur die Regeln. Der KI-Teil bleibt dann **nicht ausgeführt**, und bei der gegenwärtigen Einstellung bleibt der Gesamtbericht **unvollständig**. Fehlende, verweigerte, unvollständige oder technisch gescheiterte Antworten werden nie als positives Ergebnis gewertet.

## Das Belegregister

Unter `content/evidence/<ausgabe-id>.json` wird jeder Absatz mit stabiler Kennung wie `integrity:1` erfasst. Gespeichert werden:

- Typ: Aussage über die Quelle, Interpretation, Anwendung oder methodische Einordnung.
- Genau zugeordnete Quellen und ihr gespeicherter Wortlaut.
- Textprüfsumme jeder Quelle.
- Bindung an die vollständige englisch-hebräische Ausgabe.
- Kennzeichnung, wenn die Stelle nur Kontext liefert.

Die Zuordnung ist redaktionelle Metadatenarbeit. Der automatische Prüfer kontrolliert sie, betrachtet sie aber nicht als Beweis für ihre eigene Richtigkeit. Die KI erhält zusätzlich beide vollständigen Absatzfassungen und die Originalquellen und soll auch übersehene Einzelbehauptungen markieren.

Die Noach-Pilottexte wurden nicht verändert. Für ihre 22 Absätze ist ein erstes Register hinterlegt. Seine 26 Textanker sind vollständig in den gespeicherten Quellen auffindbar. Der aktuelle Regellauf markiert sieben Hinweise: drei Stellen mit nur kontextueller Belegabdeckung sowie vier Hinweise zur Negationsformulierung. Letztere sind ausdrücklich keine festgestellten Übersetzungsfehler. Die Bedeutung muss geprüft werden.

## Was automatisch geprüft wird

1. Fehlt ein Absatz oder verweist das Register auf einen nicht mehr vorhandenen Absatz?
2. Gehört die Zuordnung zur aktuellen Ausgabe und ihren Quellen?
3. Ist eine Tatsachenbehauptung oder Interpretation mit einem präzisen Quellenausschnitt verbunden?
4. Stimmt die gespeicherte Quelle noch mit der Prüfsumme überein?
5. Findet sich der Textanker wirklich in dieser Quelle? Niqqud, Kantillation und Satzzeichen werden für den Vergleich normalisiert; die Wortgrenzen bleiben erhalten.
6. Gibt es im Lehrtext ein längeres Zitat, das noch nicht in einer Quelle derselben Sprache gefunden wurde? Übersetzte Zitate werden zur weiteren Prüfung markiert.
7. Unterscheiden sich arabische Zahlen zwischen EN und HE? Kapitel-/Versangaben werden dabei ausgenommen. Hebräische Zahlenbuchstaben werden nicht aus beliebiger Prosa erraten.
8. Gibt es auffällige Negationsformulierungen, mögliche praktische Entscheidungssätze oder Autorennamen ohne passende Quellenmetadaten?

Die Punkte 6–8 sind Hinweise zur Durchsicht. Sie sind keine verlässliche semantische Entscheidung.

## KI-Prüfung aktivieren

Nur im neuen Repository `Moriahise/Shiurim`:

1. Unter **Settings → Secrets and variables → Actions → Secrets** ein Repository-Secret **`SHIURIM_REVIEW_API_KEY`** mit einem geeigneten OpenAI-API-Schlüssel anlegen.
2. Unter **Variables** die Repository-Variable **`SHIURIM_REVIEW_MODEL`** mit der tatsächlichen ID eines im eigenen API-Konto verfügbaren Modells setzen. Es muss Responses API und Structured Outputs unterstützen. Es wird kein unbestätigter Modellname als Standard eingesetzt.
   **Wichtig:** Der Wert ist ein Modellname, kein Einschalter: `true` oder `false` sind hier falsch. Ein dokumentiertes Beispiel ist `gpt-5.4`, das Responses API und Structured Outputs unterstützt; der tatsächliche Zugriff muss im verwendeten OpenAI-Projekt bestehen. Siehe [offizielle Modellbeschreibung](https://developers.openai.com/api/docs/models/gpt-5.4).
3. **Actions → Publish Shiurim → Run workflow** starten.

Offensichtliche Schalterwerte werden vor jedem API-Aufruf abgefangen und als ungültige Konfiguration im EN/HE-Bericht erklärt. Bei HTTP 404 zeigt der Bericht einen Hinweis auf Modell-ID und Projektzugriff. Beides bleibt eine unvollständige Vorprüfung. Ein grüner Website-Build bestätigt die technische Veröffentlichung des Berichts, nicht den Erfolg der KI-Prüfung.

Die Anwendung benutzt ausschließlich diesen eigenen Prüfschlüssel. Sie liest keinen Schlüssel aus Sanhedrin und überträgt keine Secrets zwischen Repositories. Der Schlüssel wird nur dem serverseitigen Vorprüfschritt bereitgestellt; er gelangt weder in den Browser noch in die Prüfberichte.

Die OpenAI-Responses-Anfrage verwendet ein festes Ausgabeschema und `store: false`. Die beiden Prüfdurchgänge arbeiten nur mit den übergebenen Texten und besitzen keine Werkzeuge oder externen Schreibrechte. Eingebettete Anweisungen in Quellentexten werden im Prüfprompt ausdrücklich als untrusted Text behandelt. Ausgabeformat, Absatzabdeckung, Quellen-IDs und gelieferte Originalzitate werden zusätzlich im Programm kontrolliert.

Ein Modellurteil „gestützt“ ohne tatsächlich auffindbaren Beleg wird verworfen. Unbekannte Absatz-/Quellen-IDs, ausgelassene Absätze und nicht auffindbare Modellzitate führen nicht zu einem erfolgreichen KI-Ergebnis.

## Begrenzung und Wiederverwendung

Pro Ausgabe werden höchstens zwei API-Aufrufe ausgeführt, ohne automatische Wiederholungsschleife: ein Quellen- und ein Sprachprüflauf. Je Aufruf sind höchstens 8.000 Ausgabetokens und 180 Sekunden Wartezeit eingestellt. Zu große Eingaben werden angehalten, nicht still gekürzt. Diese Grenzen sind keine Euro-Kostenkalkulation.

Erfolgreiche Ergebnisse werden an Inhalt, Quellen, Belegregister, Prüfrichtlinie, Programmstand und Modellkonfiguration gebunden. Der GitHub-Workflow verwendet einen passenden Cache, damit unveränderte Inhalte nicht bei jedem Zeitgeberlauf erneut bezahlt geprüft werden. Ein geänderter Inhalt oder Prüfschlüssel des Datenstands verlangt einen neuen Lauf. Ein Cache kann vom Anbieter entfernt werden; bei einem erneuten tatsächlichen Lauf gelten wieder die genannten Grenzen. Fehlgeschlagene Durchgänge werden nicht als erfolgreiche Cacheeinträge gespeichert.

## Berichte

```bash
python tools/content_review.py --semantic off
python tools/content_review.py --semantic auto
python tools/content_review.py --semantic required
```

`auto` verwendet die KI nur bei vorhandener Konfiguration. `required` liefert Exitcode 2, wenn die Vorprüfung nicht vollständig und ohne offene Hinweise ist. Regel- und KI-Ergebnisse bleiben im JSON getrennt. `auto` erzeugt auch bei offenen Hinweisen einen Bericht, damit die vorhandene Website weiterhin gebaut werden kann. Ein technischer Ausführungsfehler liefert Exitcode 1.

Interne Berichte liegen unter `reports/preflight/` und im Workflow-Artefakt. Für tatsächlich sichtbare Ausgaben erzeugt der Site-Build eine EN/HE-Ansicht unter `review/<ausgabe-id>/` und eine JSON-Fassung unter `data/preflight/`. Unveröffentlichte Entwürfe erhalten keine öffentliche Berichtsseite. Provider-Response-IDs und Tokenverbrauch werden aus der öffentlichen Fassung entfernt.

Der Bericht bleibt nur für den passenden Inhaltsstand gültig. Stimmen Inhalt, Register oder Richtlinie nicht mehr überein, wird der alte Bericht nicht als aktuelles Ergebnis übernommen.

## Verhältnis zur Veröffentlichung

Ein neuer regulärer Eintrag benötigt weiterhin die tatsächliche fachliche Freigabe. Zusätzlich blockieren aktuelle Vorprüfungsfehler – einschließlich einer festgestellten semantischen Bedeutungsabweichung – seine automatische Aufnahme in das Publikationsregister. Bereits veröffentlichte Texte werden dadurch nicht still gelöscht.

Hinweise verlangen Durchsicht, erteilen aber keine Freigabe. Eine fehlende KI-Prüfung wird als offen ausgewiesen; die dokumentierte menschliche Freigabe bleibt ein eigener Vorgang. Die reguläre Wochenautomatik ist weiterhin ausgeschaltet.

## Validierung

57 automatisierte Python-Tests prüfen den Publikationskern, die Quellenanbindungen und die Vorprüfung. Neun weitere JavaScript-Tests prüfen die Sefaria-Navigation. Die KI-Protokolltests verwenden ausdrücklich künstliche Antworten und keine behaupteten echten Modellgutachten. Der erste konfigurierte Produktionslauf vom 16.10.2026 kam mit dem Modellwert `true` an und endete vor einem inhaltlichen Ergebnis mit HTTP 404. Beide KI-Stufen sind damit weiterhin offen. Es liegt kein positives Modellgutachten vor. Eine vollständige Browserabnahme steht weiterhin aus.

Offizielle Schnittstellengrundlage: [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

## Betriebsanpassung nach dem ersten Modelllauf

Nach Korrektur auf `gpt-5.4` wurde das Modell am 16.10.2026 korrekt übernommen. Der erste echte Versuch endete am früheren 45-Sekunden-Zeitlimit, ohne inhaltliches Ergebnis. Deshalb beträgt die begrenzte Wartezeit nun 180 Sekunden je Aufruf; die Anzahl der Aufrufe und das Tokenlimit bleiben gleich. Technische Fehlergründe erscheinen zusätzlich im Workflow-Protokoll.

Pages-Pakete und vollständige Prüfarbeitsstände tragen jetzt Lauf-ID und Versuchszähler im Namen. Der Deploy-Job erhält den Namen aus dem tatsächlich abgeschlossenen Build. Dadurch verwechselt eine Wiederholung keine gleichnamigen Pakete aus mehreren Versuchen.
