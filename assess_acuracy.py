import json
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
            user_input, parsed_input = get_user_input(N, i, line_tokens, parsed_tokens)

            # suggest_keywords{'キーワード':優先順位}の辞書
            # 例：{'be':1, 'being':2}
            suggest_keywords = model.predict(user_input, parsed_input, type_to_symbols, variables, labels)
            prediction_cnt += 1

            # 答えが提案候補に入っている数をカウント
            if answer in suggest_keywords:
                in_suggest_cnt += 1
                rank = suggest_keywords[answer]
            
            if answer in suggest_keywords and suggest_keywords[answer] <= Ranking_Number:
                rank = suggest_keywords[answer]
                right_answer_result[rank-1] += 1
            
    
    return right_answer_result, in_suggest_cnt, prediction_cnt