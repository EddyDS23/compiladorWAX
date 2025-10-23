class CodeGenerator:
    def __init__(self):
        self.indent_level = 0

    def indent(self):
        return "    " * self.indent_level

    def generate(self, ast):
        code_lines = []
        for node in ast:
            line = self.gen_node(node)
            if line:
                code_lines.append(line)
        return "\n".join(code_lines)

    def gen_node(self, node):
        ntype = node["type"]

        # === Declaraciones de variables ===
        if ntype == "DECL":
            name = node["name"]
            expr = self.gen_node(node["value"])
            return f"{name} = {expr}"

        # === Expresiones ===
        elif ntype == "INT":
            return str(node["value"])
        elif ntype == "DOUBLE":
            return str(node["value"])
        elif ntype == "STRING":
            return f"\"{node['value']}\""
        elif ntype == "BOOL":
            return "True" if node["value"] else "False"
        elif ntype == "IDENT":
            return node["value"]
        elif ntype == "BINOP":
            left = self.gen_node(node["left"])
            right = self.gen_node(node["right"])
            return f"({left} {node['op']} {right})"

        # === Print ===
        elif ntype == "PRINT":
            expr = self.gen_node(node["value"])
            return f"print({expr})"

        # === Comentarios ===
        elif ntype == "COMMENT_LINE":
            # Un comentario de línea (# ...) ya es válido en Python
            return f"# {node['value'][1:].strip()}"
        elif ntype == "COMMENT_BLOCK":
            return self.format_block_comment(node["value"])

        # === Errores (se convierten en comentarios) ===
        elif ntype == "ERROR":
            return f"# {node['value']}"

        return None

    # --- Formateador de comentarios de bloque ---
    def format_block_comment(self, text):
        # Quitar los delimitadores /* y */
        content = text[2:-2].strip()
        # Separar por líneas
        lines = content.split("\n")
        # Anteponer # a cada línea
        return "\n".join(f"# {line.strip()}" for line in lines)
