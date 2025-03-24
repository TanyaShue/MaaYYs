import PyInstaller.__main__
import os
import site
import shutil
import zipfile

# 获取当前工作目录
current_dir = os.getcwd()

# 获取 site-packages 目录列表
site_packages_paths = site.getsitepackages()

# 查找包含 maa/bin 的路径
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, 'maa', 'bin')
    if os.path.exists(potential_path):
        maa_bin_path = potential_path
        break

if maa_bin_path is None:
    raise FileNotFoundError("Path containing maa/bin not found")

# 构建 --add-data 参数
add_data_param = f'{maa_bin_path}{os.pathsep}maa/bin'

# 查找包含 MaaAgentBinary 的路径
maa_bin_path2 = None
for path in site_packages_paths:
    potential_path = os.path.join(path, 'MaaAgentBinary')
    if os.path.exists(potential_path):
        maa_bin_path2 = potential_path
        break

if maa_bin_path2 is None:
    raise FileNotFoundError("Path containing MaaAgentBinary not found")

# 构建 --add-data 参数
add_data_param2 = f'{maa_bin_path2}{os.pathsep}MaaAgentBinary'


PyInstaller.__main__.run([
    'main.py',
    '--onefile',
    '--name=MAA_YYS.exe',
    f'--add-data={add_data_param}',
    f'--add-data={add_data_param2}',
    '--clean',
])

# 复制 assets 文件夹到 dist 目录
dist_dir = os.path.join(current_dir, 'dist')
assets_source_path = os.path.join(current_dir, 'assets')
assets_dest_path = os.path.join(dist_dir, 'assets')
syc_bat_source_path = os.path.join(current_dir, 'syc.bat')
syc_bat_dest_path = os.path.join(dist_dir, 'syc.bat')

if not os.path.exists(assets_source_path):
    raise FileNotFoundError("assets folder not found")

# 如果目标路径存在，先删除它
if os.path.exists(assets_dest_path):
    shutil.rmtree(assets_dest_path)

# 使用 shutil 复制整个文件夹
shutil.copytree(assets_source_path, assets_dest_path)
# 复制 syc.bat 文件
if os.path.exists(syc_bat_source_path):
    shutil.copy(syc_bat_source_path, syc_bat_dest_path)
else:
    raise FileNotFoundError("syc.bat file not found")

# 压缩 dist 文件夹为 zip 文件，并保存在 dist 目录中
zip_filename = 'MAA_YYS_RELEASE.zip'
zip_filepath = os.path.join(dist_dir, zip_filename)

with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            # 获取文件的绝对路径并相对路径
            file_path = os.path.join(root, file)
            # 跳过刚生成的压缩包
            if file == zip_filename:
                continue
            arcname = os.path.relpath(file_path, dist_dir)
            zipf.write(file_path, arcname)

# 删除 dist 文件夹中的所有文件和文件夹，保留压缩包
for root, dirs, files in os.walk(dist_dir):
    for file in files:
        file_path = os.path.join(root, file)
        # 不删除生成的压缩包
        if file != zip_filename:
            os.remove(file_path)
    for dir in dirs:
        shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

print(f"Packaging and compression completed: {zip_filepath}")
