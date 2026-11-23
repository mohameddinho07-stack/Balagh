import sys,toml,concurrent.futures,json

from room_client import rpc,RoomError
import os
if not os.environ.get('BALAGH_LIVE_TEST_CONFIG'):
 raise __import__('unittest').SkipTest('Set BALAGH_LIVE_TEST_CONFIG for opt-in integration tests')
c=toml.load(os.environ['BALAGH_LIVE_TEST_CONFIG'])
def call(op,t='',**p):return rpc(c['SUPABASE_URL'],c['SUPABASE_KEY'],op,token=t,payload=p.pop('payload',p),code=p.pop('code',''))
def fail(op,t='',**p):
 try:call(op,t,**p)
 except RoomError:return
 raise AssertionError('should reject '+op)
def pair():
 a=call('create',name='سباق اختبار أ',mode='race');fail('inspect',a['token'],evidence='E06')
 b=rpc(c['SUPABASE_URL'],c['SUPABASE_KEY'],'join',code=a['code'],payload={'name':'سباق اختبار ب'})
 return a,b
# Basic private progress, forged writes, gated questions and evidence validation.
a,b=pair();ta,tb=a['token'],b['token']
fail('commit',ta,state={'finished':True},revision=0);fail('interview',ta,suspect='nadine',topic='n2');fail('inspect',ta,evidence='FAKE')
for e in ['E06','E07','E08']:call('inspect',ta,evidence=e)
call('interview',ta,suspect='nadine',topic='n2');call('notes',ta,notes='PRIVATE A')
sb=call('read',tb);assert sb['state']['discovered']==[] and sb['state']['interviews']==[] and sb['notes']=='' and 'PRIVATE A' not in json.dumps(sb)
fail('accuse',tb,suspect='نادين مراد',evidence=['E06','E07','E08'])
call('inspect',tb,evidence='E01');lost=call('accuse',tb,suspect='نادين مراد',evidence=['E01']);assert lost['winner'] is None and lost['state']['finished']
fail('accuse',tb,suspect='نادين مراد',evidence=['E01']);fail('inspect',tb,evidence='E06')
win=call('accuse',ta,suspect='نادين مراد',evidence=['E06','E07','E08']);assert win['winner']==a['me']
assert call('read',tb)['winner']==a['me'];fail('accuse',ta,suspect='نادين مراد',evidence=['E06','E07','E08'])
# Both wrong, no winner.
a,b=pair()
for x in [a,b]:call('inspect',x['token'],evidence='E01');z=call('accuse',x['token'],suspect='آسر منصور',evidence=['E01'])
assert z['status']=='finished' and z['winner'] is None
# Concurrent valid submissions: exactly one succeeds under row lock.
a,b=pair()
for x in [a,b]:
 for e in ['E06','E07','E08']:call('inspect',x['token'],evidence=e)
def submit(x):
 try:return call('accuse',x['token'],suspect='نادين مراد',evidence=['E06','E07','E08'])['winner']
 except RoomError:return None
with concurrent.futures.ThreadPoolExecutor(2) as pool:r=list(pool.map(submit,[a,b]))
assert sum(x is not None for x in r)==1
assert call('read',a['token'])['winner']==call('read',b['token'])['winner']
print('PASS: waiting gate, private state/history/notes, no arbitrary commits, evidence gates, one attempt, wrong allows other, both wrong, atomic race winner')
