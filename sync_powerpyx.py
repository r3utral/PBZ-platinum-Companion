#!/usr/bin/env python3
"""Generate concise, factual collectible index from the publicly available PowerPyx pages.

Only headings, factual bell names and short navigational landmarks are stored.
Full walkthrough text remains on PowerPyx and is linked, not mirrored.
"""
import json,re,sys,html,datetime,unicodedata
from pathlib import Path
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup

PAGES={
'Valle':'phantom-blade-zero-weeping-creek-valley-collectible-locations/',
'Bosque':'phantom-blade-zero-crimson-forest-collectible-locations/',
'Lu':'phantom-blade-zero-village-of-lu-collectible-locations/',
'Pangzhen':'phantom-blade-zero-pangzhen-collectible-locations/',
'Mandato':'phantom-blade-zero-mandate-encampment-collectible-locations/',
'Meigu':'phantom-blade-zero-meigu-lake-collectible-locations/',
'Montaña':'phantom-blade-zero-mountain-of-imprisonment-collectible-locations/',
'Espejismo':'phantom-blade-zero-mirage-estate-pangzhen-collectible-locations/',
'Soulrend':'phantom-blade-zero-mount-soulrend-collectible-locations/'
}
EXPECTED_MIN={'Valle':55,'Bosque':69,'Lu':70,'Pangzhen':95,'Mandato':56,'Meigu':75,'Montaña':30,'Espejismo':35,'Soulrend':13}
# PowerPyx currently lists 83 Crimson Forest collectibles but only documents
# #1-#68 and #83 in the region's numbered article. #69-#82 are covered
# incompletely in its later Mirage Estate / frozen-lake walkthrough.
# These are SOURCE gaps, not 14 invented collectible locations.
KNOWN_SOURCE_GAPS={'Bosque': set(range(69,83))}
NUMERIC={'Valle','Bosque','Lu','Pangzhen','Mandato','Meigu','Montaña'}
SLUG={'Valle':'valle','Bosque':'bosque','Lu':'lu','Pangzhen':'pangzhen','Mandato':'mandato','Meigu':'meigu','Montaña':'montaña','Espejismo':'espejismo','Soulrend':'soulrend'}
KIND_PREFIX=re.compile(r'^(?:Memory Flower(?:\s|\s*–)|Upgrade:|Bell\s*\(|Weapon:|Phantom Edge:|Weapon Tempering Material:|Phantom Edge Tempering Material:|Tempering Material:|Accessory(?: Fragment)?:|Medicine:|Healing:|Quick Hand (?:Zhang )?Treasure:|Quest(?:s)?:|Key Item:|Boss:|Challenge:|Scarecrow:|Banyan Tree:|Quick Hand.s Request\s*\()',re.I)
NUMBERED=re.compile(r'^\s*#\s*(\d+)(?:\s*(?:&|,|and|/)\s*#?\s*(\d+))?(?:\s*(?:&|,|and|/)\s*#?\s*(\d+))?\s*[–—-]\s*(.+)$',re.I)
LANDMARKS={
 'bridge':'puente','stairs':'escaleras','ladder':'escalera','roof':'tejado','chest':'cofre','courtyard':'patio','river':'río','cave':'cueva','wall':'muro','balcony':'balcón','platform':'plataforma','cliff':'acantilado','building':'edificio','waterfall':'cascada','tunnel':'túnel','tower':'torre','altar':'altar','dock':'muelle','furnace':'horno','tree':'árbol','path':'sendero','floor':'piso','enemy':'enemigos','boat':'barca','gate':'portón','window':'ventana','zipline':'tirolina','scaffolding':'andamio','statue':'estatua','hall':'salón'
}

def norm(t):
    return re.sub(r'\s+',' ',t.replace('\xa0',' ')).strip()
def text_blocks(doc):
    soup=BeautifulSoup(doc,'html.parser')
    entry=soup.select_one('article .entry-content') or soup.select_one('.entry-content') or soup.select_one('main')
    if not entry: raise ValueError('No se encuentra el contenido principal del artículo')
    for c in entry.find_all(['aside','figure','script','style','form','footer','nav','noscript','iframe','div'],recursive=True):
        if c.name=='div' and ('gallery' not in ' '.join(c.get('class',[]))):continue
        c.decompose()
    for e in entry.find_all(['p','h2','h3','h4','li'],recursive=True):
        if e.find_parent(['p','h2','h3','h4','li']) is not None:continue
        t=norm(e.get_text(' ',strip=True))
        if t:yield t

def classification(t):
    s=t.lower()
    if any(x in s for x in ['memory flower','flor de memoria']):return 'Flor de memoria'
    if 'bell' in s or 'campana' in s:return 'Campana'
    if 'sha-chi' in s or 'blackstone' in s:return 'Mejora'
    if 'tale' in s or 'quest' in s:return 'Misión'
    if 'accessory' in s:return 'Accesorio'
    if 'tempering' in s:return 'Material de templado'
    if 'weapon' in s or 'phantom edge' in s:return 'Arma'
    if 'medicine' in s or 'healing' in s:return 'Medicina'
    if 'treasure' in s:return 'Tesoro'
    if 'key item' in s:return 'Objeto clave'
    if 'boss' in s:return 'Jefe'
    if 'challenge' in s or 'banyan' in s:return 'Desafío'
    return 'Coleccionable'

def hint(text, bell):
    # Generate sparse wayfinding facts; never copy a paragraph from the guide.
    keys=[(re.search(r'\b'+re.escape(eng)+r'\w*\b',text,re.I).start(),sp) for eng,sp in LANDMARKS.items() if re.search(r'\b'+re.escape(eng)+r'\w*\b',text,re.I)]
    keys=[sp for _,sp in sorted(keys)]
    keys=list(dict.fromkeys(keys))[:4]
    b=f'Campana de referencia: {bell}. ' if bell else ''
    if keys:return b+'Hitos del recorrido: '+', '.join(keys)+'. Consulta PowerPyx para giros y requisitos exactos.'
    return b+'Consulta el enlace de PowerPyx para confirmar el trayecto y sus requisitos.'

def url_fragment(url,title):
    # A clickable link to the specific factual item title, not a copy of its walkthrough.
    return url+'#:~:text='+quote(title, safe='')

def numbered_map(blocks,area,url):
    entries=[];phase='Primera visita';buffer=[];current=None;bell=''
    def flush():
        nonlocal current,buffer,bell
        if current:
            description=' '.join(buffer)
            current['bell']=bell
            current['detail']=hint(description,bell)
            current['priority']='Perdible' if re.search(r'MISSABLE|missable',current['name']+' '+description,re.I) else ''
            entries.append(current)
        current=None;buffer=[]
    for t in blocks:
        if re.search(r'Clean Up Visits',t,re.I):flush();phase='Volver: desbloqueos posteriores';continue
        if re.search(r'First Visit',t,re.I):flush();phase='Primera visita';continue
        m=NUMBERED.match(t)
        if m:
            flush();nums=[int(n) for n in m.groups()[:3] if n];title=norm(m.group(4));
            for idx,n in enumerate(nums):
                cat=classification(title)
                # Keep one checkbox per collectible number, even when the article groups several.
                idcode={'Valle':'c','Bosque':'b'}.get(area)
                id=(idcode+'-'+f'{n:03d}') if idcode else f'v4-{SLUG[area]}-{n:03d}'
                entry={'id':id,'num':n,'name':f'#{n} · {title}' + (f' (parte {idx+1}/{len(nums)})' if len(nums)>1 else ''),'kind':cat,'phase':phase,'priority':'Perdible' if 'MISSABLE' in title.upper() else '', 'source':url_fragment(url,f'#{n}'), 'sourcePage':url,'region':area,'bell':bell,'detail':''}
                # Same content line can represent multiple collectibles. They each get own stable ID.
                entries.append(entry)
            current=None;buffer=[];continue
        if current is None and entries and NUMBERED.match(t) is None:
            # Fill descriptions for most recent grouped numbered entry until next #
            if re.match(r'^(?:Key Item|Missable Warning|Bug Warning|Progression Required|Phantom Edge Required|Item Required|Memory Flower Pre-Requisite|.* Objective)',t,re.I):
                if 'Warning' in t or 'Required' in t:bell='';
                continue
            if not re.search(r'^(?:That.s 100%|For more|Comments|NEXT:)',t,re.I):
                e=entries[-1]
                if not e['detail']:
                    bm=re.search(r'(?:From|by|near|beside) (?:the )?(.{2,58}?) Bell\b',t,re.I)
                    if bm:bell=norm(bm.group(1))
                    st=max(0,len(entries)-3)
                    for k in range(st,len(entries)):
                        if entries[k]['detail']:continue
                        entries[k]['bell']=bell
                        entries[k]['detail']=hint(t,bell)
    for entry in entries:
        if not entry['detail']:entry['detail']=hint('',entry.get('bell',''))
    return entries

# Compatibility aliases for already published checklist IDs. These prevent resetting
# a friend's ticks when an unnumbered PowerPyx walkthrough is re-indexed.
LEGACY_ALIAS={
'Espejismo':[
 (r'^Quest: The Way Forward$',1),
 (r"Yu.er.s Memory Flower.*Struggle",2),
 (r"Patron Gao.s Memory Flower.*Thread-Binding",3),
 (r"Disciple.s Memory Flower.*Abnormality",4),
 (r'^Upgrade: Blackstone Fragment$',5),
 (r'^Accessory: Feather Fan Plume$',6),
 (r'^Accessory Fragment: Nuo Mask Fragment: Sorrow$',7),
 (r'^Upgrade: Sha-Chi Amber Fragment$',8),
 (r'Disciple.s Memory Flower.*Gone Without a Trace',9),
 (r"Quick Hand.s Request \(Mirage Estate\)",10),
 (r'^Phantom Edge Tempering Material: Maintenance Oil$',11),
 (r'^Accessory Fragment: Nuo Mask Fragment: Wrath$',13),
 (r'^Medicine: Ritual Wine$',14),
 (r'^Accessory: Executioner.s Headscarf$',15),
 (r'^Weapon: Crescent Blade$',17),
 (r'Aberrant Three-Faced Puppet.*Wandering Healer',18),
 (r'^Key Item: Opera Ticket$',19),
 (r"General.s Bronze Mirror",20),
 (r'Gold-and-Silver Sachet',21),
 (r'^Accessory: Wraith Mask$',22),
 (r'Aberrant Three-Faced Puppet.*Frost and Chaos',23),
 (r'Disciple.s Memory Flower.*True Form',24),
 (r'^Accessory: Nuo Mask$',25),
 (r'^Accessory: Thundermoon Lantern$',26),
 (r'^Phantom Edge: Tiger Cannon$',27)
],
'Soulrend':[
 (r'Monster.*Scrawny Leg',1),
 (r"Craftsman.s Tool Kit",2),
 (r"Xuan Li.s Memory Flower.*Meng Hua",3),
 (r'Statue of the Loyal Hero',4),
 (r'^Quest: Cui \(Complete\)$',5),
 (r"Xuan Li.s Memory Flower.*Fused with the Blight",6),
 (r'Monster.*Infighting',7),
 (r'Monster.*Mastermind',8),
 (r'^Weapon: Bonesaw$',9),
 (r'^Weapon Tempering Material: Baishan Headband$',10),
 (r"Xuan Li.s Memory Flower.*Control",11),
 (r'^Weapon: The Lady.s Fan$',13),
 (r'^Weapon: Aureate$',14),
 (r'^Key Item: Radiant Heart$',15)
]}

def legacy_id(area,title,used):
    for expr,n in LEGACY_ALIAS.get(area,[]):
        if re.search(expr,title,re.I):
            key=f'v4-{SLUG[area]}-{n:03d}'
            if key not in used: used.add(key);return key
    return None

def unnumbered_map(blocks,area,url):
    entries=[];phase='Primera visita';last=None;label_count={};counter=0;used_legacy=set()
    for t in blocks:
        if re.search(r'Cleanup|Clean Up',t,re.I):phase='Volver: desbloqueos posteriores';continue
        if re.match(r'^Bell\s*:',t,re.I):
            if last:last['bell']=norm(t.split(':',1)[1]);last['detail']=hint(last.pop('_raw',''),last['bell'])
            continue
        if KIND_PREFIX.match(t) or (re.search(r'Quick Hand.s Request',t,re.I) and len(t)<100):
            counter+=1;kind=classification(t)
            key=re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',t.lower()).encode('ascii','ignore').decode())[:50].strip('-')
            label_count[key]=label_count.get(key,0)+1
            id=legacy_id(area,t,used_legacy) or f'pwx-{SLUG[area]}-{key}-{label_count[key]}'
            last={'id':id,'num':counter,'name':t,'kind':kind,'bell':'','phase':phase,'priority':'','detail':'','source':url_fragment(url,t),'sourcePage':url,'region':area,'_raw':''}
            entries.append(last);continue
        if last and not last.get('detail') and not t.startswith('That’s 100%'):
            last['_raw']+= ' '+t
            last['detail']=hint(t,last.get('bell',''))
    for item in entries:
        item['detail']=hint(item.pop('_raw',''),item['bell']) if item.get('_raw') else (item['detail'] or hint('',item['bell']))
    return entries

def build(fetcher):
    data={'version':2,'generated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'provider':'PowerPyx (referencia externa, no afiliado)','maps':{},'count':0,'warnings':[]}
    for area,path in PAGES.items():
        url='https://www.powerpyx.com/'+path
        body=fetcher(url)
        blocks=list(text_blocks(body))
        arr=numbered_map(blocks,area,url) if area in NUMERIC else unnumbered_map(blocks,area,url)
        # Full consistency validation: a partial parse never overwrites a working catalog.
        if len(arr)<EXPECTED_MIN[area]:raise ValueError(f'{area}: detectados solo {len(arr)} pasos (<{EXPECTED_MIN[area]}). Revisión manual necesaria.')
        if area in NUMERIC:
            found={t['num'] for t in arr}
            missing=[n for n in range(1,max(found)+1) if n not in found]
            unexpected=sorted(set(missing)-KNOWN_SOURCE_GAPS.get(area,set()))
            if unexpected:
                raise ValueError(f'{area}: faltan números no documentados como huecos conocidos: {unexpected[:20]}. No se publicará una lista incompleta.')
            if missing:
                data['warnings'].append({
                    'region':area,
                    'type':'huecos_en_fuente',
                    'missing_numbers':missing,
                    'message':('PowerPyx anuncia 83 coleccionables en el Bosque Carmesí, '
                               'pero no enumera individualmente estos números en su artículo regional. '
                               'Consulta también el apartado de limpieza del Bosque en Mansión del Espejismo.'),
                    'source':url,
                })
                print(f'AVISO {area}: PowerPyx aún no enumera {len(missing)} números: {missing}. Se conservarán como huecos de fuente.')
        ids=[t['id'] for t in arr]
        if len(ids)!=len(set(ids)):raise ValueError(f'{area}: IDs duplicados')
        data['maps'][area]=arr;data['count']+=len(arr)
        print(f'{area}: {len(arr)} ítems identificados')
    return data

if __name__=='__main__':
    def fetch(url):
        r=requests.get(url,timeout=40,headers={'User-Agent':'Mozilla/5.0 (compatible; PBZPlatinumCompanionPersonalGuide/1.2; public information index)'})
        r.raise_for_status();return r.text
    result=build(fetch)
    Path('catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('OK',result['count'])
