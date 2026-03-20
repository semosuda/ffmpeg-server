import glob
import os
import random
import subprocess
import tempfile
import uuid
import requests
from flask import Flask, request, send_file, jsonify

app = Flask(__name__)
KOREAN_FONT = None

def find_korean_font():
    paths = [
        "/opt/render/project/fonts/NotoSansCJKkr-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in paths:
        if os.path.isfile(path):
            return path
    for match in glob.glob("/usr/share/fonts/**/*.ttf", recursive=True):
        return match
    return None

def install_ffmpeg():
    global KOREAN_FONT
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("ffmpeg available:", result.stdout.splitlines()[0])
        else:
            print("ffmpeg not working properly")
    except Exception as e:
        print(f"ffmpeg check failed: {e}")

    font = find_korean_font()
    if font:
        KOREAN_FONT = font
        print(f"Korean font found: {font}")
    else:
        print("Warning: No Korean font found")

def download_file(url, dest_path):
    response = requests.get(url, stream=True, timeout=60)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "font": KOREAN_FONT})

@app.route("/render", methods=["POST"])
def render():
    data = request.get_json(force=True)
    image_url = data.get("image_url")
    audio_url = data.get("audio_url")
    duration = data.get("duration", 6)

    if not image_url or not audio_url:
        return jsonify({"error": "image_url and audio_url are required"}), 400

    try:
        duration = float(duration)
        if duration <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "duration must be a positive number"}), 400

    text = random.choice([
        '구독 & 좋아요 눌러주세요',
        '구독하고 알림 받으세요',
        '좋아요와 구독 부탁드려요',
        '구독과 좋아요 눌러주세요',
    ])
    fontsize = random.randint(34, 42)
    boxcolor = random.choice(["red", "darkred", "crimson", "orangered"])
    y_pos = random.randint(60, 100)
    freq = round(random.uniform(1.5, 3.0), 1)

    job_id = uuid.uuid4().hex
    tmp_dir = tempfile.mkdtemp(prefix=f"render_{job_id}_")
    image_path = os.path.join(tmp_dir, "image.png")
    audio_path = os.path.join(tmp_dir, "audio.mp3")
    output_path = os.path.join(tmp_dir, "output.mp4")

    try:
        download_file(image_url, image_path)
        download_file(audio_url, audio_path)

        d = str(duration)

        if KOREAN_FONT:
            drawtext = (
                "drawtext="
                f"fontfile={KOREAN_FONT}:"
                f"text='{text}':"
                f"fontsize={fontsize}:"
                "fontcolor=white:"
                "x=(w-text_w)/2:"
                f"y=h-{y_pos}+5*sin({freq}*PI*t):"
                "alpha='if(lt(t\\,0.5)\\,t/0.5\\,1)':"
                f"box=1:boxcolor={boxcolor}@0.8:boxborderw=20"
            )
            filter_complex = (
                f"[0:v]scale=1080:1920[bg];"
                f" [bg]{drawtext}[v];"
                f" [1:a]atrim=duration={d},asetpts=PTS-STARTPTS[a]"
            )
        else:
            filter_complex = (
                f"[0:v]scale=1080:1920[v];"
                f" [1:a]atrim=duration={d},asetpts=PTS-STARTPTS[a]"
            )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-t", d, "-i", image_path,
            "-stream_loop", "-1", "-t", d, "-i", audio_path,
            "-filter_complex", filter_complex,
            "-map", "[v]",
            "-map", "[a]",
            "-t", d,
            "-preset", "ultrafast",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-pix_fmt", "yuv420p",
            output_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            return jsonify({"error": "ffmpeg failed", "details": result.stderr[-3000:]}), 500

        return send_file(output_path, mimetype="video/mp4", as_attachment=True, download_name=f"output_{job_id}.mp4")

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download a file: {str(e)}"}), 400
    except subprocess.TimeoutExpired:
        return jsonify({"error": "ffmpeg timed out"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    install_ffmpeg()
    app.run(host="0.0.0.0", port=8080, debug=False)
