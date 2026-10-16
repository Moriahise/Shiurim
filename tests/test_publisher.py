import copy
from datetime import date
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('shiurim', Path(__file__).resolve().parents[1]/'tools/shiurim.py')
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class PublisherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for folder in ['content','config','assets']:
            shutil.copytree(app.ROOT/folder,self.root/folder)
        self.path = next((self.root/'content/editions').glob('*.json'))
        self.edition = app.read(self.path)

    def tearDown(self):
        self.temp.cleanup()

    def save(self, edition=None):
        app.write(self.path,edition or self.edition)

    def reviewed_queue(self):
        self.edition['status']='scheduled'
        self.edition['publish_at']='2026-10-15T18:17:00+03:00'
        self.save()
        sources={s['id']:s for s in (app.read(p) for p in (self.root/'content/sources').glob('*.json'))}
        self.edition['review']={'scholarly_review':'approved','reviewer':'Test fixture only','reviewed_revision':1,'content_sha256':app.digest(self.edition,sources)}
        self.save()
        c=app.read(self.root/'config/site.json');c['automatic_publication']=True
        app.write(self.root/'config/site.json',c)

    def test_calendar_verified_noach(self):
        week=app.calendar_week('2026-10-17')
        self.assertEqual(week['israel'],{'en':'Noach','he':'נח'})
        self.assertIn('תשפ״ז',week['hebrew_date'])

    def test_festival_reading_and_diaspora_divergence(self):
        # 8th day of Pesach 5782: Israel reads Acharei Mos, Diaspora reads festival.
        week=app.calendar_week('2022-04-23')
        self.assertTrue(week['different_readings'])
        self.assertTrue(week['has_weekly_parashah'])
        festival=app.calendar_week('2026-09-26')
        self.assertFalse(festival['has_weekly_parashah'])
        self.assertTrue(festival['festival'])

    def test_double_parashah_and_year_boundary(self):
        weeks=app.upcoming_calendar(app.now_value('2026-12-30T15:00:00+02:00'),52)
        self.assertEqual(weeks[0]['target_shabbat'],'2027-01-02')
        self.assertEqual(len({w['target_shabbat'] for w in weeks}),52)
        self.assertTrue(any(', ' in w['israel']['en'] for w in weeks))

    def test_daylight_saving_uses_israel_zone(self):
        self.assertEqual(app.now_value('2026-10-15T16:00:00+00:00').hour,19)
        self.assertEqual(app.now_value('2026-11-05T16:00:00+00:00').hour,18)
        with self.assertRaises(app.ValidationError):app.now_value('2026-10-15T18:00:00')

    def test_source_tamper_rejected(self):
        p=next((self.root/'content/sources').glob('*.json'))
        source=app.read(p);source['hebrew']+=' changed';app.write(p,source)
        with self.assertRaisesRegex(app.ValidationError,'checksum'):app.load_all(self.root)

    def test_alignment_and_missing_evidence_rejected(self):
        self.edition['sections'][0]['he'].pop();self.save()
        with self.assertRaisesRegex(app.ValidationError,'alignment'):app.load_all(self.root)
        self.edition=app.read(next((app.ROOT/'content/editions').glob('*.json')))
        self.edition['sections'][0]['sources']=['invented'];self.save()
        with self.assertRaisesRegex(app.ValidationError,'evidence'):app.load_all(self.root)

    def test_bad_calendar_and_duplicate_week_rejected(self):
        self.edition['parashah']['en']='Invented';self.save()
        with self.assertRaisesRegex(app.ValidationError,'Calendar'):app.load_all(self.root)
        self.edition=app.read(next((app.ROOT/'content/editions').glob('*.json')))
        self.save();other=copy.deepcopy(self.edition);other['id']='second-edition'
        app.write(self.path.with_name('second-edition.json'),other)
        with self.assertRaisesRegex(app.ValidationError,'one edition'):app.load_all(self.root)

    def test_no_false_approval(self):
        self.edition['status']='scheduled';self.save()
        with self.assertRaisesRegex(app.ValidationError,'approval'):app.load_all(self.root)

    def test_approval_invalidated_after_edit(self):
        self.reviewed_queue()
        self.edition['sections'][0]['en'][0]+=' Additional claim.';self.save()
        with self.assertRaisesRegex(app.ValidationError,'matches content'):app.load_all(self.root)

    def test_due_release_idempotent(self):
        self.reviewed_queue()
        now=app.now_value('2026-10-15T18:20:00+03:00')
        first=app.publish_due(now,self.root)
        ledger=(self.root/'content/publications.json').read_bytes()
        second=app.publish_due(now,self.root)
        self.assertEqual(first['published'],[self.edition['id']])
        self.assertEqual(second['published'],[])
        self.assertEqual(ledger,(self.root/'content/publications.json').read_bytes())

    def test_disabled_queue_early_and_late_runs_do_not_release(self):
        self.reviewed_queue()
        early=app.publish_due(app.now_value('2026-10-15T17:00:00+03:00'),self.root)
        self.assertEqual(early['published'],[])
        late=app.publish_due(app.now_value('2026-10-16T08:00:00+03:00'),self.root)
        self.assertEqual(late['published'],[])
        c=app.read(self.root/'config/site.json');c['automatic_publication']=False;app.write(self.root/'config/site.json',c)
        self.assertEqual(app.publish_due(app.now_value('2026-10-15T19:00:00+03:00'),self.root)['published'],[])

    def test_draft_excluded_and_html_escaped(self):
        self.edition['status']='draft';self.save()
        app.build(app.now_value('2026-10-16T17:00:00+03:00'),self.root)
        self.assertFalse((self.root/'dist/shiur').exists())
        self.assertEqual(app.read(self.root/'dist/data/catalogue.json')['editions'],[])
        self.edition['status']='pilot';self.edition['title']['en']='<script>alert(1)</script>';self.save()
        app.build(app.now_value('2026-10-16T17:00:00+03:00'),self.root)
        html=(self.root/f'dist/shiur/{self.edition["id"]}/index.html').read_text()
        self.assertNotIn('<script>alert',html)
        self.assertIn('&lt;script&gt;',html)

    def test_failed_build_keeps_previous_site(self):
        app.build(app.now_value('2026-10-16T17:00:00+03:00'),self.root)
        old=(self.root/'dist/index.html').read_bytes()
        self.edition['source_ids'].append('not-real');self.save()
        with self.assertRaises(app.ValidationError):app.build(app.now_value('2026-10-16T17:00:00+03:00'),self.root)
        self.assertEqual(old,(self.root/'dist/index.html').read_bytes())

    def test_export_is_self_contained_and_excludes_private_files(self):
        app.build(app.now_value('2026-10-16T17:00:00+03:00'),self.root)
        app.validate_export(self.root/'dist')
        self.assertFalse((self.root/'dist/content').exists())
        self.assertFalse((self.root/'dist/reports').exists())
        provenance=app.read(self.root/'dist/data/source-provenance.json')
        self.assertEqual(len(provenance['sources']),6)

    def test_lock_rejects_parallel_writers(self):
        with app.publisher_lock(self.root):
            with self.assertRaisesRegex(app.ValidationError,'Another publisher'):app.publish_due(app.now_value(),self.root)

    def test_isolation_repository_guard(self):
        c=app.read(self.root/'config/site.json');c['repository']='Moriahise/Sanhedrin';app.write(self.root/'config/site.json',c)
        with self.assertRaisesRegex(app.ValidationError,'restricted'):app.load_all(self.root)

    def test_selected_sanhedrin_source_integrates_without_overwriting_primary_sources(self):
        text='A selected English source for editorial use.'
        source={'id':'sanhedrin-fixture','provider':'sanhedrin','language':'en','text':text,'sha256':app.sha256(text.encode()).hexdigest(),'reference_en':'Fixture reference','reference_he':'מקור לבדיקה','url':'https://shekhina.org/qa.html?id=fixture','version':'v1-fixture','license':'unrecorded','retrieved_at':'2026-10-16T00:00:00Z'}
        app.write(self.root/'content/sources/sanhedrin-fixture.json',source)
        self.edition['source_ids'].append(source['id'])
        self.edition['sections'][0]['sources'].append(source['id']);self.save()
        app.build(app.now_value('2026-10-16T17:00:00+03:00'),self.root)
        page=(self.root/f'dist/shiur/{self.edition["id"]}/sources/index.html').read_text()
        self.assertIn(text,page)
        self.assertIn('blockquote lang="en" dir="ltr"',page)
        self.assertEqual(len(app.read(self.root/'dist/data/source-provenance.json')['sources']),7)


if __name__=='__main__':unittest.main()
