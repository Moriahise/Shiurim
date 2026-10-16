# Shiurim · שיעורים

Independent weekly Torah study in English and Hebrew. Repository: **Moriahise/Shiurim**.

The first release contains a complete Noach pilot, six attributed Hebrew primary texts, a parallel-language reader, a source sheet, a searchable library, a 52-week Israel/Diaspora calendar, and a reviewed-edition publication queue.

The source libraries are now connected read-only: full-text retrieval from the published Sanhedrin export and a Sefaria work catalogue based on the official Google Cloud Storage export and the preparations in `Moriahise/sefaria-studio`. Open `sources/` for research, exact references, original export links, and downloadable source dossiers. See [source connection guide](docs/QUELLENANBINDUNG_DE.md).

Automatic content preflight now checks the paragraph evidence register, text anchors, and possible EN/HE discrepancies. Its two-stage semantic reviewer is ready for a dedicated `SHIURIM_REVIEW_API_KEY` secret and `SHIURIM_REVIEW_MODEL` repository variable. Without them, semantic review remains explicitly incomplete. View the published report at `review/`. This never grants scholarly approval. See [content preflight guide](docs/INHALTLICHE_VORPRUEFUNG_DE.md).

**Pilot status:** independent scholarly review is pending. Automatic release of regular editions is disabled until the pilot and editorial process have been evaluated. The first pilot is deliberately visible and clearly labelled. No rabbinical authorship or approval is claimed.

## Run locally

Python 3.12 is used in CI; Python 3.11+ with timezone data is supported locally.

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python tools/shiurim.py validate
python tools/shiurim.py build
python -m http.server 8000 --directory dist
```

Open `http://localhost:8000`. The generated `dist` folder is the website. Browser printing also supports saving the lesson/source sheet as PDF. No API key, server account, CDN, or external font is required to read the site.

On Windows, double-click `START_LOKAL.bat` (Python 3.11+ required). It creates an isolated environment, installs the pinned dependencies when needed, builds the website, and serves it locally at `http://localhost:8766`. Keep its console window open while reading.

## GitHub Pages

In **this repository only**: Settings → Pages → Build and deployment → Source → **GitHub Actions**. Then Actions → Publish Shiurim → Run workflow. Expected address after successful deployment: <https://moriahise.github.io/Shiurim/>.

The workflow first tests and builds. If Pages is not configured for Actions, it preserves a downloadable build artifact and records the exact activation step instead of claiming deployment. It never changes Sanhedrin or DNS.

## Weekly publication

`Publish Shiurim` runs after main-branch changes, manually, and every four hours at minute 17. The timer is a due-check, not an instruction to publish four-hourly lessons. Each edition belongs to one target Shabbat. Explicit review is required; the queue is initially off.

`publish-due` validates content and review hashes, admits only eligible scheduled editions, and records the first release in `content/publications.json`. Repeated runs are idempotent. A single production concurrency group serializes all writers. The ledger is committed before Pages deployment, and failed builds never replace the previous local build. GitHub Pages deployment failures leave the previous public site in place.

There is currently **no unattended AI authoring service**. The working automation publishes a prepared, reviewed queue. Research, writing and scholarly review remain editorial steps. The included eight-week plan provides the next dossiers; API-based draft generation is a later, separate extension with its own credentials and budget.

## Isolation

- This repository, workflows, content, and publication ledger are independent.
- The workflow refuses any repository except `Moriahise/Shiurim`.
- No token or secret from Sanhedrin is used; `GITHUB_TOKEN` is scoped to this repository.
- There is no writer targeting Sanhedrin and no shared database. Its published static export is read via GET only.
- The Sanhedrin link is an ordinary outbound navigation link.

## Editorial operations

See [German operations guide](docs/BETRIEB_DE.md), [source connection guide](docs/QUELLENANBINDUNG_DE.md), [editorial plan](docs/REDAKTIONSPLAN_DE.md), [source attribution](docs/SOURCES.md), and [implementation plan](docs/UMSETZUNGSPLAN_DE.md).

## Sources and dependencies

Calendar: [pyluach 2.3.0](https://pyluach.readthedocs.io/en/latest/), MIT. Hebrew passages: *Miqra according to the Masorah* via Sefaria, labelled CC-BY-SA by the provider. Individual source files retain exact version, provenance, date and checksums. No existing English Bible translation is included in the lesson. See source notices for the distinction between supplied Hebrew text and original project discussion.
