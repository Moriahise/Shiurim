"""Verify a whole historical cycle without changing the current published studies."""
from html import escape
import json
from pathlib import Path
import tempfile
import unittest
from urllib.parse import urlparse,unquote
from reader import archive as a,portraits as p


class ArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.site=Path(cls.tmp.name)/'site'
        cls.data_path=a.ROOT/'reader/archive/5786/lessons.json';cls.data=a.load(cls.data_path)
        p.build(p.ROOT/'site',cls.site)
        cls.before={str(f.relative_to(cls.site)):f.read_bytes() for f in cls.site.rglob('*') if f.is_file()}
        cls.result=a.apply(cls.site,cls.data_path)

    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_complete_cycle_has_54_studies_and_keeps_double_portions_separate(self):
        es=self.data['editions']
        self.assertEqual([e['number'] for e in es],list(range(1,55)))
        self.assertEqual(len({e['target_shabbat'] for e in es}),48)
        self.assertEqual(es[0]['target_shabbat'],'2025-10-18')
        self.assertEqual(es[-1]['target_shabbat'],'2026-10-03')
        self.assertEqual(es[41]['target_shabbat'],es[42]['target_shabbat'])
        self.assertEqual(es[50]['target_shabbat'],es[51]['target_shabbat'])
        self.assertEqual({e['book'] for e in es},{b[0] for b in a.BOOKS})

    def test_current_feature_and_existing_lessons_remain_unchanged(self):
        allowed={'index.html','data/catalogue.json','sitemap.xml'}
        for name,raw in self.before.items():
            if name not in allowed:self.assertEqual((self.site/name).read_bytes(),raw,name)
        before=self.before['index.html'].decode();after=(self.site/'index.html').read_text()
        def feature(text):
            n=next(n for n in p.Document(text).nodes if n.has('feature-card'))
            return text[n.start:n.end]
        self.assertEqual(feature(before),feature(after))

    def test_all_archive_body_paragraphs_and_questions_are_preserved(self):
        total=0
        for e in self.data['editions']:
            text=(self.site/'shiur'/e['id']/'index.html').read_text()
            for section in e['sections']:
                for pair in section['paragraphs']:
                    total+=1
                    for value in pair.values():self.assertIn(escape(value),text)
            for question in e['questions']:
                for value in question.values():self.assertIn(escape(value),text)
        self.assertEqual(total,540)

    def test_all_original_passages_are_present_on_both_reader_pages(self):
        total=0
        for e in self.data['editions']:
            for source in e['sources']:
                total+=1
                for suffix in ('index.html','sources/index.html'):
                    text=(self.site/'shiur'/e['id']/suffix).read_text()
                    self.assertIn(escape(source['text']).replace('\n','<br>'),text)
                    self.assertIn(escape(source['credit']),text)
        self.assertEqual(total,163)

    def test_archive_catalogue_is_complete_and_dossiers_are_absent(self):
        catalogue=json.loads((self.site/'data/catalogue.json').read_text())
        self.assertEqual(len(catalogue['editions']),len(json.loads(self.before['data/catalogue.json'])['editions'])+54)
        self.assertEqual(len({e['id'] for e in catalogue['editions']}),len(catalogue['editions']))
        for page in self.site.rglob('*.html'):
            text=page.read_text()
            self.assertNotIn('## Prüfungen',text)
            self.assertNotIn('### evidence',text)
            self.assertNotIn('IMPORT_RECEIPT',text)
        self.assertFalse(list(self.site.rglob('*.md')))
        self.assertFalse((self.site/'reader').exists())

    def test_archive_has_54_distinct_portraits_and_matching_source_sheets(self):
        ids=[]
        for e in self.data['editions']:
            selected=[]
            for suffix in ('index.html','sources/index.html'):
                text=(self.site/'shiur'/e['id']/suffix).read_text()
                selected.append(next(n.attrs[p.MARKER] for n in p.Document(text).nodes if p.MARKER in n.attrs))
            self.assertEqual(selected[0],selected[1]);ids.append(selected[0])
        self.assertEqual(len(set(ids)),54)

    def test_year_selection_and_no_script_archive_are_available(self):
        home=(self.site/'index.html').read_text();doc=p.Document(home)
        select=next(n for n in doc.nodes if n.attrs.get('id')=='cycle-year')
        current=max(a.cycle_of(e) for e in json.loads(self.before['data/catalogue.json'])['editions'])
        self.assertEqual(select.attrs['data-default-year'],str(current))
        cards=[n for n in doc.nodes if n.has('edition-card')]
        self.assertEqual(sum(n.attrs.get('data-cycle-year')=='5786' and 'hidden' in n.attrs for n in cards),54)
        self.assertIn('./archive/5786/',home)
        archive=(self.site/'archive/5786/index.html').read_text()
        nodes=p.Document(archive).nodes
        self.assertEqual(sum(n.has('edition-card') for n in nodes),54)
        self.assertEqual(sum(n.has('archive-book') for n in nodes),5)
        self.assertFalse(any('hidden' in n.attrs for n in nodes if n.has('edition-card')))

    def test_a_later_current_cycle_becomes_the_default_without_hiding_the_archive(self):
        original=self.before['index.html'].decode()
        doc=p.Document(original)
        card=next(n for n in doc.nodes if n.has('edition-card'))
        markup=original[card.start:card.end]
        old_id=next(e['id'] for e in json.loads(self.before['data/catalogue.json'])['editions'] if e['id'] in markup)
        future_id='5788-future-fixture'
        listing=next(n for n in doc.nodes if n.attrs.get('id')=='edition-list')
        original=original[:listing.closing_start]+markup.replace(old_id,future_id)+original[listing.closing_start:]
        catalogue=json.loads(self.before['data/catalogue.json'])['editions']
        future=dict(catalogue[0]);future['id']=future_id;catalogue.append(future)
        catalogue += [{k:e[k] for k in ('id','title','parashah','target_shabbat')}|{'category':'tanach'} for e in self.data['editions']]
        profiles=p.load_profiles(p.ROOT/'reader/rabbis.json')
        assigned={e['id']:p.profile_for(e,e['number'],profiles) for e in self.data['editions']}
        rendered=a.enrich_home(original,catalogue,self.data['editions'],assigned,5786)
        select=next(n for n in p.Document(rendered).nodes if n.attrs.get('id')=='cycle-year')
        self.assertEqual(select.attrs['data-default-year'],'5788')
        self.assertIn('value="5786"',rendered)

    def test_all_reader_assets_and_internal_archive_links_resolve(self):
        pages=[self.site/'archive/5786/index.html']+[self.site/'shiur'/e['id']/s for e in self.data['editions'] for s in ('index.html','sources/index.html')]
        for page in pages:
            for node in p.Document(page.read_text()).nodes:
                for attr in ('href','src'):
                    value=node.attrs.get(attr,'');url=urlparse(value)
                    if not value or url.scheme or url.netloc or not url.path:continue
                    target=(page.parent/unquote(url.path)).resolve()
                    self.assertTrue(target.is_file() or (target/'index.html').is_file(),str(target))

    def test_repeat_import_does_not_duplicate_or_overwrite_content(self):
        before={str(f.relative_to(self.site)):f.read_bytes() for f in self.site.rglob('*') if f.is_file()}
        self.assertTrue(a.apply(self.site,self.data_path)['already_present'])
        self.assertEqual(before,{str(f.relative_to(self.site)):f.read_bytes() for f in self.site.rglob('*') if f.is_file()})


if __name__=='__main__':unittest.main()
