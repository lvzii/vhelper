import os
from setuptools import setup


def get_version():
    with open(os.path.join("src", "vhelper", "__init__.py"), "r", encoding="utf-8") as f:
        file_content = f.read()
        for line in file_content.splitlines():
            if line.startswith("__version__"):
                version_line = line
                verision = version_line.split("=")[-1].strip().strip('"').strip("'")
                return verision


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
    # res = get_version()
    # print(res)
