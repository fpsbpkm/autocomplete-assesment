import preprocess
from emparser import Parser
import os,pprint

DATA_DIR = 'data'
MML_VCT = os.path.join(DATA_DIR, 'mml.vct')

print(MML_VCT)

lexer = preprocess.Lexer()
lexer.load_symbol_dict(MML_VCT)
lexer.build_len2symbol()

mml_dir = '/mnt/c/mizar/mml'
filename = 'aff_1.miz'
filepath = os.path.join(mml_dir, filename)

tmp = os.path.splitext(os.path.basename(filepath))[0]
output_path = tmp + '.xml'

with open(filepath, 'r') as f:
    lines = f.readlines()

    env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
    text_proper_lines = lexer.remove_comment(text_proper_lines)
    tokenized_lines, position_map = lexer.lex(text_proper_lines, first_line_number=len(env_lines)+1)

    txt = '\n'.join(tokenized_lines)
    # print(txt)
    p = Parser()
    tp_xmlstr = p.parse_text_proper(txt, position_map)

    with open(output_path, 'w') as f:
        f.write(tp_xmlstr)
