

# This script automatically generates 20 new videos by randomly selecting and combining two videos 
# from a specified directory for each output. After combining, it overlays a specified audio track (samsmith.mp3), 
# trimming the audio to match the duration of the combined video. The resulting videos are saved in a new combined subdirectory. 
# The script uses the MoviePy library for video and audio processing, ensuring efficient batch creation of multimedia content 
# for your project.



import os
import random
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# Paths
audio_path = r"C:\Users\manar\OneDrive\Documents\FitnessFanatiks\Audio\samsmith.mp3"
videos_dir = r"D:\FitnessFanatiks\Etsy - TheMindsetBoutique\TheMindsetBoutique\videos"
output_dir = os.path.join(videos_dir, "combined")
os.makedirs(output_dir, exist_ok=True)

# Get all video files
video_files = [f for f in os.listdir(videos_dir) if f.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))]

# Load audio once
audio_clip = AudioFileClip(audio_path)

for i in range(1, 21):
    # Pick two random videos
    selected_files = random.sample(video_files, 2)
    clips = [VideoFileClip(os.path.join(videos_dir, f)) for f in selected_files]
    # Combine videos
    combined_clip = concatenate_videoclips(clips, method="compose")
    # Trim audio to combined video duration
    audio_for_video = audio_clip.subclip(0, min(audio_clip.duration, combined_clip.duration))
    # Set audio
    final_clip = combined_clip.set_audio(audio_for_video)
    # Output path
    output_path = os.path.join(output_dir, f"combined_{i:02d}.mp4")
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")
    # Cleanup
    for clip in clips:
        clip.close()
    combined_clip.close()
    final_clip.close()

audio_clip.close()
print("20 combined videos created in:", output_dir)