#!/usr/bin/env python3
try:
    from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
    from moviepy.video.VideoClip import ColorClip
except Exception:
    from moviepy import VideoFileClip, ImageClip, CompositeVideoClip
    from moviepy.video.VideoClip import ColorClip
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
video_src_dir = r"C:\software\autoreels\AutoReels\family\reels"
output = os.path.join(script_dir, "preview_test.mp4")

# find first source video
files = [f for f in os.listdir(video_src_dir) if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))]
if not files:
    print('No source reels found in', video_src_dir)
    raise SystemExit(1)

video_path = os.path.join(video_src_dir, files[0])
print('Using', video_path)

clip = VideoFileClip(video_path)
max_duration = min(8, getattr(clip, 'duration', 8))
try:
    clip = clip.subclip(0, max_duration)
except Exception:
    try:
        clip = clip.subclipped(0, max_duration)
    except Exception:
        # leave full clip if subclip not available
        pass

portrait_w, portrait_h = 1080, 1920
scale = max(portrait_w / clip.w, portrait_h / clip.h)
try:
    clip_resized = clip.resize(scale)
except Exception:
    clip_resized = clip

try:
    clip_resized = clip_resized.set_duration(clip.duration)
except Exception:
    try:
        clip_resized = clip_resized.with_duration(clip.duration)
    except Exception:
        pass

try:
    bg = ColorClip(size=(portrait_w, portrait_h), color=(0,0,0)).set_duration(clip_resized.duration)
except Exception:
    try:
        bg = ColorClip(size=(portrait_w, portrait_h), color=(0,0,0)).with_duration(clip_resized.duration)
    except Exception:
        bg = ColorClip(size=(portrait_w, portrait_h), color=(0,0,0))
video_layer = clip_resized.with_position(('center','center'))

# use same rounded text style as app.py
audio_path = r"C:\software\autoreels\AutoReels\family\audio\samsmith.mp3"

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


def make_rounded_text_image(text, max_width, font_size=16, padding=(12, 8), radius=3, bg_color=(255,255,255,200), text_color=(0,0,0,255), prefix_words=2, prefix_color=(102,0,153,255)):
    words = text.split()
    draw = ImageDraw.Draw(Image.new("RGBA", (10,10)))
    lines_words = []
    cur = []
    normal_font = get_font_variant(font_size, bold=False)
    for w in words:
        test = " ".join(cur + [w])
        try:
            w_size = draw.textbbox((0,0), test, font=normal_font)[2]
        except Exception:
            w_size = draw.textlength(test, font=normal_font) if hasattr(draw, 'textlength') else len(test)*6
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
        try:
            bbox = draw.textbbox((0,0), line_text, font=normal_font)
            lh = bbox[3] - bbox[1]
            lw_w = bbox[2] - bbox[0]
        except Exception:
            lh = 12
            lw_w = len(line_text)*6
        line_heights.append(lh)
        text_w = max(text_w, lw_w)
    text_h = sum(line_heights) + (len(lines_words)-1)*4

    img_w = text_w + 2 * padding[0]
    img_h = text_h + 2 * padding[1]
    img = Image.new("RGBA", (img_w, img_h), (0,0,0,0))
    d = ImageDraw.Draw(img)

    rect = [0,0,img_w,img_h]
    try:
        d.rounded_rectangle(rect, radius=radius, fill=bg_color)
    except Exception:
        d.rectangle(rect, fill=bg_color)

    remaining_prefix = prefix_words
    y = padding[1]
    try:
        space_w = d.textbbox((0,0), " ", font=normal_font)[2]
    except Exception:
        space_w = 6
    for i, lw in enumerate(lines_words):
        line_text = " ".join(lw)
        try:
            bbox = d.textbbox((0,0), line_text, font=normal_font)
            total_w = bbox[2] - bbox[0]
        except Exception:
            total_w = len(line_text)*6
        x = (img_w - total_w)//2

        if remaining_prefix > 0:
            num_prefix = min(remaining_prefix, len(lw))
            prefix_text = " ".join(lw[:num_prefix])
            rest_text = " ".join(lw[num_prefix:]) if num_prefix < len(lw) else ""
            prefix_font = get_font_variant(font_size, bold=True)
            d.text((x,y), prefix_text, font=prefix_font, fill=prefix_color)
            try:
                prefix_bbox = d.textbbox((0,0), prefix_text, font=prefix_font)
                prefix_w = prefix_bbox[2] - prefix_bbox[0]
            except Exception:
                prefix_w = len(prefix_text)*6
            if rest_text:
                d.text((x + prefix_w + space_w, y), rest_text, font=normal_font, fill=text_color)
            remaining_prefix -= num_prefix
        else:
            d.text((x,y), line_text, font=normal_font, fill=text_color)

        y += line_heights[i] + 4

    return img

# build overlay using same styling
hook_text = "Preview Overlay"
max_width = int(portrait_w * 0.85)
pil_img = make_rounded_text_image(hook_text, max_width=max_width, font_size=40, padding=(24,16), radius=10)
img_clip = ImageClip(np.array(pil_img)).with_position(('center','center')).with_duration(clip_resized.duration)

final = CompositeVideoClip([bg, video_layer, img_clip], size=(portrait_w, portrait_h))

# attach audio if available (trim/loop to duration)
final_duration = getattr(final, 'duration', getattr(clip_resized, 'duration', None))
if os.path.isfile(audio_path):
    try:
        audio = AudioFileClip(audio_path)
        a_dur = getattr(audio, 'duration', None)
        try:
            a_dur = float(a_dur) if a_dur is not None else None
        except Exception:
            a_dur = None

        if a_dur is not None and final_duration is not None and a_dur >= final_duration and hasattr(audio, 'subclip'):
            audio = audio.subclip(0, final_duration)
        elif a_dur is None or (final_duration is not None and a_dur < final_duration):
            if audio_loop is not None and final_duration is not None:
                try:
                    audio = audio_loop(audio, duration=final_duration)
                except Exception:
                    try:
                        audio = audio.fx(audio_loop, duration=final_duration)
                    except Exception:
                        pass
        try:
            final = final.set_audio(audio)
        except Exception:
            try:
                final.audio = audio
            except Exception:
                pass
    except Exception as e:
        print('Warning: could not attach audio:', e)

final.write_videofile(output, codec='libx264', audio_codec='aac', fps=getattr(clip, 'fps', 24))
print('Preview written to', output)
