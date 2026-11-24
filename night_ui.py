"""قاتل وظابط مباحث: screens. Hidden lab mode, opened only with ?lab=killer.

Roles and truth live only in server memory (night.Game). A browser gets rendered
widgets for its own player, built from Game.view(token). Nothing here reads
another player's role, cards or the night truth.
"""
import secrets
import threading
import time

import streamlit as st

from night import Game, GameError, PLACES, ROLE_KILLER

_MAX_ROOMS = 40
_TTL = 6 * 3600


@st.cache_resource
def _store():
    return dict(rooms={}, lock=threading.Lock())


def _new_room(name):
    s = _store()
    with s['lock']:
        now = time.time()
        for code in [c for c, r in s['rooms'].items() if now - r['at'] > _TTL]:
            s['rooms'].pop(code, None)
        if len(s['rooms']) >= _MAX_ROOMS:
            raise GameError('الأوضات كتير دلوقتي. جرّب كمان شوية.')
        code = secrets.token_hex(3).upper()
        game = Game(clock=time.time)
        token = game.join(name)
        s['rooms'][code] = dict(game=game, at=now, lock=threading.Lock())
    return code, token


def _join(code, name):
    s = _store()
    code = (code or '').strip().upper()
    room = s['rooms'].get(code)
    if not room:
        raise GameError('الكود ده مش موجود')
    with room['lock']:
        token = room['game'].join(name)
    return code, token


def _act(op, payload=None):
    room = _store()['rooms'].get(st.session_state.get('night_code'))
    if not room:
        raise GameError('الأوضة خلصت أو اتقفلت')
    with room['lock']:
        room['at'] = time.time()
        game, token = room['game'], st.session_state['night_token']
        if op == 'start':
            game.start(token)
            return game.view(token)
        return game.act(token, op, payload)


def _view():
    room = _store()['rooms'].get(st.session_state.get('night_code'))
    if not room:
        return None
    with room['lock']:
        return room['game'].view(st.session_state['night_token'])


def _try(op, payload=None):
    try:
        _act(op, payload)
    except GameError as e:
        st.session_state['night_msg'] = str(e)
    st.rerun()


def _card(c):
    who = (c['owner'] + ' · ') if c.get('owner') else ''
    seen = ('شاف: ' + '، '.join(c['seen'])) if c['seen'] else 'ما شافش حد'
    kind = 'شهادة' if c['kind'] == 'testimony' else 'أثر'
    return '%s%s · الساعة %s · في %s · %s' % (who, kind, c['slot'], c['place'], seen)


def _entry():
    st.title('قاتل وظابط مباحث')
    st.caption('لعبة قعدة لـ 4 لحد 7 صحاب في نفس المكان. الأدوار بتتوزع لوحدها وسري. كل واحد بيشوف شاشته بس.')
    name = st.text_input('اسمك', max_chars=30, key='night_name')
    c1, c2 = st.columns(2)
    if c1.button('اعمل أوضة', type='primary', key='night_create'):
        try:
            st.session_state['night_code'], st.session_state['night_token'] = _new_room(name)
            st.rerun()
        except GameError as e:
            st.warning(str(e))
    code = st.text_input('كود الأوضة (لو داخل عند صحابك)', key='night_codein')
    if c2.button('ادخل الأوضة', key='night_joinbtn'):
        try:
            st.session_state['night_code'], st.session_state['night_token'] = _join(code, name)
            st.rerun()
        except GameError as e:
            st.warning(str(e))


@st.fragment(run_every=4)
def _room():
    v = _view()
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
    st.write('الجريمة: النور قطع الساعة ' + str(v['murder_slot']) + ' في ' + str(v['scene']) + '.')
    if v.get('private'):
        st.markdown('**مكانك في الليلة (إنت بس اللي عارفه):** ' +
                    ' | '.join('%s: %s' % (s, p) for s, p in zip(['٩', '١٠', '١١'], v['private']['my_places'])))
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
            st.markdown('**كل واحد قال كان فين وقت القتل:** ' + ' | '.join('%s: %s' % (n, p) for n, p in v['statements'].items()))
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
            ids = st.multiselect('كارتين من الترابيزة بيكذّبوا كلامه', [c['id'] for c in v['board']], max_selections=2, key='night_ids')
            if st.button('اطرح الاتهام', key='night_propose') and len(ids) == 2:
                _try('propose', dict(suspect=sus, cards=ids))
        if v['seconds_left'] is not None:
            st.caption('الوقت الباقي: ' + str(v['seconds_left']) + ' ثانية')
        if v['host'] and st.button('خلّصوا الجولة', key='night_next'):
            _try('next')
    if ph == 'ended':
        res = v['result']
        st.subheader('خلصت الليلة: ' + res['winner'] + ' كسب')
        st.write(res['why'] + '. القاتل كان: ' + '، '.join(res['killers']))
    if v['log']:
        with st.expander('اللي حصل'):
            for line in v['log']:
                st.write('• ' + line)


def run():
    if st.session_state.get('night_code') and st.session_state.get('night_token'):
        _room()
    else:
        _entry()
