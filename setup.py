# coding: utf-8
import czsc
from os import path
from setuptools import setup, find_packages

setup(
    name="czsc_enhanced",
    version="0.1.0",
    author="moses2204",
    description="Enhanced CZSC package with additional features",
    packages=find_packages(),
    install_requires=[
        "czsc>=0.9.68",
        "rs_czsc>=0.1.7",
        "numpy",
        "pandas",
        "matplotlib",
        "tqdm",
        "scikit-learn",
    ],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
