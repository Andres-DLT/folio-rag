# Folio · Chat con tus PDF

Aplicación personal en Python y Streamlit para hacer preguntas sobre uno o varios documentos y rastrear la respuesta hasta el pasaje original. Incluye un manual ficticio de tres páginas para probar la recuperación.

## Ejecutar

Con Python 3.12, desde la carpeta del proyecto:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

En Windows PowerShell, activa el entorno con `.venv\Scripts\Activate.ps1`. Abre la dirección local que imprime Streamlit. Pulsa **Abrir PDF de ejemplo** y pregunta «¿Cada cuánto se voltea el compost?». El pasaje de la página 2 indica que se voltea cada 14 días. Para consultar tus documentos, súbelos, pulsa **Indexar archivos** y elige cuáles incluir en **Consultar en**.

## Activar el RAG con OpenAI y Supabase

1. Crea un proyecto de Supabase y ejecuta `supabase.sql` en su SQL Editor. El script usa pgvector en el esquema `extensions`.
2. Copia `.env.example` a `.env`. Define `OPENAI_API_KEY`, `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` (clave secreta de servidor o service_role).
3. Reinicia Streamlit. La biblioteca mostrará **Motor semántico · OpenAI + Supabase**. Importa tus PDF.

La aplicación envía los fragmentos a OpenAI para calcular embeddings y guarda su texto, metadatos y vectores en Supabase. Al preguntar, envía los pasajes recuperados a OpenAI para redactar la respuesta. Las claves permanecen en el servidor. La biblioteca activa y el historial duran la sesión. Al volver a subir un PDF idéntico, el índice persistente se reutiliza. El esquema está pensado para una biblioteca personal.

## Cómo funciona

| Etapa | Decisión técnica |
|---|---|
| Extracción | pypdf extrae texto página por página. Cada fragmento conserva el nombre, número de página, posición ordinal y SHA-256 del archivo. Los PDF escaneados necesitan OCR previo. |
| Fragmentación | RecursiveCharacterTextSplitter de LangChain intenta conservar párrafos y frases separadas por saltos de línea antes de cortar por espacios. Usa hasta 1.000 caracteres y un solapamiento objetivo de 160 dentro de cada página. El solapamiento ayuda a recuperar contexto en los bordes. Mantener páginas separadas hace precisa la cita, aunque una idea que atraviese dos páginas puede requerir dos pasajes. |
| Embeddings | OpenAIEmbeddings usa text-embedding-3-small con 1.536 dimensiones tanto al indexar como al consultar. Representar ambas entradas en el mismo espacio permite encontrar textos relacionados aunque empleen vocabulario distinto. |
| Recuperación | pgvector filtra por los PDF seleccionados, calcula la distancia coseno exacta y devuelve los primeros k pasajes. La interfaz muestra 1 − distancia. Esa puntuación mide cercanía vectorial y carece de calibración como probabilidad de respuesta correcta. Un k mayor aporta contexto y aumenta el coste de generación. |
| Conversación | Para preguntas de seguimiento, LangChain usa hasta tres intercambios de la misma selección documental para formular una consulta autónoma. GPT-4o-mini recibe la consulta y los pasajes numerados. La aplicación valida que los identificadores de la respuesta existan y muestra la página de cada fuente. |
| Inspección | Abre **Ver recuperación** para comparar la consulta utilizada, los pasajes completos, sus páginas y su similitud con las fuentes que el modelo eligió citar. |

## Demostración y evaluación sin credenciales

El modo local procesa los documentos en memoria. Usa TF-IDF con normalización de acentos y similitud coseno para recuperar por coincidencia léxica. Devuelve el mejor pasaje como cita textual. En este modo conviene formular preguntas autónomas con vocabulario del documento.

```bash
python evaluar.py
```

La evaluación comprueba si la página correcta aparece en primera posición para tres preguntas del manual de ejemplo (Hit@1 por página). Mide la recuperación local sobre ese conjunto pequeño. Para evaluar búsquedas semánticas con tus documentos, prueba una paráfrasis sin términos compartidos, abre los pasajes y contrasta la primera página recuperada con la página esperada.

## Despliegue público gratuito

En Streamlit Community Cloud, conecta el repositorio público de GitHub, selecciona la rama `main`, el archivo `app.py` y Python 3.12. Deja los secretos vacíos para publicar el modo TF-IDF sin consumo de API. Tras desplegar, comprueba el acceso desde una ventana privada y prueba el PDF de ejemplo. El servicio gratuito puede suspender la aplicación por inactividad y reactivarla en una visita posterior.
