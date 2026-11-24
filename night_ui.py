"""قاتل وظابط مباحث: screens. Hidden lab mode, opened only with ?lab=killer.

Roles and truth live only in server memory (night.Game). A browser gets rendered
widgets for its own player, built from Game.view(token). Nothing here reads
another player's role, cards or the night truth.
"""
import secrets
import time

import streamlit as st
from night import Game, GameError, PLACES, ROLE_KILLER
from night_store import DurableStore


def _store():
    try:
        return DurableStore(st.secrets['SUPABASE_URL'], st.secrets['SUPABASE_KEY'], st.secrets['NIGHT_MASTER_SECRET'])
    except (KeyError, FileNotFoundError):
        raise GameError('حفظ الليلة لسه بيتجهز. جرّب بعدين.') from None


def _new_room(name):
    game = Game(clock=time.time)
    token = game.join(name)
    code = secrets.token_hex(5).upper()
    _store().save(code, game, 0, create=True)
    return code, token


def _join(code, name):
    code = (code or '').strip().upper()
    store = _store()
    game, revision = store.load(code)
    token = game.join(name)
    store.save(code, game, revision)
    return code, token


def _act(op, payload=None):
    return _store().act(st.session_state['night_code'], st.session_state['night_token'], op, payload)


def _view():
    return _store().read(st.session_state['night_code'], st.session_state['night_token'])


def _try(op, payload=None):
    try:
        _act(op, payload)
    except GameError as e:
        st.session_state['night_msg'] = str(e)
    st.rerun()


def _card(c):
    if c['kind'] == 'link':
        if c.get('a') and c.get('b'):
            return 'ربط · الكارت %s والكارت %s من نفس الساعة' % (c['a'], c['b'])
        return 'ربط · كارت من كروتك مربوط بكارت تاني من نفس الساعة. لما تحطه هيظهر الاتنين.'
    who = (c['owner'] + ' · ') if c.get('owner') else ''
    seen = ('شاف: ' + '، '.join(c['seen'])) if c['seen'] else 'ما شافش حد'
    kind = 'شهادة' if c['kind'] == 'testimony' else 'أثر'
    hour = 'ساعة مخبية (محتاجة كارت ربط)' if c.get('masked') else 'الساعة ' + c['slot']
    fake = '  ❌ اتكشف إنه مزوّر' if c.get('refuted') else ''
    return '%s%s · %s · في %s · %s%s' % (who, kind, hour, c['place'], seen, fake)


def _entry():
    st.title('قاتل وظابط مباحث')
    st.caption('لعبة قعدة لـ 4 لحد 7 صحاب في نفس المكان. الأدوار بتتوزع لوحدها وسري. كل واحد بيشوف شاشته بس.')
    with st.form('night_entry'):
        name = st.text_input('اسمك', max_chars=30, key='night_name')
        code = st.text_input('كود الأوضة (لو داخل عند صحابك)', key='night_codein')
        c1, c2 = st.columns(2)
        create = c1.form_submit_button('اعمل أوضة', type='primary')
        join = c2.form_submit_button('ادخل الأوضة')
        restore = st.form_submit_button('ارجع لليلتي')
        return_key = st.text_input('مفتاح رجوعك الشخصي', type='password', key='night_returnin')
    try:
        if restore:
            code = code.strip().upper()
            _store().read(code, return_key)
            st.session_state['night_code'], st.session_state['night_token'] = code, return_key
            st.rerun()
        elif create:
            st.session_state['night_code'], st.session_state['night_token'] = _new_room(name)
            st.rerun()
        elif join:
            st.session_state['night_code'], st.session_state['night_token'] = _join(code, name)
            st.rerun()
    except GameError as e:
        st.warning(str(e))


@st.fragment(run_every=4)
def _room():
    try:
        v = _view()
    except GameError as e:
        st.warning(str(e))
        return
    if v is None:
        st.warning('الأوضة خلصت أو اتقفلت.')
        if st.button('رجوع', key='night_back'):
            for k in ('night_code', 'night_token'):
                st.session_state.pop(k, None)
            st.rerun()
        return
    st.caption('كود الأوضة: ' + st.session_state['night_code'] + ' | إنت: ' + v['me'])
    if st.session_state.get('night_msg'):
        st.warning(st.session_state.pop('night_msg'))
    with st.expander('احفظ مفتاح رجوعك قبل ما تقفل'):
        st.caption('المفتاح شخصي وسري، اللي معاه المفتاح والكود يشوف دورك. احفظهم بعيد عن الجروب. الحفظ بيستمر لو التطبيق نام أو اتفتح من جديد.')
        st.code(st.session_state['night_token'], language=None)
    ph = v['phase']
    if ph == 'lobby':
        st.subheader('الصحاب اللي دخلوا (' + str(len(v['players'])) + '/7)')
        st.write('، '.join(v['players']))
        if v['host']:
            st.caption('ابدأ لما كله يدخل. الأدوار هتتوزع وسري.')
            if st.button('ابدأ الليلة', type='primary', key='night_start'):
                _try('start')
        else:
            st.info('مستنيين اللي عمل الأوضة يبدأ.')
        return
    role = v['role']
    if ph != 'ended':
        st.markdown('### دورك: **' + role + '**')
        st.caption('ما تورّيش شاشتك لحد.' + ('' if role != ROLE_KILLER else ' إنت اللي عملتها. اتصرف كأنك بريء.'))
    if v['murder_slot'] and ph == 'ended':
        st.write('الجريمة: النور قطع الساعة ' + str(v['murder_slot']) + ' في ' + str(v['scene']) + '.')
    else:
        st.write('الجريمة: النور قطع في ' + str(v['scene']) + '، بس محدش عارف الساعة كام بالظبط (٩ ولا ١٠ ولا ١١). استنتجوها من الكروت.')
        if v.get('private') and v['private'].get('murder_slot'):
            st.markdown('**الساعة الحقيقية (إنت بس اللي عارفها):** ' + str(v['private']['murder_slot']))
    if v.get('private'):
        st.markdown('**مكانك في الليلة (إنت بس اللي عارفه):** ' +
                    ' | '.join('%s: %s' % (s, p) for s, p in zip(['٩', '١٠', '١١'], v['private']['my_places'])))
        if role == ROLE_KILLER:
            st.caption('تزوير كارت: ' + ('باقيلك مرة واحدة للّيلة دي (اختار "تبوّظ أثر" وقت التفتيش)، وفيه دايماً دليل حقيقي بيكشفه.' if v['private']['forge_left'] else 'خلص، استخدمته.'))
        if v['private']['partners']:
            st.markdown('**شريكك:** ' + '، '.join(v['private']['partners']))
    if ph == 'alibi':
        if role == ROLE_KILLER and not v['i_submitted']:
            st.subheader('قول كنت فين وقت القتل')
            for p in PLACES:
                if st.button(p, key='night_alibi_' + p):
                    _try('alibi', dict(place=p))
        else:
            st.info('كل واحد بيجهّز كلامه. استنى.')
    elif ph == 'search':
        st.subheader('الجولة ' + str(v['round']) + ': فتّش في مكان')
        if v['i_submitted']:
            st.info('اتسجل اختيارك. استنى الباقيين (' + str(v['submitted_count']) + '/' + str(len(v['players'])) + ').')
        else:
            spot = st.radio('هتفتّش فين؟', PLACES, key='night_spot_%d' % v['round'], horizontal=True)
            spoil = None
            if role == ROLE_KILLER:
                spoil = st.radio('وتبوّظ أثر فين؟ (سري)', PLACES, key='night_spoil_%d' % v['round'], horizontal=True)
            if st.button('ثبّت اختياري', type='primary', key='night_search_%d' % v['round']):
                payload = dict(spot=spot)
                if role == ROLE_KILLER:
                    payload['spoil'] = spoil
                _try('search', payload)
    elif ph == 'talk':
        st.subheader('الجولة ' + str(v['round']) + ': اتكلموا بصوتكم')
        st.caption('المحاولات الباقية: ' + str(v['chances']))
        if v['statements']:
            st.markdown('**كل واحد قال كان فين (٩ / ١٠ / ١١):**')
            for n, route in v['statements'].items():
                st.write('• %s: %s' % (n, ' ← '.join(route)))
            st.caption('واحد بس كدب في ساعة واحدة. الكروت هي اللي بتكشف مين.')
        st.markdown('**كروتك (سرية لحد ما تحطها):**')
        shown = {c['id'] for c in v['board']}
        for c in v['my_cards']:
            cols = st.columns([4, 1])
            cols[0].write(_card(dict(c, owner=None)) + ('  ✅ على الترابيزة' if c['id'] in shown else ''))
            if c['id'] not in shown and cols[1].button('حطه', key='night_pub_' + c['id']):
                _try('publish', dict(card=c['id']))
        st.markdown('**الترابيزة:**')
        for c in v['board']:
            st.write('• ' + c['id'] + ' · ' + _card(c))
        pr = v['proposal']
        if pr:
            st.warning('اتهام مطروح: ' + pr['suspect'] + ' | موافقين: ' + '، '.join(pr['approvals']))
            if v['me'] != pr['suspect'] and v['me'] not in pr['approvals']:
                if st.button('أوافق على الاتهام', key='night_approve'):
                    _try('approve', dict(suspect=pr['suspect'], cards=pr['cards']))
        elif len(v['board']) >= 2:
            sus = st.selectbox('مين المتهم؟', [n for n in v['players'] if n != v['me']], key='night_sus')
            ids = st.multiselect('كارتين من الترابيزة بيكذّبوا كلامه (الكارت لازم ساعته تكون معروفة)', [c['id'] for c in v['board'] if c['kind'] != 'link'], max_selections=2, key='night_ids')
            if st.button('اطرح الاتهام', key='night_propose') and len(ids) == 2:
                _try('propose', dict(suspect=sus, cards=ids))
        if len(v['board']) >= 2:
            with st.expander('كارتين شكلهم متناقضين؟ واجهوهم'):
                st.caption('لو كارت بيقول إن حد كان في مكان وشهادة الشخص نفسه بتقول مكان تاني، واحد منهم مزوّر. الكارت المزوّر بيتسحب ومينفعش يتستخدم في اتهام.')
                cids = st.multiselect('كارتين من الترابيزة', [c['id'] for c in v['board'] if c['kind'] != 'link'], max_selections=2, key='night_cids')
                if st.button('واجه الكارتين', key='night_challenge') and len(cids) == 2:
                    _try('challenge', dict(cards=cids))
        if v['seconds_left'] is not None:
            st.caption('الوقت الباقي: ' + str(v['seconds_left']) + ' ثانية')
        if v['host'] and st.button('خلّصوا الجولة', key='night_next'):
            _try('next')
    if ph == 'ended':
        res = v['result']
        st.subheader('خلصت الليلة: ' + res['winner'] + ' كسب')
        st.write(res['why'] + '. القاتل كان: ' + '، '.join(res['killers']) + '. الجريمة كانت الساعة ' + str(res['truth']['m']) + ' في ' + str(res['truth']['scene']) + '.')
    if v['log']:
        with st.expander('اللي حصل'):
            for line in v['log']:
                st.write('• ' + line)


def run():
    if st.session_state.get('night_code') and st.session_state.get('night_token'):
        _room()
    else:
        _entry()
