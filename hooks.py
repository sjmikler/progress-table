#  Copyright (c) 2022-2025 Szymon Mikler

"""
This hook modifies the README.md file to use
direct GitHub URLs for images and links. This
is useful for PyPI. Otherwise the README.md
file would be rendered without the images.
"""

import tempfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


def with_direct_github_urls(text):
    images_github_link = "https://raw.githubusercontent.com/sjmikler/progress-table/main/images"
    text = text.replace("(images", "(" + images_github_link)

    docs_github_link = "https://github.com/sjmikler/progress-table/blob/main/docs/"
    text = text.replace("(docs", "(" + docs_github_link)

    return text


class CustomBuildHook(BuildHookInterface):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self.temp_path = None

    def initialize(self, version, build_data):
        readme_path = Path("README.md")
        original_text = readme_path.read_text(encoding="utf-8")
        updated_text = with_direct_github_urls(original_text)

        with tempfile.NamedTemporaryFile("w", delete=False) as file:
            file.write(updated_text)

        # Tell Hatch to use this modified README
        build_data["readme"] = file.name

    def finalize(self, version, build_data, artifact_path):
        p = Path(build_data["readme"])
        if p.exists():
            p.unlink()
