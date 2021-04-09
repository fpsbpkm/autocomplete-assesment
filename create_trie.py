import os
import json
import pickle
from pprint import pprint
from create_learning_data import check_token_type
from get_voc import parse_voc, load_symbol_dict
import preprocess

file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)
MML_DIR = '/mnt/c/mizar/mml'
MML_VCT = './data/mml.vct'

# トライの最大の深さ
N = 4

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
            # print(line)
            env_tokens.append(line.split())

        # print(env_tokens)
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
        print(self.type_to_symbols)

    # 「__M_」などを具体的に，優先度をつけて提案できるように
    def predict(self, user_input):
        n = len(user_input)
        tree = self.root
        
        if n > N:
            n = N

        token_list = user_input[::-1]

        for i in range(n):
            token = check_token_type(token_list, i)
            if token in tree.children:
                tree = tree.children[token]
            else:
                print("nothing")
                return []
        sorted_keywords = sorted(tree.keywords.items(), key=lambda x:x[1], reverse=True)
        print(f'input:{user_input}')
        print(f'output:{sorted_keywords}')
        print()

        suggest_keywords = []

        for keyword in sorted_keywords:
            if keyword == '__M_':
                suggest_keywords.extend(self.type_to_symbols['M'])
            else:
                pass

    def assess_acuracy(self):
        self.scan_files(1100, 1355, self.assess_one_file_acuracy)

    def assess_one_file_acuracy(self):
        self.create_type_to_symbols()
        json_loaded = None
        with open(self.file_name, 'r') as f:
            json_loaded = json.load(f)

        for line in json_loaded['contents']:
            for i in range(1, len(line)):
                if i > N:
                    user_input = line[i-N:i]
                else:
                    user_input = line[:i]
                answer = line[i][1]
    

    def assess_keystroke(self):
        self.scan_files(1100, 1355, self.assess_one_file_keystroke)

    def assess_one_file_keystroke(self):
        self.create_type_to_symbols()
        pass

    
if __name__ == '__main__':
    complete_manager = TrieCompleteManager()
    complete_manager.setup()
    complete_manager.predict(["let", "x", "be"])
    # file_name = os.path.join(MML_DIR, "armstrng.miz")
    # vocs = parse_voc(file_name)
    # symbol_dict = load_symbol_dict(MML_VCT, vocs)
    # type_to_symbols = create_type_to_symbols(symbol_dict)
    # pprint(type_to_symbols)
