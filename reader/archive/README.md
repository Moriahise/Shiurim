# Annual reading archive

Each cycle supplies a complete set of 54 bilingual studies in `YEAR/lessons.json`, numbered from Bereshit through Vezot Haberachah. The cycle number identifies the annual sequence beginning with Bereshit. Dates follow the Israel reading calendar, including the final readings after Rosh Hashanah. The individual texts of doubled portions share their actual reading date.

The archive build adds the study and source-sheet pages, a five-book annual index, the catalogue entries and sitemap links. Existing study pages and the homepage's featured study remain unchanged. The collection opens with its latest available cycle; readers can select earlier cycles or all cycles. The annual index works without JavaScript.

The supplied wording, questions and source passages are displayed in English and Hebrew. Markdown escapes are rendered as punctuation. Source names, references and credits remain attached to their passages. The portrait collection supplies a fixed identity for each study in its cycle.

Run after the portrait build: `python3 reader/archive.py --site _site`.

Multiple earlier cycles can be built together. The shared year selector lists each cycle once and keeps the latest cycle selected by default. Imported manuscripts retain all supplied teaching sections, discussion questions and complete multi-verse source passages.
