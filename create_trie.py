import os
import json
import pickle
from pprint import pprint
from create_learning_data import check_token_type


file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)
MML_DIR = '/mnt/c/mizar/mml'

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
    print(f'input:{text}')
    print(f'output:{tree.keywords}')
    print()


def assess_acuracy(file_name):
    pass

def assess_keystroke(file_name):
    pass


    
if __name__ == '__main__':
    # create()
    with open ('trie_root', 'rb') as f:
        tree = pickle.load(f)
    predict(["let", "x", "be"], tree)
    # predict(["redefine", "attr", "a"], tree)
    # predict(["let", "x"], tree)
    predict(["the"], tree)
    predict(["assume", "x"], tree)
    # predict(["__label_"], tree)