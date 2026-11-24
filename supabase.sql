-- Ejecutar en el SQL Editor del proyecto Supabase.
create extension if not exists vector with schema extensions;

create table if not exists public.folio_fragmentos (
  doc_id text not null,
  ordinal integer not null,
  nombre text not null,
  pagina integer not null,
  texto text not null,
  embedding extensions.vector(1536) not null,
  primary key (doc_id, ordinal)
);
alter table public.folio_fragmentos enable row level security;
revoke all on public.folio_fragmentos from anon, authenticated, public;
grant select, insert on public.folio_fragmentos to service_role;

create or replace function public.folio_existe(documento text)
returns boolean language sql stable as $$
  select exists(select 1 from public.folio_fragmentos where doc_id = documento);
$$;

create or replace function public.folio_guardar(filas jsonb)
returns void language sql as $$
  insert into public.folio_fragmentos (doc_id, ordinal, nombre, pagina, texto, embedding)
  select doc_id, ordinal, nombre, pagina, texto, embedding::text::extensions.vector
  from jsonb_to_recordset(filas) as f(doc_id text, ordinal int, nombre text, pagina int,
                                      texto text, embedding jsonb)
  on conflict (doc_id, ordinal) do nothing;
$$;

create or replace function public.folio_buscar(consulta extensions.vector, documentos text[], cantidad int)
returns table(doc_id text, nombre text, pagina int, ordinal int, texto text, similitud double precision)
language sql stable as $$
  select f.doc_id, f.nombre, f.pagina, f.ordinal, f.texto,
         1 - (f.embedding operator(extensions.<=>) consulta) as similitud
  from public.folio_fragmentos f
  where f.doc_id = any(documentos)
  order by f.embedding operator(extensions.<=>) consulta, f.doc_id, f.ordinal
  limit least(greatest(cantidad, 1), 8);
$$;

revoke all on function public.folio_existe(text), public.folio_guardar(jsonb),
  public.folio_buscar(extensions.vector,text[],int) from public, anon, authenticated;
grant execute on function public.folio_existe(text), public.folio_guardar(jsonb),
  public.folio_buscar(extensions.vector,text[],int) to service_role;
