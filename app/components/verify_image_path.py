# -*- coding: UTF-8 -*-
"""
该脚本主要用于添加资源文件中的图片路径校验,只需要文件名相同,则会认为为同一图片,
然后校验路径是否正确，不正确则修改路径，最后将修改后的文件保存到新的文件中

"""

import json
import os
import shutil

# 路径配置
image_dir = "../../assets/resource/yys_base/image"
pipeline_dir = "../../assets/resource/yys_base/pipeline"
backup_image_dir = "backup_image"
backup_pipeline_dir = "backup_pipeline"


# 第一步：备份原始文件
def backup_files(src_dir, backup_dir):
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)  # 如果已有备份，先删除
    shutil.copytree(src_dir, backup_dir)


# 第二步：读取 image 文件夹，生成文件名到相对路径的映射
def create_image_mapping(image_dir):
    image_map = {}  # {文件名: 相对路径}
    for root, _, files in os.walk(image_dir):
        for file in files:
            if file.endswith((".png", ".jpg", ".jpeg")):  # 根据需要添加更多扩展名
                relative_path = os.path.relpath(os.path.join(root, file), image_dir)
                image_map[file] = f"{relative_path.replace(os.sep, '/')}"  # 格式化路径为 JSON 格式
    return image_map


# 第三步：更新 JSON 文件并校验路径
def update_json_files(pipeline_dir, image_map):
    for root, _, files in os.walk(pipeline_dir):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 更新 'template' 字段并校验路径
                updated = update_and_validate_templates(data, image_map, json_path)

                # 如果有更新则覆盖保存
                if updated:
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)


# 递归更新和校验 JSON 中的 template 字段
def update_and_validate_templates(data, image_map, json_path, parent_keys=None):
    if parent_keys is None:
        parent_keys = []  # 用于记录字段的层级路径
    updated = False
    for key, value in data.items():
        current_path = parent_keys + [key]  # 当前字段的层级路径
        if isinstance(value, dict):
            updated |= update_and_validate_templates(value, image_map, json_path, current_path)
        elif key == "template":
            if isinstance(value, str):  # 单个模板路径
                new_value = validate_and_correct_path(value, image_map, json_path, current_path)
                if new_value != value:
                    data[key] = new_value
                    updated = True
            elif isinstance(value, list):  # 多个模板路径
                new_list = [
                    validate_and_correct_path(v, image_map, json_path, current_path + [str(i)])
                    for i, v in enumerate(value)
                ]
                if new_list != value:
                    data[key] = new_list
                    updated = True
    return updated


# 校验并修正路径
def validate_and_correct_path(template_path, image_map, json_path, field_path):
    file_name = os.path.basename(template_path)
    if file_name in image_map:
        correct_path = image_map[file_name]
        if template_path != correct_path:  # 路径不匹配时修正
            print(f"{' -> '.join(field_path)}")
            print(f"'{template_path}' -> 修正为: '{correct_path}'")
            return correct_path
    else:
        print(f"文件: {json_path}")
        print(f"{' -> '.join(field_path)}")
        print(f"'{file_name}' 不存在，保持原路径不变")
    return template_path  # 无需修正时返回原路径


# 主程序
if __name__ == "__main__":
    # 第一步：备份
    backup_files(image_dir, backup_image_dir)
    backup_files(pipeline_dir, backup_pipeline_dir)

    # 第二步：生成文件名到路径的映射
    image_mapping = create_image_mapping(image_dir)

    # 第三步：更新并校验 JSON 文件
    update_json_files(pipeline_dir, image_mapping)

    print("一切顺利 !!！")

