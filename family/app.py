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
import subprocess
import tempfile
import warnings


# Configuration
script_dir = os.path.dirname(os.path.abspath(__file__))
# canonicalize to the AutoReels/family paths so all copies write the same CSV
csv_file_path = r"C:\software\autoreels\AutoReels\family\Calm_ADHD_Blueprint_Hooks2.csv"
video_src_dir = r"D:\reels-dev\mixkit\women\family"
audio_path = r"C:\software\autoreels\AutoReels\family\audio\samsmith.mp3"
target_dir = r"D:\reels-dev\mixkit\output_reel_ADHD"
os.makedirs(target_dir, exist_ok=True)

# debug log
run_log_path = os.path.join(script_dir, 'run_debug.log')
def log(msg):
    try:
        with open(run_log_path, 'a', encoding='utf-8') as lf:
            lf.write(str(msg) + '\n')
    except Exception:
        pass
    try:
        print(msg)
    except Exception:
        pass


# Read CSV rows
rows = []
original_fieldnames = None
log(f"Starting app.py; script_dir={script_dir}")
if os.path.isfile(csv_file_path):
    with open(csv_file_path, mode="r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        original_fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    log(f"Loaded {len(rows)} rows from CSV")
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
    log(f"Found {len(video_files)} video files in {video_src_dir}")
    if len(video_files) > 0:
        log(f"First 5 video files: {video_files[:5]}")
else:
    log(f"Warning: video source directory not found: {video_src_dir}")


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
    try:
        # Always use video files from reels directory (not FilePath from CSV)
        if idx < len(video_files):
            video_path = os.path.join(video_src_dir, video_files[idx])
            log(f"  Input video: {video_path}")
        else:
            log(f"No video available for row {idx+1} (ID={row.get('ID')}) - skipping")
            continue

        row_id = (row.get("ID") or str(idx + 1)).strip()
        lt = (row.get("LongTailKeywords") or "").split(",")[0].strip()
        sanitized = re.sub(r'[^A-Za-z0-9]+', '_', lt).strip('_') or f"row{row_id}"
        output_name = f"{row_id}_{sanitized}.mp4"
        output_path = os.path.join(target_dir, output_name)
        hook = row.get("Hook") or ""
        
        log(f"Processing row {idx+1}/{len(rows)}: ID={row_id}")
    
        # Delete existing output to force regeneration with new settings
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                log(f"  Removed existing file to regenerate")
            except Exception:
                pass

        # Attempt to remux the input with ffmpeg to avoid container/frame-read issues
        remux_path = video_path
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_path)[1], dir=script_dir) as tf:
                tmp_path = tf.name
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                video_path,
                "-c",
                "copy",
                tmp_path,
            ]
            # suppress ffmpeg output; if ffmpeg not available this will raise
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            remux_path = tmp_path
        except Exception:
            # If remux fails, fall back to original path (keep going but warn)
            log(f"ffmpeg remux failed for {video_path}; proceeding with original file")

        clip = VideoFileClip(remux_path)
        # Use source video duration (no trimming or looping)
        target_dur = clip.duration
        log(f"Using source video duration: {target_dur:.2f}s")

        target_w, target_h = 720, 1280
        try:
            # Scale video to fit within target bounds (entire video visible, no cropping)
            scale = min(target_w / clip.w, target_h / clip.h)
            clip = clip.resize(scale)
        except Exception:
            try:
                clip = clip.resize(width=target_w)
            except Exception:
                pass

        # Text width at 40% of target width
        max_width = int(target_w * 0.4)
        pil_img = make_rounded_text_image(hook, max_width=max_width, font_size=20, padding=(16, 10), radius=6, bg_color=(255, 255, 255, 128), text_color=(0,0,0,255), prefix_words=2, prefix_color=(102,0,153,255))
        # Position text overlay at vertical and horizontal center
        img_clip = ImageClip(np.array(pil_img)).with_position(('center', 'center')).with_duration(target_dur)
        # Center video within 720x1280 frame (letterboxing if needed)
        clip_positioned = clip.with_position(('center', 'center')).with_duration(target_dur)
        final = CompositeVideoClip([clip_positioned, img_clip], size=(target_w, target_h), bg_color=(0, 0, 0)).with_duration(target_dur)

        if os.path.isfile(audio_path):
            try:
                audio_clip = AudioFileClip(audio_path)
                # Adjust audio to match source video duration
                orig_audio_dur = getattr(audio_clip, 'duration', 0)
                try:
                    if orig_audio_dur >= target_dur:
                        audio_clip = audio_clip.subclip(0, target_dur)
                        log(f"Audio trimmed from {orig_audio_dur:.2f}s to {target_dur:.2f}s")
                    elif audio_loop is not None:
                        audio_clip = audio_loop(audio_clip, duration=target_dur)
                        log(f"Audio looped from {orig_audio_dur:.2f}s to {target_dur:.2f}s")
                    else:
                        # Use what we have if shorter and looping not available
                        audio_clip = audio_clip.subclip(0, min(orig_audio_dur, target_dur))
                        log(f"Audio duration: {audio_clip.duration:.2f}s (original: {orig_audio_dur:.2f}s)")
                except Exception as e:
                    log(f"Audio duration adjustment failed: {e}")
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
                log(f"Warning: could not load audio {audio_path}: {e}")

        # Ensure final composite matches source video duration
        final = final.with_duration(target_dur)
        log(f"Final video duration set to: {target_dur:.2f}s (actual: {final.duration:.2f}s)")
        
        final.write_videofile(output_path, codec='libx264', audio_codec='aac', fps=30)
        log(f"Created: {output_path}")
        # cleanup remux temp file if created
        try:
            if remux_path != video_path and os.path.exists(remux_path):
                os.remove(remux_path)
        except Exception:
            pass
        # Update CSV with absolute FilePath for this row (atomic write)
        try:
            abs_output = os.path.abspath(output_path)
            rows[idx]['FilePath'] = abs_output
            log(f"Updating CSV: row {idx+1} FilePath = {abs_output}")

            if original_fieldnames:
                base_fns = [fn for fn in original_fieldnames if fn != 'FilePath']
            elif rows:
                base_fns = [k for k in rows[0].keys() if k != 'FilePath']
            else:
                base_fns = ['ID', 'Hook', 'LongTailKeywords']

            insert_index = 4 if len(base_fns) >= 4 else len(base_fns)
            fns = list(base_fns)
            if 'FilePath' in fns:
                fns.remove('FilePath')
            fns.insert(insert_index, 'FilePath')

            tmp_csv = csv_file_path + '.tmp'
            with open(tmp_csv, mode='w', encoding='utf-8', newline='') as wf:
                writer = csv.DictWriter(wf, fieldnames=fns)
                writer.writeheader()
                for r in rows:
                    out = {k: r.get(k, '') for k in fns}
                    # Preserve FilePath from row dict (don't convert empty string to cwd)
                    fp = r.get('FilePath', '')
                    out['FilePath'] = os.path.abspath(fp) if fp else ''
                    writer.writerow(out)
            log(f"Wrote {len(rows)} rows to temp CSV: {tmp_csv}")
            try:
                os.replace(tmp_csv, csv_file_path)
                log(f"CSV file updated successfully: {csv_file_path}")
            except Exception as replace_err:
                log(f"Warning: os.replace failed ({replace_err}), trying remove+replace")
                try:
                    os.remove(csv_file_path)
                except Exception:
                    pass
                os.replace(tmp_csv, csv_file_path)
                log(f"CSV file updated successfully: {csv_file_path}")
            
            # create thumbnail for this output if possible
            try:
                thumbs_dir = os.path.join(target_dir, 'thumbnails')
                os.makedirs(thumbs_dir, exist_ok=True)
                # try to get a frame from the final composite; fallback to source clip
                frame_np = None
                try:
                    frame_np = final.get_frame(0)
                except Exception:
                    try:
                        frame_np = clip.get_frame(0)
                    except Exception:
                        frame_np = None

                if frame_np is not None:
                    try:
                        # Use the original source clip's first frame for the thumbnail when available
                        try:
                            src_frame = clip.get_frame(0)
                        except Exception:
                            src_frame = frame_np

                        thumb_img = Image.fromarray(src_frame.astype('uint8'))
                        if thumb_img.mode != 'RGBA':
                            thumb_img = thumb_img.convert('RGBA')

                        # text: first longtail keyword (or hook fallback)
                        ltk = (row.get('LongTailKeywords') or '').split(',')
                        text = ltk[0].strip() if ltk and ltk[0].strip() else (row.get('Hook') or '')

                        # target: text wraps to 3 words per line and occupies up to 75% width
                        max_text_width = int(thumb_img.width * 0.75)
                        # start with a very large font and scale down as needed
                        target_font_size = max(32, int(thumb_img.width * 0.95))

                        # uppercase the text and prepare wrapped lines (3 words per line)
                        text = (text or '').upper()
                        words = [w for w in text.split() if w]
                        if words:
                            lines = [ ' '.join(words[i:i+3]) for i in range(0, len(words), 3) ]

                            # pick starting font and measure each line
                            font_size = target_font_size
                            font = get_font_variant(font_size, bold=True)
                            measure = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
                            md = ImageDraw.Draw(measure)

                            line_widths = []
                            line_heights = []
                            for ln in lines:
                                bb = md.textbbox((0,0), ln, font=font)
                                w = bb[2] - bb[0]
                                h = bb[3] - bb[1]
                                line_widths.append(w)
                                line_heights.append(h)

                            max_line_w = max(line_widths)
                            # if the widest line exceeds allowed width, scale font down
                            if max_line_w > 0 and max_line_w > max_text_width:
                                scale_factor = max_text_width / float(max_line_w)
                                font_size = max(10, int(font_size * scale_factor))
                                font = get_font_variant(font_size, bold=True)
                                line_widths = []
                                line_heights = []
                                for ln in lines:
                                    bb = md.textbbox((0,0), ln, font=font)
                                    line_widths.append(bb[2]-bb[0])
                                    line_heights.append(bb[3]-bb[1])
                                max_line_w = max(line_widths)

                            # line-height increase by 30%
                            base_line_h = int(sum(line_heights) / float(len(line_heights))) if line_heights else font_size
                            line_height = int(round(base_line_h * 1.3))

                            pad_x, pad_y = 12, 8
                            rect_w = max_line_w + pad_x * 2
                            rect_h = line_height * len(lines) + pad_y * 2

                            # stroke width proportional to font size
                            stroke_w = max(2, int(round(font_size * 0.12)))

                            # create text layer and draw each wrapped line centered in the layer
                            text_layer = Image.new('RGBA', (rect_w, rect_h), (0,0,0,0))
                            td = ImageDraw.Draw(text_layer)
                            try:
                                for idx_line, ln in enumerate(lines):
                                    lw = line_widths[idx_line]
                                    x = (rect_w - lw) // 2
                                    y = pad_y + idx_line * line_height
                                    td.text((x, y), ln, font=font, fill=(48,0,96,255), stroke_width=stroke_w, stroke_fill=(200,200,200,255))
                            except TypeError:
                                # fallback outline emulation per-line
                                sw = int(stroke_w)
                                for idx_line, ln in enumerate(lines):
                                    lw = line_widths[idx_line]
                                    x = (rect_w - lw) // 2
                                    y = pad_y + idx_line * line_height
                                    ox = [(-sw,0),(sw,0),(0,-sw),(0,sw),(-sw,-sw),(sw,sw),(-sw,sw),(sw,-sw)]
                                    for dx,dy in ox:
                                        td.text((x+dx, y+dy), ln, font=font, fill=(200,200,200,255))
                                    td.text((x, y), ln, font=font, fill=(48,0,96,255))

                            # rotate the text layer 30 degrees and paste centered
                            rotated = text_layer.rotate(30, expand=True, resample=Image.BICUBIC)
                            tx = (thumb_img.width - rotated.width) // 2
                            ty = (thumb_img.height - rotated.height) // 2
                            thumb_img.paste(rotated, (tx, ty), rotated)

                            out_name = os.path.splitext(os.path.basename(output_path))[0] + '.jpg'
                            out_path = os.path.join(thumbs_dir, out_name)
                            thumb_img.convert('RGB').save(out_path, quality=90)
                            log(f"Thumbnail created: {out_path}")
                    except Exception as e:
                        log(f"Warning: could not create thumbnail for {output_path}: {e}")
                else:
                    log(f"No frame available to create thumbnail for {output_path}")
            except Exception as e:
                log(f"Warning: thumbnail step failed for {output_path}: {e}")
            
            log(f"CSV updated with FilePath: {abs_output}")
        except Exception as e:
            log(f"Error in CSV update or thumbnail: {e}")
            import traceback
            log(traceback.format_exc())
    except Exception as e:
        log(f"Error processing row {idx+1} (ID={row.get('ID', 'unknown')}): {e}")
        import traceback
        log(traceback.format_exc())
        continue


log(f"\n{'='*60}")
log(f"Processing complete!")
log(f"Total rows in CSV: {len(rows)}")
log(f"Total video files available: {len(video_files)}")
log(f"Check {target_dir} for output videos")
log(f"Check {os.path.join(target_dir, 'thumbnails')} for thumbnails")
log(f"Check {csv_file_path} for updated FilePath column")
log(f"{'='*60}")