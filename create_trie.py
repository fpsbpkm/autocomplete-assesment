import os
import json
import pickle
from pprint import pprint
from create_learning_data import check_token_type
from get_voc import parse_voc, load_symbol_dict
import preprocess
import re
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
import copy

file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)
MML_DIR = '/mnt/c/mizar/mml'
MML_VCT = './data/mml.vct'

# トライの最大の深さ
N = 3
Ranking_Number = 500

class TrieNode:
    def __init__(self, name):
        self.name = name
        self.children = dict()
        self.parent = dict()
        self.keywords = dict()

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        # otherは文字列
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_child(self, node):
        self.children[node.name] = node

    def set_parent(self, parent_node):
        self.parent[parent_node.name] = parent_node

class TrieCompleteManager:

    def __init__(self):
        self.root = None
        self.accuracy = np.array([0 for _ in range(Ranking_Number)])
        self.right_answer_nums = 0
        self.prediction_time = 0
        self.setup()
    
    def setup(self):
        try:
            with open('trie_root', 'rb') as f:
                self.root = pickle.load(f)
        except:
            self.root = TrieNode('root')
            self.create()
    
    # mmlをスキャンし，引数のメソッドを順に実行する
    def apply_all_files(self, start, end, method_name):
        
        mml_lar = open("/mnt/c/mizar/mml.lar", "r")
        mml = []
        for i in mml_lar.readlines():
            mml.append(os.path.join('./learning_data', i.replace('\n', '.json')))
        mml_lar.close()
        for file_path in mml[start:end]:
            print(file_path)
            # ファイルが存在しない可能性がある，存在しない場合はスキップ
            try:
                assess_file_manager = OneFileAssessManager(file_path)
                if method_name == 'acuracy':
                    accuracy, right_answer_nums, prediction_times = assess_file_manager.assess_file_acuracy(self)
                    self.accuracy += np.array(accuracy)
                    self.right_answer_nums += right_answer_nums
                    self.prediction_time +=  prediction_times
                elif method_name == 'keystroke':
                    assess_file_manager.assess_file_keystroke(self)
                elif method_name == 'create':
                    assess_file_manager.create_one_file_trie(self)
                    
                # 拡張する場合は以下に処理を記述
                else:
                    pass
            except Exception as e:
                print(e)
                continue
    
    def create(self):
        self.apply_all_files(0, 1100, 'create')
        with open('./trie_root', 'wb') as f:
            pickle.dump(self.root, f)

    def create_type_to_symbols(self):
        lexer = preprocess.Lexer()
        lexer.load_symbol_dict(MML_VCT)
        lexer.build_len2symbol()

        with open(self.file_name, 'r') as f:
            try:
                lines = f.readlines()
                assert len(lines) > 0
            except:
                print("Error!")
        
        env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
        env_lines = lexer.remove_comment(env_lines)
        env_tokenized_lines, position_map = lexer.lex(env_lines)
        
        env_tokens = []
        for line in env_tokenized_lines:
            if line == '':
                continue
            env_tokens.append(line.split())

        voc_flag = False
        vocs = []
        for line in env_tokens:
            for token in line:
                if token == 'vocabularies':
                    voc_flag = True
                if voc_flag and token == ';':
                    voc_flag = False
                if voc_flag and not token == ',' and not token == 'vocabularies':
                    vocs.append(token)
        symbol_dict = load_symbol_dict(MML_VCT, vocs)

        # symbol_dictからtype_to_symbolsを生成
        type_to_symbols = {}
        for key in symbol_dict:
            symbol_type = symbol_dict[key]['type']
            
            if not symbol_type in type_to_symbols:
                type_to_symbols[symbol_type] = [key]
            else:
                type_to_symbols[symbol_type].append(key)
        self.type_to_symbols = type_to_symbols

    # 「__M_」などを具体的に，優先度をつけて提案できるように
    def predict(self, user_input, parsed_input, type_to_symbols, variables, labels):
        node = self.root
        parsed_input_reversed = parsed_input[::-1]
        user_input_reversed = user_input[::-1]

        # type_to_symbols = self.type_to_symbols
        # variables = self.variables
        # labels = self.labels

        # ユーザ入力から，トライ木を検索
        for i in range(len(parsed_input_reversed)):
            # 型トークンを取得
            token = parsed_input_reversed[i]
            # ユーザが利用していて，登録されていない変数を保存
            if token == '__variable_' and user_input_reversed[i] not in set(variables):
                variables.append(user_input_reversed[i])
            # ユーザが利用していて，登録されていないラベルを保存
            elif token == '__label_' and user_input_reversed[i] not in set(labels):
                labels.append(user_input_reversed[i])
            # トライ木の検索
            if token in node.children:
                node = node.children[token]
            else:
                return {}

        # sorted_keywordsは[[トークン, 出現回数]]の形式
        # 例：[['__variable_', 100], ['be', 60] ... ]
        sorted_keywords = sorted(node.keywords.items(), key=lambda x:x[1], reverse=True)

        # {キーワード:優先度}の形式で保存する
        # 例：{"be":1, "being":2}
        suggest_keywords = {}
        rank = len(suggest_keywords) + 1
        # 「__variable_」「__M_」などを展開する処理
        for keyword in sorted_keywords:
            matched = re.match(r'__(\w\d*)_', keyword[0])
            if matched:
                symbol_type = matched.groups()[0]
                if symbol_type is None:
                    return {}

                # importしていない種類が提案された場合は考えない
                if not symbol_type in type_to_symbols:
                    continue

                for word in type_to_symbols[symbol_type[0]]:
                    suggest_keywords[word] = rank
                    rank = len(suggest_keywords)
                    
            # ユーザが利用した変数を提案
            elif keyword[0] == '__variable_':
                for v in list(variables)[::-1]:
                    suggest_keywords[v] = rank
                    rank = len(suggest_keywords)
            
            elif keyword[0] == '__label_':
                for l in list(labels)[::-1]:
                    suggest_keywords[l] = rank
                    rank = len(suggest_keywords)
            elif keyword[0] == '__number_':
                pass
            else:
                suggest_keywords[keyword[0]] = rank
                rank = len(suggest_keywords)

            # 前処理段階で数字が「変数」「ラベル」両方に判断され重複し，辻褄が合わなくなっている
            # if rank != len(suggest_keywords):
            #     print('おかしい！！！')
            #     print(f'variables:{variables}')
            #     print(f'labels:{labels}')

        # print(f'user_input:{user_input}')
        # print()
        # print(f'suggest_keywordsの長さ:{len(suggest_keywords)}')
        # print(f'候補数：{cnt-1}')
        return suggest_keywords

    def assess_mml_acuracy(self):
        self.apply_all_files(1100, 1355, 'acuracy')
        # 測定後の精度を作成
        self.draw()

    # assess_mml_acuracyからの呼び出しのみを想定
    def draw(self):
        title = str(N)+'-gram(trie)'
        plt.title(title)
        plt.xlabel('Ranking')
        plt.ylabel('Correct answer rate (cumulated) [%]')
        plt.ylim(0, 100)
        plt.grid(True)

        # 精度測定後に自動で
        result = self.accuracy
        total = self.prediction_time

        left = np.array([i+1 for i in range(len(result))])
        height = np.array(result.cumsum()/total) * 100
        plt.bar(left, height)
        count = 0
        for x, y in zip(left, height):
            # plt.text(x, y, str(int(round(height[count], 0))), ha='center', va='bottom', fontsize=7)
            plt.text(x, y, '', ha='center', va='bottom', fontsize=7)
            count += 1
        plt.savefig(f'graphs/{title}.jpg')
        


class OneFileAssessManager:

    def __init__(self, file_name):
        self.file_name = file_name
        self.variables = deque([])
        self.labels = deque([])
        self.article = None
        self.type_to_symbols = None

        with open(self.file_name, 'r') as f:
            json_loaded = json.load(f)
        self.type_to_symbols = json_loaded['symbols']
        self.article = json_loaded['contents']
    
    def get_user_input(self, i, line_tokens, parsed_tokens):
        if i >= N:
            user_input = line_tokens[i-N+1:i]
            parsed_input = parsed_tokens[i-N+1:i]
        else:
            user_input = line_tokens[:i]
            parsed_input = parsed_tokens[:i]
        
        return user_input, parsed_input
    
    def assess_file_acuracy(self, trie_manager):
        right_answer_nums = [0 for _ in range(Ranking_Number)]
        prediction_cnt = 0
        in_suggest_cnt = 0

        # 不正解のキーワード保存用
        wrong_answers = {}

        for line in self.article:
            line_tokens= []
            parsed_tokens = []
            
            for token in line:
                # tokenは["x", "__variable_"]のようになっている
                # 予測プログラムには生のトークンを入力する
                line_tokens.append(token[0])
                parsed_tokens.append(token[1])

            for i in range(1, len(line_tokens)):
                answer = line[i][0]
                user_input, parsed_input = self.get_user_input(i, line_tokens, parsed_tokens)
                # suggest_keywords{'キーワード':優先順位}の辞書
                # 例：{'be':1, 'being':2}
                suggest_keywords = trie_manager.predict(user_input, parsed_input, self.type_to_symbols, self.variables, self.labels)
                prediction_cnt += 1
                
                # 答えが提案候補に入っている数をカウント
                if answer in suggest_keywords:
                    in_suggest_cnt += 1
                    rank = suggest_keywords[answer]
                # 不正解キーワードの表示（デバッグ用）
                # else:
                #     if answer in wrong_answers:
                #         wrong_answers[answer] += 1
                #     else:
                #         wrong_answers[answer] = 1

                # Ranking_Number候補以内であればインクリメント
                # FIXME:10000候補も存在しないはずだが，グラフではなぜか正答率が上昇している
                if answer in suggest_keywords and suggest_keywords[answer] <= Ranking_Number:
                    # FIXME:デバッグ用
                    if suggest_keywords[answer] > 500:
                        print(suggest_keywords[answer])
                        print(suggest_keywords)
                    rank = suggest_keywords[answer]
                    right_answer_nums[rank-1] += 1
                # print(f'input:{user_input}')
                # print(f'suggest:{suggest_keywords}')
        # print(trie_manager.accuracy, trie_manager.prediction_time)
        return right_answer_nums, in_suggest_cnt, prediction_cnt

    def assess_file_keystroke(self, trie_manager):
        original_cost = 0
        cost = 0
        saving_cost = 0
        # トークン平均文字数に利用するカウンタ
        token_cnt = 0

        # lineは[[let, let], [x, __variable_], [be, be], [object, __M_]]のような形式
        for line in self.article:
            line_tokens= []
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
            token_cnt += 1
            # print(line, first_token_cost)
            for idx in range(1, length):
                token_cnt += 1
                answer = line[idx][0]
                remaining_cost = len(answer)
                original_cost += remaining_cost

                user_input, parsed_input = self.get_user_input(idx, line_tokens, parsed_tokens)
                items = trie_manager.predict(
                    user_input, 
                    parsed_input, 
                    self.type_to_symbols, 
                    self.variables, self.labels)

                if remaining_cost <= 1:
                    cost += remaining_cost
                elif answer in items:
                    input_idx = 0
                    while remaining_cost >= 2:
                        select_cost = items[answer]
                        if select_cost < remaining_cost:
                            print(f'正解:{answer}, 文字入力数:{input_idx}, 予測順位:{items[answer]}')
                            print(f'本来のコスト:{len(answer)}')
                            print(f'節約コスト：{remaining_cost - select_cost}')
                            saving_cost += (remaining_cost - select_cost)
                            print(f'節約数の合計：{saving_cost}')
                            print()
                            cost += select_cost
                            break
                        # 1文字入力して，提案キーワードを更新する処理
                        else:
                            input_idx += 1
                            cost += 1
                            # 1文字入力したため，トークンを入力するコストが「1」減少する
                            remaining_cost -= 1
                            # 残りのコストが2未満の場合は，節約にならないため，残りのコストを加えて終了
                            if remaining_cost < 2:
                                cost += remaining_cost
                                break

                            # 提案キーワード群の更新
                            tmp = []
                            for keyword in items:
                                if keyword.startswith(answer[:input_idx]):
                                    tmp.append(keyword)
                            items = {}
                            # 提案キーワードの順位を保持する変数
                            cnt = 1
                            for item in tmp:
                                items[item] = cnt
                                cnt += 1
                else:
                    cost += remaining_cost
        print(f'トークン平均文字数：{original_cost/token_cnt}')
        return original_cost, cost, saving_cost

    def create_one_file_trie(self, trie_manager):
        for line in self.article:
            length = len(line)
            for idx in range(1, length):
                # 予測対象のトークンを取得
                token = line[idx][1]
                parent_node = None
                node = None
                diff = 0
                # 直前トークン数がN未満の場合
                if idx-N+1 < 0:
                    diff = abs(idx-N+1)
                # reversed(range(0, 3)) -> 2, 1, 0となる
                for j in reversed(range(idx-N+1+diff, idx)):
                    if j == idx-1:
                        parent_node = trie_manager.root

                    node_name = line[j][1]
                    # 既に同名のノードが存在すれば取得
                    if node_name in parent_node.children:
                        node = parent_node.children[node_name]
                    # 同名のノードが存在しなければ生成し，子ノードとして追加
                    else:
                        node = TrieNode(node_name)
                        parent_node.add_child(node)
                    # 各ノードに予測対象のキーワードを保存
                    # node.keywordsは{予測対象のワード:登場回数}の形式
                    if token in node.keywords:
                        node.keywords[token] += 1
                    else:
                        node.keywords[token] = 1
                        
                    node.set_parent(parent_node)
                    parent_node = node
    
if __name__ == '__main__':
    trie_manager = TrieCompleteManager()
    trie_manager.setup()

    # trie_manager.assess_mml_acuracy()
    # print(trie_manager.accuracy, trie_manager.right_answer_nums, trie_manager.prediction_time)

    file_manager = OneFileAssessManager('./learning_data/diophan2.json')
    original_cost, cost, saving_cost = file_manager.assess_file_keystroke(trie_manager)
    print(original_cost, cost, saving_cost, saving_cost/original_cost*100)
    # ranking, in_suggest_cnt, total = file_manager.assess_file_acuracy(trie_manager)
    # print(ranking, in_suggest_cnt, total)

    # print(f'sum:{sum(ranking)}')
    # print(complete_manager.predict(["x", "be"]))
