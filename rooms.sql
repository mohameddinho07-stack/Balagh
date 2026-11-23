-- Additive two-player prototype. Existing columns and data are preserved.
begin;
create schema if not exists extensions;
create extension if not exists pgcrypto with schema extensions;
alter table public.rooms add column if not exists investigation jsonb not null default '{"discovered":[],"interviews":[],"ai_interviews":[],"finished":false,"result":null,"hints_used":0}'::jsonb;
alter table public.rooms add column if not exists revision bigint not null default 0;
alter table public.rooms add column if not exists proposal jsonb;
alter table public.rooms add column if not exists approvals jsonb not null default '[]'::jsonb;
alter table public.players add column if not exists token_hash text;
alter table public.players add column if not exists private_notes text not null default '';
alter table public.players add column if not exists last_seen timestamptz not null default now();
create unique index if not exists balagh_room_code_unique on public.rooms(room_code);
create unique index if not exists balagh_player_token_unique on public.players(token_hash);
alter table public.rooms enable row level security;
alter table public.players enable row level security;
revoke all on public.rooms,public.players from anon,authenticated;

alter table public.rooms add column if not exists mode text not null default 'coop';
alter table public.rooms add column if not exists winner_id bigint;
alter table public.players add column if not exists investigation jsonb not null default '{"discovered":[],"interviews":[],"ai_interviews":[],"finished":false,"result":null,"hints_used":0}'::jsonb;

create or replace function public.balagh_action(s jsonb, action text, args jsonb)
returns jsonb language plpgsql set search_path=public,pg_temp as $fn$
declare catalog jsonb := $catalog${"evidence": ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09"], "characters": [{"id": "aser", "name": "آسر منصور", "age": 46, "job": "روائي جرائم", "public_info": "صاحب نادر من زمان.", "personality": "هادي وبيوزن الكلمة قبل ما يقولها.", "secret": "كان بيبتز نادر.", "alibi": "بيقول كان في مطعم الفندق.", "interviews": [{"id": "a1", "question": "إنت ونادر علاقتكم كانت إيه؟", "answer": "بص يا سيدي، إحنا صحاب من زمان. بس حقوق رواية دخلت بينا، ومن ساعتها الدنيا ما بقتش زي الأول."}, {"id": "a2", "question": "كنت فين من ⁧⁦10:50⁩ بليل⁩ لحد ⁧⁦11:25⁩ بليل⁩؟", "answer": "في مطعم الفندق. الفاتورة موجودة، والجرسون يقدر يقولك. هتلاقي ده في ملف مراجعة الكلام."}, {"id": "a3", "question": "يعني الموضوع وصل إنك تبتزّه؟", "answer": "آه، طلبت فلوس عشان أسكت عن سر قديم. مش هجمّلها. بس إني عملت كده حاجة، وإني أدخل جناحه وأقتله حاجة تانية. أنا ما دخلتش هناك الليلة دي."}]}, {"id": "layla", "name": "ليلى الديب", "age": 34, "job": "عازفة بيانو", "public_info": "كانت بتعزف في حفلة في الفندق.", "personality": "بتتوتر وبتتردد قبل ما ترد.", "secret": "كانت مرتبطة بنادر في السر.", "alibi": "بتقول كانت في قاعة الحفلة.", "interviews": [{"id": "l1", "question": "كنتِ تعرفي نادر بعيد عن الشغل؟", "answer": "أيوه... كنا مرتبطين. وما كنتش عايزة حد يعرف. أنا متوترة عشان كده، مش عشان اللي في دماغك."}, {"id": "l2", "question": "كنتِ فين وقت الزيارة اللي بالليل دي؟", "answer": "على البيانو قدام الناس. الحفلة متصوّرة من غير تقطيع، هتلاقوا التسجيل في ملف مراجعة الكلام."}, {"id": "l3", "question": "طب والساعة اللي وقفت دي حكايتها إيه؟", "requires": ["E05"], "answer": "أنا شفت ساعته بتقف قبل كده، بس ده مش دليل على حاجة. بصّ على فحص البطارية، هو اللي هيفيدك، مش تخميني أنا."}]}, {"id": "youssef", "name": "يوسف بيومي", "age": 51, "job": "دكتور نفسي", "public_info": "كان في الفندق الليلة دي.", "personality": "هادي وبيحسب ردوده.", "secret": "سمع صوت نادين في المكالمة واتردد يقوله.", "alibi": "بيقول إنه كان على التليفون وقت الجريمة.", "interviews": [{"id": "y1", "question": "كنت متعصّب ليه؟", "answer": "كان معاه ورق بتاعي ورفض يرجّعه. اتخانقنا، ده حصل. وأنا قلت للمحقق إني كنت على التليفون وقت الجريمة."}, {"id": "y2", "question": "مكالمتك خلصت ⁧⁦11:22⁩ بليل⁩، ونادر مات ⁧⁦11:42⁩ بليل⁩. إزاي يعني؟", "requires": ["E01", "E03"], "answer": "عندك حق، أنا لخبطت في المعادين. المكالمة خلصت ⁧⁦11:22⁩ بليل⁩، فمش هقدر أقول إنها تثبت أنا كنت فين الساعة ⁧⁦11:42⁩ بليل⁩."}, {"id": "y3", "question": "سمعت صوت حد معاه في المكالمة؟", "requires": ["E03"], "answer": "سمعت صوت ست، افتكرته صوت نادين، بتقول إن الضيافة جاهزة. بس أنا ما شفتهاش بعيني. خُدها حاجة تراجع وراها، مش دليل أكيد."}]}, {"id": "nadine", "name": "نادين مراد", "age": 29, "job": "صحفية تحقيقات", "public_info": "كانت بتدوّر ورا نادر وفي ملفاته.", "personality": "حاضرة وسريعة في الرد.", "secret": "قدّمت الكوباية الملوثة وخبّت حكاية الزيارة.", "alibi": "بتقول إنها مشيت ⁧⁦10:00⁩ بليل⁩.", "interviews": [{"id": "n1", "question": "مشيتي من الفندق إمتى؟", "answer": "الساعة ⁧⁦10:00⁩ بليل⁩ بالظبط. كلمته قبلها في موضوع شغل، وبعد كده ما شفتوش."}, {"id": "n2", "question": "إمضتك وكلام الموظفة بيقولوا إنك كنتِ عنده ⁧⁦10:58⁩ بليل⁩. إزاي؟", "requires": ["E06"], "answer": "أيوه رجعت شوية، وما كنتش عايزة أدخل في الحكاية دي. وقدّمت له الكوباية، ما أنكرتش ده. بس زيارتي ليه مش معناها إني قتلته."}, {"id": "n3", "question": "طب تفسّري إزاي نتيجة الكوباية مع دفتر الزيارة؟", "requires": ["E06", "E07"], "answer": "التحليل؟ ما عنديش تفسير ليه. أنا كنت هناك وقدّمت له الكوباية، دي حقيقة. بس مش هألفلك حكاية تانية وأقعد أزود كلام من غير دليل."}, {"id": "n4", "question": "نادر كان بيهددك؟", "requires": ["E08"], "answer": "آه، كان بيهدد شغلي وحياتي الخاصة. وطبعًا كنت خايفة ومتعصّبة. بس ما تمسكش الجملة دي وتقول إني اعترفت بالقتل."}]}]}$catalog$::jsonb;
 ch jsonb; q jsonb; entry jsonb; turn jsonb; topic text; answer text; history jsonb; now_seconds numeric:=extract(epoch from clock_timestamp());
begin
 if s->>'finished'='true' then raise exception 'التحقيق بتاعك خلص'; end if;
 if action='inspect' then
  if not (catalog->'evidence') ? coalesce(args->>'evidence','') then raise exception 'الدليل مش موجود'; end if;
  if not (s->'discovered') ? (args->>'evidence') then s:=jsonb_set(s,'{discovered}',(s->'discovered')||jsonb_build_array(args->>'evidence')); end if;
 elsif action in ('interview','ai') then
  select value into ch from jsonb_array_elements(catalog->'characters') where value->>'id'=args->>'suspect';
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
   if topic='n1' and exists(select 1 from jsonb_array_elements(s->'interviews') v where v->>'question_id'='n2') then answer:='أنا قلت عشرة بالليل في الأول، بس خلاص قلتلك إني رجعت زيارة وقدّمت له الكوباية. مش هارجع أنكر الزيارة تاني.'; end if;
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
revoke all on function public.balagh_action(jsonb,text,jsonb) from public,anon,authenticated;

create or replace function public.balagh_room(op text, code text default '', token text default '', payload jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path=public,extensions,pg_temp as $fn$
declare r public.rooms; p public.players; secret text; person_name text; result jsonb; s jsonb; verdict jsonb; selected jsonb; valid boolean; race_closed boolean;
begin
 if op in ('create','join') then
  person_name:=trim(payload->>'name');
  if person_name is null or length(person_name) not between 1 and 30 then raise exception 'اسم اللاعب من 1 لحد 30 حرف'; end if;
  if op='create' then
   if coalesce(payload->>'mode','coop') not in ('coop','race') then raise exception 'نوع الأوضة مش موجود'; end if;
   secret:=upper(encode(extensions.gen_random_bytes(5),'hex'));
   insert into public.rooms(room_code,status,max_players,current_players,mode) values(secret,'playing',2,0,coalesce(payload->>'mode','coop')) returning * into r;
  else
   select * into r from public.rooms where room_code=upper(trim(code)) for update;
   if r.id is null then raise exception 'كود الأوضة مش موجود'; end if;
   if r.current_players>=2 then raise exception 'الأوضة كاملة، استخدم مفتاح رجوعك'; end if;
   if r.status='finished' then raise exception 'التحقيق خلص'; end if;
  end if;
  secret:=encode(extensions.gen_random_bytes(32),'hex');
  insert into public.players(player_name,room_code,token_hash,role,is_alive,is_ready) values(person_name,r.room_code,encode(extensions.digest(secret,'sha256'),'hex'),'detective',true,true) returning * into p;
  update public.rooms set current_players=current_players+1,revision=revision+1 where id=r.id returning * into r;
 else
  if length(token)<>64 then raise exception 'مفتاح الرجوع مش صحيح'; end if;
  select * into p from public.players where token_hash=encode(extensions.digest(token,'sha256'),'hex');
  if p.id is null then raise exception 'مفتاح الرجوع مش صحيح'; end if;
  select * into r from public.rooms where room_code=p.room_code for update;
  -- Re-read player only AFTER locking room: concurrent requests share one order.
  select * into p from public.players where id=p.id;
  s:=case when r.mode='race' then p.investigation else r.investigation end;
  if op='notes' then
   if length(coalesce(payload->>'notes',''))>6000 then raise exception 'النوتة حدها 6000 حرف'; end if;
   update public.players set private_notes=coalesce(payload->>'notes','') where id=p.id returning * into p;
  elsif op in ('inspect','interview','ai','hint') then
   if r.status='finished' then raise exception 'السباق أو التحقيق خلص'; end if;
   if r.mode='race' and r.current_players<>2 then raise exception 'استنى صاحبك يدخل عشان تبدأوا سوا'; end if;
   if r.mode='coop' and (payload->>'revision')::bigint is distinct from r.revision then raise exception 'في تحديث جديد، حدّث الأوضة'; end if;
   s:=public.balagh_action(s,op,payload);
   if r.mode='race' then update public.players set investigation=s where id=p.id returning * into p;
   else update public.rooms set investigation=s,proposal=null,approvals='[]'::jsonb where id=r.id; end if;
   update public.rooms set revision=revision+1 where id=r.id returning * into r;
  elsif op in ('propose','accuse') then
   if r.current_players<>2 then raise exception 'استنى صاحبك يدخل'; end if;
   if r.status='finished' or s->>'finished'='true' then raise exception 'قرارك الأخير اتسجل أو السباق خلص'; end if;
   selected:=payload->'evidence';
   if coalesce(payload->>'suspect','') not in ('آسر منصور','ليلى الديب','يوسف بيومي','نادين مراد') or jsonb_typeof(selected) is distinct from 'array' then raise exception 'اختار متهم وأدلة'; end if;
   if jsonb_array_length(selected)=0 or not (s->'discovered') @> selected or not '["E01","E02","E03","E04","E05","E06","E07","E08","E09"]'::jsonb @> selected then raise exception 'اختار أدلة إنت فحصتها'; end if;
   if r.mode='race' and op='accuse' then
    valid:=payload->>'suspect'='نادين مراد' and selected @> '["E06","E07","E08"]'::jsonb;
    verdict:=jsonb_build_object('success',valid,'killer_correct',false,'suspect',payload->>'suspect','submitted_evidence',selected);
    update public.players set investigation=s||jsonb_build_object('finished',true,'result',verdict) where id=p.id returning * into p;
    if valid then update public.rooms set winner_id=p.id,status='finished' where id=r.id;
    elsif not exists(select 1 from public.players where room_code=r.room_code and investigation->>'finished'='false') then update public.rooms set status='finished' where id=r.id; end if;
    update public.rooms set revision=revision+1 where id=r.id returning * into r;
   elsif r.mode='coop' and op='propose' then
    update public.rooms set proposal=jsonb_build_object('suspect',payload->>'suspect','evidence',selected),approvals=jsonb_build_array(p.id),revision=revision+1 where id=r.id returning * into r;
   else raise exception 'الطلب مش لنوع الأوضة دي'; end if;
  elsif op='approve' then
   if r.mode<>'coop' or r.status='finished' then raise exception 'الموافقة مش متاحة'; end if;
   if r.proposal is null or r.proposal is distinct from payload->'proposal' then raise exception 'اقتراح الاتهام اتغيّر، راجعه الأول'; end if;
   if r.approvals @> jsonb_build_array(p.id) then raise exception 'إنت وافقت خلاص'; end if;
   s:=r.investigation||jsonb_build_object('finished',true,'result',jsonb_build_object('suspect',r.proposal->>'suspect','submitted_evidence',r.proposal->'evidence','killer_correct',r.proposal->>'suspect'='نادين مراد','evidence_complete',(r.proposal->'evidence') @> '["E06","E07","E08"]'::jsonb,'success',r.proposal->>'suspect'='نادين مراد' and (r.proposal->'evidence') @> '["E06","E07","E08"]'::jsonb));
   update public.rooms set investigation=s,approvals=approvals||jsonb_build_array(p.id),status='finished',revision=revision+1 where id=r.id returning * into r;
  elsif op<>'read' then raise exception 'طلب مش مسموح'; end if;
 end if;
 update public.players set last_seen=now() where id=p.id;
 s:=case when r.mode='race' then p.investigation else r.investigation end;
 if r.mode='race' and r.current_players<2 then s:='{"discovered":[],"interviews":[],"ai_interviews":[],"finished":false,"result":null,"hints_used":0}'::jsonb; end if;
 select jsonb_build_object('code',r.room_code,'mode',r.mode,'status',r.status,'winner',r.winner_id,'state',s,'revision',r.revision,'proposal',case when r.mode='coop' then r.proposal else null end,'approvals',case when r.mode='coop' then r.approvals else '[]'::jsonb end,'me',p.id,'notes',p.private_notes,'players',coalesce((select jsonb_agg(jsonb_build_object('id',id,'name',player_name) order by id) from public.players where room_code=r.room_code),'[]'::jsonb)) into result;
 if secret is not null then result:=result||jsonb_build_object('token',secret); end if;
 return result;
end $fn$;
revoke all on function public.balagh_room(text,text,text,jsonb) from public;
grant usage on schema public to anon,authenticated;
grant execute on function public.balagh_room(text,text,text,jsonb) to anon,authenticated;
commit;
