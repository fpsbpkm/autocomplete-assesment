import json
import numpy as np
import matplotlib.pyplot as plt
import os
from assess_keystroke import get_user_input, file_name_to_absolute
from collections import OrderedDict, deque
from pprint import pprint

# 何候補目までの精度を計測するか指定
Ranking_Number = 10
# 何文字目までの入力文字数の精度を計測するか指定
Input_Length = 6
PROJECT_DIR = os.environ['PROJECT_DIR']


def assess_file_accuracy(file_name, model):
    N = model.N
    file_predictable_num = 0
    file_prediction_times = 0

    file_all_result = OrderedDict()
    file_all_token_nums = OrderedDict({})

    file_name = file_name_to_absolute(file_name)
    with open(file_name, "r") as f:
        json_loaded = json.load(f)
    type_to_symbols = json_loaded["symbols"]
    article = json_loaded["contents"]
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

        for i in range(1, len(line_tokens) - 1):
            answer = line[i][0]
            # 文字数ごとに全トークンの数をカウント
            # （精度評価でユーザがn文字入力したときの分母として利用するため）
            file_all_token_nums.setdefault(len(answer), 0)
            file_all_token_nums[len(answer)] += 1
            user_input, parsed_input = \
                get_user_input(N, i, line_tokens, parsed_tokens)

            # suggest_keywords{'キーワード':優先順位}の辞書
            # 例：{'be':1, 'being':2}
            suggest_keywords = model.predict(
                user_input, parsed_input, type_to_symbols, variables, labels
            )
            file_prediction_times += 1

            # 答えが提案候補に入っている数をカウント
            if answer in suggest_keywords:
                file_predictable_num += 1
                rank = suggest_keywords[answer]

            # ユーザが入力をして，候補が更新された場合の各精度
            for input_idx in range(0, len(answer)):
                tmp = deque([])
                for keyword in suggest_keywords:
                    if keyword.startswith(answer[:input_idx]):
                        tmp.append(keyword)
                suggest_keywords = OrderedDict({})
                for keyword in tmp:
                    # 入力済みのものは候補に含めない
                    # 例：
                    # ユーザが「suppose」と入力が完了した場合，
                    # 候補内に「supopse」が存在しても正解としてカウントしない
                    if answer[:input_idx] == keyword:
                        continue
                    suggest_keywords[keyword] = len(suggest_keywords) + 1

                # n文字入力した場合，n文字のキーワードは考えない
                if (
                    answer in suggest_keywords
                    and suggest_keywords[answer] <= Ranking_Number
                ):

                    # print(f'カーソル直前までの入力：{user_input}')
                    # print(f'{input_idx}文字入力')
                    # print(f'answer:{answer}, rank:{suggest_keywords[answer]}')
                    # print(f'suggest:{suggest_keywords}')
                    # print()
                    rank = suggest_keywords[answer]
                    file_all_result.setdefault(
                        input_idx, [0 for _ in range(Ranking_Number)]
                    )
                    file_all_result[input_idx][rank - 1] += 1

                # pprint(f'答え:{answer}')
                # pprint(f'{input_idx}回目の入力')
                # pprint(f'ユーザが入力した文字列：{answer[:input_idx]}')
                # pprint(f'{suggest_keywords}')
                # print()

    return (
        file_all_result,
        file_predictable_num,
        file_all_token_nums,
        file_prediction_times,
    )


def assess_mml_accuracy(model):
    # all_token_numsにトークンの文字数ごとの出現数
    # （i文字入力した場合，i文字以下のトークンは対象外のため保存する必要がある）
    all_token_nums = OrderedDict({})

    # all_resultにi文字入力した場合の正解率をそれぞれ保存しておく
    # 例：OrderedDict([(0, [0.2, 0.1, 0.05 ...]), (1, [0.5, 0.2, 0.1 ...])])
    all_result = OrderedDict({})

    # prediction_result = np.array([0 for _ in range(Ranking_Number)])
    # prediction_result = OrderedDict({})
    predictable_num = 0
    prediction_times = 0

    mml_lar = open(f"{PROJECT_DIR}/about_mml/mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(i.replace("\n", ".json"))
    mml_lar.close()

    excepted_files = deque()
    for file_path in mml[1100:1356]:
        print(file_path)
        try:
            (
                file_all_result,
                file_predictable_num,
                file_all_token_nums,
                file_prediction_times,
            ) = assess_file_accuracy(file_path, model)
        except Exception as e:
            print(e)
            excepted_files.append(file_path)
            continue

        predictable_num += file_predictable_num
        prediction_times += file_prediction_times
        # ユーザの2文字の入力まで保存
        # file_all_resultから，all_resultに結果を加える
        for i in range(Input_Length):
            all_result.setdefault(i,
                                  np.array([0 for _ in range(Ranking_Number)]))
            all_token_nums.setdefault(i + 1, 0)
            all_result[i] += np.array(file_all_result[i])
            all_token_nums[i + 1] += np.array(file_all_token_nums[i + 1])

    print()
    print(model.N)
    pprint(all_result)
    print(prediction_times)
    pprint(excepted_files)

    for i in range(Input_Length):
        prediction_result = all_result[i]
        draw(model.N, prediction_result, prediction_times, i)
        # 入力済みのi+1文字以下は予測対象外なので除外
        prediction_times -= all_token_nums[i + 1]


def draw(N, prediction_result, prediction_times, i):
    title = f"{N}-gram(raw)-typing {i} characters"
    plt.title(title)
    plt.xlabel("Suggested number")
    plt.ylabel("Correct answer rate (cumulated) [%]")
    plt.ylim(0, 100)
    plt.grid(True)

    result = prediction_result
    total = prediction_times

    left = np.array([i + 1 for i in range(len(result))])
    height = np.array(result.cumsum() / total) * 100
    plt.bar(left, height, color="blue")
    count = 0
    for x, y in zip(left, height):
        plt.text(x, y, "", ha="center", va="bottom", fontsize=7)
        count += 1
    plt.savefig(f"graphs/{title}.jpg")
    plt.clf()
