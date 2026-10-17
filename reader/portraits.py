"""Add collection portraits to the validated public reader export at Pages build time.

The original reader export and its lesson text are preserved; only a separate
deployment copy receives the portrait components and styles.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass, field
from hashlib import sha256
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
MARKER = 'data-rabbi-portrait'
FESTIVALS = {
    'pesach': 54, 'passover': 54,
    'rosh hashana': 55, 'rosh hashanah': 55,
    'succos': 56, 'sukkos': 56, 'sukkot': 56,
    'yom kippur': 57, 'shavuos': 58, 'shavuot': 58,
    'shemini atzeret': 59, 'shmini atzeret': 59,
    'simchat torah': 60, 'simchas torah': 60,
    'chanukah': 61, 'hanukkah': 61, 'purim': 62,
}
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}


@dataclass
class Node:
    tag: str
    attrs: dict
    start: int
    opening_end: int
    closing_start: int = 0
    end: int = 0
    children: list = field(default_factory=list)

    def has(self, name):
        return name in self.attrs.get('class', '').split()


class Document(HTMLParser):
    """Locate component boundaries without reserializing the lesson prose."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.lines = [0]
        self.lines.extend(m.end() for m in re.finditer('\n', text))
        self.nodes = []
        self.stack = []
        self.feed(text)
        self.close()

    def position(self):
        line, column = self.getpos()
        return self.lines[line - 1] + column

    def handle_starttag(self, tag, attrs):
        start = self.position()
        node = Node(tag, dict(attrs), start, start + len(self.get_starttag_text()))
        self.nodes.append(node)
        if self.stack: self.stack[-1].children.append(node)
        if tag in VOID: node.closing_start = node.end = node.opening_end
        else: self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            node = self.stack.pop()
            node.closing_start = node.end = node.opening_end

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                node = self.stack[index]
                node.closing_start = self.position()
                node.end = self.text.index('>', node.closing_start) + 1
                del self.stack[index:]
                break

    def inside(self, outer, class_name):
        return [n for n in self.nodes if outer.opening_end <= n.start < outer.closing_start and n.has(class_name)]


def load_profiles(path):
    value = json.loads(path.read_text(encoding='utf-8'))
    profiles = value['profiles']
    if value.get('schema') != 1 or len(profiles) < 63: raise ValueError('Portrait collection is incomplete')
    for key in ('id', 'image', 'source_blob_sha'):
        if len({p[key] for p in profiles}) != len(profiles): raise ValueError('Duplicate portrait: ' + key)
    for p in profiles:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', p['id']): raise ValueError('Unsafe portrait ID')
        if p['image'] != 'assets/portraits/' + p['id'] + '.webp': raise ValueError('Unsafe portrait path')
        if not isinstance(p['name'], str) or not p['name'].strip(): raise ValueError('Portrait name missing')
    return profiles


def profile_for(edition, number, profiles):
    """Fixed portion slots survive publication order and later archive additions.

    Doubled portions use their first portion's slot. Festival slots cannot collide
    with Torah slots. Next cycles rotate the same stable ordered collection.
    """
    if number is not None:
        if not 1 <= number <= 54: raise ValueError('Invalid portion number')
        slot = number - 1
    else:
        name = ' '.join(edition['parashah']['en'].casefold().replace('-', ' ').split())
        if name not in FESTIVALS: raise ValueError('Unknown festival portrait slot: ' + name)
        slot = FESTIVALS[name]
    match = re.match(r'^(\d{4})-', edition['id'])
    cycle = int(match[1]) if match else 5787
    return profiles[(slot + (cycle - 5787) * 55) % len(profiles)]


def portion_number(text):
    doc = Document(text)
    header = next(n for n in doc.nodes if n.has('lesson-header'))
    eyebrow = doc.inside(header, 'eyebrow')[0]
    label = doc.inside(eyebrow, 'l-en')[0]
    wording = unescape(re.sub('<[^>]*>', '', text[label.opening_end:label.closing_start])).strip()
    match = re.match(r'^(\d{2})(?:[–-]\d{2})?\s', wording)
    return int(match[1]) if match else None


def figure(profile, prefix, variant):
    name = escape(profile['name'])
    return ('<figure class="rabbi-portrait rabbi-portrait--' + variant + '" ' + MARKER + '="' + profile['id'] + '">'
            '<img src="' + prefix + profile['image'] + '" alt="' + escape(profile['name'], quote=True) + '" '
            'width="420" height="420" decoding="async" loading="' + ('lazy' if variant == 'card' else 'eager') + '">'
            '<figcaption><span class="portrait-label l-en" lang="en" dir="ltr">Rabbi portrait</span>'
            '<span class="portrait-label l-he" lang="he" dir="rtl">דיוקן רב</span>'
            '<bdi dir="ltr" class="portrait-name">' + name + '</bdi></figcaption></figure>')


def render(text, assigned, edition_id=None, sheet=False):
    if MARKER in text: return text
    doc = Document(text)
    edits = []
    if edition_id:
        header = next(n for n in doc.nodes if n.has('lesson-header'))
        prefix = '../../../' if sheet else '../../'
        edits.append((header.closing_start, header.closing_start, figure(assigned[edition_id], prefix, 'lesson')))
    else:
        prefix = './'
        for node in doc.nodes:
            if not (node.has('feature-card') or node.has('edition-card')): continue
            links = [node] if node.tag == 'a' else [n for n in doc.nodes if node.opening_end <= n.start < node.closing_start and n.tag == 'a']
            match = next((re.search(r'(?:^|/)shiur/([a-z0-9-]+)/$', n.attrs.get('href', '')) for n in links if re.search(r'(?:^|/)shiur/([a-z0-9-]+)/$', n.attrs.get('href', ''))), None)
            if not match or match[1] not in assigned: raise ValueError('Reader card is not in the released catalogue')
            if node.has('feature-card'):
                ornament = doc.inside(node, 'cover-ornament')[0]
                edits.append((ornament.start, ornament.end, figure(assigned[match[1]], prefix, 'feature')))
            else:
                number = doc.inside(node, 'edition-number')[0]
                edits.append((number.end, number.end, figure(assigned[match[1]], prefix, 'card')))
    if not edits: return text
    head = next(n for n in doc.nodes if n.tag == 'head')
    edits.append((head.closing_start, head.closing_start, '<link rel="stylesheet" href="' + prefix + 'assets/portraits.css">\n'))
    for start, end, replacement in sorted(edits, reverse=True): text = text[:start] + replacement + text[end:]
    return text


def build(source, output, reader=ROOT/'reader'):
    if source.resolve() == output.resolve() or source.resolve() in output.resolve().parents:
        raise ValueError('Deployment copy must be separate from the reader source')
    if output.exists(): raise ValueError('Deployment directory must be empty')
    profiles = load_profiles(reader/'rabbis.json')
    catalogue = json.loads((source/'data/catalogue.json').read_text(encoding='utf-8'))
    assigned = {}
    for edition in catalogue['editions']:
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', edition['id']): raise ValueError('Unsafe edition ID')
        path = source/'shiur'/edition['id']/'index.html'
        assigned[edition['id']] = profile_for(edition, portion_number(path.read_text(encoding='utf-8')), profiles)
    shutil.copytree(source, output)
    (output/'index.html').write_text(render((source/'index.html').read_text(encoding='utf-8'), assigned), encoding='utf-8')
    for eid in assigned:
        for suffix in ('index.html', 'sources/index.html'):
            path = output/'shiur'/eid/suffix
            path.write_text(render(path.read_text(encoding='utf-8'), assigned, eid, suffix.startswith('sources/')), encoding='utf-8')
    shutil.copyfile(reader/'portraits.css', output/'assets/portraits.css')
    images = output/'assets/portraits'
    images.mkdir()
    for profile in profiles:
        picture = reader/'portraits'/Path(profile['image']).name
        if picture.is_symlink() or not picture.is_file() or picture.stat().st_size > 150_000: raise ValueError('Missing or oversized portrait')
        raw = picture.read_bytes()
        if raw[:4] != b'RIFF' or raw[8:12] != b'WEBP' or sha256(raw).hexdigest() != profile['image_sha256']:
            raise ValueError('Portrait checksum or format differs')
        shutil.copyfile(picture, output/profile['image'])
    if sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) >= 20_000_000: raise ValueError('Reader size limit exceeded')
    print(json.dumps({'reader_editions': len(assigned), 'available_portraits': len(profiles),
                      'assigned': {eid: p['id'] for eid, p in assigned.items()}}, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'site')
    parser.add_argument('--output', type=Path, default=ROOT/'_site')
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == '__main__': main()
