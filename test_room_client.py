import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from room_client import rpc, RoomError

class RoomClientTests(unittest.TestCase):
    def test_scoped_rpc_request(self):
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        with patch('urllib.request.urlopen', return_value=Response(b'{"revision": 3}')) as send:
            self.assertEqual(rpc('https://example.invalid','key','read','token'),{'revision':3})
            req=send.call_args.args[0]
            self.assertTrue(req.full_url.endswith('/rpc/balagh_room'))
            self.assertEqual(json.loads(req.data)['token'],'token')
            self.assertNotIn('service_role',str(req.headers))

    def test_error_is_not_success(self):
        with patch('urllib.request.urlopen',side_effect=OSError('offline')):
            with self.assertRaises(RoomError):rpc('https://example.invalid','key','read')
        err=HTTPError('https://example.invalid',400,'bad',{},io.BytesIO(json.dumps({'message':'conflict'}).encode()))
        with patch('urllib.request.urlopen',side_effect=err):
            with self.assertRaisesRegex(RoomError,'conflict'):rpc('https://example.invalid','key','commit')
