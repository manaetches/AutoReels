#!/usr/bin/env python3
import csv
import os
import re
try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip
except Exception:
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
video_src_dir = r"C:\software\autoreels\AutoReels\family\reels"
audio_path = r"C:\software\autoreels\AutoReels\family\audio\samsmith.mp3"
target_dir = r"C:\software\autoreels\AutoReels\family\output_reel"
os.makedirs(target_dir, exist_ok=True)


# Read CSV rows
rows = []
original_fieldnames = None
if os.path.isfile(csv_file_path):
    with open(csv_file_path, mode="r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        original_fieldnames = reader.fieldnames
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
    # Avoid using previously-generated outputs as inputs (prevents processing loop/static video).
    use_fp = False
    if fp and os.path.isfile(fp):
        try:
            fp_abs = os.path.abspath(fp)
            target_abs = os.path.abspath(target_dir)
            if not fp_abs.startswith(target_abs + os.sep):
                use_fp = True
        except Exception:
            use_fp = True

    if use_fp:
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

    # Target portrait (mobile) size: 9:16 aspect ratio (width x height)
    portrait_w, portrait_h = 1080, 1920

    # Scale clip to fill portrait frame
    try:
        scale = max(portrait_w / clip.w, portrait_h / clip.h)
    except Exception:
        scale = 1.0

    try:
        clip_resized = clip.resize(scale)
    except Exception:
        try:
            from moviepy.video.fx.all import resize
            clip_resized = resize(clip, scale)
        except Exception:
            clip_resized = clip

    # Ensure duration preserved and create a portrait background
    try:
        clip_resized = clip_resized.set_duration(clip.duration)
    except Exception:
        pass

    try:
        from moviepy.video.VideoClip import ColorClip
        bg = ColorClip(size=(portrait_w, portrait_h), color=(0, 0, 0)).set_duration(getattr(clip, 'duration', None) or clip_resized.duration)
    except Exception:
        bg = None

    # Center the resized clip on the portrait canvas
    video_layer = clip_resized.with_position(('center', 'center'))

    # prepare centered text overlay sized relative to portrait width
    max_width = int(portrait_w * 0.85)
    pil_img = make_rounded_text_image(hook, max_width=max_width, font_size=40, padding=(24, 16), radius=10, bg_color=(255, 255, 255, 200), text_color=(0,0,0,255), prefix_words=2, prefix_color=(102,0,153,255))
    img_clip = ImageClip(np.array(pil_img)).with_position(('center', 'center')).with_duration(getattr(clip_resized, 'duration', clip.duration))

    layers = []
    if bg is not None:
        layers.append(bg)
    layers.append(video_layer)
    layers.append(img_clip)

    final = CompositeVideoClip(layers, size=(portrait_w, portrait_h))

    # Attach audio trimmed/looped to final duration
    final_duration = getattr(final, 'duration', getattr(clip, 'duration', None))
    if os.path.isfile(audio_path):
        try:
            audio_clip = AudioFileClip(audio_path)
            audio_duration = getattr(audio_clip, 'duration', None)
            try:
                audio_duration = float(audio_duration) if audio_duration is not None else None
            except Exception:
                audio_duration = None

            if audio_duration is not None and final_duration is not None and audio_duration >= final_duration and hasattr(audio_clip, 'subclip'):
                audio_clip = audio_clip.subclip(0, final_duration)
            elif audio_duration is None or (final_duration is not None and audio_duration < final_duration):
                if audio_loop is not None and final_duration is not None:
                    try:
                        audio_clip = audio_loop(audio_clip, duration=final_duration)
                    except Exception:
                        try:
                            audio_clip = audio_clip.fx(audio_loop, duration=final_duration)
                        except Exception:
                            pass
                else:
                    if hasattr(audio_clip, 'subclip') and audio_duration is not None:
                        try:
                            audio_clip = audio_clip.subclip(0, min(audio_duration, final_duration or audio_duration))
                        except Exception:
                            pass

            try:
                final = final.set_audio(audio_clip)
            except Exception:
                try:
                    final.audio = audio_clip
                except Exception:
                    pass
        except Exception as e:
            print(f"Warning: could not load audio {audio_path}: {e}")

    # Write output (preserve source fps if available)
    try:
        fps = getattr(clip, 'fps', None) or 30
    except Exception:
        fps = 30
    final.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=fps)
    print(f"Created: {output_path}")
    # create a small marker file to reliably indicate successful creation
    try:
        marker = output_path + ".done"
        with open(marker, 'w', encoding='utf-8') as m:
            m.write('')
    except Exception:
        pass
    # Record the output absolute path into the CSV under the FilePath column (5th column)
    try:
        # update the in-memory row; `rows` is the original list loaded from CSV when present
        rows[idx]['FilePath'] = output_path

        # determine fieldnames to write, inserting FilePath as the 5th column if missing
        if original_fieldnames:
            fns = list(original_fieldnames)
        elif rows:
            fns = list(rows[0].keys())
        else:
            fns = ['ID', 'Hook', 'LongTailKeywords']

        if 'FilePath' not in fns:
            insert_index = 4 if len(fns) >= 4 else len(fns)
            fns.insert(insert_index, 'FilePath')

        # write back the CSV with updated FilePath values
        with open(csv_file_path, mode='w', encoding='utf-8', newline='') as wf:
            writer = csv.DictWriter(wf, fieldnames=fns)
            writer.writeheader()
            for r in rows:
                out = {k: r.get(k, '') for k in fns}
                writer.writerow(out)
    except Exception as e:
        print(f"Warning: could not update CSV {csv_file_path}: {e}")

