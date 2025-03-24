import PyInstaller.__main__
import os
import site
import shutil
import zipfile
import sys
import argparse
import datetime
import json
import importlib.util

# Default version
VERSION = "1.0.0"


def find_path_in_site_packages(target_path):
    """Find a path in site-packages or create a fallback"""
    site_packages_paths = site.getsitepackages()
    print(f"Looking for {target_path} in {len(site_packages_paths)} site-packages paths")

    for path in site_packages_paths:
        potential_path = os.path.join(path, target_path)
        if os.path.exists(potential_path):
            print(f"Found {target_path} at: {potential_path}")
            return potential_path

    # Create fallback if not found
    fallback_path = os.path.join(os.getcwd(), f"{target_path.replace('/', '_')}_fallback")
    os.makedirs(fallback_path, exist_ok=True)
    print(f"Created fallback path at: {fallback_path}")
    return fallback_path


def extract_version():
    """Get version from git tag, version.txt, or use default"""
    # Try from GitHub Actions
    github_ref = os.environ.get('GITHUB_REF', '')
    if github_ref.startswith('refs/tags/v'):
        version = github_ref.replace('refs/tags/v', '')
        print(f"Using version from GitHub tag: {version}")
        return version

    # Try from git command
    try:
        import subprocess
        result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'],
                                capture_output=True, text=True)
        if result.returncode == 0:
            tag = result.stdout.strip()
            if tag.startswith('v'):
                version = tag[1:]
                print(f"Using version from git tag: {version}")
                return version
    except Exception:
        pass

    # Try from version.txt
    version_file = os.path.join(os.getcwd(), 'version.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r') as f:
            version = f.read().strip()
        print(f"Using version from version.txt: {version}")
        return version

    # Use default
    print(f"Using default version: {VERSION}")
    return VERSION


def update_devices_json(version, build_time):
    """Update version information in devices.json at top level, creating the file if it doesn't exist"""
    current_dir = os.getcwd()
    config_dir = os.path.join(current_dir, 'assets', 'config')
    devices_json_path = os.path.join(config_dir, 'devices.json')

    try:
        # Create directory structure if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            print(f"Created directory: {config_dir}")

        # Initialize config
        if os.path.exists(devices_json_path):
            print(f"Reading existing JSON at: {devices_json_path}")
            with open(devices_json_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            print(f"devices.json not found. Creating new file at: {devices_json_path}")
            config = {}  # Initialize empty config if file doesn't exist

        # Add version info at top level
        config["version"] = version
        config["build_time"] = build_time

        # Save updated config
        with open(devices_json_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(f"Successfully updated version info in devices.json")
        return True
    except Exception as e:
        print(f"Error updating devices.json: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Build script for MAA_YYS')
    parser.add_argument('--version', '-v', help='Version number to use')
    parser.add_argument('--keep-files', '-k', action='store_true',
                        help='Keep intermediate files in dist directory')
    args = parser.parse_args()

    # Setup build parameters
    current_dir = os.getcwd()
    dist_dir = os.path.join(current_dir, 'dist')
    build_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    version = args.version or extract_version()

    package_name = f"MAA_YYS_{version}"
    zip_filename = f"{package_name}_{build_time}.zip"
    zip_filepath = os.path.join(dist_dir, zip_filename)

    print(f"Starting build process for MAA_YYS version {version}")
    os.makedirs(dist_dir, exist_ok=True)

    # Update version in devices.json
    update_devices_json(version, build_time)

    # Find required paths
    maa_bin_path = find_path_in_site_packages('maa/bin')
    maa_agent_binary_path = find_path_in_site_packages('MaaAgentBinary')

    # Create logs directory in dist
    logs_dir = os.path.join(dist_dir, 'logs')
    logs_backup_dir = os.path.join(logs_dir, 'backup')
    os.makedirs(logs_dir, exist_ok=True)
    os.makedirs(logs_backup_dir, exist_ok=True)

    # Create an empty app.log file to include in the zip
    with open(os.path.join(logs_dir, 'app.log'), 'w', encoding='utf-8') as f:
        f.write(f"Log file created on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Run PyInstaller
    print("Starting PyInstaller...")
    pyinstaller_args = [
        'main.py',
        '--onefile',
        '--windowed',  # No console window will appear
        f'--name={package_name}',
        '--clean',
        '--uac-admin',
        f'--add-data={maa_bin_path}{os.pathsep}maa/bin',
        f'--add-data={maa_agent_binary_path}{os.pathsep}MaaAgentBinary'
    ]

    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print("PyInstaller completed successfully")
    except Exception as e:
        print(f"PyInstaller failed: {str(e)}")
        sys.exit(1)

    # Copy assets folder
    assets_source_path = os.path.join(current_dir, 'assets')
    assets_dest_path = os.path.join(dist_dir, 'assets')
    if os.path.exists(assets_source_path):
        print(f"Copying assets from {assets_source_path} to {assets_dest_path}")
        if os.path.exists(assets_dest_path):
            shutil.rmtree(assets_dest_path)
        shutil.copytree(assets_source_path, assets_dest_path)
    else:
        print(f"Warning: assets folder not found at {assets_source_path}")

    # Create zip package
    print(f"Creating zip file: {zip_filepath}")
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        files_added = 0
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                if file == os.path.basename(zip_filepath):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, dist_dir)
                zipf.write(file_path, arcname)
                files_added += 1
        print(f"Added {files_added} files to zip")

    # Clean up if needed
    if not args.keep_files:
        print("Cleaning up dist directory (keeping only the zip file)")
        for root, dirs, files in os.walk(dist_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if file == os.path.basename(zip_filepath) or file == "version.json":
                    continue
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {str(e)}")

            if root == dist_dir:
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    try:
                        shutil.rmtree(dir_path)
                    except Exception as e:
                        print(f"Error deleting directory {dir_path}: {str(e)}")

    print(f"Build process completed successfully. Output: {zip_filepath}")
    print(f"::set-output name=zip_file::{zip_filepath}")
    print(f"::set-output name=version::{version}")
    sys.exit(0)


if __name__ == "__main__":
    main()