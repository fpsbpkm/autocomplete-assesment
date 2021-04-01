import json
from learning import is_variable

# N-gramの学習（カウント）ファイルを取得
json_open2 = open("jsons/output2.json", 'r')
json_load2 = json.load(json_open2)

json_open3 = open("jsons/output3.json", "r")
json_load3 = json.load(json_open3)

json_open4 = open("jsons/output4_10.json", "r")
json_load4 = json.load(json_open4)

keywords2 = json_load2["completions"]
keywords3 = json_load3["completions"]
keywords4 = json_load4["completions"]

# Trueのときに，変数を「___」に置き換える
is_replaced_variable = False

# 予測候補のリスト，正解を返す
def provide_items(token_list, i, N):
    # 提案するキーワードのリスト
    items = []
    N = N - 1
    # 推測には最大で直前3つのトークンを利用するため
    if i > N:
        input_text = token_list[i-N:i]
        answer = token_list[i]
    else:
        input_text = token_list[:i]
        answer = token_list[i]

    if is_variable(token_list, i) and is_replaced_variable:
            answer = '___'
    
    # ユーザが入力した変数を「___」と置き換える
    replaced_input_text = []
    for j in range(len(input_text)):
        if is_variable(input_text, j) and is_replaced_variable:
            replaced_input_text.append('___')
        else:
            replaced_input_text.append(input_text[j])


    # 入力補完のロジック
    if len(input_text) == 1:
        keywords = keywords2
        recent_input = " ".join(replaced_input_text)
    elif len(input_text) == 2:
        keywords = keywords3
        recent_input = " ".join(replaced_input_text)
    else:
        keywords = keywords4
        recent_input = " ".join(replaced_input_text)

    # print(f"input_text:{input_text}, replaced:{replaced_input_text}")

    count_items = 0
    for kw in keywords:
        if kw.startswith(recent_input) == False:
            continue
        count_items += 1
        item = kw[len(recent_input)+1:len(kw)]
        items.append(item)

        # print(f"answer:{answer}, recent_input:{recent_input}, kw:{kw}, items:{items}")

        if count_items >= 30:
            return items, answer

    return items, answer
