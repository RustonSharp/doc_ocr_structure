import os
import json
import shutil
from llm import LLMService

# 清理 json 文件
# 以 origin 目录下的文件为准，对于 new 和 temp 目录下的文件，如果不在 origin 目录下存在，则删除
def clean_json_file():
    origin_json_file_list = os.listdir("configs/structures/origin")
    new_json_file_list = os.listdir("configs/structures/new")
    temp_json_file_list = os.listdir("configs/structures/temp")
    for new_json_file in new_json_file_list:
        if new_json_file not in origin_json_file_list:
            os.remove(f"configs/structures/new/{new_json_file}")
            print(f"删除 {new_json_file} 文件")
        else:
            if new_json_file not in temp_json_file_list:
                os.remove(f"configs/structures/new/{new_json_file}")
                print(f"删除 {new_json_file} 文件")
            else:
                print(f"{new_json_file} 文件未改动")
    for temp_json_file in temp_json_file_list:
        if temp_json_file not in origin_json_file_list:
            os.remove(f"configs/structures/temp/{temp_json_file}")
            print(f"删除 {temp_json_file} 文件")
        else:
            print(f"{temp_json_file} 文件未改动")

# 检查结构化配置文件
# 1. 检查 origin 里的 json 文件是否和 temp 里的 json 文件一致
# 1.1 如果一致，说明该配置文件没有改动，直接返回
# 1.2 如果不一致，说明该配置文件有改动，记录下存在不同的文件名
# 1.3 返回存在不同的文件名列表

def check_structure_config()->list[str]:
    origin_json_file_name_list = os.listdir("configs/structures/origin")
    temp_json_file_name_list = os.listdir("configs/structures/temp")

    updated_json_file_name_list = []

    for origin_json_file_name in origin_json_file_name_list:
        if origin_json_file_name not in temp_json_file_name_list:
            updated_json_file_name_list.append(origin_json_file_name)
        else:
            origin_json_file = open(f"configs/structures/origin/{origin_json_file_name}", "r", encoding="utf-8")
            origin_json_file_content = json.load(origin_json_file)
            origin_json_file.close()
            temp_json_file = open(f"configs/structures/temp/{origin_json_file_name}", "r", encoding="utf-8")
            temp_json_file_content = json.load(temp_json_file)
            temp_json_file.close()
            if origin_json_file_content != temp_json_file_content:
                updated_json_file_name_list.append(origin_json_file_name)
    return updated_json_file_name_list

# 1. 输入参数为 需要更新的文件名列表
# 2. 遍历需要更新的文件名列表，将 origin 里的 json 文件使用 llm 重新生成专业版本，保存到 new 里，名称与 origin 里的文件名一致，如果 new 里不存在该文件，则创建，如果存在该文件，则覆盖
# 3. 将 origin 里的 json 文件复制到 temp 里，名称与 origin 里的文件名一致，如果 temp 里不存在该文件，则创建，如果存在该文件，则覆盖

def update_structure_config(updated_json_file_name_list: list[str]):
    llm_service = LLMService()
    for updated_json_file_name in updated_json_file_name_list:
        origin_json_file = open(f"configs/structures/origin/{updated_json_file_name}", "r", encoding="utf-8")
        origin_json_file_content = json.load(origin_json_file)
        origin_json_file.close()
        professional_json_content = llm_service.format_json_into_professional(json.dumps(origin_json_file_content, ensure_ascii=False, indent=4))
        new_json_file = open(f"configs/structures/new/{updated_json_file_name}", "w", encoding="utf-8")
        new_json_file.write(json.dumps(professional_json_content, ensure_ascii=False, indent=4))
        new_json_file.close()
        shutil.copy(f"configs/structures/origin/{updated_json_file_name}", f"configs/structures/temp/{updated_json_file_name}")