from setuptools import setup, find_packages

setup(
    name="coderecon",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "mcp",
        "fastmcp",
        "click",
        "ollama"
    ],
    entry_points={
        "console_scripts": [
            "coderecon=cli:main",
        ],
    },
)