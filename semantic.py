# semantic.py

class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.current_function_return_type = None

        # Creamos el alcance global y lo pre-cargamos con las funciones built-in.
        built_ins = {
            'str': {'type': 'function', 'return_type': 'string', 'param_types': ['any']},
            'input': {'type': 'function', 'return_type': 'string', 'param_types': []}
        }
        self.symbol_table = [built_ins]

    def _error(self, message, lineno):
        self.errors.append(f"[Error Semántico] Línea {lineno}: {message}")

    def enter_scope(self):
        self.symbol_table.append({})

    def exit_scope(self):
        self.symbol_table.pop()

    def add_symbol(self, name, symbol_info, lineno):
        current_scope = self.symbol_table[-1]
        if name in current_scope:
            self._error(f"El símbolo '{name}' ya ha sido declarado en este alcance.", lineno)
            return False
        current_scope[name] = symbol_info
        return True

    def get_symbol(self, name, lineno):
        for scope in reversed(self.symbol_table):
            if name in scope:
                return scope[name]
        self._error(f"El símbolo '{name}' no ha sido declarado.", lineno)
        return None

    def analyze(self, ast):
        if not ast: return
        # 1. PRIMER PASO: Registrar todas las declaraciones de funciones.
        for node in ast:
            if node['type'] == 'FUNCTION':
                self.visit(node, first_pass=True)
        # 2. SEGUNDO PASO: Analizar todo el código.
        for node in ast:
            self.visit(node, first_pass=False)

    def visit(self, node, first_pass=False):
        if node is None: return
        if isinstance(node, list):
            for item in node: self.visit(item, first_pass)
            return
        
        method_name = f'visit_{node["type"]}'
        method = getattr(self, method_name, self.generic_visit)
        # ¡Importante! Pasa la bandera 'first_pass' al método específico
        return method(node, first_pass=first_pass)

    def generic_visit(self, node, first_pass=False):
        # Durante el primer paso, solo nos interesan las funciones
        if first_pass: return
        for child in node.get("children", []):
            self.visit(child)
    
    # --- MÉTODOS DE VISITA PARA SENTENCIAS (STATEMENTS) ---

    def visit_DECLARATION(self, node, first_pass=False):
        if first_pass: return # No procesar en el primer paso
        var_type = node["children"][0]["value"]
        var_name = node["children"][1]["value"]
        lineno = node["lineno"]
        expr_node = node["children"][2]
        expr_type = self.get_expr_type(expr_node)

        if expr_type != "error" and expr_type != var_type:
            self._error(f"No se puede asignar un valor de tipo '{expr_type}' a la variable '{var_name}' de tipo '{var_type}'.", lineno)
        
        self.add_symbol(var_name, var_type, lineno)

    def visit_ASSIGN(self, node, first_pass=False):
        if first_pass: return
        var_name = node["children"][0]["value"]
        lineno = node["lineno"]
        symbol = self.get_symbol(var_name, lineno)
        if symbol:
            if isinstance(symbol, dict) and symbol.get('type') == 'function':
                self._error(f"No se puede asignar un valor a la función '{var_name}'.", lineno)
                return
            var_type = symbol
            expr_type = self.get_expr_type(node["children"][1])
            if expr_type != "error" and expr_type != var_type:
                self._error(f"No se puede asignar un valor de tipo '{expr_type}' a la variable '{var_name}' de tipo '{var_type}'.", lineno)

    def visit_PRINT(self, node, first_pass=False):
        if first_pass: return
        self.get_expr_type(node["children"][0])

    def visit_IF_ELSE(self, node, first_pass=False):
        if first_pass: return
        self.visit_IF(node, first_pass)
        self.visit(node["children"][2])

    def visit_IF(self, node, first_pass=False):
        if first_pass: return
        condition_node = node["children"][0]
        if self.get_expr_type(condition_node) != "bool":
            self._error("La condición del 'if' debe ser de tipo 'bool'.", condition_node["lineno"])
        self.visit(node["children"][1])

    def visit_WHILE(self, node, first_pass=False):
        if first_pass: return
        condition_node = node["children"][0]
        if self.get_expr_type(condition_node) != "bool":
            self._error("La condición del 'while' debe ser de tipo 'bool'.", condition_node["lineno"])
        self.visit(node["children"][1])

    def visit_FUNCTION(self, node, first_pass=False):
        func_name = node["children"][1]["value"]
        lineno = node["lineno"]

        if first_pass:
            # En el primer paso, solo registramos la firma de la función
            return_type = node["children"][0]["value"]
            params = node["children"][2]
            param_types = [p['children'][1]['value'] for p in params]
            func_info = {'type': 'function', 'return_type': return_type, 'param_types': param_types}
            self.add_symbol(func_name, func_info, lineno)
        else:
            # En el segundo paso, analizamos el cuerpo de la función
            body = node["children"][3]
            func_symbol = self.get_symbol(func_name, lineno)
            if not func_symbol: return # Ya se habrá reportado un error

            self.enter_scope()
            self.current_function_return_type = func_symbol['return_type']
            params = node["children"][2]
            for param in params:
                param_name = param['children'][0]['value']
                param_type = param['children'][1]['value']
                self.add_symbol(param_name, param_type, lineno)
            self.visit(body)
            self.exit_scope()
            self.current_function_return_type = None

    def visit_RETURN_VALUE(self, node, first_pass=False):
        if first_pass: return
        if self.current_function_return_type is None:
            self._error("La sentencia 'return' solo puede usarse dentro de una función.", node["lineno"])
            return
        if self.current_function_return_type == "void":
            self._error("Una función 'void' no puede devolver un valor.", node["lineno"])
            return
        returned_type = self.get_expr_type(node["children"][0])
        if returned_type != self.current_function_return_type:
            self._error(f"El tipo de retorno no coincide. Se esperaba '{self.current_function_return_type}' pero se encontró '{returned_type}'.", node["lineno"])

    def visit_RETURN_EMPTY(self, node, first_pass=False):
        if first_pass: return
        if self.current_function_return_type is None:
            self._error("La sentencia 'return' solo puede usarse dentro de una función.", node["lineno"])
        elif self.current_function_return_type != "void":
            self._error(f"Una función que no es 'void' debe devolver un valor.", node["lineno"])

    # --- MÉTODOS PARA EVALUAR TIPOS DE EXPRESIONES ---
    # (Estos no necesitan la bandera 'first_pass' porque solo se llaman en el segundo paso)

    def get_expr_type(self, node):
        if node is None: return "error"
        method_name = f'get_expr_type_{node["type"]}'
        method = getattr(self, method_name, lambda n: "error")
        return method(node)

    def get_expr_type_NUMBER(self, node): return node["datatype"]
    def get_expr_type_STRING(self, node): return "string"
    def get_expr_type_BOOL(self, node): return "bool"
    def get_expr_type_INPUT(self, node): return "string"

    def get_expr_type_IDENT(self, node):
        symbol = self.get_symbol(node["value"], node["lineno"])
        if not symbol: return "error"
        if isinstance(symbol, dict) and symbol.get('type') == 'function':
            return 'function'
        return symbol

    def get_expr_type_BINOP(self, node):
        left_type = self.get_expr_type(node["children"][0])
        right_type = self.get_expr_type(node["children"][1])
        op = node["value"]
        lineno = node["lineno"]
        if left_type == "error" or right_type == "error": return "error"
        if op in ('==', '!=', '<', '>', '<=', '>='): return "bool"
        if op == '+' and ("string" in (left_type, right_type)): return "string"
        if left_type not in ("int", "double") or right_type not in ("int", "double"):
            self._error(f"Operación aritmética '{op}' inválida entre tipos '{left_type}' y '{right_type}'.", lineno)
            return "error"
        if left_type == "double" or right_type == "double": return "double"
        return "int"

    def get_expr_type_LOGIC(self, node):
        left_type = self.get_expr_type(node["children"][0])
        right_type = self.get_expr_type(node["children"][1])
        if left_type != "bool" or right_type != "bool":
            self._error(f"Operación lógica '{node['value']}' solo permitida entre valores 'bool'.", node["lineno"])
            return "error"
        return "bool"
    
    def get_expr_type_FUNC_CALL(self, node):
        func_name = node["children"][0]["value"]
        lineno = node["lineno"]
        func_symbol = self.get_symbol(func_name, lineno)
        if not func_symbol or not isinstance(func_symbol, dict) or func_symbol.get('type') != 'function':
            self._error(f"'{func_name}' no es una función o no ha sido declarada.", lineno)
            return "error"
        
        args = node["children"][1:]
        expected_params = func_symbol['param_types']
        if len(args) != len(expected_params) and not ('any' in expected_params):
            self._error(f"La función '{func_name}' esperaba {len(expected_params)} argumentos, pero recibió {len(args)}.", lineno)
            return "error"
        
        for i, arg in enumerate(args):
            if i >= len(expected_params): break
            arg_type = self.get_expr_type(arg)
            expected_type = expected_params[i]
            if expected_type == 'any': continue
            if arg_type != "error" and arg_type != expected_type:
                self._error(f"Argumento {i+1} de '{func_name}': se esperaba tipo '{expected_type}' pero se encontró '{arg_type}'.", lineno)
        
        return func_symbol['return_type']