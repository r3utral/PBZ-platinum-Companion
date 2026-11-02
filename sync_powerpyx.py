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
EXPECTED_MIN={'Valle':61,'Bosque':69,'Lu':76,'Pangzhen':106,'Mandato':60,'Meigu':99,'Montaña':38,'Espejismo':35,'Soulrend':13}
# Latest documented numbered entry in each numeric regional article, not the overall game-map counter.
EXPECTED_LAST={'Valle':61,'Bosque':83,'Lu':76,'Pangzhen':106,'Mandato':60,'Meigu':99,'Montaña':38}
# Pangzhen's total 161 also includes the separate Mirage Estate walkthrough.

# PowerPyx currently lists 83 Crimson Forest collectibles but only documents
# #1-#68 and #83 in the region's numbered article. #69-#82 are covered
# incompletely in its later Mirage Estate / frozen-lake walkthrough.
# These are SOURCE gaps, not 14 invented collectible locations.
KNOWN_SOURCE_GAPS={'Bosque': set(range(69,83))}
NUMERIC={'Valle','Bosque','Lu','Pangzhen','Mandato','Meigu','Montaña'}
SLUG={'Valle':'valle','Bosque':'bosque','Lu':'lu','Pangzhen':'pangzhen','Mandato':'mandato','Meigu':'meigu','Montaña':'montaña','Espejismo':'espejismo','Soulrend':'soulrend'}
KIND_PREFIX=re.compile(r'^(?:Memory Flower(?:\s|\s*–)|Upgrade:|Bell\s*\(|Weapon:|Phantom Edge:|Weapon Tempering Material:|Phantom Edge Tempering Material:|Tempering Material:|Accessory(?: Fragment)?:|Medicine:|Healing:|Quick Hand (?:Zhang )?Treasure:|Quest(?:s)?:|Key Item:|Boss:|Challenge:|Scarecrow:|Banyan Tree:|Quick Hand.s Request\s*\()',re.I)
NUMBERED=re.compile(r'^\s*#\s*(?P<numbers>\d+(?:\s*(?:&|,|and|/)\s*#?\s*\d+){0,8})\s*(?:[–—-]\s*|\s+)(?P<title>.+)$',re.I)
# Includes #48 Scarecrow (no dash), #82 -Acolyte, and #32, #33, #34.

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

# Risk notes are authored explicitly from the PowerPyx regional warnings.
# They are attached to the relevant numbered item, never guessed from an unrelated location.
RISK_NOTES={
 'Mandato': {
  32: 'PERDIBLE: no mates a Red antes del jefe de Siete Estrellas; debe participar en la fase 2.',
  33: 'PERDIBLE: la recompensa de Red depende de mantenerla viva hasta la pelea de Siete Estrellas.',
  34: 'PERDIBLE: la recompensa de Red depende de mantenerla viva hasta la pelea de Siete Estrellas.',
  36: 'POSIBLE BUG: comprueba que el NPC transformable deje la flor de memoria. Si falla, recarga el autoguardado.',
  37: 'POSIBLE BUG: comprueba que el NPC transformable deje la flor de memoria. Si falla, recarga el autoguardado.',
  43: 'POSIBLE BUG: comprueba que el NPC transformable deje la flor de memoria. Si falla, recarga el autoguardado.',
  49: 'BUG DOCUMENTADO: antes del NPC detrás del edificio, guarda; al derrotarlo comprueba la flor. Si no aparece, recarga. PowerPyx señala que atacarlo antes de transformarse puede ayudar.',
  53: 'PERDIBLE: inspecciona primero el cadáver de Baishan tras Wu Lengshuang y antes de Yubi.',
  54: 'PERDIBLE: inspecciona primero el cadáver de Baishan tras Wu Lengshuang y antes de Yubi.',
 },
 'Meigu': {63:'PERDIBLE: completa Viaje a casa con Gen antes de llegar a este punto.'},
 'Pangzhen': {104:'PERDIBLE: para desbloquear Bai Xue, elige «Esto no te absolverá de tus pecados» en Libro de expiación.',105:'PERDIBLE: depende de Bai Xue.',106:'PERDIBLE: depende de Bai Xue.'},
}

def numbered_map(blocks,area,url):
    entries=[];phase='Primera visita';active=[];description=[];bell=''
    def flush():
        nonlocal active,description,bell
        if not active:return
        raw=' '.join(description)
        found=re.search(r'(?:From|near|beside|at) (?:the )?(.{2,65}?) Bell\b',raw,re.I)
        if found:bell=norm(found.group(1))
        for e in active:
            e['bell']=bell
            e['detail']=hint(raw,bell)
            risk=RISK_NOTES.get(area,{}).get(e['num'])
            if risk:
                e['detail']+=' '+risk
                e['priority']='Perdible' if risk.startswith('PERDIBLE') else 'Alta'
        active=[];description=[]
    for t in blocks:
        if re.search(r'^(?:Clean Up Visits|Cleanup Visits)',t,re.I):
            flush();phase='Volver: desbloqueos posteriores';continue
        if re.search(r'^Second Visit$',t,re.I):
            flush();phase='Segunda visita';continue
        if re.search(r'^First Visit$',t,re.I):
            flush();phase='Primera visita';continue
        m=NUMBERED.match(t)
        if m:
            flush()
            nums=[int(n) for n in re.findall(r'\d+',m.group('numbers'))]
            title=norm(m.group('title'))
            # A grouped entry may name multiple distinct rewards, split only at exact count.
            parts=title.split(' / ')
            names=parts if len(parts)==len(nums) else [title]*len(nums)
            for idx,n in enumerate(nums):
                name=names[idx]
                idcode={'Valle':'c','Bosque':'b'}.get(area)
                id=(idcode+'-'+f'{n:03d}') if idcode else f'v4-{SLUG[area]}-{n:03d}'
                obj={'id':id,'num':n,'name':f'#{n} · {name}', 'kind':classification(name),
                     'phase':phase,'priority':'Perdible' if 'MISSABLE' in name.upper() else '',
                     'source':url_fragment(url,f'#{n}'),'sourcePage':url,'region':area,
                     'bell':bell,'detail':''}
                entries.append(obj);active.append(obj)
            continue
        if active and not re.search(r'^(?:That.s 100%|For more|Comments|NEXT:|Key Item |Progression Required|Missable Warning|Bug Warning|.* Objective)',t,re.I):
            description.append(t)
    flush()
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
    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    data={'version':2,'generated':timestamp,'provider':'PowerPyx (referencia externa, no afiliado)','maps':{},'count':0,'warnings':[]}
    audit={'generated':timestamp,'maps':{},'errors':[],'warnings':[],'status':'checking'}
    for area,path in PAGES.items():
        url='https://www.powerpyx.com/'+path
        report={'source':url,'status':'checking','count':0,'errors':[],'warnings':[]}
        audit['maps'][area]=report
        try:
            body=fetcher(url)
            blocks=list(text_blocks(body))
            arr=numbered_map(blocks,area,url) if area in NUMERIC else unnumbered_map(blocks,area,url)
            report['count']=len(arr)
            if len(arr)<EXPECTED_MIN[area]:
                report['errors'].append(f'Extraídos {len(arr)} ítems, se esperaban al menos {EXPECTED_MIN[area]}')
            ids=[t['id'] for t in arr]
            duplicate=sorted({x for x in ids if ids.count(x)>1})
            if duplicate:report['errors'].append('IDs repetidos: '+str(duplicate[:20]))
            if area in NUMERIC:
                found={t['num'] for t in arr}
                expected_last=EXPECTED_LAST[area]
                if not found:
                    report['errors'].append('No se detectó ninguna entrada numerada')
                else:
                    report['last_number']=max(found)
                    if max(found)<expected_last:
                        report['errors'].append(f'Último índice observado #{max(found)}, pero PowerPyx publicó al menos #{expected_last}')
                    missing=[n for n in range(1,max(found)+1) if n not in found]
                    report['missing_numbers']=missing
                    unexpected=sorted(set(missing)-KNOWN_SOURCE_GAPS.get(area,set()))
                    if unexpected:
                        report['errors'].append('Números ausentes sin excepción documentada: '+str(unexpected))
                    if missing:
                        report['warnings'].append('Huecos de numeración en artículo regional: '+str(missing))
                        if area=='Bosque':
                            data['warnings'].append({'region':area,'type':'huecos_en_fuente',
                              'missing_numbers':missing,'message':'La guía regional omite #69-#82; hay que consultar el regreso al lago congelado en Mansión Espejismo.',
                              'source':url})
            if area in ['Espejismo','Soulrend']:
                report['note']='Artículo no numerado: se verificó cantidad mínima, pero no se puede certificar completitud numérica.'
            report['status']='ok' if not report['errors'] else 'error'
            if not report['errors']:
                data['maps'][area]=arr;data['count']+=len(arr)
        except Exception as ex:
            report['errors'].append(f'{type(ex).__name__}: {ex}')
            report['status']='error'
        audit['errors'] += [f'{area}: {x}' for x in report['errors']]
        audit['warnings'] += [f'{area}: {x}' for x in report['warnings']]
        print(f"{area}: {report['status'].upper()} · {report['count']} entradas"+
              (f" · anomalías: {'; '.join(report['errors'])}" if report['errors'] else ''))
    audit['status']='ok' if not audit['errors'] else 'error'
    Path('catalog_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('--- Resumen global (9 mapas) ---')
    if audit['errors']:
        for err in audit['errors']:print('ERROR:',err)
        print('Se generó catalog_audit.json. NO se publicó catalog.json ni se reemplazó el catálogo anterior.')
        raise ValueError(f'Auditoría global: {len(audit["errors"])} anomalías; revise TODAS en catalog_audit.json')
    for warn in audit['warnings']:print('ADVERTENCIA:',warn)
    return data

if __name__=='__main__':
    def fetch(url):
        r=requests.get(url,timeout=40,headers={'User-Agent':'Mozilla/5.0 (compatible; PBZPlatinumCompanionPersonalGuide/1.3; public information index)'})
        r.raise_for_status();return r.text
    result=build(fetch)
    Path('catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('OK: catálogo seguro publicado con',result['count'],'entradas')
