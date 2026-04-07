from setuptools import setup, find_packages

setup(
    name="activewiki",
    version="0.1.0",
    description="The wiki that thinks, acts, and learns. A closed-loop knowledge framework.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Strategy Arena Team",
    author_email="contact@strategyarena.io",
    url="https://github.com/EzailHQ/activewiki",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[],
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
