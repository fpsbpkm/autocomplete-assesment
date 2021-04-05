import os
import json
from pprint import pprint
from create_learning_data import check_token_type

file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)

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

    def add_child(self, node_name, node):
        self.children[node_name] = node
        # self.children.add(node)
    
    def add_keyword(self, keyword):
        if keyword in self.get_keywords():
            # 遅いため考え直すべき
            for word in self.get_keywords():
                if word == keyword:
                    target = word
            target.increment()
        else:
            self.keywords.add(keyword)

    def get_children(self):
        return self.children
    
    def get_keywords(self):
        return self.keywords


class Keyword:
    def __init__(self, type):
        # TODO:typeは辞書のキーに変更する
        self.type = type
        self.num = 1

    def __repr__(self):
        return self.type

    def __eq__(self, other):
        return self.type == other.type

    def __hash__(self):
        return hash(self.type)
    
    def increment(self):
        self.num += 1
        # print(f'type:{self.type}, num:{self.num}')

prefix_tree = {}

if __name__ == '__main__':
    with open(file_path) as f:
        json_loaded = json.load(f)
        root = TrieNode('root')
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
                    # 同名のノードが存在すれば取得
                    if node_name in parent_node.children:
                        node = parent_node.children[node_name]
                    # 同名のノードが存在しなければ生成
                    else:
                        node = TrieNode(node_name)

                    if token in node.keywords:
                        node.keywords[token] += 1
                    else:
                        node.keywords[token] = 1

                    parent_node.add_child(node_name, node)
                    node.parent[parent_node.name] = parent_node
                    parent_node = node    

    nodes = root.get_children()
    cnt = 0
    for node_key in nodes:
        cnt += 1
        # print()
        # print(f'parent:{nodes[node_key].parent}')

        # print(f'children:{vars(nodes[node_key])["children"]}')
        # print(f'node:{nodes[node_key].name}')
        # print(f'keywords:{nodes[node_key].keywords}')
        # keywords = child.get_keywords()
        # for word in keywords:
        #     print(word.type, word.num)
        # g_children = child.get_children()
        # for g_child in g_children:
        #     print(f'g_child:{g_child}')
        # break

def predict(text):
    tree = root
    n = len(text)+1
    token_list = text[::-1]

    for i in range(n-1):
        token = check_token_type(token_list, i)
        if token in tree.children:
            tree = tree.children[token]
        else:
            print("nothing")
            return
    print(tree.keywords)
    

predict(["let", "x", "be"])
predict(["redefine", "attr", "x"])
predict(["let", "x"])
predict(["let"])
predict(["assume"])