import traceback
import os
import json
import subprocess
from publish_core.database.entity import SGEntity


def main(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    """
检查剪辑提交daily的mov
    """
    try:
        if process_data.get("publish_type") == "Dailies":
            movs = process_data.get('preview_paths')
            if len(movs) > 1:
                return "剪辑提交单场次daily，只能提交一个视频"

            mov = movs[0]
            if not os.path.exists(mov):
                return f"视频文件不存在：{mov}"

            if not os.path.isfile(mov):
                return f"路径不是文件：{mov}"

            # 文件为空也视为无效
            if os.path.getsize(mov) == 0:
                return f"视频文件为空：{mov}"

            # ---- 3. 扩展名 ----
            valid_exts = {".mov", ".mp4", ".mxf", ".avi", ".mkv"}
            ext = os.path.splitext(mov)[1].lower()
            if ext not in valid_exts:
                return f"视频格式不支持：{ext}（支持 {', '.join(sorted(valid_exts))}）"

            # ---- 4. 能否正常打开（ffprobe 探测） ----
            try:
                result = subprocess.run(
                    [
                        "ffprobe", "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=codec_type,codec_name,width,height",
                        "-of", "json", mov,
                    ],
                    capture_output=True, text=True, timeout=30,
                )
            except FileNotFoundError:
                return "未找到 ffprobe，请确认 FFmpeg 已安装并加入 PATH"
            except subprocess.TimeoutExpired:
                return f"探测视频超时（文件可能损坏）：{mov}"

            if result.returncode != 0:
                err = (result.stderr or "").strip().splitlines()
                detail = err[-1] if err else "未知错误"
                return f"视频文件无法解析（可能已损坏）：{detail}"

            # ---- 5. 是否含视频流 ----
            try:
                info = json.loads(result.stdout or "{}")
            except json.JSONDecodeError:
                return "ffprobe 返回结果异常，无法判断视频流"

            streams = info.get("streams", [])
            if not streams:
                return "文件中没有视频流，可能不是有效视频"
            


    except:
        return traceback.format_exc()




def fix(submit_data:dict, process_data:dict, parent_widget=None, logger=None):
    pass