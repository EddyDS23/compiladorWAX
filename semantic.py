# semantic.py

class SemanticAnalyzer:
    def __init__(self):
        self.errors = []
        self.current_function_return_type = None
        self.scope_stack = ['global'] 

        self.symbol_log = []

        # Creamos el alcance global y lo pre-cargamos con las funciones built-in.
        built_ins = {
            'str': {
                'type_info': {'type': 'function', 'return_type': 'string', 'param_types': ['any']},
                'scope': 'global'
            },
            'input': {
                'type_info': {'type': 'function', 'return_type': 'string', 'param_types': []},
                'scope': 'global'
            }
        }
        self.symbol_table = [built_ins]

        
        for name, data in built_ins.items():
            self.symbol_log.append({
                'name': name,
                'type_info': self.format_type(data['type_info']), 
                'scope': data['scope'],
                'line': 0
            })

    def _error(self, message, lineno):
        self.errors.append(f"[Error Semántico] Línea {lineno}: {message}")

    def format_type(self, type_obj):
        """Convierte un objeto de tipo en un string legible."""
        if isinstance(type_obj, dict):
            if type_obj.get('type') == 'list':
                subtype = self.format_type(type_obj.get('subtype', 'any'))
                return f"list[{subtype}]"
            return str(type_obj)
        return str(type_obj)
    
    def _types_compatible(self, expected, actual):
        """Comprueba si el tipo 'actual' se puede asignar al 'expected'."""
        
        # Si son idénticos, son compatibles.
        if expected == actual:
            return True
        
        # Permitir promoción de int -> double
        if expected == "double" and actual == "int":
            return True
            
        # Permitir asignar 'list_element' (deberíamos eliminarlo, pero por si acaso)
        if actual == "list_element":
            return True

        # Caso: wax mi_lista:list = [1, 2]
        # expected="list", actual={'type':'list', 'subtype':'int'}
        if expected == "list" and isinstance(actual, dict) and actual.get('type') == 'list':
            return True

        # Caso: mi_lista_vacia = mi_lista_llena
        # expected={'type':'list', 'subtype':'empty'}, actual={'type':'list', 'subtype':'int'}
        if (isinstance(expected, dict) and expected.get('subtype') == 'empty' and
            isinstance(actual, dict) and actual.get('type') == 'list'):
            return True
            
        # Comprobación recursiva para tipos complejos (list[int] == list[int])
        if isinstance(expected, dict) and isinstance(actual, dict):
            if expected.get('type') != actual.get('type'):
                return False
            # Compara subtipos recursivamente
            return self._types_compatible(expected.get('subtype'), actual.get('subtype'))

        return False

    def enter_scope(self,scope_name):
        self.symbol_table.append({})
        self.scope_stack.append(scope_name)

    def exit_scope(self):
        self.symbol_table.pop()
        self.scope_stack.pop()

    def add_symbol(self, name, symbol_info, lineno):
        current_scope = self.symbol_table[-1]
        current_scope_name = self.scope_stack[-1] 

        if name in current_scope:
            self._error(f"El símbolo '{name}' ya ha sido declarado en este alcance.", lineno)
            return False
        
        
        # En lugar de solo guardar el tipo, guardamos un dict que lo contiene
        symbol_data = {
            'type_info': symbol_info,
            'scope': current_scope_name
        }
        current_scope[name] = symbol_data

        # Guardamos un registro persistente para la tabla final
        log_entry = {
            'name': name,
            'type_info': self.format_type(symbol_info), 
            'scope': current_scope_name,
            'line': lineno
        }
        self.symbol_log.append(log_entry)
        
        return True

    def get_symbol(self, name, lineno):
        for scope in reversed(self.symbol_table):
            if name in scope:
                return scope[name]['type_info']
        self._error(f"El símbolo '{name}' no ha sido declarado.", lineno)
        return None
    
    def update_symbol_type(self, name, new_type):
        """Busca el símbolo en todos los ámbitos y actualiza su tipo."""
        for scope in reversed(self.symbol_table):
            if name in scope:
                scope[name]['type_info'] = new_type
                return True
        return False

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
        # ¡Esta línea es clave! Pasa el "return" del método visitado
        return method(node, first_pass=first_pass)
    

    def generic_visit(self, node, first_pass=False):
        # Durante el primer paso, solo nos interesan las funciones
        if first_pass: return
        for child in node.get("children", []):
            self.visit(child)

    def visit_statement_list(self, nodes, first_pass=False):
        """
        Visita una lista de sentencias (un bloque 'program'),
        manejando el código inalcanzable.
        """
        if first_pass: return
        
        has_returned = False
        for node in nodes:
            if has_returned:
                self._error("Código inalcanzable detectado después de una sentencia 'return'.", node["lineno"])
                # Importante: No 'break', reporta todo el código inalcanzable
                continue 
            
            # Visitamos la sentencia y capturamos su "estado"
            status = self.visit(node, first_pass=first_pass)
            
            # Si la sentencia fue un return, marcamos la bandera
            if status == "unreachable":
                has_returned = True

    
                
        
    
    # --- MÉTODOS DE VISITA PARA SENTENCIAS (STATEMENTS) ---

    def visit_DECLARATION(self, node, first_pass=False):
        if first_pass: return # No procesar en el primer paso
        var_type = node["children"][0]["value"]
        var_name = node["children"][1]["value"]
        lineno = node["lineno"]
        expr_node = node["children"][2]
        expr_type = self.get_expr_type(expr_node)

        if expr_type == "error":
           self.add_symbol(var_name,var_type,lineno)
           return
        
        is_compatible = self._types_compatible(var_type,expr_type)

        if not is_compatible:
            self._error(f"No se puede asignar un valor de tipo '{self.format_type(expr_type)}' a la variable '{var_name}' de tipo '{var_type}'.", lineno)
        
        type_to_store = var_type

        if var_type == "list" and is_compatible and isinstance(expr_type, dict):
            type_to_store = expr_type
        
        self.add_symbol(var_name, type_to_store, lineno)

        

    def visit_ASSIGN(self, node, first_pass=False):
        if first_pass: return
        var_name = node["children"][0]["value"]
        lineno = node["lineno"]
        symbol = self.get_symbol(var_name, lineno)
        if symbol:
            if isinstance(symbol, dict) and symbol.get('type') == 'function':
                self._error(f"No se puede asignar un valor a la función '{var_name}'.", lineno)
                return
            
            # 'symbol' es el tipo esperado (ej: {'type':'list', 'subtype':'empty'})
            expected_type = symbol 
            expr_type = self.get_expr_type(node["children"][1]) # (ej: {'type':'list', 'subtype':'int'})

            if expr_type != "error":
                if not self._types_compatible(expected_type,expr_type):
                    self._error(f"No se puede asignar un valor de tipo '{self.format_type(expr_type)}' a la variable '{var_name}' de tipo '{self.format_type(expected_type)}'.", lineno)

                
               # Si asignamos a una lista vacía, actualizamos su tipo
                if (isinstance(expected_type, dict) and expected_type.get('subtype') == 'empty' and
                    isinstance(expr_type, dict) and expr_type.get('type') == 'list'):
                    # Actualiza el símbolo donde sea que haya sido declarado
                    self.update_symbol_type(var_name, expr_type)


    # Validación para asignaciones compuestas
    def visit_ASSIGN_COMPOUND(self, node, first_pass=False):
        if first_pass: return
        
        var_name = node["children"][0]["value"]
        operator = node["value"]  # +=, -=, *=, /=
        lineno = node["lineno"]
        
        # 1. Verificar que la variable existe
        var_type = self.get_symbol(var_name, lineno)
        if not var_type:
            return
        
        # 2. No se puede usar en funciones
        if isinstance(var_type, dict) and var_type.get('type') == 'function':
            self._error(f"No se puede usar '{operator}' en la función '{var_name}'.", lineno)
            return
        
        
        # 3. No se puede usar en listas
        if isinstance(var_type, dict) and var_type.get('type') == 'list':
            self._error(f"No se puede usar '{operator}' en listas. Use métodos como append() en su lugar.", lineno)
            return


        # 4. Obtener el tipo de la expresión del lado derecho
        expr_type = self.get_expr_type(node["children"][1])
        if expr_type == "error":
            return
        
        # 5. Validar tipos según el operador
        base_op = operator[0]  # Extrae '+', '-', '*', '/'
        
        if base_op == '+':
            # += funciona con números y strings
            if var_type == "string" or expr_type == "string":
                # Concatenación de strings
                if not (var_type == "string" or expr_type == "string"):
                    self._error(
                        f"No se puede usar '+=' entre '{self.format_type(var_type)}' y '{self.format_type(expr_type)}'.",
                        lineno
                    )
            else:
                # Suma numérica
                if var_type not in ("int", "double") or expr_type not in ("int", "double"):
                    self._error(
                        f"El operador '+=' requiere tipos numéricos, pero se encontró '{self.format_type(var_type)}' y '{self.format_type(expr_type)}'.",
                        lineno
                    )
        else:
            # -=, *=, /= solo funcionan con números
            if var_type not in ("int", "double") or expr_type not in ("int", "double"):
                self._error(
                    f"El operador '{operator}' solo funciona con tipos numéricos (int/double), "
                    f"pero '{var_name}' es '{self.format_type(var_type)}' y la expresión es '{self.format_type(expr_type)}'.",
                    lineno
                )
                return
        
        # 5. Verificar división por cero en /=
        if base_op == '/':
            expr_node = node["children"][1]
            if expr_node["type"] == 'NUMBER' and expr_node["value"] == 0:
                self._error("División por cero detectada en tiempo de compilación.", lineno)

    
    # NUEVO - Validación para incremento/decremento
    def visit_INCREMENT(self, node, first_pass=False):
        if first_pass: return
        
        var_name = node["children"][0]["value"]
        operator = node["value"]  # ++, --
        lineno = node["lineno"]
        
        # 1. Verificar que la variable existe
        var_type = self.get_symbol(var_name, lineno)
        if not var_type:
            return
        
        # 2. No se puede usar en funciones
        if isinstance(var_type, dict) and var_type.get('type') == 'function':
            self._error(f"No se puede usar '{operator}' en la función '{var_name}'.", lineno)
            return
        
        # 3. No se puede usar en listas
        if isinstance(var_type, dict) and var_type.get('type') == 'list':
            self._error(f"No se puede usar '{operator}' en listas.", lineno)
            return
        
        # 4. Solo funciona con números (int o double)
        if var_type not in ("int", "double"):
            self._error(
                f"El operador '{operator}' solo funciona con tipos numéricos (int/double), "
                f"pero '{var_name}' es de tipo '{self.format_type(var_type)}'.",
                lineno
            )

    def visit_LIST_APPEND(self, node, first_pass=False):
        if first_pass: return
        
        list_name = node["children"][0]["value"]
        lineno = node["lineno"]
        
        # 1. Verificar que la lista existe
        list_symbol = self.get_symbol(list_name, lineno)
        if not list_symbol:
            return
        
        # 2. Verificar que es una lista
        if not isinstance(list_symbol, dict) or list_symbol.get('type') != 'list':
            self._error(f"'{list_name}' no es una lista. No se puede usar append().", lineno)
            return
        
        # 3. Obtener el tipo del elemento a agregar
        element_to_add = node["children"][1]
        element_type = self.get_expr_type(element_to_add)
        
        if element_type == "error":
            return
        
        # 4. Verificar compatibilidad de tipos
        list_subtype = list_symbol.get('subtype')
        
        # Si la lista está vacía, actualizamos su subtipo
        if list_subtype == 'empty':
            new_list_type = {'type': 'list', 'subtype': element_type}
            self.update_symbol_type(list_name, new_list_type)
        else:
            # Si la lista ya tiene un tipo, verificamos compatibilidad
            if not self._types_compatible(list_subtype, element_type):
                self._error(
                    f"No se puede agregar un elemento de tipo '{self.format_type(element_type)}' "
                    f"a una lista de tipo '{self.format_type(list_symbol)}'.",
                    lineno
                )


   
    def visit_LIST_REMOVE(self, node, first_pass=False):
        if first_pass: return
        
        list_name = node["children"][0]["value"]
        lineno = node["lineno"]
        
        # 1. Verificar que la lista existe
        list_symbol = self.get_symbol(list_name, lineno)
        if not list_symbol:
            return
        
        # 2. Verificar que es una lista
        if not isinstance(list_symbol, dict) or list_symbol.get('type') != 'list':
            self._error(f"'{list_name}' no es una lista. No se puede usar remove().", lineno)
            return
        
        # 3. Obtener el tipo del índice/valor a remover
        element_to_remove = node["children"][1]
        remove_type = self.get_expr_type(element_to_remove)
        
        if remove_type == "error":
            return
        
        # 4. Verificar que el índice es un entero
        if remove_type != "int":
            self._error(
                f"El argumento de remove() debe ser de tipo 'int' (índice), "
                f"pero se encontró '{self.format_type(remove_type)}'.",
                lineno
            )

    def visit_PRINT(self, node, first_pass=False):
        if first_pass: return
        self.get_expr_type(node["children"][0])

    def visit_EXPR_STATEMENT(self, node, first_pass=False):
        if first_pass: return
        # Simplemente obtenemos el tipo de la expresion hija.
        # Esto es crucial, ya que si la expresion es un FUNC_CALL,
        # llamara a get_expr_type_FUNC_CALL, validando la llamada.
        self.get_expr_type(node["children"][0])

    def visit_IF_ELSE(self, node, first_pass=False):
        if first_pass: return
        # 1. Analiza la condición (igual que en visit_IF)
        condition_node = node["children"][0]
        if self.get_expr_type(condition_node) != "bool":
            self._error("La condición del 'if' debe ser de tipo 'bool'.", condition_node["lineno"])

        # 2. Analiza el bloque IF (con nuevo ámbito)
        self.enter_scope(f"if_block(L{node['lineno']})")
        self.visit_statement_list(node["children"][1], first_pass)
        self.exit_scope()
        
        # 3. Analiza el bloque ELSE (con nuevo ámbito)
        self.enter_scope(f"else_block(L{node['lineno']})")
        self.visit_statement_list(node["children"][2], first_pass)
        self.exit_scope()
        

    def visit_IF(self, node, first_pass=False):
        if first_pass: return
        condition_node = node["children"][0]
        if self.get_expr_type(condition_node) != "bool":
            self._error("La condición del 'if' debe ser de tipo 'bool'.", condition_node["lineno"])
        
        # Analiza el bloque 'program' (con nuevo ámbito)
        self.enter_scope(f"if_block(L{node['lineno']})")
        self.visit_statement_list(node["children"][1], first_pass)
        self.exit_scope()
        


    def visit_WHILE(self, node, first_pass=False):
        if first_pass: return
        condition_node = node["children"][0]
        if self.get_expr_type(condition_node) != "bool":
            self._error("La condición del 'while' debe ser de tipo 'bool'.", condition_node["lineno"])
        
        # Analiza el bloque 'program' (con nuevo ámbito)
        self.enter_scope(f"while_block(L{node['lineno']})")
        self.visit_statement_list(node["children"][1], first_pass)
        self.exit_scope()

    
    def visit_FOR(self, node, first_pass=False):
        if first_pass: return
        
        type_node = node["children"][0]
        var_name_node = node["children"][1]
        init_expr = node["children"][2]
        condition = node["children"][3]
        increment = node["children"][4]
        body = node["children"][5]
        
        var_name = var_name_node["value"]
        var_type = type_node["value"]
        lineno = node["lineno"]
        
        # 1. Validar que el tipo sea int
        if var_type != "int":
            self._error(
                f"La variable de control del 'for' debe ser de tipo 'int', "
                f"pero se declaró como '{var_type}'.",
                lineno
            )
        
        # 2. Validar que el valor inicial sea int
        init_type = self.get_expr_type(init_expr)
        if init_type != "int" and init_type != "error":
            self._error(
                f"El valor inicial del 'for' debe ser de tipo 'int', "
                f"pero se encontró '{self.format_type(init_type)}'.",
                init_expr["lineno"]
            )
        
        # 3. Crear nuevo scope ANTES de validar condición e incremento
        self.enter_scope(f"for_block(L{lineno})")
        
        # 4. Declarar la variable de control en el scope del for
        self.add_symbol(var_name, "int", lineno)
        
        # 5. Ahora validar la condición (puede usar la variable)
        cond_type = self.get_expr_type(condition)
        if cond_type != "bool" and cond_type != "error":
            self._error(
                f"La condición del 'for' debe ser de tipo 'bool', "
                f"pero se encontró '{self.format_type(cond_type)}'.",
                condition["lineno"]
            )
        
        # 6. Validar el incremento (usa la variable ya declarada)
        self.visit_for_increment(increment, var_name, first_pass)
        
        # 7. Analizar el cuerpo del for
        self.visit_statement_list(body, first_pass)
        
        # 8. Salir del scope
        self.exit_scope()
    
    def visit_for_increment(self, node, expected_var, first_pass):
        """Valida el nodo de incremento del for"""
        if node["type"] == "FOR_INCREMENT":
            # i++ o i--
            var_name = node["children"][0]["value"]
            if var_name != expected_var:
                self._error(
                    f"La variable de incremento '{var_name}' debe ser la misma que la variable de control '{expected_var}'.",
                    node["lineno"]
                )
        elif node["type"] == "FOR_INCREMENT_EXPR":
            # i += 1, i = i + 1, etc.
            var_name = node["children"][0]["value"]
            if var_name != expected_var:
                self._error(
                    f"La variable de incremento '{var_name}' debe ser la misma que la variable de control '{expected_var}'.",
                    node["lineno"]
                )
            # Validar la expresión
            expr_type = self.get_expr_type(node["children"][1])
            if expr_type != "int" and expr_type != "error":
                self._error(
                    f"El incremento debe usar un valor de tipo 'int', pero se encontró '{self.format_type(expr_type)}'.",
                    node["lineno"]
                )

    def visit_FUNCTION(self, node, first_pass=False):
        func_name = node["children"][1]["value"]
        lineno = node["lineno"]

        if first_pass:
            # En el primer paso, solo registramos la firma de la función
            return_type = node["children"][0]["value"]
            params = node["children"][2]
            param_types = []
            for p in params:
                # Asumiendo que p['children'][1] es el nodo 'Type'
                param_types.append(p['children'][1]['value'])
            
            func_info = {'type': 'function', 'return_type': return_type, 'param_types': param_types}
            self.add_symbol(func_name, func_info, lineno)
        else:
            # En el segundo paso, analizamos el cuerpo de la función
            body = node["children"][3]
            func_symbol = self.get_symbol(func_name, lineno)
            if not func_symbol: return # Ya se habrá reportado un error

            self.enter_scope(f"function({func_name})")
            self.current_function_return_type = func_symbol['return_type']
            params = node["children"][2]
            for param in params:
                param_name = param['children'][0]['value']
                param_type = param['children'][1]['value']
                self.add_symbol(param_name, param_type, lineno)
            
            # ¡Usa el nuevo visit_statement_list!
            self.visit_statement_list(body, first_pass) 
            
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

        return "unreachable"

    def visit_RETURN_EMPTY(self, node, first_pass=False):
        if first_pass: return
        if self.current_function_return_type is None:
            self._error("La sentencia 'return' solo puede usarse dentro de una función.", node["lineno"])
        elif self.current_function_return_type != "void":
            self._error(f"Una función que no es 'void' debe devolver un valor.", node["lineno"])

        return "unreachable"

    def get_expr_type(self, node):
        if node is None: return "error"
        method_name = f'get_expr_type_{node["type"]}'
        
        # Si el método no se encuentra, llama a self.unsupported_expr
        method = getattr(self, method_name, self.unsupported_expr)
        return method(node)

    def get_expr_type_NUMBER(self, node): return node["datatype"]
    def get_expr_type_STRING(self, node): return "string"
    def get_expr_type_BOOL(self, node): return "bool"

    def get_expr_type_NOT(self, node):
        """Valida el operador NOT (!)"""
        operand_type = self.get_expr_type(node["children"][0])
        
        if operand_type == "error":
            return "error"
        
        if operand_type != "bool":
            self._error(
                f"El operador '!' solo puede aplicarse a expresiones de tipo 'bool', "
                f"pero se encontró '{self.format_type(operand_type)}'.",
                node["lineno"]
            )
            return "error"
        
        return "bool"
    
    def get_expr_type_UNARY_MINUS(self, node):
        """Valida el operador unario menos (-)"""
        operand_type = self.get_expr_type(node["children"][0])
    
        if operand_type == "error":
            return "error"
    
        if operand_type not in ("int", "double"):
            self._error(
                f"El operador unario '-' solo puede aplicarse a números (int/double), "
                f"pero se encontró '{self.format_type(operand_type)}'.",
                node["lineno"]
            )
            return "error"
    
        return operand_type  # Mantiene el tipo (int sigue siendo int, double sigue double)
    
    def get_expr_type_INPUT(self, node):
        if node.get("children") and len(node["children"]) > 0:
            msg_type = self.get_expr_type(node["children"][0])
            if msg_type != "string" and msg_type != "error":
                self._error(
                    f"El argumento de input() debe ser de tipo 'string', "
                    f"pero se encontró '{self.format_type(msg_type)}'.",
                    node["lineno"]
                )
        return "string"

    def get_expr_type_LIST(self, node):
      # Caso 1: Lista vacía []
        if not node["children"]:
            return {'type': 'list', 'subtype': 'empty'}
        
        # Caso 2: Lista con elementos
        # Determina el tipo base usando el primer elemento
        first_type = self.get_expr_type(node["children"][0])
        if first_type == "error": return "error"

        # Comprueba que todos los demás elementos sean del mismo tipo
        for i, element_node in enumerate(node["children"][1:]):
            current_type = self.get_expr_type(element_node)
            if current_type == "error": return "error"
            
            
            if not self._types_compatible(first_type, current_type):
                self._error(f"Tipos mezclados en la lista. Se esperaba '{self.format_type(first_type)}' (del primer elemento) pero se encontró '{self.format_type(current_type)}' en el elemento {i+1}.", element_node["lineno"])
                return "error"
        
        # Si todos son compatibles, devuelve el tipo de lista parametrizado
        return {'type': 'list', 'subtype': first_type}


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
        
        # Validar división por cero
        if op == '/':
            right_node = node["children"][1]
            if right_node["type"] == 'NUMBER' and right_node["value"] == 0:
                self._error("División por cero detectada en tiempo de compilación.", lineno)
                return "error"
        
        # Validar módulo por cero
        if op == '%':
            right_node = node["children"][1]
            if right_node["type"] == 'NUMBER' and right_node["value"] == 0:
                self._error("Módulo por cero detectada en tiempo de compilación.", lineno)
                return "error"

        if left_type == "error" or right_type == "error": return "error"
        if op in ('==', '!=', '<', '>', '<=', '>='): return "bool"
        if op == '+' and ("string" in (left_type, right_type)): return "string"

        # Validar que son operaciones numéricas
        if left_type not in ("int", "double") or right_type not in ("int", "double"):
            self._error(f"Operación aritmética '{op}' inválida entre tipos '{left_type}' y '{right_type}'.", lineno)
            return "error"
        
        # Módulo solo funciona con enteros
        if op == '%':
            if left_type != "int" or right_type != "int":
                self._error(f"El operador '%' (módulo) solo funciona con tipos 'int', pero se encontró '{left_type}' y '{right_type}'.", lineno)
                return "error"
            return "int"
        
        # Potencia puede devolver double si hay exponentes negativos o decimales
        if op == '**':
            # Si ambos son int y el exponente es positivo, devuelve int
            if left_type == "int" and right_type == "int":
                right_node = node["children"][1]
                # Si el exponente es literal y positivo, devuelve int
                if right_node["type"] == 'NUMBER' and right_node["value"] >= 0:
                    return "int"
            # En cualquier otro caso, devuelve double por seguridad
            return "double"
            
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
            
            if expected_type == 'any': continue # La función acepta cualquier cosa
            
            if arg_type != "error" and arg_type != expected_type:
                self._error(f"Argumento {i+1} de '{func_name}': se esperaba tipo '{expected_type}' pero se encontró '{arg_type}'.", lineno)
        
        return func_symbol['return_type']
    
    def get_expr_type_LIST_ACCESS(self, node):
        list_name_node = node["children"][0]
        index_node = node["children"][1]
        lineno = node["lineno"]
        
        # 1. Obtener el símbolo de la lista y su tipo
        list_symbol = self.get_symbol(list_name_node["value"], lineno)
        if not list_symbol: return "error"

        # 2. Verificar que es un objeto de tipo lista
        if not isinstance(list_symbol, dict) or list_symbol.get('type') != 'list':
            self._error(f"Se está intentando acceder con índice a '{list_name_node['value']}', que no es una lista (es tipo '{self.format_type(list_symbol)}').", lineno)
            return "error"
        
        # 3. Verificar que el índice es un entero
        index_type = self.get_expr_type(index_node)
        if index_type != "int":
            self._error(f"El índice de acceso a la lista debe ser 'int', pero se encontró '{index_type}'.", lineno)
            return "error"
        
        # 4. Validar índices literales negativos
        if index_node["type"] == "NUMBER" and index_node["value"] < 0:
            self._error(f"No se permiten índices negativos. Se encontró índice: {index_node['value']}", lineno)
            return "error"
        
        # 5. Devolver el subtipo de la lista
        subtype = list_symbol.get('subtype')
        if subtype == 'empty':
            self._error(f"Se está intentando acceder a un elemento de una lista vacía ('{list_name_node['value']}').", lineno)
            return "error"
        
        return subtype
    
    def unsupported_expr(self, node):
        # Este método SÍ reporta el error antes de devolver "error"
        self._error(f"El tipo de expresión '{node['type']}' no está soportado en el análisis semántico.", node["lineno"])
        return "error"
