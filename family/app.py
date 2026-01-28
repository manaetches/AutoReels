#!/usr/bin/env python3
import csv
import os
import re
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip
try:
    from moviepy.audio.fx.all import audio_loop
except Exception:
    audio_loop = None
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "Calm_ADHD_Blueprint_Hooks2.csv")
video_src_dir = os.path.join(script_dir, "reels")
audio_path = os.path.join(script_dir, "samsmith.mp3")
target_dir = os.path.join(script_dir, "output_reel")
os.makedirs(target_dir, exist_ok=True)


# Read CSV rows
rows = []
if os.path.isfile(csv_file_path):
    with open(csv_file_path, mode="r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
else:
    print(f"Warning: CSV not found at {csv_file_path} — using sample rows for test")
    rows = [
        {"ID": "1", "Hook": "Sample hook one — quick intro", "LongTailKeywords": "sample_keyword_one"},
        {"ID": "2", "Hook": "Sample hook two — interesting fact", "LongTailKeywords": "sample_keyword_two"},
    ]


# available local reels
video_files = []
if os.path.isdir(video_src_dir):
    video_files = [f for f in os.listdir(video_src_dir) if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))]


def get_font_variant(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            if bold:
                return ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", size)
            return ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def make_rounded_text_image(text, max_width, font_size=16, padding=(12, 8), radius=3, bg_color=(255, 255, 255, 128), text_color=(0, 0, 0, 255), prefix_words=2, prefix_color=(102, 0, 153, 255)):
    words = text.split()
    draw = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines_words = []
    cur = []
    normal_font = get_font_variant(font_size, bold=False)
    for w in words:
        test = " ".join(cur + [w])
        w_size = draw.textbbox((0, 0), test, font=normal_font)[2]
        if w_size <= max_width - 2 * padding[0]:
            cur.append(w)
        else:
            if cur:
                lines_words.append(cur)
            cur = [w]
    if cur:
        lines_words.append(cur)

    line_heights = []
    text_w = 0
    for lw in lines_words:
        line_text = " ".join(lw)
        bbox = draw.textbbox((0, 0), line_text, font=normal_font)
        line_heights.append(bbox[3] - bbox[1])
        text_w = max(text_w, bbox[2] - bbox[0])
    text_h = sum(line_heights) + (len(lines_words) - 1) * 4

    img_w = text_w + 2 * padding[0]
    img_h = text_h + 2 * padding[1]
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    rect = [0, 0, img_w, img_h]
    try:
        d.rounded_rectangle(rect, radius=radius, fill=bg_color)
    except Exception:
        d.rectangle(rect, fill=bg_color)

    remaining_prefix = prefix_words
    y = padding[1]
    space_w = d.textbbox((0, 0), " ", font=normal_font)[2]
    for i, lw in enumerate(lines_words):
        line_text = " ".join(lw)
        bbox = d.textbbox((0, 0), line_text, font=normal_font)
        total_w = bbox[2] - bbox[0]
        x = (img_w - total_w) // 2

        if remaining_prefix > 0:
            num_prefix = min(remaining_prefix, len(lw))
            prefix_text = " ".join(lw[:num_prefix])
            rest_text = " ".join(lw[num_prefix:]) if num_prefix < len(lw) else ""
            prefix_font = get_font_variant(font_size, bold=True)
            d.text((x, y), prefix_text, font=prefix_font, fill=prefix_color)
            prefix_bbox = d.textbbox((0, 0), prefix_text, font=prefix_font)
            prefix_w = prefix_bbox[2] - prefix_bbox[0]
            if rest_text:
                d.text((x + prefix_w + space_w, y), rest_text, font=normal_font, fill=text_color)
            remaining_prefix -= num_prefix
        else:
            d.text((x, y), line_text, font=normal_font, fill=text_color)

        y += line_heights[i] + 4

    return img


# Process rows
for idx, row in enumerate(rows):
    fp = (row.get("FilePath") or "").strip()
    if fp and os.path.isfile(fp):
        video_path = fp
    else:
        if idx < len(video_files):
            video_path = os.path.join(video_src_dir, video_files[idx])
        else:
            print(f"No video available for row {idx+1} (ID={row.get('ID')}) - skipping")
            continue

    row_id = (row.get("ID") or str(idx + 1)).strip()
    lt = (row.get("LongTailKeywords") or "").split(",")[0].strip()
    sanitized = re.sub(r'[^A-Za-z0-9]+', '_', lt).strip('_') or f"row{row_id}"
    output_name = f"{row_id}_{sanitized}.mp4"
    output_path = os.path.join(target_dir, output_name)
    hook = row.get("Hook") or ""

    clip = VideoFileClip(video_path)
    max_width = int(clip.w * 0.85)
    pil_img = make_rounded_text_image(hook, max_width=max_width, font_size=20, padding=(16, 10), radius=6, bg_color=(255, 255, 255, 128), text_color=(0,0,0,255), prefix_words=2, prefix_color=(102,0,153,255))
    img_clip = ImageClip(np.array(pil_img)).with_position('center').with_duration(clip.duration)
    final = CompositeVideoClip([clip, img_clip])

    if os.path.isfile(audio_path):
        try:
            audio_clip = AudioFileClip(audio_path)
            # Try methods compatible with different MoviePy versions
            try:
                if hasattr(audio_clip, 'set_duration'):
                    audio_clip = audio_clip.set_duration(clip.duration)
                elif hasattr(audio_clip, 'subclip'):
                    # If audio shorter than clip, try to subclip or loop
                    try:
                        if getattr(audio_clip, 'duration', 0) >= clip.duration:
                            audio_clip = audio_clip.subclip(0, clip.duration)
                        elif audio_loop is not None:
                            audio_clip = audio_loop(audio_clip, duration=clip.duration)
                        else:
                            # last resort: subclip until audio end
                            audio_clip = audio_clip.subclip(0, getattr(audio_clip, 'duration', clip.duration))
                    except Exception:
                        pass
            except Exception:
                pass
            if hasattr(final, 'set_audio'):
                final = final.set_audio(audio_clip)
            else:
                try:
                    final.audio = audio_clip
                except Exception:
                    # fallback to set_audio if direct assignment fails
                    final = final.set_audio(audio_clip)
        except Exception as e:
            print(f"Warning: could not load audio {audio_path}: {e}")

    final.write_videofile(output_path, codec='libx264', audio_codec='aac')
    print(f"Created: {output_path}")
#!/usr/bin/env python3
import csv
import os
import re
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# Configuration
# script_dir = os.path.dirname(os.path.abspath(__file__))
# csv_file_path = os.path.join(script_dir, "Calm_ADHD_Blueprint_Hooks2.csv")
# video_src_dir = os.path.join(script_dir, "reels")
# audio_path = os.path.join(script_dir, "samsmith.mp3")
# target_dir = os.path.join(script_dir, "output_reel")
#!/usr/bin/env python3
import csv
import os
import re
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont


# Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "Calm_ADHD_Blueprint_Hooks2.csv")
video_src_dir = os.path.join(script_dir, "reels")
audio_path = os.path.join(script_dir, "audio/samsmith.mp3")
target_dir = os.path.join(script_dir, "output_reel")
os.makedirs(target_dir, exist_ok=True)


# Read CSV rows
rows = []
if os.path.isfile(csv_file_path):
    with open(csv_file_path, mode="r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
else:
    print(f"Warning: CSV not found at {csv_file_path} — using sample rows for test")
    rows = [
        {"ID": "1", "Hook": "Sample hook one — quick intro", "LongTailKeywords": "sample_keyword_one"},
        {"ID": "2", "Hook": "Sample hook two — interesting fact", "LongTailKeywords": "sample_keyword_two"},
    ]


# available local reels
video_files = []
if os.path.isdir(video_src_dir):
    video_files = [f for f in os.listdir(video_src_dir) if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))]


def get_font_variant(size, bold=False):
    try:
        if bold:
            return ImageFont.truetype("arialbd.ttf", size)
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        try:
            if bold:
                return ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", size)
            return ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", size)
        except Exception:
            return ImageFont.load_default()


def make_rounded_text_image(text, max_width, font_size=16, padding=(12, 8), radius=3, bg_color=(255, 255, 255, 128), text_color=(0, 0, 0, 255), prefix_words=2, prefix_color=(102, 0, 153, 255)):
    words = text.split()
    draw = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines_words = []
    cur = []
    normal_font = get_font_variant(font_size, bold=False)
    for w in words:
        test = " ".join(cur + [w])
        w_size = draw.textbbox((0, 0), test, font=normal_font)[2]
        if w_size <= max_width - 2 * padding[0]:
            cur.append(w)
        else:
            if cur:
                lines_words.append(cur)
            cur = [w]
    if cur:
        lines_words.append(cur)

    line_heights = []
    text_w = 0
    for lw in lines_words:
        line_text = " ".join(lw)
        bbox = draw.textbbox((0, 0), line_text, font=normal_font)
        line_heights.append(bbox[3] - bbox[1])
        text_w = max(text_w, bbox[2] - bbox[0])
    text_h = sum(line_heights) + (len(lines_words) - 1) * 4

    img_w = text_w + 2 * padding[0]
    img_h = text_h + 2 * padding[1]
    img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    rect = [0, 0, img_w, img_h]
    try:
        d.rounded_rectangle(rect, radius=radius, fill=bg_color)
    except Exception:
        d.rectangle(rect, fill=bg_color)

    remaining_prefix = prefix_words
    y = padding[1]
    space_w = d.textbbox((0, 0), " ", font=normal_font)[2]
    for i, lw in enumerate(lines_words):
        line_text = " ".join(lw)
        bbox = d.textbbox((0, 0), line_text, font=normal_font)
        total_w = bbox[2] - bbox[0]
        x = (img_w - total_w) // 2

        if remaining_prefix > 0:
            num_prefix = min(remaining_prefix, len(lw))
            prefix_text = " ".join(lw[:num_prefix])
            rest_text = " ".join(lw[num_prefix:]) if num_prefix < len(lw) else ""
            prefix_font = get_font_variant(font_size, bold=True)
            d.text((x, y), prefix_text, font=prefix_font, fill=prefix_color)
            prefix_bbox = d.textbbox((0, 0), prefix_text, font=prefix_font)
            prefix_w = prefix_bbox[2] - prefix_bbox[0]
            if rest_text:
                d.text((x + prefix_w + space_w, y), rest_text, font=normal_font, fill=text_color)
            remaining_prefix -= num_prefix
        else:
            d.text((x, y), line_text, font=normal_font, fill=text_color)

        y += line_heights[i] + 4

    return img


# Process rows
for idx, row in enumerate(rows):
    fp = (row.get("FilePath") or "").strip()
    if fp and os.path.isfile(fp):
        video_path = fp
    else:
        if idx < len(video_files):
            video_path = os.path.join(video_src_dir, video_files[idx])
        else:
            print(f"No video available for row {idx+1} (ID={row.get('ID')}) - skipping")
            continue

    row_id = (row.get("ID") or str(idx + 1)).strip()
    lt = (row.get("LongTailKeywords") or "").split(",")[0].strip()
    sanitized = re.sub(r'[^A-Za-z0-9]+', '_', lt).strip('_') or f"row{row_id}"
    output_name = f"{row_id}_{sanitized}.mp4"
    output_path = os.path.join(target_dir, output_name)
    hook = row.get("Hook") or ""

    clip = VideoFileClip(video_path)
    max_width = int(clip.w * 0.85)
    pil_img = make_rounded_text_image(hook, max_width=max_width, font_size=20, padding=(16, 10), radius=6, bg_color=(255, 255, 255, 128), text_color=(0,0,0,255), prefix_words=2, prefix_color=(102,0,153,255))
    img_clip = ImageClip(np.array(pil_img)).with_position('center').with_duration(clip.duration)
    final = CompositeVideoClip([clip, img_clip])

    if os.path.isfile(audio_path):
        try:
            audio_clip = AudioFileClip(audio_path)
            audio_clip = audio_clip.set_duration(clip.duration)
            final = final.set_audio(audio_clip)
        except Exception as e:
            print(f"Warning: could not load audio {audio_path}: {e}")

