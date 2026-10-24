"""Add sourced First Year essences to the 5787 deployment copy only."""
from __future__ import annotations

import argparse
from datetime import date
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from reader.portraits import Document

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'reader/ben-ish-chai/5787.json'
MARKER = 'data-ben-ish-chai'
STYLESHEET = 'ben-ish-chai.css'
FESTIVALS = {'ראש השנה', 'יום כיפור', 'יום כפור', 'סוכות', 'פסח', 'שבועות',
             'שמיני עצרת', 'שמחת תורה', 'חנוכה', 'פורים'}


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text)
                   if c.isalpha() and not unicodedata.combining(c))


def load(path=DATA):
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema') != 1 or data.get('reading_cycle') != 5787:
        raise ValueError('Unexpected Ben Ish Chai reading cycle')
    date.fromisoformat(data['cycle_start']); date.fromisoformat(data['next_cycle_start'])
    entries = data['editions']
    if [e['number'] for e in entries] != list(range(1, 55)):
        raise ValueError('All 54 individual Parashot must have an essence')
    if len({normalize(e['parashah']['he']) for e in entries}) != 54:
        raise ValueError('Duplicate Parashah in the First Year collection')
    for entry in entries:
        for name in ('parashah', 'title', 'essence'):
            pair = entry[name]
            if set(pair) != {'en', 'he'} or not pair['en'].strip() or not re.search('[א-ת]', pair['he']):
                raise ValueError('An English/Hebrew essence is incomplete')
        source = entry['source']
        if source['year'] != 1 or not re.fullmatch(r'BIH-\d{7}', source['segment_id']):
            raise ValueError('Only identified Shana Rishona passages may be used')
        raw = json.dumps({k: source[k] for k in ('he', 'en')}, ensure_ascii=False, sort_keys=True)
        if not source['en'].strip() or sha256(raw.encode()).hexdigest() != source['sha256']:
            raise ValueError('The bilingual source passage has changed')
    return data


def resolve(parashah, data):
    """Resolve Hebrew spellings and doubled portions without using the lesson title."""
    name = normalize(parashah['he'])
    if name.startswith('פרשת'): name = name[len('פרשת'):]
    if name in {normalize(n) for n in FESTIVALS}: return []
    for alias, canonical in data['aliases'].items():
        name = name.replace(normalize(alias), normalize(canonical))
    entries = sorted(data['editions'], key=lambda e: len(normalize(e['parashah']['he'])), reverse=True)
    found = []
    while name:
        entry = next((e for e in entries if name.startswith(normalize(e['parashah']['he']))), None)
        if entry is None:
            raise ValueError('No exact First Year source mapping for ' + parashah['he'])
        found.append(entry)
        name = name[len(normalize(entry['parashah']['he'])):]
    if len(found) > 2 or len({e['number'] for e in found}) != len(found):
        raise ValueError('Unexpected combined Parashah')
    return found


def pair(value, tag='span', cls=''):
    return ''.join(f'<{tag} class="l-{lang} {cls}" lang="{lang}" dir="'
                   + ('rtl' if lang == 'he' else 'ltr') + '">'
                   + escape(value[lang]) + f'</{tag}>' for lang in ('en', 'he'))


def component(entries):
    studies = []
    for entry in entries:
        source = entry['source']
        section = {'en': 'Introduction', 'he': 'פתיחה'} if source['section'] == 'introduction' else {
            'en': '§' + source['section'], 'he': 'סעיף ' + source['section']}
        reference = {lang: source['chapter'][lang] + ' · ' + section[lang] for lang in ('en', 'he')}
        studies.append('<div class="bic-study" data-bic-parashah="' + str(entry['number']) + '">'
                       + '<p class="bic-parashah">' + pair(entry['parashah']) + '</p>'
                       + '<h3>' + pair(entry['title']) + '</h3>'
                       + '<div class="paragraph-pair bic-copy">' + pair(entry['essence'], 'p') + '</div>'
                       + '<p class="bic-source">' + pair(reference) + '</p></div>')
    return ('<section class="ben-ish-chai-essence" ' + MARKER + '="5787" aria-labelledby="bic-heading">'
            + '<div class="bic-heading"><h2 id="bic-heading">'
            + pair({'en': 'Ben Ish Chai · Essence', 'he': 'בן איש חי · תמצית'}) + '</h2>'
            + '<p class="bic-year"><span class="l-en" lang="en" dir="ltr">'
            + '<em>Shana Rishona</em><strong>First Year</strong></span>'
            + '<span class="l-he" lang="he" dir="rtl"><strong>שנה ראשונה</strong></span></p></div>'
            + ''.join(studies) + '</section>')


def render(text, entries, prefix='../../'):
    doc = Document(text)
    questions = [n for n in doc.nodes if n.has('guiding-question')]
    if len(questions) != 1:
        raise ValueError('Expected one guiding question on the Parashah lesson')
    existing = [n for n in doc.nodes if MARKER in n.attrs]
    if len(existing) > 1: raise ValueError('Duplicate First Year essence')
    markup = component(entries)
    edits = [(existing[0].start, existing[0].end, markup)] if existing else [
        (questions[0].start, questions[0].start, markup)]
    href = prefix + 'assets/' + STYLESHEET
    if not any(n.tag == 'link' and n.attrs.get('href') == href for n in doc.nodes):
        head = next(n for n in doc.nodes if n.tag == 'head')
        edits.append((head.closing_start, head.closing_start,
                      '<link rel="stylesheet" href="' + href + '">\n'))
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def apply(site, data_path=DATA):
    data = load(data_path)
    catalogue = json.loads((site / 'data/catalogue.json').read_text(encoding='utf-8'))
    changed = []
    for edition in catalogue['editions']:
        # The reading cycle includes its closing readings after Rosh Hashanah.
        if not data['cycle_start'] <= edition['target_shabbat'] < data['next_cycle_start']:
            continue
        entries = resolve(edition['parashah'], data)
        if not entries: continue
        eid = edition['id']
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', eid): raise ValueError('Unsafe lesson identity')
        page = site / 'shiur' / eid / 'index.html'
        original = page.read_text(encoding='utf-8')
        updated = render(original, entries)
        if updated != original:
            page.write_text(updated, encoding='utf-8')
            changed.append(eid)
    if changed:
        shutil.copyfile(ROOT / 'reader' / STYLESHEET, site / 'assets' / STYLESHEET)
    return {'reading_cycle': 5787, 'prepared_parashot': len(data['editions']), 'updated_lessons': changed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=ROOT / '_site')
    args = parser.parse_args()
    print(json.dumps(apply(args.site), ensure_ascii=False))


if __name__ == '__main__': main()
