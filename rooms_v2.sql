-- Balagh shared game modes (generated: python gen_rooms_sql.py). Additive and idempotent.
-- One engine for every case: coop (everyone shares one investigation), race (each player alone),
-- team (shared inside a team, separate between teams). Cases come from the generated catalog.
begin;
alter table public.rooms add column if not exists case_id text not null default '001';
alter table public.rooms add column if not exists team_count int not null default 1;
alter table public.rooms add column if not exists team_size int not null default 1;
alter table public.rooms add column if not exists started boolean not null default true;
alter table public.rooms add column if not exists units jsonb not null default '{}'::jsonb;
alter table public.rooms add column if not exists winner_unit text;
alter table public.rooms add column if not exists host_id bigint;
alter table public.players add column if not exists unit text;

-- One-time carry-over of rooms created by the earlier two-player version.
update public.rooms r set units=jsonb_build_object('0',jsonb_build_object('investigation',r.investigation,'proposal',r.proposal,'approvals',r.approvals,'rev',r.revision))
 where r.mode='coop' and r.units='{}'::jsonb;
update public.players p set unit='0' where p.unit is null and exists(select 1 from public.rooms r where r.room_code=p.room_code and r.mode='coop');
update public.players p set unit='p'||p.id where p.unit is null;
update public.rooms r set units=coalesce((select jsonb_object_agg(p.unit,jsonb_build_object('investigation',p.investigation,'proposal',null,'approvals','[]'::jsonb,'rev',0)) from public.players p where p.room_code=r.room_code),'{}'::jsonb)
 where r.mode='race' and r.units='{}'::jsonb;
update public.rooms set winner_unit='p'||winner_id where winner_id is not null and winner_unit is null;
update public.rooms r set host_id=(select min(id) from public.players p where p.room_code=r.room_code) where host_id is null;

drop function if exists public.balagh_action(jsonb,text,jsonb);
create or replace function public.balagh_catalog() returns jsonb language sql immutable as $cat$select $catalog${"001":{"characters":[{"id":"aser","interviews":[{"answer":"بص يا سيدي، إحنا صحاب من زمان. بس حقوق رواية دخلت بينا، ومن ساعتها الدنيا ما بقتش زي الأول. وكان دايمًا يسمي تهديده آخر مشهد. حسبته كلام مخرج وخلاص.","id":"a1","question":"إنت ونادر علاقتكم كانت إيه؟","requires":[]},{"answer":"في مطعم الفندق. الفاتورة موجودة، والجرسون يقدر يقولك. هتلاقي ده في ملف مراجعة الكلام.","id":"a2","question":"كنت فين من ⁧⁦10:50⁩ بليل⁩ لحد ⁧⁦11:25⁩ بليل⁩؟","requires":[]},{"answer":"آه، طلبت فلوس عشان أسكت عن سر قديم. مش هجمّلها. بس إني عملت كده حاجة، وإني أدخل جناحه وأقتله حاجة تانية. أنا ما دخلتش هناك الليلة دي.","id":"a3","question":"يعني الموضوع وصل إنك تبتزّه؟","requires":[]}],"job":"روائي جرائم","name":"آسر منصور"},{"id":"layla","interviews":[{"answer":"أيوه... كنا مرتبطين. وما كنتش عايزة حد يعرف. أنا متوترة عشان كده، مش عشان اللي في دماغك.","id":"l1","question":"كنتِ تعرفي نادر بعيد عن الشغل؟","requires":[]},{"answer":"على البيانو قدام الناس. الحفلة متصوّرة من غير تقطيع، هتلاقوا التسجيل في ملف مراجعة الكلام.","id":"l2","question":"كنتِ فين وقت الزيارة اللي بالليل دي؟","requires":[]},{"answer":"أنا شفت ساعته بتقف قبل كده، بس ده مش دليل على حاجة. بصّ على فحص البطارية، هو اللي هيفيدك، مش تخميني أنا.","id":"l3","question":"طب والساعة اللي وقفت دي حكايتها إيه؟","requires":["E05"]}],"job":"عازفة بيانو","name":"ليلى الديب"},{"id":"youssef","interviews":[{"answer":"كان معاه ورق بتاعي ورفض يرجّعه. اتخانقنا، ده حصل. وأنا قلت للمحقق إني كنت على التليفون وقت الجريمة.","id":"y1","question":"كنت متعصّب ليه؟","requires":[]},{"answer":"عندك حق، أنا لخبطت في المعادين. المكالمة خلصت ⁧⁦11:22⁩ بليل⁩، فمش هقدر أقول إنها تثبت أنا كنت فين الساعة ⁧⁦11:42⁩ بليل⁩.","id":"y2","question":"مكالمتك خلصت ⁧⁦11:22⁩ بليل⁩، ونادر مات ⁧⁦11:42⁩ بليل⁩. إزاي يعني؟","requires":["E01","E03"]},{"answer":"سمعت صوت ست، افتكرته صوت نادين، بتقول إن الضيافة جاهزة. بس أنا ما شفتهاش بعيني. خُدها حاجة تراجع وراها، مش دليل أكيد.","id":"y3","question":"سمعت صوت حد معاه في المكالمة؟","requires":["E03"]}],"job":"دكتور نفسي","name":"يوسف بيومي"},{"id":"nadine","interviews":[{"answer":"الساعة ⁧⁦10:00⁩ بليل⁩ بالظبط. كلمته قبلها في موضوع شغل، وبعد كده ما شفتوش.","id":"n1","question":"مشيتي من الفندق إمتى؟","requires":[]},{"answer":"أيوه رجعت شوية، وما كنتش عايزة أدخل في الحكاية دي. وقدّمت له الكوباية، ما أنكرتش ده. بس زيارتي ليه مش معناها إني قتلته.","id":"n2","question":"إمضتك وكلام الموظفة بيقولوا إنك كنتِ عنده ⁧⁦10:58⁩ بليل⁩. إزاي؟","requires":["E06"]},{"answer":"التحليل؟ ما عنديش تفسير ليه. أنا كنت هناك وقدّمت له الكوباية، دي حقيقة. بس مش هألفلك حكاية تانية وأقعد أزود كلام من غير دليل.","id":"n3","question":"طب تفسّري إزاي نتيجة الكوباية مع دفتر الزيارة؟","requires":["E06","E07"]},{"answer":"آه، كان بيهدد شغلي وحياتي الخاصة. وطبعًا كنت خايفة ومتعصّبة. بس ما تمسكش الجملة دي وتقول إني اعترفت بالقتل.","id":"n4","question":"نادر كان بيهددك؟","requires":["E08"]},{"answer":"أنا فهمتها إنه هيقفل الموضوع لو اختفى. ما كنتش عارفة إن الإرسال مجدول ومش مستني منه ضغطة. اللي كنت بحاول أوقفه كان هيكمل من غيره. ده ما يمسحش اللي المحضر أثبته، بس يغيّر الحكاية اللي كنت بحكيها لنفسي.","id":"n5","question":"آخر مشهد كان رسالة وداع، ولا حاجة لسه جاية؟","requires":["E05","E08"]}],"job":"صحفية تحقيقات","name":"نادين مراد"}],"continuity":[{"after":["n2"],"answer":"أنا قلت عشرة بالليل في الأول، بس خلاص قلتلك إني رجعت زيارة وقدّمت له الكوباية. مش هارجع أنكر الزيارة تاني.","case":"001","suspect":"nadine","topic":"n1"}],"evidence":{"E01":[],"E02":[],"E03":[],"E04":[],"E05":[],"E06":[],"E07":[],"E08":[],"E09":[]},"killer":"نادين مراد","required":["E06","E07","E08"]},"002":{"characters":[{"id":"omar","interviews":[{"answer":"بعد ما رجعنا من التصوير على ٨:٣٠ اتخانقنا. أنا عايز أراجع اللقطات وأظبط الألوان الأول، وهو مستعجل وعايز ينزّلها على جروب الرحلة الليلة، وكان مصمم تتسجّل هناك قبل العاشرة بالظبط. زعلت منه فعلاً، بس لحد ما حصل اللي حصل كنت قاعد مع عبده بنسجّل المقابلة بالكاميرا الواسعة.","id":"s201","question":"إنت ودينهو كنتوا مختلفين على إيه؟","requires":[]},{"answer":"أيوه، لبست جاكيتي الفاتح من وقت التسليم قبل المغرب، وهو سادة من غير أي علامة. اللي عليه رقعة قماش على الكتف هو جاكيت باسم. بس ما تمشيش ورا اللون: فيه تلات حاجات فاتحة في المخيم، جاكيتي وجاكيت باسم ووشاح عبده. دفتر المعدات هو اللي بيفرّق.","id":"s202","question":"الجاكيت الفاتح كان معاك طول الليل؟","requires":["E03"]},{"answer":"كنت قاعد مع عبده قدام الخيمة بنسجّل المقابلة. التسجيل الأصلي على الكارت متصل من غير قطع. افحصه بنفسك، ولو أنا مش فيه يبقى كلامي باطل.","id":"s203","question":"كنت فين وقت الصورة؟","requires":["E02"]}],"job":"مصور صحفي","name":"عمر معاذ"},{"id":"bassem","interviews":[{"answer":"شفته قبل ما النور يقطع بشوية. بعدها قعدت أصلّح الفانوس من ٩:٤٥ لحد ١٠:٠٥ من غير ما أبعد. والنور قطع ١٠:٠٠ فجأة ودينهو كان ماشي جنب المخزن في الضلمة. أكيد وقع.","id":"s204","question":"آخر مرة شفت دينهو كانت إمتى؟","requires":[]},{"answer":"استنى. ممكن أكون لخبطت في الساعة، الليلة كانت زحمة وأنا كنت تعبان. اللي فاكره قلته، ومكنتش بحاول أخبّي حاجة.","id":"s205","question":"الفانوس كان شغّال، ووقت الوفاة قبل ما يطفي.","requires":["E01","E05"]},{"answer":"آه، دخلت معاه المخزن. كان بينا موضوع عاوزين نخلصه، ومكنتش عايز حد يفتكرني آخر واحد شافه فسكتّ. بس الصورة بتقول إني كنت جنبه، ما بتقولش أنا عملت إيه جوه.","id":"s206","question":"الصورة جايباك داخل المخزن معاه.","requires":["E06"]},{"answer":"نسخة الحسابات كانت معاه وكان هيطلّعها الصبح. طلبت أقابله لوحدنا عند المخزن عشان آخدها، واتخانقنا جامد. حكاية الفانوس كانت كدبة مني. باقي الكلام إنت شايفه قدامك، ومش هزوّد.","id":"s207","question":"حسابات الرحلة والتسجيل، هترد عليهم إزاي؟","requires":["E07","E08"]},{"answer":"لأ. لما شفت الحامل متحرك افتكرته بيصوّر السما زي الجدول. دينهو كان سابقني بخطوة من أول الليلة، والكاميرا والرسالة كانوا اتظبطوا قبل ما أدخل المخزن. ده اللي وجعني أكتر من أي حاجة، إني دخلت وأنا فاكر إني اللي ماسك الخيط.","id":"s214","question":"رسالة دينهو لنفسه قبل ٩:٣٠. كنت عارف إنه مجهّز؟","requires":["E10"]}],"job":"مندوب مبيعات","name":"باسم"},{"id":"abdo","interviews":[{"answer":"استخدم شغل صوت بتاعي في لقطات الرحلة من غير ما يكتب اسمي. كلمته مرتين ومردّش. وبعدها بشوية رجع سألني على نفس المقطع ده وقال لازم أعرف توقيته الظبط. كنت مستني حقي، مش موته. وفي الوقت ده كنت قاعد مع عمر في المقابلة.","id":"s208","question":"كنت متضايق من دينهو ليه؟","requires":[]},{"answer":"سلّمت الكارت الأصلي بتاع التسجيل. التقرير بيقول متصل من غير قطع، والوقت متراجع على صورة الموبايل. ما تصدقنيش عشان بقول، صدّق الملف.","id":"s209","question":"تسجيل المقابلة ممكن يكون متمنتج؟","requires":["E09"]},{"answer":"لأ، مفيش تبديل. باسم لابس نفس الجاكيت اللي عليه الرقعة من قبل المقابلة لحد ما لقينا دينهو. ده اللي شفته بعيني ومش هقول أكتر منه.","id":"s210","question":"شفت تبديل جاكيتات؟","requires":["E06"]}],"job":"موظف في مكتب حكومي","name":"عبده"},{"id":"ahmed","interviews":[{"answer":"لأ، ماشفتش اللي حصل. كنت برا المخيم. اللي أعرفه بعد ما رجعت هو كلام اتقال لي، وده مش شهادة على اللي حصل.","id":"s211","question":"إنت شفت اللي حصل؟","requires":[]},{"answer":"الجهاز بتاع نقطة الاتصال مستقل عن موبايلاتنا. سجله بيقول إني وصلت ٩:٤٧ وفضلت في مكالمة فيديو مع سلامة لحد ٩:٥٧. والطريق من المخيم ليها خمس دقايق على الأقل، يعني مكنتش في الممر وقت الصورة.","id":"s212","question":"إيه اللي يثبت مكانك؟","requires":["E04"]},{"answer":"باسم قالي إن دينهو وقع لما النور فصل. بس التقرير بيحدد الوفاة قبل ١٠:٠٠ والمؤقّت طفّى الفانوس في معاده، فالحكاية مش راكبة. أنا مش طبيب، بس فرق الوقت واضح.","id":"s213","question":"ليه كلام باسم وقف معاك؟","requires":["E01","E05"]}],"job":"موظف كول سنتر في شركة أثاث","name":"أحمد هيصا"}],"continuity":[{"after":["s206","s207"],"answer":"أنا قلت حكاية الفانوس في الأول. بعد الصورة قلتلك إني دخلت مع دينهو، ومش هارجع أقول إني كنت عند الفانوس.","case":"002","suspect":"bassem","topic":"s204"}],"evidence":{"E01":[],"E02":[],"E03":[],"E04":[],"E05":["E01"],"E06":["E02","E03"],"E07":["E01","E02","E06"],"E08":["E02"],"E09":["E04","E05"],"E10":["E07","E08"]},"killer":"باسم","required":["E06","E07","E08"]},"003":{"characters":[{"id":"hani","interviews":[{"answer":"طلب ينقل مسؤولية الرحلات لحد تاني. أنا زعلت، بس زعلي مش معناه إني دخلت له الغرفة. سألني كمان إذا كنت بميّز تلات دقات قبل الكلام. قال علامة عشان النسخ ما تتلخبطش.","id":"b301","question":"كنت مختلف مع عادل ليه؟","requires":[]},{"answer":"أنا سمعت الصوت في السماعة بس. ما شفتوش. لو التقرير بيقول التسجيل قديم يبقى استنتاجي الأول غلط.","id":"b302","question":"سمعت صوته، يبقى كان عايش؟","requires":["E03","E05"]},{"answer":"الكاميرا وحسن. ما تعتمدش على إننا بنأكد لبعض، شوف التسجيل نفسه.","id":"b303","question":"مين يراجع حكاية السطح؟","requires":["E04"]}],"job":"قبطان المركب","name":"هاني مسعود"},{"id":"dalia","interviews":[{"answer":"في غرفة الماكينات من تسعة إلا تلت لحد تسعة. ما دخلتش غرفة عادل.","id":"b304","question":"كنتي فين قبل الاستغاثة؟","requires":[]},{"answer":"عشان فحص الصيانة. العهدة باسمي، بس ده مش معناه إني عملت حاجة.","id":"b305","question":"نسخة M2 كانت معاكي ليه؟","requires":["E02"]},{"answer":"كنت عايزة أأخر وقت اكتشاف اللي حصل. آه، الملف القديم أنا اللي حطّيته. مش هقول إن الصوت كان مباشر.","id":"b306","question":"إنتِ اللي حمّلتي تسجيل الاستغاثة؟","requires":["E06"]},{"answer":"عادل كان ناوي يسلّم الحسابات. دخلت له عشان الورق. أنا كذبت عن مكاني، ومفيش عندي تفسير تاني لدخولي وخروجي.","id":"b307","question":"الكاميرا والفواتير بيقولوا إيه؟","requires":["E07","E08"]},{"answer":"أنا اخترت الملف عشان صوته، ماخدتش بالي من علامة النسخة. كنت بحاول أزوّق وقت اللي حصل، فذيعت بنفس إيدي العلامة اللي ربطت التسجيل بالمراجعة اللي كنت عايزة أخبيها. ده مش معناه إنه كان عايش وقت الإذاعة.","id":"b314","question":"ليه علامة المراجعة في الاستغاثة اللي اخترتيها؟","requires":["E05","E06","E08"]}],"job":"مهندسة الصيانة","name":"داليا أمين"},{"id":"nagla","interviews":[{"answer":"أجور متأخرة. كنت هسيب الشغل بعد الرحلة. بس أنا في المطبخ، وسلّمت التسجيل الأصلي للتحقيق.","id":"b308","question":"كان بينك وبين عادل حساب قديم؟","requires":[]},{"answer":"تصوير محلي متفق عليه لفيديو وصفة الرحلة. المحضر راجع استمراره ووقته. مش عشان أنا قلت كاميرا يبقى كفاية.","id":"b309","question":"ليه كاميرا في المطبخ؟","requires":["E09"]},{"answer":"لأ. سمعت السماعة وأنا في المطبخ. ما شفتهوش بعد ما دخل غرفة الخرائط.","id":"b310","question":"شفتي عادل وهو بيستغيث؟","requires":["E03"]}],"job":"مسؤولة الضيافة","name":"نجلاء سامي"},{"id":"hassan","interviews":[{"answer":"شفت هاني على السطح وسمعت صوت في السماعة. ما شفتش عادل وهو بيتكلم. فرق كبير بين الاتنين.","id":"b311","question":"إيه اللي شفته بنفسك؟","requires":[]},{"answer":"المركب راسي، بس الأهم كاميرات المداخل ومحضر المعاينة. مفيش صعود أو نزول ولا ممر تاني في الفترة. البحر لوحده مش حجة.","id":"b312","question":"ليه ما يكونش حد من بره؟","requires":["E07"]},{"answer":"أنا من الجهاز المستقل الساعة تسعة وربع. البلاغ الحقيقي بعد اكتشاف الوفاة، مش التسجيل اللي اتسمع الساعة تسعة.","id":"b313","question":"مين بلّغ النجدة؟","requires":["E03","E05"]}],"job":"مرشد الرحلة وشاهد","name":"حسن عبد الرحيم"}],"continuity":[{"after":["b306","b307"],"answer":"أنا قلت غرفة الماكينات في الأول. بعد المواجهة قلتلك إني كنت عند لوحة الخدمة، ومش هارجع أنكر مكاني اللي في المحضر.","case":"003","suspect":"dalia","topic":"b304"}],"evidence":{"E01":[],"E02":[],"E03":[],"E04":[],"E05":["E03"],"E06":["E03","E05"],"E07":["E01","E02","E06"],"E08":["E02"],"E09":["E04","E07"]},"killer":"داليا أمين","required":["E06","E07","E08"]}}$catalog$::jsonb$cat$;
revoke all on function public.balagh_catalog() from public,anon,authenticated;

create or replace function public.balagh_action(s jsonb, action text, args jsonb, cat jsonb)
returns jsonb language plpgsql set search_path=public,pg_temp as $fn$
declare ch jsonb; q jsonb; entry jsonb; turn jsonb; topic text; answer text; history jsonb; rule jsonb;
 now_seconds numeric:=extract(epoch from clock_timestamp());
begin
 if s->>'finished'='true' then raise exception 'التحقيق بتاعك خلص'; end if;
 if action='inspect' then
  if not (cat->'evidence') ? coalesce(args->>'evidence','') then raise exception 'الدليل مش موجود'; end if;
  if not (s->'discovered') @> coalesce(cat->'evidence'->(args->>'evidence'),'[]'::jsonb) then raise exception 'افحص الأدلة المطلوبة الأول'; end if;
  if not (s->'discovered') ? (args->>'evidence') then s:=jsonb_set(s,'{discovered}',(s->'discovered')||jsonb_build_array(args->>'evidence')); end if;
 elsif action in ('interview','ai') then
  select value into ch from jsonb_array_elements(cat->'characters') where value->>'id'=args->>'suspect';
  if ch is null then raise exception 'اختار شخصية من القضية'; end if;
  topic:=args->>'topic';
  select value into q from jsonb_array_elements(ch->'interviews') where value->>'id'=topic;
  if q is not null and not (s->'discovered') @> coalesce(q->'requires','[]'::jsonb) then raise exception 'بص على أدلة السؤال الأول'; end if;
  history:=coalesce(s->'ai_interviews','[]'::jsonb);
  if action='ai' then
   if length(trim(coalesce(args->>'question',''))) not between 1 and 350 then raise exception 'السؤال من 1 لحد 350 حرف'; end if;
   if jsonb_array_length(history)>=20 then raise exception 'وصلت لحد 20 سؤال'; end if;
   if now_seconds-coalesce((s->>'ai_last_attempt')::numeric,0)<8 then raise exception 'استنى 8 ثواني بين الأسئلة'; end if;
  elsif q is null then raise exception 'السؤال مش موجود'; end if;
  if q is not null then
   entry:=jsonb_build_object('suspect',ch->>'name','question_id',topic,'question',q->>'question','answer',q->>'answer');
   if not exists(select 1 from jsonb_array_elements(s->'interviews') v where v->>'question_id'=topic) then s:=jsonb_set(s,'{interviews}',(s->'interviews')||jsonb_build_array(entry)); end if;
   answer:=q->>'answer';
   for rule in select value from jsonb_array_elements(coalesce(cat->'continuity','[]'::jsonb)) loop
    if rule->>'suspect'=ch->>'id' and rule->>'topic'=topic
       and exists(select 1 from jsonb_array_elements(s->'interviews') v where (rule->'after') ? (v->>'question_id')) then answer:=rule->>'answer'; end if;
   end loop;
  elsif topic='identity' then answer:='أنا '||(ch->>'name')||'، '||(ch->>'job')||'.';
  elsif topic='repeat' then
   select value->>'answer' into answer from jsonb_array_elements(history) with ordinality a(value,n) where value->>'suspect_id'=ch->>'id' order by n desc limit 1;
  elsif topic<>'unknown' then raise exception 'موضوع السؤال مش موجود';
  end if;
  if action='ai' then
   answer:=coalesce(answer,'مش عندي حاجة أضيفها في النقطة دي. اسألني عن اللي قلته أو واجهني بدليل من الملف.');
   turn:=jsonb_build_object('suspect_id',ch->>'id','suspect',ch->>'name','question',args->>'question','topic',topic,'answer',answer);
   s:=s||jsonb_build_object('ai_interviews',history||jsonb_build_array(turn),'ai_last_attempt',now_seconds);
  end if;
 elsif action='hint' then s:=jsonb_set(s,'{hints_used}',to_jsonb((s->>'hints_used')::int+1));
 else raise exception 'تحديث مش مسموح'; end if;
 return s;
end $fn$;
revoke all on function public.balagh_action(jsonb,text,jsonb,jsonb) from public,anon,authenticated;

create or replace function public.balagh_room(op text, code text default '', token text default '', payload jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path=public,extensions,pg_temp as $fn$
declare r public.rooms; p public.players; secret text; person_name text; result jsonb; s jsonb; u jsonb; ukey text; cat jsonb;
 verdict jsonb; selected jsonb; mode text; cid text; tc int; ts int; mx int; want int; best int; cnt int; members int; shared boolean;
 final boolean:=false; newunits jsonb; empty_state jsonb:='{"discovered":[],"interviews":[],"ai_interviews":[],"finished":false,"result":null,"hints_used":0}'::jsonb;
 empty_unit jsonb:='{"investigation":{"discovered":[],"interviews":[],"ai_interviews":[],"finished":false,"result":null,"hints_used":0},"proposal":null,"approvals":[],"rev":0}'::jsonb;
 ok boolean; kc boolean; ec boolean; sus text; i int;
begin
 if op in ('create','join') then
  person_name:=trim(payload->>'name');
  if person_name is null or length(person_name) not between 1 and 30 then raise exception 'اسم اللاعب من 1 لحد 30 حرف'; end if;
  if op='create' then
   mode:=coalesce(payload->>'mode','coop');
   if mode not in ('coop','race','team') then raise exception 'نوع الأوضة مش موجود'; end if;
   cid:=coalesce(payload->>'case','001');
   if not (public.balagh_catalog() ? cid) then raise exception 'القضية مش موجودة'; end if;
   tc:=1; ts:=1;
   if mode='team' then
    tc:=coalesce((payload->>'team_count')::int,2); ts:=coalesce((payload->>'team_size')::int,2);
    if tc not between 2 and 4 or ts not between 1 and 5 or tc*ts>10 then raise exception 'عدد الفرق من 2 لـ 4 وكل فريق من 1 لـ 5، والمجموع 10 بالكتير'; end if;
    mx:=tc*ts;
   else
    mx:=coalesce((payload->>'max_players')::int,2);
    if mx not between 2 and 10 then raise exception 'عدد اللاعبين من 2 لـ 10'; end if;
   end if;
   secret:=upper(encode(extensions.gen_random_bytes(5),'hex'));
   insert into public.rooms(room_code,status,max_players,current_players,mode,case_id,team_count,team_size,started)
     values(secret,'playing',mx,0,mode,cid,tc,ts,mode='coop') returning * into r;
  else
   select * into r from public.rooms where room_code=upper(trim(code)) for update;
   if r.id is null then raise exception 'كود الأوضة مش موجود'; end if;
   if r.current_players>=r.max_players then raise exception 'الأوضة كاملة، استخدم مفتاح رجوعك'; end if;
   if r.status='finished' then raise exception 'التحقيق خلص'; end if;
   if not r.started then null; elsif r.mode<>'coop' then raise exception 'السباق بدأ خلاص ومش بيقبل لاعبين جداد'; end if;
  end if;
  ukey:=case when r.mode='coop' then '0' else null end;
  if r.mode='team' then
   want:=coalesce((payload->>'team')::int,0);
   if want<>0 and want not between 1 and r.team_count then raise exception 'رقم الفريق مش موجود'; end if;
   if want=0 then
    best:=null;
    for i in 1..r.team_count loop
     select count(*) into cnt from public.players where room_code=r.room_code and unit='t'||i;
     if cnt<r.team_size and (best is null or cnt<(select count(*) from public.players where room_code=r.room_code and unit='t'||best)) then best:=i; end if;
    end loop;
    if best is null then raise exception 'كل الفرق كاملة'; end if;
    want:=best;
   else
    select count(*) into cnt from public.players where room_code=r.room_code and unit='t'||want;
    if cnt>=r.team_size then raise exception 'الفريق ده كامل'; end if;
   end if;
   ukey:='t'||want;
  end if;
  secret:=encode(extensions.gen_random_bytes(32),'hex');
  insert into public.players(player_name,room_code,token_hash,role,is_alive,is_ready,unit) values(person_name,r.room_code,encode(extensions.digest(secret,'sha256'),'hex'),'detective',true,true,ukey) returning * into p;
  if ukey is null then update public.players set unit='p'||id where id=p.id returning * into p; end if;
  update public.rooms set current_players=current_players+1,revision=revision+1,host_id=coalesce(host_id,p.id),
    units=case when r.mode='coop' and r.units ? '0' then jsonb_set(r.units,'{0}',(r.units->'0')||'{"proposal":null,"approvals":[]}'::jsonb) else r.units end
    where id=r.id returning * into r;
 else
  if length(token)<>64 then raise exception 'مفتاح الرجوع مش صحيح'; end if;
  select * into p from public.players where token_hash=encode(extensions.digest(token,'sha256'),'hex');
  if p.id is null then raise exception 'مفتاح الرجوع مش صحيح'; end if;
  select * into r from public.rooms where room_code=p.room_code for update;
  select * into p from public.players where id=p.id;
  cat:=public.balagh_catalog()->r.case_id;
  ukey:=p.unit; u:=coalesce(r.units->ukey,empty_unit); s:=u->'investigation';
  shared:=r.mode='coop' or (r.mode='team' and r.team_size>1);
  select count(*) into members from public.players where room_code=r.room_code and unit=ukey;
  if op='notes' then
   if length(coalesce(payload->>'notes',''))>6000 then raise exception 'النوتة حدها 6000 حرف'; end if;
   update public.players set private_notes=coalesce(payload->>'notes','') where id=p.id returning * into p;
  elsif op='start' then
   if r.mode='coop' or r.started then raise exception 'الأوضة بدأت خلاص'; end if;
   if p.id is distinct from r.host_id then raise exception 'اللي عمل الأوضة هو اللي يبدأ'; end if;
   if r.status='finished' then raise exception 'التحقيق خلص'; end if;
   if (select count(distinct unit) from public.players where room_code=r.room_code)<2 then raise exception 'محتاجين فريقين أو لاعبين على الأقل'; end if;
   update public.rooms set started=true,revision=revision+1 where id=r.id returning * into r;
  elsif op in ('inspect','interview','ai','hint') then
   if r.status='finished' then raise exception 'السباق أو التحقيق خلص'; end if;
   if not r.started then raise exception 'استنى صاحب الأوضة يبدأ'; end if;
   if shared and (payload->>'revision')::bigint is distinct from (u->>'rev')::bigint then raise exception 'في تحديث جديد، حدّث الأوضة'; end if;
   s:=public.balagh_action(s,op,payload,cat);
   u:=jsonb_build_object('investigation',s,'proposal',null,'approvals','[]'::jsonb,'rev',(u->>'rev')::bigint+1);
   update public.rooms set units=jsonb_set(units,array[ukey],u),revision=revision+1 where id=r.id returning * into r;
  elsif op in ('propose','accuse','approve') then
   if r.status='finished' or s->>'finished'='true' then raise exception 'قرارك الأخير اتسجل أو السباق خلص'; end if;
   if not r.started then raise exception 'استنى صاحب الأوضة يبدأ'; end if;
   if r.mode='coop' and r.current_players<2 then raise exception 'استنى صاحبك يدخل'; end if;
   if op='approve' then
    if members<2 then raise exception 'الموافقة مش متاحة'; end if;
    if u->'proposal' is null or u->'proposal' is distinct from payload->'proposal' then raise exception 'اقتراح الاتهام اتغيّر، راجعه الأول'; end if;
    if (u->'approvals') @> jsonb_build_array(p.id) then raise exception 'إنت وافقت خلاص'; end if;
    u:=jsonb_set(u,'{approvals}',(u->'approvals')||jsonb_build_array(p.id));
    selected:=u->'proposal'->'evidence'; sus:=u->'proposal'->>'suspect';
    final:=(select coalesce(jsonb_agg(id),'[]'::jsonb) from public.players where room_code=r.room_code and unit=ukey) <@ (u->'approvals');
   else
    if (op='accuse' and members<>1) or (op='propose' and members<2) then raise exception 'الطلب مش لنوع الفريق ده'; end if;
    selected:=payload->'evidence'; sus:=coalesce(payload->>'suspect','');
    if not exists(select 1 from jsonb_array_elements(cat->'characters') c where c.value->>'name'=sus) or jsonb_typeof(selected) is distinct from 'array' then raise exception 'اختار متهم وأدلة'; end if;
    if jsonb_array_length(selected)=0 or jsonb_array_length(selected)>30 or not (s->'discovered') @> selected then raise exception 'اختار أدلة إنت فحصتها'; end if;
    if op='accuse' then final:=true;
    else u:=jsonb_build_object('investigation',s,'proposal',jsonb_build_object('suspect',sus,'evidence',selected),'approvals',jsonb_build_array(p.id),'rev',(u->>'rev')::bigint+1); end if;
   end if;
   if final then
    kc:=sus=cat->>'killer'; ec:=selected @> (cat->'required'); ok:=kc and ec;
    verdict:=jsonb_build_object('success',ok,'killer_correct',kc,'evidence_complete',ec,'suspect',sus,'submitted_evidence',selected);
    u:=jsonb_build_object('investigation',s||jsonb_build_object('finished',true,'result',verdict),'proposal',null,'approvals','[]'::jsonb,'rev',(u->>'rev')::bigint+1);
    newunits:=jsonb_set(r.units,array[ukey],u);
    if r.mode='coop' or ok then
     update public.rooms set units=newunits,status='finished',winner_unit=case when r.mode<>'coop' and ok then ukey else null end,revision=revision+1 where id=r.id returning * into r;
    elsif not exists(select 1 from public.players pl where pl.room_code=r.room_code and coalesce(newunits->pl.unit->'investigation'->>'finished','false')<>'true') then
     update public.rooms set units=newunits,status='finished',revision=revision+1 where id=r.id returning * into r;
    else update public.rooms set units=newunits,revision=revision+1 where id=r.id returning * into r; end if;
   else
    update public.rooms set units=jsonb_set(r.units,array[ukey],u),revision=revision+1 where id=r.id returning * into r;
   end if;
  elsif op<>'read' then raise exception 'طلب مش مسموح'; end if;
 end if;
 update public.players set last_seen=now() where id=p.id;
 ukey:=p.unit; u:=coalesce(r.units->ukey,empty_unit);
 select count(*) into members from public.players where room_code=r.room_code and unit=ukey;
 s:=case when r.mode<>'coop' and not r.started then empty_state else u->'investigation' end;
 select jsonb_build_object('code',r.room_code,'mode',r.mode,'case_id',r.case_id,'status',r.status,'started',r.started,'host',r.host_id,
   'team_count',r.team_count,'team_size',r.team_size,'max_players',r.max_players,'winner_unit',r.winner_unit,'my_unit',p.unit,'unit_size',members,
   'state',s,'revision',r.revision,'urev',coalesce((u->>'rev')::bigint,0),'proposal',u->'proposal','approvals',coalesce(u->'approvals','[]'::jsonb),'me',p.id,'notes',p.private_notes,
   'players',coalesce((select jsonb_agg(jsonb_build_object('id',id,'name',player_name,'unit',unit) order by id) from public.players where room_code=r.room_code),'[]'::jsonb),
   'unit_done',case when r.started then coalesce((select jsonb_object_agg(k,coalesce(v->'investigation'->>'finished','false')='true') from jsonb_each(r.units) e(k,v)),'{}'::jsonb) else '{}'::jsonb end) into result;
 if secret is not null then result:=result||jsonb_build_object('token',secret); end if;
 return result;
end $fn$;
revoke all on function public.balagh_room(text,text,text,jsonb) from public;
grant usage on schema public to anon,authenticated;
grant execute on function public.balagh_room(text,text,text,jsonb) to anon,authenticated;
commit;
