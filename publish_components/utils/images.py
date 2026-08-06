#!/usr/bin/env python  
# -*- coding:utf-8 -*-
""" 
@author:jiongwan
@team : Octmedia TD Department
@file: images.py 
@time: 2022/11/30
@contact: wanjw126@126.com
"""
import json
import os
import platform
import subprocess

import wave
import contextlib

if platform.system().lower() == 'windows':
    _no_window = subprocess.STARTUPINFO()
    _no_window.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    _no_window = None


def draw_info_on_video(video, text, out_path, font, font_size, pos, color='white'):
    bit_rate = get_video_datarate(video)
    cmd = 'ffmpeg -i {input} ' \
          '-vf "drawtext=fontfile={font}:text=\'{text}\':fontcolor={color}:fontsize={size}:x={x}:y={y}" ' \
          '-codec:a copy -vcodec "h264" -b:v {bit_rate} -crf 16 {output}'.format(input=video, font=font, text=text,
                                                                                 color=color,
                                                                                 size=font_size, x=pos[0], y=pos[1],
                                                                                 output=out_path,
                                                                                 bit_rate=bit_rate)
    try:
        py2output = subprocess.check_output(cmd, shell=False, stderr=subprocess.PIPE, startupinfo=_no_window)
    except subprocess.CalledProcessError as e:
        print(e.output)


def get_video_datarate(video):
    cmd_str = 'ffprobe.exe -i ' + video + ' -print_format json -loglevel fatal -show_format'
    p = subprocess.Popen(cmd_str, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, startupinfo=_no_window)
    (out, err) = p.communicate()
    data = json.loads(out)
    return data['format']['bit_rate']


def get_info_by_ffprobe(mov_path):
    cmd_str = 'ffprobe.exe -i ' + mov_path + ' -print_format json -loglevel fatal -show_streams -count_frames -select_streams v'
    p = subprocess.Popen(cmd_str, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    try:
        out = out.decode("utf-8")
    except:
        pass
    if not out or len(out) == 0:
        print('Invalid mov file: '.format(mov_path))
        return 960, 540, 0

    out = out.replace('\r', ' ').replace('\n', ' ').replace('"', ' ').replace(':', ' ').replace(',', '')
    l_mov_info = [t for t in out.split(' ') if t != '']

    if 'width' in l_mov_info:
        i = l_mov_info.index('width')
        res_x = int(l_mov_info[i + 1])
    else:
        res_x = 960

    if 'height' in l_mov_info:
        i = l_mov_info.index('height')
        res_y = int(l_mov_info[i + 1])
    else:
        res_y = 540

    if 'nb_frames' in l_mov_info:
        i = l_mov_info.index('nb_frames')
        duration = int(l_mov_info[i + 1])
    else:
        duration = 0
    return res_x, res_y, duration


def get_comment_by_ffprobe(mov_path):
    """

    :param mov_path: 'Z:/DS/Work/TD/wanjingwei/toXiangda/s99_902.Cm.P1.v109.mov'
    :return: {'format':
                {'bit_rate': '19985224',
                ...,
                'tags': {'comment': 'R:/dsf/Images/Cm/99/902/comp/v109/render/s99_902.Cm.P1.v109.####.exr',
                         ...}}}
    """
    cmd_str = 'ffprobe.exe -i ' + mov_path + ' -print_format json -loglevel fatal -show_format'
    p = subprocess.Popen(cmd_str, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    data = json.loads(out)
    if 'comment' in data['format']['tags']:
        return data['format']['tags']['comment']
    return ''


def get_info_by_rvls(mov_path):
    rvls_exe = os.path.join(os.environ.get('RV_PATH'), 'rvls.exe').replace('\\', '/')
    if not os.path.isfile(rvls_exe):
        rvls_exe = 'C:/Program Files/Shotgun/RV-7.7.0/bin/rvls.exe'

    cmd_str = rvls_exe + ' -x ' + mov_path
    p = subprocess.Popen(cmd_str, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    if not out or len(out) == 0:
        print('Invalid mov file: '.format(mov_path))
        return 960, 540, 0

    out = out.replace('\r', ' ').replace('\n', ' ')
    l_mov_info = [t for t in out.split(' ') if t != '']

    if 'Resolution' in l_mov_info:
        i = l_mov_info.index('Resolution')
        res_x = l_mov_info[i + 1]
        res_y = l_mov_info[i + 3]
    else:
        res_x = 960
        res_y = 540

    if 'Duration' in l_mov_info:
        i = l_mov_info.index('Duration')
        duration = int(l_mov_info[i + 1])
    elif mov_path.endswith('.#.tif'):
        img_dir = os.path.dirname(mov_path)
        img_frames = []
        tokens = os.path.basename(mov_path).split('.#.')
        for file_name in os.listdir(img_dir):
            if file_name.startswith(tokens[0]) and file_name.endswith(tokens[1]):
                if file_name.split('.')[-2].isdigit():
                    img_frames.append(int(file_name.split('.')[-2]))
        img_frames.sort()
        if len(img_frames) == 0:
            duration = 0
        else:
            duration = img_frames[-1] - img_frames[0] + 1
    else:
        duration = 0

    return res_x, res_y, duration


def get_video_codec(file_path):
    cmd = 'ffprobe.exe -v error -select_streams v:0 ' \
          '-show_entries stream=codec_name -of default=noprint_wrappers=1:nokey=1 {}'.format(file_path)
    p = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         startupinfo=_no_window)
    (out, err) = p.communicate()
    return out.strip()


def convert_to_h264(src, dst):
    video_rate = get_video_datarate(src)
    cmd = 'ffmpeg -i {} -acodec copy -vcodec "h264" -b:v {} -pix_fmt yuv420p -crf 16 -f mov {}'.format(src, video_rate, dst)
    print('cmd:' + cmd)
    subprocess.check_output(cmd, shell=False, stderr=subprocess.STDOUT, startupinfo=_no_window)


def get_audio_length(fname):
    with contextlib.closing(wave.open(fname, 'r')) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        duration = frames/float(rate*f.getnchannels())
        return duration
