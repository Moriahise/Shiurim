"""Protect stable portrait identity, lesson prose, and the reader-only export."""
import json
from pathlib import Path
import tempfile
import unittest
from reader import portraits as p


class PortraitTests(unittest.TestCase):
    def setUp(self):
        self.profiles = p.load_profiles(p.ROOT/'reader/rabbis.json')
        self.editions = json.loads((p.ROOT/'site/data/catalogue.json').read_text())['editions']
        self.assigned = {e['id']: p.profile_for(e, p.portion_number((p.ROOT/'site/shiur'/e['id']/'index.html').read_text()), self.profiles) for e in self.editions}

    def test_source_collection_has_71_files_and_70_different_portraits(self):
        manifest = json.loads((p.ROOT/'reader/rabbis.json').read_text())
        self.assertEqual(manifest['source_file_count'], 71)
        self.assertEqual(len(self.profiles), 70)
        self.assertEqual(len(manifest['duplicate_files']), 1)

    def test_bereshit_and_noach_have_different_fixed_portraits(self):
        first = self.assigned['5787-bereshit-responsibility']
        second = self.assigned['5787-noach-responsibility']
        self.assertEqual(first['name'], 'Aharon Mualem Chacham Dayan')
        self.assertEqual(second['name'], 'Aharon Sutton Chacham Dayan')
        self.assertNotEqual(first['image'], second['image'])

    def test_all_55_current_cycle_editions_receive_different_portraits(self):
        edition = {'id': '5787-fixture', 'parashah': {'en': 'Fixture'}}
        numbers = [n for n in range(1,55) if n not in (43,52)]
        ids = [p.profile_for(edition, n, self.profiles)['id'] for n in numbers]
        for name in ('Pesach', 'Rosh Hashana', 'Succos'):
            edition['parashah']['en'] = name
            ids.append(p.profile_for(edition, None, self.profiles)['id'])
        self.assertEqual(len(ids), 55)
        self.assertEqual(len(set(ids)), 55)

    def test_new_cycles_rotate_without_changing_existing_edition_identity(self):
        old = {'id': '5787-fixture', 'parashah': {'en': 'Bereshit'}}
        new = old | {'id': '5788-fixture'}
        self.assertNotEqual(p.profile_for(old, 1, self.profiles), p.profile_for(new, 1, self.profiles))
        self.assertEqual(p.profile_for(old, 1, self.profiles), self.profiles[0])
        for name in ('Pesach', 'Rosh Hashana', 'Succos', 'Yom Kippur'):
            self.assertIsNotNone(p.profile_for(new | {'parashah': {'en': name}}, None, self.profiles))

    def test_lesson_body_and_header_prose_are_preserved_byte_for_byte(self):
        for edition in self.editions:
            for sheet in (False, True):
                original = (p.ROOT/'site/shiur'/edition['id']/('sources/index.html' if sheet else 'index.html')).read_text()
                rendered = p.render(original, self.assigned, edition['id'], sheet)
                doc = p.Document(rendered)
                figure = next(n for n in doc.nodes if p.MARKER in n.attrs)
                without = rendered[:figure.start] + rendered[figure.end:]
                css = '<link rel="stylesheet" href="' + ('../../../' if sheet else '../../') + 'assets/portraits.css">\n'
                self.assertEqual(without.replace(css, ''), original)
                self.assertIn(self.assigned[edition['id']]['name'], rendered)

    def test_homepage_cards_and_lesson_share_the_same_identity(self):
        original = (p.ROOT/'site/index.html').read_text()
        feature = next(n for n in p.Document(original).nodes if n.has('feature-card'))
        eid = feature.attrs['href'].rstrip('/').split('/')[-1]
        text = p.render(original, self.assigned)
        doc = p.Document(text)
        portraits = [n for n in doc.nodes if p.MARKER in n.attrs]
        self.assertEqual(len(portraits), len(self.editions) + 1)
        expected = self.assigned[eid]['id']
        self.assertEqual(next(n for n in portraits if n.has('rabbi-portrait--feature')).attrs[p.MARKER], expected)
        self.assertEqual(p.render(text, self.assigned), text)

    def test_deployment_is_local_self_contained_and_does_not_modify_the_source(self):
        before = {str(f.relative_to(p.ROOT/'site')): f.read_bytes() for f in (p.ROOT/'site').rglob('*') if f.is_file()}
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)/'deploy'
            p.build(p.ROOT/'site', target)
            self.assertEqual(len(list((target/'assets/portraits').glob('*.webp'))), 70)
            for page in target.rglob('*.html'):
                text = page.read_text()
                for node in p.Document(text).nodes:
                    if node.tag != 'img' or 'portraits/' not in node.attrs.get('src', ''): continue
                    self.assertTrue((page.parent/node.attrs['src']).is_file())
                    self.assertNotIn('https:', node.attrs['src'])
                self.assertNotIn('source_blob_sha', text)
            self.assertFalse((target/'reader').exists())
            self.assertFalse((target/'redaktion').exists())
        self.assertEqual(before, {str(f.relative_to(p.ROOT/'site')): f.read_bytes() for f in (p.ROOT/'site').rglob('*') if f.is_file()})

    def test_unknown_festival_and_unsafe_assets_are_rejected(self):
        with self.assertRaises(ValueError):
            p.profile_for({'id':'5787-fixture','parashah':{'en':'Unknown'}}, None, self.profiles)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'profiles.json'
            value = json.loads((p.ROOT/'reader/rabbis.json').read_text())
            value['profiles'][0]['image'] = '../private.json'
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError): p.load_profiles(path)


if __name__ == '__main__': unittest.main()
