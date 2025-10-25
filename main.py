# main.py
# Archivo principal que orquesta el análisis y la ejecución.
# Acepta argumentos de línea de comandos para mostrar diferentes fases.

# --- IMPORTACIONES ---
import sys
import argparse
import json
import io
import contextlib

from lexer import lexer
from parser import parser
from semantic import SemanticAnalyzer
from generator import CodeGenerator  # <-- 1. IMPORTAR EL GENERADOR

# ==============================
# FUNCIÓN DE UTILIDAD (print_ast)
# ==============================
def print_ast(node_list, indent=""):
    """
    Imprime el AST de forma legible en la consola.
    Esta versión maneja correctamente listas anidadas (bloques 'program').
    """
    if not isinstance(node_list, list):
        node_list = [node_list]

    for node in node_list:
        if not node:
            continue

        if isinstance(node, dict):
            node_type = node.get("type", "N/A")
            line = node.get("lineno", "N/A")
            label = f"{indent}├── {node_type} [linea {line}]"
            
            if "value" in node and node["value"] is not None:
                label += f" ({node['value']})"
            
            if "datatype" in node and node["datatype"] is not None:
                label += f" ({node['datatype']})"

            print(label)
            
            children = node.get("children", [])
            if children:
                child_indent = indent + "│   "
                print_ast(children, child_indent)
        
        elif isinstance(node, list):
            print_ast(node, indent)

# ==============================
# EJECUCIÓN PRINCIPAL
# ==============================
def main():
    # --- 1. Configurar el Parser de Argumentos ---
    arg_parser = argparse.ArgumentParser(
        description="Compilador 'Wax' (Lexer, Parser, Analyzer, Generator).",
        epilog="Por defecto (sin flags), solo reportará errores si los encuentra."
    )
    
    arg_parser.add_argument(
        "filename",
        help="El archivo .wax que se va a compilar."
    )
    arg_parser.add_argument(
        "--tokens",
        action="store_true",
        help="Muestra la lista de tokens de la FASE 1."
    )
    arg_parser.add_argument(
        "--ast",
        action="store_true",
        help="Muestra el Árbol de Sintaxis Abstracta (AST) de la FASE 2."
    )
    arg_parser.add_argument(
        "--table",
        action="store_true",
        help="Muestra el registro completo de símbolos de la FASE 3."
    )
    
    # --- 2. ARGUMENTOS AÑADIDOS ---
    arg_parser.add_argument(
        "--code",
        action="store_true",
        help="Muestra el código Python generado (FASE 4)."
    )
    arg_parser.add_argument(
        "--execute",
        action="store_true",
        help="Ejecuta el código Python generado (FASE 5)."
    )
    # -------------------------------

    arg_parser.add_argument(
        "--all",
        action="store_true",
        help="Muestra la salida de todas las fases (tokens, AST, tabla y código)."
    )
    
    args = arg_parser.parse_args()

    # --- 2. Lectura del Archivo ---
    try:
        with open(args.filename, "r", encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"[Error Crítico] No se encontró el archivo '{args.filename}'")
        sys.exit(1)

    # --- 3. Ejecutar Fases (Recolección) ---

    # FASE 1: LÉXICO
    lexer.input(data)
    token_list = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        token_list.append(tok)

    # FASE 2: SINTÁCTICO
    lexer.lineno = 1
    ast = parser.parse(data, lexer=lexer)
    
    if not ast:
        print("[Error Crítico] Falló el análisis sintáctico. No se puede continuar.")
        sys.exit(1)

    # FASE 3: SEMÁNTICO
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # --- 4. Reporte de Errores Semánticos ---
    if analyzer.errors:
        print("\n=== SE ENCONTRARON ERRORES ===")
        for error in analyzer.errors:
            print(error)
        print("[Error Crítico] Falló el análisis semántico.")
        sys.exit(1)

    # --- 5. FASE 4: GENERACIÓN DE CÓDIGO ---
    # (Solo se ejecuta si las fases anteriores pasaron)
    python_code = None
    try:
        generator = CodeGenerator()
        python_code = generator.generate(ast)
    except Exception as e:
        print(f"\n[Error Crítico] Falló el generador de código.")
        print(f"    > {type(e).__name__}: {e}")
        sys.exit(1)

    # --- 6. FASES 5 y 6: REPORTE Y EJECUCIÓN ---
    
    if args.tokens or args.all:
        print("\n=== FASE 1: TOKENS ===")
        for tok in token_list:
            print(f"{tok.type}: {tok.value} (linea {tok.lineno})")

    if args.ast or args.all:
        print("\n=== FASE 2: AST (ÁRBOL DE SINTAXIS) ===")
        print_ast(ast)

    if args.table or args.all:
        print("\n=== FASE 3: REGISTRO DE SÍMBOLOS ===")
        print(json.dumps(analyzer.symbol_log, indent=2))

    if args.code or args.all:
        print("\n=== FASE 4: CÓDIGO PYTHON GENERADO ===")
        print(python_code)

    if args.execute:
        print("\n=== FASE 5: EJECUTANDO CÓDIGO... ===")
        stdout_capture = io.StringIO()
        try:
            # Redirigimos la salida estándar para capturar los 'print'
            with contextlib.redirect_stdout(stdout_capture):
                exec(python_code, {}, {})
            
            output = stdout_capture.getvalue()
            if output:
                print("--- Salida del Programa ---")
                print(output, end='') # 'end' para evitar doble salto de línea
                print("---------------------------")
            print("✔ Ejecución finalizada.")

        except Exception as e:
            print(f"[Error de Ejecución] El programa generado falló.")
            print(f"    > {type(e).__name__}: {e}")
            sys.exit(1)
    
    if not args.execute:
        print("\n✔ Compilación exitosa. Sin errores.")


if __name__ == "__main__":
    main()