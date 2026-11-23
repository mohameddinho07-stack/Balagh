"""Narrow Supabase RPC client. No table access or service-role key."""
import json
import urllib.request
import urllib.error

class RoomError(Exception):
    pass


def rpc(url, key, op, token='', code='', payload=None):
    body = json.dumps(dict(op=op, token=token, code=code, payload=payload or {})).encode()
    req = urllib.request.Request(url.rstrip('/')+'/rest/v1/rpc/balagh_room', data=body,
          headers={'apikey': key, 'Content-Type':'application/json', 'User-Agent':'Balagh/0.2'})
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        try:
            message = json.load(exc).get('message', '')
        except (ValueError, OSError):
            message = ''
        if exc.code == 400 and message and len(message) < 180:
            raise RoomError(message) from None
        raise RoomError('الأوضة ما ردّتش. جرّب تحديث الأوضة، من غير ما تعمل أوضة جديدة.') from None
    except (OSError, ValueError):
        raise RoomError('الاتصال بالأوضة اتقطع. تحديث الأوضة بيرجع آخر حاجة اتحفظت.') from None
