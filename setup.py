#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup

setup(
    name="url-normalize",
    version="1.3.3",
    author="Nikolay Panov",
    author_email="github@niksite.ru",
    description="URL normalization for Python",
    long_description=open("README.md").read(),
    license="Python",
    url="https://github.com/niksite/url-normalize",
    packages=['url_normalize'],
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Text Processing :: Indexing",
        "Topic :: Utilities",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3"
    ],
    install_requires=['future'],
)
