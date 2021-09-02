from subprocess import CalledProcessError, run


def prepare_ubuntu_vm(domain_name):
    """ubuntu Desktop 20.04のVMを用意する。
    
    毎回OSインストールするのは時間がかかるので、インストール済みの既存のVMをクローンする。

    Args:
        domain_name (str) : 作成するクローンのVMのドメインネーム
    """

    try:
        result = run(["virt-clone", "-o", "aubuntu20.04", "-n", domain_name, "--auto-clone"], check=True, text=False)
    except CalledProcessError as e:
        print(e)
        exit(1)

    print(result)


    return


if __name__ == "__main__":
    prepare_ubuntu_vm('a')

