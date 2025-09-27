#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Navie 项目安装配置
"""

from setuptools import setup, find_packages
import os

# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Navie - GitHub自动注册系统"

# 读取依赖
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), 'requirements', 'base.txt')
    if os.path.exists(req_path):
        with open(req_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    name="navie",
    version="1.0.0",
    author="Navie Team",
    author_email="team@navie.com",
    description="GitHub自动注册系统",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/navie/navie",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "navie-web=navie.web.email_web_manager:main",
            "navie-cli=navie.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
