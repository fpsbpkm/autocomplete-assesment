import os

MML_DIR = '/mnt/c/mizar/mml'
f = os.path.join(MML_DIR, "henmodel")+'.miz'
with open(f, 'r') as f:
    # ファイルによっては変数名のエラーが出るため注意
    lines = f.readlines()
