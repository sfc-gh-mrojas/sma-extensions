#!/usr/bin/python3
import os
import ast
import networkx as nx
import matplotlib.pyplot as plt
from rich import print
import pydot

def get_imports(file_path):
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read(), filename=file_path)
    with open(file_path, 'r') as file:
        lines = file.readlines()
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if module_name:
                to_add = module_name
                if ".." in lines[node.lineno-1]:
                    to_add = "../" + module_name
                imports.append(to_add)
            for alias in node.names:
                if alias.name == "*":
                    imports.append(f'{module_name}')
                else:
                    imports.append(f'{module_name}.{alias.name}')
    print(imports)
    return imports


def convert_and_filter_relative_imports(folder_path, imports, file_path):
    relative_dir = file_path.replace(folder_path + "/","")
    reldir = os.path.dirname(relative_dir)
    print(f"[cyan]Reviewing {file_path} [/cyan]")

    for import_reference in imports:
        reldir = os.path.dirname(relative_dir)
        if "../" in import_reference:
            reldir = os.path.dirname(reldir)
            import_reference = import_reference.replace("../","")
        possible_full_path = os.path.join(folder_path, os.path.join(reldir,import_reference.replace(".","/") + ".py"))
         
        possible_full_path = os.path.abspath(possible_full_path)
        print(f"Checking import: {import_reference} ==> {possible_full_path}, {os.path.isfile(possible_full_path)} ")
        if os.path.isfile(possible_full_path):
            yield possible_full_path.replace(folder_path,"")
        

def build_dependency_graph(folder_path):
    G = nx.DiGraph()
    G2 = pydot.Dot(graph_type='digraph')
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                imports = get_imports(file_path)
                
                inner_deps=set(convert_and_filter_relative_imports(folder_path, imports, file_path))

                for imp in inner_deps:
                    G.add_edge( folder_path + file, imp)
                    G2.add_edge(pydot.Edge(root + "/" + file, imp))
    G2.write("dependencies.dot")
    return G

def filter_existing_dependencies(G, existing_files):
    filtered_G = G.copy()
    for node in G.nodes():
        if node not in existing_files:
            filtered_G.remove_node(node)
    return filtered_G

def draw_dependency_graph(G):
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, font_weight='bold', node_size=800, node_color='skyblue', font_size=8)
    plt.show()

if __name__ == "__main__":
    target_folder = "/path/to/your/folder"  # Change this to your target folder
    target_folder = "output"
    import glob
    existing_files = [x.replace(target_folder,"") for x in glob.glob(f"{target_folder}/**/*.py", recursive=True)]

    dependency_graph = build_dependency_graph(target_folder)
    filtered_dependency_graph = filter_existing_dependencies(dependency_graph, existing_files)
    nx.nx_pydot.write_dot(filtered_dependency_graph, 'dependency_graph.dot')
    draw_dependency_graph(filtered_dependency_graph)
