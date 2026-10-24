"""Protect lesson text, reading-cycle scope, bilingual sources, and insertion position."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from reader import ben_ish_chai as bic
from reader.portraits import Document


class BenIshChaiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = bic.load()
        cls.catalogue = json.loads((bic.ROOT/'site/data/catalogue.json').read_text())['editions']

    def test_every_individual_portion_has_both_languages_and_a_first_year_source(self):
        self.assertEqual(len(self.data['editions']), 54)
        for entry in self.data['editions']:
            self.assertEqual(entry['source']['year'], 1)
            self.assertTrue(entry['source']['he'].strip())
            self.assertTrue(entry['source']['en'].strip())
            self.assertGreater(len(entry['essence']['en'].split()), 30)
            self.assertGreater(len(entry['essence']['he'].split()), 20)
            self.assertEqual(bic.resolve(entry['parashah'], self.data), [entry])

    def test_variant_spellings_and_all_seven_double_portions_resolve_exactly(self):
        for spelling, expected in [('כי תבא', [50]), ('בחקתי', [33]), ('פינחס', [41]),
                                   ('בהעלתך', [36]), ('שלח לך', [37]), ('מְצֹרָע', [28]),
                                   ('ויקהל, פקודי', [22,23]), ('תזריע־מצרע', [27,28]),
                                   ('אחרי מות, קדושים', [29,30]), ('בהר–בחוקתי', [32,33]),
                                   ('חקת, בלק', [39,40]), ('מטות, מסעי', [42,43]),
                                   ('נצבים, וילך', [51,52])]:
            self.assertEqual([e['number'] for e in bic.resolve({'he': spelling}, self.data)], expected)
        self.assertEqual(bic.resolve({'he': 'פסח'}, self.data), [])
        with self.assertRaises(ValueError): bic.resolve({'he': 'פרשה לא מוכרת'}, self.data)

    def test_combined_source_chapters_are_attributed_without_inventing_chapters(self):
        entries = self.data['editions']
        for first, second, source in [(27,28,'תזריע–מצורע'), (29,30,'אחרי מות–קדושים'),
                                      (32,33,'בהר–בחוקותי')]:
            for n in (first,second): self.assertEqual(entries[n-1]['source']['chapter']['he'], source)
        self.assertEqual(entries[11]['source']['segment_id'], 'BIH-0001031')
        self.assertEqual(entries[16]['source']['segment_id'], 'BIH-0001137')

    def test_only_the_component_and_its_stylesheet_are_added_to_published_lessons(self):
        for edition in self.catalogue:
            original = (bic.ROOT/'site/shiur'/edition['id']/'index.html').read_text()
            entries = bic.resolve(edition['parashah'], self.data)
            updated = bic.render(original, entries)
            doc = Document(updated)
            section = next(n for n in doc.nodes if bic.MARKER in n.attrs)
            question = next(n for n in doc.nodes if n.has('guiding-question'))
            self.assertEqual(section.end, question.start)
            self.assertIn('<strong>First Year</strong>', updated)
            self.assertIn('<strong>שנה ראשונה</strong>', updated)
            link = next(n for n in doc.nodes if n.attrs.get('href') == '../../assets/ben-ish-chai.css')
            stripped = updated
            for a,b in sorted([(section.start,section.end), (link.start,link.end+1)], reverse=True):
                stripped = stripped[:a]+stripped[b:]
            self.assertEqual(stripped, original, edition['id'])
            self.assertEqual(bic.render(updated, entries), updated)

    def test_new_source_revision_replaces_the_existing_component_without_duplication(self):
        e = self.catalogue[0]
        original = (bic.ROOT/'site/shiur'/e['id']/'index.html').read_text()
        entries = copy.deepcopy(bic.resolve(e['parashah'], self.data))
        first = bic.render(original, entries)
        entries[0]['essence']['en'] = 'A revised editorial essence.'
        updated = bic.render(first, entries)
        self.assertEqual(sum(bic.MARKER in n.attrs for n in Document(updated).nodes), 1)
        self.assertIn('A revised editorial essence.', updated)
        self.assertNotIn(entries[0]['source']['segment_id'], updated)

    def test_a_future_lesson_receives_its_essence_but_other_cycles_and_source_sheets_do_not(self):
        template = (bic.ROOT/'site/shiur'/self.catalogue[0]['id']/'index.html').read_text()
        with tempfile.TemporaryDirectory() as folder:
            site = Path(folder); (site/'data').mkdir(); (site/'assets').mkdir()
            fixtures = []
            for eid, target, name in [('5787-future','2027-09-25','נצבים, וילך'),
                                      ('5786-old','2026-09-05','נצבים'),
                                      ('5788-new','2027-10-30','בראשית'),
                                      ('5788-closing','2027-10-23','וזאת הברכה')]:
                fixtures.append({'id':eid,'target_shabbat':target,'parashah':{'he':name}})
                page = site/'shiur'/eid/'index.html';page.parent.mkdir(parents=True)
                page.write_text(template)
                sheet = page.parent/'sources/index.html';sheet.parent.mkdir();sheet.write_text(template)
            (site/'data/catalogue.json').write_text(json.dumps({'editions': fixtures}))
            before = {p:p.read_bytes() for p in site.rglob('*') if p.is_file()}
            result = bic.apply(site)
            self.assertEqual(result['updated_lessons'], ['5787-future','5788-closing'])
            expected = {site/'shiur'/eid/'index.html' for eid in result['updated_lessons']}
            for p, raw in before.items():
                if p not in expected: self.assertEqual(p.read_bytes(), raw, str(p))
            future = (site/'shiur/5787-future/index.html').read_text()
            self.assertEqual(sum(n.has('bic-study') for n in Document(future).nodes), 2)
            self.assertEqual(bic.apply(site)['updated_lessons'], [])

    def test_tampering_with_a_source_or_dropping_a_portion_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'data.json'
            for change in ('source','missing'):
                data = copy.deepcopy(self.data)
                if change == 'source':data['editions'][0]['source']['he'] += ' changed'
                else:data['editions'].pop()
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):bic.load(path)


if __name__ == '__main__': unittest.main()
