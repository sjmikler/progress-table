#  Copyright (c) 2022 Szymon Mikler

from pathlib import Path

from setuptools import setup, find_packages

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="UTF-8")

setup(
    name="progress-table",
    version="1.2.3",
    url="https://github.com/gahaalt/progress-table.git",
    author="Szymon Mikler",
    author_email="sjmikler@gmail.com",
    license="MIT",
    description="Display progress as a pretty table in the command line.",
    packages=find_packages(),
    python_requires=">=3.7",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    install_requires=["colorama"],
    long_description=long_description,
    long_description_content_type="text/markdown",
)
