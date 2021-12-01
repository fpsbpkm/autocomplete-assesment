import os
import preprocess

DATA_DIR = "./data/"
MML_VCT = os.path.join(DATA_DIR, "mml.vct")
MML_DIR = "/mnt/c/mizar/mml"


def load_symbol_dict(mml_vct, miz_files=None):
    symbol_dict = {}
    if miz_files is not None:
        miz_files = set(miz_files)
        miz_files.add("HIDDEN")

    lines = None
    with open(mml_vct) as f:
        lines = f.readlines()
        assert len(lines) > 0

    ignore_next_line = False
    ignore_this_file = False
    for line in lines:
        line = line.rstrip()
        if line[0] == "#":
            filename = line[1:]
            ignore_next_line = True
            if miz_files and filename not in miz_files:
                ignore_this_file = True
            else:
                ignore_this_file = False
        elif ignore_next_line:
            # number of each type of symbols are written here -> ignore
            ignore_next_line = False
        elif len(line) > 0 and not ignore_this_file:
            # symbol is written in this line
            load_symbol_in_line(line, filename, symbol_dict)

    return symbol_dict


def load_symbol_in_line(line, filename, symbol_dict):
    """Read symbol written in a line of mml.vct file and add to symbol_dict.
    This function read one or two symbol written in a line of mml.vct file.
    The format example of mml.vct is shown at the comment of create_symbol_dict().
    Args:
        line (str): A line of mml.vct file. Other redundant lines are
        filename (str): File name in which the symbol is defined
    """
    assert len(line) > 1

    symbol_type = line[0]
    values = line[1:].split(" ")
    name = values[0]
    # assert name not in self.symbol_dict
    if len(values) == 1:
        # only one symbol is defined
        symbol_dict[name] = {"type": symbol_type, "filename": filename}
    else:
        assert len(values) == 2
        if symbol_type == "O" and values[1].isdigit():
            # priority is included
            symbol_dict[name] = {
                "type": symbol_type,
                "filename": filename,
                "priority": values[1],
            }
        else:
            # two names are defined
            symbol_dict[name] = {"type": symbol_type, "filename": filename}

            assert values[1] not in symbol_dict
            symbol_dict[values[1]] = \
                {"type": symbol_type, "filename": filename}


def parse_voc(filename):
    lexer = preprocess.Lexer()
    lexer.load_symbol_dict(MML_VCT)
    lexer.build_len2symbol()

    with open(filename, "r") as f:
        # ファイルによっては変数名のエラーが出るため注意
        try:
            lines = f.readlines()
            assert len(lines) > 0
        except Exception:
            print("Error!")

    env_lines, text_proper_lines = lexer.separate_env_and_text_proper(lines)
    env_lines = lexer.remove_comment(env_lines)
    env_tokenized_lines, position_map = lexer.lex(env_lines)
    # print(env_tokenized_lines)
    env_tokens = []
    for line in env_tokenized_lines:
        if line == "":
            continue
        # print(line)
        env_tokens.append(line.split())

    # print(env_tokens)
    voc_flag = False
    vocs = []
    for line in env_tokens:
        for token in line:
            if token == "vocabularies":
                voc_flag = True
            if voc_flag and token == ";":
                voc_flag = False
            if voc_flag and not token == "," and not token == "vocabularies":
                vocs.append(token)
    return vocs


if __name__ == "__main__":
    filename = os.path.join(MML_DIR, "armstrng.miz")
    vocs = parse_voc(filename)
    # print(MML_VCT)
    symbol_dict = load_symbol_dict(MML_VCT, vocs)
    print(symbol_dict)
    for symbol in symbol_dict:
        if symbol_dict[symbol]["type"] == "M":
            print(symbol)
