# gui.py
# Interfaz gráfica del compilador WAX (Versión con números de línea nativos y input interactivo)

import sys
import io
import json
import contextlib

# --- Importaciones del Compilador ---
from lexer import lexer
from parser import parser
from semantic import SemanticAnalyzer
from generator import CodeGenerator

# --- Importaciones de PySide6 ---
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QHBoxLayout, QVBoxLayout, QTextEdit,
    QPushButton, QCheckBox, QTabWidget,
    QSplitter, QPlainTextEdit, QInputDialog
)
from PySide6.QtCore import Qt, QSize, QRect
from PySide6.QtGui import QFont, QPainter, QColor, QTextFormat

# ===============================================
#               PROGRAMA.WAX
# ===============================================

DEFAULT_WAX_CODE="""
# ==========================================================
#         Programa de Evaluación de Becas v3.0 (con bucle)
# ==========================================================

# La función devuelve un "código de razón" en lugar de múltiples valores.
# Si devuelve "", el alumno es aceptado.
wax function evaluarAlumno : string(edad:int, ingreso:int, promedio:int) {
    if (edad < 18 || edad > 25) { return "edad"; }
    if (ingreso >= 5000) { return "ingreso"; }
    if (promedio < 90) { return "promedio"; }
    return "";
}

# --- CONTADORES ---
wax aceptados:int = 0;
wax rechazados:int = 0;
wax rechazos_edad:int = 0;
wax rechazos_ingreso:int = 0;
wax rechazos_promedio:int = 0;

# --- DATOS DE ALUMNOS (organizados en listas) ---
wax numero_alumnos:int = 5;
wax edades:list = [20, 17, 23, 26, 22];
wax ingresos:list = [4000, 3000, 6000, 2000, 4500];
# Usamos una lista de listas para las calificaciones
wax calificaciones:list = [
    [95, 92, 90],  # Alumno 1 
    [88, 90, 85],  # Alumno 2
    [92, 91, 93],  # Alumno 3
    [97, 96, 98],  # Alumno 4
    [80, 85, 88]   # Alumno 5
];

# --- PROCESO DE EVALUACIÓN AUTOMATIZADO ---
wax i:int = 0; # Nuestro contador para el bucle
wax promedio:int = 0;
wax codigo_rechazo:string = "";
wax califs_alumno:list = [];

print("--- Iniciando Proceso de Evaluacion ---");

while (i < numero_alumnos) {
    
    # Obtenemos las calificaciones del alumno actual
    califs_alumno = calificaciones[i];
    # Calculamos su promedio
    promedio = (califs_alumno[0] + califs_alumno[1] + califs_alumno[2]) / 3;

    # Llamamos a la función con los datos del alumno i
    codigo_rechazo = evaluarAlumno(edades[i], ingresos[i], promedio);
    
    # El bloque de lógica es el mismo, pero ahora se repite para cada i
    if (codigo_rechazo == "") {
        aceptados = aceptados + 1;
        print("Alumno " + str(i+1) + ": Aceptado");
    } else {
        rechazados = rechazados + 1;
        
        
        if (codigo_rechazo == "edad") {
            rechazos_edad = rechazos_edad + 1;
        }

        if (codigo_rechazo == "ingreso") {
            rechazos_ingreso = rechazos_ingreso + 1;
        }

        if (codigo_rechazo == "promedio") {
            rechazos_promedio = rechazos_promedio + 1;
        }
        print("Alumno " + str(i+1) + ": Rechazado por " + codigo_rechazo);
    }

    # Incrementamos el contador para evitar un bucle infinito
    i = i + 1;
}

# --- RESULTADOS FINALES ---
print("---------------------------------");
print("--- Resultados de la Evaluacion ---");
print("Total de alumnos aceptados: " + str(aceptados));
print("Total de alumnos rechazados: " + str(rechazados));
print("--- Desglose de Rechazos ---");
print("Por edad: " + str(rechazos_edad));
print("Por ingreso: " + str(rechazos_ingreso));
print("Por promedio: " + str(rechazos_promedio));
print("---------------------------------");

# --- Ejemplo con input() ---
# wax nombre:string = input("Escribe tu nombre: ");
# print("Hola, " + nombre);

"""


# ===============================================
# CLASE 1: EL WIDGET DE NÚMEROS DE LÍNEA
# (Esto dibuja la barra lateral)
# ===============================================
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

    def sizeHint(self):
        return QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

# ===============================================
# CLASE 2: EL EDITOR DE CÓDIGO
# (Este widget combina la barra de números y el texto)
# ===============================================
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        # Conectar señales para que los números de línea se actualicen
        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def lineNumberAreaWidth(self):
        # Calcula el ancho necesario para mostrar los números
        digits = 1
        count = max(1, self.blockCount())
        while count >= 10:
            count //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def highlightCurrentLine(self):
        extraSelections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(Qt.GlobalColor.darkGray).lighter(110) # Color de fondo de la línea actual
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.setExtraSelections(extraSelections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(Qt.GlobalColor.lightGray).lighter(110)) # Color de fondo de la barra

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(Qt.GlobalColor.darkGray)) # Color del número
                painter.drawText(0, int(top), self.lineNumberArea.width(), self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

# ===============================================
# FUNCIÓN PERSONALIZADA DE INPUT
# ===============================================
def custom_input(prompt="", parent_widget=None):
    """
    Reemplazo de input() que muestra un diálogo de Qt.
    """
    text, ok = QInputDialog.getText(parent_widget, "Input", prompt)
    if ok:
        return text
    return ""

# ==============================
# CLASE PRINCIPAL DE LA APLICACIÓN
# (Modificada para usar 'CodeEditor' y manejar input())
# ==============================

class CompilerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compilador WAX v1.0")
        self.setGeometry(100, 100, 1200, 700)

        font = QFont("Monospace")
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        font.setPointSize(14)

        # --- Widgets Principales ---
        
        # 1. Panel de Controles (Superior)
        controls_layout = QHBoxLayout()
        self.btn_compile = QPushButton("Compilar (F5)")
        self.btn_compile.setShortcut("F5")

        self.btn_execute = QPushButton("Ejecutar (F6)")
        self.btn_execute.setShortcut("F6")
        self.btn_execute.setEnabled(False)
        
        self.chk_tokens = QCheckBox("Mostrar Tokens")
        self.chk_ast = QCheckBox("Mostrar AST")
        self.chk_table = QCheckBox("Mostrar Tabla de Símbolos")
        
        controls_layout.addWidget(self.btn_compile)
        controls_layout.addWidget(self.btn_execute)
        controls_layout.addWidget(self.chk_tokens)
        controls_layout.addWidget(self.chk_ast)
        controls_layout.addWidget(self.chk_table)
        controls_layout.addStretch()

        # 2. Editor de Código (Izquierda)
        self.code_input = CodeEditor()
        self.code_input.setFont(font)
        self.code_input.setPlainText(DEFAULT_WAX_CODE)

        # 3. Panel de Salida (Derecha) - Sigue usando QTextEdit
        self.output_tabs = QTabWidget()
        self.tab_errors = QTextEdit() # Sigue siendo QTextEdit
        self.tab_errors.setFont(font)
        self.tab_errors.setReadOnly(True)
        
        self.tab_tokens = QTextEdit()
        self.tab_tokens.setFont(font)
        self.tab_tokens.setReadOnly(True)
        
        self.tab_ast = QTextEdit()
        self.tab_ast.setFont(font)
        self.tab_ast.setReadOnly(True)
        
        self.tab_table = QTextEdit()
        self.tab_table.setFont(font)
        self.tab_table.setReadOnly(True)

        self.tab_python = QTextEdit()
        self.tab_python.setFont(font)
        self.tab_python.setReadOnly(True)

        self.output_tabs.addTab(self.tab_errors, "Errores / Salida")
        self.output_tabs.addTab(self.tab_tokens, "Tokens")
        self.output_tabs.addTab(self.tab_ast, "AST")
        self.output_tabs.addTab(self.tab_table, "Tabla de Símbolos")

        # --- Layouts Principales ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.code_input)
        splitter.addWidget(self.output_tabs)
        splitter.setSizes([600, 600])

        main_layout = QVBoxLayout()
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(splitter)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.btn_compile.clicked.connect(self.compile_code)
        self.btn_execute.clicked.connect(self.execute_code)

    def clear_outputs(self):
        self.tab_errors.clear()
        self.tab_tokens.clear()
        self.tab_ast.clear()
        self.tab_table.clear()
        self.tab_python.clear()

    def compile_code(self):
        self.clear_outputs()
        self.btn_execute.setEnabled(False)
        
        # .toPlainText() funciona igual en QPlainTextEdit
        code = self.code_input.toPlainText()
        if not code.strip():
            self.tab_errors.setText("No hay código para compilar.")
            self.output_tabs.setCurrentWidget(self.tab_errors)
            return

        # --- FASE 1: LÉXICO ---
        lexer.input(code)
        token_list = []
        while True:
            tok = lexer.token()
            if not tok:
                break
            token_list.append(tok)

        # --- FASE 2: SINTÁCTICO ---
        lexer.lineno = 1
        ast = None
        stderr_capture = io.StringIO()
        with contextlib.redirect_stderr(stderr_capture):
            ast = parser.parse(code, lexer=lexer)
        
        parser_errors = stderr_capture.getvalue()
        if parser_errors:
            self.tab_errors.setText(f"--- Errores de Sintaxis ---\n{parser_errors}")
            self.output_tabs.setCurrentWidget(self.tab_errors)
            return
            
        if not ast:
            self.tab_errors.setText("Error desconocido de parsing. No se generó el AST.")
            self.output_tabs.setCurrentWidget(self.tab_errors)
            return

        # --- FASE 3: SEMÁNTICO ---
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)

        if analyzer.errors:
            self.tab_errors.setText("--- Errores Semánticos ---\n" + "\n".join(analyzer.errors))
            self.output_tabs.setCurrentWidget(self.tab_errors)
        else:
            self.tab_errors.setText("✓ Compilación exitosa. Sin errores.")
            try:
                generator = CodeGenerator()
                python_code = generator.generate(ast)
                self.tab_python.setText(python_code)
                self.btn_execute.setEnabled(True)
            except Exception as e:
                # Esto es por si nuestro generador tiene un bug
                self.tab_errors.setText(f"--- Error del Generador de Código ---\n¡Ocurrió un error inesperado al generar el código!\n\n{type(e).__name__}: {e}")
                self.output_tabs.setCurrentWidget(self.tab_errors)

        # --- FASE 4: REPORTE ---
        if self.chk_tokens.isChecked():
            tokens_str = "\n".join([f"{tok.type}: {tok.value} (linea {tok.lineno})" for tok in token_list])
            self.tab_tokens.setText(tokens_str)
            if not analyzer.errors:
                self.output_tabs.setCurrentWidget(self.tab_tokens)

        if self.chk_ast.isChecked():
            ast_str = format_ast_string(ast, stream=io.StringIO())
            self.tab_ast.setText(ast_str)
            if not analyzer.errors and not self.chk_tokens.isChecked():
                 self.output_tabs.setCurrentWidget(self.tab_ast)

        if self.chk_table.isChecked():
            table_str = json.dumps(analyzer.symbol_log, indent=2)
            self.tab_table.setText(table_str)
            if not analyzer.errors and not self.chk_tokens.isChecked() and not self.chk_ast.isChecked():
                 self.output_tabs.setCurrentWidget(self.tab_table)

    def execute_code(self):
        """Ejecuta el código de la pestaña 'Código Python' con soporte para input()."""
        
        python_code = self.tab_python.toPlainText()
        if not python_code:
            self.tab_errors.setText("No hay código Python para ejecutar.")
            self.output_tabs.setCurrentWidget(self.tab_errors)
            return
        
        # Preparamos un buffer para capturar salida
        output_lines = []
        
        # Creamos una función input personalizada que usa este widget
        def gui_input(prompt=""):
            # Mostramos primero todo lo que se ha impreso hasta ahora
            if output_lines:
                current_output = "\n".join(output_lines)
                self.tab_errors.setText(f"--- Ejecutando... ---\n{current_output}")
                self.output_tabs.setCurrentWidget(self.tab_errors)
                QApplication.processEvents()  # Forzar actualización de UI
            
            # Mostramos el diálogo
            text, ok = QInputDialog.getText(self, "Input", prompt)
            
            # Guardamos en el log lo que el usuario escribió
            if ok:
                output_lines.append(f"{prompt}{text}")
                return text
            return ""
        
        # Función print personalizada
        def gui_print(*args, **kwargs):
            line = " ".join(str(arg) for arg in args)
            output_lines.append(line)
            # Actualizamos la UI en tiempo real
            current_output = "\n".join(output_lines)
            self.tab_errors.setText(f"--- Ejecutando... ---\n{current_output}")
            self.output_tabs.setCurrentWidget(self.tab_errors)
            QApplication.processEvents()
        
        try:
            # Creamos un namespace con nuestras funciones personalizadas
            exec_globals = {
                'input': gui_input,
                'print': gui_print,
                '__builtins__': __builtins__
            }
            
            # Ejecutamos el código
            exec(python_code, exec_globals, {})
            
            # Mostramos la salida final
            final_output = "\n".join(output_lines)
            self.tab_errors.setText(f"--- Ejecución Finalizada ---\n{final_output}\n\n✓ Programa terminado exitosamente.")
            
        except Exception as e:
            # Si hay error, mostramos lo que se ejecutó hasta el momento
            partial_output = "\n".join(output_lines)
            self.tab_errors.setText(
                f"--- Salida Parcial ---\n{partial_output}\n\n"
                f"--- Error de Ejecución ---\n{type(e).__name__}: {e}"
            )
            
        finally:
            self.output_tabs.setCurrentWidget(self.tab_errors)

# ==============================
# FUNCIÓN DE FORMATO DE AST
# ==============================
def format_ast_string(node_list, indent="", stream=None):
    if stream is None:
        stream = io.StringIO()
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
            stream.write(label + "\n")
            children = node.get("children", [])
            if children:
                child_indent = indent + "│   "
                format_ast_string(children, child_indent, stream)
        elif isinstance(node, list):
            format_ast_string(node, indent, stream)
    return stream.getvalue()

# ==============================
# PUNTO DE ENTRADA
# ==============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    try:
        import qdarktheme
        app.setStyleSheet(qdarktheme.load_stylesheet())
    except ImportError:
        print("Instala 'pyqtdarktheme' (pip install pyqtdarktheme) para un mejor look.")

    window = CompilerApp()
    window.show()
    sys.exit(app.exec())