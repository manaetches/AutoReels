import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.config import change_settings

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q8\magick.exe"})

videos_dir = r"D:\Travel"
output_dir = r"D:\Travel\Reengineered"
os.makedirs(output_dir, exist_ok=True)

video_files = [f for f in os.listdir(videos_dir) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

processed_count = 0
output_files = []

for filename in video_files:
    # Only process files whose name (without extension) starts with M-W (case insensitive)
    base_name = os.path.splitext(filename)[0]
    first_letter = base_name[0].upper()
    if first_letter < 'M' or first_letter > 'W':
        continue

    # Remove underscores and numbers from hook name
    hook_words = base_name.replace("_", " ").split()
    hook_words = [word for word in hook_words if not word.isdigit()]
    hook_text = " ".join(hook_words)

    video_path = os.path.join(videos_dir, filename)
    try:
        clip = VideoFileClip(video_path)
        vertical_pos = int(clip.h - clip.h * 0.15)
        txt_clip = TextClip(
            hook_text,
            fontsize=70,
            color='white',
            font='Arial-Bold',
            bg_color='#001f3f',  # Navy blue
            method='caption',
            size=(clip.w - 100, None)
        ).set_duration(clip.duration).set_position(('center', vertical_pos))
        final = CompositeVideoClip([clip, txt_clip])
        output_path = os.path.join(output_dir, f"travel_{filename}")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")
        final.close()
        clip.close()
        processed_count += 1
        output_files.append(output_path)
        print(f"Overlay added to '{filename}' as '{output_path}'")
    except Exception as e:
        print(f"Error processing {filename}: {e}")

print(f"\nTotal videos processed: {processed_count}")
if output_files:
    print("Output files:")
    for out in output_files:
        print(out)
else:
    print("No videos were processed.")