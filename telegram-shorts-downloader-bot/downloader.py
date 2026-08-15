import os
import uuid
import asyncio
import platform
import shutil
import urllib.request
import zipfile
import yt_dlp
import imageio_ffmpeg
from config import TEMP_DOWNLOADS_DIR

FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

def ensure_js_runtime():
    """Ensure a JavaScript runtime (Node or Deno) is available for yt-dlp signature challenge solving."""
    if shutil.which("node") or shutil.which("deno"):
        return
    if platform.system() == "Linux":
        deno_dir = "/tmp/bin"
        os.makedirs(deno_dir, exist_ok=True)
        deno_path = os.path.join(deno_dir, "deno")
        if not os.path.exists(deno_path):
            try:
                zip_path = "/tmp/deno.zip"
                url = "https://github.com/denoland/deno/releases/download/v1.46.3/deno-x86_64-unknown-linux-gnu.zip"
                urllib.request.urlretrieve(url, zip_path)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(deno_dir)
                os.chmod(deno_path, 0o755)
                print("Auto-installed Deno JS runtime for yt-dlp signature challenges.")
            except Exception as e:
                print("Notice: Could not auto-download Deno:", e)
        if os.path.exists(deno_path):
            curr_path = os.environ.get("PATH", "")
            if deno_dir not in curr_path:
                os.environ["PATH"] = f"{deno_dir}:{curr_path}"

# Call at module import
ensure_js_runtime()

def extract_video_info(url: str):
    ensure_js_runtime()
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'js_runtimes': {'node': {}, 'deno': {}},
        'remote_components': ['ejs:github'],
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'tv_embedded']
            }
        }
    }
    if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
        ydl_opts['ffmpeg_location'] = FFMPEG_EXE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        duration = info.get('duration', 0)
        mins = int(duration // 60)
        secs = int(duration % 60)
        
        formats = info.get('formats', [])
        has_1080 = any(f.get('height') and f.get('height') >= 1080 for f in formats)
        has_720 = any(f.get('height') and f.get('height') >= 720 for f in formats)

        return {
            'id': info.get('id'),
            'title': info.get('title', 'Без названия'),
            'thumbnail': info.get('thumbnail'),
            'uploader': info.get('uploader') or info.get('channel', 'YouTube'),
            'duration_str': f"{mins}:{secs:02d}",
            'duration_sec': duration,
            'view_count': info.get('view_count', 0),
            'is_short': duration <= 90 or '/shorts/' in url,
            'has_1080': has_1080,
            'has_720': has_720
        }

async def async_extract_info(url: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, extract_video_info, url)

def download_video_sync(url: str, quality: str):
    file_id = str(uuid.uuid4())[:8]
    ext = 'mp3' if quality == 'audio' else 'mp4'
    out_template = os.path.join(TEMP_DOWNLOADS_DIR, f"{file_id}.%(ext)s")

    opts = {
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'js_runtimes': {'node': {}, 'deno': {}},
        'remote_components': ['ejs:github'],
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'tv_embedded']
            }
        },
        'postprocessor_args': {
            'ffmpeg': ['-movflags', '+faststart']
        }
    }

    if FFMPEG_EXE and os.path.exists(FFMPEG_EXE):
        opts['ffmpeg_location'] = FFMPEG_EXE

    if quality == 'audio':
        opts.update({
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        })
    elif quality == '1080':
        opts.update({
            'format': 'bestvideo[height<=1080][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'merge_output_format': 'mp4'
        })
    elif quality == '720':
        opts.update({
            'format': 'bestvideo[height<=720][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best',
            'merge_output_format': 'mp4'
        })
    elif quality == '480':
        opts.update({
            'format': 'bestvideo[height<=480][vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo[height<=480]+bestaudio/best[height<=480]/best',
            'merge_output_format': 'mp4'
        })
    else:  # best / max
        opts.update({
            'format': 'bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        })

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get('title', 'video')
        duration = int(info.get('duration') or 0)
        
        # Get actual video resolution
        width = info.get('width') or 0
        height = info.get('height') or 0
        if 'requested_downloads' in info and info['requested_downloads']:
            req = info['requested_downloads'][0]
            width = req.get('width') or width
            height = req.get('height') or height

    # Find the actual generated file
    target_path = os.path.join(TEMP_DOWNLOADS_DIR, f"{file_id}.{ext}")
    if not os.path.exists(target_path):
        for f in os.listdir(TEMP_DOWNLOADS_DIR):
            if f.startswith(file_id):
                target_path = os.path.join(TEMP_DOWNLOADS_DIR, f)
                break

    file_size = os.path.getsize(target_path) if os.path.exists(target_path) else 0

    return {
        'filepath': target_path,
        'title': title,
        'duration': duration,
        'width': width,
        'height': height,
        'size_bytes': file_size,
        'is_audio': quality == 'audio'
    }

async def async_download_video(url: str, quality: str):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, download_video_sync, url, quality)

def cleanup_file(filepath: str):
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error removing temp file {filepath}: {e}")
