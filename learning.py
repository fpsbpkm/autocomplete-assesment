import preprocess
import os
import re
import glob, json

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

DATA_DIR = 'data'
MML_VCT = os.path.join('.', DATA_DIR, 'mml.vct')
MML_DIR = '/mnt/c/mizar/mml'
data = {}

N = 2

def count_ngram(tokens, n):
    # variable_history = create_variable_history()
    variable_to_type = {}
    decleared_cnt = 0

    for line in tokens:

        # 変数を型に置き換える処理
        replaced_line = []
        for i in range(len(line)):

            if is_variable(line, i) and is_replaced_variable:
                replaced_line.append('___')
            else:
                matched = re.match(r'__\w+_', line[i])
                if matched:
                    replaced_line.append(re.sub(r'__\w+_' ,'', line[i]))
                else:
                    replaced_line.append(line[i])
    
        # N-gramのパターンを保存，カウントする処理
        for i in range(len(line)-n+1):
            temp = replaced_line[i:i+n]
            key = ' '.join(temp)
            if not key in data:
                data[key] = 1
            else:
                data[key] += 1

if __name__ == '__main__':

    mml_lar = open("/mnt/c/mizar/mml.lar", "r")

    mizar_files = glob.glob(os.path.join(MML_DIR, '*.miz'))
    # mizar_files = [os.path.join(MML_DIR, "graph_3a.miz")]
    lexer = preprocess.Lexer()
    lexer.load_symbol_dict(MML_VCT)
    lexer.build_len2symbol()
    count = 0
    results = []

    mml = []
    for i in mml_lar.readlines():
        mml.append(os.path.join(MML_DIR, i.replace('\n', '.miz')))

    for filepath in mml:
        count += 1
        # 本来は1100で終了
        if count == 1100:
            break
        lines = None
        with open(filepath, 'r') as f:
            try:
                lines = f.readlines()
                assert len(lines) > 0
            except:
                continue
        print(filepath)
        
        env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
        env_lines = lexer.remove_comment(env_lines)
        text_proper_lines = lexer.remove_comment(text_proper_lines)
        try:
            tokenized_lines, position_map = lexer.lex(text_proper_lines)
        except Exception:
            continue
        tokens = []
        for line in tokenized_lines:
            # i = re.sub('__\w+_', '', i)
            tokens.append(line.split())

        count_ngram(tokens, N)
        
    result = sorted(data.items(), key=lambda x:x[1], reverse=True)

    result_list = [i[0] for i in result if i[1] >= 10]
    completions = {'completions': result_list}

    with open('./jsons/output2_10(replaced=False).json', 'w') as f:
        json.dump(completions, f)

    mml_lar.close()
