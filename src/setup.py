# coding=utf-8

from setuptools import setup

setup(
  name='orbit_framework',
  version='0.1.0',
  description='Ein Python-Framework für robuste TinkerForge-Anwendungen',
  author='Tobias Kiertscher',
  author_email='dev@mastersign.de',
  url='http://mastersign.github.io/orbit/',
  download_url='https://github.com/mastersign/orbit/releases/download/v0.1.0-alpha/orbit_framework.egg',
  packages=[
    'orbit_framework', 
    'orbit_framework.components',
    'orbit_framework.jobs',
    ],
  provides='orbit_framework',
  requires=[
    'tinkerforge (>=2.1.0)'
    ],
  long_description="""\
ORBIT ermöglicht die Entwicklung von dialogbasierten Systemen \
durch ein einfaches Konzept von Apps und Services. \
Es unterstützt eine robuste Anwendungsarchitektur durch wiederverwendbare \
Komponenten und die Entkopplung von Anwendungsteilen mit Hilfe eines \
Nachrichtensystem. Die Verwaltung der Verbindung zu TinkerForge-Bricks \
und -Bricklets übernimmt ein Gerätemanager, dadurch wird das Entwickeln \
von Anwendungen, die mit Verbindungsabbrüchen umgehen müssen, stark vereinfacht. \
""",
  classifiers=[
    "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "Programming Language :: Python",
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Natural Language :: German",
    "Topic :: Home Automation",
    "Topic :: Games/Entertainment",
    ],
  keywords='TinkerForge framework',
  license='LGPL-3.0',
  install_requires=[
    'setuptools',
    ],
)