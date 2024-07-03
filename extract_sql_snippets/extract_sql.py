# you might need to install astor
import os
import ast
import argparse
import astor
import rich
import csv
snippet_count = 0

class SnippetReporter:
    def __init__(self):
        self.snippets_info = []
    def report(self, file_path,id, snippet,snippet_index,line):
        self.snippets_info.append({"file":file_path, "id":id,"LOC":snippet.count("\n") + (1 if len(snippet) > 0 else 0), "chars": len(snippet),"index": snippet_index, "line": line})
    def to_file(self, output):
        with open(output, 'w', newline='') as csvfile:
            fieldnames = ['file', 'index','line','id','LOC','chars']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for x in self.snippets_info:
                writer.writerow(x)

class SQLExtractor(ast.NodeTransformer):

    def __init__(self,current_file, output_scripts, reporter:SnippetReporter):
        self.output_scripts = output_scripts
        self.found = False
        self.current_file = current_file
        self.self_snippet_count = 0
        self.reporter = reporter
    def visit_Call(self, node):
        global snippet_count
        if isinstance(node.func, ast.Attribute
            ) and node.func.attr == 'sql' and isinstance(node.func.value,
            ast.Name) and (node.func.value.id == 'spark' or node.func.value
            .id == 'session'):
            if len(node.args) == 1:
                sql_text_node = node.args[0]
                if isinstance(sql_text_node, ast.Constant) and isinstance(
                    sql_text_node.value, str):
                    sql_text = sql_text_node.value
                elif isinstance(sql_text_node, ast.JoinedStr):
                    sql_text = ''.join([(part.value if isinstance(part, ast
                        .Constant) else '{' + astor.to_source(part.value).
                        strip() + '}') for part in sql_text_node.values])
                else:
                    return node
                snippet_filename = f'snippet{snippet_count:04}.sql'
                snippet_path = os.path.join(self.output_scripts,snippet_filename)
                with open(snippet_path, 'w') as snippet_file:
                    snippet_file.write(sql_text)
                name = f'___snippet{snippet_count:04}___'
                new_arg = ast.Constant(value=name, kind=None)
                node.args[0] = new_arg
                snippet_count += 1
                self.self_snippet_count += 1
                self.found = True
                self.reporter.report(self.current_file,name,sql_text,self.self_snippet_count, node.lineno)
        self.generic_visit(node)
        return node


def process_file(file_path, output_preprocessed, output_scripts, reporter):
    with open(file_path, 'r') as f:
        code = f.read()
    tree = ast.parse(code)
    extractor = SQLExtractor(file_path,output_scripts, reporter)
    new_tree = extractor.visit(tree)
    ast.fix_missing_locations(new_tree)
    new_code = astor.to_source(new_tree)
    preprocessed_path = os.path.join(output_preprocessed,file_path)
    os.makedirs(os.path.dirname(preprocessed_path), exist_ok=True)
    with open(preprocessed_path, 'w') as f:
        f.write(new_code)


def main(input_folder, output_preprocessed, output_scripts):
    if not os.path.exists(output_preprocessed):
        os.makedirs(output_preprocessed)
    if not os.path.exists(output_scripts):
        os.makedirs(output_scripts)
    reporter = SnippetReporter()
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.py'):
                if os.path.abspath(output_preprocessed) == os.path.abspath(root):
                    continue
                process_file(os.path.join(root, file), output_preprocessed,
                    output_scripts, reporter)
    reporter.to_file(os.path.join(output_scripts, 'snippets.csv'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
        'Process spark.sql calls with SQL literals.')
    parser.add_argument('--input-folder', type=str, required=True, help=
        'Folder containing the input .py files')
    parser.add_argument('--output-preprocessed', type=str, required=True,
        help='Folder to save the preprocessed .py files')
    parser.add_argument('--output-scripts', type=str, required=True, help=
        'Folder to save the extracted SQL scripts')
    args = parser.parse_args()
    main(args.input_folder, args.output_preprocessed, args.output_scripts)
