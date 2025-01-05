"""
从服务器包安装配置
"""

from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="ncod-slave",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="NCOD从服务器 - 设备管理和监控服务",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ncod",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "ncod-slave=ncod.slave.app:run",
        ],
    },
    include_package_data=True,
    package_data={
        "ncod.slave": [
            "README.md",
            "requirements.txt",
            "config/*.json",
            "tests/*",
        ],
    },
    zip_safe=False,
    test_suite="tests",
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-asyncio>=0.15.1",
            "pytest-cov>=2.12.1",
            "black>=21.7b0",
            "flake8>=3.9.2",
            "mypy>=0.910",
            "isort>=5.9.3",
        ],
        "docs": [
            "sphinx>=4.1.2",
            "sphinx-rtd-theme>=0.5.2",
            "sphinx-autodoc-typehints>=1.12.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/yourusername/ncod/issues",
        "Source": "https://github.com/yourusername/ncod",
        "Documentation": "https://ncod.readthedocs.io/",
    },
)
