import pickle
from create_learning_data import check_token_type
from create_trie import TrieNode

N = 4
test = TrieNode('test')
print(vars(test))
def predict(text):
    with open ('trie_root', 'rb') as f:
        tree = pickle.load(f)
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
    

predict(["let", "x", "be"])
predict(["redefine", "attr", "x"])
predict(["let", "x"])
predict(["let"])
predict(["assume"])
predict(["hence"])