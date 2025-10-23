# lexer.py
# Contiene toda la lógica para el análisis léxico (reconocimiento de tokens).

import ply.lex as lex

# ==============================
# LÉXICO
# ==============================
keywords = {
    "wax": "WAX",
    "function": "FUNCTION",
    "print": "PRINT",
    "input": "INPUT",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "return": "RETURN",
    "true": "BOOL",
    "false": "BOOL",
    "str": "STR",
    "void":"VOID",
}

tokens = (
    "IDENT","INT","DOUBLE","STRING",
    "PLUS","MINUS","STAR","SLASH",
    "EQUAL","EQEQ","NOTEQ","LT","GT","LE","GE",
    "AND","OR",
    "SEMI","LPAREN","RPAREN","LBRACE","RBRACE",
    "COLON","COMMA","LBRACKET","RBRACKET",
    "COMMENT_LINE","COMMENT_BLOCK"
) + tuple(keywords.values())

# Símbolos
t_PLUS   = r"\+"
t_MINUS  = r"-"
t_STAR   = r"\*"
t_SLASH  = r"/"
t_EQEQ   = r"=="
t_NOTEQ  = r"!="
t_LE     = r"<="
t_GE     = r">="
t_LT     = r"<"
t_GT     = r">"
t_EQUAL  = r"="
t_AND    = r"&&"
t_OR     = r"\|\|"
t_SEMI   = r";"
t_COMMA  = r","
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"
t_COLON  = r":"
t_ignore = " \t"

def t_COMMENT_LINE(t):
    r"\#.*"
    pass

def t_COMMENT_BLOCK(t):
    r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/"
    t.lexer.lineno += t.value.count("\n")
    pass

def t_IDENT(t):
    r"[a-zA-Z_][a-zA-Z0-9_]*"
    if t.value in ("true","false"):
        t.type = "BOOL"
        t.value = True if t.value == "true" else False
    elif t.value in keywords:
        t.type = keywords[t.value]
    return t

def t_DOUBLE(t):
    r"\d+\.\d+"
    t.value = float(t.value)
    return t

def t_INT(t):
    r"\d+"
    t.value = int(t.value)
    return t

def t_STRING(t):
    r'"([^"\\]|\\.)*"'
    raw = t.value[1:-1]
    t.value = bytes(raw,"utf-8").decode("unicode_escape")
    return t

def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}")
    t.lexer.skip(1)

# Construye el lexer
lexer = lex.lex()