import re
import preprocess
import pprint
import os
import time
import glob
import codecs
from completion import provide_items
import copy
from raw_ngram import RawNgram

DATA_DIR = './data'
MML_VCT = os.path.join(DATA_DIR, 'mml.vct')
MML_DIR = '/mnt/c/mizar/mml'

lexer = preprocess.Lexer()
lexer.load_symbol_dict(MML_VCT)
lexer.build_len2symbol()

file_name = "/mnt/c/mizar/mml/nomin_6.miz"

N = 3

def count_line_keystroke(token_list):

    for i in token_list:
        pass

    line_cost = len(token_list[0])

    for i in range(1, len(token_list)):
        items, answer = provide_items(token_list, i, N)

        token_cost = len(answer)

        if token_cost <= 1:
            line_cost += token_cost
        elif answer in set(items):
            input_idx = 0
            while token_cost >= 2:
                select_cost = items.index(answer) + 1
                if select_cost < token_cost:
                    line_cost += select_cost
                    print(f"{answer[:input_idx], answer, select_cost}")
                    print(f"{token_cost-select_cost}の節約")
                    break
                else:
                    input_idx += 1
                    line_cost += 1
                    token_cost -= 1
                    # 残りのコストが2未満の場合は，節約にならないため，残りのコストを加えて終了
                    if token_cost < 2:
                        line_cost += token_cost
                        break
                    tmp = []
                    for i in items:
                        if i.startswith(answer[:input_idx]):
                            tmp.append(i)
                    # ユーザが新たに入力するため，候補を更新
                    items = copy.copy(tmp)            
        else:
            line_cost += token_cost
    
    return line_cost

if __name__ == '__main__':

    with open(file_name, 'r') as f:
        lines = f.readlines()

        env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
        text_proper_lines = lexer.remove_comment(text_proper_lines)

        tokenized_lines, position_map = lexer.lex(text_proper_lines)
        
        word_count = 0
        token_count = 0
        autocomplete_cost = 0
        
        for line in tokenized_lines:
            # 正規表現が完全ではないため，シンボルなどが置き換えられて文字数が少なくなっていたかも
            line = re.sub('__\w\d*_', '', line)
            token_list = line.split(" ")
            original_line_cost = 0
            for token in token_list:
                token_count += 1
                original_line_cost += len(token)
                word_count += len(token)
            
            line_cost = count_line_keystroke(token_list)
            autocomplete_cost += line_cost
            
            print(f"補完あり：{autocomplete_cost}, 補完なし：{word_count}, 節約ストローク数：{word_count-autocomplete_cost}, トークンの平均文字数：{word_count/token_count}")

        print(word_count)
