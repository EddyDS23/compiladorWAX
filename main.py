# main.py
# Archivo principal que orquesta el análisis y la ejecución.

# --- IMPORTACIONES ---
from lexer import lexer
from parser import parser
from semantic import SemanticAnalyzer
from utils import print_ast, ASTVisualizer  

# Ya no necesitas la definición de print_ast aquí porque la importamos.

# ==============================
# EJECUCIÓN PRINCIPAL
# ==============================
if __name__ == "__main__":
    filename = "program.wax"
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"[Error] No se encontró el archivo '{filename}'")
        exit(1)

    # === FASE 1: LÉXICO ===
    print("\n=== FASE 1: TOKENS ===")
    lexer.input(data)
    for tok in lexer:
        print(f"{tok.type}: {tok.value} (linea {tok.lineno})")

    # === FASE 2: SINTÁCTICO ===
    print("\n=== FASE 2: AST ===")
    lexer.lineno = 1
    ast = parser.parse(data, lexer=lexer)
    
    if ast:
        # --- 1. Imprimir el árbol en la consola ---
        print("\n--- AST (Versión de Texto) ---")
        print_ast(ast) # <-- AÑADE ESTA LÍNEA

        # --- 2. Generar la imagen del árbol ---
        #print("\n--- AST (Versión Gráfica) ---")
        #print("Generando imagen del AST...")
        #visualizer = ASTVisualizer()
        #visualizer.visualize(ast, 'arbol_becas')
    else:
        print("[Error] No se pudo generar el AST")

    
    # === FASE 3: SEMÁNTICO (Ahora funcional) ===
    print("\n=== FASE 3: ANÁLISIS SEMÁNTICO ===")
    if ast:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
        
        if analyzer.errors:
            print("Se encontraron los siguientes errores semánticos:")
            for error in analyzer.errors:
                print(error)
        else:
            print("✔ Sin errores semánticos.")
            # Opcional: imprimir la tabla de símbolos si todo está bien
            print("Tabla de símbolos final:", analyzer.symbol_table)
    else:
        print("No se puede realizar el análisis semántico debido a errores de sintaxis.")
