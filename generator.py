# generator.py
# Traduce el AST verificado a código Python ejecutable.

class CodeGenerator:
    def __init__(self):
        self.indent_level = 0

    def indent(self):
        """Devuelve un string de indentación del nivel actual."""
        return "    " * self.indent_level

    def generate(self, ast):
        """Punto de entrada principal. Genera código para una lista de nodos."""
        code_lines = []
        for node in ast:
            # Visita cada nodo de alto nivel (global)
            line = self.visit(node)
            if line:
                code_lines.append(line)
        return "\n".join(code_lines)

    def visit(self, node):
        """Llama al método 'visit_TIPO' apropiado para un nodo."""
        if node is None:
            return ""
        
        # Si es una lista (un bloque de programa), visítala
        if isinstance(node, list):
            return self.visit_program(node)

        method_name = f'visit_{node["type"]}'
        # Llama al método (ej. visit_DECLARATION) o a generic_visit si no existe
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        """Fallback para nodos no implementados (ej. Type, PARAM)."""
        # La mayoría de los nodos "hijos" se visitan manualmente,
        # así que este método es principalmente para ignorar nodos
        # que no generan código por sí mismos (como 'Type').
        return ""

    # --- Métodos de Visita para Bloques ---

    def visit_program(self, node_list):
        """Visita una lista de sentencias (un bloque de código)."""
        self.indent_level += 1
        block_code = []
        for stmt in node_list:
            line = self.visit(stmt)
            if line:
                # Añade la indentación correcta a cada línea generada
                block_code.append(f"{self.indent()}{line}")
        self.indent_level -= 1
        return "\n".join(block_code)

    # --- Métodos de Visita para Sentencias (Statements) ---

    def visit_DECLARATION(self, node):
        # Wax: wax mi_var:int = 5
        # Py:  mi_var = 5
        # children: [0]=TypeNode, [1]=IdentNode, [2]=ExprNode
        var_name = self.visit(node["children"][1])
        expr = self.visit(node["children"][2])
        return f"{var_name} = {expr}"

    def visit_ASSIGN(self, node):
        # Wax: mi_var = 10
        # Py:  mi_var = 10
        # children: [0]=IdentNode, [1]=ExprNode
        var_name = self.visit(node["children"][0])
        expr = self.visit(node["children"][1])
        return f"{var_name} = {expr}"

    def visit_PRINT(self, node):
        # Wax: print(x)
        # Py:  print(x)
        expr = self.visit(node["children"][0])
        return f"print({expr})"

    def visit_IF(self, node):
        # Wax: if (cond) { ... }
        # Py:  if cond: \n    ...
        condition = self.visit(node["children"][0])
        block = self.visit(node["children"][1]) # El bloque es una lista 'program'
        return f"if {condition}:\n{block}"

    def visit_IF_ELSE(self, node):
        # Wax: if (cond) { ... } else { ... }
        # Py:  if cond: \n    ... \n else: \n    ...
        condition = self.visit(node["children"][0])
        if_block = self.visit(node["children"][1])
        else_block = self.visit(node["children"][2])
        # El 'else:' debe estar al nivel de indentación actual
        return f"if {condition}:\n{if_block}\n{self.indent()}else:\n{else_block}"

    def visit_WHILE(self, node):
        # Wax: while (cond) { ... }
        # Py:  while cond: \n    ...
        condition = self.visit(node["children"][0])
        block = self.visit(node["children"][1])
        return f"while {condition}:\n{block}"

    def visit_FUNCTION(self, node):
        # Wax: wax function mi_func:int(a:int) { ... }
        # Py:  def mi_func(a): \n    ...
        # children: [0]=ReturnType, [1]=IdentNode, [2...]=ParamList, [3]=ProgramBlock
        func_name = self.visit(node["children"][1])
        
        # Visitar manualmente los nodos de parámetros
        param_nodes = node["children"][2]
        params = [self.visit(p) for p in param_nodes]
        param_str = ", ".join(params)
        
        block = self.visit(node["children"][3])
        return f"def {func_name}({param_str}):\n{block}"

    def visit_PARAM(self, node):
        # Devuelve solo el nombre del parámetro, Python no necesita el tipo
        # children: [0]=IdentNode, [1].TypeNode
        return self.visit(node["children"][0])

    def visit_RETURN_VALUE(self, node):
        # Wax: return x
        # Py:  return x
        # El parser lo puso en una lista, así que tomamos el primer elemento
        expr = self.visit(node["children"][0])
        return f"return {expr}"

    def visit_RETURN_EMPTY(self, node):
        # Wax: return
        # Py:  return
        return "return"

    # --- Métodos de Visita para Expresiones (Expressions) ---
    # (Estos devuelven el string, no añaden indentación)

    def visit_Identifier(self, node):
        # Nodo para nombres de variables, funciones, params
        return node["value"]
    
    def visit_IDENT(self, node):
        # Nodo para variables usadas en expresiones
        return node["value"]

    def visit_NUMBER(self, node):
        return str(node["value"])

    def visit_STRING(self, node):
        # Añadimos las comillas que el parser quitó
        return f'"{node["value"]}"'

    def visit_BOOL(self, node):
        # Convertimos a la sintaxis de Python
        return "True" if node["value"] else "False"

    def visit_LIST(self, node):
        # Wax: [1, 2, 3]
        # Py:  [1, 2, 3]
        items = [self.visit(item) for item in node["children"]]
        return f"[{', '.join(items)}]"

    def visit_LIST_ACCESS(self, node):
        # Wax: mi_lista[i]
        # Py:  mi_lista[i]
        list_name = self.visit(node["children"][0])
        index = self.visit(node["children"][1])
        return f"{list_name}[{index}]"

    def visit_BINOP(self, node):
        # Wax: a + b
        # Py:  (a + b) (los paréntesis aseguran la precedencia)
        left = self.visit(node["children"][0])
        right = self.visit(node["children"][1])
        op = node["value"]
        return f"({left} {op} {right})"

    def visit_LOGIC(self, node):
        # Wax: a || b
        # Py:  (a or b)
        left = self.visit(node["children"][0])
        right = self.visit(node["children"][1])
        op = "or" if node["value"] == "||" else "and"
        return f"({left} {op} {right})"
    
    def visit_FUNC_CALL(self, node):
        # Wax: mi_func(a, b)
        # Py:  mi_func(a, b)
        # children: [0]=IdentNode, [1...]=Args
        func_name = self.visit(node["children"][0])
        args = [self.visit(arg) for arg in node["children"][1:]]
        return f"{func_name}({', '.join(args)})"

    def visit_INPUT(self, node):
        # Wax: input()
        # Py:  input()
        return "input()"