import os
import re

from setuptools import setup


def get_version():
    with open(os.path.join("src", "vhelper", "__init__.py"), "r", encoding="utf-8") as f:
        file_content = f.read()
        pattern = r"{}\W*=\W*\'([^\"]+)\'".format("__version__")
        version = re.findall(pattern, file_content)
        return version


_deps = ["nlpertools"]


def main():
    setup(
        # https://juejin.cn/post/7369349560421040128
        install_requires=_deps,
        extras_require={
            "none": [],
        },
        version=get_version(),
    )


if __name__ == "__main__":
    main()
    # get_version()
