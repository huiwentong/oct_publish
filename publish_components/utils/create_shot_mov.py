# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import tempfile
import platform

if platform.system().lower() == 'windows':
    _no_window = subprocess.STARTUPINFO()
    _no_window.dwFlags |= subprocess.STARTF_USESHOWWINDOW
else:
    _no_window = None


def get_chunks(m, n):
    t = m % n
    cnt = 0
    d_chunks = {}
    for i in range(n):
        d_chunks[i] = []
        v = m // n
        if i < t and t > 0:
            v += 1
        for j in range(v):
            d_chunks[i].append(cnt)
            cnt += 1
    return d_chunks


def get_wh(use, mov_path):
    rvls = os.path.dirname(use) + '/rvls.exe'
    cmd_str = '"{}" -x {}'.format(rvls, mov_path)
    print(cmd_str)
    p = subprocess.Popen(cmd_str, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window)
    out, err = p.communicate()
    tokens = [t for t in str(out).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').replace(',', ' ').split(' ') if t != '']
    if 'Resolution' in tokens:
        i = tokens.index('Resolution')
        if tokens[i+1].isdigit() and tokens[i+3].isdigit():
            return int(tokens[i+1]), int(tokens[i+3])
    return 0, 0


def create(l_img_files, mov_path, duration, use="C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe"):
    temp_dir = tempfile.mkdtemp()

    if len(l_img_files) * 2 - 1 <= duration:
        d_chunks = get_chunks(duration, len(l_img_files))
        for i, l_frames in d_chunks.items():
            src = l_img_files[i]
            basename, ext = os.path.splitext(src)
            for f in l_frames:
                dst = '{}/img.{:04d}{}'.format(temp_dir, f, ext)
                shutil.copyfile(src, dst)
    else:
        for i, src in enumerate(l_img_files):
            basename, ext = os.path.splitext(src)
            dst = '{}/img.{:04d}{}'.format(temp_dir, i, ext)
            shutil.copyfile(src, dst)

    if use == 'ffmpeg':
        cmd_str = 'rez-env ffmpeg -- ffmpeg -framerate 24 -i "{input}" -c:v mjpeg -pix_fmt yuvj420p "{output}"'
        if platform.system().lower() == 'windows':
            # command saved to a bat file, need %% to avoid converting `%0` in bat.
            cmd_str = cmd_str.format(
                input=os.path.join(temp_dir, 'img.%04d'+ext),
                output=mov_path
            )
        else:
            cmd_str = cmd_str.format(
                input=os.path.join(temp_dir, 'img.%04d' + ext),
                output=mov_path
            )
    else:
        cmd_str = '"' + use + '" ' + temp_dir + ' -o ' + mov_path
    print(cmd_str)
    p = subprocess.Popen(cmd_str, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window)
    p.communicate()

    if use != 'ffmpeg':
        w, h = get_wh(use, mov_path)
        if w > 15000 or h > 15000:
            shutil.copyfile(mov_path, temp_dir + '/big.mov')
            if w >= h:
                cmd_str = '"' + use + '" ' + temp_dir + '/big.mov -resize 15000 0 -o ' + mov_path
            else:
                cmd_str = '"' + use + '" ' + temp_dir + '/big.mov -resize 0 15000 -o ' + mov_path

            print(cmd_str)
            p = subprocess.Popen(cmd_str, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window)
            p.communicate()

    # shutil.rmtree(temp_dir)
    return

def convert_nzt_nuke_mov(input, output, dcc = 'Nuke'):
    """
    rez-env ffmpeg -- ffmpeg
    -i "R:/projects/nzt/shot/g20/g20300/lgt/slapcomp/g20300.lgt.slapcomp.v002/preview/g20300.lgt.slapcomp.v002.mov"
    -map 0 -c:v prores -c:a copy
    "R:/projects/nzt/shot/g20/g20300/lgt/slapcomp/g20300.lgt.slapcomp.v002/preview/g20300.lgt.slapcomp.v002.shotgun.mov"

    :param input:
    :param output:
    :return:
    """
    # cmd_str = '//192.168.15.15/pipeline/packages/ffmpeg/4.2.2/platform-windows/bin/ffmpeg.exe -i "{input}" -map 0 -c:v prores -c:a copy "{output}"'\
    #     .format(input = input, output = output)
    # # cmd_str = '//192.168.15.15/pipeline/packages/ffmpeg/4.2.2/platform-windows/bin/ffmpeg.exe -i "{input}" -strict experimental -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 -c:a copy "{output}"'\
    # #     .format(input = input, output = output)
    # print(cmd_str)
    # try:
    #     p = subprocess.Popen(cmd_str)
    #     # ret = p.communicate()
    #     ret = p.wait()
    #     return True
    # except:
    #     return False
    cmd_str = ''
    if not input.endswith('.mov'):          # mov, jpg, png, tif, etc ...
        nk_template_file = os.path.dirname(__file__) + '/templates/exr_to_sg_mov.nk'
        new_nk = os.path.dirname(output) + '/exr_to_sg_mov.nk'
        new_nk = new_nk.replace('\\', '/')
        lines = []
        with open(nk_template_file, 'r') as op:
            lines = op.readlines()
            lines[42] = ' name {}\n'.format(new_nk)
            lines[60] = ' file {}\n'.format(input)
            lines[73] = ' file {}\n'.format(output)

        with open(new_nk, 'w') as op:
            op.writelines(lines)


        if dcc == 'Nuke':
            cmd_str = "\"C:/Program Files/Nuke12.2v2/Nuke12.2.exe\" -V 2 -x -X \"WriteSgMov\" -F 1-1 \"{nk}\"".format(nk = new_nk)
        else:
            cmd_str = "\"C:/rez/bin/rez-env.exe\" nuke-12.2v2 oct_nuke nuke_plugins -- nuke -V 2 -x -X \"WriteSgMov\" -F 1-1 \"{nk}\"".format(
                nk=new_nk)

    else:
        cmd_str = '//192.168.15.15/pipeline/packages/ffmpeg/4.2.2/platform-windows/bin/ffmpeg.exe -i "{input}" -strict experimental -vcodec libx264 -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -pix_fmt yuv420p -g 30 -vprofile high -bf 0 -crf 23 -c:a copy "{output}"'\
            .format(input = input, output = output)
    print(cmd_str)

    try:
        p = subprocess.Popen(cmd_str)
        # ret = p.communicate()
        ret = p.wait()
        return True
    except:
        return False