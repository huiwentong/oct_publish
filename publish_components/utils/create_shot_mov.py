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


# def create(l_img_files, mov_path, duration, use="C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe"):
#     temp_dir = tempfile.mkdtemp()
#
#     if len(l_img_files) * 2 - 1 <= duration:
#         d_chunks = get_chunks(duration, len(l_img_files))
#         for i, l_frames in d_chunks.items():
#             src = l_img_files[i]
#             basename, ext = os.path.splitext(src)
#             for f in l_frames:
#                 dst = '{}/img.{:04d}{}'.format(temp_dir, f, ext)
#                 shutil.copyfile(src, dst)
#     else:
#         for i, src in enumerate(l_img_files):
#             basename, ext = os.path.splitext(src)
#             dst = '{}/img.{:04d}{}'.format(temp_dir, i, ext)
#             shutil.copyfile(src, dst)
#
#     if use == 'ffmpeg':
#         cmd_str = 'rez-env ffmpeg -- ffmpeg -framerate 24 -i "{input}" -c:v mjpeg -pix_fmt yuvj420p "{output}"'
#         if platform.system().lower() == 'windows':
#             # command saved to a bat file, need %% to avoid converting `%0` in bat.
#             cmd_str = cmd_str.format(
#                 input=os.path.join(temp_dir, 'img.%04d'+ext),
#                 output=mov_path
#             )
#         else:
#             cmd_str = cmd_str.format(
#                 input=os.path.join(temp_dir, 'img.%04d' + ext),
#                 output=mov_path
#             )
#     else:
#         cmd_str = '"' + use + '" ' + temp_dir + ' -o ' + mov_path
#     print(cmd_str)
#     p = subprocess.Popen(cmd_str, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window)
#     p.communicate()
#
#     if use != 'ffmpeg':
#         w, h = get_wh(use, mov_path)
#         if w > 15000 or h > 15000:
#             shutil.copyfile(mov_path, temp_dir + '/big.mov')
#             if w >= h:
#                 cmd_str = '"' + use + '" ' + temp_dir + '/big.mov -resize 15000 0 -o ' + mov_path
#             else:
#                 cmd_str = '"' + use + '" ' + temp_dir + '/big.mov -resize 0 15000 -o ' + mov_path
#
#             print(cmd_str)
#             p = subprocess.Popen(cmd_str, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window)
#             p.communicate()
#
#     # shutil.rmtree(temp_dir)
#     return

def create(l_img_files, mov_path, duration, resolution=None, use="C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe"):
    """
    创建视频文件

    参数:
        l_img_files: 图片文件列表
        mov_path: 输出视频路径
        duration: 持续时间
        resolution: 分辨率，格式为 (width, height)，例如 (1920, 1080)。None 表示不限制
        use: 使用的工具，可以是 'ffmpeg' 或 RV 可执行文件路径
    """
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
        cmd_str = '"' + use + '" ' + temp_dir + ' -o ' + mov_path + ' -quality ' + '0.5'

        # 如果指定了分辨率，添加缩放参数
        if resolution is not None:
            w, h = resolution
            cmd_str += ' -resize {} {}'.format(w, h)

    print(cmd_str)
    p = subprocess.Popen(cmd_str, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=_no_window)
    p.communicate()

    if use != 'ffmpeg':
        w, h = get_wh(use, mov_path)

        # 如果未指定分辨率，但视频尺寸过大，则自动缩放
        if resolution is None and (w > 15000 or h > 15000):
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


# def concat_mov(l_mov_files, mov_path, use="C:/Program Files/Shotgun/RV-7.7.0/bin/rvio_hw.exe"):
#     """
#     拼接 MOV 文件列表。
#     :param l_mov_files: 视频文件路径列表
#     :param mov_path: 输出文件路径
#     :param use: 使用的工具路径 ('ffmpeg' 或 RV 可执行文件路径)
#     """
#     if not l_mov_files:
#         return
#
#     if len(l_mov_files) == 1:
#         shutil.copy2(l_mov_files[0], mov_path)
#         return
#
#     temp_dir = tempfile.mkdtemp()
#
#     # 获取文件扩展名，默认使用第一个文件的扩展名，或者强制为 .mov
#     _, ext = os.path.splitext(l_mov_files[0])
#
#     try:
#         if use == 'ffmpeg':
#             # --- FFmpeg 处理逻辑 ---
#             # 1. 在临时目录生成 filelist.txt
#             list_path = os.path.join(temp_dir, 'filelist.txt')
#             with open(list_path, 'w') as f:
#                 for mov in l_mov_files:
#                     # FFmpeg concat demuxer 要求路径使用正斜杠
#                     safe_path = mov.replace('\\', '/')
#                     f.write("file '{}'\n".format(safe_path))
#
#             # 2. 构建命令
#             # 使用 -f concat -safe 0 来读取列表
#             cmd_str = 'rez-env ffmpeg -- ffmpeg -f concat -safe 0 -i "{input}" -c copy "{output}"'
#
#             if platform.system().lower() == 'windows':
#                 # Windows bat 文件中 % 需要转义为 %%
#                 safe_list_path = list_path.replace('\\', '/').replace('%', '%%')
#             else:
#                 safe_list_path = list_path
#
#             cmd_str = cmd_str.format(input=safe_list_path, output=mov_path)
#
#         else:
#             # --- RV (rvio) 处理逻辑 ---
#             # RV 通常可以直接接受多个文件作为输入序列进行拼接/播放
#             # 命令格式: rvio_hw.exe file1.mov file2.mov -o output.mov
#             input_files_str = ' '.join(['"{}"'.format(f) for f in l_mov_files])
#             cmd_str = '"' + use + '" ' + input_files_str + ' -o ' + mov_path
#
#         print(cmd_str)
#
#         # 3. 执行进程
#         p = subprocess.Popen(
#             cmd_str,
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE,
#             startupinfo=_no_window
#         )
#         stdout, stderr = p.communicate()
#
#         if p.returncode != 0:
#             print("Error:", stderr)
#
#     finally:
#         # 清理临时目录
#         if os.path.exists(temp_dir):
#             shutil.rmtree(temp_dir)
#
#     return