# utils.py
# Contiene funciones de ayuda, como la visualización del AST.
import graphviz

def print_ast(node, prefix="", is_last=True):
    if isinstance(node, (list, tuple)):
        for i, n in enumerate(node):
            print_ast(n, prefix, i == len(node)-1)
        return

    # Ignora nodos None que pueden venir de sentencias vacías o comentarios
    if not isinstance(node, dict):
        return

    connector = "└── " if is_last else "├── "
    datatype = f" ({node.get('datatype')})" if node.get('datatype') else ""
    value = f": {node.get('value')}" if node.get('value') is not None else ""
    lineno = f" [linea {node.get('lineno')}]" if node.get('lineno') else ""
    print(f"{prefix}{connector}{node['type']}{datatype}{value}{lineno}")

    children = node.get("children", [])
    for i, child in enumerate(children):
        # El prefijo para los hijos cambia dependiendo si este es el último nodo
        child_prefix = prefix + ("    " if is_last else "│   ")
        print_ast(child, child_prefix, i == len(children)-1)
        
        
class ASTVisualizer:
    def __init__(self):
        self.dot = graphviz.Digraph('AST', comment='Abstract Syntax Tree')
        self.dot.attr('node', shape='box')
        self.seq = 0

    def visit(self, node, parent=None):
        if isinstance(node, (list, tuple)):
            for item in node:
                self.visit(item, parent)
            return

        if not isinstance(node, dict):
            return

        # Crea un nombre único para el nodo actual
        node_name = f'node{self.seq}'
        self.seq += 1

        # Crea la etiqueta del nodo con su información
        label = f"{node['type']}"
        if node.get('value') is not None:
            label += f"\\nvalue: {node['value']}"
        if node.get('datatype') is not None:
            label += f"\\ndatatype: {node['datatype']}"
        
        self.dot.node(node_name, label)

        # Si tiene un padre, dibuja una flecha
        if parent:
            self.dot.edge(parent, node_name)

        # Visita a los hijos
        for child in node.get('children', []):
            self.visit(child, node_name)

    def visualize(self, ast, filename='ast_output'):
        self.visit(ast)
        self.dot.render(filename, view=True, format='png')
        print(f"Árbol guardado como {filename}.png")
