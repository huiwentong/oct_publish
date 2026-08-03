# -*- coding: utf-8 -*-
import os

name = 'oct_publish'

version = '0.1.0'

authors = [
    'huiwentong',
]

description = 'New Publish Pipeline Tool - Next Generation Publisher'

build_command = False

# tools = [
#     'newpublish'
# ]

requires = [
    'QtPy',
    'PyYAML',
    'requests',
    'shotgun_api3',
    'oct',
    'psycopg2_binary',
    'requests',
]

def commands():
    env.PATH.append('{root}/bin')
    env.PYTHONPATH.append('{root}')
    env.PYTHONPATH.append('{root}/publish_core')
    env.PYTHONPATH.append('{root}/publish_components')
    env.PYTHONPATH.append('{root}/publish_gui')

uuid = 'newpublish'
