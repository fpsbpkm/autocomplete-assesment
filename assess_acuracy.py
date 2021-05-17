import json

Ranking_Number = 500

def get_user_input(N, i, line_tokens, parsed_tokens):
        if i >= N:
            user_input = line_tokens[i-N+1:i]
            parsed_input = parsed_tokens[i-N+1:i]
        else:
            user_input = line_tokens[:i]
            parsed_input = parsed_tokens[:i]
        
        return user_input, parsed_input

def assess_file_acuracy(file_name, model):
    right_answer_nums = [0 for _ in range(Ranking_Number)]
    prediction_cnt = 0
    in_suggest_cnt = 0

    N = model.N
    file_name = './learning_data/' + file_name

    with open(file_name, 'r') as f:
        json_loaded = json.load(f)
    type_to_symbols = json_loaded['symbols']
    article = json_loaded['contents']

    for line in article:
        line_tokens = []
        parsed_tokens = []

        for token in line:
            # tokenは["x", "__variable_"]の形式になっている
            line_tokens.append(token[0])
            parsed_tokens.append(token[1])
        
        for i in range(1, len(line_tokens)):
            answer = line[i][0]
            user_input, parsed_input = get_user_input(N, i, line_tokens, parsed_tokens)
            # suggest_keywords{'キーワード':優先順位}の辞書
            # 例：{'be':1, 'being':2}
            suggest_keywords = model.predict(user_input, parsed_input, type_to_symbols, model.variables, model.labels)
        
        