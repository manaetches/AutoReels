import csv
import os
import re
import textwrap
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Get the absolute path to the CSV file in the same directory as this script
# Defaults (can be overridden by run_process parameters)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Portrait output size (9:16)
OUT_W, OUT_H = 720, 1280
MAX_DURATION = 15  # seconds

def run_process(csv_path=None, video_src_dir=None, target_dir=None, music_path=None, rows_count=3):
    """Process CSV rows and generate videos.
    Parameters are optional overrides; if not provided, sensible defaults are used.
    Returns list of created output paths (strings).
    """
    # resolve defaults
    csv_file_path = csv_path or os.path.join(script_dir, "Calm_ADHD_Blueprint_Hooks2.csv")
    video_src_dir = video_src_dir or r"D:\reels-dev\mixkit\women\family"
    target_dir = target_dir or r"D:\reels-dev\mixkit\women\family\ADHD_output_reel"
    os.makedirs(target_dir, exist_ok=True)

    # Read CSV into list of dicts
    with open(csv_file_path, mode='r', encoding='utf-8', newline='') as file:
        dr = list(csv.DictReader(file))

    if not dr:
        raise RuntimeError('CSV is empty or could not be read.')

    # select number of rows
    rows_to_process = dr[:rows_count]

    # List video files (alphabetical)
    video_files = sorted([f for f in os.listdir(video_src_dir) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))])
    if len(video_files) < len(rows_to_process):
        raise RuntimeError('Not enough video files in source directory.')

    # Background music
    bg_audio = None
    if music_path and os.path.exists(music_path):
        try:
            bg_audio = AudioFileClip(music_path)
        except Exception as e:
            print('Could not load background audio:', e)

    created = []

# Helper: font loader
def get_font(size=16):
    def _try(name):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            return None
    # try regular then fallback
    f = _try("arial.ttf") or _try(r"C:\Windows\Fonts\arial.ttf")
    if f:
        return f
    return ImageFont.load_default()

# Helper: create rounded-corner PIL image with optional highlighted keyword
def make_rounded_text_image(text, max_width, font_size=16, highlight=None,
                            highlight_size=20, padding=(10, 10), radius=5,
                            bg_color=(255, 255, 255, 128), text_color=(0, 0, 0, 255), highlight_color=(85, 0, 128, 255)):
    base_font = get_font(font_size)
    # try to load a bold font for highlighted text (Windows fallback), else use base
    try:
        hl_font = ImageFont.truetype("arialbd.ttf", highlight_size)
    except Exception:
        try:
            hl_font = ImageFont.truetype(r"C:\Windows\Fonts\arialbd.ttf", highlight_size)
        except Exception:
            hl_font = get_font(highlight_size)
    draw = ImageDraw.Draw(Image.new('RGBA', (10, 10)))

    words = text.split()
    lines = []
    cur = ''
    for w in words:
        test = (cur + ' ' + w).strip()
        bbox = draw.textbbox((0, 0), test, font=base_font)
        w_size = bbox[2]
        if w_size <= max_width - 2 * padding[0]:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)

    # measure line sizes, account for highlight width
    line_sizes = []
    total_h = 0
    max_line_w = 0
    for line in lines:
        if highlight and highlight.lower() in line.lower():
            parts = re.split(f'({re.escape(highlight)})', line, flags=re.IGNORECASE)
            w_line = 0
            for part in parts:
                if part.lower() == highlight.lower():
                    w_line += draw.textbbox((0, 0), part, font=hl_font)[2]
                else:
                    w_line += draw.textbbox((0, 0), part, font=base_font)[2]
        else:
            w_line = draw.textbbox((0, 0), line, font=base_font)[2]
        h_line = draw.textbbox((0, 0), line, font=base_font)[3]
        max_line_w = max(max_line_w, w_line)
        line_sizes.append((w_line, h_line))
        total_h += h_line + 4
    total_h -= 4

    img_w = int(max_line_w + 2 * padding[0])
    img_h = int(total_h + 2 * padding[1])
    img = Image.new('RGBA', (img_w, img_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    rect = [0, 0, img_w, img_h]
    try:
        d.rounded_rectangle(rect, radius=radius, fill=bg_color)
    except Exception:
        d.rectangle(rect, fill=bg_color)

    y = padding[1]
    for i, line in enumerate(lines):
        w_line, h_line = line_sizes[i]
        x = (img_w - w_line) // 2
        if highlight and highlight.lower() in line.lower():
            parts = re.split(f'({re.escape(highlight)})', line, flags=re.IGNORECASE)
            x_cursor = x
            for part in parts:
                if part.lower() == highlight.lower():
                    # Draw highlighted part in bold dark purple without removing background
                    pw = d.textbbox((0, 0), part, font=hl_font)[2]
                    d.text((x_cursor, y), part, font=hl_font, fill=highlight_color)
                    x_cursor += pw
                else:
                    d.text((x_cursor, y), part, font=base_font, fill=text_color)
                    x_cursor += d.textbbox((0, 0), part, font=base_font)[2]
        else:
            d.text((x, y), line, font=base_font, fill=text_color)
        y += h_line + 4

    return img

# Helper: create bg audio clip for duration with multiple fallbacks
def bg_for_duration(bg_clip, duration):
    if bg_clip is None:
        return None
    try:
        return bg_clip.set_duration(duration)
    except Exception:
        pass
    try:
        return bg_clip.subclip(0, duration)
    except Exception:
        pass
    try:
        return bg_clip.with_duration(duration)
    except Exception:
        pass
    try:
        from moviepy.audio.fx.all import audio_loop
        return audio_loop(bg_clip, duration=duration)
    except Exception:
        pass
    return None
    return None

    # Process rows and videos
    for idx, (drow, video_file) in enumerate(zip(rows_to_process, video_files[:len(rows_to_process)])):
    hook = (drow.get('Hook') or '')
    # highlight first two words of the hook (updated per request)
    first_two = ' '.join(hook.split()[:2]) if hook else ''

    # output filename derived from first longtail keyword if present
    longtail = (drow.get('LongTailKeywords') or '')
    first_kw = longtail.split(',')[0].strip() if longtail else f'hook_{idx+1}'
    fname = re.sub(r'[^A-Za-z0-9_\-]', '_', first_kw.replace(' ', '_'))
    output_path = os.path.join(target_dir, f"{fname}.mp4")

    video_path = os.path.join(video_src_dir, video_file)
    clip = VideoFileClip(video_path)
    duration = min(MAX_DURATION, clip.duration)
    # Trim safely across different moviepy versions
    try:
        clip = clip.subclip(0, duration)
    except Exception:
        if hasattr(clip, 'with_duration'):
            try:
                clip = clip.with_duration(duration)
            except Exception:
                pass
        elif hasattr(clip, 'set_duration'):
            try:
                clip = clip.set_duration(duration)
            except Exception:
                pass

    # fit clip into portrait canvas while preserving aspect ratio
    scale = min(OUT_W / clip.w, OUT_H / clip.h)
    # handle resize/resized across moviepy versions
    try:
        clip_resized = clip.resize(scale)
    except Exception:
        try:
            clip_resized = clip.resized(scale)
        except Exception:
            try:
                new_w = int(clip.w * scale)
                new_h = int(clip.h * scale)
                clip_resized = clip.resize((new_w, new_h))
            except Exception:
                clip_resized = clip
    bg_array = np.zeros((OUT_H, OUT_W, 3), dtype=np.uint8)
    bg_clip = ImageClip(bg_array).with_duration(clip_resized.duration)
    x_pos = (OUT_W - clip_resized.w) / 2
    y_pos = (OUT_H - clip_resized.h) / 2
    clip_centered = clip_resized.with_position((x_pos, y_pos))

    # prepare text image: narrow width -> 20% of OUT_W
    max_text_w = int(OUT_W * 0.20)
    # Changed highlight color to dark purple here (RGB ~ 85,0,128)
    pil_img = make_rounded_text_image(hook, max_width=max_text_w, font_size=16,
                                      highlight=first_two if first_two else None,
                                      highlight_size=20, padding=(10, 10), radius=3,
                                      highlight_color=(85, 0, 128, 255))

    # center the text overlay
    img_clip = ImageClip(np.array(pil_img)).with_position(('center', 'center')).with_duration(clip_resized.duration)

    final = CompositeVideoClip([bg_clip, clip_centered, img_clip])

    # audio: mix background music if available
    if bg_audio:
        try:
            bg = bg_for_duration(bg_audio, final.duration)
            if bg is not None:
                # apply volumex with fallback to fx.volumex
                try:
                    bg = bg.volumex(0.3)
                except Exception:
                    try:
                        from moviepy.audio.fx.all import volumex as _volumex

                        bg = _volumex(bg, 0.3)
                    except Exception:
                        pass

                orig_audio = getattr(clip, 'audio', None)
                if orig_audio:
                    # reduce original audio then combine
                    try:
                        a1 = orig_audio.volumex(0.7)
                    except Exception:
                        try:
                            from moviepy.audio.fx.all import volumex as _volumex

                            a1 = _volumex(orig_audio, 0.7)
                        except Exception:
                            a1 = orig_audio
                    try:
                        from moviepy.audio.AudioClip import CompositeAudioClip

                        combined = CompositeAudioClip([a1, bg])
                        final = final.with_audio(combined)
                    except Exception:
                        final = final.with_audio(bg)
                else:
                    final = final.with_audio(bg)
            else:
                # fallback: keep original audio if any
                pass
        except Exception as e:
            print('Audio mixing failed:', e)

        try:
            final.write_videofile(output_path, codec='libx264', audio_codec='aac')
            print(f"Created: {output_path}")
        except Exception as e:
            print('Write failed:', e)
            # fallback: try writing to a temp file then atomically replace
            try:
                alt = output_path + '.tmp.mp4'
                final.write_videofile(alt, codec='libx264', audio_codec='aac')
                try:
                    os.replace(alt, output_path)
                    print(f"Created (via fallback): {output_path}")
                except Exception as re:
                    print('Could not replace temp file into place:', re)
            except Exception as e2:
                print('Fallback write also failed:', e2)

        # Update CSV row with FilePath (use DictReader/DictWriter to avoid column shifts)
        try:
            with open(csv_file_path, mode='r', encoding='utf-8', newline='') as rf:
                current_rows = list(csv.DictReader(rf))
                fieldnames = list(current_rows[0].keys()) if current_rows else []

            # ensure FilePath is in fieldnames
            if 'FilePath' not in fieldnames:
                fieldnames.append('FilePath')

            # match by Hook exact text first, else fallback to index
            matched = False
            for i, old in enumerate(current_rows):
                if (old.get('Hook') or '').strip() == hook.strip():
                    current_rows[i]['FilePath'] = output_path
                    matched = True
                    break

            if not matched:
                if idx < len(current_rows):
                    current_rows[idx]['FilePath'] = output_path
                else:
                    newrow = {k: '' for k in fieldnames}
                    newrow['Hook'] = hook
                    newrow['FilePath'] = output_path
                    current_rows.append(newrow)

            # write back using DictWriter to preserve columns cleanly
            # write to temp file then replace for safety
            tmp = csv_file_path + '.tmp'
            with open(tmp, mode='w', encoding='utf-8', newline='') as wf:
                writer = csv.DictWriter(wf, fieldnames=fieldnames)
                writer.writeheader()
                for d in current_rows:
                    fp = d.get('FilePath') or ''
                    if isinstance(fp, list):
                        fp = fp[-1] if fp else ''
                    d['FilePath'] = fp
                    writer.writerow(d)
            try:
                os.replace(tmp, csv_file_path)
            except Exception:
                # final fallback: try writing directly
                with open(csv_file_path, mode='w', encoding='utf-8', newline='') as wf:
                    writer = csv.DictWriter(wf, fieldnames=fieldnames)
                    writer.writeheader()
                    for d in current_rows:
                        writer.writerow(d)
        except Exception as e:
            print('CSV update failed:', e)
    created.append(output_path)

    return created


if __name__ == '__main__':
    # simple CLI to run the processor
    import argparse
    parser = argparse.ArgumentParser(description='Generate reels from CSV hooks')
    parser.add_argument('--csv', help='Path to CSV file', default=None)
    parser.add_argument('--src', help='Source videos directory', default=None)
    parser.add_argument('--out', help='Output directory', default=None)
    parser.add_argument('--music', help='Background music file', default=None)
    parser.add_argument('--rows', help='Number of rows to process', type=int, default=3)
    args = parser.parse_args()
    try:
        created = run_process(csv_path=args.csv, video_src_dir=args.src, target_dir=args.out, music_path=args.music, rows_count=args.rows)
        print('Done. Created:', created)
    except Exception as e:
        print('Processing failed:', e)
 