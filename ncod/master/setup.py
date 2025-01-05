"""Setup模块"""

from setuptools import find_packages, setup

setup(
    name="ncod",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "pydantic",
        "python-multipart",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-dotenv",
    ],
)
