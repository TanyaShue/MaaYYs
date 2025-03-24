import PyInstaller.__main__
import os
import site
import shutil
import zipfile
import sys


# Log function for better debugging
def log(message):
    print(f"[BUILD] {message}")


try:
    # 获取当前工作目录
    current_dir = os.getcwd()
    log(f"Current directory: {current_dir}")

    # 获取 site-packages 目录列表
    site_packages_paths = site.getsitepackages()
    log(f"Found {len(site_packages_paths)} site-packages paths")

    # 查找包含 maa/bin 的路径
    maa_bin_path = None
    for path in site_packages_paths:
        potential_path = os.path.join(path, 'maa', 'bin')
        if os.path.exists(potential_path):
            maa_bin_path = potential_path
            log(f"Found maa/bin at: {maa_bin_path}")
            break

    if maa_bin_path is None:
        # 如果没找到，尝试手动创建路径
        log("Path containing maa/bin not found. Creating fallback directory...")
        fallback_path = os.path.join(current_dir, 'maa_bin_fallback')
        os.makedirs(fallback_path, exist_ok=True)
        maa_bin_path = fallback_path
        log(f"Created fallback path at: {maa_bin_path}")

    # 构建 --add-data 参数
    add_data_param = f'{maa_bin_path}{os.pathsep}maa/bin'
    log(f"First add-data parameter: {add_data_param}")

    # 查找包含 MaaAgentBinary 的路径
    maa_bin_path2 = None
    for path in site_packages_paths:
        potential_path = os.path.join(path, 'MaaAgentBinary')
        if os.path.exists(potential_path):
            maa_bin_path2 = potential_path
            log(f"Found MaaAgentBinary at: {maa_bin_path2}")
            break

    if maa_bin_path2 is None:
        # 如果没找到，尝试手动创建路径
        log("Path containing MaaAgentBinary not found. Creating fallback directory...")
        fallback_path = os.path.join(current_dir, 'maa_agent_binary_fallback')
        os.makedirs(fallback_path, exist_ok=True)
        maa_bin_path2 = fallback_path
        log(f"Created fallback path at: {maa_bin_path2}")

    # 构建 --add-data 参数
    add_data_param2 = f'{maa_bin_path2}{os.pathsep}MaaAgentBinary'
    log(f"Second add-data parameter: {add_data_param2}")

    # 运行 PyInstaller
    log("Starting PyInstaller...")
    PyInstaller.__main__.run([
        'main.py',
        '--onefile',
        '--name=MAA_YYS.exe',
        f'--add-data={add_data_param}',
        f'--add-data={add_data_param2}',
        '--clean',
    ])
    log("PyInstaller completed")

    # 复制 assets 文件夹到 dist 目录
    dist_dir = os.path.join(current_dir, 'dist')
    assets_source_path = os.path.join(current_dir, 'assets')
    assets_dest_path = os.path.join(dist_dir, 'assets')

    # 检查 dist 目录是否存在，如果不存在则创建
    if not os.path.exists(dist_dir):
        log(f"Creating dist directory: {dist_dir}")
        os.makedirs(dist_dir, exist_ok=True)

    # 检查 assets 目录
    if os.path.exists(assets_source_path):
        log(f"Copying assets from {assets_source_path} to {assets_dest_path}")
        # 如果目标路径存在，先删除它
        if os.path.exists(assets_dest_path):
            log(f"Removing existing assets directory: {assets_dest_path}")
            shutil.rmtree(assets_dest_path)

        # 使用 shutil 复制整个文件夹
        shutil.copytree(assets_source_path, assets_dest_path)
        log("Assets copied successfully")
    else:
        log(f"Warning: assets folder not found at {assets_source_path}")

    # 检查 syc.bat 文件
    syc_bat_source_path = os.path.join(current_dir, 'syc.bat')
    syc_bat_dest_path = os.path.join(dist_dir, 'syc.bat')
    if os.path.exists(syc_bat_source_path):
        log(f"Copying syc.bat from {syc_bat_source_path} to {syc_bat_dest_path}")
        shutil.copy2(syc_bat_source_path, syc_bat_dest_path)
        log("syc.bat copied successfully")
    else:
        log(f"Warning: syc.bat not found at {syc_bat_source_path}")

    # 检查 dist 目录中的文件
    log("Files in dist directory before zipping:")
    for item in os.listdir(dist_dir):
        log(f" - {item}")

    # 压缩 dist 文件夹为 zip 文件，并保存在 dist 目录中
    zip_filename = 'MAA_YYS_RELEASE.zip'
    zip_filepath = os.path.join(dist_dir, zip_filename)
    log(f"Creating zip file: {zip_filepath}")

    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_added = 0
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                # 获取文件的绝对路径并相对路径
                file_path = os.path.join(root, file)
                # 跳过刚生成的压缩包
                if file == zip_filename:
                    continue
                arcname = os.path.relpath(file_path, dist_dir)
                log(f"Adding to zip: {arcname}")
                zipf.write(file_path, arcname)
                files_added += 1

        log(f"Added {files_added} files to zip")

    # 验证 zip 文件是否已创建
    if os.path.exists(zip_filepath):
        log(f"Zip file created successfully: {zip_filepath}")
        log(f"Zip file size: {os.path.getsize(zip_filepath)} bytes")
    else:
        log(f"Error: Zip file was not created at {zip_filepath}")
        sys.exit(1)  # 如果 zip 未创建，退出并报错

    # 删除 dist 文件夹中的所有文件和文件夹，保留压缩包
    log("Cleaning up dist directory (keeping only the zip file)")
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # 不删除生成的压缩包
            if file != zip_filename:
                log(f"Removing file: {file_path}")
                os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            log(f"Removing directory: {dir_path}")
            shutil.rmtree(dir_path, ignore_errors=True)

    # 最终确认
    log("Final contents of dist directory:")
    for item in os.listdir(dist_dir):
        log(f" - {item}")

    log(f"Packaging and compression completed: {zip_filepath}")

except Exception as e:
    log(f"Error during build process: {str(e)}")
    import traceback

    log(traceback.format_exc())
    sys.exit(1)  # 如果有任何错误，退出并报错