import os
import json
import pickle
from pprint import pprint
from create_learning_data import check_token_type
from get_voc import parse_voc, load_symbol_dict

file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)
MML_DIR = '/mnt/c/mizar/mml'
MML_VCT = './data/mml.vct'

# トライの最大の深さ
N = 4

class TrieNode:
    def __init__(self, name):
        # TODO:nameは辞書のキーに変更する
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
        self.symbols = None
    
    def setup(self):
        try:
            with open ('trie_root', 'rb') as f:
                self.root = pickle.load(f)
        except:
            self.create()

    def create(self):
        mml_lar = open("/mnt/c/mizar/mml.lar", "r")
        mml = []
        for i in mml_lar.readlines():
            mml.append(os.path.join('./learning_data', i.replace('\n', '.json')))
        mml_lar.close()

        # mml = [os.path.join('./learning_data', 'abcmiz_0.json')]
        self.root = TrieNode('root')
        for file_path in mml[:1100]:
            print(file_path)
            self.file_name = file_path
            try:
                self.create_one_file_trie()
            except Exception as e:
                print(e)
                continue

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

    # 「__M_」などを具体的に，優先度をつけて提案できるように
    def predict(self, text):
        n = len(text)+1
        tree = self.root

        if n > N:
            n = N

        token_list = text[::-1]

        for i in range(n-1):
            token = check_token_type(token_list, i)
            if token in tree.children:
                tree = tree.children[token]
            else:
                print("nothing")
                return
        sorted_keywords = sorted(tree.keywords.items(), key=lambda x:x[1], reverse=True)
        print(f'input:{text}')
        print(f'output:{sorted_keywords}')
        print()

        for keyword in sorted_keywords:
            if keyword == '__M_':
                pass
            else:
                pass

    def assess_acuracy(self, file_name):
        pass

    def assess_keystroke(self, file_name):
        pass


    def create_type_to_symbols(self, symbol_dict):
        type_to_symbols = {}
        for key in symbol_dict:
            symbol_type = symbol_dict[key]['type']
            
            if not symbol_type in type_to_symbols:
                type_to_symbols[symbol_type] = [key]
            else:
                type_to_symbols[symbol_type].append(key)
        
        return type_to_symbols

    
if __name__ == '__main__':
    complete_manager = TrieCompleteManager()
    complete_manager.setup()
    complete_manager.predict(["let", "x", "be"])
    # file_name = os.path.join(MML_DIR, "armstrng.miz")
    # vocs = parse_voc(file_name)
    # symbol_dict = load_symbol_dict(MML_VCT, vocs)
    # type_to_symbols = create_type_to_symbols(symbol_dict)
    # pprint(type_to_symbols)


