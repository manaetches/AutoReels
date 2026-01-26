from moviepy.editor import VideoFileClip, AudioFileClip

video_path = r"D:\Travel\Reengineered\travel_Adventure_Awaits_20.mp4"
audio_path = r"D:\Travel\music\travel_audio.mp3"
output_path = r"D:\Travel\Reengineered\travel_Adventure_Awaits_20_with_audio.mp4"

# Load video and audio
video_clip = VideoFileClip(video_path)
audio_clip = AudioFileClip(audio_path).subclip(0, min(AudioFileClip(audio_path).duration, video_clip.duration))

# Set audio to video
final_clip = video_clip.set_audio(audio_clip)
final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

# Cleanup
video_clip.close()
audio_clip.close()
final_clip.close()

print(f"Audio added. Output saved to: {output_path}")