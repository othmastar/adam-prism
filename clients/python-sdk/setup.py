"""Adam Prism Python SDK — setup.py"""

import os
import subprocess
from pathlib import Path

from setuptools import find_packages, setup

HERE = Path(__file__).parent


def get_version() -> str:
    """Get version from git tag (e.g. v1.0.0 → 1.0.0) or fallback."""
    try:
        tag = subprocess.check_output(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=HERE,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if tag.startswith("v"):
            return tag[1:]
        return tag
    except Exception:
        return "0.1.0"


def get_long_description() -> str:
    readme = HERE / "README.md"
    if readme.exists():
        return readme.read_text(encoding="utf-8")
    return ""


setup(
    name="adam-prism-client",
    version=get_version(),
    description="Python SDK for Adam Prism API — التوأم الرقمي الشخصي",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Mohamed Othman",
    author_email="",
    url="https://github.com/anomalyco/Adam_Prism_Complete_v2",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "httpx>=0.27.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.23",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    license="Apache 2.0",
    keywords="adam prism ai chatbot sdk arabic",
    project_urls={
        "Source": "https://github.com/anomalyco/Adam_Prism_Complete_v2",
        "Bug Tracker": "https://github.com/anomalyco/Adam_Prism_Complete_v2/issues",
    },
)
