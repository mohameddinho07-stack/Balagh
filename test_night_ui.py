"""UI-level secrecy: four real Streamlit sessions share one server store."""
import unittest
from streamlit.testing.v1 import AppTest

ROLE_K = 'قاتل'


def page_text(at):
    parts = []
    for group in (at.markdown, at.caption, at.subheader, at.title, at.text, at.warning, at.info, at.success, at.error):
        parts += [str(e.value) for e in group]
    parts += [str(b.label) for b in at.button] + [str(r.label) for r in at.radio]
    parts += [str(o) for r in at.radio for o in r.options]
    return '\n'.join(parts)


def fresh():
    at = AppTest.from_file('app.py', default_timeout=30)
    at.query_params['lab'] = 'killer'
    return at.run()


class NightUI(unittest.TestCase):
    def test_roles_private_per_session(self):
        host = fresh()
        host.text_input(key='night_name').set_value('محمد').run()
        host.button(key='night_create').click().run()
        code = host.session_state['night_code']
        others = []
        for n in ['سارة', 'أحمد', 'كريم']:
            a = fresh()
            a.text_input(key='night_name').set_value(n).run()
            a.text_input(key='night_codein').set_value(code).run()
            a.button(key='night_joinbtn').click().run()
            others.append(a)
        host.run()
        host.button(key='night_start').click().run()
        self.assertEqual(len(host.exception), 0, [e.value for e in host.exception])
        sessions = [host] + others
        for s in sessions:
            s.run()
        for s in sessions:
            self.assertEqual(len(s.exception), 0, [e.value for e in s.exception])
        texts = [page_text(s) for s in sessions]
        killers = [i for i, t in enumerate(texts) if 'دورك: ' + ROLE_K in t or 'دورك: **' + ROLE_K in t]
        self.assertEqual(len(killers), 1, texts)
        for i, t in enumerate(texts):
            if i != killers[0]:
                self.assertNotIn(ROLE_K, t.replace('ظابط مباحث', ''), 'a cop screen mentions the killer role')
                self.assertNotIn(sessions[killers[0]].session_state['night_token'], t)
        # the killer's name never appears as such on a cop screen before the end
        kname = [n for n in ['محمد', 'سارة', 'أحمد', 'كريم']][killers[0]]
        for i, t in enumerate(texts):
            if i != killers[0]:
                self.assertNotIn('القاتل كان', t)


if __name__ == '__main__':
    unittest.main()
