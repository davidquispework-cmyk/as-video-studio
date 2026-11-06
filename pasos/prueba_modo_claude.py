"""Prueba corta del MODO DE CLAUDE (potente / equilibrado / ahorro).

Sin llamar al CLI: se dobla `_una_pasada` y se mira que modelo le llega.
Redirige ESTUDIO_AJUSTES y ESTUDIO_SECRETOS a una carpeta temporal.
"""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix="modo_claude_")
os.environ["ESTUDIO_AJUSTES"] = os.path.join(TMP, "ajustes.json")
os.environ["ESTUDIO_SECRETOS"] = TMP
os.environ.pop("ESTUDIO_MODO_CLAUDE", None)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ajustes      # noqa: E402
import cli_claude   # noqa: E402

FALLOS = []


def igual(visto, esperado, que):
    if visto != esperado:
        FALLOS.append(f"{que}: {visto!r} != {esperado!r}")


llegado = {}


def doble(instruccion, modelo, esfuerzo, *resto):
    llegado["ultimo"] = (modelo, esfuerzo)
    return "ok", {}


cli_claude._una_pasada = doble
cli_claude.cuentas = lambda: [None]

# de fabrica: equilibrado (lo de POR_FASE)
igual(cli_claude.modo_claude(), "equilibrado", "de fabrica")
cli_claude.ejecutar("x", "opus", "xhigh", para="la redaccion del guion")
igual(llegado["ultimo"], ("sonnet", "medium"), "equilibrado guion")
cli_claude.ejecutar("x", "opus", "xhigh", para="la direccion de los planos")
igual(llegado["ultimo"], ("opus", "high"), "equilibrado direccion")

ajustes.guardar({"modo_claude": "ahorro"})
cli_claude.ejecutar("x", "opus", "xhigh", para="la direccion de los planos")
igual(llegado["ultimo"], ("sonnet", "medium"), "ahorro direccion")
cli_claude.ejecutar("x", "opus", "xhigh", para="la reescritura del bloque")
igual(llegado["ultimo"], ("haiku", "low"), "ahorro revision")
cli_claude.ejecutar("x", "haiku", "low", para="contestar en el asistente")
igual(llegado["ultimo"], ("haiku", "low"), "nunca sube")

ajustes.guardar({"modo_claude": "potente"})
cli_claude.ejecutar("x", "opus", "xhigh", para="la redaccion del guion")
igual(llegado["ultimo"], ("opus", "xhigh"), "potente")

try:
    ajustes.guardar({"modo_claude": "gratis"})
    FALLOS.append("acepto un modo que no existe")
except ValueError:
    pass

tabla = cli_claude.tabla_modos()
igual(tabla["puesto"], "potente", "tabla puesto")
igual(len(tabla["fases"]), 13, "fases en la tabla")

if FALLOS:
    print("FALLA\n  " + "\n  ".join(FALLOS))
    sys.exit(1)
print("OK modo de Claude: equilibrado de fabrica, ahorro topa, potente intacto")
