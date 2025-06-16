"""Setup configuration for Arc-Verifier package."""

from setuptools import setup, find_packages
import os

# Read version from package
version = {}
with open(os.path.join("arc_verifier", "__version__.py")) as f:
    exec(f.read(), version)

# Read long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arc-verifier",
    version=version["__version__"],
    author="Arc-Verifier Contributors",
    author_email="",
    description="Verification and evaluation framework for autonomous agents across agentic protocols",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arc-computer/arc-verifier",
    packages=find_packages(exclude=["tests*", "internal_docs*", "temp_issues*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "docker>=6.0.0",
        "pydantic>=2.0.0",
        "httpx>=0.24.0",
        "aiofiles>=23.0.0",
        "python-dateutil>=2.8.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "mypy>=1.0.0",
            "ruff>=0.1.0",
            "build>=0.10.0",
            "twine>=4.0.0",
        ],
        "llm": [
            "anthropic>=0.18.0",
            "openai>=1.0.0",
        ],
        "web": [
            "flask>=2.3.0",
            "flask-cors>=4.0.0",
            "gunicorn>=21.2.0",
            "flask-compress>=1.14",
            "flask-caching>=2.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "arc-verifier=arc_verifier.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "arc_verifier": [
            "web/templates/*.html",
            "web/static/*.css",
            "web/static/*.js",
        ],
    },
)