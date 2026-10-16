import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('preflight_test_module',ROOT/'tools/content_review.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


class ContentReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.policy=json.loads((ROOT/'config/preflight.json').read_text())
        self.edition=json.loads(next((ROOT/'content/editions').glob('*.json')).read_text())
        self.sources={s['id']:s for s in (json.loads(p.read_text()) for p in (ROOT/'content/sources').glob('*.json'))}
        self.evidence=r.load_evidence(ROOT,self.edition['id'])
        self.env={'SHIURIM_REVIEW_API_KEY':'test-key-not-a-real-credential','SHIURIM_REVIEW_MODEL':'fixture-model'}
        self.calls=[]

    def tearDown(self):self.temp.cleanup()

    def stage(self,stage,payload):
        rows=[]
        for p in payload['paragraphs']:
            sid=p['source_ids'][0];source=next(s for s in payload['sources'] if s['id']==sid)
            rows.append({'paragraph_id':p['paragraph_id'],'verdict':('not_applicable' if p['suggested_kind'] in ('application','method') else 'supported') if stage=='evidence' else 'equivalent','source_ids':[sid],'evidence_quotes':[{'source_id':sid,'quote':source['text']}],'reason':{'en':'Fixture result only.','he':'תוצאת בדיקה מלאכותית בלבד.'}})
        return {'stage':stage,'paragraphs':rows}

    def wire_stage(self,stage,payload):
        data=self.stage(stage,payload)
        data['paragraphs']=[{k:v for k,v in row.items() if k!='evidence_quotes'}|{'evidence_source_ids':[a['source_id'] for a in row['evidence_quotes']]} for row in data['paragraphs']]
        return data

    def client(self,stage,payload,config,key,model):
        self.calls.append(stage)
        return {'result':self.stage(stage,payload),'response_id':'test-response','model':model,'usage':{'input_tokens':1}}

    def test_matching_normalizes_niqqud_and_preserves_word_boundaries(self):
        self.assertTrue(r.matches_quote('צא מן התבה','צֵ֖א מִן־הַתֵּבָ֑ה'))
        self.assertFalse(r.matches_quote('מותר','אסור'))
        self.assertFalse(r.matches_quote('permitted','unpermitted'))

    def test_pilot_has_complete_mapping_and_all_text_anchors(self):
        result=r.rule_review(self.edition,self.sources,self.evidence,self.policy)
        self.assertEqual(result['paragraphs_total'],22)
        self.assertEqual(result['paragraphs_mapped'],22)
        self.assertEqual(result['anchors_verified'],26)
        self.assertFalse(any(f['severity']=='error' for f in result['findings']))

    def test_quote_change_and_source_checksum_are_blocking(self):
        anchor=self.evidence['paragraphs'][0]['evidence'][0]
        anchor['quote']='מילים שלא נמצאות במקור'
        anchor['source_sha256']='0'*64
        codes={f['code'] for f in r.rule_review(self.edition,self.sources,self.evidence,self.policy)['findings']}
        self.assertIn('QUOTE_NOT_FOUND',codes);self.assertIn('EVIDENCE_CHANGED',codes)

    def test_wrong_source_and_missing_support_are_blocking(self):
        self.evidence['paragraphs'][0]['evidence'][0]['source_id']='invented'
        self.evidence['paragraphs'][2]['evidence']=[]
        codes={f['code'] for f in r.rule_review(self.edition,self.sources,self.evidence,self.policy)['findings']}
        self.assertIn('UNKNOWN_EVIDENCE',codes);self.assertIn('MISSING_EVIDENCE',codes)

    def test_duplicate_missing_orphan_and_stale_register(self):
        self.evidence['paragraphs'].append(copy.deepcopy(self.evidence['paragraphs'][0]))
        self.evidence['paragraphs'].append({'paragraph_id':'missing:1','kind':'method'})
        self.evidence['paragraphs'].pop(2)
        self.edition['sections'][0]['en'][0]+=' New assertion.'
        codes={f['code'] for f in r.rule_review(self.edition,self.sources,self.evidence,self.policy)['findings']}
        self.assertTrue({'DUPLICATE_MAPPING','UNMAPPED_PARAGRAPH','ORPHAN_MAPPING','STALE_REGISTER'}<=codes)

    def test_numeric_drift_and_unmatched_body_quote_are_flagged(self):
        self.edition['sections'][0]['en'][0]+=' There are 17 items. “a deliberately invented quotation”'
        codes={f['code'] for f in r.rule_review(self.edition,self.sources,self.evidence,self.policy)['findings']}
        self.assertIn('NUMBER_DIFFERENCE',codes);self.assertIn('BODY_QUOTE_UNVERIFIED',codes)

    def test_polarity_ruling_and_attribution_are_inspection_notes(self):
        self.edition['sections'][0]['en'][0]='Rashi says it is forbidden and must never be done.'
        self.edition['sections'][0]['he'][0]='זהו נוסח אחר לחלוטין.'
        findings=r.rule_review(self.edition,self.sources,self.evidence,self.policy)['findings']
        codes={f['code'] for f in findings}
        self.assertTrue({'POLARITY_REVIEW','PRACTICAL_RULING_REVIEW','ATTRIBUTION_CHECK'}<=codes)
        self.assertTrue(all(f['severity']=='warning' for f in findings if f['code'] in {'POLARITY_REVIEW','PRACTICAL_RULING_REVIEW','ATTRIBUTION_CHECK'}))

    def test_missing_key_never_runs_model_or_grants_approval(self):
        before=copy.deepcopy(self.edition)
        result=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ={})
        self.assertEqual(result['semantic']['status'],'not_configured')
        self.assertEqual(result['status'],'incomplete');self.assertFalse(result['scholarly_approval_granted'])
        self.assertEqual(self.calls,[]);self.assertEqual(before,self.edition)

    def test_switch_values_never_trigger_an_api_call_or_complete_preflight(self):
        for model in ('true','FALSE','on','yes','1','0','none',' true '):
            with self.subTest(model=model):
                result=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env|{'SHIURIM_REVIEW_MODEL':model})
                self.assertEqual(result['semantic']['status'],'invalid_configuration')
                self.assertEqual(result['semantic']['diagnostic']['code'],'INVALID_MODEL')
                self.assertEqual(result['status'],'incomplete')
                self.assertEqual(self.calls,[])
                self.assertFalse(result['scholarly_approval_granted'])
                with self.assertRaisesRegex(r.ReviewError,'actual model ID'):
                    r.api_review('evidence',{},self.policy['semantic'],'fake-key',model,lambda *args:self.fail('No request allowed'))

    def test_model_access_failure_is_diagnosable_without_leaking_provider_data(self):
        def unavailable(*args):raise r.ReviewError('Review API HTTP 404')
        report=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=unavailable,environ=self.env)
        self.assertEqual(report['semantic']['diagnostic']['code'],'MODEL_UNAVAILABLE')
        from html import escape
        page=r.report_body(report,self.edition,lambda v:escape(v['en'])+' '+escape(v['he']))
        self.assertIn('HTTP 404',page)
        self.assertNotIn(self.env['SHIURIM_REVIEW_API_KEY'],page)
        self.assertEqual(report['status'],'incomplete')

    def test_invalid_configuration_is_explained_in_the_public_report(self):
        report=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env|{'SHIURIM_REVIEW_MODEL':'true'})
        from html import escape
        public=r.public_report(report)
        page=r.report_body(public,self.edition,lambda v:escape(v['en'])+' '+escape(v['he']))
        self.assertIn('SHIURIM_REVIEW_MODEL',page)
        self.assertIn('No AI review request was sent.',page)
        self.assertIn('לא נשלחה',page)
        self.assertNotIn(self.env['SHIURIM_REVIEW_API_KEY'],json.dumps(public))

    def test_two_passes_cached_only_for_identical_inputs(self):
        first=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env)
        second=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env)
        self.assertEqual(first['semantic']['status'],'completed');self.assertEqual(second['semantic']['status'],'completed')
        self.assertEqual(self.calls,['evidence','bilingual'])
        self.evidence['note']['en']+=' Changed mapping metadata.'
        r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env)
        self.assertEqual(len(self.calls),4)

    def test_semantic_invented_ids_missing_rows_and_fake_quotes_rejected(self):
        payload=r.semantic_payload(self.edition,self.sources,self.evidence)
        for mutation in ('id','missing','quote'):
            data=self.stage('evidence',payload)
            if mutation=='id':data['paragraphs'][0]['paragraph_id']='invented:1'
            if mutation=='missing':data['paragraphs'].pop()
            if mutation=='quote':data['paragraphs'][0]['evidence_quotes'][0]['quote']='this is not source text'
            with self.subTest(case=mutation):
                with self.assertRaises(r.ReviewError):r.validate_semantic(data,'evidence',payload)

    def test_source_statement_cannot_be_not_applicable(self):
        payload=r.semantic_payload(self.edition,self.sources,self.evidence)
        data=self.stage('evidence',payload);data['paragraphs'][0]['verdict']='not_applicable'
        with self.assertRaises(r.ReviewError):r.validate_semantic(data,'evidence',payload)

    def test_translation_drift_is_blocking(self):
        def client(stage,*args):
            result=self.client(stage,*args)
            if stage=='bilingual':result['result']['paragraphs'][0]['verdict']='drift'
            return result
        report=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=client,environ=self.env)
        self.assertEqual(report['status'],'blocking_issues')
        self.assertIn('SEMANTIC_BILINGUAL',{f['code'] for f in report['findings']})

    def test_failed_second_stage_is_incomplete_and_first_stage_reused(self):
        def client(stage,*args):
            if stage=='bilingual':raise r.ReviewError('Timeout')
            return self.client(stage,*args)
        first=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=client,environ=self.env)
        self.assertEqual(first['semantic']['status'],'failed');self.assertEqual(first['status'],'incomplete')
        self.assertEqual(set(first['semantic']['stages']),{'evidence'})
        r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env)
        self.assertEqual(self.calls,['evidence','bilingual'])

    def test_api_request_is_structured_bounded_and_does_not_store(self):
        payload=r.semantic_payload(self.edition,self.sources,self.evidence)
        captured=[]
        def requester(request,timeout):
            captured.append((request,timeout))
            return {'status':'completed','id':'fixture','model':'fixture-model','output':[{'content':[{'type':'output_text','text':json.dumps(self.wire_stage('evidence',payload))}]}]}
        value=r.api_review('evidence',payload,self.policy['semantic'],'fake-key','fixture-model',requester)
        request,timeout=captured[0];body=json.loads(request.data)
        self.assertEqual(request.full_url,'https://api.openai.com/v1/responses')
        self.assertFalse(body['store']);self.assertTrue(body['text']['format']['strict'])
        self.assertNotIn('fake-key',request.data.decode());self.assertEqual(timeout,180)
        self.assertEqual(body['max_output_tokens'],8000)
        self.assertEqual(value['result']['stage'],'evidence')
        self.assertEqual(value['result']['paragraphs'][0]['evidence_quotes'][0]['quote'],payload['sources'][0]['text'])
        props=body['text']['format']['schema']['properties']['paragraphs']['items']['properties']
        self.assertNotIn('evidence_quotes',props)
        self.assertEqual(set(props['evidence_source_ids']['items']['enum']),{s['id'] for s in payload['sources']})

    def test_evidence_selection_cannot_introduce_text_or_unknown_source_ids(self):
        payload=r.semantic_payload(self.edition,self.sources,self.evidence)
        for mutation in ('unknown','duplicate','extra_text','wrong_paragraph_source','empty_support'):
            with self.subTest(mutation=mutation):
                wire=self.wire_stage('evidence',payload)
                row=wire['paragraphs'][0]
                if mutation=='unknown':row['evidence_source_ids']=['invented']
                elif mutation=='duplicate':row['evidence_source_ids']*=2
                elif mutation=='extra_text':row['evidence_quotes']=[{'source_id':row['source_ids'][0],'quote':'fabricated text'}]
                elif mutation=='wrong_paragraph_source':
                    sid=next(s['id'] for s in payload['sources'] if s['id'] not in payload['paragraphs'][0]['source_ids'])
                    row['evidence_source_ids']=[sid];row['source_ids']=[sid]
                else:row['evidence_source_ids']=[]
                with self.assertRaises(r.ReviewError):r.validate_semantic(r.resolve_evidence(wire,payload),'evidence',payload)

    def test_incomplete_refused_or_invalid_api_results_fail(self):
        payload=r.semantic_payload(self.edition,self.sources,self.evidence)
        responses=[{'status':'incomplete'}, {'status':'completed','output':[{'content':[{'type':'refusal','refusal':'No'}]}]}, {'status':'completed','output':[{'content':[{'type':'output_text','text':'not-json'}]}]}]
        for response in responses:
            with self.subTest(response=response):
                with self.assertRaises(r.ReviewError):r.api_review('evidence',payload,self.policy['semantic'],'fake','fixture',lambda *args:response)

    def test_oversize_input_is_not_truncated(self):
        settings=self.policy['semantic']|{'max_input_characters':10}
        with self.assertRaisesRegex(r.ReviewError,'exceeds limit'):r.api_review('evidence',r.semantic_payload(self.edition,self.sources,self.evidence),settings,'fake','fixture',lambda *args:None)

    def test_report_is_invalidated_by_text_or_register_change(self):
        r.save(self.root/'config/preflight.json',self.policy)
        r.save(self.root/'content/evidence'/(self.edition['id']+'.json'),self.evidence)
        report=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,environ={})
        r.save(self.root/'reports/preflight'/(self.edition['id']+'.json'),report)
        self.edition['sections'][0]['en'][0]+=' Changed claim.'
        current=r.current_report(self.root,self.edition,self.sources,self.policy)
        self.assertNotEqual(current['binding'],report['binding'])
        self.assertEqual(current['status'],'blocking_issues')

    def test_report_html_escapes_external_content(self):
        report=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,environ={})
        report['findings'].append(r.issue('FIXTURE','warning','opening:1','<script>bad()</script>','<script>bad()</script> נוסח'))
        from html import escape
        def pair(value):return escape(value['en'])+' '+escape(value['he'])
        page=r.report_body(report,self.edition,pair)
        self.assertNotIn('<script>',page);self.assertIn('&lt;script&gt;',page)

    def test_public_report_omits_response_ids_and_usage(self):
        report=r.evaluate(self.edition,self.sources,self.evidence,self.policy,root=self.root,semantic='auto',client=self.client,environ=self.env)
        public=r.public_report(report)
        self.assertNotIn('response_id',public['semantic']['stages']['evidence'])
        self.assertNotIn('usage',public['semantic']['stages']['evidence'])
        self.assertIn('response_id',report['semantic']['stages']['evidence'])


if __name__=='__main__':unittest.main()
