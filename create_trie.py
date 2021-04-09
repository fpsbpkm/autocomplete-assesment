import os
import json
import pickle
from pprint import pprint
from create_learning_data import check_token_type
from get_voc import parse_voc, load_symbol_dict
import preprocess
import re

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
        self.file_name = None
        self.type_to_symbols = None
    
    def setup(self):
        try:
            with open ('trie_root', 'rb') as f:
                self.root = pickle.load(f)
        except:
            self.create()
    
    # mmlをスキャンし，引数のメソッドを順に実行する
    def scan_files(self, start, end, execute_method):
        self.root = TrieNode('root')
        mml_lar = open("/mnt/c/mizar/mml.lar", "r")
        mml = []
        for i in mml_lar.readlines():
            mml.append(os.path.join('./learning_data', i.replace('\n', '.json')))
        mml_lar.close()
        for file_path in mml[start:end]:
            print(file_path)
            self.file_name = file_path
            try:
                execute_method()
            except Exception as e:
                print(e)
                continue
    
    def create(self):
        self.scan_files(0, 1100, self.create_one_file_trie)
        with open('./trie_root', 'wb') as f:
            pickle.dump(self.root, f)

    def create_one_file_trie(self):
        json_loaded = None
        with open(self.file_name) as f:
            json_loaded = json.load(f)
        for line in json_loaded['contents']:
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
                        parent_node = self.root
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
    def predict(self, user_input):
        variables = []
        labels = []
        n = len(user_input)
        tree = self.root
        
        if n > N:
            n = N

        token_list = user_input[::-1]
        # print(f"user_input:{user_input}")
        for i in range(n):
            token = check_token_type(token_list, i)
            # ユーザが利用している変数を保存しておく
            if token == '__variable_':
                variables.append(token_list[i])
            elif token == '__label_':
                labels.append(token_list[i])

            if token in tree.children:
                tree = tree.children[token]
            else:
                # print("nothing")
                return {}
        sorted_keywords = sorted(tree.keywords.items(), key=lambda x:x[1], reverse=True)

        # {キーワード:優先度}の形式で保存する
        # 例：{"be":1, "being":2}
        suggest_keywords = {}
        cnt = 1
        for keyword in sorted_keywords:
            # 「_\w__」の条件で，正規表現を使う
            matched = re.match(r'__(\w)_', keyword[0])
            if matched:
                symbol_type = matched.groups()[0]
                # print(f"symbol_type:{symbol_type}")
                if symbol_type is None:
                    return {}
                for word in self.type_to_symbols[symbol_type[0]]:
                    suggest_keywords[word] = cnt
                    cnt += 1
                # FIXME:下は一時的なコード
                # suggest_keywords[keyword[0]] = cnt
                # cnt += 1
            elif keyword[0] == '__variable_':
                # 最も最近出てきた変数を提案する
                for v in variables[::-1]:
                    suggest_keywords[v] = cnt
                    cnt += 1
            elif keyword[0] == '__label_':
                # 最も最近出てきたラベルを提案する
                for l in labels[::-1]:
                    suggest_keywords[l] = cnt
                    cnt += 1
            else:
                suggest_keywords[keyword[0]] = cnt
                cnt += 1
        # print(suggest_keywords)
        return suggest_keywords

    def assess_acuracy(self):
        self.scan_files(1100, 1355, self.assess_one_file_acuracy)

    def assess_one_file_acuracy(self):
        # jsonファイルからsymbolsを読みだすだけで良い
        # self.create_type_to_symbols()
        json_loaded = None
        right_answer_nums = [0 for _ in range(30)]

        with open(self.file_name, 'r') as f:
            json_loaded = json.load(f)
        self.type_to_symbols = json_loaded['symbols']
        prediction_cnt = 0
        tmp_cnt = 0
        for line in json_loaded['contents']:
            line_tokens= []
            for token in line:
                # tokenは["x", "__variable_"]のようになっている
                # 予測プログラムには生のトークンを入力する
                line_tokens.append(token[0])

            for i in range(1, len(line_tokens)):
                # 最大でN-1トークンを切り出す
                if i > N:
                    user_input = line_tokens[i-N+1:i]
                else:
                    user_input = line_tokens[:i]
                
                answer = line[i][0]
                suggest_keywords = self.predict(user_input)
                prediction_cnt += 1

                # pprint(f'answer:{answer}, suggests:{suggest_keywords}')
                
                if answer in suggest_keywords:
                    tmp_cnt += 1
                    rank = suggest_keywords[answer]
                    print(answer, rank)

                # 30候補以内であればインクリメント
                if answer in suggest_keywords and suggest_keywords[answer] <= 30:
                    rank = suggest_keywords[answer]
                    right_answer_nums[rank-1] += 1
                    
        print(tmp_cnt)
        print(prediction_cnt)
        return right_answer_nums

    def assess_keystroke(self):
        self.scan_files(1100, 1355, self.assess_one_file_keystroke)

    def assess_one_file_keystroke(self):
        self.create_type_to_symbols()
        pass

    
if __name__ == '__main__':
    complete_manager = TrieCompleteManager()
    complete_manager.setup()
    
    
    complete_manager.file_name = "./learning_data/yellow19.json"
    result = complete_manager.assess_one_file_acuracy()
    print(result)

    # complete_manager.predict(["let", "x", "be"])
