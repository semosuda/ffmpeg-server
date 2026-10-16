"""땀냄시 방식 쇼츠 편집 스크립트 (이대호 01: 홍화철).
1x 타임라인으로 컷을 만들고, 자막을 입힌 뒤, 마지막에 1.2배속으로 변환한다.
사용: python3 build.py [preview|full]
"""
import json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = f"{ROOT}/daeho/hong.mp4"
NARR = f"{ROOT}/prod/narr"
OUT = f"{ROOT}/prod/out"
FONT_DIR = f"{ROOT}/fonts"
SW, SH = 640, 360          # 원본 해상도
VW, VH = 1080, 960         # 영상 영역
SPEED = 1.2
os.makedirs(OUT, exist_ok=True)

R = "{\\c&H2B2BFF&}"       # 빨강 강조 시작
W = "{\\c&HFFFFFF&}"       # 흰색 복귀

# 컷 정의: v=영상 시작(초), d=길이, a=음성 시작(기본 v), av=원본 음량,
# cx=크롭 중심 x(0~1), top/h=크롭 세로 범위(px), zoom=(모드, 배율), zc=확대 중심(0~1, 0~1)
# n=(나레이션 파일, 시작, 끝), subs=[(형식, 시작, 끝, 텍스트)] (컷 기준 시간)
CUTS = [
    # 파트 1: 훅
    dict(id=1, v=168.0, d=2.50, av=0.18, cx=0.66, zoom=("slow", 1.10),
         n=("N1", 0.0, 2.50), subs=[("A", 0, 2.50, f"이대호와 정훈을 {R}삼자범퇴로{W} 잡아버린")]),
    dict(id=2, v=494.4, d=1.17, av=0.18, cx=0.33, zoom=("slow", 1.12),
         n=("N1", 2.50, 3.67), subs=[("A", 0, 1.17, "고등학생 투수인데")]),
    # 파트 2: 권위자(이대호)가 훅 증명
    dict(id=3, v=988.4, d=1.55, cx=0.5, zoom=("slow", 1.05),
         subs=[("B", 0, 1.55, "아 화철이 오늘 기분 좋겠네")]),
    dict(id=4, a=990.95, v=991.6, d=1.35, cx=0.5, zoom=("punch", 1.35), zc=(0.5, 0.45),
         subs=[("B", 0, 1.35, "아버지한테 전화해 가지고")]),
    dict(id=5, v=992.3, d=1.9, cx=0.5, zoom=("fast", 1.35), zc=(0.5, 0.45),
         subs=[("BW", 0, 1.9, "삼촌 잡았다고 하겠네??")]),
    dict(id=6, v=1005.2, a=1000.85, d=2.45, cx=0.45, zoom=("none", 1.0),
         subs=[("B", 0, 2.45, "선배님 아들이라고 해서 대충 쳤는데")]),
    dict(id=7, v=997.3, d=0.75, cx=0.55, zoom=("punch", 1.5), zc=(0.5, 0.5),
         subs=[("C", 0, 0.75, "(웃음)")]),
    # 파트 3: 주인공 썰
    dict(id=9, v=99.6, d=2.47, av=0.18, cx=0.5, zoom=("slow", 1.08),
         n=("N2", 0.0, 2.47), subs=[("A", 0, 2.47, f"그리고 대선배들 앞에서 {R}각오를{W} 밝히는데")]),
    dict(id=10, v=103.2, d=1.9, cx=0.5, zoom=("none", 1.0),
         subs=[("B", 0, 1.9, "너무 대선배님들이기도 하고")]),
    dict(id=11, v=105.4, d=1.25, cx=0.5, zoom=("punch", 1.3), zc=(0.5, 0.4),
         subs=[("B", 0, 1.25, "긴장도 되고 하지만")]),
    dict(id=12, v=108.7, d=1.6, cx=0.5, zoom=("none", 1.0),
         subs=[("BW", 0, 1.6, "최선을 다해서 상대해 볼 생각입니다")]),
    dict(id=13, v=110.85, d=2.0, cx=0.5, zoom=("none", 1.0),
         subs=[("B", 0, 2.0, "최고 구속이 몇까지 나왔는지??")]),
    dict(id=14, v=112.95, d=1.7, cx=0.5, zoom=("punch", 1.3), zc=(0.5, 0.4),
         subs=[("B", 0, 1.7, "지금 한 147km까지 (확신)")]),
    dict(id=15, v=158.0, d=1.1, cx=0.5, zoom=("none", 1.0),
         subs=[("CT", 0, 1.1, "(응원)")]),
    dict(id=18, v=138.4, d=1.7, cx=0.5, zoom=("none", 1.0),
         subs=[("B", 0, 1.7, "그래도 직구 위주로!")]),
    dict(id=19, v=140.1, d=1.25, cx=0.5, zoom=("punch", 1.3), zc=(0.5, 0.4),
         subs=[("B", 0, 1.25, "남자는 직구니까")]),
    dict(id=20, a=356.9, v=356.3, d=2.5, cx=0.5, zoom=("slow", 1.10),
         subs=[("B", 0, 2.5, "와 화철이 언제 커가지고"), ("CG", 0.3, 2.5, "(감탄)")]),
    dict(id=22, v=144.3, d=0.5, cx=0.55, zoom=("none", 1.0),
         subs=[("C", 0, 0.5, "(자신만만)")]),
    dict(id=23, v=144.8, d=0.5, cx=0.55, zoom=("punch", 1.35), zc=(0.55, 0.4),
         subs=[("C", 0, 0.5, "(자신만만)")]),
    # 파트 4: 상대 소개 → 시작
    dict(id=24, v=333.6, d=1.01, av=0.18, cx=0.5, zoom=("none", 1.0),
         n=("N3", 0.0, 1.01), subs=[("A", 0, 1.01, "그리고 정훈과의")]),
    dict(id=25, h=225, v=150.0, d=1.10, av=0.18, cx=0.3, zoom=("none", 1.0),
         n=("N3", 1.01, 2.11), subs=[("A", 0, 1.10, f"승부가 {R}시작되는데{W}")]),
    # 파트 5: 승부
    dict(id=26, v=252.0, d=2.5, cx=0.75, zoom=("none", 1.0),
         subs=[("CG2", 1.0, 2.5, "(커트)")]),
    dict(id=27, top=75, h=225, v=247.6, d=1.1, cx=0.42, zoom=("punch", 1.25), zc=(0.5, 0.4),
         subs=[("B", 0, 1.1, "끈질기네")]),
    dict(id=28, v=295.5, d=4.0, cx=0.7, zoom=("none", 1.0),
         subs=[("D", 1.0, 3.5, "\" 우와 \"")]),
    dict(id=29, v=304.0, d=0.9, av=0.18, cx=0.7, zoom=("none", 1.0),
         n=("N4", 0.0, 0.9), subs=[("A", 0, 0.9, "정훈을 잡아내자")]),
    dict(id=30, v=361.0, d=0.9, av=0.18, cx=0.5, zoom=("none", 1.0),
         n=("N4", 0.9, 1.8), subs=[("A", 0, 0.9, f"이대호가 {R}직접{W}")]),
    dict(id=31, v=362.0, d=1.19, av=0.18, cx=0.5, zoom=("punch", 1.3), zc=(0.5, 0.4),
         n=("N4", 1.8, 2.99), subs=[("A", 0, 1.19, "타석에 들어서는데")]),
    dict(id=32, v=408.4, d=2.4, cx=0.68, zoom=("none", 1.0),
         subs=[("C", 1.6, 2.4, "(딱)")]),
    dict(id=33, v=412.5, d=1.8, cx=0.7, zoom=("none", 1.0), subs=[]),
    dict(id=34, v=419.6, d=1.6, cx=0.7, zoom=("none", 1.0), subs=[]),
    # 파트 6: 상대 무너짐 → 마무리
    dict(id=35, v=423.2, d=1.5, cx=0.4, zoom=("none", 1.0),
         subs=[("B", 0, 1.5, "아 볼인데...")]),
    dict(id=36, v=442.0, d=2.0, cx=0.5, zoom=("none", 1.0),
         subs=[("E", 0, 2.0, "이어지는 승부")]),
    dict(id=37, v=488.0, d=2.5, cx=0.7, zoom=("none", 1.0),
         subs=[("E", 0, 1.5, "이어지는 승부")]),
    dict(id=38, v=972.0, d=2.8, cx=0.5, zoom=("slow", 1.06),
         subs=[("B", 0, 2.8, "잘 안 보이더라~ 나이가 나이인 만큼... (아쉽)")]),
    dict(id=39, v=1079.3, d=2.11, av=0.18, cx=0.5, zoom=("slow", 1.08),
         n=("N5", 0.0, 2.11), subs=[("A", 0, 2.11, "삼촌 잡고 아빠한테 자랑하는 건")]),
    dict(id=40, v=1081.4, d=1.0, av=0.18, cx=0.5, zoom=("slow", 1.08), zc=(0.5, 0.4),
         n=("N5", 2.11, 3.11), subs=[("A", 0, 1.0, "국룰인가 봅니다")]),
]

def crop_box(c):
    top = c.get("top", 38); h = c.get("h", 250)
    w = round(h * VW / VH)
    x = min(max(round(c["cx"] * SW - w / 2), 0), SW - w)
    return w, h, x, top

def vfilter(c):
    w, h, x, y = crop_box(c)
    mode, z = c["zoom"]; d = c["d"]
    zx, zy = c.get("zc", (0.5, 0.5))
    if mode == "slow":   zexp = f"1+({z}-1)*t/{d}"
    elif mode == "fast": zexp = f"1+({z}-1)*min(t/0.35\\,1)"
    elif mode == "punch": zexp = f"{z}"
    else:                zexp = "1"
    return (f"crop={w}:{h}:{x}:{y},scale={VW}:{VH}:flags=lanczos,"
            f"scale=w='trunc({VW}*({zexp})/2)*2':h='trunc({VH}*({zexp})/2)*2':eval=frame:flags=bicubic,"
            f"crop={VW}:{VH}:'(iw-{VW})*{zx}':'(ih-{VH})*{zy}',"
            f"eq=contrast=1.08:saturation=1.15,unsharp=5:5:1.1,fps=30,setsar=1")

def render_cut(c):
    out = f"{OUT}/cut_{c['id']:02d}.mp4"
    a = c.get("a", c["v"]); av = c.get("av", 1.0); d = c["d"]
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-ss", f"{c['v']}", "-t", f"{d}", "-i", SRC,
           "-ss", f"{a}", "-t", f"{d}", "-i", SRC]
    fc = f"[0:v]{vfilter(c)}[v];[1:a]aresample=48000,volume={av},apad,atrim=0:{d}[sa]"
    if "n" in c:
        nf, ns, ne = c["n"]
        cmd += ["-i", f"{NARR}/{nf}.mp3"]
        fc += (f";[2:a]aresample=48000,atrim={ns}:{ne},asetpts=PTS-STARTPTS,volume=1.6,"
               f"pan=stereo|c0=c0|c1=c0,apad,atrim=0:{d}[na];[sa][na]amix=inputs=2:normalize=0[a]")
    else:
        fc += ";[sa]anull[a]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-t", f"{d}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    return out

def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

STYLES = {
    # 형식: (글자색, 외곽선색, 박스, 위치, 크기)
    "A":  ("&HFFFFFF&", 5, False, (540, 1080), 66),
    "BW": ("&HFFFFFF&", 5, False, (540, 1080), 62),
    "E":  ("&HFFFFFF&", 5, False, (540, 1080), 66),
    "D":  ("&HFFFFFF&", 5, False, (540, 980), 72),
    "B":  ("&H2B2BFF&", 0, True,  (540, 1265), 60),
    "C":  ("&H2B2BFF&", 0, True,  (540, 1265), 60),
    "CT": ("&H2B2BFF&", 0, True,  (540, 600), 62),
    "CG": ("&H30D830&", 5, False, (900, 580), 60),
    "CG2": ("&H30D830&", 5, False, (540, 780), 64),
}

def write_ass(times, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Line,Black Han Sans,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,5,0,5,20,20,20,1
Style: Box,Black Han Sans,60,&H002B2BFF,&H00FFFFFF,&H70000000,&H70000000,0,0,0,0,100,100,0,0,3,10,0,5,20,20,20,1
Style: Title,Black Han Sans,84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,6,0,5,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    total = times[-1][1] + CUTS[-1]["d"]
    ev = [f"Dialogue: 0,{ts(0)},{ts(total)},Title,,0,0,0,,{{\\pos(540,293)}}{{\\c&H00E6FF&}}이대호 삼촌을{{\\c&HFFFFFF&}} 잡아버린",
          f"Dialogue: 0,{ts(0)},{ts(total)},Title,,0,0,0,,{{\\pos(540,392)}}{{\\c&H2B2BFF&}}147km{{\\c&HFFFFFF&}} 고등학생 투수"]
    for c, start in times:
        for kind, s, e, text in c["subs"]:
            col, ol, box, (x, y), size = STYLES[kind]
            style = "Box" if box else "Line"
            tag = f"{{\\pos({x},{y})\\fs{size}\\c{col}}}"
            ev.append(f"Dialogue: 1,{ts(start+s)},{ts(start+e)},{style},,0,0,0,,{tag}{text}")
    open(path, "w").write(head + "\n".join(ev) + "\n")
    return total

def main(mode):
    files, times, t = [], [], 0.0
    for c in CUTS:
        files.append(render_cut(c)); times.append((c, t)); t += c["d"]
    lst = f"{OUT}/list.txt"
    open(lst, "w").write("".join(f"file '{f}'\n" for f in files))
    total = write_ass(times, f"{OUT}/subs.ass")
    json.dump([(c["id"], round(s, 2), c["d"]) for c, s in times], open(f"{OUT}/timeline.json", "w"))
    body = f"{OUT}/body_1x.mp4"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c", "copy", body], check=True)
    final = f"{OUT}/daeho01_final.mp4"
    fc = (f"color=c=black:s=1080x1920:r=30:d={total}[bg];[bg][0:v]overlay=0:480:shortest=1,"
          f"ass={OUT}/subs.ass:fontsdir={FONT_DIR},setpts=PTS/{SPEED}[v];"
          f"[0:a]atempo={SPEED},loudnorm=I=-7:TP=-1:LRA=9,volume=3dB,alimiter=limit=0.89[a]")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", body,
                    "-filter_complex", fc, "-map", "[v]", "-map", "[a]", "-r", "30",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", final], check=True)
    print("1x 길이", round(total, 2), "→ 최종", round(total / SPEED, 2), "초 :", final)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "full")
