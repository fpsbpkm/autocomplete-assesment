import preprocess
import os
import re
import glob, json
from pprint import pprint

DATA_DIR = '/home/fpsbpkm/emparser/build/lib.linux-x86_64-3.7/emparser/data/'
MML_VCT = os.path.join(DATA_DIR, 'mml.vct')
MML_DIR = '/mnt/c/mizar/mml'

RESERVED_WORDS = set(['according','aggregate','all','and','antonym','are','as',
  'associativity','assume','asymmetry','attr','be','begin','being','by',
  'canceled','case','cases','cluster','coherence','commutativity',
  'compatibility','connectedness','consider','consistency','constructors',
  'contradiction','correctness','def','deffunc','define','definition',
  'definitions','defpred','do','does','end','environ','equals','ex','exactly',
  'existence','for','from','func','given','hence','hereby','holds',
  'idempotence','identify','if','iff','implies','involutiveness',
  'irreflexivity','is','it','let','means','mode','non','not','notation',
  'notations','now','of','or','otherwise','over','per','pred','prefix',
  'projectivity','proof','provided','qua','reconsider','reduce','reducibility',
  'redefine','reflexivity','registration','registrations','requirements',
  'reserve','sch','scheme','schemes','section','selector','set','sethood','st',
  'struct','such','suppose','symmetry','synonym','take','that','the','then',
  'theorem','theorems','thesis','thus','to','transitivity','uniqueness',
  'vocabularies','when','where','with','wrt'])

SPECIAL_SYMBOLS = set([',', ';', ':', '(', ')', '[', ']', '{', '}', '=', '&',
    '->', '.=', '$1', '$2', '$3','$4','$5','$6','$7','$8','$9', '(#', '#)',
    '...', '$10'])

NUMBERS = set(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])


def is_reserved_word(word):
    if word in RESERVED_WORDS or token in SPECIAL_SYMBOLS:
        return True
    else:
        return False

def check_token_type(line,idx):
    token = line[idx]
    matched = re.match(r'__\w+_', token)
    # NOTE:ラベル以降の判定が正しくない
    if matched:
        return matched[0]
    elif is_reserved_word(token):
        return token
    elif token in NUMBERS:
        return "__number_"
    elif idx+1 <= len(line)-1 and line[idx+1] == ':':
        return "__label_"
    elif 'by' in set(line[:idx]):
        return "__label_"
    elif 'from' in set(line[:idx]):
        return "__label_"
    else:
        return "__variable_"


if __name__ == '__main__':
    mml_lar = open("/mnt/c/mizar/mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(i.replace('\n', ''))
    
    for filename in mml:

        f = os.path.join(MML_DIR, filename)+'.miz'
        lexer = preprocess.Lexer()
        lexer.load_symbol_dict(MML_VCT)
        lexer.build_len2symbol()

        with open(f, 'r') as f:
            # ファイルによっては変数名のエラーが出るため注意
            try:
                lines = f.readlines()
                assert len(lines) > 0
            except:
                continue
            env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
            text_proper_lines = lexer.remove_comment(text_proper_lines)
            # トークンの取得
            try:
                tokenized_lines, position_map = lexer.lex(text_proper_lines)
            except Exception:
                continue
            tokens = []
            for line in tokenized_lines:
                tokens.append(line.split())
        
        OUTPUT_DIR = "/home/fpsbpkm/emparser/build/lib.linux-x86_64-3.7/emparser/learning_data"
        output_file = os.path.join(OUTPUT_DIR, filename)+'.json'
        data = []
        # 「let x be Nat」の場合，
        # [(let, let), (x, variable), (Nat, M)]の形式にしたjsonファイルを作成
        for line in tokens:
            line_data = []
            for i in range(len(line)):
                token = re.sub(r'__\w+_', '', line[i])
                token_type = check_token_type(line, i)
                line_data.append([token, token_type])
            if line_data:
                data.append(line_data)
        
        with open(output_file, 'w') as f:
            json.dump(data, f)
        print(filename)