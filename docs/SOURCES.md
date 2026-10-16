# Source attribution and textual integrity

The six Hebrew passages accompanying the first pilot were retrieved from the public Sefaria texts API on 16 October 2026. Each JSON file under `content/sources/` records the exact passage, URL, retrieval timestamp, version source, version title, provider license label, original Hebrew, and SHA-256.

**Text version:** *Miqra according to the Masorah*. **Provider:** Sefaria. **Provider license label:** CC-BY-SA. The exact provider-returned license label is retained; this project does not invent a more specific license version. Consult the linked source and version source for the underlying edition and license details. The Hebrew passages are reproduced without textual alteration.

| Reference | Source |
|---|---|
| Genesis 6:9 | https://www.sefaria.org/Genesis.6.9 |
| Genesis 6:22 | https://www.sefaria.org/Genesis.6.22 |
| Genesis 8:16 | https://www.sefaria.org/Genesis.8.16 |
| Genesis 8:20 | https://www.sefaria.org/Genesis.8.20 |
| Genesis 9:9 | https://www.sefaria.org/Genesis.9.9 |
| Genesis 11:4 | https://www.sefaria.org/Genesis.11.4 |

No existing English Bible translation is reproduced in the pilot. Its English and Hebrew discussion is new, AI-assisted editorial work, explicitly awaiting independent scholarly review. Source text and editorial interpretation are distinct in the lesson and source sheet. Copyright and licensing of the Hebrew source text remain those of the underlying edition.

Calendar calculations use [pyluach 2.3.0](https://pyluach.readthedocs.io/en/latest/) (MIT), with an independent spot-check of Noach on 17 October 2026 against [Hebcal](https://www.hebcal.com/sedrot/noach-20261017). Published lessons remain self-contained. The separate source research view now reads the published Sanhedrin export and Sefaria via GET-only connections. It has no access to the active Sanhedrin database and uses no OpenAI key.

The Sefaria catalogue is a compact derivative of the official Sefaria-Export work index, augmented with Hebrew work names from the official Sefaria table of contents. The prepared `Moriahise/sefaria-studio` work index is a fallback. These metadata do not represent redistribution of the complete text corpus; original text versions retain their own licensing. Source research dossiers preserve the original provider's attribution and license, and are not automatically public lesson sources.
