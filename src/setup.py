# coding=utf-8

from setuptools import setup, find_packages
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
  name='orbit_framework',
  version='0.1.0',
  description='Ein Python-Framework für robuste TinkerForge-Anwendungen',
  author='Tobias Kiertscher',
  author_email='dev@mastersign.de',
  url='http://mastersign.github.io/orbit/',
  packages=find_packages(),
  long_description=long_description,
  classifiers=[
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    #"Development Status :: 3 - Alpha",
    #"Development Status :: 4 - Beta",
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "Natural Language :: German",
    "Topic :: Home Automation",
    "Topic :: Games/Entertainment",
    ],
  keywords='TinkerForge framework',
  license='LGPL-3.0',
  install_requires=[
    'tinkerforge >= 2.1.0',
    ],
)
