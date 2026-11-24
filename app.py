import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag import Nube, buscar_local, fragmentar

load_dotenv()
st.set_page_config(page_title="Folio · Chat documental", page_icon="📖", layout="centered")
st.markdown("""
<style>
.stApp {background:#f9f8f3;color:#223b33}
[data-testid="stSidebar"] {background:#efefe6}
h1,h2,h3 {font-family:Georgia,serif!important;font-weight:normal!important}
h1 {font-size:3.1rem!important;letter-spacing:-.045em}
[data-testid="stChatMessage"] {background:#f1f1e9;border-radius:12px}
</style>""", unsafe_allow_html=True)
s = st.session_state
s.setdefault("docs", {})
s.setdefault("mensajes", [])
s.setdefault("seleccion", [])
claves = [os.getenv(k) for k in ("OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY")]
cloud = all(claves)
motor = Nube(claves[1], claves[2]) if cloud else None


def importar(data, nombre):
    trozos = fragmentar(data, nombre)
    llave = trozos[0]["doc_id"]
    if llave in s.docs:
        return
    if motor:
        motor.indexar(trozos)
    s.docs[llave] = trozos
    s.seleccion = [*s.seleccion, llave]


with st.sidebar:
    st.header("Biblioteca")
    archivos = st.file_uploader("Añadir documentos", type="pdf", accept_multiple_files=True)
    muestra = st.button("Abrir PDF de ejemplo", use_container_width=True)
    procesar = st.button("Indexar archivos", disabled=not archivos, use_container_width=True)
    if muestra or procesar:
        ejemplo = Path(__file__).parent / "ejemplos/manual_huerto.pdf"
        lote = [(ejemplo.name, ejemplo.read_bytes())] if muestra else [(a.name, a.getvalue()) for a in archivos]
        with st.spinner("Fragmentando e indexando…"):
            for nombre, data in lote:
                try:
                    importar(data, nombre)
                except ValueError as exc:
                    st.error(str(exc))
                except Exception:
                    st.error(f"No se pudo indexar {nombre}. Revisa el PDF y la conexión del motor.")
    seleccion = st.multiselect("Consultar en", list(s.docs),
                               format_func=lambda x: s.docs[x][0]["nombre"], key="seleccion")
    k = st.slider("Fragmentos por consulta", 1, 8, 4)
    total = sum(len(s.docs[d]) for d in seleccion)
    st.caption(f"{len(seleccion)} documentos seleccionados · {total} fragmentos")
    st.divider()
    st.caption("Motor semántico · OpenAI + Supabase" if cloud else "Motor local · TF-IDF y citas textuales")
    if any(claves) and not cloud:
        st.warning("Configuración parcial. Completa las tres variables para activar OpenAI y Supabase.")

st.title("Folio")
st.markdown("### Conversa con tus documentos")
st.write("Sube un PDF, haz una pregunta y consulta los pasajes que sustentan la respuesta.")


def mostrar(turno):
    with st.chat_message("user"):
        st.write(turno["pregunta"])
    with st.chat_message("assistant"):
        st.write(turno["texto"])
        for i in turno["ids"]:
            h = turno["hits"][i-1]
            st.caption(f"[{i}] {h['nombre']} · pág. {h['pagina']}")
        with st.expander(f"Ver recuperación · {len(turno['hits'])} fragmentos"):
            st.caption("Consulta utilizada")
            st.text(turno["consulta"])
            for i, hit in enumerate(turno["hits"], 1):
                st.caption(f"[{i}] {hit['nombre']} · pág. {hit['pagina']} · coseno {hit['similitud']:.3f}")
                st.text(hit["texto"])


for turno in s.mensajes:
    mostrar(turno)
if not s.mensajes and not seleccion:
    st.info("Añade tu primer documento desde la biblioteca o abre el PDF de ejemplo.")
if not s.mensajes and any(s.docs[d][0]["nombre"] == "manual_huerto.pdf" for d in seleccion):
    st.caption("Prueba con «¿Cada cuánto se voltea el compost?»")
pregunta = st.chat_input("Escribe una pregunta sobre tus PDF…", disabled=not seleccion, max_chars=2000)
if pregunta:
    with st.spinner("Buscando pasajes…"):
        try:
            consulta = pregunta
            if motor:
                historial = [(t["pregunta"], t["texto"]) for t in s.mensajes if t["docs"] == sorted(seleccion)]
                consulta, hits, texto, ids = motor.consultar(pregunta, seleccion, k, historial)
            else:
                hits = buscar_local(consulta, [t for d in seleccion for t in s.docs[d]], k)
                ids = [1] if hits else []
                texto = hits[0]["texto"] if hits else "No encontré pasajes con términos coincidentes."
            turno = dict(pregunta=pregunta, consulta=consulta, hits=hits, texto=texto,
                         ids=ids, docs=sorted(seleccion))
            s.mensajes.append(turno)
            mostrar(turno)
        except Exception:
            st.error("No se pudo completar la consulta. Comprueba la conexión, las claves y el esquema SQL.")
