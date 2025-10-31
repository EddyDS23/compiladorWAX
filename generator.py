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
        code_lines = ["import sys"]
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
    
    #Generar código para asignaciones compuestas
    def visit_ASSIGN_COMPOUND(self, node):
        # Wax: a += 5
        # Py:  a += 5
        var_name = self.visit(node["children"][0])
        expr = self.visit(node["children"][1])
        operator = node["value"]  # +=, -=, *=, /=
        return f"{var_name} {operator} {expr}"
    
    # Generar código para incremento/decremento
    def visit_INCREMENT(self, node):
        # Wax: i++; o ++i; o i--; o --i;
        # Py:  i += 1 o i -= 1
        var_name = self.visit(node["children"][0])
        operator = node["value"]  # ++, --
        
        if operator == '++':
            return f"{var_name} += 1"
        else:  # --
            return f"{var_name} -= 1"
    
    def visit_LIST_APPEND(self, node):
        # Wax: mi_lista.append(5)
        # Py:  mi_lista.append(5)
        list_name = self.visit(node["children"][0])
        element = self.visit(node["children"][1])
        return f"{list_name}.append({element})"

    def visit_LIST_REMOVE(self, node):
        # Wax: mi_lista.remove(0)  # índice
        # Py:  del mi_lista[0]
        list_name = self.visit(node["children"][0])
        index = self.visit(node["children"][1])
        return f"del {list_name}[{index}]"

    def visit_PRINT(self, node):
        # Wax: print(x)
        # Py:  print(x)
        expr = self.visit(node["children"][0])
        return f"print({expr}, flush=True)"

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
    
    def visit_FOR(self, node):
        # Wax: for (wax i:int = 0; i < 10; i++) { ... }
        # Py:  i = 0
        #      while i < 10:
        #          ...
        #          i += 1
        
        var_name_node = node["children"][1]
        init_expr = node["children"][2]
        condition = node["children"][3]
        increment = node["children"][4]
        body = node["children"][5]
        
        var_name = self.visit(var_name_node)
        init_value = self.visit(init_expr)
        cond = self.visit(condition)
        
        # Generar el código del incremento
        inc_code = self.visit_for_increment(increment)
        
        # Convertir el body (lista de statements) en código
        self.indent_level += 1
        body_code = []
        for stmt in body:
            line = self.visit(stmt)
            if line:
                body_code.append(f"{self.indent()}{line}")
        
        # Agregar el incremento al final del cuerpo
        body_code.append(f"{self.indent()}{inc_code}")
        self.indent_level -= 1
        
        body_str = "\n".join(body_code)
        
        # Generar el código completo
        return f"{var_name} = {init_value}\nwhile {cond}:\n{body_str}"
    
    def visit_for_increment(self, node):
        """Genera código para el incremento del for"""
        if node["type"] == "FOR_INCREMENT":
            # i++ o i--
            var_name = self.visit(node["children"][0])
            operator = node["value"]
            if operator == '++':
                return f"{var_name} += 1"
            else:  # --
                return f"{var_name} -= 1"
        elif node["type"] == "FOR_INCREMENT_EXPR":
            # i += 1, i = i + 1, etc.
            var_name = self.visit(node["children"][0])
            expr = self.visit(node["children"][1])
            operator = node["value"]
            return f"{var_name} {operator} {expr}"

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
    
    def visit_NOT(self, node):
        # Wax: !condicion
        # Py:  not condicion
        operand = self.visit(node["children"][0])
        return f"(not {operand})"
    
    def visit_UNARY_MINUS(self, node):
        # Wax: -x
        # Py:  -x
        operand = self.visit(node["children"][0])
        return f"(-{operand})"
    
    def visit_FUNC_CALL(self, node):
        # Wax: mi_func(a, b)
        # Py:  mi_func(a, b)
        # children: [0]=IdentNode, [1...]=Args
        func_name = self.visit(node["children"][0])
        args = [self.visit(arg) for arg in node["children"][1:]]
        return f"{func_name}({', '.join(args)})"

    def visit_INPUT(self, node):
        # Wax: input() o input("mensaje")
        # Py:  import sys; sys.stdout.flush(); input() o input("mensaje")
        if node.get("children") and len(node["children"]) > 0:
            # input con mensaje - forzamos flush antes
            message = self.visit(node["children"][0])
            return f"(sys.stdout.flush() or input({message}))"
        else:
            # input sin mensaje
            return "(sys.stdout.flush() or input())"