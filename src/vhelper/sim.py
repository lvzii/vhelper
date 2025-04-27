import subprocess
import nlpertools
import sys


def sim_by_modelsim_x():
    result = subprocess.run(["vlib", "work"])
    if result.returncode != 0:
        return False
    result = subprocess.run(["vlog", "example.sv", "example_tb.sv"])
    if result.returncode != 0:
        return False
    result = subprocess.run(["vsim", "-c", "tb_counter" "-do" '"run -all; exit"'])
    if result.returncode != 0:
        return False
    return True


def syntax_check_by_iverilog(path, timeout=5):
    # TODO 得设计成iverilog是在wsl还是windows还是哪里的
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
