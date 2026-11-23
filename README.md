# بلاغ | Balagh

لعبة تحقيق مصرية تجريبية بـ Python وStreamlit. هذه النسخة تطوّر القضية الفردية الموجودة «الغرفة المغلقة» بنفس الشخصيات داخل المشروع نفسه.

## التشغيل المحلي

يتطلب Python 3.10 أو أحدث:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

على Windows: استخدم `.venv\Scripts\activate` بدل أمر التفعيل أعلاه.

اللعب الأساسي مش محتاج مفتاح AI ولا حساب Supabase. تجربة سؤال كل الشخصيات بطريقتك بتستخدم Groq بمفتاح على السيرفر. حط `GROQ_API_KEY` في `.streamlit/secrets.toml` محليًا، أو في إعدادات Secrets على Streamlit Cloud. ما تحطش المفتاح في GitHub.

## التجربة

1. ابدأ التحقيق وافحص الأدلة باستخدام زر «تم فحص الدليل».
2. اسأل الشخصيات. تظهر أسئلة مواجهة إضافية بعد فحص الأدلة المرتبطة بها.
3. راجع سجل الاستجوابات واكتب ملاحظاتك.
4. اختر المتهم والأدلة الداعمة وأكّد القرار النهائي. ينهي القرار المحاولة ولا يكشف اسم الفاعل تلقائيًا عند الخطأ.
5. بعد انتهاء المحاولة يمكنك طلب كشف الحل، أو بدء محاولة جديدة نظيفة.

اللعب الفردي محفوظ في الجلسة بس. أوضة التعاون بين لاعبين بتتحفظ على Supabase، بتفاصيل الدخول والخصوصية تحت.

## ما تغيّر في القضية

- فصل كاميرا الممر المعطلة عن كاميرا البهو المستقلة.
- تفسير الباب المؤمّن من الداخل والساعة المتوقفة، وتصحيح التوقيت المضلل لمكالمة يوسف.
- أدلة مرقمة تربط الزيارة بالكوب والدافع. المادة السامة خيالية ولا تتضمن وصفة أو جرعة أو إرشادات عملية.
- إجابات مكتوبة مختلفة للشخصيات، مع سجل يبقى عبر إعادة تشغيل واجهة Streamlit.
- الاتهام يُقيّم اسم المتهم وسلسلة الأدلة المطلوبة، لا الاسم فقط.

أضيفت تفاصيل قصصية وأدلة جديدة لاستكمال اللغز، وليست حقائق موجودة في النسخة الأولى. هذه تجربة أولى بسيطة وليست محاكاة جنائية أو قانونية واقعية. كشف الدافع وسلسلة الأدلة واضح عمدًا لاختبار دورة اللعب؛ يمكن زيادة صعوبة اللغز لاحقًا بعد تجربة اللاعبين.

## الاختبارات

```bash
python -m unittest -v
```

تغطي الاختبارات نسخ الحالة، سلامة المعرفات، إتاحة الأسئلة، منع الإجابات المقفلة، حفظ سجل الاستجواب، اكتمال أدلة الاتهام، منع الاتهامات المتكررة وإعادة المحاولة.

## حدود وأمان التطوير القادم

- حل القضية موجود في المصدر. لا يمكن ضمان تجربة بلا حرق لمن يقرأ المستودع المفتوح.
- حفظ الحقيقة في عملية Streamlit الحالية ليس تصميم API جاهزًا للعب جماعي. يجب فصل حالة الغرفة العامة عن الأدوار الخاصة ومفتاح الحل مع صلاحيات وصول مناسبة قبل إضافة غرف مشتركة.
- AI حقيقي من Groq بالموديل `openai/gpt-oss-20b` بيفهم السؤال ويختار موضوع مسموح. الردود من نص القضية المكتوب، مش حوار مولّد بحرية. الحقائق المقفولة والحل ما بيتبعتوش للموديل.
- سؤالك وآخر 4 أسئلة وموضوعاتها بيتبعتوا لـ Groq. بلاش بيانات شخصية أو أسرار.
- التجربة على الخطة المجانية، من غير خدمة مدفوعة بديلة. الحدود المشتركة وقت الإعداد: 30 طلب في الدقيقة و1000 في اليوم. ممكن تتغير أو تخلص؛ وقتها الأسئلة الجاهزة تفضل شغالة. فيه حد 20 سؤال مشترك بين كل الشخصيات في المحاولة و8 ثواني بين الطلبات، مش حماية كاملة ضد إساءة الاستخدام.
- مصدر الحدود: https://console.groq.com/docs/rate-limits
- سياسة البيانات: https://console.groq.com/docs/your-data
- فيه أوضة تعاون بين اتنين، لكن لسه مفيش أدوار سرية أو 2v2/4v4. تجربة AI مع كل الشخصيات بنفس الواجهة ومن غير اختيار تلقائي لشخصية.


## أوضة التحقيق التعاوني

اتنين يدخلوا بكود أوضة. الأدلة والاستجوابات مشتركة، والنوتة خاصة لكل لاعب وبزر حفظ. الاتهام النهائي محتاج موافقة لاعبين مختلفين على نفس المتهم والأدلة. أي تحديث للتحقيق بيلغي الاقتراح القديم. دي مش لعبة أدوار سرية.

كل لاعب بينزّل مفتاح رجوع شخصي. ما يتبعتش للشات ولا لصاحبك: اللي معاه يقدر يدخل باسمك ويشوف نوتتك. مفيش استرجاع بالاسم. كود الأوضة دعوة لشخص تاني لو فيه مكان، مش هوية مؤكدة. الرجوع بعد قفل الجلسة بالمفتاح، والنوتة بتفضل على السيرفر.

`rooms.sql` ترقية إضافية للجداول الموجودة، من غير مسح بيانات. الجدولين مش متاحين مباشرة من Data API. المتاح بس وظيفة `balagh_room`، ومفاتيح اللاعبين مخزنة كبصمات SHA-256. مفتاح Supabase العام يفضل على السيرفر، ومفيش احتياج لمفتاح service_role. التحديثات بتستخدم revision عشان ما تدوسش على تغيير صاحبك. المزامنة باستعلام كل 5 ثواني والصفحة مفتوحة، مش WebSocket.

لازم `SUPABASE_URL` و`SUPABASE_KEY` في Secrets. شغّل الترقية ثم اسمح بوظيفة `balagh_room` بس في Data API، من غير فتح الجداول أو إلغاء RLS. الخطة مجانية وقت الإعداد، وممكن تتوقف مع قلة الاستخدام أو نفاد الحدود. مفيش ترقية أو دفع تلقائي. الأوض محفوظة لحد حذفها إداريًا، ومفيش نسخ احتياطية تلقائية على المجاني. النسخة دي تجربة صغيرة، مش حماية كاملة ضد الإساءة أو منصة إنتاج.

## Detective race
Select سباق محققين. Two investigators work independently on the same case. The investigation waits until both join. Each gets one final accusation. A wrong suspect or incomplete evidence eliminates only that player. Both wrong means no winner. The first server-accepted correct suspect plus the authored required evidence wins; concurrent submissions are serialized by the database room lock. The other player sees the winner within the existing five-second refresh while open. There is no push notification after closing the app.

Progress, interview/AI history and notes are private in races. Action-specific database operations validate clue IDs, interview gates and final evidence; arbitrary state commits are rejected in both modes. The AI classifier can choose a topic but cannot author case answers or determine the winner. Race AI limit is 20 questions per player. Existing co-op keeps shared history and the shared limit.

This is the same fixed case whose solution is already in this repository and solo mode. It is a friends race, not a blind or cheat-proof contest. Inspection records show which clue buttons were used, not proof that someone read or reasoned about them. Recovery keys are bearer credentials. There is no automatic room expiry yet.

Apply the additive `rooms.sql` migration before deploying this app version. It preserves existing co-op rooms but replaces their broad commit operation with validated actions. Only `balagh_room` is executable by client roles; the internal `balagh_action` helper and raw tables must remain inaccessible.

Optional destructive-to-test-data-only integration checks: set `BALAGH_LIVE_TEST_CONFIG` to a private TOML file containing SUPABASE_URL/SUPABASE_KEY, then run `python test_race_live.py`. It creates test rooms with distinct Arabic test names, never use real-player names for cleanup. Never commit that config.

## 3D atmosphere slice
Choose أوضة 3D، تجربة. This is a contained, real-time Three.js room: drag to orbit, wheel or +/- to zoom, and click/tap the blue cup, watch, telephone or folder. The same four files are available as keyboard-accessible buttons. Evidence text is injected from the unchanged canonical case. Its inspected state is session-local to the embedded scene and does not change scored solo/co-op/race state. A full page refresh starts the slice afresh. No room tokens, backend keys or Groq secret enter this component.

Original low-poly procedural scene and original procedural sine-based ambient music/effects, muted until explicit play. Play/pause, volume and reduced-motion controls included. Background tabs suspend audio. Three.js 0.170.0 loads from jsDelivr, Cairo font from Google Fonts, so network and browser WebGL support are needed; file buttons remain a fallback if 3D cannot load. Full MIT and SIL OFL notices are included in the scene. This is a vertical slice, not a full 3D conversion or free-walking game. Mobile browser emulation is tested, real-device performance still needs user feedback.

## Immersive entry
New sessions start inside the 3D atmosphere, then Start opens a case chooser containing only the implemented case 001, then existing game modes. A persistent local Streamlit component owns the audio so the same context survives chooser/game reruns; it collapses to an audio bar during play and stops rendering the hidden 3D scene. Initial audio is attempted once, browser policy may block it, and a gesture inside the scene starts it unless the user muted it. Visible mute/play and volume controls remain. No attempt to bypass browser policy. Full refresh starts a new entry visit. The original four-file 3D inspection slice remains a separate mode; entry does not reveal those files before case selection. No database or RPC changes.


### Integrated hotel investigation
The hotel case now opens its own crime scene inside the investigation. Nine original evidence cards are readable from the scene or its file board. Marking a card read updates the same investigation evidence used by interview gates and accusation options. Report packets are a visual file rack, not new physical clues. The room layout remains illustrative. The old experimental mode is no longer in the mode chooser. Solo, co-op and race retain their original boundaries, revision checks and finished-state locks. A single persistent entry component owns music; the crime scene creates no audio context. Future cases need their own scene mapping; no additional cases are included.
