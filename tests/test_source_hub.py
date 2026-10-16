import copy
from hashlib import sha256
import importlib.util
import io
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('source_hub',ROOT/'tools/source_hub.py')
hub=importlib.util.module_from_spec(spec);spec.loader.exec_module(hub)


class FakeTransport:
    def __init__(self,values):self.values=values;self.calls=[]
    def json(self,url,optional=False,index=False):
        self.calls.append(url)
        value=self.values.get(url)
        if isinstance(value,Exception):raise value
        if value is None and not optional:raise hub.SourceError('Fixture not found: '+url)
        return copy.deepcopy(value)


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.base='https://shekhina.org/'
        self.release='v1-'+'a'*24
        self.db=self.base+'releases/'+self.release+'/'
        self.manifest={'schema':1,'release':self.release,'data_base':'releases/'+self.release+'/','total':3,'page_size':64,'synonyms':{'shabbos':'shabbat'},'stopwords':['the']}
        self.record={'id':'my-1','n':0,'title':'Fixture question','question_html':'<p>Question</p><script>unsafe()</script>','answers':[{'html':'<p>First answer</p>','author':'Author A','author_url':'https://example.org/a'},{'html':'<p>Second answer</p>','author':'Author B'}],'language':'en','url':'https://judaism.stackexchange.com/questions/1','license':'CC BY-SA 4.0'}
        path='content/'+hub.shard('my-1',2)+'/'+sha256(b'my-1').hexdigest()+'.json'
        self.values={self.base+'catalog/manifest.json':self.manifest,self.db+'catalog/pages/00000.json':[{'n':0,'id':'my-1'},{'n':1,'id':'my-2'},{'n':2,'id':'my-3'}],self.db+'catalog/locator/'+hub.shard('my-1',2)+'.json':{'my-1':{'n':0,'file':path}},self.db+path:self.record}
        for token,postings in [('shabbat',[0,3,1,2]),('care',[0,2,2,4]),('מוקצה',[1,7])]:self.values[self.db+'search/'+hub.shard(token)+'.json']={token:postings}
        self.transport=FakeTransport(self.values)
        self.client=hub.Sanhedrin({'base_urls':[self.base],'manifest_path':'catalog/manifest.json'},self.transport)

    def test_fulltext_intersection_and_synonym(self):
        r=self.client.search('the shabbos care')
        self.assertEqual(r['total'],1);self.assertEqual(r['items'][0]['id'],'my-1')
        self.assertTrue(all(x.startswith(self.base) for x in self.transport.calls))

    def test_hebrew_niqqud_search(self):
        r=self.client.search('מוּקְצֶה')
        self.assertEqual(r['items'][0]['id'],'my-2')

    def test_unknown_term_and_empty_query(self):
        self.assertEqual(self.client.search('imaginary')['total'],0)
        self.assertEqual(self.client.search('')['total'],3)

    def test_pin_one_release_per_query(self):
        self.client.init();self.values[self.base+'catalog/manifest.json']['data_base']='releases/v1-'+'b'*24+'/'
        self.client.search('care')
        self.assertEqual(self.transport.calls.count(self.base+'catalog/manifest.json'),1)
        self.assertTrue(all('/'+'b'*24+'/' not in u for u in self.transport.calls))

    def test_missing_release_data_is_not_an_empty_answer(self):
        del self.values[self.db+'catalog/pages/00000.json']
        with self.assertRaises(hub.SourceError):self.client.search('care')
        self.values[self.base+'catalog/manifest.json']['release']='v1-'+'b'*24
        with self.assertRaisesRegex(hub.SourceError,'release changed'):self.client.search('unknown')

    def test_capture_preserves_all_answers_and_attribution(self):
        capture=self.client.capture('my-1')
        self.assertIn('First answer',capture['text']);self.assertIn('Second answer',capture['text'])
        self.assertNotIn('unsafe',capture['text'])
        self.assertEqual([a['author'] for a in capture['answers_attribution']],['Author A','Author B'])
        self.assertEqual(capture['sha256'],sha256(capture['text'].encode()).hexdigest())
        self.assertEqual(capture['origin']['release'],self.release)
        self.assertEqual(capture['review_status'],'research_capture_only')

    def test_tampered_locator_and_public_id_rejected(self):
        locations=self.values[self.db+'catalog/locator/'+hub.shard('my-1',2)+'.json']
        locations['my-1']['file']='../private.sqlite'
        with self.assertRaisesRegex(hub.SourceError,'locator'):self.client.detail('my-1')

    def test_manifest_and_data_path_validation(self):
        self.values[self.base+'catalog/manifest.json']['data_base']='https://evil.example/'
        with self.assertRaises(hub.SourceError):self.client.init()
        with self.assertRaises(hub.SourceError):self.client.data('../state.sqlite')

    def test_primary_unavailable_uses_read_only_mirror(self):
        second='https://moriahise.github.io/Sanhedrin/'
        self.values[self.base+'catalog/manifest.json']=hub.SourceError('Offline')
        self.values[second+'catalog/manifest.json']=self.manifest
        c=hub.Sanhedrin({'base_urls':[self.base,second],'manifest_path':'catalog/manifest.json'},self.transport)
        c.init();self.assertEqual(c.base,second)

    def test_catalogue_keeps_exact_export_urls_and_prefers_merged(self):
        prefix='https://storage.googleapis.com/sefaria-export/json/Tanakh/Torah/Genesis/'
        data={'generated_at':'fixture','books':[{'title':'Genesis','language':'Hebrew','json_url':prefix+'Hebrew/Named.json','versionTitle':'Named','categories':['Tanakh']},{'title':'Genesis','language':'Hebrew','json_url':prefix+'Hebrew/merged.json','versionTitle':'merged','categories':['Tanakh']},{'title':'Genesis','language':'English','json_url':prefix+'English/merged.json','versionTitle':'merged','categories':['Tanakh']}]}
        c=hub.compact_catalogue(data,'fixture')
        self.assertEqual(len(c['works']),1)
        self.assertEqual(c['works'][0]['languages']['Hebrew']['url'],prefix+'Hebrew/merged.json')
        self.assertEqual(set(c['works'][0]['languages']),{'Hebrew','English'})
        data['books'][0]['json_url']='https://evil.example/collect'
        with self.assertRaises(hub.SourceError):hub.compact_catalogue(data,'fixture')

    def test_exact_reference_uses_resolved_ref_version_and_license(self):
        cfg={'api_prefix':'https://www.sefaria.org/api/texts/'}
        url=cfg['api_prefix']+'Genesis%206%3A9?context=0&commentary=0&pad=0'
        t=FakeTransport({url:{'ref':'Genesis 6:9','heRef':'בראשית ו׳:ט׳','he':'<b>נח</b>','heVersionTitle':'Fixture version','heLicense':'Public Domain'}})
        c=hub.Sefaria(cfg,t).capture_reference('Genesis 6:9')
        self.assertEqual(c['text'],'נח');self.assertEqual(c['version'],'Fixture version')
        self.assertEqual(c['license'],'Public Domain');self.assertEqual(c['reference_en'],'Genesis 6:9')

    def test_unknown_license_remains_unrecorded(self):
        self.record.pop('license')
        self.assertEqual(self.client.capture('my-1')['license'],'unrecorded')

    def test_disabled_connection(self):
        self.client.config['enabled']=False
        with self.assertRaisesRegex(hub.SourceError,'disabled'):self.client.init()

    def test_url_allowlist_and_redirect_boundaries(self):
        for u in ['http://shekhina.org/','https://shekhina.org@evil.example/','https://storage.googleapis.com/other-bucket/a','https://storage.googleapis.com/sefaria-export/json/%2e%2e/private','https://raw.githubusercontent.com/other/repo/main/key','file:///etc/passwd']:
            with self.subTest(url=u):
                with self.assertRaises(hub.SourceError):hub.validate_url(u)
        self.assertIn('Genesis',hub.validate_url('https://storage.googleapis.com/sefaria-export/json/Tanakh/Torah/Genesis/Hebrew/merged.json'))

    def test_get_only_bounded_transport_and_cache(self):
        class Response(io.BytesIO):
            headers={}
        class Opener:
            def __init__(self):self.methods=[]
            def open(self,request,timeout):self.methods.append(request.get_method());return Response(b'{"ok":true}')
        t=hub.Transport({'max_requests':1,'max_text_bytes':100,'max_index_bytes':100,'max_response_seconds':1})
        opener=Opener();t.opener=opener
        self.assertTrue(t.json('https://shekhina.org/fixture.json')['ok'])
        self.assertTrue(t.json('https://shekhina.org/fixture.json')['ok'])
        self.assertEqual(opener.methods,['GET'])
        with self.assertRaisesRegex(hub.SourceError,'budget'):t.json('https://shekhina.org/other.json')

    def test_large_response_rejected(self):
        class Response(io.BytesIO):headers={}
        class Opener:
            def open(self,*args,**kwargs):return Response(b'123456789')
        t=hub.Transport({'max_requests':2,'max_text_bytes':4,'max_index_bytes':4,'max_response_seconds':1});t.opener=Opener()
        with self.assertRaisesRegex(hub.SourceError,'size limit'):t.json('https://shekhina.org/fixture.json')


if __name__=='__main__':unittest.main()
