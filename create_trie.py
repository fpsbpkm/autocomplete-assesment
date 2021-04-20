import os
import json
import pickle
from pprint import pprint
from create_learning_data import check_token_type
from get_voc import parse_voc, load_symbol_dict
import preprocess
import re
import numpy as np

file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)
MML_DIR = '/mnt/c/mizar/mml'
MML_VCT = './data/mml.vct'

# トライの最大の深さ
N = 3

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
        self.accuracy = np.array([0 for _ in range(30)])
        self.prediction_time = 0
        self.setup()
    
    def setup(self):
        try:
            with open('trie_root', 'rb') as f:
                self.root = pickle.load(f)
        except:
            self.create()
    
    # mmlをスキャンし，引数のメソッドを順に実行する
    def apply_all_files(self, start, end, method_name):
        self.root = TrieNode('root')
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
                    accuracy, tmp, prediction_times = assess_file_manager.assess_file_acuracy(self)
                    print(accuracy)
                    self.accuracy += np.array(accuracy)
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
    def predict(self, user_input, type_to_symbols):
        variables = []
        labels = []
        n = len(user_input)
        tree = self.root
        
        # カーソル直前のトークン数
        if n > N:
            n = N

        token_list = user_input[::-1]
        for i in range(n):
            # FIXME:シンボルに接頭辞がついていないため，意図通りに動作しない
            token = check_token_type(token_list, i)
            # ユーザが利用している変数を保存しておく
            if token == '__variable_':
                variables.append(token_list[i])
            elif token == '__label_':
                labels.append(token_list[i])

            if token in tree.children:
                tree = tree.children[token]
            else:
                return {}

        # [[トークン, 出現回数]]の形式
        # 例：[['__variable', 100], ['be', 60] ... ]
        sorted_keywords = sorted(tree.keywords.items(), key=lambda x:x[1], reverse=True)

        # {キーワード:優先度}の形式で保存する
        # 例：{"be":1, "being":2}
        suggest_keywords = {}
        cnt = 1
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
            elif keyword[0] == '__variable_':
                # FIXME:変数の判別ができていない，1つしか提案できていない
                # for v in variables[::-1]:
                #     suggest_keywords[v] = cnt
                #     cnt += 1

                for v in ['x', 'y']:
                    suggest_keywords[v] = cnt
                    cnt += 1
                pass
            elif keyword[0] == '__label_':
                # FIXME:変数の場合と同様
                # for l in labels[::-1]:
                #     suggest_keywords[l] = cnt
                #     cnt += 1

                for l in ['A1', 'A2']:
                    suggest_keywords[l] = cnt
                    cnt += 1
                pass
            else:
                suggest_keywords[keyword[0]] = cnt
                cnt += 1
        return suggest_keywords

    def assess_mml_acuracy(self):
        self.apply_all_files(1100, 1355, 'acuracy')
        


class OneFileAssessManager:

    def __init__(self, file_name):
        self.file_name = file_name
        self.variables = []
        self.labels = []
        self.article = None
        self.type_to_symbols = None

        with open(self.file_name, 'r') as f:
            json_loaded = json.load(f)
        self.type_to_symbols = json_loaded['symbols']
        self.article = json_loaded['contents']

    
    def assess_file_acuracy(self, trie_manager):
        right_answer_nums = [0 for _ in range(30)]
        prediction_cnt = 0
        in_suggest_cnt = 0

        for line in self.article:
            line_tokens= []
            for token in line:
                # tokenは["x", "__variable_"]のようになっている
                # 予測プログラムには生のトークンを入力する
                line_tokens.append(token[0])

            for i in range(1, len(line_tokens)):
                # 最大でN-1トークンを切り出す，iのトークンを予測
                if i >= N:
                    user_input = line_tokens[i-N+1:i]
                else:
                    user_input = line_tokens[:i]
                
                answer = line[i][0]
                
                suggest_keywords = trie_manager.predict(user_input, self.type_to_symbols)
                prediction_cnt += 1
                
                if answer in suggest_keywords:
                    in_suggest_cnt += 1
                    rank = suggest_keywords[answer]

                # 30候補以内であればインクリメント
                if answer in suggest_keywords and suggest_keywords[answer] <= 30:
                    rank = suggest_keywords[answer]
                    right_answer_nums[rank-1] += 1
                # print(f'input:{user_input}')
                # print(f'suggest:{suggest_keywords}')
        print(right_answer_nums, in_suggest_cnt, prediction_cnt)
        return right_answer_nums, in_suggest_cnt, prediction_cnt


    def assess_file_keystroke(self, trie_manager):
        pass

    def create_one_file_trie(self, trie_manager):
        for line in self.article:
            length = len(line)
            for idx in range(1, length):
                token = line[idx][1]
                parent_node = None
                node = None
                diff = 0
                if idx-N+1 < 0:
                    diff = abs(idx-N+1)
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
                    if token in node.keywords:
                        node.keywords[token] += 1
                    else:
                        node.keywords[token] = 1
                    parent_node.add_child(node)
                    node.set_parent(parent_node)
                    parent_node = node
    
if __name__ == '__main__':
    trie_manager = TrieCompleteManager()
    trie_manager.setup()

    trie_manager.assess_mml_acuracy()
    print(trie_manager.accuracy, trie_manager.prediction_time)

    # file_manager = OneFileAssessManager('./learning_data/abcmiz_0.json')
    # ranking, in_suggest_cnt, total = file_manager.assess_file_acuracy(trie_manager)
    # print(ranking, in_suggest_cnt, total)

    # print(f'sum:{sum(ranking)}')
    # print(complete_manager.predict(["x", "be"]))
