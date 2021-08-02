# raw-ngramモデル用
# 移植予定

import preprocess
import os
import re
import glob, json

DATA_DIR = 'data'
MML_VCT = os.path.join('.', DATA_DIR, 'mml.vct')
MML_DIR = '/mnt/c/mizar/mml'
key_word_sequence_data = {}
N = 4

def count_ngram(tokens, n):
    # variable_history = create_variable_history()
    variable_to_type = {}
    decleared_cnt = 0

    for line in tokens:

        replaced_line = []
        # 接頭辞を消す処理
        for i in range(len(line)):
            matched = re.match(r'__(\w\d*)_', line[i])
            if matched:
                replaced_line.append(re.sub(r'__(\w\d*)_' ,'', line[i]))
            else:
                replaced_line.append(line[i])
    
        # N-gramのパターンを保存，カウントする処理
        for i in range(len(line)-n+1):
            keyword_sequence = replaced_line[i:i+n]
            key = ' '.join(keyword_sequence)
            if not key in key_word_sequence_data:
                key_word_sequence_data[key] = 1
            else:
                key_word_sequence_data[key] += 1

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
            # i = re.sub('__(\w\d*)_', '', i)
            tokens.append(line.split())

        count_ngram(tokens, N)
        
    result = sorted(key_word_sequence_data.items(), key=lambda x:x[1], reverse=True)

    result_list = [i[0] for i in result if i[1] >= 100]
    completions = {'completions': result_list}

    with open('./jsons/output4.json', 'w') as f:
        json.dump(completions, f)

    mml_lar.close()
