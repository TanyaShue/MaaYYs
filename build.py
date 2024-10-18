import PyInstaller.__main__
import os
import site

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
    raise FileNotFoundError("未找到包含 maa/bin 的路径")

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
    raise FileNotFoundError("未找到包含 MaaAgentBinary 的路径")

# 构建 --add-data 参数
add_data_param2 = f'{maa_bin_path2}{os.pathsep}MaaAgentBinary'


# # 运行 PyInstaller
PyInstaller.__main__.run([
    'src/task_service.py',
    '--onefile',
    '--name=MAA_YYS_BACKEND',
    f'--add-data={add_data_param}',
    f'--add-data={add_data_param2}',
    '--clean',
])
# PyInstaller.__main__.run([
#     'src/main.py',
#     '--name=MAA_YYS'
# ])
# PyInstaller.__main__.run([
#     'test/abc.py',
#     '--clean',
#     '--onefile',
#     '--name=MAA_YYS_TEST'
# ])