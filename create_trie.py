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

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        # otherは文字列
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_child(self, node):
        self.children.add(node)
    
    def add_keyword(self, keyword):
        if keyword in self.get_keywords():
            # 遅いため考え直すべき
            for word in self.get_keywords():
                if word == keyword:
                    target = word
            target.increment()
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

    def __repr__(self):
        return self.type

    def __eq__(self, other):
        return self.type == other.type

    def __hash__(self):
        return hash(self.type)
    
    def increment(self):
        self.num += 1
        # print(f'type:{self.type}, num:{self.num}')


if __name__ == '__main__':
    with open(file_path) as f:
        json_loaded = json.load(f)
        root = TrieNode('root')
        for line in json_loaded['contents']:
            length = len(line)
            
            # 短い階層は現状では考えない
            if length < N:
                continue

            for idx in range(N-1, length):
                token = line[idx][1]
                parent_node = None
                node = None
                for j in reversed(range(idx-N+1, idx)):
                    if j == idx-1:
                        parent_node = root
                    
                    # 同名のノードが存在すれば取得
                    if TrieNode(line[j][1]) in parent_node.get_children():
                        # 遅いため，よろしくない
                        for child in parent_node.get_children():
                            if TrieNode(line[j][1]) == child:
                                node = child
                    # 同名のノードが存在しなければ生成
                    else:
                        node = TrieNode(line[j][1])

                    keyword = Keyword(token)
                    node.add_keyword(keyword)

                    parent_node.add_child(node)
                    parent_node = node    

    children = root.get_children()
    cnt = 0
    for child in children:
        cnt += 1
        print()
        print(f'child:{child.name}')
        print(f'children:{vars(child)["children"]}')
        # keywords = child.get_keywords()
        # for word in keywords:
        #     print(word.type, word.num)
        # g_children = child.get_children()
        # for g_child in g_children:
        #     print(f'g_child:{g_child}')
        # break

print(cnt)
