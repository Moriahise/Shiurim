"""GET-only source adapters. Writes are confined to the independent Shiurim tree."""
from __future__ import annotations

import argparse
import gzip
from datetime import datetime, timezone
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unicodedata
from urllib.error import HTTPError
from urllib.parse import quote, unquote, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    'shekhina.org': ('/',),
    'moriahise.github.io': ('/Sanhedrin/',),
    'storage.googleapis.com': ('/sefaria-export/json/',),
    'raw.githubusercontent.com': ('/Sefaria/Sefaria-Export/', '/Moriahise/sefaria-studio/'),
    'www.sefaria.org': ('/api/texts/', '/api/index'),
}


class SourceError(ValueError):
    pass


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def validate_url(url):
    p = urlparse(url)
    path = unquote(p.path)
    if (p.scheme != 'https' or p.hostname not in ALLOWED or p.username or p.password
            or p.port not in (None, 443) or '\\' in path or '..' in path.split('/')
            or not any(path.startswith(prefix) for prefix in ALLOWED.get(p.hostname, ()))):
        raise SourceError('Source URL is outside the read-only allowlist')
    return quote(url, safe=":/?=&%+;,@!$'()*[]-")


class Redirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class Transport:
    def __init__(self, limits=None):
        self.limits = limits or {'max_requests':40,'max_text_bytes':8_000_000,'max_index_bytes':40_000_000,'max_response_seconds':30}
        self.requests = 0
        self.cache = {}
        self.opener = build_opener(Redirects())

    def json(self, url, *, optional=False, index=False):
        url = validate_url(url)
        if url in self.cache:
            return self.cache[url]
        self.requests += 1
        if self.requests > self.limits['max_requests']:
            raise SourceError('Read request budget exceeded')
        limit = self.limits['max_index_bytes' if index else 'max_text_bytes']
        req = Request(url, headers={'Accept':'application/json','Accept-Encoding':'identity','User-Agent':'Shiurim-SourceReader/1.0'}, method='GET')
        try:
            with self.opener.open(req, timeout=self.limits['max_response_seconds']) as response:
                if response.headers.get('Content-Encoding','identity') not in ('identity',''):
                    raise SourceError('Unsupported compressed response')
                length = response.headers.get('Content-Length')
                if length and int(length) > limit:
                    raise SourceError('Source exceeds configured size limit')
                raw = response.read(limit+1)
        except HTTPError as e:
            if optional and e.code == 404:
                return None
            raise SourceError(f'Source returned HTTP {e.code}: {url}') from e
        if len(raw) > limit:
            raise SourceError('Source exceeds configured size limit')
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeDecodeError) as e:
            raise SourceError('Source did not return valid JSON') from e
        self.cache[url] = data
        return data


class Plain(HTMLParser):
    def __init__(self):
        super().__init__();self.parts=[];self.skip=0
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style'):self.skip+=1
        elif tag in ('p','br','div','li','h1','h2','h3') and not self.skip:self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style') and self.skip:self.skip-=1
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)


def plain(value):
    parser=Plain();parser.feed(str(value or ''))
    return re.sub(r'\n\s*\n+', '\n\n',unescape(''.join(parser.parts))).strip()


def normalized(value):
    return ''.join(c for c in unicodedata.normalize('NFKC',str(value)).lower() if not ('\u0591' <= c <= '\u05bd' or '\u05bf' <= c <= '\u05c7')).replace('׳',"'").replace('’',"'").replace('״','"')


def search_tokens(query):
    return re.findall(r"[^\W_]+(?:['\"][^\W_]+)*",normalized(query),re.UNICODE)


def shard(value,length=3):
    return sha256(value.encode()).hexdigest()[:length]


class Sanhedrin:
    def __init__(self, config, transport=None):
        self.config=config;self.transport=transport or Transport();self.base=None;self.manifest=None

    def init(self):
        if not self.config.get('enabled',True):raise SourceError('Sanhedrin connection is disabled')
        if self.manifest:return self.manifest
        errors=[]
        for base in self.config['base_urls']:
            try:
                m=self.transport.json(urljoin(base,self.config['manifest_path']))
                if (m.get('schema')!=1 or not re.fullmatch(r'releases/v1-[a-f0-9]{24}/',m.get('data_base',''))
                        or not isinstance(m.get('total'),int) or not 0<m['total']<1_000_000
                        or not isinstance(m.get('page_size'),int) or not 1<=m['page_size']<=1000):
                    raise SourceError('Invalid Sanhedrin release manifest')
                self.base=base;self.manifest=m;return m
            except Exception as e:errors.append(str(e))
        raise SourceError('Sanhedrin export unavailable: '+'; '.join(errors))

    def data(self,relative,optional=False):
        m=self.init()
        if not re.fullmatch(r'[a-zA-Z0-9_./-]+',relative) or '..' in relative or relative.startswith('/'):
            raise SourceError('Invalid export path')
        value=self.transport.json(urljoin(self.base,m['data_base']+relative),optional=optional)
        if value is None:
            manifest_url=urljoin(self.base,self.config['manifest_path'])
            if hasattr(self.transport,'cache'):self.transport.cache.pop(validate_url(manifest_url),None)
            current=self.transport.json(manifest_url)
            if current.get('release')!=m['release']:
                raise SourceError('Sanhedrin release changed; restart the query')
        # A newer manifest is checked but never adopted within a query.
        return value

    def metadata(self,ordinals):
        m=self.init();items={}
        for page in sorted({n//m['page_size'] for n in ordinals}):
            rows=self.data(f'catalog/pages/{page:05d}.json')
            if not isinstance(rows,list):raise SourceError('Invalid catalogue page')
            items.update({x['n']:x for x in rows})
        if any(n not in items for n in ordinals):raise SourceError('Incomplete release metadata')
        return [items[n] for n in ordinals]

    def search(self,query,limit=12):
        m=self.init();limit=max(1,min(int(limit),30))
        terms=list(dict.fromkeys(m.get('synonyms',{}).get(t,t) for t in search_tokens(query)))
        terms=[t for t in terms if len(t)>=2 and t not in m.get('stopwords',[])]
        if not query.strip():
            candidates=list(range(m['total']));scores={}
        elif not terms:
            candidates=[];scores={}
        else:
            maps=[]
            for term in terms[:8]:
                part=self.data('search/'+shard(term)+'.json',True) or {}
                postings=part.get(term,[])
                if len(postings)%2:raise SourceError('Invalid postings')
                current=dict(zip(postings[::2],postings[1::2]))
                if any(not isinstance(n,int) or not 0<=n<m['total'] for n in current):raise SourceError('Invalid search ordinal')
                maps.append(current)
            if len(terms)>8:raise SourceError('Use at most eight search terms')
            ids=set(maps[0]).intersection(*(set(x) for x in maps[1:]))
            scores={n:sum(x[n] for x in maps) for n in ids}
            candidates=sorted(ids,key=lambda n:(-scores[n],n))
        return {'provider':'sanhedrin','release':m['release'],'total':len(candidates),'items':self.metadata(candidates[:limit])}

    def detail(self,public_id):
        if not public_id or len(public_id)>160:raise SourceError('Invalid public ID')
        locations=self.data('catalog/locator/'+shard(public_id,2)+'.json',True) or {}
        location=locations.get(public_id)
        if not location:raise SourceError('Public ID not found')
        expected='content/'+shard(public_id,2)+'/'+sha256(public_id.encode()).hexdigest()+'.json'
        if location.get('file')!=expected:raise SourceError('Unexpected content locator')
        item=self.data(expected)
        if item.get('id')!=public_id:raise SourceError('Public ID mismatch')
        return item

    def capture(self,public_id):
        q=self.detail(public_id)
        question=plain(q.get('question_html',''))
        answers=[plain(a.get('html','')) for a in q.get('answers',[])]
        text='\n\n'.join([question]+[a for a in answers if a]).strip()
        if not text:raise SourceError('Record has no usable full text')
        m=self.init()
        return {
            'id':'sanhedrin-'+sha256(public_id.encode()).hexdigest()[:20],
            'provider':'sanhedrin','language':q.get('language','he'),
            'reference_en':q.get('title_en') or q.get('title') or public_id,
            'reference_he':q.get('title_he') or ('סנהדרין · '+public_id),
            'url':urljoin(self.base,'qa.html?id='+quote(public_id,safe='')),
            'original_url':q.get('url'), 'version':m['release'],
            'license':q.get('license') or 'unrecorded', 'author':q.get('author'),
            'answers_attribution':[{k:v for k,v in a.items() if k not in ('html','text','body')} for a in q.get('answers',[])],
            'retrieved_at':utcnow(),'text':text,'sha256':sha256(text.encode()).hexdigest(),
            'origin':{'public_id':public_id,'release':m['release'],'data_base':m['data_base']},
            'review_status':'research_capture_only',
        }


def compact_catalogue(data,origin):
    if not isinstance(data,dict) or not isinstance(data.get('books'),list):raise SourceError('Invalid Sefaria catalogue')
    works={}
    for b in data['books']:
        title=b.get('title');language=b.get('language');url=b.get('json_url')
        if not title or language not in ('Hebrew','English') or not url:continue
        validate_url(url)
        if not url.startswith('https://storage.googleapis.com/sefaria-export/json/'):
            raise SourceError('Book URL outside Sefaria export bucket')
        book=works.setdefault(title,{'title':title,'categories':b.get('categories',[]),'languages':{}})
        current=book['languages'].get(language)
        if current is None or b.get('versionTitle')=='merged':
            book['languages'][language]={'version':b.get('versionTitle') or 'unrecorded','url':url}
    if not works:raise SourceError('Empty Sefaria catalogue')
    return {'schema':1,'origin':origin,'generated_at':data.get('generated_at'),'indexed_at':utcnow(),'works':sorted(works.values(),key=lambda b:b['title'].casefold())}


class Sefaria:
    def __init__(self,config,transport=None,catalogue=None):
        self.config=config;self.transport=transport or Transport();self.catalogue=catalogue

    def sync(self):
        if not self.config.get('enabled',True):raise SourceError('Sefaria connection is disabled')
        errors=[]
        for url in self.config['index_urls']:
            try:
                candidate=compact_catalogue(self.transport.json(url,index=True),url)
                try:
                    toc=self.transport.json('https://www.sefaria.org/api/index',index=True)
                    hebrew={}
                    def walk(nodes):
                        for node in nodes:
                            if isinstance(node,dict) and isinstance(node.get('contents'),list):walk(node['contents'])
                            elif isinstance(node,dict) and node.get('title') and node.get('heTitle'):hebrew[node['title']]=node['heTitle']
                    walk(toc)
                    for book in candidate['works']:
                        if book['title'] in hebrew:book['he_title']=hebrew[book['title']]
                    candidate['hebrew_titles']=sum('he_title' in b for b in candidate['works'])
                except Exception as e:
                    candidate['hebrew_title_warning']=str(e)
                self.catalogue=candidate;return candidate
            except Exception as e:errors.append(str(e))
        raise SourceError('Sefaria indices unavailable: '+'; '.join(errors))

    def search(self,query,language=None,limit=20):
        if not self.config.get('enabled',True):raise SourceError('Sefaria connection is disabled')
        c=self.catalogue or self.sync();tokens=normalized(query).split()
        items=[b for b in c['works'] if (not language or language in b['languages']) and all(t in normalized(b['title']+' '+b.get('he_title','')+' '+' '.join(b['categories'])) for t in tokens)]
        return {'provider':'sefaria-export','total':len(items),'items':items[:max(1,min(limit,30))]}

    def book(self,title,language='Hebrew'):
        c=self.catalogue or self.sync();book=next((b for b in c['works'] if b['title']==title),None)
        if not book or language not in book['languages']:raise SourceError('Book/language not found')
        data=self.transport.json(book['languages'][language]['url'])
        if data.get('title')!=title or 'text' not in data:raise SourceError('Book identity mismatch')
        return data

    def capture_reference(self,reference,language='Hebrew'):
        if not reference.strip() or len(reference)>240:raise SourceError('Invalid exact reference')
        url=self.config['api_prefix']+quote(reference,safe='')+'?context=0&commentary=0&pad=0'
        data=self.transport.json(url)
        if data.get('error') or not data.get('ref'):raise SourceError('Reference could not be resolved')
        field='he' if language=='Hebrew' else 'text'
        def flatten(x):
            if isinstance(x,str):return [plain(x)]
            if isinstance(x,list):return [s for child in x for s in flatten(child)]
            raise SourceError('Unsupported reference text structure')
        text='\n'.join(flatten(data.get(field,[]))).strip()
        if not text:raise SourceError('Reference has no text in requested language')
        version=data.get('heVersionTitle' if language=='Hebrew' else 'versionTitle') or 'unrecorded'
        return {
            'id':'sefaria-'+sha256((data['ref']+'|'+language+'|'+version).encode()).hexdigest()[:20],
            'provider':'sefaria','language':'he' if language=='Hebrew' else 'en',
            'reference_en':data['ref'],'reference_he':data.get('heRef') or 'ספריא',
            'url':'https://www.sefaria.org/'+quote(data['ref'].replace(' ','_'),safe=':,.–-'),
            'version':version,'version_source':data.get('heVersionSource' if language=='Hebrew' else 'versionSource'),
            'license':data.get('heLicense' if language=='Hebrew' else 'license') or 'unrecorded',
            'retrieved_at':utcnow(),'text':text,'sha256':sha256(text.encode()).hexdigest(),
            'origin':{'resolved_ref':data['ref'],'retrieval':'exact-reference-api'},'review_status':'research_capture_only',
        }


def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    temp.replace(path)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['sync','search','capture','health'])
    p.add_argument('--provider',choices=['sanhedrin','sefaria'],default='sanhedrin')
    p.add_argument('--query',default='')
    p.add_argument('--id')
    p.add_argument('--ref')
    p.add_argument('--language',choices=['Hebrew','English'],default='Hebrew')
    args=p.parse_args()
    config=json.loads((ROOT/'config/libraries.json').read_text())
    transport=Transport(config['limits'])
    catalogue_path=ROOT/'content/library-catalogue/sefaria.json.gz'
    catalogue=json.loads(gzip.decompress(catalogue_path.read_bytes())) if catalogue_path.exists() else None
    san=Sanhedrin(config['sanhedrin'],transport)
    sef=Sefaria(config['sefaria'],transport,catalogue)
    try:
        if args.command=='sync':
            try:
                c=sef.sync()
                catalogue_path.parent.mkdir(parents=True,exist_ok=True)
                temp=catalogue_path.with_suffix('.tmp')
                temp.write_bytes(gzip.compress(json.dumps(c,ensure_ascii=False,separators=(',',':')).encode(),compresslevel=9,mtime=0))
                temp.replace(catalogue_path)
                result={'works':len(c['works']),'origin':c['origin'],'generated_at':c['generated_at'],'fresh':True}
            except Exception as e:
                if not catalogue:raise
                result={'works':len(catalogue['works']),'fresh':False,'retained_existing':True,'error':str(e)}
        elif args.command=='health':
            result={'checked_at':utcnow()}
            def sef_health():
                if not catalogue:raise SourceError('No local book catalogue')
                sample=sef.book('Genesis','Hebrew')
                return {'works':len(catalogue['works']),'origin':catalogue['origin'],'catalogue_date':catalogue.get('generated_at'),'google_export_available':bool(sample.get('text'))}
            for name,action in [('sanhedrin',lambda:{'total':san.init()['total'],'release':san.init()['release']}),('sefaria',sef_health)]:
                try:result[name]={'ok':True,**action()}
                except Exception as e:result[name]={'ok':False,'error':str(e)}
            dump(ROOT/'reports/libraries-health.json',result)
        elif args.command=='search':
            result=san.search(args.query) if args.provider=='sanhedrin' else sef.search(args.query,args.language)
        else:
            if args.provider=='sanhedrin':
                if not args.id:raise SourceError('--id is required')
                result=san.capture(args.id)
            else:
                if not args.ref:raise SourceError('--ref is required')
                result=sef.capture_reference(args.ref,args.language)
            target=ROOT/'drafts/sources'/(result['id']+'.json')
            if target.exists():
                existing=json.loads(target.read_text())
                if existing.get('sha256')==result['sha256'] and existing.get('version')==result['version'] and existing.get('license')==result['license']:
                    result=existing
                else:
                    suffix=sha256(json.dumps(result,ensure_ascii=False,sort_keys=True).encode()).hexdigest()[:16]
                    target=target.with_name(result['id']+'-'+suffix+'.json')
                    dump(target,result)
            else:
                dump(target,result)
            result={'saved':str(target),'id':result['id'],'sha256':result['sha256'],'license':result['license'],'review_status':result['review_status']}
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except Exception as e:
        print('Source connection failed: '+str(e),file=sys.stderr);return 1


if __name__=='__main__':raise SystemExit(main())
