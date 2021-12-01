# トークンに種類を付与する前処理するプログラム
# .mizファイルから.jsonファイルを生成
import preprocess
import os
import re
import json
from get_voc import load_symbol_dict, parse_voc

PROJECT_DIR = os.environ['PROJECT_DIR']
DATA_DIR = f"{PROJECT_DIR}/data/"
MML_VCT = os.path.join(DATA_DIR, "mml.vct")
MML_DIR = "/mnt/c/mizar/mml"

RESERVED_WORDS = set(
    [
        "according",
        "aggregate",
        "all",
        "and",
        "antonym",
        "are",
        "as",
        "associativity",
        "assume",
        "asymmetry",
        "attr",
        "be",
        "begin",
        "being",
        "by",
        "canceled",
        "case",
        "cases",
        "cluster",
        "coherence",
        "commutativity",
        "compatibility",
        "connectedness",
        "consider",
        "consistency",
        "constructors",
        "contradiction",
        "correctness",
        "def",
        "deffunc",
        "define",
        "definition",
        "definitions",
        "defpred",
        "do",
        "does",
        "end",
        "environ",
        "equals",
        "ex",
        "exactly",
        "existence",
        "for",
        "from",
        "func",
        "given",
        "hence",
        "hereby",
        "holds",
        "idempotence",
        "identify",
        "if",
        "iff",
        "implies",
        "involutiveness",
        "irreflexivity",
        "is",
        "it",
        "let",
        "means",
        "mode",
        "non",
        "not",
        "notation",
        "notations",
        "now",
        "of",
        "or",
        "otherwise",
        "over",
        "per",
        "pred",
        "prefix",
        "projectivity",
        "proof",
        "provided",
        "qua",
        "reconsider",
        "reduce",
        "reducibility",
        "redefine",
        "reflexivity",
        "registration",
        "registrations",
        "requirements",
        "reserve",
        "sch",
        "scheme",
        "schemes",
        "section",
        "selector",
        "set",
        "sethood",
        "st",
        "struct",
        "such",
        "suppose",
        "symmetry",
        "synonym",
        "take",
        "that",
        "the",
        "then",
        "theorem",
        "theorems",
        "thesis",
        "thus",
        "to",
        "transitivity",
        "uniqueness",
        "vocabularies",
        "when",
        "where",
        "with",
        "wrt",
    ]
)

SPECIAL_SYMBOLS = set(
    [
        ",",
        ";",
        ":",
        "(",
        ")",
        "[",
        "]",
        "{",
        "}",
        "=",
        "&",
        "->",
        ".=",
        "$1",
        "$2",
        "$3",
        "$4",
        "$5",
        "$6",
        "$7",
        "$8",
        "$9",
        "(#",
        "#)",
        "...",
        "$10",
    ]
)

NUMBERS = set(["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"])


def is_reserved_word(word):
    if word in RESERVED_WORDS or word in SPECIAL_SYMBOLS:
        return True
    else:
        return False


def check_token_type(line, idx):
    token = line[idx]
    matched = re.match(r"__\w\d*_", token)

    # NOTE:ラベル以降の判定が正しくない
    if matched:
        return matched[0]
    elif is_reserved_word(token):
        return token
    # NOTE:数字を「変数」と判断させないよう，以下の処理が必要
    elif re.fullmatch(r"^[0-9]+$", token):
        return "__number_"
    elif idx + 1 <= len(line) - 1 and line[idx + 1] == ":":
        return "__label_"
    # NOTE: ラベルと変数の区別が完璧ではないが，ほとんどの場合で正しく分類できていると思われる
    elif "by" in set(line[:idx]):
        return "__label_"
    elif "from" in set(line[:idx]):
        return "__label_"
    else:
        return "__variable_"


if __name__ == "__main__":
    mml_lar = open("/mnt/c/mizar/mml.lar", "r")
    mml = []
    error_file_to_msg = {}
    for i in mml_lar.readlines():
        mml.append(i.replace("\n", ""))

    for filename in mml:
        f = os.path.join(MML_DIR, filename) + ".miz"
        lexer = preprocess.Lexer()
        lexer.load_symbol_dict(MML_VCT)
        lexer.build_len2symbol()

        with open(f, "r") as f:
            # ファイルによっては変数名のエラーが出るため注意
            try:
                lines = f.readlines()
                assert len(lines) > 0
            except Exception:
                continue
            env_lines, text_proper_lines = \
                lexer.separate_env_and_text_proper(lines)
            text_proper_lines = lexer.remove_comment(text_proper_lines)
            # トークンの取得
            try:
                tokenized_lines, position_map = lexer.lex(text_proper_lines)
            except Exception as e:
                error_file_to_msg[filename] = str(e)
                continue
            tokens = []
            for line in tokenized_lines:
                tokens.append(line.split())

        OUTPUT_DIR = f"{PROJECT_DIR}/learning_data"
        output_file = os.path.join(OUTPUT_DIR, filename) + ".json"
        file_dict = {"symbols": {}, "contents": []}
        # 「let x be Nat」の場合，
        # [[let, let], [x, __variable_], [be, be], [Nat, __M_]]
        # の形式にしたjsonファイルを作成
        for line in tokens:
            line_data = []
            for i in range(len(line)):
                token = re.sub(r"__\w\d*_", "", line[i])
                token_type = check_token_type(line, i)
                line_data.append([token, token_type])
            if line_data:
                file_dict["contents"].append(line_data)

        filename = os.path.join(MML_DIR, filename + ".miz")
        vocs = parse_voc(filename)
        symbol_dict = load_symbol_dict(MML_VCT, vocs)

        type_to_symbols = {}
        for key in symbol_dict:
            symbol_type = symbol_dict[key]["type"]
            if symbol_type not in type_to_symbols:
                type_to_symbols[symbol_type] = [key]
            else:
                type_to_symbols[symbol_type].append(key)

        for symbol_type in type_to_symbols:
            file_dict["symbols"][symbol_type] = type_to_symbols[symbol_type]

        with open(output_file, "w") as f:
            json.dump(file_dict, f)
            print(filename)
