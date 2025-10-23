# parser.py
# Contiene toda la lógica para el análisis sintáctico (gramática y construcción del AST).
# Este archivo DEPENDE de 'lexer.py' para la lista de tokens.

import ply.yacc as yacc
from lexer import tokens

# ==============================
# SINTÁCTICO (AST)
# ==============================
def make_node(type, children=None, value=None, datatype=None, lineno=None):
    return {"type": type, "children": children or [], "value": value, "datatype": datatype, "lineno": lineno}

precedence = (
    ("left", "OR"),
    ("left", "AND"),
    ("left", "EQEQ", "NOTEQ", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "STAR", "SLASH"),
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

def p_statement_multi_assignment(p):
    """statement : ident_list EQUAL expression_list SEMI"""
    p[0] = make_node("ASSIGN_MULTI", [p[1], p[3]], lineno=p.lineno(1))

def p_statement_if(p):
    """statement : IF LPAREN expression RPAREN LBRACE program RBRACE
                 | IF LPAREN expression RPAREN LBRACE program RBRACE ELSE LBRACE program RBRACE"""
    if len(p) == 8:
        p[0] = make_node("IF", [p[3], p[6]], lineno=p.lineno(1))
    else:
        p[0] = make_node("IF_ELSE", [p[3], p[6], p[10]], lineno=p.lineno(1))

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

# ---------- EXPRESSIONS ----------
def p_expression_binop(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression STAR expression
                  | expression SLASH expression"""
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
    """expression : INPUT LPAREN RPAREN"""
    p[0] = make_node("INPUT", datatype="string", lineno=p.lineno(1))

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
        param_node = make_node("PARAM", [make_node("Identifier", value=p[1]), make_node("Type", value=p[3])])
        p[0] = [param_node]
    else:
        p[0] = []

def p_empty(p):
    "empty :"
    p[0] = None

# ---------- ERRORES ----------
def p_error(p):
    if p:
        print(f"[Error Sintáctico] Token inesperado {p.type} ('{p.value}') en línea {p.lineno}")
    else:
        print("[Error Sintáctico] Fin inesperado de la entrada")

# Construye el parser
parser = yacc.yacc()