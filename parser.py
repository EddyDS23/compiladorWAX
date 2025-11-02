# parser.py
# Contiene toda la lógica para el análisis sintáctico (gramática y construcción del AST).
# Este archivo DEPENDE de 'lexer.py' para la lista de tokens.

import ply.yacc as yacc
from lexer import tokens,lexer
import sys

# ==============================
# SINTÁCTICO (AST)
# ==============================
def make_node(type, children=None, value=None, datatype=None, lineno=None):
    return {"type": type, "children": children or [], "value": value, "datatype": datatype, "lineno": lineno}

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("right", "NOT"),
     ("right", "UMINUS"), 
    ("left", "EQEQ", "NOTEQ", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "STAR", "SLASH","MOD"),
    ("right", "POW"),
)

# ---------- PROGRAM ----------
def p_program(p):
    """program : program statement
               | statement
               | empty"""
    if len(p) == 3:
        if p[2] is not None:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = p[1]
    elif len(p) == 2 and p[1] is not None:
        p[0] = [p[1]]
    else:
        p[0] = []

# ---------- STATEMENTS ----------
def p_statement_comment(p):
    """statement : COMMENT_LINE
                 | COMMENT_BLOCK"""
    p[0] = None # Ignoramos los comentarios en el AST final

def p_statement_decl(p):
    """statement : WAX IDENT COLON IDENT EQUAL expression SEMI"""
    type_node = make_node("Type", value=p[4], lineno=p.lineno(4))
    id_node = make_node("Identifier", value=p[2], lineno=p.lineno(2))
    p[0] = make_node("DECLARATION", [type_node, id_node, p[6]], lineno=p.lineno(1))

def p_statement_assignment(p):
    """statement : IDENT EQUAL expression SEMI"""
    id_node = make_node("Identifier", value=p[1], lineno=p.lineno(1))
    p[0] = make_node("ASSIGN", [id_node, p[3]], lineno=p.lineno(1))

def p_statement_compound_assignment(p):
    """statement : IDENT PLUSEQ expression SEMI
                 | IDENT MINUSEQ expression SEMI
                 | IDENT STAREQ expression SEMI
                 | IDENT SLASHEQ expression SEMI"""
    id_node = make_node("Identifier", value=p[1], lineno=p.lineno(1))
    operator = p[2]  # +=, -=, *=, /=
    p[0] = make_node("ASSIGN_COMPOUND", [id_node, p[3]], value=operator, lineno=p.lineno(1))

def p_statement_increment(p):
    """statement : IDENT PLUSPLUS SEMI
                 | IDENT MINUSMINUS SEMI
                 | PLUSPLUS IDENT SEMI
                 | MINUSMINUS IDENT SEMI"""
    if p[2] in ('++', '--'):
        # Post-incremento/decremento: i++; o i--;
        id_node = make_node("Identifier", value=p[1], lineno=p.lineno(1))
        operator = p[2]
    else:
        # Pre-incremento/decremento: ++i; o --i;
        id_node = make_node("Identifier", value=p[2], lineno=p.lineno(2))
        operator = p[1]
    
    p[0] = make_node("INCREMENT", [id_node], value=operator, lineno=p.lineno(1))

def p_statement_multi_assignment(p):
    """statement : ident_list EQUAL expression_list SEMI"""
    p[0] = make_node("ASSIGN_MULTI", [p[1], p[3]], lineno=p.lineno(1))

def p_statement_list_append(p):
    """statement : IDENT DOT APPEND LPAREN expression RPAREN SEMI"""
    list_node = make_node("IDENT", value=p[1], lineno=p.lineno(1))
    p[0] = make_node("LIST_APPEND", [list_node, p[5]],lineno=p.lineno(1))

def p_statement_list_remove(p):
    """statement : IDENT DOT REMOVE LPAREN expression RPAREN SEMI"""
    list_node = make_node("IDENT", value=p[1], lineno=p.lineno(1))
    p[0] = make_node("LIST_REMOVE", [list_node, p[5]], lineno=p.lineno(1))


def p_statement_if(p):
    """statement : IF LPAREN expression RPAREN LBRACE program RBRACE
                 | IF LPAREN expression RPAREN LBRACE program RBRACE ELSE LBRACE program RBRACE"""
    if len(p) == 8:
        p[0] = make_node("IF", [p[3], p[6]], lineno=p.lineno(1))
    else:
        p[0] = make_node("IF_ELSE", [p[3], p[6], p[10]], lineno=p.lineno(1))

def p_statement_for(p):
    """statement : FOR LPAREN WAX IDENT COLON IDENT EQUAL expression SEMI expression SEMI for_increment RPAREN LBRACE program RBRACE"""
    # for (wax i:int = 0; i < 10; i++) { ... }
    var_name = p[4]      # i
    var_type = p[6]      # int
    init_value = p[8]    # 0
    condition = p[10]    # i < 10
    increment = p[12]    # nodo de incremento
    body = p[15]         # program
    
    type_node = make_node("Type", value=var_type, lineno=p.lineno(6))
    id_node = make_node("Identifier", value=var_name, lineno=p.lineno(4))
    
    p[0] = make_node("FOR", [type_node, id_node, init_value, condition, increment, body], lineno=p.lineno(1))

def p_for_increment(p):
    """for_increment : IDENT PLUSPLUS
                     | IDENT MINUSMINUS
                     | PLUSPLUS IDENT
                     | MINUSMINUS IDENT
                     | IDENT PLUSEQ expression
                     | IDENT MINUSEQ expression
                     | IDENT STAREQ expression
                     | IDENT SLASHEQ expression
                     | IDENT EQUAL expression"""
    if len(p) == 3:
        if p[2] in ('++', '--'):
            # i++ o i--
            id_node = make_node("Identifier", value=p[1], lineno=p.lineno(1))
            p[0] = make_node("FOR_INCREMENT", [id_node], value=p[2], lineno=p.lineno(1))
        else:
            # ++i o --i
            id_node = make_node("Identifier", value=p[2], lineno=p.lineno(2))
            p[0] = make_node("FOR_INCREMENT", [id_node], value=p[1], lineno=p.lineno(1))
    elif len(p) == 4:
        # i += 1, i -= 1, i *= 2, i /= 2, i = i + 1
        id_node = make_node("Identifier", value=p[1], lineno=p.lineno(1))
        p[0] = make_node("FOR_INCREMENT_EXPR", [id_node, p[3]], value=p[2], lineno=p.lineno(1))

def p_statement_while(p):
    "statement : WHILE LPAREN expression RPAREN LBRACE program RBRACE"
    p[0] = make_node("WHILE", [p[3], p[6]], lineno=p.lineno(1))

def p_statement_print(p):
    "statement : PRINT LPAREN expression RPAREN SEMI"
    p[0] = make_node("PRINT", [p[3]], lineno=p.lineno(1))

def p_return_type(p):
    """return_type : IDENT
                   | VOID"""
    p[0] = make_node("Type", value=p[1], lineno=p.lineno(1))

def p_statement_return_value(p):
    """statement : RETURN expression_list SEMI"""
    p[0] = make_node("RETURN_VALUE", p[2], lineno=p.lineno(1))

def p_statement_return_empty(p):
    """statement : RETURN SEMI"""
    p[0] = make_node("RETURN_EMPTY", lineno=p.lineno(1))

def p_statement_func(p):
    "statement : WAX FUNCTION IDENT COLON return_type LPAREN paramlist RPAREN LBRACE program RBRACE"
    id_node = make_node("Identifier", value=p[3], lineno=p.lineno(3))
    p[0] = make_node("FUNCTION", [p[5], id_node, p[7], p[10]], lineno=p.lineno(1))

def p_statement_expression(p):
    """statement : expression SEMI"""
    p[0] = make_node("EXPR_STATEMENT", [p[1]], lineno=p.lineno(2))

# ---------- EXPRESSIONS ----------
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression STAR expression
                  | expression SLASH expression
                  | expression MOD expression
                  | expression POW expression"""
    p[0] = make_node("BINOP", [p[1], p[3]], value=p[2], lineno=p.lineno(2))

def p_expression_comparison(p):
    """expression : expression LT expression
                  | expression LE expression
                  | expression GT expression
                  | expression GE expression
                  | expression EQEQ expression
                  | expression NOTEQ expression"""
    p[0] = make_node("BINOP", [p[1], p[3]], value=p[2], datatype="bool", lineno=p.lineno(2))

def p_expression_logic(p):
    """expression : expression AND expression
                  | expression OR expression"""
    p[0] = make_node("LOGIC", [p[1], p[3]], value=p[2], datatype="bool", lineno=p.lineno(2))

def p_expression_group(p):
    "expression : LPAREN expression RPAREN"
    p[0] = p[2]

def p_expression_number(p):
    """expression : INT
                  | DOUBLE"""
    datatype = "int" if isinstance(p[1], int) else "double"
    p[0] = make_node("NUMBER", value=p[1], datatype=datatype, lineno=p.lineno(1))

def p_expression_string(p):
    "expression : STRING"
    p[0] = make_node("STRING", value=p[1], datatype="string", lineno=p.lineno(1))

def p_expression_bool(p):
    "expression : BOOL"
    p[0] = make_node("BOOL", value=p[1], datatype="bool", lineno=p.lineno(1))

def p_expression_not(p):
    """expression : NOT expression"""
    p[0] = make_node("NOT", [p[2]], lineno=p.lineno(1))

def p_expression_unary_minus(p):
    """expression : MINUS expression %prec UMINUS"""
    p[0] = make_node("UNARY_MINUS", [p[2]], lineno=p.lineno(1))

def p_expression_ident(p):
    "expression : IDENT"
    p[0] = make_node("IDENT", value=p[1], lineno=p.lineno(1))

def p_expression_list(p):
    "expression : LBRACKET list_items RBRACKET"
    p[0] = make_node("LIST", p[2], lineno=p.lineno(1))

def p_list_items(p):
    """list_items : list_items COMMA expression
                  | expression
                  | empty"""
    if len(p) == 4: p[0] = p[1] + [p[3]]
    elif len(p) == 2: p[0] = [] if p[1] is None else [p[1]]

def p_expression_list_access(p):
    "expression : IDENT LBRACKET expression RBRACKET"
    p[0] = make_node("LIST_ACCESS", [make_node("IDENT", value=p[1], lineno=p.lineno(1)), p[3]], lineno=p.lineno(1))

def p_expression_func_call(p):
    "expression : IDENT LPAREN arglist RPAREN"
    id_node = make_node("IDENT", value=p[1], lineno=p.lineno(1))
    p[0] = make_node("FUNC_CALL", [id_node] + p[3], lineno=p.lineno(1))

def p_expression_str_call(p):
    "expression : STR LPAREN expression RPAREN"
    p[0] = make_node("FUNC_CALL", [make_node("IDENT", value="str", lineno=p.lineno(1)), p[3]], lineno=p.lineno(1))

def p_expression_input(p):
    """expression : INPUT LPAREN RPAREN
                  | INPUT LPAREN expression RPAREN"""
    if len(p) == 4:
        p[0] = make_node("INPUT", datatype="string", lineno=p.lineno(1))
    else:
        p[0] = make_node("INPUT", [p[3]], datatype="string", lineno=p.lineno(1))

# ---------- LISTAS Y PARÁMETROS ----------
def p_arglist(p):
    """arglist : arglist COMMA expression
               | expression
               | empty"""
    if len(p) == 4: p[0] = p[1] + [p[3]]
    elif len(p) == 2: p[0] = [] if p[1] is None else [p[1]]

def p_expression_list_values(p):
    """expression_list : expression_list COMMA expression
                       | expression"""
    if len(p) == 4: p[0] = p[1] + [p[3]]
    else: p[0] = [p[1]]

def p_ident_list(p):
    """ident_list : ident_list COMMA IDENT
                  | IDENT"""
    if len(p) == 4: p[0] = p[1] + [make_node("IDENT", value=p[3], lineno=p.lineno(3))]
    else: p[0] = [make_node("IDENT", value=p[1], lineno=p.lineno(1))]

def p_paramlist(p):
    """paramlist : paramlist COMMA IDENT COLON IDENT
                 | IDENT COLON IDENT
                 | empty"""
    if len(p) == 6:
        param_node = make_node("PARAM", [make_node("Identifier", value=p[3]), make_node("Type", value=p[5])])
        p[0] = p[1] + [param_node]
    elif len(p) == 4:
        param_node = make_node("PARAM", [make_node( "Identifier", value=p[1]), make_node("Type", value=p[3])])
        p[0] = [param_node]
    else:
        p[0] = []

def p_empty(p):
    "empty :"
    p[0] = None

# ---------- ERRORES ----------
def p_error(p):
    if p:
        # Error estándar: un token inesperado
        print(f"[Error Sintáctico] Token inesperado {p.type} ('{p.value}') en línea {p.lineno}",file=sys.stderr)
    else:
        # Error de "Fin inesperado de la entrada" (EOF)
        print(f"[Error Sintáctico] Fin inesperado de la entrada.",file=sys.stderr)
        
        # Accedemos a la pila interna del parser
        stack = parser.symstack
        
        # Buscamos de arriba hacia abajo (reversed) en la pila
        # por el último token de apertura que no se cerró.
        for sym in reversed(stack):
            # 'sym' puede ser un No-Terminal (sin 'type') o un Token (con 'type')
            if hasattr(sym, 'type'):
                if sym.type == 'LBRACE': # '{'
                    print(f"    > Sugerencia: Revisa si falta un '}}' (llave de cierre) para el bloque que comenzó en la línea {sym.lineno}.",file=sys.stderr)
                    return
                if sym.type == 'LPAREN': # '('
                    print(f"    > Sugerencia: Revisa si falta un ')' (paréntesis de cierre) para la expresión que comenzó en la línea {sym.lineno}.",file=sys.stderr)
                    return

        # Si no encontramos un token específico, damos la sugerencia genérica
        print(f"    > Sugerencia: Revisa si falta un '}}' o ';' en algún lugar.",file=sys.stderr)

# Construye el parser
parser = yacc.yacc()