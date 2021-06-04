import os
import json
import numpy as np
import matplotlib.pyplot as plt
from assess_keystroke import get_user_input, file_name_to_absolute

Ranking_Number = 500


def assess_file_acuracy(file_name, model):
    N = model.N
    right_answer_result = [0 for _ in range(Ranking_Number)]
    prediction_cnt = 0
    in_suggest_cnt = 0

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

        for i in range(1, len(line_tokens)):
            answer = line[i][0]
            user_input, parsed_input = get_user_input(
                N, i, line_tokens, parsed_tokens)

            # suggest_keywords{'キーワード':優先順位}の辞書
            # 例：{'be':1, 'being':2}
            suggest_keywords = model.predict(
                user_input, parsed_input, type_to_symbols, variables, labels)
            prediction_cnt += 1

            # 答えが提案候補に入っている数をカウント
            if answer in suggest_keywords:
                in_suggest_cnt += 1
                rank = suggest_keywords[answer]

            if answer in suggest_keywords and suggest_keywords[answer] <= Ranking_Number:
                rank = suggest_keywords[answer]
                right_answer_result[rank-1] += 1

    return right_answer_result, in_suggest_cnt, prediction_cnt


def assess_mml_acuracy(file_name, model):
    accuracy = np.array([0 for _ in range(Ranking_Number)])
    right_answer_nums = 0
    prediction_times = 0

    mml_lar = open("/mnt/c/mizar/mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(os.path.join('./learning_data', i.replace('\n', '.json')))
    mml_lar.close()
    for file_path in mml[:1100]:
        print(file_path)
        try:
            file_accuracy, file_right_answer_nums, file_prediction_times = assess_file_acuracy(
                file_name, model)
            accuracy += file_accuracy
            right_answer_nums += file_right_answer_nums
            prediction_times += file_prediction_times
        except Exception as e:
            print(e)
            continue
    print(accuracy)
    # draw(model.N, accuracy, prediction_times)
    return None

def draw(N, accuracy, prediction_times):
    title = str(N)+'-gram(trie)'
    plt.title(title)
    plt.xlabel('Ranking')
    plt.ylabel('Correct answer rate (cumulated) [%]')
    plt.ylim(0, 100)
    plt.grid(True)

    # 精度測定後に自動で
    result = accuracy
    total = prediction_times

    left = np.array([i+1 for i in range(len(result))])
    height = np.array(result.cumsum()/total) * 100
    plt.bar(left, height)
    count = 0
    for x, y in zip(left, height):
        # plt.text(x, y, str(int(round(height[count], 0))), ha='center', va='bottom', fontsize=7)
        plt.text(x, y, '', ha='center', va='bottom', fontsize=7)
        count += 1
    plt.savefig(f'graphs/{title}.jpg')
