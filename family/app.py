#csv_file_path = "Calm_ADHD_Blueprint_Hooks.csv"  # Path updated to same directory
import csv
import os
import textwrap
from moviepy import VideoFileClip, CompositeVideoClip, ImageClip
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Get the absolute path to the CSV file in the same directory as this script
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "Calm_ADHD_Blueprint_Hooks.csv")

# Source and target directories
video_src_dir = r"D:\reels-dev\mixkit\women\family"
target_dir = r"D:\reels-dev\mixkit\women\family\ADHD_output_reel"
os.makedirs(target_dir, exist_ok=True)

# Read first 3 hooks from CSV
hooks = []
with open(csv_file_path, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    header = next(reader)
    for i, row in enumerate(reader):
        if i < 3:
            hooks.append(row[0])  # Only the hook text
        else:
            break

# List video files
video_files = [f for f in os.listdir(video_src_dir) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]
if len(video_files) < 3:
    print("Not enough video files in source directory.")
else:
    for idx, (hook, video_file) in enumerate(zip(hooks, video_files[:3])):
        video_path = os.path.join(video_src_dir, video_file)
        output_path = os.path.join(target_dir, f"hook_overlay_{idx+1}.mp4")
        clip = VideoFileClip(video_path)
        # Create a rounded-corner background image (PIL) with centered text
        def get_font(size=16):
            # Try common Windows font, else fallback to default
            try:
                return ImageFont.truetype("arial.ttf", size)
            except Exception:
                try:
                    return ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", size)
                except Exception:
                    return ImageFont.load_default()

        def make_rounded_text_image(text, max_width, font_size=16, padding=(12,8), radius=3,
                                    bg_color=(255,255,255,255), text_color=(0,0,0,255)):
            font = get_font(font_size)
            # wrap text by measuring
            words = text.split()
            lines = []
            cur = ''
            draw = ImageDraw.Draw(Image.new('RGBA', (10,10)))
            for w in words:
                test = (cur + ' ' + w).strip()
                w_size = draw.textbbox((0,0), test, font=font)[2]
                if w_size <= max_width - 2*padding[0]:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = w
            if cur:
                lines.append(cur)

            # compute text block size
            line_heights = [draw.textbbox((0,0), l, font=font)[3] - draw.textbbox((0,0), l, font=font)[1] for l in lines]
            text_w = 0
            for l in lines:
                bbox = draw.textbbox((0,0), l, font=font)
                text_w = max(text_w, bbox[2]-bbox[0])
            text_h = sum(line_heights) + (len(lines)-1)*4

            img_w = text_w + 2*padding[0]
            img_h = text_h + 2*padding[1]
            img = Image.new('RGBA', (img_w, img_h), (0,0,0,0))
            d = ImageDraw.Draw(img)
            # draw rounded rectangle
            rect = [0,0,img_w,img_h]
            try:
                d.rounded_rectangle(rect, radius=radius, fill=bg_color)
            except Exception:
                # fallback: draw regular rectangle
                d.rectangle(rect, fill=bg_color)

            # draw text
            y = padding[1]
            for i, line in enumerate(lines):
                bbox = d.textbbox((0,0), line, font=font)
                lw = bbox[2]-bbox[0]
                x = (img_w - lw)//2
                d.text((x, y), line, font=font, fill=text_color)
                y += line_heights[i] + 4

            return img

        max_width = int(clip.w * 0.85)
        pil_img = make_rounded_text_image(hook, max_width=max_width, font_size=16, padding=(16,10), radius=3)
        img_clip = ImageClip(np.array(pil_img)).with_position('center').with_duration(clip.duration)
        final = CompositeVideoClip([clip, img_clip])
        final.write_videofile(output_path, codec='libx264', audio_codec='aac')
        print(f"Created: {output_path}")