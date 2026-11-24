import json,tempfile,unittest
import pgserver,psycopg2
from test_rooms_pg import SHIM
from night_store import DurableStore
from night import Game,GameError

class StorageSQL(unittest.TestCase):
 def test_sql_encrypted_restore_and_no_public_access(self):
  with tempfile.TemporaryDirectory() as d:
   srv=pgserver.get_server(d);conn=psycopg2.connect(srv.get_uri());conn.autocommit=True
   try:
    cur=conn.cursor();cur.execute('create role anon;create role authenticated;');cur.execute(SHIM)
    cur.execute(open('night_persistence.sql').read());cur.execute(open('night_persistence.sql').read())
    def rpc(b):
     cur.execute('select public.balagh_night_store(%s,%s,%s,%s,%s)',(b['op'],b['code'],b['capability'],b.get('expected',0),b.get('snapshot','')))
     return cur.fetchone()[0]
    store=DurableStore('x','x','local-test-encryption-master-'*4,transport=rpc,clock=lambda:0)
    g=Game(seed=12,clock=lambda:0);tokens=[g.join(x) for x in ['a','b','c','d']]
    store.save('ABCDEF1234',g,0,True);store.act('ABCDEF1234',tokens[0],'start')
    for t in tokens:self.assertEqual(store.read('ABCDEF1234',t)['me'],g._by_token(t)['name'])
    cur.execute('set role anon')
    with self.assertRaises(psycopg2.errors.InsufficientPrivilege):cur.execute('select * from public.balagh_night_snapshots')
    self.assertFalse(rpc(dict(op='read',code='ABCDEF1234',capability='0'*64))['found'])
    self.assertFalse(rpc(dict(op='commit',code='ABCDEF1234',capability='0'*64,snapshot='x'*150,expected=2))['found'])
    cur.execute('reset role')
   finally:conn.close();srv.cleanup()
