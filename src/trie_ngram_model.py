import pickle
import time
import re
import os
import json
from collections import OrderedDict

os.environ["PROJECT_DIR"] = os.path.dirname(os.path.dirname(f"{__file__}"))
PROJECT_DIR = os.environ["PROJECT_DIR"]


# 予測にクラストークンを使うか
IS_USING_CLASS_NAME = int(True)


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


class TrieNgramModel:
    def __init__(self):
        self.N = 5
        self.setup()

    def setup(self):
        try:
            # WARNING:利用するトライ木に注意
            with open(f"{PROJECT_DIR}/trie_root", "rb") as f:
                self.root = pickle.load(f)
        except OSError:
            self.root = TrieNode("root")
            self.learning()

    # トライ木の作成
    def learning(self):
        mml_lar = open(f"{PROJECT_DIR}/about_mml/mml.lar", "r")
        mml = []
        for i in mml_lar.readlines():
            mml.append(
                os.path.join(f"{PROJECT_DIR}/learning_data", i.replace("\n", ".json"))
            )
        mml_lar.close()
        # FIXME:本来は1100
        for file_path in mml[0:1100]:
            try:
                with open(file_path, "r") as f:
                    json_loaded = json.load(f)
                article = json_loaded["contents"]
                N = self.N
                print(file_path)
                for line in article:
                    length = len(line)
                    for idx in range(1, length):
                        # WARNING: IS_USING_CLASS_NAMEが意図通りに設定されているか注意
                        token = line[idx][IS_USING_CLASS_NAME]
                        parent_node = None
                        node = None
                        diff = 0
                        # 直前のトークン数がN未満の場合
                        if idx - N + 1 < 0:
                            diff = abs(idx - N + 1)
                        # reversed(range(0, 3)) -> 2, 1, 0
                        for j in reversed(range(idx - N + 1 + diff, idx)):
                            if j == idx - 1:
                                parent_node = self.root
                            # WARNING: IS_USING_CLASS_NAMEが意図通りに設定されているか注意
                            node_name = line[j][IS_USING_CLASS_NAME]
                            # 既に同名のノードが存在すれば取得
                            if node_name in parent_node.children:
                                node = parent_node.children[node_name]
                            # 同名のノードが存在しない場合は生成し，子ノードとして追加
                            else:
                                node = TrieNode(node_name)
                                parent_node.add_child(node)
                            # 各ノードに予測対象のキーワードを保存
                            # node.keywordsは{予測対象のワード:登場回数}の形式
                            if token in node.keywords:
                                node.keywords[token] += 1
                            else:
                                node.keywords[token] = 1
                            node.set_parent(parent_node)
                            parent_node = node
            except Exception:
                continue

        # WARNING: 新しくトライ木を作りたい場合はコメントアウトを解除
        with open(f"{PROJECT_DIR}/trie_root", "wb") as f:
            pickle.dump(self.root, f)

    def predict(self, user_input, parsed_input, type_to_symbols, variables, labels):
        node = self.root
        parsed_input_reversed = parsed_input[::-1]
        user_input_reversed = user_input[::-1]

        # ユーザ入力から，トライ木を検索
        for i in range(len(parsed_input_reversed)):
            # 入力は型トークン
            # 例：「__M_」「__variable_」など
            token = parsed_input_reversed[i]
            # ユーザが利用していて，登録されていない変数を保存
            if token == "__variable_" and user_input_reversed[i] not in set(variables):
                variables.append(user_input_reversed[i])
            # ユーザが利用していて，登録されていないラベルを保存
            elif token == "__label_" and user_input_reversed[i] not in set(labels):
                labels.append(user_input_reversed[i])
            # トライ木の検索
            if token in node.children:
                node = node.children[token]
            else:
                return {}
        # sorted_keywordsは[[トークン, 出現回数]]の形式
        # 例：[['__variable_', 100], ['be', 60] ... ]
        sorted_keywords = sorted(
            node.keywords.items(), key=lambda x: x[1], reverse=True
        )
        # {キーワード:順位}の形式で保存する
        # 例：{"be":1, "being":2}
        suggest_keywords = OrderedDict({})
        # 提案候補の順位を記録する変数
        rank = 1
        # 「__variable_」「__M_」などを具体的なトークンに置き換える処理
        for keyword in sorted_keywords:
            matched = re.match(r"__(\w\d*)_", keyword[0])
            if matched:
                symbol_type = matched.groups()[0]
                # 本来はあり得ない条件
                if symbol_type is None:
                    continue
                # 環境部でimportしていないシンボルクラスが提案された場合は何もしない
                if symbol_type not in type_to_symbols:
                    continue
                for word in type_to_symbols[symbol_type[0]]:
                    suggest_keywords[word] = rank
                    # REVIEW:+1すべきか要確認
                    rank = len(suggest_keywords) + 1
            # ユーザが利用した変数を提案
            elif keyword[0] == "__variable_":
                for v in list(variables)[::-1]:
                    suggest_keywords[v] = rank
                    rank = len(suggest_keywords) + 1
            # ユーザが利用したラベルを提案
            elif keyword[0] == "__label_":
                for label in list(labels)[::-1]:
                    suggest_keywords[label] = rank
                    rank = len(suggest_keywords) + 1
            elif keyword[0] == "__number_":
                pass
            else:
                suggest_keywords[keyword[0]] = rank
                rank = len(suggest_keywords) + 1

        return suggest_keywords


if __name__ == "__main__":
    from assess_keystroke import assess_mml_keystroke
    from assess_accuracy import assess_mml_accuracy

    print(PROJECT_DIR)
    del os.environ["PROJECT_DIR"]
    start_time = time.time()
    trie_model = TrieNgramModel()
    # np.set_printoptions(precision=1)
    # assess_mml_accuracy(trie_model)
    original_cost, reduced_cost, prediction_times = assess_mml_keystroke(trie_model)
    print(original_cost, reduced_cost, prediction_times)
    elapsed_time = time.time() - start_time
    print(f"N:{trie_model.N}, elapsed_time:{elapsed_time}")
