-- Encrypted snapshots only. Plaintext roles/tokens never enter this table.
create table if not exists public.balagh_night_snapshots (
 code text primary key check (code ~ '^[A-F0-9]{10}$'),
 capability_hash text not null,
 revision bigint not null default 1,
 snapshot text not null,
 updated_at timestamptz not null default now()
);
alter table public.balagh_night_snapshots enable row level security;
revoke all on public.balagh_night_snapshots from anon, authenticated;
create or replace function public.balagh_night_store(op text, code text, capability text, expected bigint default 0, snapshot text default '')
returns jsonb language plpgsql security definer set search_path = public, extensions as $$
declare r public.balagh_night_snapshots%rowtype; h text;
begin
 if code !~ '^[A-F0-9]{10}$' or capability !~ '^[a-f0-9]{64}$' then raise exception 'invalid request'; end if;
 h := encode(extensions.digest(capability,'sha256'),'hex');
 if op='create' then
   if length(snapshot)<100 or length(snapshot)>200000 then raise exception 'invalid snapshot'; end if;
   insert into public.balagh_night_snapshots(code,capability_hash,snapshot) values(code,h,snapshot) on conflict do nothing;
   if found then return jsonb_build_object('ok',true,'revision',1); end if;
   return jsonb_build_object('ok',false);
 end if;
 select * into r from public.balagh_night_snapshots n where n.code=balagh_night_store.code for update;
 if not found or r.capability_hash<>h then return jsonb_build_object('found',false); end if;
 if op='read' then return jsonb_build_object('found',true,'revision',r.revision,'snapshot',r.snapshot); end if;
 if op='commit' then
   if r.revision<>expected then return jsonb_build_object('ok',false); end if;
   if length(snapshot)<100 or length(snapshot)>200000 then raise exception 'invalid snapshot'; end if;
   update public.balagh_night_snapshots n set snapshot=balagh_night_store.snapshot, revision=r.revision+1, updated_at=now() where n.code=balagh_night_store.code;
   return jsonb_build_object('ok',true,'revision',r.revision+1);
 end if;
 raise exception 'invalid operation';
end $$;
revoke all on function public.balagh_night_store(text,text,text,bigint,text) from public;
grant execute on function public.balagh_night_store(text,text,text,bigint,text) to anon, authenticated;
