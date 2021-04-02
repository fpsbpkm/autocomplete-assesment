import os
import json
from pprint import pprint

file_name = 'abcmiz_0.json'
file_path = os.path.join('./learning_data', file_name)

# トライの最大の深さ
N = 4

class TrieNode:
    def __init__(self, name):
        self.name = name
        self.children = set()
        self.parent = {}
        self.keywords = set()

    # def __repr__(self):
    #     return self.name

    def __eq__(self, other):
        print(other)
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_child(self, node):
        self.children.add(node)
    
    def add_keyword(self, keyword):
        if keyword in self.keywords:
            keyword.increment()
            pass
        else:
            self.keywords.add(keyword)

    def get_name(self):
        return self.name

    def get_children(self):
        return self.children
    
    def get_keywords(self):
        return self.keywords


class Keyword:
    def __init__(self, type):
        self.type = type
        self.num = 1
    
    def increment(self):
        self.num += 1



prefix_tree = {}

if __name__ == '__main__':

    with open(file_path) as f:
        json_loaded = json.load(f)
        # print(json_loaded['symbols'])
        root = TrieNode('root')
        for line in json_loaded['contents']:
            length = len(line)
            part_tree = prefix_tree

            if length < N:
                continue
            for idx in range(N-1, length):
                token = line[idx][1]
                for j in range(idx-N+1, idx):
                    if j == idx-N+1:
                        parent_node = root
                    
                    # 同名のノードが存在するか確認する必要がある
                    # print(parent_node.get_children())
                    if line[j][1] in parent_node.get_children():
                        # print('exist!')
                        continue

                    node = TrieNode(line[j][1])
                    # keyword = Keyword(line[j][1])
                    # node.add_keyword(keyword)
                    parent_node.add_child(node)
                    parent_node = node

                keyword = Keyword(token)
                parent_node.add_keyword(keyword)

    children = root.get_children()
    for child in children:
        print(child.name)
        # keywords = child.get_keywords()
        # for k in keywords:
        #     print(k.type, k.num, end='')
        # print('')
