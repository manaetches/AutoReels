import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q8\magick.exe"})

input_dir = r"D:\wellness\reengineered"
output_dir = r"D:\wellness\reengineered\overlay"
os.makedirs(output_dir, exist_ok=True)

video_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

for filename in video_files:
    video_path = os.path.join(input_dir, filename)
    # Remove "wellness_" and underscores, then strip extension
    base_name = os.path.splitext(filename)[0]
    hook_text = base_name.replace("wellness_", "").replace("_", " ").strip()
    try:
        clip = VideoFileClip(video_path)
        vertical_pos = int(clip.h - clip.h * 0.25)
        txt_clip = TextClip(
            hook_text,
            fontsize=70,
            color='white',
            font='Arial-Bold',
            bg_color='#7c69e3',  # Bright purple
            method='caption',
            size=(clip.w - 100, None)
        ).set_duration(clip.duration).set_position(('center', vertical_pos))
        final = CompositeVideoClip([clip, txt_clip])
        output_path = os.path.join(output_dir, f"{filename}")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()
        clip.close()
        print(f"Overlay added to '{filename}' as '{output_path}'")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

print("All overlays processed and saved to:", output_dir)