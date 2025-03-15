#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

"""Hooks for Progress Table.

This hook modifies the README.md file to use
direct GitHub URLs for images and links. This
is useful for PyPI. Otherwise the README.md
file would be rendered without the images.
"""

from pathlib import Path

from hatchling.metadata.plugin.interface import MetadataHookInterface


def with_direct_github_urls(text):
    images_github_link = "https://raw.githubusercontent.com/sjmikler/progress-table/main/images"
    text = text.replace("(images", "(" + images_github_link)

    docs_github_link = "https://github.com/sjmikler/progress-table/blob/main/docs/"
    return text.replace("(docs", "(" + docs_github_link)


class ReadmeHook(MetadataHookInterface):
    def update(self, metadata: dict):
        readme_path = Path("README.md")
        original_text = readme_path.read_text(encoding="utf-8")
        updated_text = with_direct_github_urls(original_text)
        with open("README_pypi.md", "w", encoding="utf-8") as f:
            f.write(updated_text)

        # Tell Hatch to use this modified README
        print("Generated README for Pypi!")
