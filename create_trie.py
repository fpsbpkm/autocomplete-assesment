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


def create():
    mml_lar = open("/mnt/c/mizar/mml.lar", "r")
    mml = []
    for i in mml_lar.readlines():
        mml.append(os.path.join('./learning_data', i.replace('\n', '.json')))
    mml_lar.close()

    # mml = [os.path.join('./learning_data', 'abcmiz_0.json')]
    root = TrieNode('root')
    for file_path in mml[:1100]:
        print(file_path)
        try:
            with open(file_path) as f:
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
                                parent_node = root
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
        except Exception as e:
            print(e)
            continue
        

        with open('./trie_root', 'wb') as f:
            pickle.dump(root, f)

# 「__M_」などを具体的に，優先度をつけて提案できるように
def predict(text, tree):
    n = len(text)+1

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

def assess_acuracy(file_name):
    pass

def assess_keystroke(file_name):
    pass


def create_type_to_symbols(symbol_dict):
    type_to_symbols = {}
    for key in symbol_dict:
        symbol_type = symbol_dict[key]['type']
        
        if not symbol_type in type_to_symbols:
            type_to_symbols[symbol_type] = [key]
        else:
            type_to_symbols[symbol_type].append(key)
    
    return type_to_symbols

    
if __name__ == '__main__':
    # create()
    file_name = os.path.join(MML_DIR, "armstrng.miz")
    vocs = parse_voc(file_name)
    symbol_dict = load_symbol_dict(MML_VCT, vocs)
    type_to_symbols = create_type_to_symbols(symbol_dict)
    pprint(type_to_symbols)
    with open ('trie_root', 'rb') as f:
        tree = pickle.load(f)
    # predict(["let", "x", "be"], tree)
    # predict(["redefine", "attr", "a"], tree)
    # predict(["let", "x"], tree)
    # predict(["ex", "x"], tree)
    # predict(["assume", "x"], tree)
    # predict(["__label_"], tree)
