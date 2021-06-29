import os
from subprocess import run

from config import BINARIES_DIR

binaries = [os.path.join(BINARIES_DIR, f) for f in os.listdir(BINARIES_DIR) if os.path.isfile(os.path.join(BINARIES_DIR, f))]
print(binaries)

binaries += ["exit 1"]
for binary in binaries:
    # checkをTrueにするとrunが例外SubprocessErrorを投げるようになる。
    # capture_outputをTrueにすると返り値のクラスに標準出力、標準エラー出力が格納される。
    # shell=Trueにすると文字列としてコマンドを渡せる
    result = run([binary], shell=True, capture_output=True, check=False)
    print(f"returncode: {result.returncode}\nstdout: {result.stdout}\nstderr: {result.stderr}")

print("Done!")
