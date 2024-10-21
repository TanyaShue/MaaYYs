import PyInstaller.__main__
import os
import site
import shutil
import zipfile

# Get the current working directory
current_dir = os.getcwd()

# Get the site-packages directory list
site_packages_paths = site.getsitepackages()

# Search for the path that contains maa/bin
maa_bin_path = None
for path in site_packages_paths:
    potential_path = os.path.join(path, 'maa', 'bin')
    if os.path.exists(potential_path):
        maa_bin_path = potential_path
        break

if maa_bin_path is None:
    raise FileNotFoundError("The path containing maa/bin was not found")

# Build --add-data parameter
add_data_param = f'{maa_bin_path}{os.pathsep}maa/bin'

# Search for the path that contains MaaAgentBinary
maa_bin_path2 = None
for path in site_packages_paths:
    potential_path = os.path.join(path, 'MaaAgentBinary')
    if os.path.exists(potential_path):
        maa_bin_path2 = potential_path
        break

if maa_bin_path2 is None:
    raise FileNotFoundError("The path containing MaaAgentBinary was not found")

# Build --add-data parameter
add_data_param2 = f'{maa_bin_path2}{os.pathsep}MaaAgentBinary'

# Add custom_actions and custom_recognition folders
custom_actions_path = os.path.join(current_dir, './src/custom_actions')
custom_recognition_path = os.path.join(current_dir, './src/custom_recognition')

if not os.path.exists(custom_actions_path):
    raise FileNotFoundError("The custom_actions folder was not found")

if not os.path.exists(custom_recognition_path):
    raise FileNotFoundError("The custom_recognition folder was not found")

# Build --add-data parameters
add_data_custom_actions = f'{custom_actions_path}{os.pathsep}custom_actions'
add_data_custom_recognition = f'{custom_recognition_path}{os.pathsep}custom_recognition'

# Copy DLL files to the root of the Python environment
dll_dir = os.path.join(current_dir, 'DLL')
python_root = os.path.dirname(os.__file__)

if os.path.exists(dll_dir):
    for dll_file in os.listdir(dll_dir):
        source_path = os.path.join(dll_dir, dll_file)
        dest_path = os.path.join(python_root, dll_file)

        if os.path.isfile(source_path):
            if os.path.exists(dest_path):
                os.remove(dest_path)  # Remove the old file if it exists
            shutil.copy(source_path, dest_path)

# Run PyInstaller to package the task_service.py
PyInstaller.__main__.run([
    'src/task_service.py',
    '--onefile',
    '--name=MAA_YYS_BACKEND.exe',
    f'--add-data={add_data_param}',
    f'--add-data={add_data_param2}',
    f'--add-data={add_data_custom_actions}',
    f'--add-data={add_data_custom_recognition}',
    '--clean',
])

# Run PyInstaller to package the main.py
PyInstaller.__main__.run([
    'src/main.py',
    '--onefile',
    '--name=MAA_YYS.exe',
    '--clean',
])

# Copy assets folder to the dist directory
dist_dir = os.path.join(current_dir, 'dist')
assets_source_path = os.path.join(current_dir, 'assets')
assets_dest_path = os.path.join(dist_dir, 'assets')

if not os.path.exists(assets_source_path):
    raise FileNotFoundError("The assets folder was not found")

# If the destination path exists, remove it first
if os.path.exists(assets_dest_path):
    shutil.rmtree(assets_dest_path)

# Use shutil to copy the entire folder
shutil.copytree(assets_source_path, assets_dest_path)

# Compress the dist folder into a zip file and save it in the dist directory
zip_filename = 'MAA_YYS_RELEASE.zip'
zip_filepath = os.path.join(dist_dir, zip_filename)

with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            # Get the absolute and relative paths of the file
            file_path = os.path.join(root, file)
            # Skip the generated zip file
            if file == zip_filename:
                continue
            arcname = os.path.relpath(file_path, dist_dir)
            zipf.write(file_path, arcname)

# Delete all files and folders in the dist directory, except the zip file
for root, dirs, files in os.walk(dist_dir):
    for file in files:
        file_path = os.path.join(root, file)
        # Do not delete the generated zip file
        if file != zip_filename:
            os.remove(file_path)
    for dir in dirs:
        shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

print(f"Packaging and compression completed: {zip_filepath}")
