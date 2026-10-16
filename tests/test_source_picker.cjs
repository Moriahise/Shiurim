/* State integration tests with a minimal DOM double; no browser dependency. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const nav=require('../assets/sefaria-navigation.js');
class Element {
  constructor(tag='div'){this.tag=tag;this.children=[];this.dataset={};this.listeners={};this.textContent='';this.disabled=false;}
  append(...items){this.children.push(...items);}
  replaceChildren(...items){this.children=items;if(this.tag==='select')this._value=undefined;}
  get options(){return this.children;}
  get value(){return this._value??(this.tag==='select'?this.children[0]?.value||'':'');}
  set value(v){this._value=v;}
  setAttribute(k,v){this[k]=v;}
  removeAttribute(k){delete this[k];}
  addEventListener(k,v){this.listeners[k]=v;}
  async emit(k){await this.listeners[k]?.({preventDefault(){}});}
}
const settle=async()=>{for(let i=0;i<8;i++)await new Promise(resolve=>setImmediate(resolve));};
async function harness(){
  const names=['source-search','source-query','source-provider','source-feedback','source-results','source-reader','sanhedrin-state','sefaria-state','sefaria-category','sefaria-book-filter','sefaria-book','sefaria-book-count','sefaria-section','sefaria-levels','reference-language','sefaria-picker-state','selected-reference','selected-export','read-selection','retry-sefaria','sefaria-picker','reference-form','exact-reference'];
  const selects=new Set(['source-provider','sefaria-category','sefaria-book','sefaria-section','reference-language']);
  const elements=Object.fromEntries(names.map(id=>[id,new Element(selects.has(id)?'select':'div')]));
  const el=id=>elements[id];
  for(const value of ['Hebrew','English']){const o=new Element('option');o.value=value;el('reference-language').append(o);}
  el('source-provider').value='sefaria';
  const works=[{title:'Genesis',he_title:'בראשית',categories:['Tanakh','Torah'],languages:{Hebrew:{url:'https://storage.googleapis.com/sefaria-export/json/Genesis.json'}}},
    {title:'Shabbat',he_title:'שבת',categories:['Talmud','Bavli'],languages:{Hebrew:{url:'https://storage.googleapis.com/sefaria-export/json/Shabbat.json'}}},
    ...Array.from({length:24},(_,i)=>({title:'Work '+i,he_title:'חיבור '+i,categories:['Tanakh','Commentary'],languages:{Hebrew:{url:'https://storage.googleapis.com/sefaria-export/json/work.json'}}}))];
  const pending=new Map(), calls=[];
  const shape=title=>new Promise((resolve,reject)=>pending.set(title,{resolve,reject}));
  const response=(url,data)=>({ok:true,url,headers:{get:()=>null},text:async()=>JSON.stringify(data)});
  const context={document:{getElementById:el,documentElement:{dataset:{mode:'en'}},createElement:tag=>new Element(tag),createDocumentFragment:()=>new Element()},location:{href:'https://example.test/Shiurim/sources/',origin:'https://example.test'},URL,TextEncoder,TextDecoder,AbortController,setTimeout,clearTimeout,SefariaNavigation:nav,crypto:require('node:crypto').webcrypto,
    fetch:async u=>{
      const url=String(u);calls.push(url);
      if(url.endsWith('sefaria-library.json'))return response(url,{schema:1,works});
      if(url.includes('/api/shape/'))return response(url,await shape(decodeURIComponent(url.split('/api/shape/')[1])));
      if(url.includes('/api/v2/raw/index/')){const title=decodeURIComponent(url.split('/index/')[1]);return response(url,{title,schema:{addressTypes:title==='Shabbat'?['Talmud','Integer']:['Perek','Pasuk']}});}
      throw Error('Fixture unavailable');
    }};
  vm.runInNewContext(fs.readFileSync(require.resolve('../assets/source-library.js'),'utf8'),context);
  await settle();return {el,works,pending,calls};
}
test('category lists every match, filters Hebrew, and clears a former reference',async()=>{
  const {el}=await harness();
  assert.equal(el('sefaria-book').options.length,26); // 25 books plus prompt, beyond the topic result limit
  assert.equal(el('sefaria-book').options[1].value,'Genesis');
  el('sefaria-book-filter').value='בְּרֵאשִׁית';await el('sefaria-book-filter').emit('input');
  assert.equal(el('sefaria-book').options.length,2);
  el('sefaria-book-filter').value='missing';await el('sefaria-book-filter').emit('input');
  assert.equal(el('sefaria-book').disabled,true);assert.equal(el('read-selection').disabled,true);
  assert.equal(el('exact-reference').value,'');
});
test('a late book response cannot overwrite a newer selection or category',async()=>{
  const {el,pending}=await harness();
  el('sefaria-book').value='Genesis';await el('sefaria-book').emit('change');
  el('sefaria-category').value='Talmud';await el('sefaria-category').emit('change');
  el('sefaria-book').value='Shabbat';await el('sefaria-book').emit('change');
  pending.get('Shabbat').resolve([{title:'Shabbat',chapters:[0,0,7,17]}]);await settle();
  assert.equal(el('selected-reference').textContent,'Shabbat 2a');
  pending.get('Genesis').resolve([{title:'Genesis',chapters:[31,25]}]);await settle();
  assert.equal(el('selected-reference').textContent,'Shabbat 2a');
  el('sefaria-category').value='Tanakh';await el('sefaria-category').emit('change');
  assert.equal(el('selected-reference').textContent,'');assert.equal(el('read-selection').disabled,true);
});
test('failed structures offer retry and retain the direct export link',async()=>{
  const {el,pending}=await harness();
  el('sefaria-book').value='Genesis';await el('sefaria-book').emit('change');
  pending.get('Genesis').reject(Error('Offline'));await settle();
  assert.equal(el('read-selection').disabled,true);assert.equal(el('retry-sefaria').hidden,false);
  assert.equal(el('selected-export').children[0].href,'https://storage.googleapis.com/sefaria-export/json/Genesis.json');
  const retry=el('retry-sefaria').emit('click');await settle();
  pending.get('Genesis').resolve([{title:'Genesis',chapters:[31]}]);await retry;await settle();
  assert.equal(el('selected-reference').textContent,'Genesis 1');assert.equal(el('read-selection').disabled,false);
});
