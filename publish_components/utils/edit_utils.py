import re
import json
import subprocess
from pprint import pprint
from pathlib import Path

FPS = 24  # 根据你的工程实际帧率修改


def tc_to_frames(tc, fps=FPS):
    h, m, s, f = map(int, tc.split(':'))
    return h * 3600 * fps + m * 60 * fps + s * fps + f


def frames_to_seconds(frames, fps=FPS):
    return frames / fps


# 匹配 4 个时间码的 EDL 行
# 组: 1=事件号 2=源入 3=源出 4=记录入 5=记录出
EDL_PATTERN = re.compile(
    r'^(\d{3})\s+AX\s+V\s+C\s+'
    r'(\d{2}:\d{2}:\d{2}:\d{2})\s+'   # 源入点
    r'(\d{2}:\d{2}:\d{2}:\d{2})\s+'   # 源出点
    r'(\d{2}:\d{2}:\d{2}:\d{2})\s+'   # 记录入点
    r'(\d{2}:\d{2}:\d{2}:\d{2})'      # 记录出点
)

CLIP_NAME_PATTERN = re.compile(r'^\*\s*FROM CLIP NAME:\s*(\S+)')


def parse_edl(edl_path, fps=FPS):
    """
    解析 EDL，返回镜头列表。每个镜头包含：
      event: 事件号
      clip_name: CLIP NAME
      src_in/src_out: 源时间码（帧）
      rec_in/rec_out: 记录时间线（帧）—— 拆分用
      duration: 时长（帧）
      order: 剪辑顺序（按 EDL 行出现顺序，从 1 开始）
    """
    clips = []
    current = None
    order = 0

    with open(edl_path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            m = EDL_PATTERN.match(line)
            if m:
                # 如果上一段还没拿到 CLIP NAME，先入列（clip_name 暂空）
                if current is not None:
                    clips.append(current)

                event, s_in, s_out, r_in, r_out = m.groups()
                order += 1
                current = {
                    'event': event,
                    'clip_name': None,
                    'src_in': tc_to_frames(s_in, fps),
                    'src_out': tc_to_frames(s_out, fps),
                    'rec_in': tc_to_frames(r_in, fps),
                    'rec_out': tc_to_frames(r_out, fps),
                    'order': order,
                }
                continue

            cm = CLIP_NAME_PATTERN.match(line.strip())
            if cm and current is not None:
                current['clip_name'] = cm.group(1)

    if current is not None:
        clips.append(current)

    # 计算时长，并做基本校验
    for c in clips:
        c['duration'] = c['rec_out'] - c['rec_in']
        if c['duration'] <= 0:
            raise ValueError(f"事件 {c['event']} 记录出点 <= 入点，EDL 可能有误")
        if c['clip_name'] is None:
            # 兜底命名，避免后续 None
            c['clip_name'] = f"clip_{c['event']}"

    return clips


def split_video(video_path, clips, out_dir, fps=FPS):
    """
    用 ffmpeg 按记录时间线精确拆分视频。
    每段输出命名为 {clip_name}.mp4（或保持原扩展名）。
    使用 -ss / -to 基于帧精确到帧，配合 -avoid_negative_ts 保证无偏移。
    """
    video_path = Path(video_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    suffix = video_path.suffix  # 保留原扩展名
    results = []

    for c in clips:
        start_sec = frames_to_seconds(c['rec_in'], fps)
        end_sec = frames_to_seconds(c['rec_out'], fps)
        out_file = out_dir / f"{c['clip_name']}{suffix}"

        # -ss 放在 -i 前面是快速定位，但为了帧精确，这里放后面并配合 -to
        # 用 -ss 在 -i 之后 + 重新编码，保证帧级精确
        cmd = [
            'ffmpeg', '-y',
            '-ss', f"{start_sec:.6f}",        # 移到 -i 前面
            '-to', f"{end_sec:.6f}",          # 移到 -i 前面
            '-i', str(video_path),
            '-map', '0:v:0', '-map', '0:a?',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '16',
            '-pix_fmt', 'yuv420p',             # 显式指定通用像素格式
            '-c:a', 'aac', '-b:a', '192k',
            '-movflags', '+faststart',
            str(out_file),
        ]
        print(f"[{c['order']:03d}] {c['clip_name']}: "
              f"{start_sec:.3f}s → {end_sec:.3f}s ({c['duration']}f)")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        results.append(out_file)

    return results


def split_audio(video_path, clips, out_dir, fps=FPS):
    """
    用 ffmpeg 按记录时间线拆分视频中的音频轨。
    输出为独立音频文件，命名为 {clip_name}.wav。
    - 使用重新编码，确保每个切点采样级精确
    - wav(PCM s16le) 无损，兼容性最好
    """
    video_path = Path(video_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results = []

    for c in clips:
        start_sec = frames_to_seconds(c['rec_in'], fps)
        end_sec = frames_to_seconds(c['rec_out'], fps)
        out_file = out_dir / f"{c['clip_name']}.wav"   # ← 改扩展名

        cmd = [
            'ffmpeg', '-y',
            '-ss', f"{start_sec:.6f}",
            '-to', f"{end_sec:.6f}",
            '-i', str(video_path),
            '-map', '0:a:0',
            '-vn',
            '-c:a', 'pcm_s16le',                  
            str(out_file),
        ]
        print(f"[{c['order']:03d}] {c['clip_name']}: "
              f"{start_sec:.3f}s → {end_sec:.3f}s ({c['duration']}f)")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        results.append(out_file)

    return results

def build_json(clips, fps=FPS):
    """
    生成 JSON：按剪辑顺序记录
    {镜头名称: {持续时长, 剪辑入点(帧), 剪辑出点(帧), 剪辑顺序}}
    """
    data = {}
    for c in clips:
        data[c['clip_name']] = {
            'duration': c['duration'],
            'cut_in': c['rec_in'],
            'cut_out': c['rec_out'],
            'order': c['order'],
        }
    return data


def main(edl_path, video_path, out_dir, json_path, fps=FPS):
    clips = parse_edl(edl_path, fps=fps)
    print(f"解析到 {len(clips)} 个镜头")
    pprint(clips)

    # 可选：检查时间线是否有重叠（叠化）
    for i in range(1, len(clips)):
        prev, cur = clips[i-1], clips[i]
        if cur['rec_in'] < prev['rec_out']:
            overlap = prev['rec_out'] - cur['rec_in']
            print(f"⚠️ 叠化/重叠：{prev['clip_name']} 与 {cur['clip_name']} "
                  f"重叠 {overlap} 帧（{overlap/fps:.3f}s）")

    split_video(video_path, clips, out_dir, fps=fps)

    data = build_json(clips, fps=fps)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"JSON 已写入：{json_path}")
    return clips, data


if __name__ == '__main__':
    main(
        edl_path='P:/MK2/20_Publish/Publish_history/s26/s26.edl',
        video_path='P:/MK2/20_Publish/Publish_history/s26/MK2_s26_story-edit_V03_20261117_pub_to_lay.mov',   # 你 EDL 导出的视频
        out_dir='C:/Users/huiwentong/Desktop/temp/edltest',
        json_path='C:/Users/huiwentong/Desktop/temp/edltest/clips.json',
        fps=24,
    )