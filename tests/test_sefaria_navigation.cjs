const {test} = require('node:test');
const assert = require('node:assert/strict');
const nav = require('../assets/sefaria-navigation.js');
const index = (title, addressTypes) => ({title, schema:{addressTypes}});

test('Torah chapters and exact verses retain their own numbering', () => {
  const sections=nav.sections([{title:'Genesis',heTitle:'בראשית',chapters:[31,25]}],index('Genesis',['Perek','Pasuk']));
  assert.equal(sections[0].ref,'Genesis 1');
  assert.equal(sections[0].he,'בראשית 1');
  assert.equal(nav.children(sections[1])[8].ref,'Genesis 2:9');
});
test('Talmud and its commentaries start at 2a, skipping empty sides', () => {
  for(const [title,chapters,types] of [
    ['Shabbat',[0,0,7,17],['Talmud','Integer']],
    ['Rashi on Shabbat',[0,0,[4,0,5],[2,2]],['Talmud','Integer','Integer']]
  ]) {
    const sections=nav.sections([{title,chapters}],index(title,types));
    assert.equal(sections[0].ref,title+' 2a');
    assert.equal(sections[1].ref,title+' 2b');
    if(types.length===3) {
      const lines=nav.children(sections[0]);assert.equal(lines[1].ref,title+' 2a:3');
      assert.equal(nav.children(lines[1])[4].ref,title+' 2a:3:5');
    }
  }
});
test('nested commentary counts do not become named nodes or fake verses', () => {
  const s=nav.sections([{title:'Rashi on Genesis',chapters:[[3,0,2],[],[1]]}],index('Rashi on Genesis',['Perek','Pasuk','Integer']));
  assert.deepEqual(s.map(s=>s.ref),['Rashi on Genesis 1','Rashi on Genesis 3']);
  assert.deepEqual(nav.children(s[0]).map(s=>s.ref),['Rashi on Genesis 1:1','Rashi on Genesis 1:3']);
});
test('complex named nodes, shared titles and default nodes keep canonical titles', () => {
  const idx={title:'Ben Ish Hai',schema:{nodes:[
    {key:'Introduction',addressTypes:['Integer']},
    {key:'Drashot',nodes:[{sharedTitle:'Noach',addressTypes:['Integer']}]},
    {default:true,addressTypes:['Integer','Integer']}
  ]}};
  const shape=[{isComplex:true,chapters:[
    {title:'Ben Ish Hai, Introduction',heTitle:'בן איש חי, הקדמה',chapters:19},
    {chapters:[{title:'Ben Ish Hai, Drashot, Noach',chapters:6}]},
    {title:'Ben Ish Hai',chapters:[2,3]}
  ]}];
  const s=nav.sections(shape,idx);
  assert.equal(s[0].ref,'Ben Ish Hai, Introduction');
  assert.equal(nav.children(s[1])[5].ref,'Ben Ish Hai, Drashot, Noach 6');
  assert.equal(s[2].ref,'Ben Ish Hai 1');
});
test('missing metadata and unsupported addresses keep named nodes without guessing', () => {
  const shape=[{title:'Work, Section',chapters:[2,3]}];
  for(const schema of [null,{title:'Work, Section',schema:{addressTypes:['Year']}},{title:'Work, Section',schema:{addressTypes:['Integer'],startingAddress:'4'}}]) {
    const s=nav.sections(shape,schema);
    assert.deepEqual(s.map(s=>s.ref),['Work, Section']);
    assert.deepEqual(nav.children(s[0]),[]);
  }
});
test('empty and invalid structures fail visibly instead of inventing a chapter', () => {
  for(const shape of [[],{}, {error:'Unavailable'},[{title:'Genesis',chapters:[0,[]]}]]) assert.throws(()=>nav.sections(shape,index('Genesis',['Perek'])));
});
