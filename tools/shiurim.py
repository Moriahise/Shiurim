"""Isolated, deterministic bilingual publisher. No access to Sanhedrin."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from html import escape
import json
import gzip
from pathlib import Path
import re
import shutil
import sys
import tempfile
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from pyluach import dates, parshios

ROOT = Path(__file__).resolve().parents[1]
JERUSALEM = ZoneInfo("Asia/Jerusalem")
SAFE_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CATEGORIES = {
    "tanach": ("Torah & commentary", "תורה ופרשנות"),
    "halacha": ("Halacha & sugya", "הלכה וסוגיה"),
    "mussar": ("Mussar & inner work", "מוסר ועבודת ה׳"),
    "mikdash": ("Mikdash & community", "מקדש וקהילה"),
}


class ValidationError(ValueError):
    pass


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write("\n")
        tmp = Path(f.name)
    tmp.replace(path)


def now_value(value=None):
    now = datetime.fromisoformat(value) if value else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValidationError("An explicit timezone is required")
    return now.astimezone(JERUSALEM)


def pair(value, tag="span", cls=""):
    return "".join(f'<{tag} class="l-{lang} {cls}" lang="{lang}" dir="{"rtl" if lang == "he" else "ltr"}">{escape(str(value[lang]))}</{tag}>' for lang in ("en", "he"))


def label(en, he, tag="span", cls=""):
    return pair({"en": en, "he": he}, tag, cls)


def calendar_week(target):
    day = date.fromisoformat(target) if isinstance(target, str) else target
    if day.weekday() != 5:
        raise ValidationError("Target must be a Saturday")
    gd = dates.GregorianDate(day.year, day.month, day.day)
    heb = gd.to_heb()
    israel = parshios.getparsha_string(gd, israel=True)
    diaspora = parshios.getparsha_string(gd, israel=False)
    festival = gd.festival(israel=True)
    festival_he = gd.festival(israel=True, hebrew=True)
    return {
        "target_shabbat": day.isoformat(), "hebrew_date": heb.hebrew_date_string(),
        "israel": {"en": israel or festival or "Festival reading", "he": parshios.getparsha_string(gd, israel=True, hebrew=True) or festival_he or "קריאת החג"},
        "diaspora": {"en": diaspora or gd.festival() or "Festival reading", "he": parshios.getparsha_string(gd, hebrew=True) or gd.festival(hebrew=True) or "קריאת החג"},
        "different_readings": israel != diaspora,
        "festival": festival, "festival_he": festival_he,
        "has_weekly_parashah": israel is not None,
    }


def upcoming_calendar(now, count=8):
    start = now.date()
    target = start + timedelta(days=(5 - start.weekday()) % 7)
    return [calendar_week(target + timedelta(weeks=i)) for i in range(count)]


def digest(edition, sources):
    payload = {k: v for k, v in edition.items() if k not in {"review", "status"}}
    payload["source_checksums"] = {sid: sources[sid]["sha256"] for sid in sorted(edition["source_ids"])}
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_text(item):
    return item.get('hebrew') if 'hebrew' in item else item.get('text','')


def review_tools():
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    from tools import content_review
    return content_review


def validate_pair(value, field):
    if not isinstance(value, dict) or any(not isinstance(value.get(lang), str) or not value[lang].strip() for lang in ("en", "he")):
        raise ValidationError(f"Missing EN/HE pair: {field}")
    if not re.search(r"[א-ת]", value["he"]):
        raise ValidationError(f"Hebrew missing: {field}")


def load_all(root=ROOT):
    config = read(root / "config/site.json")
    if config["repository"] != "Moriahise/Shiurim":
        raise ValidationError("Publisher is restricted to Moriahise/Shiurim")
    sources = {}
    for path in sorted((root / "content/sources").glob("*.json")):
        item = read(path)
        sid = item["id"]
        if not SAFE_ID.fullmatch(sid) or sid in sources:
            raise ValidationError("Invalid or duplicate source ID")
        if not source_text(item) or sha256(source_text(item).encode()).hexdigest() != item["sha256"]:
            raise ValidationError(f"Source checksum mismatch: {sid}")
        u = urlparse(item["url"])
        if (u.scheme != "https" or u.username or u.password or u.hostname not in {'www.sefaria.org','shekhina.org','moriahise.github.io'}
                or (u.hostname=='moriahise.github.io' and not u.path.startswith('/Sanhedrin/'))):
            raise ValidationError("Unapproved source URL")
        for key in ("reference_en", "reference_he", "version", "license", "retrieved_at"):
            if not item.get(key):
                raise ValidationError(f"Missing source provenance: {sid}/{key}")
        sources[sid] = item
    editions = []
    ids, weekly_slots = set(), set()
    for path in sorted((root / "content/editions").glob("*.json")):
        e = read(path)
        eid = e.get("id", "")
        if not SAFE_ID.fullmatch(eid) or eid in ids:
            raise ValidationError("Invalid or duplicate edition ID")
        ids.add(eid)
        if e.get("schema") != 1 or not isinstance(e.get("revision"), int) or e["revision"] < 1:
            raise ValidationError("Unsupported schema/revision")
        if e.get("status") not in {"draft", "pilot", "scheduled", "published"} or e.get("category") not in CATEGORIES:
            raise ValidationError("Invalid status/category")
        cal = calendar_week(e["target_shabbat"])
        if e["parashah"] != cal["israel"]:
            raise ValidationError(f"Calendar mismatch: {eid}")
        if e["target_shabbat"] in weekly_slots:
            raise ValidationError("Only one edition per target Shabbat")
        weekly_slots.add(e["target_shabbat"])
        publication = now_value(e["publish_at"])
        if publication.date() >= date.fromisoformat(e["target_shabbat"]):
            raise ValidationError("Publication must precede target Shabbat")
        if not e.get("source_ids") or len(e["source_ids"]) != len(set(e["source_ids"])):
            raise ValidationError("Missing/duplicate sources")
        if any(sid not in sources for sid in e["source_ids"]):
            raise ValidationError("Unresolved source")
        for field in ("title", "subtitle", "question", "summary", "objective", "level", "authorship"):
            validate_pair(e.get(field), field)
        if not e.get("sections") or not e.get("questions"):
            raise ValidationError("Incomplete lesson")
        section_ids = set()
        cited = set()
        for section in e["sections"]:
            sid = section.get("id", "")
            if not SAFE_ID.fullmatch(sid) or sid in section_ids:
                raise ValidationError("Invalid/duplicate section ID")
            section_ids.add(sid)
            validate_pair(section.get("title"), "section title")
            if not section.get("sources") or any(s not in e["source_ids"] for s in section["sources"]):
                raise ValidationError("Section has unresolved evidence")
            cited.update(section["sources"])
            if not isinstance(section.get("en"), list) or not section["en"] or len(section["en"]) != len(section.get("he", [])):
                raise ValidationError("Paragraph alignment mismatch")
            for en, he in zip(section["en"], section["he"]):
                validate_pair({"en": en, "he": he}, "paragraph")
        if cited != set(e["source_ids"]):
            raise ValidationError("Unused source in source sheet")
        for question in e["questions"]:
            validate_pair(question, "discussion question")
        review = e.get("review", {})
        if review.get("scholarly_review") == "approved":
            if not review.get("reviewer") or review.get("reviewed_revision") != e["revision"] or review.get("content_sha256") != digest(e, sources):
                raise ValidationError("Approval is missing or no longer matches content")
        if e["status"] in {"scheduled", "published"} and review.get("scholarly_review") != "approved":
            raise ValidationError("Regular publication requires scholarly approval")
        editions.append(e)
    ledger = read(root / "content/publications.json") if (root / "content/publications.json").exists() else {"schema": 1, "releases": []}
    edition_map = {e["id"]: e for e in editions}
    released = set()
    for release in ledger["releases"]:
        eid = release["id"]
        if eid in released or eid not in edition_map:
            raise ValidationError("Duplicate or missing ledger edition")
        released.add(eid)
        e = edition_map[eid]
        if release["revision"] != e["revision"] or release["content_sha256"] != digest(e, sources):
            raise ValidationError("Released content changed; preserve previous revision before correcting")
        if e.get("review", {}).get("scholarly_review") != "approved":
            raise ValidationError("Released edition lost approval")
    return config, sources, editions, ledger


@contextmanager
def publisher_lock(root=ROOT):
    path = root / "reports/publisher.lock"
    path.parent.mkdir(exist_ok=True)
    try:
        handle = path.open("x")
    except FileExistsError as exc:
        raise ValidationError("Another publisher is active; no concurrent writers") from exc
    try:
        with handle:
            handle.write(datetime.now(timezone.utc).isoformat())
        yield
    finally:
        path.unlink(missing_ok=True)


def publish_due(now, root=ROOT):
    with publisher_lock(root):
        config, sources, editions, ledger = load_all(root)
        result = {"checked_at": now.isoformat(), "automatic_publication": config["automatic_publication"], "published": [], "waiting": []}
        existing = {r["id"] for r in ledger["releases"]}
        for e in editions:
            if e["id"] in existing or e["status"] != "scheduled":
                continue
            due = now_value(e["publish_at"])
            target = date.fromisoformat(e["target_shabbat"])
            # No late Friday/Shabbat release, including recovery attempts.
            if not config["automatic_publication"] or now < due:
                result["waiting"].append(e["id"])
                continue
            reviewer=review_tools()
            policy=read(root/'config/preflight.json')
            preflight=reviewer.current_report(root,e,sources,policy)
            if any(f['severity']=='error' for f in preflight['findings']):
                result['waiting'].append(e['id']+': content preflight has blocking findings')
                continue
            if now.date() >= target - timedelta(days=1) or now - due > timedelta(days=config["max_catchup_days"]):
                result["waiting"].append(e["id"] + ": missed safe publication window")
                continue
            # Fail closed on any Jerusalem Yom Tov date or the eve of a Yom Tov.
            # No sunset estimate: all such civil dates are conservatively blocked.
            def yom_tov(day):
                gd = dates.GregorianDate(day.year, day.month, day.day)
                return bool(gd.festival(israel=True, include_working_days=False))
            if now.weekday() in (4, 5) or yom_tov(now.date()) or yom_tov(now.date() + timedelta(days=1)):
                result["waiting"].append(e["id"] + ": protected day")
                continue
            ledger["releases"].append({"id": e["id"], "revision": e["revision"], "content_sha256": digest(e, sources), "published_at": now.isoformat()})
            existing.add(e["id"])
            result["published"].append(e["id"])
        if result["published"]:
            write(root / "content/publications.json", ledger)
        write(root / "reports/latest-run.json", result)
        return result


def layout(title, body, prefix="./", description="Weekly Torah learning in English and Hebrew.", libraries=False, review=False):
    connections="https://shekhina.org https://moriahise.github.io https://storage.googleapis.com https://www.sefaria.org" if libraries else ''
    library_script=f'<link rel="stylesheet" href="{prefix}assets/sources.css"><script defer src="{prefix}assets/sefaria-navigation.js"></script><script defer src="{prefix}assets/source-library.js"></script>' if libraries else ''
    review_style=f'<link rel="stylesheet" href="{prefix}assets/review.css">' if review else ''
    return f'''<!doctype html>
<html lang="en" dir="ltr" class="no-js" data-mode="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} · Shiurim</title><meta name="description" content="{escape(description, quote=True)}">
<meta name="theme-color" content="#152d39"><meta name="color-scheme" content="light">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' {connections}; font-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'">
<link rel="icon" href="{prefix}assets/mark.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/site.css">
<script defer src="{prefix}assets/site.js"></script>{library_script}{review_style}</head><body>
<a class="skip" href="#main">{label('Skip to content','דילוג לתוכן')}</a>
<header class="site-header"><a class="wordmark" href="{prefix}"><span class="brand-mark" aria-hidden="true">ש</span><span>SHIURIM<small lang="he" dir="rtl">שיעורים</small></span></a>
<nav aria-label="Main navigation"><a href="{prefix}#library">{label('The library','ספריית השיעורים')}</a><a href="{prefix}sources/">{label('Source libraries','ספריות המקורות')}</a><a href="{prefix}#path">{label('Learning path','מסלול הלימוד')}</a><a href="{prefix}about/">{label('Our approach','דרך הלימוד')}</a></nav>
<div class="language-controls" role="group" aria-label="Reading language"><button data-mode-set="en" aria-pressed="true">EN</button><button data-mode-set="he" aria-pressed="false" lang="he">עב</button><button data-mode-set="parallel" aria-pressed="false">{label('Parallel','מקביל')}</button></div></header>
{body}
<footer class="site-footer"><div class="footer-brand">SHIURIM <span lang="he">שיעורים</span></div><p>{label('One question. A week of learning.','שאלה אחת. שבוע של לימוד.')}</p><div><a href="{prefix}about/">{label('Sources & editorial method','מקורות ודרך העריכה')}</a><a href="https://shekhina.org/">{label('Sanhedrin · Responsa archive ↗','סנהדרין · ארכיון שאלות ותשובות ↗')}</a><a href="https://github.com/Moriahise/Shiurim">GitHub ↗</a></div></footer>
</body></html>'''


def date_label(e):
    day = date.fromisoformat(e["target_shabbat"])
    return label(day.strftime("%d %B %Y"), calendar_week(day)["hebrew_date"])


def minutes(e):
    return {lang: max(1, round(sum(len(p.split()) for s in e["sections"] for p in s[lang]) / (190 if lang == "en" else 160))) for lang in ("en", "he")}


def status_label(e, released=False):
    return label('Published edition' if released else 'Pilot · scholarly review pending', 'מהדורה שפורסמה' if released else 'מהדורת ניסיון · ממתינה לביקורת תורנית')


def source_block(s, number):
    lang=s.get('language','he')
    provider=s.get('provider','sefaria')
    return f'''<article class="source" id="source-{escape(s['id'])}"><div class="source-heading"><span class="source-no">{number:02}</span><h3>{label(s['reference_en'],s['reference_he'])}</h3><a href="{escape(s['url'],quote=True)}" target="_blank" rel="noopener noreferrer">{label('Open source ↗','פתיחת המקור ↗')}</a></div><blockquote lang="{escape(lang)}" dir="{'rtl' if lang=='he' else 'ltr'}">{escape(source_text(s))}</blockquote><p class="provenance">{escape(s['version'])} · {escape(str(s['license']))} · {escape(provider)}<br>{label('Source text and editorial discussion are kept distinct.','לשון המקור והדיון המערכתי מובחנים זה מזה.')}</p></article>'''


def lesson(e, sources, released=False, sheet=False):
    prefix = "../../../" if sheet else "../../"
    reading = "../" if sheet else "./"
    m = minutes(e)
    sidebar = ''.join(f'<a href="#{s["id"]}">{pair(s["title"])}</a>' for s in e['sections'])
    contents = []
    if not sheet:
        for s in e['sections']:
            paras = ''.join(f'<div class="paragraph-pair">{pair({"en":en,"he":he},"p")}</div>' for en, he in zip(s['en'],s['he']))
            refs = ''.join(f'<a href="#source-{sid}">{pair({"en":sources[sid]["reference_en"],"he":sources[sid]["reference_he"]})}</a>' for sid in s['sources'])
            contents.append(f'<section class="lesson-section" id="{s["id"]}"><h2>{pair(s["title"])}</h2>{paras}<div class="section-refs">{refs}</div></section>')
        questions = ''.join(f'<li>{pair(q)}</li>' for q in e['questions'])
        contents.append(f'<section class="discussion"><div class="eyebrow">{label("For the study table","לשולחן הלימוד")}</div><h2>{label("Keep the conversation going","ממשיכים לשאול")}</h2><ol>{questions}</ol></section>')
    sheet_body = ''.join(source_block(sources[sid], i+1) for i,sid in enumerate(e['source_ids']))
    body = f'''<main id="main"><div class="reading-top"><a href="{prefix}#library">{label('← The library','ספריית השיעורים ←')}</a><div class="reading-actions"><a href="{reading}{'' if sheet else 'sources/'}">{label('Read lesson' if sheet else 'Source sheet','לשיעור' if sheet else 'דף מקורות')}</a><a href="{prefix}review/{e['id']}/">{label('Content preflight','בדיקה מקדימה')}</a><button data-print>{label('Print / save PDF','הדפסה / שמירה כ־PDF')}</button></div></div>
<header class="lesson-header"><div class="eyebrow">{pair(e['parashah'])} <span aria-hidden="true">/</span> {date_label(e)}</div><div class="edition-status">{status_label(e,released)}</div><h1>{pair(e['title'])}</h1><p class="lesson-subtitle">{pair(e['subtitle'])}</p><div class="lesson-meta">{label(str(m['en'])+' min read',str(m['he'])+' דקות קריאה')} <span>·</span> {label(str(len(e['source_ids']))+' sources',str(len(e['source_ids']))+' מקורות')} <span>·</span> {pair(e['level'])}</div><p class="byline">{pair(e['authorship'])}</p></header>
<div class="lesson-grid"><aside class="contents"><p class="eyebrow">{label('In this shiur','בשיעור זה')}</p>{sidebar if not sheet else ''}<a href="#sources">{label('The sources','המקורות')}</a><a href="#main">{label('Back to top ↑','לראש הדף ↑')}</a></aside><article class="lesson-body"><div class="guiding-question"><div class="eyebrow">{label('The guiding question','השאלה המנחה')}</div>{pair(e['question'],'p')}</div>{''.join(contents)}<section id="sources" class="sources-section"><div class="eyebrow">{label('Return to the text','חוזרים למקור')}</div><h2>{label('The source sheet','דף המקורות')}</h2>{sheet_body}</section><p class="editorial-note">{label('Pilot text: source-linked and AI-assisted; independent scholarly review is pending. Interpretive applications are distinguished from the source text.','טקסט ניסיון: מבוסס מקורות ונערך בסיוע בינה מלאכותית; ביקורת תורנית עצמאית טרם הושלמה. היישומים הפרשניים מובחנים מלשון המקור.') if not released else label('Study text with documented source references. See our editorial method for review scope.','טקסט לימודי עם מראי מקומות מתועדים. היקף הביקורת מפורט בדרך העריכה.')} {label('Revision','גרסה')} {e['revision']}.</p></article></div></main>'''
    return layout(e['title']['en'] + (' · Sources' if sheet else ''),body,prefix,e['summary']['en'])


def home(editions, ledger, now):
    released = {r['id'] for r in ledger['releases']}
    latest = editions[0] if editions else None
    if latest:
        e = latest
        target = f'./shiur/{e["id"]}/'
        m = minutes(e)
        year = dates.GregorianDate.from_pydate(date.fromisoformat(e['target_shabbat'])).to_heb().year
        feature = f'''<a class="feature-card" href="{target}" aria-label="{escape(e['title']['en'],quote=True)}"><div class="feature-top"><span>{pair(e['parashah'])}</span><span>{len(editions):02} / {year}</span></div><div class="cover-ornament" aria-hidden="true"><span lang="he" dir="rtl">{escape(e['parashah']['he'])}</span><div></div></div><div class="cover-bottom"><div class="eyebrow">{label('Featured study','השיעור הנבחר')}</div><h2>{pair(e['title'])}</h2><p>{pair(e['subtitle'])}</p><div class="cover-link">{label('Open the shiur','פתיחת השיעור')} <span aria-hidden="true">↗</span></div></div></a>'''
        card = f'''<article class="edition-card" data-search="{escape(' '.join([e['title']['en'],e['title']['he'],e['summary']['en'],e['summary']['he'],e['parashah']['en'],e['parashah']['he']]),quote=True)}" data-category="{e['category']}"><div class="edition-number">01<span>5787</span></div><div class="edition-card-body"><div class="eyebrow">{pair(e['parashah'])} · {date_label(e)}</div><h3><a href="{target}">{pair(e['title'])}</a></h3><p>{pair(e['summary'])}</p><div class="card-meta">{label(str(m['en'])+' min read',str(m['he'])+' דקות קריאה')} · {label(str(len(e['source_ids']))+' sources',str(len(e['source_ids']))+' מקורות')}<span class="small-status">{status_label(e,e['id'] in released)}</span></div></div><a class="card-arrow" href="{target}" aria-label="{escape(e['title']['en'],quote=True)}">↗</a></article>'''
        lead = f'<a class="button primary" href="{target}">{label("Read the shiur" if e["id"] in released else "Read the pilot shiur","לקריאת השיעור" if e["id"] in released else "לקריאת שיעור הניסיון")} <span aria-hidden="true">↗</span></a>'
    else:
        feature = f'<div class="feature-card empty-feature">{label("The next chapter begins here.","כאן מתחיל פרק חדש.","h2")}</div>'
        card = label('The first edition is being prepared.','המהדורה הראשונה בהכנה.','p')
        lead = '<a class="button primary" href="#path">'+label('Explore the learning path','למסלול הלימוד')+'</a>'
    # All visible lessons, not only the featured edition, belong in the archive.
    cards = []
    for i,e in enumerate(editions):
        m = minutes(e)
        target = f'./shiur/{e["id"]}/'
        search = ' '.join([e['title']['en'],e['title']['he'],e['summary']['en'],e['summary']['he'],e['parashah']['en'],e['parashah']['he']] + [p for s in e['sections'] for lang in ('en','he') for p in s[lang]])
        cards.append(f'<article class="edition-card" data-search="{escape(search,quote=True)}" data-category="{e["category"]}"><div class="edition-number">{len(editions)-i:02}<span>{dates.GregorianDate.from_pydate(date.fromisoformat(e["target_shabbat"])).to_heb().year}</span></div><div class="edition-card-body"><div class="eyebrow">{pair(e["parashah"])} · {date_label(e)}</div><h3><a href="{target}">{pair(e["title"])}</a></h3><p>{pair(e["summary"])}</p><div class="card-meta">{label(str(m["en"])+" min read",str(m["he"])+" דקות קריאה")} · {label(str(len(e["source_ids"]))+" sources",str(len(e["source_ids"]))+" מקורות")}<span class="small-status">{status_label(e,e["id"] in released)}</span></div></div><a class="card-arrow" href="{target}" aria-label="{escape(e["title"]["en"],quote=True)}">↗</a></article>')
    rotation = ''.join(f'<article class="path-item"><span class="path-no">0{i+1}</span><h3>{label(*CATEGORIES[cat])}</h3><p>{label(*text)}</p></article>' for i,(cat,text) in enumerate([
        ('tanach',('A close reading. A clear question. A conversation with the commentators.','קריאה מדויקת. שאלה בהירה. שיחה עם המפרשים.')),
        ('halacha',('Follow a question through its sources, distinctions, and differing views.','מלווים שאלה דרך מקורותיה, הבחנותיה וריבוי הדעות.')),
        ('mussar',('Bring the learning into character, prayer, and everyday responsibility.','מחברים את הלימוד למידות, לתפילה ולאחריות היומיומית.')),
        ('mikdash',('Study sacred service, Jerusalem, and the life of a community.','לומדים על עבודת הקודש, ירושלים וחיי הציבור.'))]))
    weeks = upcoming_calendar(now,5)
    rows = ''.join(f'<div class="calendar-row"><span>{date_label({"target_shabbat":w["target_shabbat"]})}</span><strong>{pair(w["israel"])}</strong><span class="calendar-status">{label("Calendar preview","תצוגת לוח")}</span></div>' for w in weeks)
    body = f'''<main id="main"><section class="hero"><div class="hero-copy"><div class="eyebrow"><span class="gold-rule"></span>{label('A weekly Beit Midrash · English & Hebrew','בית מדרש שבועי · אנגלית ועברית')}</div><h1>{label('A week. A question. A deeper understanding.','שבוע אחד. שאלה אחת. הבנה עמוקה יותר.')}</h1><p class="hero-description">{label('Make room for a thoughtful encounter with Torah. One focused shiur, original sources, and two languages brought into conversation.','מפנים מקום למפגש מעמיק עם התורה. שיעור ממוקד, מקורות מקוריים ושתי שפות הנפגשות בלימוד אחד.')}</p><div class="hero-actions">{lead}<a class="text-link" href="./about/">{label('Discover our approach →','על דרך הלימוד ←')}</a></div><div class="hero-footnote">{label('A new learning project in the Sanhedrin community.','מיזם לימוד חדש לצד קהילת סנהדרין.')}</div></div>{feature}</section>
<section class="principles" aria-label="Learning principles"><div>{label('Source-led','מתחילים במקור','strong')}{label('Read the text, then follow the argument.','קוראים את הכתוב, וממנו מפתחים את העיון.')}</div><div>{label('Two languages, one study','שתי שפות, לימוד אחד','strong')}{label('English, Hebrew, or both side by side.','אנגלית, עברית או שתיהן זו לצד זו.')}</div><div>{label('A rhythm for the year','קצב לימוד לאורך השנה','strong')}{label('Parashah, festivals, and a wider horizon.','פרשה, מועדים ואופק לימודי רחב.')}</div></section>
<section id="library" class="library-section"><div class="section-heading"><div><div class="eyebrow">{label('The study collection','ספריית הלימוד')}</div><h2>{label('Begin here. Return often.','מתחילים כאן. חוזרים ללמוד.')}</h2></div><span class="collection-count">{label(str(len(editions))+(' available study' if len(editions)==1 else ' available studies'),str(len(editions))+' שיעורים זמינים')}</span></div><div class="library-tools"><label class="search-label" for="search">{label('Search the library','חיפוש בספרייה')}<input id="search" type="search" placeholder="Noach, responsibility… / נח, אחריות…" autocomplete="off"></label><label class="filter-label" for="category">{label('Study focus','תחום הלימוד')}<select id="category"><option value="all" data-en="All studies" data-he="כל השיעורים">All studies</option>{''.join(f'<option value="{k}" data-en="{v[0]}" data-he="{v[1]}">{v[0]}</option>' for k,v in CATEGORIES.items())}</select></label></div><div id="edition-list">{''.join(cards) or card}</div><p id="no-results" hidden role="status">{label('No studies match your search. Try another word or focus.','לא נמצאו שיעורים מתאימים. נסו מילה או תחום אחר.')}</p><p id="search-status" class="sr-only" aria-live="polite"></p></section>
<section id="path" class="path-section"><div class="section-heading"><div><div class="eyebrow">{label('One thread, many perspectives','חוט אחד, מבטים רבים')}</div><h2>{label('A learning path through the year','מסלול לימוד לאורך השנה')}</h2></div><p>{label('The weekly parashah gives us a frame. Festivals take their place in the calendar. Four perspectives keep the learning open and connected.','פרשת השבוע מעניקה מסגרת. המועדים מקבלים את מקומם בלוח, וארבע נקודות מבט שומרות על לימוד מגוון ומחובר.')}</p></div><div class="path-grid">{rotation}</div></section>
<section class="calendar-section"><div><div class="eyebrow">{label('Looking ahead · Israel reading cycle','מבט קדימה · סדר הקריאה בארץ ישראל')}</div><h2>{label('The weeks ahead','השבועות הבאים')}</h2><p>{label('These are calendar readings, not announcements of completed lessons. Each shiur appears after its editorial preparation.','אלה נתוני לוח הקריאה, ולא הודעה על שיעורים מוכנים. כל שיעור יופיע לאחר הכנתו ועריכתו.')}</p><a class="text-link" href="./about/">{label('How editions are prepared →','כיצד מכינים את השיעורים ←')}</a></div><div class="calendar-list">{rows}<p class="calendar-credit">{label('Calendar calculated with pyluach · Israel / Diaspora differences appear in the calendar data.','הלוח מחושב באמצעות pyluach · הבדלים בין ארץ ישראל לחו״ל מופיעים בנתוני הלוח.')}</p></div></section></main>'''
    return layout('Weekly Torah learning · שיעור השבוע',body)


def library_page():
    body=f'''<main id="main" class="source-main"><header class="source-intro"><div class="eyebrow">{label('A wider Beit Midrash','בית מדרש רחב יותר')}</div><h1>{label('Go back to the sources.','חוזרים למקורות.')}</h1><p>{label('Search the Sanhedrin responsa archive. Find a work in the Sefaria export library. Read, compare, and preserve the exact passages that support your learning.','חפשו בארכיון השאלות והתשובות של סנהדרין. מצאו חיבור בספריית היצוא של ספריא. קראו ושמרו את הקטעים המדויקים שעליהם נשען הלימוד.')}</p></header>
<div class="connection-strip"><div><strong>Sanhedrin · סנהדרין</strong><span id="sanhedrin-state" role="status">{label('Connecting…','מתחברים…')}</span></div><div><strong>Sefaria · ספריא</strong><span id="sefaria-state" role="status">{label('Loading book catalogue…','טוענים את קטלוג הספרים…')}</span></div></div>
<form id="source-search" class="source-search"><label for="source-query">{label('Search topic, title, or Hebrew term','חיפוש נושא, כותרת או מונח בעברית')}<input id="source-query" type="search" placeholder="Noah / נח / Rashi / רש״י" maxlength="200"></label><label for="source-provider">{label('Library','ספרייה')}<select id="source-provider"><option value="all" data-en="Both libraries" data-he="שתי הספריות">Both libraries</option><option value="sanhedrin">Sanhedrin · סנהדרין</option><option value="sefaria">Sefaria · ספריא</option></select></label><button class="button primary" type="submit">{label('Search','חיפוש')} ↗</button></form>
<p class="source-help">{label('Sanhedrin searches questions and answers. Sefaria searches book titles and categories; choose a category, work, and section below to read a particular passage.','סנהדרין מחפש בשאלות ובתשובות. ספריא מחפש בשמות חיבורים וקטגוריות; לקריאת קטע מסוים בחרו למטה קטגוריה, חיבור וקטע.')}</p>
<section class="sefaria-browser" aria-labelledby="sefaria-browser-title"><div class="picker-heading"><h2 id="sefaria-browser-title">{label('Browse Sefaria','עיון בספריא')}</h2><p class="source-help">{label('Choose a category and a book. Its available chapters, pages, or named sections will appear automatically.','בחרו קטגוריה וחיבור. הפרקים, הדפים או הקטעים הזמינים בו יופיעו אוטומטית.')}</p></div>
<form id="sefaria-picker" class="sefaria-picker"><div class="picker-catalogue"><label for="sefaria-category">{label('1 · Category','1 · קטגוריה')}<select id="sefaria-category" disabled><option data-en="Loading categories…" data-he="טוענים קטגוריות…">Loading categories…</option></select></label><label for="sefaria-book-filter">{label('Find a book · English or Hebrew','איתור חיבור · אנגלית או עברית')}<input id="sefaria-book-filter" type="search" maxlength="200" placeholder="Genesis / בראשית / Rashi / רש״י" autocomplete="off" disabled></label><label for="sefaria-book" class="book-choice">{label('2 · Book','2 · חיבור')}<select id="sefaria-book" size="6" aria-describedby="sefaria-book-count" disabled></select></label><p id="sefaria-book-count" class="source-help" role="status"></p></div><div class="picker-passage"><label for="sefaria-section">{label('3 · Chapter, page, or section','3 · פרק, דף או קטע')}<select id="sefaria-section" disabled><option data-en="Choose a book first" data-he="בחרו תחילה חיבור">Choose a book first</option></select></label><div id="sefaria-levels"></div><label for="reference-language">{label('Text language','שפת המקור')}<select id="reference-language"><option value="Hebrew" data-en="Hebrew" data-he="עברית">Hebrew</option><option value="English" data-en="English" data-he="אנגלית">English</option></select></label><p id="sefaria-picker-state" class="source-help" role="status" aria-live="polite"></p><output id="selected-reference" dir="auto" aria-label="Selected Sefaria reference"></output><div id="selected-export" class="source-help"></div><button id="read-selection" class="button primary" type="submit" disabled>{label('Read selected passage','קריאת הקטע שנבחר')} ↗</button><button id="retry-sefaria" class="text-link" type="button" hidden>{label('Try loading again','ניסיון טעינה נוסף')}</button></div></form>
<details class="manual-reference"><summary>{label('Enter an exact reference manually','הזנת מראה מקום מדויק ידנית')}</summary><form id="reference-form" class="reference-form"><label for="exact-reference">{label('Exact Sefaria reference','מראה מקום מדויק בספריא')}<input id="exact-reference" placeholder="Genesis 6:9 / Rashi on Genesis 6:9:1" maxlength="240" required></label><button class="button" type="submit">{label('Read passage','קריאת הקטע')} ↗</button></form></details></section>
<div id="source-feedback" role="status" aria-live="polite"></div><div class="source-workspace"><section id="source-results" aria-label="Source search results"></section><aside id="source-reader" aria-label="Selected source"><div class="reader-placeholder"><span class="brand-mark" aria-hidden="true">ש</span><h2>{label('A source, in its own words.','המקור, בלשונו.')}</h2><p>{label('Select a result to read it here. Source dossiers preserve the text, reference, author, version, and retrieval date for editorial use.','בחרו תוצאה לקריאה כאן. תיק המקור שומר את הטקסט, מראה המקום, המחבר, הגרסה ותאריך השליפה לצורכי עריכה.')}</p></div></aside></div>
<noscript><p>{label('The source search requires JavaScript. You can also open the original libraries directly.','חיפוש המקורות דורש JavaScript. אפשר לפתוח את הספריות המקוריות ישירות.')}</p></noscript><div class="library-origin"><a href="https://shekhina.org/">Sanhedrin ↗</a><a href="https://github.com/Moriahise/sefaria-studio">Sefaria Studio ↗</a><a href="https://github.com/Sefaria/Sefaria-Export">Sefaria Export ↗</a><p>{label('External records remain at their source. A research dossier is not a scholarly approval or an automatic addition to a shiur.','הרשומות החיצוניות נשארות במקורן. תיק מחקר אינו אישור תורני ואינו מתווסף לשיעור באופן אוטומטי.')}</p></div></main>'''
    return layout('Source libraries · ספריות המקורות',body,'../',libraries=True)


def about():
    blocks = [
        ('Connected source libraries','ספריות מקורות מחוברות','The source research view reads the published Sanhedrin archive and the Sefaria work catalogue, including the Google Cloud Storage exports prepared in Sefaria Studio. Search results can be read and saved as attributed research dossiers. They do not automatically become a published lesson or a scholarly approval.','תצוגת חקר המקורות קוראת את ארכיון סנהדרין שפורסם ואת קטלוג ספריא, לרבות קובצי היצוא ב־Google Cloud Storage שהוכנו ב־Sefaria Studio. אפשר לקרוא תוצאות ולשמור אותן כתיקי מחקר עם ייחוס. הן אינן נעשות שיעור מפורסם או אישור תורני באופן אוטומטי.'),
        ('A Beit Midrash with a clear purpose','בית מדרש עם תכלית ברורה','Shiurim is an independent weekly study project alongside the Sanhedrin responsa archive. It brings one focused line of learning into English and Hebrew, with original sources close at hand.','שיעורים הוא מיזם לימוד שבועי עצמאי לצד ארכיון השאלות והתשובות של סנהדרין. הוא מציע מהלך לימודי ממוקד באנגלית ובעברית, כשהמקורות המקוריים קרובים לעין.'),
        ('How a study is built','כיצד נבנה שיעור','Each edition begins with a guiding question and a source dossier. The argument is developed in paired sections. Hebrew and English carry the same references, qualifications, and conclusions. Quoted text, interpretation, and ethical application are kept distinct.','כל מהדורה מתחילה בשאלה מנחה ובתיק מקורות. מהלך הלימוד נבנה בסעיפים מקבילים. העברית והאנגלית נושאות אותם מראי מקומות, סייגים ומסקנות. לשון המקור, הפרשנות והיישום המוסרי מובחנים זה מזה.'),
        ('The pilot stage','שלב הניסיון','The first edition is an AI-assisted editorial pilot. Its Hebrew passages have been retrieved from Sefaria, preserved with provenance and checksums, and linked to the discussion. Independent scholarly review has not yet been completed. A pilot label is not a claim of rabbinical approval.','המהדורה הראשונה היא מהדורת ניסיון מערכתית בסיוע בינה מלאכותית. פסוקיה העבריים נשלפו מספריא, נשמרו עם פרטי מקור וחתימות בדיקה וקושרו לדיון. ביקורת תורנית עצמאית טרם הושלמה. סימון מהדורת הניסיון אינו טענה לאישור רבני.'),
        ('A weekly rhythm, introduced carefully','קצב שבועי הנבנה בהדרגה','The planned release rhythm is Thursday evening in Israel time, with earlier preparation around festivals. The publication system only admits explicitly reviewed editions. Automatic release is initially disabled while the pilot is being evaluated. Calendar previews are not promises that a lesson is already written.','הקצב המתוכנן הוא פרסום ביום חמישי בערב לפי שעון ישראל, עם הכנה מוקדמת סביב מועדים. מערכת הפרסום מקבלת רק מהדורות שאושרו במפורש. הפרסום האוטומטי מושבת בתחילה בזמן בחינת הניסיון. תצוגת לוח אינה הבטחה ששיעור כבר נכתב.'),
        ('Sources and attribution','מקורות וייחוס','The source sheet gives the work, location, Hebrew text version, license label, and original link. The initial Hebrew passages are from Miqra according to the Masorah via Sefaria (CC-BY-SA). The wording is preserved. English discussion is written for this project; an existing copyrighted English translation has not been copied into the lesson.','בדף המקורות מופיעים החיבור, המקום המדויק, גרסת הטקסט העברי, סימון הרישיון וקישור המקור. הפסוקים העבריים הראשונים הם ממהדורת מקרא על פי המסורה באמצעות ספריא (CC-BY-SA). לשונם נשמרת. הדיון באנגלית נכתב למיזם זה; תרגום אנגלי קיים המוגן בזכויות לא הועתק לשיעור.'),
        ('Study and practical decisions','לימוד והכרעות מעשיות','The series offers learning, including the careful presentation of differing views. It does not attribute participation to a rabbi who has not reviewed an edition. Personal halachic questions require attention to individual circumstances and an appropriate rabbinical authority.','הסדרה מיועדת ללימוד, ובכלל זה להצגה מדויקת של דעות שונות. היא אינה מייחסת השתתפות לרב שלא בדק מהדורה. שאלות הלכתיות אישיות דורשות תשומת לב לנסיבות הפרטיות ולסמכות תורנית מתאימה.'),
    ]
    body = '<main id="main" class="about-main"><div class="eyebrow">'+label('Our approach','דרך הלימוד')+'</div><h1>'+label('Careful sources. Thoughtful learning.','מקורות מדויקים. לימוד מעמיק.')+'</h1>'+''.join('<section><h2>'+label(en,he)+'</h2><div class="paragraph-pair">'+label(pen,phe,'p')+'</div></section>' for en,he,pen,phe in blocks)+'</main>'
    return layout('Our approach · דרך הלימוד',body,'../')


def build(now, root=ROOT):
    config, sources, editions, ledger = load_all(root)
    released = {r['id'] for r in ledger['releases']}
    visible = [e for e in editions if e['id'] in released or (config['pilot_visible'] and e['status']=='pilot')]
    visible.sort(key=lambda e:(e['target_shabbat'],e['id']),reverse=True)
    with publisher_lock(root):
        temp = Path(tempfile.mkdtemp(prefix='.build-',dir=root))
        try:
            shutil.copytree(root/'assets',temp/'assets')
            (temp/'index.html').write_text(home(visible,ledger,now),encoding='utf-8')
            (temp/'about').mkdir()
            (temp/'about/index.html').write_text(about(),encoding='utf-8')
            (temp/'sources').mkdir()
            (temp/'sources/index.html').write_text(library_page(),encoding='utf-8')
            reviewer=review_tools()
            policy=read(root/'config/preflight.json')
            (temp/'review').mkdir()
            report_links=[]
            for e in visible:
                report=reviewer.current_report(root,e,sources,policy)
                report_dir=temp/'review'/e['id'];report_dir.mkdir()
                report_html=layout('Content preflight · '+e['title']['en'],reviewer.report_body(report,e,pair),'../../',review=True)
                (report_dir/'index.html').write_text(report_html,encoding='utf-8')
                report_links.append(f'<article class="review-card"><h2><a href="./{e["id"]}/">{pair(e["title"])}</a></h2><p>{label("Automatic preliminary checks; scholarly approval is separate.","בדיקות מקדימות אוטומטיות; האישור התורני נפרד.")}</p><p>{report["summary"]["errors"]} {label("blocking findings","ממצאים חוסמים")} · {report["summary"]["warnings"]} {label("inspection notes","הערות לבדיקה")}</p></article>')
                write(temp/'data/preflight'/(e['id']+'.json'),reviewer.public_report(report))
            review_body='<main id="main" class="review-main"><header class="review-header"><div class="eyebrow">'+label('Editorial transparency','שקיפות מערכתית')+'</div><h1>'+label('Content preflight reports','דוחות בדיקה מקדימה לתוכן')+'</h1><p>'+label('These reports record preliminary checks and remaining questions. They do not grant scholarly approval.','הדוחות מתעדים בדיקות מקדימות ושאלות שנותרו. הם אינם מעניקים אישור תורני.')+'</p></header>'+''.join(report_links)+'</main>'
            (temp/'review/index.html').write_text(layout('Content preflight reports',review_body,'../',review=True),encoding='utf-8')
            for e in visible:
                directory=temp/'shiur'/e['id']
                (directory/'sources').mkdir(parents=True)
                (directory/'index.html').write_text(lesson(e,sources,e['id'] in released),encoding='utf-8')
                (directory/'sources/index.html').write_text(lesson(e,sources,e['id'] in released,True),encoding='utf-8')
            (temp/'data').mkdir(exist_ok=True)
            catalogue_path=root/'content/library-catalogue/sefaria.json.gz'
            if catalogue_path.exists():
                catalogue_raw=gzip.decompress(catalogue_path.read_bytes())
                catalogue=json.loads(catalogue_raw)
                if catalogue.get('schema')!=1 or not isinstance(catalogue.get('works'),list):
                    raise ValidationError('Invalid Sefaria catalogue')
                (temp/'data/sefaria-library.json').write_bytes(catalogue_raw)
            health_path=root/'reports/libraries-health.json'
            if health_path.exists():
                shutil.copyfile(health_path,temp/'data/libraries-status.json')
            write(temp/'data/calendar.json',{'schema':1,'calculated_at':now.isoformat(),'timezone':'Asia/Jerusalem','weeks':upcoming_calendar(now,52)})
            write(temp/'data/catalogue.json',{'schema':1,'editions':[{'id':e['id'],'title':e['title'],'parashah':e['parashah'],'target_shabbat':e['target_shabbat'],'category':e['category'],'status':'published' if e['id'] in released else 'pilot'} for e in visible]})
            write(temp/'data/status.json',{'schema':1,'built_at':now.isoformat(),'published_editions':len(released),'pilot_editions':len([e for e in visible if e['status']=='pilot']),'automatic_publication':config['automatic_publication'],'next_steps':'Pilot scholarly review; then enable reviewed queue publication.'})
            # Only source passages actually used in public editions enter the export.
            used={sid for e in visible for sid in e['source_ids']}
            write(temp/'data/source-provenance.json',{'schema':1,'sources':[sources[sid] for sid in sorted(used)]})
            (temp/'.nojekyll').touch()
            (temp/'404.html').write_text(layout('Page not found', '<main id="main" class="about-main"><h1>'+label('This page could not be found.','הדף לא נמצא.')+'</h1><a href="'+escape(config['base_url'],quote=True)+'">'+label('Return to Shiurim','חזרה לשיעורים')+'</a></main>',config['base_url']),encoding='utf-8')
            (temp/'robots.txt').write_text('User-agent: *\nAllow: /\n',encoding='utf-8')
            urls=['', 'about/', 'sources/', 'review/']+[f'shiur/{e["id"]}/' for e in visible]
            (temp/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(config['base_url']+u)+'</loc></url>' for u in urls)+'</urlset>',encoding='utf-8')
            validate_export(temp)
            output=root/'dist'
            previous=None
            if output.exists():
                previous=root/'reports'/('previous-site-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f'))
                previous.parent.mkdir(exist_ok=True)
                output.replace(previous)
            try:
                temp.replace(output)
            except Exception:
                if previous:
                    previous.replace(output)
                raise
        finally:
            if temp.exists():
                shutil.rmtree(temp)
    return {'visible_editions':len(visible),'output':str(root/'dist')}


def validate_export(folder):
    from html.parser import HTMLParser
    class Links(HTMLParser):
        def __init__(self):
            super().__init__();self.links=[];self.ids=[]
        def handle_starttag(self, tag, attrs):
            a=dict(attrs)
            if 'id' in a:self.ids.append(a['id'])
            if tag in ('a','link','script'):
                self.links.append(a.get('href') if tag!='script' else a.get('src'))
    total=0
    for page in folder.rglob('*.html'):
        parser=Links();parser.feed(page.read_text())
        if len(parser.ids)!=len(set(parser.ids)):
            raise ValidationError(f'Duplicate HTML IDs in {page}')
        for href in parser.links:
            if not href or urlparse(href).scheme or href.startswith('//'):continue
            pathname,_,anchor=href.partition('#')
            target=(page.parent/pathname).resolve() if pathname else page.resolve()
            if not target.is_relative_to(folder.resolve()):raise ValidationError('Escaping export link')
            if target.is_dir():target=target/'index.html'
            if not target.exists():raise ValidationError(f'Broken link: {page.name} -> {href}')
            if anchor and target.suffix=='.html':
                other=Links();other.feed(target.read_text())
                if anchor not in other.ids:raise ValidationError(f'Broken anchor: {href}')
        total+=page.stat().st_size
    if total>20_000_000:raise ValidationError('Export exceeds pilot size budget')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['validate','build','publish-due','calendar','review-digest'])
    p.add_argument('--now',help='ISO timestamp with explicit timezone')
    p.add_argument('--id',help='Edition ID for review-digest')
    args=p.parse_args()
    try:
        now=now_value(args.now)
        if args.command=='validate':
            _,sources,editions,_=load_all();result={'valid':True,'editions':len(editions),'sources':len(sources)}
        elif args.command=='build':result=build(now)
        elif args.command=='publish-due':result=publish_due(now)
        elif args.command=='calendar':result=upcoming_calendar(now,52)
        else:
            _,sources,editions,_=load_all(); e=next((e for e in editions if e['id']==args.id),None)
            if not e:raise ValidationError('Edition not found')
            result={'id':e['id'],'revision':e['revision'],'content_sha256':digest(e,sources)}
        print(json.dumps(result,ensure_ascii=False,indent=2))
    except (ValidationError,KeyError,ValueError) as exc:
        print('Validation failed: '+str(exc),file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
