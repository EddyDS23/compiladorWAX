# Compilador WAX 🚀

¡Bienvenido al Compilador WAX! Este es un completo Entorno de Desarrollo Integrado (IDE) y compilador para el lenguaje de programación interpretado "Wax". Este proyecto toma código fuente escrito en Wax, realiza un análisis léxico, sintáctico y semántico, y finalmente lo traduce a código Python limpio y ejecutable.

El proyecto incluye tanto la lógica del compilador de 4 fases como una interfaz gráfica de usuario (GUI) completa construida con PySide6.

![Screenshot del IDE de WAX](https://i.imgur.com/Tu-URL.png) 
*(Sugerencia: Reemplaza este enlace con una captura de pantalla real de tu GUI)*

---

## ⚡ Características Principales

* **IDE Gráfico Completo:** Una GUI construida con PySide6 que sirve como un editor de texto y entorno de ejecución.
* **Editor de Código Avanzado:** El editor incluye numeración de línea y resaltado de la línea actual.
* **Compilador de 4 Fases:**
    1.  **Léxico (`lexer.py`):** Convierte el código en tokens.
    2.  **Sintáctico (`parser.py`):** Construye un Árbol de Sintaxis Abstracta (AST) y reporta errores de sintaxis con precisión.
    3.  **Semántico (`semantic.py`):** Valida el AST, chequea tipos, maneja ámbitos y detecta errores lógicos.
    4.  **Generador (`generator.py`):** Traduce el AST validado a código Python 3.
* **Ejecución Directa:** Ejecuta el código generado con un solo clic y captura la salida (incluyendo `print`) en la GUI.
* **Depuración Visual:** Muestra los **Tokens**, el **AST** y la **Tabla de Símbolos** completa en pestañas separadas.
* **Manejo de Ámbitos (Scopes):** Diferencia correctamente entre ámbitos globales, de función y de bloque (`if`, `while`).
* **Detección de Errores Avanzada:** Reporta errores como:
    * Errores de sintaxis (ej. `falta un '}' en la línea 63`).
    * Errores semánticos (ej. `tipos incompatibles`, `variable no declarada`).
    * División por cero.
    * Código inalcanzable (después de un `return`).
* **Tipado de Listas:** Soporta declaraciones de listas con chequeo de tipos (ej. `list[int]`, `list[string]`).

---

## 🛠️ Stack de Tecnologías

* **Python 3.10+** (Recomendado)
* **PLY:** Para el análisis léxico y sintáctico.
* **PySide6:** Para toda la interfaz gráfica de usuario.
* **pyqtdarktheme:** (Opcional) Para el tema oscuro del IDE.

---

## 🚀 Cómo Usarlo

Este proyecto se puede ejecutar como un IDE gráfico (recomendado) o como una herramienta de línea de comandos (CLI).

### 1. Instalación

1.  Clona o descarga este repositorio.
2.  Navega a la carpeta del proyecto y crea un entorno virtual:
    ```bash
    # Se recomienda Python 3.10 o 3.11 para máxima compatibilidad de librerías
    python3.11 -m venv venv
    ```
3.  Activa el entorno virtual:
    * En Linux/macOS: `source venv/bin/activate`
    * En Windows: `.\venv\Scripts\activate`
4.  Instala las dependencias:
    ```bash
    pip install ply PySide6 pyqtdarktheme
    ```

### 2. Ejecutar el IDE Gráfico (Recomendado)

Una vez instaladas las dependencias, simplemente ejecuta `gui.py`:

```bash
python gui.py
```
El IDE se abrirá con un código de ejemplo. ¡Ya puedes compilar (F5) y ejecutar (F6)!

### 3. Ejecutar la Versión de Consola (CLI)

También puedes usar `main.py` para compilar archivos desde la terminal.

```bash
# Muestra todas las fases (Tokens, AST, Tabla, Código)
python main.py program.wax --all

# Solo compila y ejecuta el archivo
python main.py program.wax --execute
```
**Opciones de la CLI:**
* `program.wax`: (Requerido) El archivo a compilar.
* `--tokens`: Muestra la salida del léxico.
* `--ast`: Muestra el árbol de sintaxis abstracta.
* `--table`: Muestra la tabla de símbolos.
* `--code`: Muestra el código Python generado.
* `--execute`: Ejecuta el código generado.
* `--all`: Activa `--tokens`, `--ast`, `--table` y `--code`.

---

## 📜 Referencia del Lenguaje Wax

### Tokens

| Tipo | Descripción | Ejemplos |
| --- | --- | --- |
| **Palabras Clave** | Reservadas por el lenguaje | `wax`, `function`, `if`, `else`, `while`, `return`, `print` |
| **Funciones Nativas** | Funciones incorporadas | `str`, `input` |
| **Identificadores** | Nombres de variables/funciones | `mi_var`, `evaluarAlumno` |
| **Tipos** | Tipos de datos primitivos | `int`, `double`, `string`, `bool`, `list`, `void` |
| **Literales** | Valores fijos | `123`, `5.5`, `"hola"`, `true`, `false` |
| **Operadores** | Aritméticos, Lógicos, Relacionales | `+`, `-`, `*`, `/`, `=`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `||` |
| **Delimitadores** | Símbolos de agrupación y separación | `(`, `)`, `{`, `}`, `[`, `]`, `,`, `;`, `:` |
| **Comentarios** | Ignorados por el compilador | `# línea` , `/* bloque */` |

### Sintaxis

```wax
# --- Comentarios ---
# Esto es un comentario de una línea.

/*
  Esto es un
  comentario de bloque.
*/

# --- Declaración de Variables ---
# wax <nombre> : <tipo> = <expresión>;
wax mi_entero:int = 10;
wax mi_string:string = "Hola";
wax mi_lista:list = [1, 2, 3];
wax lista_vacia:list = []; # El tipo se infiere en la asignación

# --- Asignación ---
mi_entero = mi_entero + 5;

# --- Estructura IF / ELSE ---
if (mi_entero > 10 && mi_string == "Hola") {
    print("Condición 1");
} else {
    print("Condición 2");
}

# --- Bucle WHILE ---
wax i:int = 0;
while (i < 5) {
    print(i);
    i = i + 1;
}

# --- Declaración de Funciones ---
# wax function <nombre> : <tipo_retorno> ( <params> ) { ... }
wax function sumar : int (a:int, b:int) {
    return a + b;
}

# Función sin retorno (void)
wax function saludar : void (nombre:string) {
    print("Hola, " + nombre);
    return; # Opcional
}

# --- Llamadas a Funciones y Nativas ---
wax resultado:int = sumar(5, 3);
saludar("Mundo");

wax texto_numero:string = str(resultado);
print("Escribe tu nombre:");
wax nombre_usuario:string = input();

# --- Listas ---
wax calificaciones:list = [90, 85, 100];
wax primera_calif:int = calificaciones[0];
calificaciones[1] = 95;
```

---

## 📦 Ejecutable Portable

Para crear un ejecutable portable (un solo archivo) para tu sistema operativo, puedes usar **PyInstaller**.

1.  Asegúrate de estar en tu `venv` y tener `pyinstaller` instalado (`pip install pyinstaller`).
2.  **Importante:** Borra los archivos de caché de PLY para evitar errores:
    ```bash
    rm parsetab.py
    rm parser.out
    ```
3.  Ejecuta el comando de PyInstaller:
    ```bash
    pyinstaller --onefile --windowed --name=WaxCompiler gui.py
    ```
4.  ¡Encontrarás tu ejecutable (`WaxCompiler` o `WaxCompiler.exe`) dentro de la nueva carpeta `dist/`!