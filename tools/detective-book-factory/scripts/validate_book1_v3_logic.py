"""Enumerate Book 1 puzzle constraints; emit a source-bound 30-case logic ledger.

This is a logic audit, not PDF/visual QA. Spatial predicates are an explicit,
reviewable transcription of the locked clues, never the stored placements.
Stored placements are compared only AFTER exhaustive search. Unknown publication
changes still require editorial review; hashes bind each report to its input.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Each tuple is a reader clue in source-identity coordinates. Room skins/aliases
# are presentation mappings. on/beside use the exact locked object types.
SPATIAL = {
    2: [('Hope','row',3),('Hope','col','B'),('Drew','room','Library'),('Drew','col','D'),
        ('Rory','corner'),('Rory','beside','teacherdesk'),('Edgar','room','Art Room'),
        ('Edgar','col','F'),('Vesta','on','deskchair')],
    4: [('Finlay','row',2),('Finlay','col','A'),('Ivor','solo','Food Court'),
        ('Raquel','room','Prize Tent'),('Raquel','row',4),('Amelie','beside','ringtoss_stand'),
        ('Clarissa','room','Ring Toss'),('Clarissa','row',5)],
    6: [('Stafford','row',3),('Stafford','col','E'),('Hubert','room','Dinosaur Hall'),
        ('Hubert','beside','case'),('Ava','room','Foyer'),('Ava','row',2),
        ('Vera','room','Gallery'),('Vera','beside','statue'),('Wallace','on','bench'),('Wallace','beside','skeleton')],
    7: [('Bruce','solo','Lounge'),('Isla','rooms','Kitchen','Lounge'),
        ('Winifred','distance','commercial_range',2),('Zelda','wall'),('Zelda','beside','cart'),
        ('Roscoe','row',5),('Roscoe','col','E')],
    10: [('Eliza','on','seat'),('Eliza','beside','seat'),('Nicholas','col','F'),('Nicholas','on','seat'),
         ('Willie','col','B'),('Willie','beside','cryopod'),('Frances','distance','tank',7),
         ('Blythe','wall'),('Blythe','beside','crate'),('Verity','room_object_not_beside','console')],
    12: [('Kendra','solo','Bird Room'),('Norris','room','Play Yard'),('Norris','row',2),
         ('Irma','rank_south',3),('Earlene','rooms','Puppy Room','Bird Room'),('Cleo','col','B'),
         ('Cleo','wall'),('Siobhan','xor_room','Kendra','Training Room')],
    13: [('Jewel','diagonal','Shirley'),('Shirley','room','Ranger Station'),
         ('Elliot','same_room','Jewel'),('Wanda','northwest','Bronwen'),('Bronwen','southwest','Mercer'),
         ('Mercer','room','Ranger Station'),('Mercer','row',5)],
    15: [('Hiram','northeast','Carolyn'),('Primrose','northeast','Damian'),
         ('Damian','room','First-Aid Hut'),('Damian','row',5),('Carolyn','beside','camp_cot'),
         ('Jonquil','solo','Welcome Lodge'),('Isabella','room_object_not_beside','camp_cot')],
    17: [('Octavia','rooms','Kitchen Car','Baggage Car'),('Margaret','room','Kitchen Car'),
         ('Margaret','col','B'),('Kerry','room','Lounge Car'),('Kerry','row',6),('Samuel','on','bench'),
         ('Lincoln','room','Lounge Car'),('Lincoln','col','G'),('Ambrose','rows_north','Kerry',3)],
    19: [('Archibald','rows_north','Madge',2),('Theodore','distance','piano',7),
         ('Ottoline','xor_room','Archibald','Science Lab'),('Drew','same_room','Theodore'),
         ('Madge','southwest','Ottoline'),('Kimberly','room','Auditorium'),('Kimberly','col','F')],
    20: [('Standish','south','Pamela'),('Pamela','southeast','Millie'),('Leslie','diagonal','Aurora'),
         ('Millie','room','Propulsion Lab'),('Millie','row',4),('Aurora','same_room','Millie'),
         ('Thatcher','solo','Academy Mess Hall')],
    22: [('Leigh','diagonal','Irene'),('Irene','same_room','Natasha'),('Clarence','diagonal','William'),
         ('Natasha','xor_room','Leigh','Gymnasium'),('Gemma','distance','piano',7),
         ('William','room_object_not_beside','lockers')],
    23: [('Vesta','distance','gondola',7),('Charlene','northeast','Madge'),('Owen','southwest','Charlene'),
         ('Rebecca','columns_east','Charlene',2),('Madge','male_on_bench'),
         ('Peyton','xor_room','Vesta','Popcorn Stand')],
    25: [('Giselle','diagonal','Regan'),('Celia','room','Lobby'),('Celia','col','D'),
         ('Regan','northwest','Giselle'),('Theodore','diagonal','Warren'),('Silas','northeast','Giselle'),
         ('Warren','room','Laundry'),('Warren','on','stool')],
    29: [('Michelle','northwest','Vera'),('Cassandra','northeast','Ransom'),('Jordana','diagonal','Wilhelmina'),
         ('Betsy','same_room','Jordana'),('Vera','northwest','Cassandra'),('Ransom','room','Gymnasium'),
         ('Payton','same_room','Michelle'),('Wilhelmina','room','Office'),('Wilhelmina','beside','teacherdesk')],
}


def xy(cell):
    return ord(cell[0])-65, int(cell[1:])-1


def enumerate_spatial(case, max_nodes=500_000):
    """AC-3 + complete MRV search, stop at the second solution (non-unique)."""
    number = int(case['id'].split('_')[1])
    rows, cols = case['grid']['rows'], case['grid']['columns']
    people = [p['source_name'] for p in case['characters']]
    cells = [f'{chr(65+x)}{y+1}' for y in range(rows) for x in range(cols)]
    objects = {o['cell']: o for o in case['objects']}
    room_at = {c: r['source_room_id'] for r in case['rooms'] for c in r['cells']}
    room_id = {r['source_name']: r['source_room_id'] for r in case['rooms']}
    available = [c for c in cells if not objects.get(c, {}).get('blocked', False)]
    domains = {p: set(available) for p in people}
    binary = []
    solo = []
    bench_subjects = []

    def obj_cells(kind):
        result = [c for c,o in objects.items() if o['type'] == kind]
        if not result:
            raise ValueError(f'{case["id"]}: absent object type {kind}')
        return result

    def beside(c, kind):
        x,y = xy(c)
        return any(abs(x-xy(o)[0])+abs(y-xy(o)[1]) == 1 and room_at[c] == room_at[o]
                   for o in obj_cells(kind))

    def unary(p, fn):
        domains[p] = {c for c in domains[p] if fn(c)}

    for rule in SPATIAL[number]:
        p, kind, *a = rule
        if kind == 'row': unary(p, lambda c: xy(c)[1]+1 == a[0])
        elif kind == 'col': unary(p, lambda c: c[0] == a[0])
        elif kind in ('room','solo','rooms'):
            ids = {room_id[name] for name in a}
            unary(p, lambda c: room_at[c] in ids)
            if kind == 'solo': solo.append(p)
        elif kind == 'corner': unary(p, lambda c: xy(c)[0] in (0,cols-1) and xy(c)[1] in (0,rows-1))
        elif kind == 'wall': unary(p, lambda c: xy(c)[0] in (0,cols-1) or xy(c)[1] in (0,rows-1))
        elif kind == 'rank_south': unary(p, lambda c: xy(c)[1] == rows-a[0])
        elif kind == 'on': unary(p, lambda c: c in obj_cells(a[0]))
        elif kind == 'beside': unary(p, lambda c: beside(c,a[0]))
        elif kind == 'distance':
            unary(p, lambda c: any(sum(abs(v-w) for v,w in zip(xy(c),xy(o))) == a[1] for o in obj_cells(a[0])))
        elif kind == 'room_object_not_beside':
            unary(p, lambda c: any(room_at[c] == room_at[o] for o in obj_cells(a[0])) and not beside(c,a[0]))
        elif kind == 'male_on_bench': bench_subjects.append(p)
        else:
            q = a[0]
            if q not in people: raise ValueError(f'Unknown person {q}')
            if kind == 'xor_room':
                rid = room_id[a[1]]
                predicate = lambda c,d,rid=rid: (room_at[c] == rid) != (room_at[d] == rid)
            elif kind == 'same_room': predicate = lambda c,d: room_at[c] == room_at[d]
            elif kind == 'diagonal': predicate = lambda c,d: abs(xy(c)[0]-xy(d)[0]) == abs(xy(c)[1]-xy(d)[1]) == 1
            elif kind == 'rows_north':
                gap=a[1]; predicate=lambda c,d,gap=gap: xy(d)[1]-xy(c)[1] == gap
            elif kind == 'columns_east':
                gap=a[1]; predicate=lambda c,d,gap=gap: xy(c)[0]-xy(d)[0] == gap
            elif kind in ('northwest','northeast','southwest','southeast','south'):
                direction=kind
                def predicate(c,d,direction=direction):
                    x,y=xy(c); u,v=xy(d)
                    return (('north' not in direction or y<v) and ('south' not in direction or y>v)
                            and ('west' not in direction or x<u) and ('east' not in direction or x>u))
            else: raise ValueError(f'Unknown constraint {rule}')
            binary.append((p,q,predicate))
    for p in solo:
        for q in people:
            if p != q: binary.append((p,q,lambda c,d: room_at[c] != room_at[d]))
    pair_predicates = {(p,q): [] for p in people for q in people if p != q}
    for p,q,fn in binary:
        pair_predicates[p,q].append(fn)
        pair_predicates[q,p].append(lambda c,d,fn=fn: fn(d,c))
    # Compile pair support tables before recursion. No canonical placements used.
    support = {}
    for (p,q),predicates in pair_predicates.items():
        support[p,q] = {c:{d for d in domains[q]
                             if c[0] != d[0] and c[1:] != d[1:]
                             and all(fn(c,d) for fn in predicates)} for c in domains[p]}
    owner = case['source_owner']
    male = [p['source_name'] for p in case['characters'] if p['gender']=='m']
    benches = set(obj_cells('bench')) if bench_subjects else set()
    nodes=0; solutions=[]; limited=False

    def global_possible(ds):
        for oc in ds[owner]:
            rid=room_at[oc]
            possible=sum(any(room_at[c]==rid for c in ds[p]) for p in people if p != owner)
            forced=sum(all(room_at[c]==rid for c in ds[p]) for p in people if p != owner)
            if forced <= 1 <= possible: break
        else: return False
        for subject in bench_subjects:
            if not any(p != subject and any(c in benches and room_at[c]==room_at[d]
                       for c in ds[p] for d in ds[subject]) for p in male): return False
        return True

    def propagate(ds):
        queue=list(pair_predicates)
        while queue:
            p,q=queue.pop()
            keep={c for c in ds[p] if support[p,q][c] & ds[q]}
            if not keep: return False
            if keep != ds[p]:
                ds[p]=keep
                queue.extend((r,p) for r in people if r not in (p,q))
        return global_possible(ds)

    def visit(ds):
        nonlocal nodes,limited
        if len(solutions)>=2 or limited: return
        nodes+=1
        if nodes>max_nodes: limited=True; return
        if not propagate(ds): return
        remaining=[p for p in people if len(ds[p])>1]
        if not remaining:
            solutions.append({p:next(iter(ds[p])) for p in people}); return
        p=min(remaining,key=lambda p:(len(ds[p]),p))
        for c in sorted(ds[p]):
            candidate={q:set(values) for q,values in ds.items()}
            candidate[p]={c}; visit(candidate)
            if len(solutions)>=2 or limited: break
    visit({p:set(v) for p,v in domains.items()})
    canonical={p['source_name']:p['placement'] for p in case['characters']}
    companion=None
    if len(solutions)==1:
        solved=solutions[0]
        companions=[p for p in people if p != owner and room_at[solved[p]]==room_at[solved[owner]]]
        if len(companions)==1: companion={'name':companions[0],'coordinate':solved[companions[0]]}
    answer_matches=companion=={k:case['source_answer'][k] for k in ('name','coordinate')}
    return {'solution_count':len(solutions),'exhaustive':not limited and len(solutions)<2,
            'nodes':nodes,'solutions':solutions,'canonical_match':solutions == [canonical],
            'derived_companion_answer':companion,'answer_matches':answer_matches,
            'initial_domains':{p:sorted(v) for p,v in domains.items()},
            'constraints':[list(r) for r in SPATIAL[number]],
            'status':'PASS' if solutions == [canonical] and answer_matches and not limited else 'NEEDS WORK'}


def read_yaml(path):
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def load_missions(master=None):
    if master:
        return read_yaml(master)
    documents=[read_yaml(ROOT/f'content/book1_en_phase{i}.yml') for i in (1,2,3)]
    data=documents[0]
    data['missions']=sum((d['missions'] for d in documents),[])
    return data


def minutes(value):
    hour,minute=map(int,value.split(':'))
    return hour*60+minute


def tutorial_solutions(tutorial):
    people=tutorial['people']; n=tutorial['size']; answers=[]
    for col_order in itertools.permutations(range(n)):
        for row_order in itertools.permutations(range(1,n+1)):
            assignment={p:f'{chr(65+x)}{y}' for p,x,y in zip(people,col_order,row_order)}
            valid=True
            for clue in tutorial['clues']:
                s=clue.upper().rstrip('.')
                exact=re.fullmatch(r'(\w+) WAS IN ROW (\d+), COLUMN ([A-Z])',s)
                room=re.fullmatch(r'(\w+) WAS IN THE (\w+), COLUMN ([A-Z])',s)
                col_not=re.fullmatch(r'(\w+) WAS IN COLUMN ([A-Z]), BUT NOT IN ROW (\d+)',s)
                if exact:
                    p,row,col=exact.groups(); valid &= assignment[p]==col+row
                elif room:
                    p,r,col=room.groups()
                    area=next(x for x in tutorial['rooms'] if x['name'].upper()==r)
                    valid &= assignment[p] in area['cells'] and assignment[p][0]==col
                elif col_not:
                    p,col,row=col_not.groups(); valid &= assignment[p][0]==col and assignment[p][1:]!=row
                elif s.startswith(('EACH PERSON','THE BADGE APPEARED')):
                    pass
                else:
                    raise ValueError(f'Unmodelled tutorial clue: {clue}')
            if valid: answers.append(assignment)
    return answers


def code_solutions(code):
    solutions=[]
    for sequence in itertools.permutations(code['symbols']):
        valid=True
        for clue in code['clues']:
            s=clue.upper().rstrip('.')
            m=re.fullmatch(r'(\w+) COMES IMMEDIATELY AFTER (\w+)',s)
            if m: valid &= sequence.index(m[1])==sequence.index(m[2])+1; continue
            m=re.fullmatch(r'(\w+) (?:APPEARS|COMES) BEFORE (\w+)',s)
            if m: valid &= sequence.index(m[1])<sequence.index(m[2]); continue
            m=re.fullmatch(r'(\w+) COMES AFTER (\w+)',s)
            if m: valid &= sequence.index(m[1])>sequence.index(m[2]); continue
            m=re.fullmatch(r'(\w+) IS NOT (FIRST|SECOND|THIRD|FOURTH)',s)
            if m: valid &= sequence.index(m[1])!=['FIRST','SECOND','THIRD','FOURTH'].index(m[2]); continue
            raise ValueError(f'Unmodelled code clue: {clue}')
        if valid: solutions.append(list(sequence))
    return solutions


def nonspatial_checks(missions, runtime_cases, spatial_results):
    by_number={int(m['number']):m for m in missions}
    results={}
    def emit(n,ok,proof,answer=None,**extra):
        results[n]={'status':'PASS' if ok else 'NEEDS WORK','proof':proof,'answer':answer,**extra}
    m=by_number[1]; t=m['tutorial']; found=tutorial_solutions(t)
    old=dict(t); old['clues']=["COLE was in the Library, column A." if x.startswith('COLE was') else x for x in t['clues']]
    previous=tutorial_solutions(old)
    emit(1,found==[t['positions']],f'Exhaustive 4! × 4! row/column assignments: {len(found)} valid complete placement(s).',
         t['answer'],solutions=found,solution_count=len(found),before_repair_solution_count=len(previous),before_repair_counterexamples=previous)
    m=by_number[3]; v=m['visual']
    rubric=' '.join(str(v.get(k,'')) for k in ('rule','rules','evidence_rules','identity_rules','rubric','relevance_rule')).strip()
    rubric+=' '+as_text(m.get('investigation_rules',[])) if m.get('investigation_rules') else ''
    rubric_ok=bool(rubric) and not ('timing' in rubric.lower() and 'one of each' in rubric.lower())
    photo_answer='RIBBON KNOT + TAG NUMBER + SHOEPRINT DIRECTION'
    emit(3,len(v['meaningful'])==3 and rubric_ok and v['answer']==photo_answer,
         'Printed relevance rule distinguishes parcel identity, evidence-tag identity and route. Three named changes fit those categories; background decoration/loose props do not.' if rubric_ok else
         'Three declared meaningful differences and three decoys. Requires printed identity/route rubric; an instruction to find a timing change is unsupported by the existing six differences.',
         v['answer'],declared_meaningful=v['meaningful'],printed_rubric=rubric,
         visual_qa='Evidence photos and all six differences must be inspected in the rendered PDF.')
    m=by_number[5]; c=m['code']; found=code_solutions(c)
    old={'symbols':c['symbols'],'clues':['BOLT comes immediately after STAR.','BALL appears before HEART.','STAR is not first.','HEART is not third.']}
    old_solutions=code_solutions(old)
    emit(5,found==[c['answer']],f'Exhaustive 4! symbol permutations: {len(found)} valid code(s).',c['answer'],
         solution_count=len(found),solutions=found,before_repair_solution_count=len(old_solutions),before_repair_counterexamples=old_solutions)
    m=by_number[8]; route=m['route']; valid=[o['id'] for o in route['options'] if not o.get('fails')]
    context=json.dumps(m)
    explicit_time=bool(re.search(r'16:20',context))
    emit(8,valid==[route['answer']] and explicit_time,
         f'Hard closures eliminate A/B; remaining route(s) {valid}. Closure until16:30 requires a stated current time before16:30 and no waiting.',
         route['answer'],valid_options=valid,departure_time_explicit=explicit_time)
    m=by_number[9]; items=m['checkpoint']['evidence']
    matching=[i for i in items if 'plain' in i['mark'].lower() and '0' in i['mark']]
    classifications=all(i.get('recurring')==(i in matching) for i in items)
    count_ok='Four independent cases plus the opening badge' not in json.dumps(m)
    emit(9,classifications and count_ok,
         f'{len(matching)} matching plain-zero items; decorative ring/pointer patterns excluded. These establish recurrence, not cause.',
         m['checkpoint']['answer'],matching_items=matching,temporal_audit='Badge/case2/case4/case6 already occurred; any added item must cite an earlier source event.')
    m=by_number[11]; cl=m['classification']; start,end=re.search(r'(\d\d:\d\d)-(\d\d:\d\d)',cl['case_window']).groups()
    outside=[]
    for item in cl['items']:
        stamps=re.findall(r'\b\d\d:\d\d\b',item['label'])
        if stamps and any(not minutes(start)<=minutes(x)<=minutes(end) for x in stamps): outside.append(item['id'])
    question=m['objective']+' '+cl.get('question','')
    scoped=bool(re.search(r'(record|photo|timestamp)',question,re.I)) and not re.search(r'object that definitely|item cannot possibly',question,re.I)
    emit(11,outside==[cl['answer']] and scoped,
         f'Only timestamped record(s) {outside} fall outside {start}–{end}; untimestamped personal objects are not contradictory records.',
         cl['answer'],outside_records=outside,objective_scoped_to_records=scoped)
    m=by_number[14]; c=m['consistency']; edges=c['map']['edges']; distances={}
    for a,b in edges: distances[a,b]=distances[b,a]=1
    places=sorted({x for edge in edges for x in edge})
    for p in places: distances[p,p]=0
    for k in places:
        for a in places:
            for b in places:
                distances[a,b]=min(distances.get((a,b),999),distances.get((a,k),999)+distances.get((k,b),999))
    needed=distances['STAGE','DRESSING']*c['map']['walking_minutes_per_edge']
    impossible=[]
    statement_audit=[]
    for statement in c['statements']:
        stamps=re.findall(r'\b\d\d:\d\d\b',statement['text'])
        locations=re.findall(r'\b(?:on|in|toward) (Dressing|Hall|Stage|Prop)\b',statement['text'],flags=re.I)
        if len(stamps)==2 and len(locations)==2:
            required=distances[locations[0].upper(),locations[1].upper()]*c['map']['walking_minutes_per_edge']
            elapsed=minutes(stamps[1])-minutes(stamps[0])
            possible=elapsed>=required
            if not possible: impossible.append(statement['speaker'])
            statement_audit.append({'speaker':statement['speaker'],'minimum_minutes':required,'claimed_minutes':elapsed,'possible':possible})
        elif len(stamps)==1:
            statement_audit.append({'speaker':statement['speaker'],'possible':True,'basis':'One location/time assertion; no contradictory second endpoint.'})
        else: raise ValueError(f'Unmodelled timing statement: {statement}')
    emit(14,needed==4 and impossible==[c['answer']],
         'Shortest path Stage → Hall → Dressing has two edges, 2min each, so4min; claimed16:10→16:12 allows only2min. Other statements admit placements.',
         c['answer'],minimum_travel_minutes=needed,available_minutes=2,statements=statement_audit,
         assumption='Edges are all available routes and 2min is the minimum traversal time, including for the witness; no unstated shortcuts.')
    m=by_number[16]; tv=m['timeline_visual']; printed=' '.join(tv['evidence'])
    range_match=re.search(r'(\d{4}) through (\d{4})',printed)
    installed_match=re.search(r'UPGRADE COMPLETED (\d{4})',printed)
    if not range_match or not installed_match: raise ValueError('Unmodelled photo-date constraints')
    first,last=map(int,range_match.groups()); installed=int(installed_match[1])
    years=[y for y in tv['candidate_years'] if first<=y<=last and y>=installed]
    explicit_event='official events only' in printed and 'after that sticker was installed' in printed
    emit(16,years==[tv['answer']['year']] and tv['answer']['building']=='OLD ACADEMY ANNEX' and explicit_event,
         'Candidate years intersect the printed badge period1999–2003 and installed security date≥2001: only2002. Crest/plaque identifies the Training Annex. Envelope expiry is unnecessary and cannot alone date a photo.',
         tv['answer'],candidate_years=years,printed_event_rule=explicit_event,
         assumption='Badge-period evidence describes the official event date, not merely a vintage badge worn later; sticker was already installed when photo taken.')
    m=by_number[18]; tl=m['timeline']; offsets={}
    for rule in tl['rules']:
        parsed=re.fullmatch(r'(.+) = real time(?: (minus|plus) (\d+) minutes)?\.',rule)
        if not parsed: raise ValueError(f'Unmodelled clock rule: {rule}')
        offsets[parsed[1]]=(-1 if parsed[2]=='minus' else 1)*int(parsed[3] or 0)
    converted={r['id']:minutes(r['shown'])-offsets[r['source']] for r in tl['records']}
    ordered=sorted(converted,key=converted.get)
    valid=ordered==tl['answer_order'] and len(set(converted.values()))==len(converted)
    valid &= all(converted[r['id']]==minutes(r['real']) for r in tl['records'])
    emit(18,valid,'Subtract each clock offset from its displayed time; all four real timestamps differ, so their ascending order is unique.',
         ordered,computed_real_minutes=converted,assumption='Same day, fixed clock offsets, no midnight rollover.')
    m=by_number[21]; rec=m['reconstruction']; scraps={s['id']:s for s in rec['scraps']}; chains=[]
    for seq in itertools.permutations(scraps):
        if scraps[seq[0]]['left_edge']!='straight' or scraps[seq[-1]]['right_edge']!='straight': continue
        if all(scraps[a]['right_edge']==scraps[b]['left_edge'] for a,b in zip(seq,seq[1:])): chains.append(list(seq))
    emitted=[' '.join(scraps[i]['text'] for i in seq) for seq in chains]
    emit(21,chains==[rec['answer_order']] and emitted==[rec['answer_text']],
         f'Enumerated24 scrap orders using physical edge labels alone: {len(chains)} complete chain(s); sentence read only afterward.',
         emitted,solution_count=len(chains),chains=chains,before_repair_solution_count=0,
         before_repair_defect='A.right_edge=curve-1 did not match C.left_edge=wave-4.')
    m=by_number[24]; vs=m['visual_sequence']; prints=sorted(vs['prints'],key=lambda p:-p['mud']); values=[p['mud'] for p in prints]
    direction=f"{prints[0]['position']} -> {prints[-1]['position']}"
    printed_track=vs['rule'].lower()
    controlled=('uninterrupted' in printed_track or 'one continuous' in printed_track) and bool(re.search(r'no (?:fresh|new) mud',printed_track))
    emit(24,len(set(values))==len(values) and direction==vs['answer'] and controlled,
         'Strictly decreasing transfer100→70→35→10 gives one ordered trail from EastPath to WestGate; tread decoration does not encode movement.',
         direction,ordered_prints=prints,printed_controlled_track_rule=controlled,
         assumption='One uninterrupted walk; same wet-mud source, no fresh mud added, comparable ground and print pressure.')
    m=by_number[26]; ids=m['checkpoint']['case_numbers']; letters=[]; rooms=[]; valid=True
    for n in ids:
        case=runtime_cases[n]; solved=spatial_results[n]
        occupied=set(solved['solutions'][0].values()) if solved['status']=='PASS' else set()
        empty=[r for r in case['rooms'] if r['kind']=='room' and not occupied.intersection(r['cells'])]
        valid &= solved['status']=='PASS' and len(empty)==1
        if len(empty)==1:
            letters.append(empty[0]['final_name'][0].upper()); rooms.append({'case':n,'room':empty[0]['final_name'],'letter':letters[-1]})
    text=''.join(letters)
    emit(26,valid and len(ids)==14 and text=='CHECKTHEOLDMAP' and max(ids)<26
         and re.sub(r'\s+','',m['checkpoint']['answer'])==text,
         'Count occupants in each ROOM using independently solved placements, exclude ZONES, take the sole empty-room initial in ascending case order.',
         text,rooms=rooms,callbacks=ids,assumption='Reader was told to preserve each full placement; final ROOM/ZONE labels match the locked runtime.')
    m=by_number[27]; ov=m['map_overlay']; transforms=[]
    geometry_present=all(all(k in a for k in ('old_cell','current_cell')) for a in ov['anchors']) and bool(ov.get('old_room_cells')) and bool(ov.get('current_archive_wall_cells'))
    noncollinear=False; mapped=[]
    if geometry_present:
        old_points=[xy(a['old_cell']) for a in ov['anchors']]
        current_points=[xy(a['current_cell']) for a in ov['anchors']]
        if len(old_points)>=3:
            p,q,r=old_points[:3]
            noncollinear=(q[0]-p[0])*(r[1]-p[1]) != (q[1]-p[1])*(r[0]-p[0])
        matrices=[(1,0,0,1),(0,-1,1,0),(-1,0,0,-1),(0,1,-1,0),
                  (-1,0,0,1),(1,0,0,-1),(0,1,1,0),(0,-1,-1,0)]
        for a,b,c,d in matrices:
            x,y=old_points[0]; u,v=current_points[0]
            tx,ty=u-a*x-b*y,v-c*x-d*y
            transform=lambda p:(a*p[0]+b*p[1]+tx,c*p[0]+d*p[1]+ty)
            if all(transform(p)==q for p,q in zip(old_points,current_points)):
                transforms.append({'matrix':[a,b,c,d],'translation':[tx,ty]})
                mapped.append({transform(xy(cell)) for cell in ov['old_room_cells']})
    target={xy(cell) for cell in ov.get('current_archive_wall_cells',[])}
    emit(27,geometry_present and noncollinear and len(transforms)==1 and mapped==[target],
         'Three named non-collinear landmarks fix the alignment. Enumerated all eight square-grid rotations/reflections with translation fixed by the first anchor; exactly one maps all anchors and the old target onto the current Archive wall.' if geometry_present else
         'Named matching landmarks alone do not prove an alignment. Coordinate-based geometry and unique target overlap must be verified against the rendered plans.',
         ov['answer'],transforms=transforms,solution_count=len(transforms),noncollinear=noncollinear,
         geometry={k:ov.get(k) for k in ('grid','anchors','old_room_cells','current_archive_wall_cells','transform')},
         required='Rendered plan landmarks and wall/target cells must use these same source coordinates; no doorway may be drawn into the sealed footprint.')
    m=by_number[28]; fs=m['fact_theory_sort']; buckets={b:[] for b in ('FACT','THEORY','UNSUPPORTED ASSUMPTION')}
    for card in fs['cards']: buckets.setdefault(card['bucket'],[]).append(card['text'])
    definitions=fs.get('definitions',m.get('investigation_rules'))
    expected_buckets=[]
    for card in fs['cards']:
        text=card['text'].lower()
        if any(s in text for s in ('same plain 0','empty-room initials','old room sits')): expected='FACT'
        elif 'unfinished training system' in text: expected='THEORY'
        elif any(s in text for s in ('secretly watching','tunnel')): expected='UNSUPPORTED ASSUMPTION'
        else: raise ValueError(f'Unreviewed fact/theory statement: {card["text"]}')
        expected_buckets.append(expected==card['bucket'])
    rule_word=re.match(r'ZERO (\w+)\.',fs['rule_zero'])
    emit(28,len(buckets['FACT'])==3 and len(buckets['THEORY'])==1 and len(buckets['UNSUPPORTED ASSUMPTION'])==2
         and bool(definitions) and results[27]['status']=='PASS' and all(expected_buckets)
         and bool(rule_word) and rule_word[1]==fs['missing_word'],
         'Three claims repeat earned observations (zero marks, empty-room message, sealed-space match). Unfinished-training explanation remains possible, not proven. Watcher/tunnel claims have no observed support.',
         fs['missing_word'],classified=buckets,printed_definitions=definitions,
         assumption='Printed rubric distinguishes an evidence-linked tentative explanation from an unsupported assertion; Case27 observation must actually be earned.')
    m=by_number[30]; stages=m['finale']['stages']; expected={
        'RULE':by_number[28]['fact_theory_sort']['missing_word'],
        'ROOM':runtime_cases[29]['source_answer']['coordinate'],
        'CODE':by_number[5]['code']['answer'],'DETECTIVE':'READER-WRITTEN NAME'}
    valid=all(s['answer']==expected[s['id']] and (s['source_case']=='opening' or int(s['source_case'])<30) for s in stages)
    valid &= results[5]['status']=='PASS' and results[28]['status']=='PASS' and spatial_results[29]['status']=='PASS'
    emit(30,valid,'All four lock fields equal answers earned earlier: RuleZero word, boss coordinate, unique four-symbol code, and the reader’s one opening ID. Reader name is intentionally variable, not a fixed spelling puzzle.',
         expected,source_cases={s['id']:s['source_case'] for s in stages},
         assumption='Reader identity reveal depends on the invitation and NEXT DETECTIVE hook being shown before asking for identification; causal system explanation needs story QA.')
    return results


CALLBACKS = {
    1:'First five-case recap; Cases09/28 recurring-signal audit. Opening ID is reused in30.',
    3:'First five-case recap and Case28 evidence-versus-assumption lesson.',
    5:'First five-case recap; exact four-symbol order required by Case30 CODE stage.',
    8:'Route-checking practice; no new answer token required later.',
    9:'Case28 distinguishes the established recurring mark from its unproven cause.',
    11:'Old Academy context; photo observation must not be treated as proof of a watcher.',
    14:'Timing/memory lesson; no later lock consumes this witness name.',
    16:'Old Academy provenance and RULE0 FIRST seed Cases27–28 and the final reveal.',
    18:'Deliberate false lead:0:07 is NOT a required meta token.',
    21:'The empty-space instruction is required to motivate Case26.',
    24:'Observation practice; the tread motif adds context but no extra meta letter.',
    26:'CHECK THE OLD MAP is the explicit instruction driving Case27.',
    27:'The sealed-space observation becomes FACT in28; RULE FIRST, ROOM SECOND orders the finale.',
    28:'ASSUMPTIONS is required by Case30 RULE stage.',
    29:'D3 is required by Case30 ROOM stage; no extra empty-room letter.',
    30:'Book1 resolves; new incoming case belongs to Book2 and supplies no retroactive Book1 clue.',
}


def as_text(value):
    if isinstance(value,str): return value
    return json.dumps(value,ensure_ascii=False,sort_keys=True)


def readability(text):
    """Format internal audit prose only; do not mutate quoted publication content."""
    text=re.sub(r'\b(Case|Cases|Book|The|before|until|period|only|so|claimed|Enumerated|transfer|Rule)(?=\d)',r'\1 ',text)
    text=re.sub(r'(\d)(min)\b',r'\1 \2',text)
    return text.replace('EastPath','East Path').replace('WestGate','West Gate').replace('Book1','Book 1').replace('RuleZero','Rule Zero')


def self_test(runtime_cases):
    original=runtime_cases[2]
    baseline=enumerate_spatial(original)
    corrupt_answer=copy.deepcopy(original)
    corrupt_answer['characters'][0]['placement']='A1'
    rerun=enumerate_spatial(corrupt_answer)
    assert rerun['solutions']==baseline['solutions'] and not rerun['canonical_match'], 'Stored answer must not seed the search'
    blocked=copy.deepcopy(original)
    blocked['objects'].append({'cell':'B3','type':'test_block','blocked':True,'occupiable':False})
    assert enumerate_spatial(blocked)['solution_count']==0, 'A blocked exact-clue cell must be rejected'
    before={'symbols':['BALL','STAR','BOLT','HEART'],'clues':['BOLT comes immediately after STAR.',
            'BALL appears before HEART.','STAR is not first.','HEART is not third.']}
    assert len(code_solutions(before))==2, 'Historical alternate code must remain detectable'
    after=copy.deepcopy(before); after['clues'][-1]='HEART comes after BOLT.'
    assert code_solutions(after)==[['BALL','STAR','BOLT','HEART']]
    return ['Stored-placement corruption does not alter computed solutions and fails canonical equality.',
            'Blocking the exact B3 clue cell yields zero spatial solutions.',
            'Old four-symbol clues yield two codes; repaired clues yield exactly the intended one.']


def evidence_for(m):
    if m.get('spatial_source_id'): return m.get('spatial',m.get('spatial_copy',{})).get('clue_cards',m.get('spatial_copy',{}).get('clue_cards',[]))
    if m['number']==1:
        t=m['tutorial']; return t['clues']+[f"{r['name']}: {', '.join(r['cells'])}" for r in t['rooms']]
    key={'visual':'visual','code':'code','route':'route','classification':'classification',
         'consistency':'consistency','timeline-visual':'timeline_visual','timeline':'timeline',
         'reconstruction':'reconstruction','visual-sequence':'visual_sequence','room-zero-checkpoint':'checkpoint',
         'map-overlay':'map_overlay','fact-theory-sort':'fact_theory_sort','multi-stage-finale':'finale'}[m['type']]
    block=m[key]
    excluded={'answer','answer_order','answer_text','answer_coordinate','real','reason','reveal','reader_payoff','series_hook','missing_word'}
    return [f'{k}: {as_text(v)}' for k,v in block.items() if k not in excluded]


def write_ledger(path,data,runtime_cases,results,bindings):
    pending=[n for n,r in sorted(results.items()) if r['status']!='PASS']
    lines=['# HMDA Book 1 V3 — Case logic ledger','',
           'This ledger is generated from the declared publication input and the locked spatial runtime. '
           'It distinguishes exhaustive constraint proof from interpretive story/visual review. '
           'It does not certify rendered illustrations, page visibility, marker readability or physical print quality.','',
           f"Logic status: **{'PASS' if not pending else 'NEEDS WORK'}**. Remaining machine/editorial gaps: "
           +( ', '.join(f'{n:02d}' for n in pending) if pending else 'none in the encoded constraints')+'.','',
           '## Evidence and reproducibility','',
           'Run `python scripts/validate_book1_v3_logic.py --master dist/book1_en_master_owner_review_v3.yml '
           '--runtime dist/hmda_spatial_runtime_v3.json`. Use the actual final runtime path if different. '
           'The matching JSON report records solution counts, counterexamples, domains, constraints and input hashes.','',
           '```json',json.dumps(bindings,indent=2,ensure_ascii=False),'```','',
           'The15 spatial CSPs start with every usable floor/object square. Unary clues filter domains; '
           'binary clues, one-person-per-row/column, solo-room constraints, the bench companion and exactly '
           'one owner companion are enforced. AC-3 and finite backtracking exhaust the remaining assignments. '
           'Stored answer placements are consulted only after search. The source engine’s initial domains '
           'are not used to seed this solver.','',
           'Source-dependent rules: beside means an edge-sharing cell within the same space; diagonally next '
           'means one row and one column away; grid-step distance is Manhattan distance without routing around '
           'walls; cardinal offsets do not imply a shared row or column. Every witness belongs to one simultaneous '
           'snapshot. A not-beside-object clue also states that the room contains the object. '
           'These rules must be supplied to the child, not inferred from this internal ledger.','',
           '## Repairs and proof boundaries','',
           '- Case01 baseline had two complete placements. Its delivery witness was uniquely Dani, but the claimed '
           'Cole=A3 step was unjustified. An explicit row3/columnA clue repairs the full placement.',
           '- Case05 baseline allowed BALL–STAR–BOLT–HEART and BALL–HEART–STAR–BOLT. '
           'The explicit HEART-after-BOLT clue removes the second code without changing the intended answer.',
           '- Case21 baseline A→C tear did not match (curve-1 versus wave-4), giving zero edge-valid chains. '
           'Both physical edges must match; the answer list is not evidence.',
           '- Case08 requires a departure before the closure ends; Case11 must ask about the out-of-window '
           'timestamped record, not assert that an entire physical phone can never be evidence.',
           '- Case03 needs an explicit relevance rubric; Case27 needs measurable landmark/target geometry; '
           'Case28 needs an explicit categorization rubric. Their answer declarations alone are insufficient.',
           '- Naming/room display changes preserve source identities. A companion witness is not automatically '
           'the person responsible for moving an object: the incident must state that the recorded handover '
           'was to/from that companion, or the objective must only ask who shared the space.','',
           '## Case coverage','',
           '|Case|Type|Logic check|Unique answer evidence|', '|---|---|---|---|']
    for m in data['missions']:
        n=int(m['number']); r=results[n]
        proof=f"{r['solution_count']} placement(s), exhaustive={r['exhaustive']}" if n in SPATIAL else r.get('proof','')
        lines.append(f"|{n:02d}|{m['type']}|{r['status']}|{readability(proof.replace('|','/'))}|")
    lines=[readability(line) for line in lines]
    for m in data['missions']:
        n=int(m['number']); r=results[n]; case=runtime_cases.get(n)
        guides=[data.get('characters',{}).get(g,{}).get('name',g.upper()) for g in m.get('guides',[])]
        lines += ['',f"## Case {n:02d} — {m['title']}",'',f"- **Narrative setup:** {m['hook']}",
                  f"- **Objective:** {m['objective']}",f"- **Puzzle type:** {m['type']}.",
                  f"- **Happy Makers:** {', '.join(guides)}."]
        if case:
            aliases='; '.join(f"{i:02d} {p['source_name']} → {p['display_name']}" for i,p in enumerate(case['characters'],1))
            answer=case['source_answer']
            lines += [f'- **Witness identities / naming aliases:** {aliases}.',
                      '- **Rules:** One person in each row and each column; only declared occupiable cells; all clue '
                      'relations refer to this single snapshot. Exactly one other person shares the owner’s final space. '
                      'Full placement must be recorded for later reuse.',
                      f"- **Unique intended answer:** {answer['display_name']} at {answer['coordinate']} "
                      f"(locked source identity {answer['name']}).",
                      '- **Complete independently solved placement:** '+ '; '.join(f"{i:02d} {p['display_name']} — {p['placement']}" for i,p in enumerate(case['characters'],1))+'.',
                      f"- **Solvability evidence:** Exhaustive CSP found {r['solution_count']} complete assignment(s), "
                      f"canonical match={r['canonical_match']}, search nodes={r['nodes']}. No answer position was an input constraint.",
                      '- **Timing assumption:** All observations are simultaneous at the stated incident/record time; '
                      'no witness moves between clues. The named companion only answers the physical-incident question '
                      'when that incident’s handover/access link is explicit.']
            for field in ('source_page_asset','puzzle_asset','solution_asset'):
                asset=m.get('spatial',{}).get(field)
                if asset: lines.append(f'- **Visual asset ({field}):** `{asset}`.')
            if not m.get('spatial',{}).get('puzzle_asset'):
                lines.append(f"- **Visual assets:** `{case['id']}` locked puzzle and solution maps; numeric witness board; full placement key. Asset paths not yet attached to this input.")
        else:
            participants=m.get('tutorial',{}).get('people') or [x['speaker'] for x in m.get('consistency',{}).get('statements',[])]
            default_rules={
                1:'Each of the four people uses a different row and column; room cells are explicitly listed.',
                3:'Use the supplied evidence relevance rubric, not aesthetic preference; select exactly three changes.',
                5:'Use each of the four symbols once; satisfy every order constraint simultaneously.',
                8:'Depart at16:20; no waiting; closed corridor, locked door and wall cannot be crossed.',
                9:'Match the deliberate plain0 evidence mark; exclude decorative circles/pointers; do not infer its cause.',
                11:'Evaluate timestamped records A–D against the inclusive15:20–16:05 window; untimed personal items are not competing records.',
                14:'Only drawn connections are available; each edge takes at least2min; compare travel time to claimed elapsed time.',
                16:'Use the on-page official-event badge period and installed sticker date, not outside history.',
                18:'Real time equals displayed time minus the stated clock offset; then sort.',
                21:'Use every scrap exactly once, with the printed text upright; match physical edge types from straight left to straight right.',
                24:'One uninterrupted controlled-track walk; no new mud; deposited mud decreases after leaving the muddy patch.',
                26:'Use the fourteen listed earlier cases in order; find the sole empty ROOM, excluding all ZONES; take its initial.',
                27:'Use fixed named landmarks and the stated common scale; page edges are not alignment evidence.',
                28:'Classify using the three explicitly supplied evidence-support definitions; no invented watcher/tunnel fact.',
                30:'Use previously earned word, coordinate and code plus the chosen reader ID; introduce no new lock rule.'}[n]
            lines += [f"- **Unique intended answer:** {as_text(r.get('answer'))}",
                      '- **Other participants:** '+(', '.join(participants) if participants else 'No additional named solver/witness beyond the listed team is required.')+'.',
                      '- **Rules:** '+as_text(m.get('investigation_rules',readability(default_rules))),
                      f"- **Solvability evidence:** {readability(r['proof'])}",
                      f"- **Timing/rule assumption:** {r.get('assumption','Only the explicit finite options and evidence printed with the case may be used; no outside history or hidden clue.')}",
                      '- **Naming aliases:** Named nonspatial participants are taken from this publication case’s evidence; '
                      'no source-name substitution is used in the solver.',
                      '- **Visual assets:** '+{
                          1:'4×4 tutorial map and numeric witness key.',3:'paired evidence photographs with six controlled changes.',
                          5:'four symbol tiles and four writable lock positions.',8:'three route diagrams, barriers and departure clock.',
                          9:'recurring-mark evidence cards and decorative lookalikes.',11:'bag contents and legible timestamp labels.',
                          14:'complete node/edge route map and witness timing cards.',16:'old group photo, plaque, badge-period sheet and dated sticker.',
                          18:'four clock records with source labels.',21:'four torn scraps with matching physical edge profiles.',
                          24:'four visible prints with strictly decreasing mud intensity.',26:'fourteen prior completed maps plus the case index.',
                          27:'old/current plan layers with matching landmarks and a sealed target footprint.',
                          28:'six statement cards and three defined category zones.',30:'four final lock fields, reader ID and five badges plus one NEXT DETECTIVE hook.'}[n]]
            if 'solution_count' in r: lines.append(f"- **Enumerated solution count:** {r['solution_count']}.")
            if 'before_repair_solution_count' in r: lines.append(f"- **Baseline before repair:** {r['before_repair_solution_count']} valid complete solutions.")
        lines += ['','### Evidence given to the reader','']
        lines.extend(f'{i}. {as_text(e)}' for i,e in enumerate(evidence_for(m),1))
        lines += ['','### Deduction path','']
        lines.extend(f'{i}. {step}' for i,step in enumerate(m.get('solution_steps',[]),1))
        callback=readability(CALLBACKS.get(n,'Case26 revisits this map; the empty ROOM initial joins CHECK THE OLD MAP. Cases27–30 depend on that instruction.'))
        signal=m.get('signal_log',m.get('meta_reveal',''))
        lines += ['',f'- **Room Zero / meta signal:** {as_text(signal)}',f'- **Later callback / required reuse:** {callback}']
        if case and n != 29:
            lines += [f"- **Required hidden output:** Empty ROOM `{case['meta']['room']}` → `{case['meta']['letter']}`. "
                      'Its existence follows from the solved occupancy; it is not assumed by the solver.']
        lines += [f"- **Final QA status:** Logic **{r['status']}** for the bound inputs. Rendered visual evidence, "
                  'numeric marker clarity, clues-before-puzzle placement and page references require the separate V3 PDF audit.']
        if r['status']!='PASS': lines.append('- **Unresolved issue:** '+r.get('required',r.get('proof','See JSON counterexamples.')))
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--master',type=Path)
    ap.add_argument('--runtime',type=Path,default=ROOT/'dist/hmda_spatial_runtime_aliases.json')
    ap.add_argument('--report',type=Path,default=ROOT/'docs/HMDA_BOOK1_V3_LOGIC_REPORT.json')
    ap.add_argument('--ledger',type=Path,default=ROOT/'docs/HMDA_BOOK1_V3_LOGIC_LEDGER.md')
    ap.add_argument('--spatial-only',action='store_true')
    ap.add_argument('--self-test',action='store_true')
    args=ap.parse_args()
    runtime=json.loads(args.runtime.read_text(encoding='utf-8'))
    runtime_cases={int(c['id'].split('_')[1]):c for c in runtime['cases']}
    selection_path=ROOT/'content/spatial_source_manifest_final.yml'
    selection=read_yaml(selection_path)
    expected={c['id'] for c in selection['cases']}
    if {c['id'] for c in runtime['cases']}!=expected:
        raise ValueError('Runtime does not cover exactly the locked15 spatial cases')
    if any(c['provenance']['checkpoint_sha256']!=selection['source']['checkpoint_sha256'] for c in runtime['cases']):
        raise ValueError('Runtime checkpoint provenance differs from the locked source')
    results={n:enumerate_spatial(c) for n,c in runtime_cases.items()}
    bindings={'runtime':args.runtime.name,'runtime_sha256':hashlib.sha256(args.runtime.read_bytes()).hexdigest(),
              'selection_manifest_sha256':hashlib.sha256(selection_path.read_bytes()).hexdigest(),
              'checkpoint_sha256':selection['source']['checkpoint_sha256']}
    if not args.spatial_only:
        data=load_missions(args.master)
        if [int(m['number']) for m in data['missions']]!=list(range(1,31)):
            raise ValueError('Input must contain exactly30 ordered cases')
        inputs=[args.master] if args.master else [ROOT/f'content/book1_en_phase{i}.yml' for i in (1,2,3)]
        bindings['content']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
        results.update(nonspatial_checks(data['missions'],runtime_cases,results))
        write_ledger(args.ledger,data,runtime_cases,results,bindings)
    report={'scope':'Explicit locked-clue CSP and nonspatial finite checks; no PDF or visual QA',
            'bindings':bindings,'cases':dict(sorted(results.items()))}
    if args.self_test: report['self_tests']=self_test(runtime_cases)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    for n,r in sorted(results.items()):
        if n in SPATIAL:
            print(f'Case {n:02d}: {r["status"]}; solutions={r["solution_count"]}; exhaustive={r["exhaustive"]}; nodes={r["nodes"]}')
        else: print(f'Case {n:02d}: {r["status"]}; {r["proof"]}')
    return 0 if all(r['status']=='PASS' for r in results.values()) else 1


if __name__=='__main__':
    raise SystemExit(main())
