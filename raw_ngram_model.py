import json
import time
from assess_keystroke import assess_file_keystroke
from assess_accuracy import assess_file_accuracy
import numpy as np
from pprint import pprint 
from collections import OrderedDict

# N-gramの学習（カウント）ファイルを取得
json_open2 = open("jsons/output2.json", 'r')
json_load2 = json.load(json_open2)

json_open3 = open("jsons/output3.json", "r")
json_load3 = json.load(json_open3)

keywords2 = json_load2["completions"]
keywords3 = json_load3["completions"]

class RawNgramModel:
    def __init__(self):
        self.N = 2
    # user_inputは適切に切り取られたユーザの入力
    # 例：["x", "be"]
    def predict(self, user_input_list, parsed_input_list=None, type_to_symbols=None, variables=None, labels=None):
        # {キーワード:優先度}の形式で保存する
        # 例：{"be":1, "being":2}
        suggest_keywords = {}

        # 入力補完のロジック
        if len(user_input_list) == 1:
            keywords = keywords2
            user_input_string = " ".join(user_input_list)
        else:
            keywords = keywords3
            user_input_string = " ".join(user_input_list)

        rank = 0
        for kw in keywords:
            if kw.startswith(user_input_string) == False:
                continue
            rank += 1
            suggest = kw[len(user_input_string)+1:len(kw)]
            suggest_keywords[suggest] = rank

        return suggest_keywords


if __name__ == '__main__':
    start = time.time()
    raw_ngram = RawNgramModel()
    # original_cost, cost, saving_cost = assess_file_keystroke('diophan2.json', raw_ngram)
    # print(original_cost, cost, saving_cost)
    all_result, in_suggest_cnt, all_token_nums = assess_file_accuracy(
        'scmfsa_2.json', raw_ngram)

    all_token_cnt = sum(all_token_nums.values())
    # pprint(all_result)
    np.set_printoptions(precision=1)
    # 各文字入力の段階での正答率を表示したい
    for i in range(len(all_result)):
        tmp = np.array(all_result[i])
        pprint(f'{i}文字入力の場合：{(tmp/all_token_cnt*100)}, {sum(tmp/all_token_cnt*100):.1f}%')
        # 特定の文字数のトークンが必ず存在している保証はないため，その場合は0で初期化
        all_token_nums.setdefault(i+1, 0)
        all_token_cnt -= all_token_nums[i+1]
    elapsed_time = time.time() - start
    print (f"elapsed_time:{elapsed_time}")
