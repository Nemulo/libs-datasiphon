from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="datasiphon",  # Required
    version="0.3.11",  # Required
    description="Dynamic building of filtered database queries",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Nemulo/libs-datasiphon",
    author="Marek Nemeth",
    author_email="99m.nemeth@gmail.com",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Typing :: Typed",
    ],
    keywords=["database", "sql", "filtering", "query"],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10, <4",
    install_requires=["sqlalchemy>=2.0.0", "qstion>=1.1.2"],  # Optional
    project_urls={  # Optional
        "Documentation": "https://github.com/Nemulo/libs-datasiphon/blob/main/README.md",
        "Bug Reports": "https://github.com/Nemulo/libs-datasiphon/issues",
        "Source": "https://github.com/Nemulo/libs-datasiphon",
    },
)
