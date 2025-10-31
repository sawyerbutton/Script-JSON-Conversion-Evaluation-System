"""
Setup script for Script JSON Conversion Evaluation System
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README作为长描述
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取requirements.txt
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="script-json-eval",
    version="0.1.0",
    author="Development Team",
    author_email="your-email@example.com",
    description="剧本JSON转换质量评估系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/Script-JSON-Conversion-Evaluation-System",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
        ],
        "docs": [
            "sphinx>=7.0.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "script-eval=scripts.test_system:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["configs/*.yaml", "prompts/*.txt"],
    },
    zip_safe=False,
)
