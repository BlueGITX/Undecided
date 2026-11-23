"""
MindLend — end-to-end user test (Playwright, Python).
Runs every user flow by clicking and typing like a user, on a phone and a desktop viewport.

  pip install playwright && playwright install chromium
  python -m http.server 8765            # from the project root
  python tests/e2e.py http://localhost:8765/html/index.html
"""
import re, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8765/html/index.html'
FAILS, PASSES = [], [0]


def check(cond, msg):
    if cond:
        PASSES[0] += 1
    else:
        FAILS.append(msg)
        print('   ✗', msg)


def run(viewport, label):
    print(f'\n=== {label} {viewport} ===')
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport=viewport)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
        pg.on('console', lambda m: m.type == 'error' and 'fonts.g' not in m.text and 'ERR_TUNNEL' not in m.text and errs.append('console: ' + m.text))
        desktop = viewport['width'] >= 900

        sc = lambda: pg.evaluate('S.sc')
        ov = lambda: pg.evaluate('S.ov && S.ov.k')
        err = lambda: (pg.locator('#v .er').all_inner_texts() or [''])[0]
        def c(sel, i=0):
            pg.locator(sel).nth(i).click()
            pg.wait_for_timeout(60)
        def t(text, i=0):
            pg.get_by_text(text, exact=True).nth(i).click()
            pg.wait_for_timeout(60)
        def fill(m, v):
            pg.fill(f'[data-m="{m}"]', v)
        def tab(k):
            c(f'#sb [data-a=tab][data-k={k}]' if desktop else f'.tb [data-a=tab][data-k={k}]')
        def refresh():
            pg.reload()
            pg.wait_for_timeout(250)
        def toast_text():
            return ' '.join(pg.locator('.tt').all_inner_texts())

        # ---------- 1. Fresh visit: splash → onboarding → welcome
        print(' 1 fresh visit / onboarding')
        pg.goto(URL); pg.wait_for_timeout(200)
        check(sc() == 'splash', 'fresh visit starts at splash')
        pg.wait_for_timeout(4000); check(sc() == 'splash2', 'splash → splash2')
        pg.wait_for_timeout(3000); check(sc() == 'ob', 'splash2 → onboarding')
        refresh(); check(sc() == 'ob', 'refresh on onboarding stays on onboarding')
        t('Next →'); check(pg.evaluate('S.arg.i') == 1, 'onboarding page 2')
        t('Next →'); t('Get Started'); check(sc() == 'welcome', 'Get Started → Welcome')
        refresh(); check(sc() == 'welcome', 'refresh on Welcome stays (no splash)')
        check(pg.get_by_text('Create an account →').is_visible() and pg.get_by_text('I have already an account').is_visible(), 'Welcome shows sign up + sign in')

        # ---------- 2. Sign up validation
        print(' 2 sign up')
        t('Create an account →'); check(sc() == 'signup', 'open Sign Up')
        c('[data-a=signup]'); check('username' in err().lower(), 'empty sign up → error')
        fill('un', 'ana'); fill('em', 'bad-email'); c('[data-a=signup]'); check('valid email' in err(), 'bad email → error')
        fill('em', 'Ana@Test.com'); c('[data-a=signup]'); check('Terms' in err(), 'terms required')
        c('[data-a=terms]'); fill('pw1', 'short'); fill('pw2', 'short'); c('[data-a=signup]'); check('Weak' in err(), 'weak password → error')
        fill('pw1', 'Password1'); fill('pw2', 'password1'); c('[data-a=signup]'); check('Weak' in err(), 'case-different confirm password is rejected')
        c('[data-a=eye][data-k=pw1]'); check(pg.get_attribute('[data-m=pw1]', 'type') == 'text', 'SHOW reveals password')
        fill('pw2', 'Password1'); c('[data-a=signup]'); check(sc() == 'skills', 'valid sign up → Skills')

        # ---------- 3. Set-up steps
        print(' 3 set-up')
        t('Continue →'); check('skill' in err(), 'skills: continue without choice → error')
        c('[data-a=back]'); check(sc() == 'signup', 'skills Back → Sign Up'); pg.go_back() if False else None
        c('[data-a=signup]'); check('already' in err(), 'same email again → "account already" error')
        # go forward again through history-free path: sign in is not needed, use skills via state
        pg.evaluate("go('skills')"); pg.wait_for_timeout(60)
        t('Python'); fill('sq', 'Origami'); pg.press('[data-m=sq]', 'Enter'); pg.wait_for_timeout(60)
        check(pg.evaluate('S.me.skills') == ['Python', 'Origami'], 'pick skill + add custom skill with Enter')
        refresh(); check(sc() == 'skills' and pg.evaluate('S.me.skills.length') == 2, 'refresh keeps Skills + selection')
        c('[data-a=go][data-s=interests]'); check(sc() == 'interests', 'skills → interests')
        c('[data-a=go][data-s=photo]'); check('interest' in err(), 'interests required')
        t('Music'); t('Design'); c('[data-a=go][data-s=photo]'); check(sc() == 'photo', 'interests → photo')
        c('[data-a=photoNext]'); c('[data-a=photoNext]'); c('[data-a=photoPrev]'); check(pg.evaluate('S.pick') == 1, 'photo arrows')
        c('[data-a=pick]', 3); pick = pg.evaluate('S.pick'); fill('fn', 'Ana Bold')
        c('[data-a=photook]'); check(sc() == 'about' and pg.evaluate('S.me.av') == pick, 'Use this picture → About, avatar saved')
        c('[data-a=go][data-s=role]'); check('date of birth' in err(), 'about: empty → error')
        fill('loc', 'Ulaanbaatar'); c('[data-a=go][data-s=role]'); check(sc() == 'about', 'about: location only is not enough')
        t('Female'); fill('dob', '2999-01-01'); c('[data-a=go][data-s=role]'); check('valid date' in err(), 'about: future birth date rejected')
        fill('dob', '2000-05-05'); refresh(); check(sc() == 'about' and pg.input_value('[data-m=loc]') == 'Ulaanbaatar', 'refresh keeps About form values')
        c('[data-a=go][data-s=role]'); check(sc() == 'role', 'about (all 3 filled) → role')
        c('[data-a=finish]'); check('Choose' in err(), 'role required')
        t('Both'); c('[data-a=finish]'); check(sc() == 'home', 'Complete set up → Home')
        check('Hello, Ana Bold !' in pg.inner_text('#v h1'), 'Home greets with the full name')
        check(pg.evaluate('S.me.age') != '' and pg.evaluate('S.me.loc') == 'Ulaanbaatar' and pg.evaluate('S.me.gender') == 'Female', 'about data saved to profile')

        # ---------- 4. Home objectives, notifications, people
        print(' 4 home / people')
        c('[data-a=all][data-k=p]'); check(pg.locator('.bd .cd').count() == 5, 'See All people')
        c('[data-a=all][data-k=""]'); c('[data-a=all][data-k=s]'); t('Yoga'); check(sc() == 'search' and pg.input_value('[data-m=q]') == 'Yoga', 'Discover skill → Search prefilled')
        check('person found' in pg.inner_text('.bd'), 'search result count shown')
        fill('q', 'zzz'); check(pg.inner_text('.bd p').startswith('0'), 'search filters live')
        fill('q', ''); c('[data-a=sf][data-k=top]'); check(pg.locator('.bd .cd').count() == 3, 'top rated filter')
        c('[data-a=sf][data-k=on]'); check(pg.locator('.bd .cd').count() == 3, 'online filter')
        c('[data-a=sf][data-k=all]'); c('.bd [data-a=user]', 1); check(sc() == 'user', 'open person profile')
        c('[data-a=fav]'); check(pg.locator('.st.on').count() == 1, 'favourite toggles')
        c('[data-a=request]'); check('Requested' in pg.inner_text('[data-a=request]'), 'To request → Requested')
        c('[data-a=reply][data-k=public]'); c('[data-a=sendreply]'); check('Write a reply' in pg.inner_text('.md'), 'empty public reply → error')
        fill('replyText', 'Thanks!'); c('[data-a=sendreply]'); check(ov() is None and pg.locator('.rvc .rpl').count() == 1, 'public reply posted + thread opened')
        refresh(); check(sc() == 'user' and pg.locator('.rvc .rpl').count() == 1, 'refresh on profile keeps reply')
        c('[data-a=back]'); check(sc() == 'search', 'Back from profile → Search')
        tab('home'); c('[data-a=notif]'); check(sc() == 'notif', 'bell → Notifications')
        c('[data-a=nacc]'); check('Accepted' in pg.inner_text('.bd'), 'accept swap request')
        c('.bd [data-a=user][data-id="5"]'); check('Add to the session' in pg.inner_text('[data-a=request]'), 'accepted person → Add to the session')
        c('[data-a=request]'); check(sc() == 'home' and pg.input_value('[data-m=sw]') == 'Lukas Weber', 'Add to the session → prefilled form')

        # ---------- 5. Sessions: add / cancel / finish / rate
        print(' 5 sessions')
        fill('sw', 'Nobody'); c('[data-a=addses]'); check('person' in err(), 'unknown person → error')
        fill('sw', 'Lukas Weber'); c('[data-a=addses]'); check('subject' in err(), 'subject required')
        fill('ss', 'German'); c('[data-a=addopen]') if pg.locator('[data-a=addopen]').count() else None
        fill('t1', '19:00'); fill('t2', '18:00'); c('[data-a=addses]'); check('end must be after' in err(), 'end time before start → error')
        fill('t2', '20:00'); fill('d1', '2030-02-10'); fill('d2', '2030-02-01'); c('[data-a=addses]'); check('last day' in err(), 'end date before start → error')
        fill('d2', '2030-03-01'); c('[data-a=addses]'); check(pg.locator('.bd .cd.col').count() == 1, 'session added')
        c('[data-a=addopen]'); fill('sw', 'Alex Chen'); fill('ss', 'Physics'); c('[data-a=addses]'); check(pg.locator('.bd .cd.col').count() == 2, 'second session added')
        c('[data-a=canc]', 1); check(ov() == 'canc', 'cancel asks for confirmation'); t('Keep it'); check(pg.locator('.bd .cd.col').count() == 2, 'Keep it keeps session')
        c('[data-a=canc]', 1); t('Yes, cancel'); check(pg.locator('.bd .cd.col').count() == 1, 'Yes, cancel removes session')
        c('[data-a=fin]'); c('.md [data-a=cl]'); check(pg.locator('.bd .cd.col').count() == 1, 'Finish → No keeps session')
        c('[data-a=fin]'); c('[data-a=finyes]'); check('Session finished, thank you!' in pg.inner_text('.md'), 'Finish → Yes → "Session finished, thank you!"')
        c('.md [data-a=cl]'); check(ov() is None and sc() == 'home' and pg.evaluate('S.tab') == 'ses', 'Close stays on Session tab')
        c('[data-a=htab][data-k=rate]'); names = pg.locator('.bd .cd.col b').all_inner_texts()
        check(names[0] == 'Lukas Weber' and len(names) == 3, 'finished session appears first in To rate')
        pg.locator('textarea').nth(1).fill('draft for Sofia')
        c('[data-a=rate]'); check('Tap a star' in toast_text(), 'rating needs a star')
        c('.stars >> nth=0 >> span >> nth=4'); pg.locator('textarea').nth(0).fill('Great German lesson'); c('[data-a=rate]')
        check(ov() == 'thx', 'Send review → Thank you'); c('.md [data-a=cl]')
        check(pg.locator('textarea').nth(0).input_value() == 'draft for Sofia', 'other drafts stay on their own card')
        refresh(); check(pg.evaluate('S.tab') == 'rate' and pg.locator('.bd .cd.col').count() == 2, 'refresh keeps To rate')

        # ---------- 6. Messages / chat
        print(' 6 messages')
        tab('msg'); check(sc() == 'msgs', 'Messages tab'); check('+2' in pg.inner_text('.bd'), 'unread badge')
        c('.bd .cd[data-a=chat]'); check(sc() == 'chat', 'open chat')
        pg.fill('#ci', 'Hello there'); pg.press('#ci', 'Enter'); pg.wait_for_timeout(1300)
        check(pg.locator('.bub.me').count() == 1 and pg.locator('.bub').count() == 3, 'send message + auto reply')
        pg.fill('#ci', 'Bye'); c('[data-a=send]'); c('[data-a=back]'); pg.wait_for_timeout(1300)
        check(pg.evaluate('S.msgs[1].m.length') == 5 and pg.evaluate('S.msgs[1].un') == 1, 'reply arriving after leaving chat is kept as unread')
        refresh(); check(sc() == 'msgs' and pg.evaluate('S.msgs[1].m.length') == 5, 'refresh keeps chat history')
        c('[data-a=menu]'); t('pin'); check('📌' in pg.inner_text('.bd'), 'pin')
        c('[data-a=menu]'); t('mute'); check('🔇' in pg.inner_text('.bd'), 'mute')
        c('[data-a=menu]', 1); t('archive'); c('[data-a=ma][data-k="1"]'); check(pg.locator('.bd .cd[data-a=chat]').count() == 1, 'archive → Archived chat')
        c('[data-a=menu]'); t('unarchive'); c('[data-a=ma][data-k="0"]'); check(pg.locator('.bd .cd[data-a=chat]').count() == 5, 'unarchive')
        fill('mq', 'mia'); check(pg.locator('.bd .cd[data-a=chat]').count() == 1, 'search conversations'); fill('mq', '')
        c('[data-a=menu]', 4); t('block'); check(pg.locator('.bd .cd[data-a=chat]').count() == 4, 'blocked user disappears from Messages')
        c('[data-a=menu]', 3); t('delete'); check(pg.locator('.bd .cd[data-a=chat]').count() == 3, 'delete conversation')
        c('.dim', 0) if pg.locator('.dim').count() else None

        # ---------- 7. Reviews
        print(' 7 reviews')
        tab('rev'); check(sc() == 'reviews', 'Reviews tab'); c('[data-a=reply]'); c('.md [data-a=cl]'); check(ov() is None, 'reply Cancel')
        c('[data-a=reply]'); fill('replyText', 'Thank you!'); c('[data-a=sendreply]'); check('1 reply' in pg.inner_text('.bd'), 'reply to received review')
        c('[data-a=toggleReplies]'); check(pg.locator('.rpl').count() == 0, 'collapse replies')
        c('[data-a=rg][data-k="1"]'); check('Lukas Weber' in pg.inner_text('.bd') and 'Great German lesson' in pg.inner_text('.bd'), 'Given shows the new review')

        # ---------- 8. Profile, edit, settings
        print(' 8 profile')
        tab('profile'); check(sc() == 'profile' and 'Ana Bold' in pg.inner_text('.pf2'), 'My Profile shows name')
        check('Python / Origami' in pg.inner_text('.bd'), 'profile shows skills')
        c('[data-a=sw][data-k=dark]'); check(pg.evaluate("document.documentElement.hasAttribute('data-dark')"), 'dark mode on')
        refresh(); check(pg.evaluate("document.documentElement.hasAttribute('data-dark')") and sc() == 'profile', 'dark mode survives refresh')
        c('[data-a=sw][data-k=dark]')
        t('Edit'); fill('en', 'Discard Me'); c('[data-a=epick]', 7); c('[data-a=eback]')
        check('Ana Bold' in pg.inner_text('.pf2') and pg.evaluate('S.me.av') == pick, 'Edit → Back discards changes')
        t('Edit'); check(pg.input_value('[data-m=en]') == 'Ana Bold', 'Edit opens with saved values')
        fill('ee', 'not-an-email'); c('[data-a=save]'); check(sc() == 'edit' and 'valid email' in toast_text(), 'invalid email blocked on save')
        fill('ee', 'ana.new@test.com'); fill('en', 'Ana Updated'); fill('eage', '200'); c('[data-a=save]'); check(sc() == 'edit', 'invalid age blocked')
        fill('eage', '26'); fill('ehobby', 'Chess'); fill('eb', 'Hello world')
        c('[data-a=skrem]'); fill('esq', 'Java'); c('[data-a=skadd][data-c=Java]'); fill('eiq', 'Kites'); pg.press('[data-m=eiq]', 'Enter'); pg.wait_for_timeout(60)
        c('[data-a=epick]', 9); refresh(); check(sc() == 'edit' and pg.input_value('[data-m=en]') == 'Ana Updated', 'refresh keeps Edit draft')
        c('[data-a=save]'); check(sc() == 'profile', 'Save → My Profile')
        txt = pg.inner_text('#v')
        check('Ana Updated' in txt and 'ana.new@test.com' in txt and 'Hello world' in txt and 'Origami / Java' in txt and 'Kites' in txt and 'Age: 26' in txt, 'My Profile shows edited values')
        check(pg.evaluate('S.me.av') == 9, 'avatar saved')
        tab('home'); check('Hello, Ana Updated !' in pg.inner_text('#v h1'), 'Home header uses new name')
        if desktop: check('Ana Updated' in pg.inner_text('#sbu'), 'sidebar uses new name')
        tab('profile'); c('[data-a=go][data-s=privacy]'); c('[data-a=pv][data-k=loc]'); check(pg.evaluate('S.pv.loc') == 0, 'privacy toggle')
        c('[data-a=go][data-s=blocked]'); check(pg.locator('[data-a=unblock]').count() == 1, 'blocked list shows the blocked user'); c('[data-a=unblock]'); check('No blocked' in pg.inner_text('.bd'), 'unblock')
        c('[data-a=back]'); c('[data-a=go][data-s=chpw]')
        c('[data-a=chpw]'); check('current' in err(), 'chpw: current required')
        fill('cp0', 'wrong'); c('[data-a=chpw]'); check('wrong' in err(), 'chpw: wrong current')
        fill('cp0', 'Password1'); fill('cp1', 'short'); c('[data-a=chpw]'); check('8' in err(), 'chpw: too short')
        fill('cp1', 'NewPass99'); fill('cp2', 'Other999'); c('[data-a=chpw]'); check('match' in err(), 'chpw: mismatch')
        fill('cp2', 'NewPass99'); c('[data-a=chpw]'); check(sc() == 'privacy', 'password changed → back')
        c('[data-a=back]'); c('[data-a=go][data-s=help]'); c('[data-a=faq]', 1); check(sc() == 'faq', 'open FAQ')
        c('.rowl[data-a=faq]'); c('[data-a=back]'); check(sc() == 'help', 'FAQ → other FAQ → Back returns to Help')
        t('Contact support'); c('[data-a=supportSend]'); check('issue type' in err(), 'support validation')
        pg.select_option('[data-m=supType]', 'Bug report'); c('[data-a=supportSend]')
        check(pg.locator('[data-m=supType]').input_value() == 'Bug report', 'issue type stays selected after error')
        fill('supSubject', 'Bug'); fill('supMessage', 'Details'); c('[data-a=supportSend]'); check(sc() == 'help', 'support sent → back')
        c('[data-a=back]'); check(sc() == 'profile', 'Help Back → Profile')

        # ---------- 9. Sign out / sign in / data persistence
        print(' 9 sign out / in')
        tab('profile')
        if desktop: c('.sb-out')
        else: c('#v [data-a=ask]')
        check(ov() == 'ask', 'sign out asks'); t('No'); check(sc() == 'profile', 'No keeps you signed in')
        c('#v [data-a=ask]'); t('Yes'); check(sc() == 'signin' and pg.evaluate('S.uid') is None, 'Yes → Sign In, user cleared')
        check(pg.locator('#ph.has-sb').count() == 0, 'sidebar hidden after sign out')
        refresh(); check(sc() == 'signin', 'refresh after sign out stays on Sign In')
        pg.evaluate("S.sc='profile';draw()"); check(sc() == 'signin', 'signed-out user cannot open app screens')
        fill('em', 'ana.new@test.com'); fill('pw', 'Password1'); c('[data-a=signin]'); check('Wrong' in err(), 'old password rejected')
        fill('pw', 'NewPass99'); pg.press('[data-m=pw]', 'Enter'); pg.wait_for_timeout(80); check(sc() == 'home', 'sign in with new password (Enter key)')
        check('Hello, Ana Updated !' in pg.inner_text('#v h1'), 'profile restored after sign in')
        c('[data-a=htab][data-k=ses]'); check(pg.locator('.bd .cd.col').count() == 0 and pg.evaluate('S.fin.length') == 2 and pg.evaluate('S.given.length') == 2, 'user data restored')
        # other user does not inherit data
        tab('profile'); c('#v [data-a=ask]') if not desktop else c('.sb-out'); t('Yes')
        fill('em', 'bob@test.com'); fill('pw', 'whatever'); c('[data-a=signin]')
        check(pg.evaluate('S.me.name') == 'bob' and pg.evaluate('S.given.length') == 1, 'another account starts clean')
        tab('profile'); c('#v [data-a=ask]') if not desktop else c('.sb-out'); t('Yes')

        # ---------- 10. Forgot password
        print(' 10 forgot password')
        t('Forgot Password?'); c('[data-a=sendcode]'); check('valid email' in err(), 'forgot: email required')
        fill('fe', 'ana.new@test.com'); c('[data-a=sendcode]'); pg.wait_for_timeout(1000); check(sc() == 'otp', 'code sent → OTP')
        refresh(); check(sc() == 'otp' and len(pg.evaluate('S.otp')) == 6, 'refresh keeps OTP screen + code')
        pg.locator('[data-o="0"]').type('x'); check(pg.input_value('[data-o="0"]') == '', 'OTP accepts digits only')
        for i, d in enumerate('000000'): pg.locator(f'[data-o="{i}"]').fill(d)
        c('[data-a=verify]'); check('Wrong code' in err() or pg.evaluate('S.otp') == '000000', 'wrong code → error')
        code = pg.evaluate('S.otp')
        pg.locator('[data-o="0"]').click()
        for i, d in enumerate(code): pg.locator(f'[data-o="{i}"]').fill(d)
        c('[data-a=verify]'); check(sc() == 'newpw', 'right code → New password')
        fill('pw1', 'Reset1234'); fill('pw2', 'Reset12345'); c('[data-a=reset]'); check('match' in err(), 'reset mismatch')
        fill('pw2', 'Reset1234'); c('[data-a=reset]'); pg.wait_for_timeout(1100); check(sc() == 'signin', 'reset → Sign In')
        fill('em', 'ANA.NEW@test.com'); fill('pw', 'Reset1234'); c('[data-a=signin]'); check(sc() == 'home', 'sign in with reset password (email case-insensitive)')

        # ---------- 11. Refresh everywhere + back buttons
        print(' 11 refresh / back')
        for name, nav in [('chat', "go('chat',{id:2})"), ('user', "go('user',{id:3})"), ('faq', "go('faq',{i:4})"), ('notif', "go('notif')"), ('revd', "go('revd',{g:0,i:0})"), ('chpw', "go('chpw')")]:
            pg.evaluate(nav); pg.wait_for_timeout(50); refresh()
            check(sc() == name, f'refresh keeps {name}')
            if pg.locator('[data-a=back]').count():
                c('[data-a=back]'); check(sc() != name, f'Back works on {name} after refresh')
        pg.evaluate("S.st=[];S.sc='chat';S.arg={id:999};draw()"); check(sc() == 'home', 'broken screen data falls back to Home (no crash)')

        # ---------- 12. New visit (new tab) shows splash → sign in / sign up again
        print(' 12 new visit')
        pg2 = ctx.new_page(); pg2.goto(URL); pg2.wait_for_timeout(200)
        check(pg2.evaluate('S.sc') == 'splash', 'new tab = fresh visit → splash / onboarding → Sign in / Sign up')
        pg2.close()

        for x in errs: print('   console:', x)
        check(not errs, f'no console errors ({len(errs)})')
        b.close()


for vp, label in [({'width': 390, 'height': 844}, 'PHONE'), ({'width': 1440, 'height': 900}, 'DESKTOP')]:
    run(vp, label)
print(f'\nPASSED {PASSES[0]}  FAILED {len(FAILS)}')
for f in FAILS: print(' -', f)
sys.exit(1 if FAILS else 0)
