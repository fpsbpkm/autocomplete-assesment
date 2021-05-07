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
Ranking_Number = 20000

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
        n = len(user_input)
        tree = self.root
        
        # カーソル直前のトークン数
        if n > N:
            n = N

        parsed_input_reversed = parsed_input[::-1]

        # ユーザ入力から，トライ木を検索
        for i in range(len(parsed_input_reversed)):
            # FIXME:シンボルに接頭辞がついていないため，意図通りに動作しない
            # object -> 変数と判定されてしまう
            # 「let x be object;」
            # token = check_token_type(token_list, i)
            token = parsed_input_reversed[i]

            # ユーザが利用している変数を保存
            if token == '__variable_':
                variables.append(user_input[i])
                pass
            # ユーザが利用しているラベルを保存
            elif token == '__label_':
                labels.append(user_input[i])
                pass
            # トライ木の検索
            if token in tree.children:
                tree = tree.children[token]
            else:
                return {}

        # sorted_keywordsは[[トークン, 出現回数]]の形式
        # 例：[['__variable', 100], ['be', 60] ... ]
        sorted_keywords = sorted(tree.keywords.items(), key=lambda x:x[1], reverse=True)

        # {キーワード:優先度}の形式で保存する
        # 例：{"be":1, "being":2}
        suggest_keywords = {}
        cnt = 1

        # 「__variable_」「__M_」などを展開する処理
        for keyword in sorted_keywords:
            matched = re.match(r'__(\w)_', keyword[0])
            if matched:
                symbol_type = matched.groups()[0]
                if symbol_type is None:
                    return {}

                # importしていない種類が提案された場合は考えない
                if not symbol_type in type_to_symbols:
                    continue

                for word in type_to_symbols[symbol_type[0]]:
                    suggest_keywords[word] = cnt
                    cnt += 1
            # ユーザが利用した変数を提案
            elif keyword[0] == '__variable_':
                for v in list(variables)[::-1]:
                    suggest_keywords[v] = cnt
                    cnt += 1
            
            elif keyword[0] == '__label_':
                for l in list(labels)[::-1]:
                    suggest_keywords[l] = cnt
                    cnt += 1
            else:
                suggest_keywords[keyword[0]] = cnt
                cnt += 1
        return suggest_keywords

    def assess_mml_acuracy(self):
        self.apply_all_files(1105, 1110, 'acuracy')
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
        plt.bar(left[:-2], height[:-2])
        count = 0
        for x, y in zip(left[:-2], height[:-2]):
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
            user_input = parsed_tokens[:i]
            parsed_input = parsed_tokens[:i]
        
        return user_input, parsed_input
    
    def assess_file_acuracy(self, trie_manager):
        right_answer_nums = [0 for _ in range(Ranking_Number)]
        prediction_cnt = 0
        in_suggest_cnt = 0

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

                # Ranking_Number候補以内であればインクリメント
                if answer in suggest_keywords and suggest_keywords[answer] <= Ranking_Number:
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
        # lineは[[let, let], [x, __variable_], [be, be], [object, __M_]]のような形式

        for line in self.article:
            line_tokens= []
            parsed_tokens = []
            print(f'original_cost:{original_cost}, cost:{cost}')
            
            for token in line:
                # tokenは["x", "__variable_"]のようになっている
                line_tokens.append(token[0])
                parsed_tokens.append(token[1])

            for i in range(1, len(line_tokens)):
                answer = line[i][0]

            length = len(line)
            for idx in range(1, length):
                answer = line[idx][0]
                token_cost = len(answer)
                original_cost += token_cost

                user_input, parsed_input = self.get_user_input(i, line_tokens, parsed_tokens)
                items = trie_manager.predict(user_input, parsed_input, self.type_to_symbols, self.variables, self.labels)

                if token_cost <= 1:
                    cost += token_cost
                elif answer in items:
                    input_idx = 0
                    while token_cost >= 2:
                        select_cost = items[answer]
                        if select_cost < token_cost:
                            print(f'answer:{answer}, items[answer]:{items[answer]}, 文字入力数:{input_idx}')
                            print(f'select_cost:{select_cost}, token_cost:{token_cost}')
                            print(f'節約コスト：{token_cost - select_cost}')
                            saving_cost += (token_cost - select_cost)
                            print()
                            cost += select_cost
                            break
                        # 1文字入力
                        else:
                            input_idx += 1
                            cost += 1
                            token_cost -= 1
                            # 残りのコストが2未満の場合は，節約にならないため，残りのコストを加えて終了
                            if token_cost < 2:
                                cost += token_cost
                                break

                            # 提案キーワード群の更新
                            tmp = []
                            for keyword in items:
                                if keyword.startswith(answer[:input_idx]):
                                    tmp.append(keyword)
                            items = {}
                            cnt = 1
                            for item in tmp:
                                items[item] = cnt
                                cnt += 1
                else:
                    cost += token_cost
    
        return original_cost, cost, saving_cost

    def create_one_file_trie(self, trie_manager):
        for line in self.article:
            length = len(line)
            for idx in range(1, length):
                # 予測対象のトークン
                token = line[idx][1]
                parent_node = None
                node = None
                diff = 0
                # 直前トークン数がN未満の場合
                if idx-N+1 < 0:
                    diff = abs(idx-N+1)
                # HACK:このあたりが怪しい
                # reversed(range(1, 4)) -> 3, 2, 1となる
                for j in reversed(range(idx-N+1+diff, idx)):
                    if j == idx-1:
                        parent_node = trie_manager.root
                    node_name = line[j][1]
                    # 既に同名のノードが存在すれば取得
                    if node_name in parent_node.children:
                        node = parent_node.children[node_name]
                    # 同名のノードが存在しなければ生成
                    else:
                        node = TrieNode(node_name)
                    # 各ノードに予測対象のキーワードを保存
                    # {予測対象のワード:登場回数}
                    if token in node.keywords:
                        node.keywords[token] += 1
                    else:
                        node.keywords[token] = 1
                    # FIXME:ノードの追加は新しく生成したときでは？
                    parent_node.add_child(node)
                    node.set_parent(parent_node)
                    parent_node = node
    
if __name__ == '__main__':
    trie_manager = TrieCompleteManager()
    trie_manager.setup()

    trie_manager.assess_mml_acuracy()
    print(trie_manager.accuracy, trie_manager.right_answer_nums, trie_manager.prediction_time)


    # file_manager = OneFileAssessManager('./learning_data/pascal.json')
    # original_cost, cost, saving_cost = file_manager.assess_file_keystroke(trie_manager)
    # print(original_cost, cost, saving_cost)
    # ranking, in_suggest_cnt, total = file_manager.assess_file_acuracy(trie_manager)
    # print(ranking, in_suggest_cnt, total)

    # print(f'sum:{sum(ranking)}')
    # print(complete_manager.predict(["x", "be"]))
