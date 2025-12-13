from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="web-analyzer-cli",
    version="1.0.0",
    author="Irving Ruas",
    author_email="irving@ruas.dev.br",
    description="CLI tool para análise de performance de websites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/N1ghthill/web-analyzer-cli",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests>=2.25.1",
        "beautifulsoup4>=4.9.3",
    ],
    entry_points={
        "console_scripts": [
            "web-analyzer=src.main:main",
        ],
    },
)
