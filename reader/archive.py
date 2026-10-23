"""Publish complete earlier reading cycles alongside the current reader collection."""
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
from urllib.parse import urlparse
from xml.etree import ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from reader import portraits as portrait

ROOT=Path(__file__).resolve().parents[1]
BASE='https://moriahise.github.io/Shiurim/'
BOOKS=[('bereshit','Bereshit','בראשית'),('shemot','Shemot','שמות'),('vayikra','Vayikra','ויקרא'),('bamidbar','Bamidbar','במדבר'),('devarim','Devarim','דברים')]


def bi(value,tag='span',cls=''):
    return ''.join(f'<{tag} class="l-{lang} {cls}" lang="{lang}" dir="'+('rtl' if lang=='he' else 'ltr')+'">'+escape(value[lang])+f'</{tag}>' for lang in ('en','he'))


def label(en,he,tag='span',cls=''):
    return bi({'en':en,'he':he},tag,cls)


def load(path):
    data=json.loads(path.read_text(encoding='utf-8'))
    editions=data['editions'];year=data['cycle_year']
    if data.get('schema')!=1 or not isinstance(year,int) or [e['number'] for e in editions]!=list(range(1,55)):
        raise ValueError('An archive cycle requires all 54 individually numbered studies')
    if len({e['id'] for e in editions})!=54:raise ValueError('Duplicate archive study')
    for e in editions:
        if not re.fullmatch(str(year)+r'-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*',e['id']) or e['cycle_year']!=year:
            raise ValueError('Invalid archive identity')
        if not data['cycle_start']<=e['target_shabbat']<data['next_cycle_start']:raise ValueError('Reading date outside cycle')
        date.fromisoformat(e['target_shabbat'])
        if len(e['sections'])<5 or len(e['questions'])<3 or len(e['sources'])<3 or any(not s['paragraphs'] for s in e['sections']):raise ValueError('Incomplete study')
        pairs=[e[k] for k in ('title','subtitle','parashah','question','objective')]+e['questions']
        pairs += [s['title'] for s in e['sections']]+[p for s in e['sections'] for p in s['paragraphs']]
        for pair in pairs:
            if set(pair)!={'en','he'} or not pair['en'].strip() or not re.search('[א-ת]',pair['he']):raise ValueError('Unpaired archive text')
        for source in e['sources']:
            url=urlparse(source['url'])
            if url.scheme!='https' or url.netloc not in {'www.sefaria.org','sefaria.org'}:raise ValueError('Unsafe source link')
    return data


def cycle_of(e):
    match=re.match(r'^(\d{4})-',e['id'])
    if not match:raise ValueError('Study is missing its reading cycle')
    return int(match[1])


def minutes(e):
    return {lang:max(1,round(sum(len(p[lang].split()) for s in e['sections'] for p in s['paragraphs'])/(190 if lang=='en' else 160))) for lang in ('en','he')}


def heading(e):
    return bi({lang:f'{e["number"]:02} '+e['parashah'][lang] for lang in ('en','he')})


def reading_date(e):
    return label(date.fromisoformat(e['target_shabbat']).strftime('%d %B %Y'),e['hebrew_date'])


def source_html(source,index):
    text=escape(source['text']).replace('\n','<br>')
    return f'<article class="source" id="source-{index}"><div class="source-heading"><span class="source-no">{index:02}</span><h3>{bi(source["reference"])}</h3><a href="{escape(source["url"],quote=True)}" target="_blank" rel="noopener noreferrer">'+label('Open source ↗','פתיחת המקור ↗')+'</a></div><blockquote lang="he" dir="rtl">'+text+'</blockquote><p class="provenance">'+escape(source['credit'])+'<br>'+label('Source text as supplied for this edition; divine names follow its spelling.','נוסח המקור כפי שנמסר למהדורה זו; השמות נכתבו לפי נוסח המהדורה.')+'</p></article>'


def template_page(template,body,title,description,prefix):
    doc=portrait.Document(template)
    main=next(n for n in doc.nodes if n.tag=='main' and n.attrs.get('id')=='main')
    text=template[:main.start]+body+template[main.end:]
    text=re.sub(r'<title>.*?</title>',lambda m:'<title>'+escape(title)+' · Shiurim</title>',text,count=1,flags=re.S)
    text=re.sub(r'<meta name="description" content="[^"]*">',lambda m:'<meta name="description" content="'+escape(description,quote=True)+'">',text,count=1)
    if 'assets/archive.css' not in text:text=text.replace('</head>','<link rel="stylesheet" href="'+prefix+'assets/archive.css">\n</head>',1)
    if 'assets/portraits.css' not in text:text=text.replace('</head>','<link rel="stylesheet" href="'+prefix+'assets/portraits.css">\n</head>',1)
    return text


def lesson(e,template,profile,neighbours,sheet=False):
    prefix='../../../' if sheet else '../../'
    reading='../' if sheet else './'
    m=minutes(e);year=e['cycle_year']
    sections=[]
    if not sheet:
        for i,section in enumerate(e['sections'],1):
            paragraphs=''.join('<div class="paragraph-pair">'+bi(p,'p')+'</div>' for p in section['paragraphs'])
            sections.append(f'<section class="lesson-section" id="section-{i}"><h2>'+bi(section['title'])+'</h2>'+paragraphs+'</section>')
        sections.append('<section class="discussion"><div class="eyebrow">'+label('For the study table','לשולחן הלימוד')+'</div><h2>'+label('Keep the conversation going','ממשיכים לשאול')+'</h2><ol>'+''.join('<li>'+bi(q)+'</li>' for q in e['questions'])+'</ol></section>')
    source_sheet=''.join(source_html(s,i) for i,s in enumerate(e['sources'],1))
    sidebar=''.join(f'<a href="#section-{i}">'+bi(s['title'])+'</a>' for i,s in enumerate(e['sections'],1)) if not sheet else ''
    previous,next_=neighbours
    links=[]
    if previous:links.append('<a href="'+prefix+'shiur/'+previous['id']+'/">'+label('← Previous study','השיעור הקודם ←')+' · '+heading(previous)+'</a>')
    if next_:links.append('<a href="'+prefix+'shiur/'+next_['id']+'/">'+label('Next study →','השיעור הבא →')+' · '+heading(next_)+'</a>')
    text=('<main id="main"><div class="reading-top"><a href="'+prefix+f'archive/{year}/">'+label(f'← Cycle {year} archive',f'ארכיון מחזור {year} ←')+'</a><div class="reading-actions"><a href="'+reading+('' if sheet else 'sources/')+'">'+label('Read lesson' if sheet else 'Source sheet','לשיעור' if sheet else 'דף מקורות')+'</a><button data-print>'+label('Print / save PDF','הדפסה / שמירה כ־PDF')+'</button></div></div>'
          '<header class="lesson-header"><div class="eyebrow">'+heading(e)+' <span aria-hidden="true">/</span> '+reading_date(e)+'</div><div class="edition-status">'+label(f'Archive · Reading cycle {year}',f'ארכיון · מחזור הקריאה {year}')+'</div><h1>'+bi(e['title'])+'</h1><p class="lesson-subtitle">'+bi(e['subtitle'])+'</p><div class="lesson-meta">'+label(str(m['en'])+' min read',str(m['he'])+' דקות קריאה')+' <span>·</span> '+label(str(len(e['sources']))+' sources',str(len(e['sources']))+' מקורות')+'</div><p class="byline">'+label('Shiurim','שיעורים')+'</p>'+portrait.figure(profile,prefix,'lesson')+'</header>'
          '<div class="lesson-grid"><aside class="contents"><p class="eyebrow">'+label('In this shiur','בשיעור זה')+'</p>'+sidebar+'<a href="#sources">'+label('The sources','המקורות')+'</a><a href="#main">'+label('Back to top ↑','לראש הדף ↑')+'</a></aside><article class="lesson-body"><div class="guiding-question"><div class="eyebrow">'+label('The guiding question','השאלה המנחה')+'</div>'+bi(e['question'],'p')+'</div><div class="archive-objective"><div class="eyebrow">'+label('Learning objective','מטרת הלימוד')+'</div>'+bi(e['objective'],'p')+'</div>'+''.join(sections)+'<section id="sources" class="sources-section"><div class="eyebrow">'+label('Return to the text','חוזרים למקור')+'</div><h2>'+label('The source sheet','דף המקורות')+'</h2>'+source_sheet+'</section><nav class="archive-neighbours" aria-label="Study sequence">'+''.join(links)+'</nav></article></div></main>')
    return template_page(template,text,f'{e["number"]:02} {e["parashah"]["en"]} · {year} · '+e['title']['en'],e['objective']['en'],prefix)


def card(e,profile,prefix='./',hidden=False):
    m=minutes(e);search=' '.join([e['title'][lang]+' '+e['objective'][lang]+' '+e['parashah'][lang] for lang in ('en','he')]+[p[lang] for s in e['sections'] for p in s['paragraphs'] for lang in ('en','he')])
    url=prefix+'shiur/'+e['id']+'/'
    return (f'<article class="edition-card archive-card" data-cycle-year="{e["cycle_year"]}" data-search="{escape(search,quote=True)}" data-category="tanach"'+(' hidden' if hidden else '')+'><div class="edition-number">'+f'{e["number"]:02}<span>{e["cycle_year"]}</span></div>'+portrait.figure(profile,prefix,'card')+'<div class="edition-card-body"><div class="eyebrow">'+bi(e['parashah'])+' · '+reading_date(e)+'</div><h3><a href="'+url+'">'+bi(e['title'])+'</a></h3><p>'+bi(e['objective'])+'</p><div class="card-meta">'+label(str(m['en'])+' min read',str(m['he'])+' דקות קריאה')+' · '+label(str(len(e['sources']))+' sources',str(len(e['sources']))+' מקורות')+'<span class="small-status">'+label(f'Archive {e["cycle_year"]}',f'ארכיון {e["cycle_year"]}')+'</span></div></div><a class="card-arrow" href="'+url+'" aria-label="'+escape(e['title']['en'],quote=True)+'">↗</a></article>')


def archive_index(data,template,assigned):
    year=data['cycle_year'];prefix='../../'
    template=template.replace('href="../','href="../../').replace('src="../','src="../../')
    links=''.join('<a href="#book-'+key+'">'+label(en,he)+'</a>' for key,en,he in BOOKS)
    groups=[]
    for key,en,he in BOOKS:
        entries=[e for e in data['editions'] if e['book']==key]
        groups.append('<section class="archive-book" id="book-'+key+'"><div class="section-heading"><h2>'+label(en,he)+'</h2><span class="collection-count">'+label(str(len(entries))+' studies',str(len(entries))+' שיעורים')+'</span></div>'+''.join(card(e,assigned[e['id']],prefix) for e in entries)+'</section>')
    body=('<main id="main" class="archive-main"><header class="archive-intro"><div class="eyebrow">'+label('The annual study archive','ארכיון השיעורים השנתי')+'</div><h1>'+label(f'Reading cycle {year}',f'מחזור הקריאה {year}')+'</h1><p>'+label('54 complete studies · English and Hebrew · All five books of the Torah','54 שיעורים מלאים · אנגלית ועברית · כל חמשת חומשי התורה')+'</p><div class="archive-actions"><a class="button primary" href="'+prefix+'#library">'+label('Return to the current cycle →','למחזור הנוכחי ←')+'</a><a class="text-link" href="'+prefix+f'?year={year}#library">'+label('Search this cycle','חיפוש במחזור זה')+'</a></div><p class="archive-calendar-note">'+label('Double portions appear as individual studies with the same reading date.','פרשיות מחוברות מופיעות כשיעורים נפרדים באותו תאריך קריאה.')+'</p></header><nav class="archive-books" aria-label="Torah books">'+links+'</nav>'+''.join(groups)+'</main>')
    return template_page(template,body,f'{year} · Annual study archive',f'All 54 Torah portions in reading cycle {year}, with complete English and Hebrew lessons and original sources.',prefix)


def enrich_home(text,catalogue,archived,assigned,year):
    doc=portrait.Document(text);editions={e['id']:e for e in catalogue};edits=[]
    current=max(cycle_of(e) for e in catalogue)
    for node in doc.nodes:
        if not node.has('edition-card'):continue
        links=[n for n in doc.nodes if node.opening_end<=n.start<node.closing_start and n.tag=='a']
        eid=next(n.attrs['href'].rstrip('/').split('/')[-1] for n in links if '/shiur/' in n.attrs.get('href',''))
        if 'data-cycle-year' not in node.attrs:edits.append((node.opening_end-1,node.opening_end-1,f' data-cycle-year="{cycle_of(editions[eid])}"'))
    listing=next(n for n in doc.nodes if n.attrs.get('id')=='edition-list')
    edits.append((listing.closing_start,listing.closing_start,''.join(card(e,assigned[e['id']],hidden=True) for e in archived)))
    tools=next(n for n in doc.nodes if n.has('library-tools'))
    years=sorted({cycle_of(e) for e in catalogue},reverse=True)
    options=''.join(f'<option value="{y}" data-en="{y}'+(' · Current cycle' if y==current else ' · Archive')+'" data-he="'+str(y)+(' · המחזור הנוכחי' if y==current else ' · ארכיון')+'"'+(' selected' if y==current else '')+'>'+str(y)+(' · Current cycle' if y==current else ' · Archive')+'</option>' for y in years)
    control='<label class="filter-label year-filter" for="cycle-year">'+label('Reading cycle','מחזור קריאה')+f'<select id="cycle-year" data-default-year="{current}">'+options+'<option value="all" data-en="All cycles" data-he="כל המחזורים">All cycles</option></select></label>'
    existing=next((n for n in doc.nodes if n.has('year-filter')),None)
    if existing:edits.append((existing.start,existing.end,control))
    else:edits.append((tools.closing_start,tools.closing_start,control))
    library=next(n for n in doc.nodes if n.has('library-section'))
    section_heading=doc.inside(library,'section-heading')[0]
    edits.append((section_heading.closing_start,section_heading.closing_start,f'<a class="text-link archive-shortcut" href="./archive/{year}/">'+label(f'Explore archive {year} →',f'לעיון בארכיון {year} ←')+'</a>'))
    head=next(n for n in doc.nodes if n.tag=='head')
    if not any(n.tag=='script' and n.attrs.get('src')=='./assets/archive.js' for n in doc.nodes):
        edits.append((head.closing_start,head.closing_start,'<link rel="stylesheet" href="./assets/archive.css"><script defer src="./assets/archive.js"></script>\n'))
    for start,end,replacement in sorted(edits,reverse=True):text=text[:start]+replacement+text[end:]
    return text


def apply(site,data_path,reader=ROOT/'reader'):
    data=load(data_path);year=data['cycle_year']
    catalogue_path=site/'data/catalogue.json';catalogue=json.loads(catalogue_path.read_text())
    before={e['id'] for e in catalogue['editions']};new_ids={e['id'] for e in data['editions']}
    if before&new_ids:
        if new_ids<=before:return {'already_present':True,'cycle_year':year}
        raise ValueError('Partial archive import would duplicate existing studies')
    if year>=max(cycle_of(e) for e in catalogue['editions']):raise ValueError('Archive must precede the current reader cycle')
    profiles=portrait.load_profiles(reader/'rabbis.json')
    assigned={e['id']:portrait.profile_for(e,e['number'],profiles) for e in data['editions']}
    if len({p['id'] for p in assigned.values()})!=54:raise ValueError('Archive portraits must be different')
    first=catalogue['editions'][0]['id']
    lesson_template=(site/'shiur'/first/'index.html').read_text();sheet_template=(site/'shiur'/first/'sources/index.html').read_text()
    for i,e in enumerate(data['editions']):
        folder=site/'shiur'/e['id']
        if folder.exists():raise ValueError('Archive path already exists')
        (folder/'sources').mkdir(parents=True)
        neighbours=(data['editions'][i-1] if i else None,data['editions'][i+1] if i+1<len(data['editions']) else None)
        (folder/'index.html').write_text(lesson(e,lesson_template,assigned[e['id']],neighbours),encoding='utf-8')
        (folder/'sources/index.html').write_text(lesson(e,sheet_template,assigned[e['id']],neighbours,True),encoding='utf-8')
        catalogue['editions'].append({k:e[k] for k in ('id','title','parashah','target_shabbat')}|{'category':'tanach'})
    original_home=(site/'index.html').read_text()
    (site/'index.html').write_text(enrich_home(original_home,catalogue['editions'],data['editions'],assigned,year),encoding='utf-8')
    folder=site/'archive'/str(year);folder.mkdir(parents=True)
    (folder/'index.html').write_text(archive_index(data,(site/'about/index.html').read_text(),assigned),encoding='utf-8')
    catalogue_path.write_text(json.dumps(catalogue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for name in ('archive.css','archive.js'):shutil.copyfile(reader/name,site/'assets'/name)
    tree=ET.parse(site/'sitemap.xml');ns='http://www.sitemaps.org/schemas/sitemap/0.9';ET.register_namespace('',ns)
    for path in [f'archive/{year}/']+[f'shiur/{e["id"]}/{suffix}' for e in data['editions'] for suffix in ('','sources/')]:
        row=ET.SubElement(tree.getroot(),'{'+ns+'}url');ET.SubElement(row,'{'+ns+'}loc').text=BASE+path
    tree.write(site/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    total=sum(p.stat().st_size for p in site.rglob('*') if p.is_file())
    if total>=portrait.MAX_READER_BYTES:raise ValueError('Reader size limit exceeded')
    return {'cycle_year':year,'archive_studies':54,'total_studies':len(catalogue['editions']),'reader_bytes':total}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--site',type=Path,default=ROOT/'_site');args=parser.parse_args()
    for data in sorted((ROOT/'reader/archive').glob('*/lessons.json')):print(json.dumps(apply(args.site,data),ensure_ascii=False))


if __name__=='__main__':main()
