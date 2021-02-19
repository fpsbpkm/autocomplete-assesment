import re
import preprocess
import pprint
import os
from graph import draw
import time
import glob
import codecs
from completion import provide_items

# 評価するn-gramの数を指定
N = 3

# def display_result(result):
#     total = sum(result)
#     draw(result)
#     for i,r in enumerate(result):
#         print(r)
#         if i < 30:
#             print(f"{i+1}位：{r/total*100}%")
#         elif i == 30:
#             print(f"30位以下：{r/total*100}%")
#         else:
#             print(f"不正解：{r/total*100}%")

# 1文ごとに正解率を評価して更新する関数
def assesment(token_list):
    items = []
    ranking = [0 for _ in range(31)]
    for i in range(1, len(token_list)):
        # 予測候補と正解を取得
        items, answer = provide_items(token_list, i, N)
        # 30位以内の正解率
        if answer in set(items[:30]):
            for j in range(30):
                # インデックスの範囲内か確認（不要かも？）
                if j+1 > len(items):
                    break
                if answer == items[j]:
                    # print(f"正解：{answer}, {items[j]}")
                    ranking[j] += 1
                    break
        else:
            # print(f"答え：{answer}, 候補：{items}")
            ranking[30] += 1

    return ranking

# mml.vctを配置したパスを指定（配置場所によって変える必要があるため注意）
DATA_DIR = './data'
MML_VCT = os.path.join(DATA_DIR, 'mml.vct')
MML_DIR = '/mnt/c/mizar/mml'

lexer = preprocess.Lexer()
lexer.load_symbol_dict(MML_VCT)
lexer.build_len2symbol()

start = time.time()

mml_lar = codecs.open("/mnt/c/mizar/mml.lar", "r")
mml = []
# mml.larのファイル名を使って，絶対パスへ変換
for i in mml_lar.readlines()[1099:]:
    mml.append(os.path.join(MML_DIR, i.replace('\n', '.miz')))

# 30位以内それぞれのランキング
result = [0 for _ in range(31)]
count = 0
errors = 0
for file_name in mml:
    with open(file_name, 'r') as f:
        lines = f.readlines()

    if count >= 5:
        break
    count += 1

    env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
    text_proper_lines = lexer.remove_comment(text_proper_lines)
    try:
        tokenized_lines, position_map = lexer.lex(text_proper_lines)
    except:
        errors += 1
        continue

    for line in tokenized_lines:
        line = re.sub('__\w+_', '', line)
        token_list = line.split(" ")
        temp = assesment(token_list)
        result = [result[i]+temp[i] for i in range(len(result))]

    print(f"{file_name} has done. count:{count}")
    print(result)

elapsed_time = time.time() - start

print(f"処理時間：{elapsed_time}")
print(f"エラー数：{errors}")
print(f"合計ファイル数：{count-errors}")
# display_result(result)
draw(result, N)

mml_lar.close()
