import os
import shutil
from pathlib import Path


def clean_project():
    base_path = Path(__file__).parent.absolute()

    # 需要保留的目录
    keep_dirs = {
        "ncod",
        "config",
        "tests",
        "keys",
        "frontend",
        "deploy",
        "docs",
        "migrations",
        "scripts",
        "setup",
        "src",
        "VirtualHere",
    }

    # 需要保留的文件
    keep_files = {
        ".env.*",  # 保留所有环境配置文件
        ".gitignore",
        "requirements*.txt",
        "pyproject.toml",
        "pytest.ini",
        "setup.*",
        "*.md",
        "*.json",
        "*.yaml",
        "*.yml",
        "*.ini",
        "*.cfg",
        "cleanup.py",  # 保留清理脚本本身
    }

    # 需要清理的目录模式
    clean_dirs = {
        ".vscode",
        ".vite",
        ".venv",
        ".ruff_cache",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        "__pycache__",
        "dist",
        "build",
        "coverage",
    }

    # 需要清理的文件模式
    clean_files = {"*.pyc", "*.pyo", "*.pyd", "*.log", "*.tmp", "*.bak"}

    print("开始清理项目...")

    # 清理根目录
    for item in base_path.iterdir():
        if item.is_dir():
            # 清理开发工具生成的目录
            if any(item.name.startswith(prefix) for prefix in clean_dirs):
                print(f"删除目录: {item}")
                shutil.rmtree(item, ignore_errors=True)
            # 删除不在保留列表中的目录
            elif item.name not in keep_dirs:
                print(f"删除目录: {item}")
                shutil.rmtree(item, ignore_errors=True)
        elif item.is_file():
            # 清理开发工具生成的文件
            if any(item.name.startswith(prefix) for prefix in clean_files):
                print(f"删除文件: {item}")
                item.unlink(missing_ok=True)
            # 删除不在保留列表中的文件
            elif not any(item.match(pattern) for pattern in keep_files):
                print(f"删除文件: {item}")
                item.unlink(missing_ok=True)

    # 递归清理子目录
    for root, dirs, files in os.walk(base_path):
        root_path = Path(root)

        # 清理开发工具生成的目录
        for dir_name in dirs[:]:
            if any(dir_name.startswith(prefix) for prefix in clean_dirs):
                dir_path = root_path / dir_name
                print(f"删除目录: {dir_path}")
                shutil.rmtree(dir_path, ignore_errors=True)
                dirs.remove(dir_name)

        # 清理开发工具生成的文件
        for file_name in files:
            if any(file_name.startswith(prefix) for prefix in clean_files):
                file_path = root_path / file_name
                print(f"删除文件: {file_path}")
                file_path.unlink(missing_ok=True)

    print("清理完成！")


if __name__ == "__main__":
    clean_project()
