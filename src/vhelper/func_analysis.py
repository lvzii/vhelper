import os
from pathlib import Path
import re
import nlpertools
import itertools
import sys


def remove_comments(file_content):
    """
    去除 Verilog 代码中的注释
    :param file_content: Verilog 代码内容
    :return: 去除注释后的代码内容
    """
    # 去除单行注释
    file_content = re.sub(r"//.*", "", file_content)
    # 去除多行注释
    file_content = re.sub(r"/\*.*?\*/", "", file_content, flags=re.DOTALL)
    return file_content


def get_sub_modules(file_content):
    """
    从 Verilog 代码内容中提取子模块名称
    :param file_content: Verilog 代码内容
    :return: 子模块名称列表
    """

    file_content = remove_comments(file_content)
    sub_modules = []
    # 正则表达式用于匹配 Verilog 模块实例化
    verilog_module_pattern = r"(\w+)\s+(\w+)\s*\([\s\S]*?\)\s*;(?![^()]*\))"
    # \w+ 匹配一个或多个字母、数字或下划线字符，用于匹配模块名称。
    # \s+ 匹配一个或多个空白字符，用于匹配模块实例化中的空格。
    # \([\s\S]*? 匹配括号内的内容，[\s\S] 匹配任意字符，包括空格和换行符，*? 表示非贪婪匹配。
    verilog_module_pattern = r"(\w+)\s+([\w#]+)\s*\([\s\S]*?"
    #   i2c_master_byte_ctrl byte_controller (
    matches = re.findall(verilog_module_pattern, file_content)
    # print(f"匹配到的内容: {matches}")
    for match in matches:
        module_name = match[0]
        if module_name not in {"begin", "module", "else", "STOD_COND", "PRINTF_COND", "delay", "pullup"}:
            sub_modules.append(module_name)
    return sub_modules


def analyze_module(
    module_name,
    folder_path,
    depth,
    hierarchy,
    visited_modules,
    call_chains,
    current_chain,
):
    """
    递归分析模块及其子模块的调用关系
    :param module_name: 当前模块名称
    :param folder_path: 模块所在文件夹路径
    :param depth: 当前模块的深度
    :param result_lines: 用于存储结果的列表
    :param visited_modules: 已访问过的模块集合
    :param call_chains: 用于存储所有模块调用链路的列表
    :param current_chain: 当前的模块调用链路
    """
    # TODO 是否只有顶层模块可以文件名与模块不同名
    if depth == 1:
        file_path = Path(folder_path, f"{module_name}.v")
        if not file_path.exists() and "." not in module_name:
            print(f"顶层模块名与文件名不统一，请输入<顶层模块所在文件名>.<顶层模块名>, 如testbench.tst_bench_top")

            sys.exit()
        if "." in module_name:
            file_path = Path(folder_path, f"{module_name.split(".")[0]}.v")
    else:
        file_path = os.path.join(folder_path, f"{module_name}.v")
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return
    new_chain = current_chain + [module_name]
    content = nlpertools.readtxt_string(file_path)
    sub_modules = get_sub_modules(content)
    print(f"模块 {module_name} 的子模块: {sub_modules}")
    if sub_modules:
        for sub_module in sub_modules:
            if sub_module not in visited_modules:
                visited_modules.add(sub_module)
                indent = "---|" * depth
                line = f"[{depth}]  *{indent}{sub_module}"
                # print(line)
                hierarchy.append(line)
                analyze_module(
                    sub_module,
                    folder_path,
                    depth + 1,
                    hierarchy,
                    visited_modules,
                    call_chains,
                    new_chain,
                )
    call_chains.append(new_chain)


def get_call_chains(folder_path, top_modules):
    """
    获取输入模块的调用链路
    :param folder_path: 模块所在文件夹路径
    :param top_modules: 输入的多个顶层模块列表
    :return: 每个模块的调用链路列表
    """
    all_call_chains = []
    for top_module in top_modules:
        hierarchy, call_chains, visited_modules, current_chain, depth = [], [], set(), [], 1
        hierarchy.append(top_module)
        visited_modules.add(top_module)
        analyze_module(top_module, folder_path, depth, hierarchy, visited_modules, call_chains, current_chain)
        all_call_chains.extend(call_chains)
    return all_call_chains


def find_source_error_from_chains(chains, candidate_modules):
    """
    我需要知道candidate_modules中的模块，谁是最根源的，导致了其他模块的错误
    :param chains: 中包含了所有的链路调用关系
    :param candidate_modules: 中包含了所有可能存在错误的模块
    :return: 返回错误根源的模块
    """
    # 先把所有的chains中的模块，放到一个字典中，它的值是他所有的祖先
    module_dict = {}
    for chain in chains:
        for i in range(len(chain)):
            # 获取当前模块的所有祖先模块
            ancestors = chain[:i]
            if chain[i] not in module_dict:
                module_dict[chain[i]] = set()  # 使用集合来存储祖先模块
            module_dict[chain[i]].update(ancestors)  # 更新集合中的祖先模块
    # 将集合转换为列表，方便后续处理和打印
    for k in module_dict:
        module_dict[k] = list(module_dict[k])

    # 拿到所有的候选模块的祖先模块
    candidate_ancestors = list(itertools.chain(*module_dict.values()))
    print(candidate_ancestors)
    for i in candidate_modules:
        if i not in candidate_ancestors:
            return i
    return None


...

if __name__ == "__main__":
    # folder_path = r".\ethmac2"
    # top_modules = ["tb_ethernet"]
    # candidate_modules = ["tb_ethernet", "ethmac", "eth_txethmac", "eth_rxaddrcheck"]  # 这里是所有tb结果不一致的模块
    # folder_path = r".\modules2"
    # top_modules = ["tst_bench_top_t1"]
    # candidate_modules = ["tst_bench_top_t1", "i2c_master_top", "i2c_master_byte_ctrl", "i2c_master_bit_ctrl"]
    folder_path = r".\pit_latest"
    top_modules = ["testbench.tst_bench_top"]
    candidate_modules = []
    error_chains = get_call_chains(folder_path, top_modules)
    print("模块调用链路：")
    for cdx, chain in enumerate(error_chains):
        print(cdx, " -> ".join(chain))
    error_module = find_source_error_from_chains(error_chains, candidate_modules)
    print(f"错误根源的模块是：{error_module}")
