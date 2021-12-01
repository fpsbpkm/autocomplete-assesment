import json
from collections import OrderedDict, deque

# Tab,矢印キーなどのコストを設定する変数
SPECIAL_KEY_COST = 1


def get_user_input(N, i, line_tokens, parsed_tokens):
    if i >= N:
        user_input_list = line_tokens[i - N + 1: i]
        parsed_input_list = parsed_tokens[i - N + 1: i]
    else:
        user_input_list = line_tokens[:i]
        parsed_input_list = parsed_tokens[:i]

    return user_input_list, parsed_input_list


def file_name_to_absolute(file_name):
    return "./learning_data/" + file_name


def assess_file_keystroke(file_name, model):
    # NOTE:modelにNを持たせておく
    N = model.N
    file_name = file_name_to_absolute(file_name)
    with open(file_name, "r") as f:
        json_loaded = json.load(f)
    type_to_symbols = json_loaded["symbols"]
    article = json_loaded["contents"]
    variables = []
    labels = []
    original_cost = 0
    cost = 0
    saving_cost = 0
    token_counter = 0
    # lineは[[let, let], [x, __variable_], [be, be], [object, __M_]]のような形式
    for line in article:
        line_tokens = []
        parsed_tokens = []
        # print(f'original_cost:{original_cost}, cost:{cost}')
        for token in line:
            # tokenは["x", "__variable_"]のようになっている
            line_tokens.append(token[0])
            parsed_tokens.append(token[1])
        length = len(line)
        # 文頭のトークンは予測できないため，コストとして追加
        first_token_cost = len(line_tokens[0])
        original_cost += first_token_cost
        cost += first_token_cost
        token_counter += 1
        # print(line, first_token_cost)
        for idx in range(1, length):
            token_counter += 1
            answer = line[idx][0]
            remaining_cost = len(answer)
            original_cost += remaining_cost
            user_input, parsed_input = get_user_input(
                N, idx, line_tokens, parsed_tokens
            )
            # suggested_keywordsは{キーワード:提案順位}の形式
            # 例：{"be":1, "being":2}
            suggested_keywords = model.predict(
                user_input, parsed_input, type_to_symbols, variables, labels
            )
            # 残りの入力に必要なコストが特殊キーのコスト以下ならコスト削減の可能性はない
            if remaining_cost <= SPECIAL_KEY_COST:
                cost += remaining_cost
            elif answer in suggested_keywords:
                input_idx = 0
                # 残りの入力コストが特殊キーのコストより大きい場合，コスト削減の可能性がある
                while remaining_cost > SPECIAL_KEY_COST:
                    select_cost = SPECIAL_KEY_COST * suggested_keywords[answer]
                    if select_cost < remaining_cost:
                        # print(f'正解:{answer}, 文字入力数:{input_idx},
                        #       予測順位:{suggested_keywords[answer]}')
                        # print(f'本来のコスト:{len(answer)}')
                        # print(f'節約コスト：{remaining_cost - select_cost}')
                        saving_cost += remaining_cost - select_cost
                        # print(f'節約数の合計：{saving_cost}')
                        # print()
                        cost += select_cost
                        break
                    # 1文字入力して，提案キーワードを更新する処理
                    else:
                        input_idx += 1
                        cost += 1
                        # 1文字入力したため，トークンを入力するコストが「1」減少する
                        remaining_cost -= 1
                        # 残りのコストが2未満の場合は，節約にならないため，残りのコストを加えて終了
                        # FIXME:特殊キーのコストを0.5とする場合は，残りのコストが2でも節約できる可能性がある
                        if remaining_cost < 1:
                            cost += remaining_cost
                            break
                        # 提案キーワード群の更新
                        tmp = deque()
                        for keyword in suggested_keywords:
                            if keyword.startswith(answer[:input_idx]):
                                tmp.append(keyword)
                        suggested_keywords = OrderedDict({})
                        # 提案キーワードの順位を保持する変数
                        cnt = 1
                        for keyword in tmp:
                            suggested_keywords[keyword] = \
                                len(suggested_keywords) + 1
                            cnt += 1
            else:
                cost += remaining_cost
    print(f"トークン平均文字数：{original_cost/token_counter}")
    return original_cost, saving_cost, token_counter


def assess_mml_keystroke(model):
    original_cost, reduced_cost, token_counter = 0, 0, 0

    mml_lar = open("./mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(i.replace("\n", ".json"))
    mml_lar.close()
    for file_path in mml[1100:1356]:
        print(file_path)
        if original_cost != 0:
            # print(original_cost, reduced_cost,
            #       reduced_cost/original_cost, token_counter)
            pass
        try:
            (
                file_original_cost,
                file_reduced_cost,
                file_token_counter,
            ) = assess_file_keystroke(file_path, model)
            original_cost += file_original_cost
            reduced_cost += file_reduced_cost
            token_counter += file_token_counter

        except Exception as e:
            print(e)
            continue
        print(original_cost, reduced_cost,
              reduced_cost / original_cost, token_counter)
    return original_cost, reduced_cost, token_counter
