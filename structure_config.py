import os
import json

# 清理 json 文件，如果 new 和 temp 里的 json 文件在 origin 里不存在，则删除
def clean_json_file():
    origin_json_file_list = os.listdir("configs/structures/origin")
    new_json_file_list = os.listdir("configs/structures/new")
    temp_json_file_list = os.listdir("configs/structures/temp")
    for origin_json_file in origin_json_file_list:
        if origin_json_file not in new_json_file_list:
            os.remove(origin_json_file)
            print(f"删除 {origin_json_file} 文件")
        else:
            if origin_json_file not in temp_json_file_list:
                os.remove(origin_json_file)
                print(f"删除 {origin_json_file} 文件")
            else:
                print(f"{origin_json_file} 文件未改动")

# 检查结构化配置文件
# 1. 检查 origin 里的 json 文件是否和 temp 里的 json 文件一致
# 1.1 如果一致，说明该配置文件没有改动，直接返回
# 1.2 如果不一致，说明该配置文件有改动，需要使用 llm 重新生成专业版本，即 new 里的 json 文件
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
