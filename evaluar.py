"""Mide aciertos del primer pasaje en un conjunto pequeño y reproducible."""
from pathlib import Path
from rag import buscar_local, fragmentar

ruta = Path(__file__).parent / "ejemplos/manual_huerto.pdf"
trozos = fragmentar(ruta.read_bytes(), ruta.name)
casos = [
    ("¿Qué días se programa el riego?", 1),
    ("¿Cada cuánto se voltea el compost?", 2),
    ("¿Quién es responsable del inventario?", 3),
]
aciertos = 0
for pregunta, esperada in casos:
    resultado = buscar_local(pregunta, trozos, 1)
    pagina = resultado[0]["pagina"] if resultado else None
    aciertos += pagina == esperada
    print(f"{pregunta}  →  página {pagina} (esperada: {esperada})")
print(f"Hit@1 por página: {aciertos}/{len(casos)}")
raise SystemExit(aciertos != len(casos))
