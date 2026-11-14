"""Medidor de cobertura de sentencias y ramas basado en sys.settrace.

Uso: python tools/cobertura.py . src/rescatebot/reglas.py,src/rescatebot/__init__.py,src/rescatebot/db.py
Alternativa estándar: coverage run --branch -m pytest && coverage report -m
"""
import ast, sys, os, json, threading
ROOT=os.path.abspath(sys.argv[1]); TARGETS=[os.path.join(ROOT,p) for p in sys.argv[2].split(',')]
executed={t:set() for t in TARGETS}; arcs={t:set() for t in TARGETS}
def tracer(frame,event,arg):
    f=os.path.abspath(frame.f_code.co_filename)
    if f not in executed: return None
    last=[None]
    def local(fr,ev,a):
        if ev=='line':
            executed[f].add(fr.f_lineno)
            if last[0] is not None: arcs[f].add((last[0],fr.f_lineno))
            last[0]=fr.f_lineno
        elif ev=='return':
            if last[0] is not None: arcs[f].add((last[0],-1))
        return local
    return local
sys.path.insert(0,os.path.join(ROOT,'src')); sys.path.insert(0,os.path.join(ROOT,'tests'))
os.chdir(ROOT)
import pytest
sys.settrace(tracer); threading.settrace(tracer)
rc=pytest.main(['-q','-p','no:cacheprovider'])
sys.settrace(None)
def code_lines(co,acc):
    for _,_,l in co.co_lines():
        if l: acc.add(l)
    for c in co.co_consts:
        if hasattr(c,'co_lines'): code_lines(c,acc)
res={}
for t in TARGETS:
    src=open(t,encoding='utf-8').read(); tree=ast.parse(src)
    stm=set()
    for node in ast.walk(tree):
        if isinstance(node,ast.stmt) and not isinstance(node,(ast.FunctionDef,ast.ClassDef,ast.Import,ast.ImportFrom)) or isinstance(node,(ast.Import,ast.ImportFrom)):
            if isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str): continue
            stm.add(node.lineno)
        if isinstance(node,(ast.FunctionDef,)): stm.add(node.lineno)
    miss=sorted(stm-executed[t])
    br_tot=0; br_hit=0; br_miss=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.If,ast.While)):
            L=node.lineno; B=node.body[0].lineno
            outs={b for (a,b) in arcs[t] if a==L}
            br_tot+=2
            if B in outs: br_hit+=1
            else: br_miss.append(f'{L}->{B}')
            if any(b!=B for b in outs): br_hit+=1
            else: br_miss.append(f'{L}->salida')
    rel=os.path.relpath(t,ROOT)
    res[rel]=dict(stmts=len(stm),miss=len(miss),missing=miss,branches=br_tot,partial=br_tot-br_hit,br_missing=br_miss)
tot_s=sum(r['stmts'] for r in res.values()); tot_m=sum(r['miss'] for r in res.values()); tb=sum(r['branches'] for r in res.values()); tp=sum(r['partial'] for r in res.values())
print('\nName                              Stmts   Miss Branch BrMiss  Cover   Missing')
print('-'*92)
for k,r in res.items():
    cov=100*((r['stmts']-r['miss'])+(r['branches']-r['partial']))/max(1,r['stmts']+r['branches'])
    mis=', '.join(list(map(str,r['missing']))+r['br_missing'])
    print(f"{k:<33} {r['stmts']:>5} {r['miss']:>6} {r['branches']:>6} {r['partial']:>6} {cov:>6.1f}%   {mis[:60]}")
cov=100*((tot_s-tot_m)+(tb-tp))/max(1,tot_s+tb)
print('-'*92); print(f"{'TOTAL':<33} {tot_s:>5} {tot_m:>6} {tb:>6} {tp:>6} {cov:>6.1f}%")
json.dump(res,open('/tmp/cov.json','w'),indent=1)
sys.exit(rc)
