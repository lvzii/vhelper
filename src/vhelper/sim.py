from argparse import OPTIONAL
import os
import subprocess
import nlpertools
import sys
from pathlib import Path
import re
from typing import Optional

"""
统一说明
如果returncode是0,说明成功
如果returncode是非0,说明失败

"""


class SimSoftware(object):
    """
    仿真软件的基类
    """

    def __init__(self, name):
        self.name = name


# modelsim
class ModelSim(object):
    def __init__(self):
        self.name = "ModelSim"

    def get_top_module_name(self, stdout):
        # 从仿真输出中提取顶层模块名
        top_module_name = re.findall(r"Top level modules:\s*(\w+)\n", stdout, re.MULTILINE)
        return top_module_name[0].strip()

    def compile(self, compile_dir):
        filelist = nlpertools.listdir(Path(compile_dir), including_dir=True)
        working_dir = Path(compile_dir) / "work"
        result = subprocess.run(
            ["vlib", str(working_dir)], capture_output=True, text=True, encoding="utf-8", errors="ignore"
        )

        result = subprocess.run(
            ["vlog"]
            + ["-sv"]
            + ["-work", str(working_dir)]
            + [str(f) for f in filelist if str(f).endswith(".v") or str(f).endswith(".sv")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        return result

    def sim(self, sim_dir):
        """
        return:  仿真结果
        仿真结果

        """
        working_dir = Path(sim_dir) / "work"
        result = self.compile(sim_dir)

        top_module_name = self.get_top_module_name(result.stdout)
        result = subprocess.run(
            ["vsim", "-c", top_module_name, "-do", "run -all; exit"],  # 它是怎么知道的
            capture_output=True,
            text=True,
            cwd=working_dir.parent,
            encoding="utf-8",
            errors="ignore",
        )
        return result


# iverilog
class IverilogSoftware(object):
    def __init__(self, platform="windows", distro_name="Ubuntu-24.04", timeout=0):
        """
        platform: windows wsl linux
        """
        self.name = "Iverilog"
        self.platform = platform
        self.distro_name = distro_name
        self.timeout = timeout

        self.default_compiled_file = "testbench.vvp"

        # TODO wsl下 检查代理并提醒你关闭,因为会导致乱码
        if self.platform == "wsl":
            proxy = os.environ.get("http_proxy") or os.environ.get("https_proxy")
            if proxy:
                print("检测到你开启了代理,这会导致wsl下的stdout/stderr乱码,请关闭代理")
                print(f"当前代理为: {proxy}")
                raise RuntimeError("请关闭代理后再试")

    def postprocess_cmd(self, cmd_list):
        """
        对命令进行后处理
        :param cmd_list: 命令列表
        :return: 处理后的命令列表
        """
        if self.timeout > 0:
            # TODO 忘记这里timeout会杀死timeout的程序吗
            cmd_list.insert(0, f"timeout {self.timeout}s")
        if self.platform == "wsl":
            cmd_list = ["wsl", "-d", self.distro_name, "bash", "-c"] + [" ".join(cmd_list)]

        return cmd_list

    def compile_dir(self, compile_dir):
        filelist = nlpertools.listdir(Path(compile_dir), including_dir=True)
        compiled_file_path = Path(compile_dir) / self.default_compiled_file
        cmd_list = ["iverilog", "-g2012", "-o", compiled_file_path.as_posix()] + [
            f.as_posix() for f in filelist if str(f).endswith(".v") or str(f).endswith(".sv")
        ]
        cmd_list = self.postprocess_cmd(cmd_list)
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        return result

    def compile(self, compile_dir):
        return self.compile_dir(compile_dir)

    def compile_file(self, filelist: list[str]):
        """
        使用iverilog编译verilog代码和testbench
        :param verilog_path: verilog代码文件路径
        :param testbench_path: testbench文件路径
        :return: 返回编译结果
        """

        cmd_list = ["iverilog", "-g2012", "-o", self.default_compiled_file] + [f.as_posix() for f in filelist]

        cmd_list = self.postprocess_cmd(cmd_list)
        # print(cmd_list)

        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        return result

    def sim_dir(self, sim_dir: str | Path):
        sim_dir = Path(sim_dir)
        compiled_file_path = Path(sim_dir) / self.default_compiled_file
        result = self.compile_dir(sim_dir.as_posix())
        cmd_list = ["vvp", compiled_file_path.as_posix()]
        cmd_list = self.postprocess_cmd(cmd_list)
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        print(result.stdout)
        return result

    def sim(self, sim_dir: str | Path):
        return self.sim_dir(sim_dir)

    def sim_files(self, filelist: list[str | Path]):
        """
        使用iverilog编译和运行testbench
        :param testbench_path: testbench文件路径
        :param verilog_path: verilog代码文件路径
        """

        result = self.compile_file(filelist)

        if result.returncode != 0:
            print(f"Error compiling: {result.stderr}")
            return result
        cmd_list = ["vvp", self.default_compiled_file]
        cmd_list = self.postprocess_cmd(cmd_list)
        print(cmd_list)
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        print(result.stdout)
        return result


def sim_by_modelsim_x(sim_dir):
    filelist = nlpertools.listdir(sim_dir)
    result = subprocess.run(["vlib", "work"])
    if result.returncode != 0:
        return False
    result = subprocess.run(["vlog"] + filelist)
    if result.returncode != 0:
        return False
    result = subprocess.run(["vsim", "-c", "tb_counter" "-do" '"run -all; exit"'])
    if result.returncode != 0:
        return False
    return True


def syntax_check_by_iverilog(path, timeout=5):
    # TODO 得设计成iverilog是在wsl还是windows还是哪里的
    # TODO timeout 可以吗 https://juejin.cn/post/7391703459803086848
    command = f"timeout {timeout}s iverilog {path}"
    result = subprocess.run(
        [command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )
    if result.returncode == 0:
        # print("Command executed successfully")
        return True, ""
    else:
        # 这里包含了124超时
        # print("stderr:", result.stderr)
        # print("Command failed with return code", result.returncode)
        return False, result.stderr


def syntax_check_by_iverilog_complex(path, with_error=False):
    # TODO 这里最好可以返回状态码,比如想通过timeout控制,如果是124代表超时
    # 指定要使用的 WSL 发行版
    distro_name = "Ubuntu-24.04"

    # 定义要在指定发行版中运行的命令
    # command = "iverilog  1.v"
    command = f"timeout 3s iverilog {path}"
    # print(command)
    try:
        # 使用 subprocess 在指定发行版中运行命令
        result = subprocess.run(
            ["wsl", "-d", distro_name, "bash", "-c", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        # 打印命令输出
        # print("stdout:", result.stdout)
        # print("stderr:", result.stderr)

        # 检查命令是否成功
        if result.returncode == 0:
            # print("Command executed successfully")
            if with_error:
                return True, ""
            else:
                return True
        else:
            # 这里包含了124超时
            # print("stderr:", result.stderr)
            # print("Command failed with return code", result.returncode)
            if with_error:
                return False, result.stderr
            else:
                return False
    except UnicodeDecodeError as e:
        print("Error decoding output:", e)
        sys.exit()


def syntax_check_by_verilator(path):
    distro_name = "Ubuntu-24.04"
    # 定义要在指定发行版中运行的命令
    # command = "iverilog  1.v"
    command = f"timeout 30s verilator --no-timing -Wall -cc {path}"
    # print(command)
    try:
        # 使用 subprocess 在指定发行版中运行命令
        result = subprocess.run(
            ["wsl", "-d", distro_name, "bash", "-c", command],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        # print(result.returncode)
        # if result.returncode == 1:
        #     print(result.stderr)
        log = result.stderr

    except:
        log = "none"
        # print()
    return log
