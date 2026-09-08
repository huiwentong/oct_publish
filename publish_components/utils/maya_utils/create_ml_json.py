# -*- coding: utf-8 -*-

import json
from datetime import datetime


def convert_path(orig):
    orig = orig.replace('\\', '/').rstrip('/')
    if orig.startswith('I:/') or orig.startswith('i:/'):
        new_path = '/ifs/projects/publish/' + orig[3:]
    if orig.startswith('W:/') or orig.startswith('w:/'):
        new_path = '/ifs/projects/' + orig[3:]
    if orig.startswith('R:/') or orig.startswith('r:/'):
        new_path = '/mnt/render/' + orig[3:]
    else:
        new_path = orig

    return new_path


def move_link_dirs(key='', l_move_dirs = [], l_link_dirs = []):

    if key == '':
        key = datetime.isoformat(datetime.now()).rsplit('.', 1)[0]

    j_path = 'W:/temp/build_links/' + key + '.json'
    d_temp = {'move': l_move_dirs, 'links': l_link_dirs}

    with open(j_path, 'w') as f:
        d_sym_links_new = {'move':[], 'links':[]}
        for attr in ['move', 'links']:
            l_existing = []
            for src, dst in d_temp[attr]:
                # remove duplicated operations
                key = src + ' ' + dst
                if not key in l_existing:
                    l_existing.append(key)
                    d_sym_links_new[attr].append(
                        (convert_path(src), convert_path(dst))
                    )

        json.dump(d_sym_links_new, f, indent=4)