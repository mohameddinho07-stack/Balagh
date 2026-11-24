import copy
import json
import unittest
from night import Game, GameError
from night_store import DurableStore, pack, unpack

class MemoryRPC:
    def __init__(self): self.rows={}
    def __call__(self,b):
        r=self.rows.get(b['code'])
        if b['op']=='create':
            if r:return {'ok':False}
            self.rows[b['code']]=dict(cap=b['capability'],revision=1,snapshot=b['snapshot'])
            return {'ok':True,'revision':1}
        if not r or r['cap']!=b['capability']:return {'found':False}
        if b['op']=='read':return dict(found=True,revision=r['revision'],snapshot=r['snapshot'])
        if b['expected']!=r['revision']:return {'ok':False}
        r.update(revision=r['revision']+1,snapshot=b['snapshot'])
        return dict(ok=True,revision=r['revision'])

class Persistence(unittest.TestCase):
    def test_restore_every_phase_and_conflict(self):
        rpc=MemoryRPC();master='test-secret-not-a-production-key-'*3
        store=DurableStore('x','x',master,transport=rpc,clock=lambda:0)
        g=Game(seed=8,clock=lambda:0);tokens=[g.join(n) for n in ['a','b','c','d']]
        code='ABCDEF1234';store.save(code,g,0,True)
        for t in tokens:self.assertEqual(store.read(code,t),g.view(t))
        store.act(code,tokens[0],'start');g,_=store.load(code)
        for t in tokens:self.assertEqual(store.read(code,t),g.view(t))
        self.assertNotIn('killers',rpc.rows[code]['snapshot'])
        self.assertNotIn(tokens[0],rpc.rows[code]['snapshot'])
        with self.assertRaises(GameError):store.read(code,'x'*64)
        old,rev=store.load(code);store.save(code,old,rev)
        with self.assertRaises(GameError):store.save(code,old,rev)
        wrong=DurableStore('x','x','wrong'*20,transport=rpc)
        with self.assertRaises(GameError):wrong.load(code)
        # Serializing then restoring must preserve RNG, tuple-key proposal guard,
        # truth and token hashes, but never rely on pickle or executable data.
        g.proposed[('a',1)]=True
        h=unpack(pack(g),clock=lambda:0)
        self.assertEqual(h.proposed,g.proposed)
        self.assertEqual(h.rng.random(),g.rng.random())
        self.assertEqual(h.view(tokens[1]),g.view(tokens[1]))

if __name__=='__main__':unittest.main()
