from setuptools import setup, find_packages
import os

# Read README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ai-agent-base",
    version="0.1.0",
    author="AI Agent Base Contributors",
    author_email="contact@example.com",
    description="A highly extensible AI agent framework built with LangChain and vector embeddings",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/example/ai-agent-base",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "redis": [
            "redis>=4.5.0",
        ],
        "postgres": [
            "sqlalchemy>=2.0.0",
            "psycopg2-binary>=2.9.0",
        ],
        "mongodb": [
            "pymongo>=4.0.0",
        ],
        "pinecone": [
            "pinecone-client>=2.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "ai-agent=__main__:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
    },
    project_urls={
        "Bug Reports": "https://github.com/example/ai-agent-base/issues",
        "Source": "https://github.com/example/ai-agent-base",
        "Documentation": "https://ai-agent-base.readthedocs.io/",
    },
)