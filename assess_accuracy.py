import os
import json
import numpy as np
import matplotlib.pyplot as plt
from assess_keystroke import get_user_input, file_name_to_absolute
from collections import OrderedDict, deque
from pprint import pprint 

Ranking_Number = 5

all_token_nums = OrderedDict({})
all_result = OrderedDict({})

def assess_file_accuracy(file_name, model):
    N = model.N
    file_prediction_result = [0 for _ in range(Ranking_Number)]
    file_predictable_num = 0
    file_prediction_times = 0

    file_name = file_name_to_absolute(file_name)
    with open(file_name, 'r') as f:
        json_loaded = json.load(f)
    type_to_symbols = json_loaded['symbols']
    article = json_loaded['contents']
    # ファイル内で宣言された変数，ラベルの保存用リスト
    variables = []
    labels = []
    for line in article:
        line_tokens = []
        parsed_tokens = []

        for token in line:
            # tokenは["x", "__variable_"]のようになっている
            # 予測プログラムには生のトークンを入力する
            line_tokens.append(token[0])
            parsed_tokens.append(token[1])

        for i in range(1, len(line_tokens)-1):
            answer = line[i][0]
            # 文字数ごとに全トークンの数をカウント
            # （精度評価でユーザがn文字入力したときの分母として利用するため）
            all_token_nums.setdefault(len(answer), 0)
            all_token_nums[len(answer)] += 1
            user_input, parsed_input = get_user_input(
                N, i, line_tokens, parsed_tokens)

            # suggest_keywords{'キーワード':優先順位}の辞書
            # 例：{'be':1, 'being':2}
            suggest_keywords = model.predict(
                user_input, parsed_input, type_to_symbols, variables, labels)
            file_prediction_times += 1

            # 答えが提案候補に入っている数をカウント
            if answer in suggest_keywords:
                file_predictable_num += 1
                rank = suggest_keywords[answer]

            # if answer in suggest_keywords and suggest_keywords[answer] <= Ranking_Number:
            #     rank = suggest_keywords[answer]
            #     file_prediction_result[rank-1] += 1

            # ユーザが入力をして，候補が更新された場合の各精度
            for input_idx in range(0, len(answer)):
                # input_idx文字以上の文字数のトークンをカウントする変数
                denominator_cnt = 0
                tmp = deque([])
                for keyword in suggest_keywords:
                    if keyword.startswith(answer[:input_idx]):
                        tmp.append(keyword)
                    if len(keyword) >= input_idx:
                        denominator_cnt = 0
                suggest_keywords = OrderedDict({})
                prediction_result = [0 for _ in range(Ranking_Number)]
                for keyword in tmp:
                    # 入力済みのものは候補に含めない
                    # 例：
                    # ユーザが「suppose」と入力が完了した場合，
                    # 候補内に「supopse」が存在しても正解としてカウントしない
                    if answer[:input_idx] == keyword:
                        continue
                    suggest_keywords[keyword] = len(suggest_keywords) + 1
                
                # n文字入力した場合，n文字のキーワードは考えない
                if answer in suggest_keywords and suggest_keywords[answer] <= Ranking_Number:
                    rank = suggest_keywords[answer]
                    all_result.setdefault(input_idx, [0 for _ in range(Ranking_Number)])
                    all_result[input_idx][rank-1] += 1
                    
                
                # pprint(f'答え:{answer}')
                # pprint(f'{input_idx}回目の入力')
                # pprint(f'ユーザが入力した文字列：{answer[:input_idx]}')
                # pprint(f'{suggest_keywords}')
                # print()

    return all_result, file_predictable_num, all_token_nums

def assess_mml_accuracy(model):
    prediction_result = np.array([0 for _ in range(Ranking_Number)])
    predictable_num = 0
    prediction_times = 0

    mml_lar = open("/mnt/c/mizar/mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(i.replace('\n', '.json'))
    mml_lar.close()
    for file_path in mml[1100:1356]:
        print(file_path)
        try:
            file_prediction_result, file_predictable_num, file_prediction_times = assess_file_acuracy(
                file_path, model)
            prediction_result += file_prediction_result
            predictable_num += file_predictable_num
            prediction_times += file_prediction_times
        except Exception as e:
            print(e)
            continue
    draw(model.N, prediction_result, prediction_times)

def draw(N, prediction_result, prediction_times):
    title = str(N)+'-gram(trie)'
    plt.title(title)
    plt.xlabel('Ranking')
    plt.ylabel('Correct answer rate (cumulated) [%]')
    plt.ylim(0, 100)
    plt.grid(True)

    result = prediction_result
    total = prediction_times

    left = np.array([i+1 for i in range(len(result))])
    height = np.array(result.cumsum()/total) * 100
    plt.bar(left, height)
    count = 0
    for x, y in zip(left, height):
        plt.text(x, y, '', ha='center', va='bottom', fontsize=7)
        count += 1
    plt.savefig(f'graphs/{title}.jpg')
