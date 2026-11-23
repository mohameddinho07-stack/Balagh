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

create or replace function public.balagh_room(op text, code text default '', token text default '', payload jsonb default '{}'::jsonb)
returns jsonb language plpgsql security definer set search_path = public,extensions,pg_temp as $$
declare r public.rooms; p public.players; secret text; person_name text; result jsonb; next_state jsonb;
begin
 if op in ('create','join') then
  person_name := trim(payload->>'name');
  if person_name is null or length(person_name) not between 1 and 30 then raise exception 'اسم اللاعب من 1 لحد 30 حرف'; end if;
  if op='create' then
   secret := upper(encode(extensions.gen_random_bytes(5),'hex'));
   insert into public.rooms(room_code,status,max_players,current_players) values(secret,'playing',2,0) returning * into r;
  else
   select * into r from public.rooms where room_code=upper(trim(code)) for update;
   if r.id is null then raise exception 'كود الأوضة مش موجود'; end if;
   if r.current_players >= 2 then raise exception 'الأوضة كاملة، استخدم مفتاح رجوعك لو كنت فيها'; end if;
   if r.investigation->>'finished'='true' then raise exception 'التحقيق خلص'; end if;
  end if;
  secret := encode(extensions.gen_random_bytes(32),'hex');
  insert into public.players(player_name,room_code,token_hash,role,is_alive,is_ready)
  values(person_name,r.room_code,encode(extensions.digest(secret,'sha256'),'hex'),'detective',true,true) returning * into p;
  update public.rooms set current_players=current_players+1 where id=r.id returning * into r;
 else
  if length(token)<>64 then raise exception 'مفتاح الرجوع مش صحيح'; end if;
  select * into p from public.players where token_hash=encode(extensions.digest(token,'sha256'),'hex');
  if p.id is null then raise exception 'مفتاح الرجوع مش صحيح'; end if;
  select * into r from public.rooms where room_code=p.room_code for update;
  if op='notes' then
   if length(coalesce(payload->>'notes',''))>6000 then raise exception 'النوتة طويلة، الحد 6000 حرف'; end if;
   update public.players set private_notes=coalesce(payload->>'notes','') where id=p.id returning * into p;
  elsif op='commit' then
   if (payload->>'revision')::bigint <> r.revision then raise exception 'في تحديث جديد، حدّث الأوضة وجرّب تاني'; end if;
   if r.investigation->>'finished'='true' then raise exception 'التحقيق خلص'; end if;
   next_state := payload->'state';
   if next_state is null or jsonb_typeof(next_state)<>'object' or length(next_state::text)>120000 then raise exception 'تحديث مش سليم'; end if;
   if next_state->>'finished'<>'false' or next_state->'result'<>'null'::jsonb then raise exception 'القرار النهائي محتاج موافقة الاتنين'; end if;
   update public.rooms set investigation=next_state,revision=revision+1,proposal=null,approvals='[]'::jsonb where id=r.id returning * into r;
  elsif op='propose' then
   if r.current_players<>2 then raise exception 'استنى صاحبك يدخل'; end if;
   if r.investigation->>'finished'='true' then raise exception 'التحقيق خلص'; end if;
   if payload->>'suspect' not in ('آسر منصور','ليلى الديب','يوسف بيومي','نادين مراد') or jsonb_typeof(payload->'evidence')<>'array' or jsonb_array_length(payload->'evidence')=0 or not (r.investigation->'discovered') @> (payload->'evidence') then raise exception 'اختار متهم وأدلة فحصتوها'; end if;
   update public.rooms set proposal=jsonb_build_object('suspect',payload->>'suspect','evidence',payload->'evidence'),approvals=jsonb_build_array(p.id),revision=revision+1 where id=r.id returning * into r;
  elsif op='approve' then
   if r.proposal is null or r.proposal <> payload->'proposal' then raise exception 'اقتراح الاتهام اتغيّر، راجعه الأول'; end if;
   if r.approvals @> jsonb_build_array(p.id) then raise exception 'إنت وافقت خلاص، مستني صاحبك'; end if;
   next_state := r.investigation || jsonb_build_object('finished',true,'result',jsonb_build_object('suspect',r.proposal->>'suspect','submitted_evidence',r.proposal->'evidence','killer_correct',r.proposal->>'suspect'='نادين مراد','evidence_complete',(r.proposal->'evidence') @> '["E06","E07","E08"]'::jsonb,'success',r.proposal->>'suspect'='نادين مراد' and (r.proposal->'evidence') @> '["E06","E07","E08"]'::jsonb));
   update public.rooms set investigation=next_state,approvals=approvals||jsonb_build_array(p.id),status='finished',revision=revision+1 where id=r.id returning * into r;
  elsif op<>'read' then raise exception 'طلب مش معروف';
  end if;
 end if;
 update public.players set last_seen=now() where id=p.id;
 select jsonb_build_object('code',r.room_code,'state',r.investigation,'revision',r.revision,'proposal',r.proposal,'approvals',r.approvals,
 'me',p.id,'notes',p.private_notes,'players',coalesce((select jsonb_agg(jsonb_build_object('id',id,'name',player_name,'last_seen',last_seen) order by id) from public.players where room_code=r.room_code),'[]'::jsonb)) into result;
 if secret is not null then result:=result||jsonb_build_object('token',secret); end if;
 return result;
end $$;
revoke all on function public.balagh_room(text,text,text,jsonb) from public;
grant usage on schema public to anon,authenticated;
grant execute on function public.balagh_room(text,text,text,jsonb) to anon,authenticated;
commit;
