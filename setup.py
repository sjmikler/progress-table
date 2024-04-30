#  Copyright (c) 2022-2024 Szymon Mikler

from pathlib import Path

from setuptools import find_packages, setup


def package_relative_path(path):
    return Path(__file__).parent / path


def get_version():
    text = package_relative_path("progress_table/__init__.py").read_text(encoding="UTF-8")
    for line in text.split("\n"):
        if line.startswith("__version__"):
            delim = '"' if '"' in line else "'"
            return line.split(delim)[1]
    else:
        raise RuntimeError("Unable to find version string.")


long_description = package_relative_path("README.md").read_text(encoding="UTF-8")


def with_direct_github_urls(description):
    images_github_link = "https://raw.githubusercontent.com/sjmikler/progress-table/main/images"
    description = description.replace("(images", "(" + images_github_link)

    docs_github_link = "https://github.com/sjmikler/progress-table/blob/main/docs/"
    description = description.replace("(docs", "(" + docs_github_link)
    return description


setup(
    name="progress-table",
    version=get_version(),
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
    long_description=with_direct_github_urls(long_description),
    long_description_content_type="text/markdown",
)
