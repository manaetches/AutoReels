#!/usr/bin/env python3
"""
FACELESS VIDEO GENERATOR - Reels Automation
============================================
Randomly sources video clips, overlays text hooks from CSV, combines with background audio,
and adds AI voiceover narration. Perfect for creating engaging social media reels at scale.

Features:
- Random video clip selection from source directory
- Multi-hook support (Hook1, Hook2, Hook3, Hook4, Hook5, Hook6)
- Background music integration
- TTS voiceover narration
- Customizable text overlays with animations
- Batch processing with progress tracking
"""

import csv
import os
import re
import random
from pathlib import Path

try:
    from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips
except Exception:
    from moviepy import VideoFileClip, CompositeVideoClip, ImageClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips
try:
    from moviepy.audio.fx.all import audio_loop, volumex
except Exception:
    audio_loop = None
    volumex = None

import wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# =============================================================================
# TTS ENGINE PREFERENCE
# =============================================================================
# Force specific TTS engine: "piper", "gtts", "pyttsx3", "edge-tts", "elevenlabs", or "auto" for automatic selection
# elevenlabs = ElevenLabs AI (online, BEST QUALITY, requires API key)
# piper = Piper TTS (offline, NATURAL MALE VOICE - Joe, smooth professional tone)
# gtts = Google TTS (online, reliable, good quality, neutral voice)
# pyttsx3 = Offline TTS (uses Windows voices, fast but limited voices)
# edge-tts = Microsoft Edge TTS (online, high quality but connection issues)
PREFERRED_TTS_ENGINE = "elevenlabs"  # Using ElevenLabs for best quality voiceover

# Optional TTS support - install with: pip install pyttsx3 gtts edge-tts
print("\n" + "="*60)
print("INITIALIZING TTS ENGINES")
print("="*60)

TTS_ENGINE = None
PYTTSX3_AVAILABLE = False
GTTS_AVAILABLE = False
EDGE_TTS_AVAILABLE = False
COQUI_TTS_AVAILABLE = False
PIPER_TTS_AVAILABLE = False
ELEVENLABS_AVAILABLE = False
pyttsx3 = None
gTTS = None
edge_tts = None
TTS = None
PiperVoice = None
ElevenLabs = None

try:
    import pyttsx3 as pyttsx3_module
    pyttsx3 = pyttsx3_module
    PYTTSX3_AVAILABLE = True
    print("✓ pyttsx3 library imported successfully")
except ImportError as e:
    print(f"⚠ pyttsx3 import failed: {e}")

try:
    from gtts import gTTS as gTTS_class
    gTTS = gTTS_class
    GTTS_AVAILABLE = True
    print("✓ gTTS library imported successfully")
except ImportError as e:
    print(f"⚠ gTTS import failed: {e}")

try:
    import edge_tts as edge_tts_module
    edge_tts = edge_tts_module
    EDGE_TTS_AVAILABLE = True
    print("✓ edge-tts library imported successfully (Microsoft Edge TTS with natural voices)")
except ImportError as e:
    print(f"⚠ edge-tts import failed: {e}")

try:
    from TTS.api import TTS as CoquiTTS
    TTS = CoquiTTS
    COQUI_TTS_AVAILABLE = True
    print("✓ Coqui TTS library imported successfully (High-quality neural TTS with male voices)")
except ImportError as e:
    print(f"⚠ Coqui TTS import failed: {e}")

try:
    from piper import PiperVoice as PiperVoiceClass
    PiperVoice = PiperVoiceClass
    PIPER_TTS_AVAILABLE = True
    print("✓ Piper TTS library imported successfully (Deep male voice - offline)")
except ImportError as e:
    print(f"⚠ Piper TTS import failed: {e}")

try:
    from elevenlabs import ElevenLabs as ElevenLabsClient
    ElevenLabs = ElevenLabsClient
    ELEVENLABS_AVAILABLE = True
    print("✓ ElevenLabs library imported successfully (BEST quality AI voices - online)")
except ImportError as e:
    print(f"⚠ ElevenLabs import failed: {e}")

print(f"\nLibrary availability:")
print(f"  - pyttsx3: {PYTTSX3_AVAILABLE}")
print(f"  - gTTS: {GTTS_AVAILABLE}")
print(f"  - edge-tts: {EDGE_TTS_AVAILABLE}")
print(f"  - piper-tts: {PIPER_TTS_AVAILABLE}")
print(f"  - elevenlabs: {ELEVENLABS_AVAILABLE}")

# Check for male voices in pyttsx3
has_male_voice = False
if PYTTSX3_AVAILABLE:
    try:
        print("\n  Testing pyttsx3 initialization...")
        test_engine = pyttsx3.init()
        
        # List available voices
        voices = test_engine.getProperty('voices')
        print(f"\n  Available pyttsx3 voices ({len(voices)} total):")
        for idx, voice in enumerate(voices):
            print(f"    [{idx}] {voice.name}")
            voice_lower = voice.name.lower()
            if any(keyword in voice_lower for keyword in ["david", "mark", "male", "guy", "ryan"]):
                print(f"        *** MALE VOICE ***")
                has_male_voice = True
        
        test_engine.stop()
        del test_engine
    except Exception as e:
        print(f"  ✗ pyttsx3 failed to initialize: {type(e).__name__}: {e}")

# Select best TTS engine based on preference and availability
if PREFERRED_TTS_ENGINE and PREFERRED_TTS_ENGINE != "auto":
    # Manual selection
    if PREFERRED_TTS_ENGINE == "elevenlabs" and ELEVENLABS_AVAILABLE:
        TTS_ENGINE = "elevenlabs"
        print(f"\n  ✓ Using ElevenLabs (online AI voices - BEST quality for professional content)")
    elif PREFERRED_TTS_ENGINE == "piper" and PIPER_TTS_AVAILABLE:
        TTS_ENGINE = "piper"
        print(f"\n  ✓ Using Piper TTS (offline natural male voice - BEST for professional narration)")
    elif PREFERRED_TTS_ENGINE == "coqui" and COQUI_TTS_AVAILABLE:
        TTS_ENGINE = "coqui"
        print(f"\n  ✓ Using Coqui TTS (offline neural TTS - BEST quality with male voices)")
    elif PREFERRED_TTS_ENGINE == "gtts" and GTTS_AVAILABLE:
        TTS_ENGINE = "gtts"
        print(f"\n  ✓ Using gTTS (online TTS - manual preference)")
    elif PREFERRED_TTS_ENGINE == "pyttsx3" and PYTTSX3_AVAILABLE:
        TTS_ENGINE = "pyttsx3"
        print(f"\n  ✓ Using pyttsx3 (offline TTS - manual preference)")
    elif PREFERRED_TTS_ENGINE == "edge-tts" and EDGE_TTS_AVAILABLE:
        TTS_ENGINE = "edge-tts"
        print(f"\n  ✓ Using edge-tts (Microsoft Edge TTS - manual preference)")
    else:
        print(f"\n  ✗ CRITICAL: Preferred engine '{PREFERRED_TTS_ENGINE}' not available!")
        print(f"\n  ✗ CRITICAL: Script is configured for ElevenLabs ONLY - no fallback allowed")
        if PREFERRED_TTS_ENGINE == "elevenlabs":
            print(f"\n  ✗ Make sure ElevenLabs is installed: pip install elevenlabs")
            print(f"\n  ✗ Make sure API key has text_to_speech permission")
        raise Exception(f"Required TTS engine '{PREFERRED_TTS_ENGINE}' is not available. Stopping.")
else:
    # Automatic selection - ElevenLabs ONLY policy
    if ELEVENLABS_AVAILABLE:
        TTS_ENGINE = "elevenlabs"
        print(f"\n  ✓ Using ElevenLabs (online AI voices - BEST quality)")
    else:
        print(f"\n  ✗ CRITICAL: ElevenLabs is not available!")
        print(f"\n  ✗ CRITICAL: Script is configured for ElevenLabs ONLY - no fallback to other engines")
        print(f"\n  ✗ Install ElevenLabs: pip install elevenlabs")
        print(f"\n  ✗ Make sure API key has text_to_speech permission")
        raise Exception("ElevenLabs is not available. No fallback allowed. Stopping.")

print(f"\n✓ Selected TTS Engine: {TTS_ENGINE}")

if not TTS_ENGINE:
    print("\n" + "!"*60)
    print("⚠ WARNING: No working TTS engine found!")
    print("  Install with: pip install pyttsx3 gtts")
    print("!"*60)

print("="*60 + "\n")

# =============================================================================
# CONFIGURATION - Customize Your Video Generation Here
# =============================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(script_dir, "mom_fitness_motivation2.csv")
video_src_dir = r"D:\reels-dev\mixkit\fitness\fit_moms"
audio_path = r"D:\reels-dev\mixkit\music\gym.wav"
target_dir = r"D:\reels-dev\mixkit\fitness\fit_moms\faceless_videos"
os.makedirs(target_dir, exist_ok=True)

# =============================================================================
# CONTROLS - Video Generation Parameters
# =============================================================================

# === VIDEO GENERATION CONTROLS ===
MAX_VIDEOS_TO_GENERATE = 60  # Set to integer (e.g., 10, 50, 100) or None for all CSV rows
SHUFFLE_CSV_ROWS = False  # Randomize the order of CSV rows before processing

# === VIDEO CLIP CONTROLS ===
RANDOM_VIDEO_SELECTION = True  # True: random clips per video | False: sequential
ALLOW_VIDEO_REUSE = True  # Allow same video to be used multiple times if needed
TARGET_VIDEO_DURATION = 40  # Final video duration in seconds (e.g., 15, 30, 40, 60)
MAX_SEGMENT_DURATION = 5  # Maximum duration per segment/clip in seconds (each gets different Hook)
CLIP_DURATION_RANGE = (4, 5)  # Min/max seconds per clip when assembling from multiple clips

# === SEGMENT STRUCTURE CONTROLS ===
SEGMENT_MODE = "match_hooks"  # Options: "match_hooks", "fixed_duration"
                              # "match_hooks" = number of segments matches number of available hooks (e.g., 8 hooks = 8 segments, duration divided evenly)
                              # "fixed_duration" = segments use MAX_SEGMENT_DURATION, allowing hook repetition for longer videos
                              # Example: 40s video with 8 hooks → "match_hooks" = 8 segments of 5s each, "fixed_duration" = 8 segments of 5s

# === HOOK TEXT CONTROLS ===
HOOK_SELECTION = "rotate"  # Options: "Hook1", "Hook2", "Hook3", "Hook4", "Hook5", "Hook6", "Hook7", "Hook8", "random", "rotate"
                          # "random" = pick random hook for each video
                          # "rotate" = cycle through all available hooks sequentially (Hook1->Hook2->...->Hook8)
USE_NARRATIVE_FOR_TTS = False  # Not used in multi-segment mode (uses Hook text for each segment)

# === AUDIO CONTROLS ===
ENABLE_BACKGROUND_MUSIC = True  # Toggle background music on/off
BACKGROUND_MUSIC_VOLUME = 0.0001  # 0.0 to 1.0 (0.5% = 0.005 for very subtle background, 1% = 0.01, 10% = 0.1, 100% = 1.0)
AUDIO_START_OFFSET = 0  # Start background audio X seconds into the video (for sync)
ENABLE_VOICEOVER = True  # Toggle AI voiceover narration on/off
VOICEOVER_VOLUME = 1.5  # 0.0 to 1.0 (100% = 1.0)
TTS_VOICE_SPEED = 160  # Words per minute for pyttsx3 (default: 150-200, slower = more natural)
TTS_VOICE_GENDER = "male"  # Voice gender: "male" or "female"
TTS_VOICE_INDEX = None  # Specific voice index (0, 1, 2...) or None for auto-select by gender (pyttsx3 only)
TTS_LANGUAGE = "en"  # Language code for gTTS (e.g., "en", "es", "fr")
# Edge-TTS voices (high quality neural voices from Microsoft Edge)
# Male voices: "en-US-GuyNeural" (default male), "en-US-DavisNeural" (professional), "en-GB-RyanNeural" (British)
# Female voices: "en-US-JennyNeural" (default female), "en-US-AriaNeural" (expressive)
EDGE_TTS_VOICE = "en-US-DavisNeural"  # Used when TTS_ENGINE is "edge-tts"

# === ELEVENLABS API CONFIGURATION ===
ELEVENLABS_API_KEY = "sk_fbf41ffad60809a6d440367d6d2a6fc1f16f961e5e198955"  # Your ElevenLabs API key
# Popular ElevenLabs STANDARD voices (work with free tier):
# "pNInz6obpgDQGcFmaJgB" - Adam - Deep, authoritative male (great for narration)
# "ErXwobaYiN019PkySvjV" - Antoni - Well-rounded male
# "VR6AewLTigWG4xSOukaG" - Arnold - Crisp, strong male  
# "N2lVS1w4EtoT3dr4eOWO" - Callum - Smooth, professional male
# "IKne3meq5aSn9XLyUdCD" - Charlie - Natural, conversational male
# "TxGEqnHWrfWFTfGW9XjX" - Josh - Professional, clear male (news anchor style)
# Library/cloned voices require paid subscription!
ELEVENLABS_VOICE = "pNInz6obpgDQGcFmaJgB"  # Adam - Standard voice (works with free tier)
ELEVENLABS_MODEL = "eleven_multilingual_v2"  # "eleven_monolingual_v1" or "eleven_multilingual_v2"

# === TEXT OVERLAY CONTROLS ===
TEXT_OVERLAY_ENABLED = True  # Show text overlay on video
TEXT_POSITION = ('center', 'top')  # Position tuple: (horizontal, vertical) - 'left'/'center'/'right', 'top'/'center'/'bottom'
TEXT_POSITION_OFFSET = (0, 480)  # Offset in pixels (horizontal, vertical) from TEXT_POSITION
TEXT_CUSTOM_POSITION = None  # Override with (x, y) pixel coordinates or None
TEXT_WIDTH_PERCENT = 0.85  # Text width as percentage of video width (0.85 = 85%)
FONT_SIZE = 40  # Base font size for text overlay
FONT_FAMILY = "arial"  # Font family: "arial", "impact", "times", etc.
FONT_COLOR = (0, 0, 0, 255)  # RGBA color tuple (black = 0,0,0,255)
FONT_BG_COLOR = (255, 255, 255, 200)  # RGBA background color (white semi-transparent)
PREFIX_WORDS = 2  # Number of initial words to highlight in different color
PREFIX_COLOR = (102, 0, 153, 255)  # RGBA color for prefix words (purple)
TEXT_PADDING = (24, 16)  # Padding around text (horizontal, vertical) in pixels
TEXT_BORDER_RADIUS = 10  # Border radius for rounded text background

# === TITLE OVERLAY CONTROLS ===
TITLE_OVERLAY_ENABLED = True  # Show title overlay on video
TITLE_POSITION = ('center', 'top')  # Position tuple: (horizontal, vertical)
TITLE_POSITION_OFFSET = (0, 200)  # Offset in pixels (horizontal, vertical) from top
TITLE_WIDTH_PERCENT = 0.80  # Title width as percentage of video width
TITLE_FONT_SIZE = 48  # Font size for title
TITLE_FONT_FAMILY = "arial"  # Font family for title
TITLE_FONT_COLOR = (255, 255, 255, 255)  # White color for title text
TITLE_FONT_WEIGHT = "bold"  # Bold font weight (note: simulated with font rendering)
TITLE_BG_COLOR = None  # No background for title (None or RGBA tuple like (0, 0, 0, 180))
TITLE_PADDING = (20, 12)  # Padding around title text if background is used
TITLE_BORDER_RADIUS = 8  # Border radius if background is used

# === ANIMATION CONTROLS ===
TEXT_FADE_IN_DURATION = 0.5  # Text fade-in duration in seconds (0 = instant)
TEXT_FADE_OUT_DURATION = 0.5  # Text fade-out duration in seconds (0 = instant)
VIDEO_CROSSFADE_DURATION = 2.0  # Crossfade/dissolve transition between video segments in seconds (0 = cut, 2.0 = smooth fade)

# === OUTPUT CONTROLS ===
OUTPUT_FPS = 30  # Frames per second for output video (24, 30, 60)
OUTPUT_RESOLUTION = (1080, 1920)  # Portrait (width, height) - 9:16 aspect ratio
VIDEO_CODEC = 'libx264'  # Video codec: 'libx264' (h264), 'libx265' (h265/HEVC)
AUDIO_CODEC = 'aac'  # Audio codec: 'aac', 'mp3'
BITRATE = "8000k"  # Video bitrate for quality (e.g., "5000k", "8000k", "12000k")
OUTPUT_FILENAME_PREFIX = "fit_moms_"  # Prefix for output filenames (e.g., "fit_moms_" → "fit_moms_15_min_rule.mp4")

# === ROW PROCESSING RANGE ===
ROW_START = 48   # Start processing from this row number (1-based, 1 = first data row)
ROW_END = None  # End processing at this row number (1-based, None = process all remaining rows)
# Example: ROW_START = 3, ROW_END = 30 will process rows 3 through 30


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_voiceover_audio(text, output_path, engine=None):
    """
    Generate voiceover audio from text using TTS.
    Returns path to generated audio file or None if failed.
    """
    # Use global TTS_ENGINE if not specified
    if engine is None:
        engine = TTS_ENGINE
        
    print(f"      🔧 generate_voiceover_audio called:")
    print(f"         Engine: {engine}")
    print(f"         ENABLE_VOICEOVER: {ENABLE_VOICEOVER}")
    print(f"         Text length: {len(text)} chars")
    print(f"         Output path: {output_path}")
    
    if not engine or not ENABLE_VOICEOVER:
        print(f"         ⚠ Skipping - engine={engine}, ENABLE_VOICEOVER={ENABLE_VOICEOVER}")
        return None
        
    try:
        if engine == "elevenlabs":
            # ElevenLabs AI TTS (best quality, online, requires API key)
            print(f"         → Using ElevenLabs (Premium AI Voiceover)...")
            if not ELEVENLABS_AVAILABLE or ElevenLabs is None:
                print(f"         ✗ ElevenLabs not available!")
                print(f"         ✗ CRITICAL: ElevenLabs library not imported. Install with: pip install elevenlabs")
                raise Exception("ElevenLabs is not available. No fallback allowed.")
            
            if not ELEVENLABS_API_KEY:
                print(f"         ✗ ElevenLabs API key not set!")
                print(f"         → Get your API key from: https://elevenlabs.io/app/settings/api-keys")
                print(f"         → Set ELEVENLABS_API_KEY in script or environment variable")
                print(f"         ✗ CRITICAL: Cannot proceed without valid ElevenLabs API key")
                raise Exception("ElevenLabs API key missing. No fallback allowed.")
            
            try:
                # Initialize ElevenLabs client
                client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
                print(f"         → Client initialized with voice: {ELEVENLABS_VOICE}")
                
                # Generate audio using ElevenLabs API
                print(f"         → Generating audio with model: {ELEVENLABS_MODEL}...")
                audio_generator = client.text_to_speech.convert(
                    text=text,
                    voice_id=ELEVENLABS_VOICE,
                    model_id=ELEVENLABS_MODEL
                )
                
                # Stream audio chunks to file
                output_path_mp3 = output_path.replace(".wav", ".mp3")
                with open(output_path_mp3, 'wb') as audio_file:
                    for chunk in audio_generator:
                        audio_file.write(chunk)
                
                print(f"         → Audio generated successfully")
                
                # Verify file was created
                if os.path.exists(output_path_mp3):
                    file_size = os.path.getsize(output_path_mp3)
                    print(f"         → File created: {file_size} bytes")
                    if file_size > 1000:  # At least 1KB
                        print(f"         ✓ Using ElevenLabs premium AI voice ({ELEVENLABS_VOICE})")
                        return output_path_mp3
                    else:
                        print(f"         ✗ CRITICAL: Audio file too small ({file_size} bytes)")
                        raise Exception(f"ElevenLabs generated invalid audio file. No fallback allowed.")
                else:
                    print(f"         ✗ CRITICAL: Audio file not created")
                    raise Exception("ElevenLabs failed to create audio file. No fallback allowed.")
                
            except Exception as e:
                print(f"         ✗ ElevenLabs API error: {type(e).__name__}: {str(e)[:200]}")
                print(f"         ✗ CRITICAL: Check your API key and internet connection")
                print(f"         ✗ CRITICAL: No fallback to other TTS engines allowed")
                raise  # Re-raise the exception to stop execution
        
        elif engine == "pyttsx3":
            # Offline TTS engine (faster, no internet needed)
            print(f"         → Using pyttsx3...")
            if not PYTTSX3_AVAILABLE or pyttsx3 is None:
                print(f"         ✗ pyttsx3 not available!")
                return None
                
            tts_engine = None
            try:
                tts_engine = pyttsx3.init()
                print(f"         → pyttsx3 initialized")
                
                # Set voice - prioritize David for male narration
                voices = tts_engine.getProperty('voices')
                print(f"         → Available voices: {len(voices)}")
                
                if TTS_VOICE_INDEX is not None and TTS_VOICE_INDEX < len(voices):
                    tts_engine.setProperty('voice', voices[TTS_VOICE_INDEX].id)
                    print(f"         → Voice set to index {TTS_VOICE_INDEX}: {voices[TTS_VOICE_INDEX].name}")
                elif TTS_VOICE_GENDER and voices:
                    # Auto-select by gender - prioritize David for male
                    selected_voice = None
                    
                    if TTS_VOICE_GENDER.lower() == "male":
                        # Priority 1: David (most natural male voice on Windows)
                        for voice in voices:
                            if "david" in voice.name.lower():
                                selected_voice = voice
                                print(f"         → Found David voice: {voice.name}")
                                break
                        
                        # Priority 2: Other male voices
                        if not selected_voice:
                            for voice in voices:
                                voice_lower = voice.name.lower()
                                if "mark" in voice_lower or "male" in voice_lower or "man" in voice_lower:
                                    selected_voice = voice
                                    print(f"         → Found male voice: {voice.name}")
                                    break
                    
                    elif TTS_VOICE_GENDER.lower() == "female":
                        for voice in voices:
                            voice_lower = voice.name.lower()
                            if "zira" in voice_lower or "hazel" in voice_lower or "female" in voice_lower or "woman" in voice_lower:
                                selected_voice = voice
                                print(f"         → Found female voice: {voice.name}")
                                break
                    
                    if selected_voice:
                        tts_engine.setProperty('voice', selected_voice.id)
                        print(f"         ✓ Using {TTS_VOICE_GENDER} narrator: {selected_voice.name}")
                    else:
                        # Fallback: use first voice
                        print(f"         ⚠ No {TTS_VOICE_GENDER} voice found, using default: {voices[0].name if voices else 'default'}")
                
                tts_engine.setProperty('rate', TTS_VOICE_SPEED)
                tts_engine.setProperty('volume', VOICEOVER_VOLUME)
                print(f"         → Properties set (rate={TTS_VOICE_SPEED}, volume={VOICEOVER_VOLUME})")
                tts_engine.save_to_file(text, output_path)
                print(f"         → save_to_file() called")
                tts_engine.runAndWait()
                print(f"         → runAndWait() completed")
            finally:
                # Properly dispose of engine
                if tts_engine:
                    try:
                        tts_engine.stop()
                        del tts_engine
                    except:
                        pass
            
            # Give the file system a moment to finalize
            import time
            time.sleep(0.1)
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"         → File created: {file_size} bytes")
                if file_size > 0:
                    return output_path
                else:
                    print(f"      ⚠ Audio file created but empty: {output_path}")
                    return None
            else:
                print(f"      ⚠ Audio file not created: {output_path}")
                return None
            
        elif engine == "gtts":
            # Online TTS engine (reliable, requires internet)
            print(f"         → Using gTTS...")
            if not GTTS_AVAILABLE or gTTS is None:
                print(f"         ✗ gTTS not available!")
                return None
                
            # Use slow=False for natural pace (slow=True makes it too slow)
            tts = gTTS(text=text, lang=TTS_LANGUAGE, slow=False)
            print(f"         → gTTS object created")
            tts.save(output_path)
            print(f"         → save() completed")
            print(f"         → save() completed")
            
            # Verify file was created
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"         → File created: {file_size} bytes")
                if file_size > 0:
                    return output_path
                else:
                    print(f"      ⚠ Audio file created but empty: {output_path}")
                    return None
            else:
                print(f"      ⚠ Audio file not created: {output_path}")
                return None
                
        elif engine == "piper":
            # Piper TTS (high quality natural male voice, offline)
            print(f"         → Using Piper TTS (Natural Male Voice - Joe)...")
            if not PIPER_TTS_AVAILABLE or PiperVoice is None:
                print(f"         ✗ Piper TTS not available!")
                # Fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
            
            try:
                # Load Piper voice model (Joe - natural male voice)
                model_path = os.path.join(os.path.dirname(__file__), "piper_voices", "en_US-joe-medium.onnx")
                if not os.path.exists(model_path):
                    print(f"         ✗ Piper voice model not found: {model_path}")
                    if GTTS_AVAILABLE:
                        print(f"         → Falling back to gTTS...")
                        return generate_voiceover_audio(text, output_path, engine="gtts")
                    return None
                
                print(f"         → Loading voice model...")
                voice = PiperVoice.load(model_path)
                
                # Change output to WAV (Piper generates WAV)
                output_path_wav = output_path.replace(".mp3", ".wav")
                
                print(f"         → Synthesizing audio...")
                with wave.open(output_path_wav, 'wb') as wav_file:
                    voice.synthesize_wav(text, wav_file)
                
                # Verify file was created
                if os.path.exists(output_path_wav):
                    file_size = os.path.getsize(output_path_wav)
                    print(f"         → Audio generated: {file_size} bytes")
                    if file_size > 1000:  # At least 1KB
                        print(f"         ✓ Using Piper TTS natural male voice (Joe)")
                        return output_path_wav
                    else:
                        print(f"      ⚠ Audio file too small")
                        if GTTS_AVAILABLE:
                            print(f"         → Falling back to gTTS...")
                            return generate_voiceover_audio(text, output_path, engine="gtts")
                        return None
                else:
                    print(f"      ⚠ Audio file not created")
                    if GTTS_AVAILABLE:
                        print(f"         → Falling back to gTTS...")
                        return generate_voiceover_audio(text, output_path, engine="gtts")
                    return None
                
            except Exception as e:
                print(f"         ✗ Piper TTS error: {type(e).__name__}: {str(e)[:100]}")
                # Fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
        
        elif engine == "coqui":
            # Coqui TTS (high quality neural voices, offline)
            print(f"         → Using Coqui TTS (Neural TTS)...")
            if not COQUI_TTS_AVAILABLE or TTS is None:
                print(f"         ✗ Coqui TTS not available!")
                # Fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
            
            try:
                # Initialize Coqui TTS with a male voice model
                print(f"         → Loading Coqui TTS model (first time takes a moment)...")
                # Use VCTK model which has multiple speakers including males
                tts_model = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False, gpu=False)
                
                # Select a male speaker (p243, p245, p246, p247 are good male voices)
                # p243 = Adult male, clear and professional
                speaker = "p243"
                print(f"         → Using speaker: {speaker} (professional male voice)")
                
                # Generate audio
                tts_model.tts_to_file(text=text, file_path=output_path, speaker=speaker)
                print(f"         → Audio generated successfully")
                
                # Verify file was created
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    print(f"         → File created: {file_size} bytes")
                    if file_size > 0:
                        print(f"         ✓ Using Coqui TTS deep male voice")
                        return output_path
                    else:
                        print(f"      ⚠ Audio file created but empty")
                        if GTTS_AVAILABLE:
                            print(f"         → Falling back to gTTS...")
                            return generate_voiceover_audio(text, output_path, engine="gtts")
                        return None
                else:
                    print(f"      ⚠ Audio file not created")
                    if GTTS_AVAILABLE:
                        print(f"         → Falling back to gTTS...")
                        return generate_voiceover_audio(text, output_path, engine="gtts")
                    return None
                
            except Exception as e:
                print(f"         ✗ Coqui TTS error: {type(e).__name__}: {str(e)[:100]}")
                # Fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
                
        elif engine == "edge-tts":
            # Microsoft Edge TTS (high quality neural voices, requires internet)
            print(f"         → Using edge-tts (Microsoft Edge Neural TTS)...")
            if not EDGE_TTS_AVAILABLE or edge_tts is None:
                print(f"         ✗ edge-tts not available!")
                # Fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
            
            import asyncio
            import sys
            
            # Handle asyncio event loop on Windows
            if sys.platform == 'win32':
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                except Exception:
                    pass
            
            async def _generate_edge_tts():
                """Async function to generate edge-tts audio"""
                voice = EDGE_TTS_VOICE
                print(f"         → Voice: {voice} (deep professional male)")
                print(f"         → Generating audio...")
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)
                print(f"         → Audio saved successfully")
            
            # Run the async function with retry and fallback
            edge_tts_success = False
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(_generate_edge_tts())
                    edge_tts_success = True
                finally:
                    loop.close()
                print(f"         ✓ edge-tts generation completed")
            except Exception as e:
                error_name = type(e).__name__
                print(f"         ✗ edge-tts error: {error_name}: {str(e)[:100]}")
                
                # If edge-tts fails, fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS (edge-tts connection failed)...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
            
            # Give the file system a moment to finalize
            import time
            time.sleep(0.2)
            
            # Verify file was created and has content
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"         → File created: {file_size} bytes")
                if file_size > 0:
                    print(f"         ✓ Using Microsoft Edge voice: {EDGE_TTS_VOICE}")
                    return output_path
                else:
                    print(f"      ⚠ Audio file created but empty (0 bytes)")
                    # Fallback to gTTS
                    if GTTS_AVAILABLE:
                        print(f"         → Falling back to gTTS...")
                        return generate_voiceover_audio(text, output_path, engine="gtts")
                    return None
            else:
                print(f"      ⚠ Audio file not created")
                # Fallback to gTTS
                if GTTS_AVAILABLE:
                    print(f"         → Falling back to gTTS...")
                    return generate_voiceover_audio(text, output_path, engine="gtts")
                return None
                
        else:
            print(f"      ⚠ Unknown TTS engine: {engine}")
            return None
            
    except Exception as e:
        print(f"      ⚠ TTS generation error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None


def select_hook_text(row, hook_mode, iteration=0):
    """
    Select appropriate hook text based on HOOK_SELECTION mode.
    Returns the selected hook text.
    """
    # Handle tuple/list (use first element) - common config error
    if isinstance(hook_mode, (tuple, list)):
        hook_mode = hook_mode[0] if hook_mode else "Hook1"
    
    if hook_mode == "random":
        # Randomly pick from available hooks
        available_hooks = [row.get(f"Hook{i}", "").strip() for i in range(1, 9)]  # Support up to Hook8
        available_hooks = [h for h in available_hooks if h]
        return random.choice(available_hooks) if available_hooks else ""
        
    elif hook_mode == "rotate":
        # Cycle through all available hooks dynamically
        available_hooks = [row.get(f"Hook{i}", "").strip() for i in range(1, 9) if row.get(f"Hook{i}", "").strip()]
        if available_hooks:
            hook_idx = iteration % len(available_hooks)
            return available_hooks[hook_idx]
        return ""
        
    else:
        # Specific hook (Hook1, Hook2, Hook3, Hook4, Hook5, Hook6, Hook7, or Hook8)
        return row.get(hook_mode, "").strip()


def get_random_videos(video_files, count=1, allow_reuse=True):
    """
    Get random video files from available pool.
    """
    if not video_files:
        return []
    
    if allow_reuse or count <= len(video_files):
        return random.sample(video_files, min(count, len(video_files))) if not allow_reuse else random.choices(video_files, k=count)
    else:
        # Not enough unique videos, return what we have
        return video_files.copy()


def calculate_position_with_offset(base_position, offset=(0, 0), clip_size=None, canvas_size=None):
    """
    Calculate position with offset applied.
    
    Args:
        base_position: Tuple of (horizontal, vertical) - can be strings like 'center', 'top' or pixel values
        offset: Tuple of (x_offset, y_offset) in pixels
        clip_size: Tuple of (width, height) of the clip
        canvas_size: Tuple of (width, height) of the canvas
    
    Returns:
        Position tuple (x, y) in pixels
    """
    if not offset or (offset[0] == 0 and offset[1] == 0):
        # If no offset and position is already numeric, return as-is
        if isinstance(base_position[0], (int, float)) and isinstance(base_position[1], (int, float)):
            return base_position
        # Otherwise, need to calculate string positions
    
    x_base, y_base = base_position
    x_offset, y_offset = offset
    
    # If both are numeric (pixel coordinates), add offset directly
    if isinstance(x_base, (int, float)) and isinstance(y_base, (int, float)):
        return (int(x_base + x_offset), int(y_base + y_offset))
    
    # If using string positions, calculate based on clip and canvas sizes
    if clip_size is None or canvas_size is None:
        # Fallback: return center position with offset
        return (x_offset, y_offset)
    
    # Calculate base position
    if x_base == 'center':
        x = (canvas_size[0] - clip_size[0]) // 2
    elif x_base == 'left':
        x = 0
    elif x_base == 'right':
        x = canvas_size[0] - clip_size[0]
    elif isinstance(x_base, (int, float)):
        x = int(x_base)
    else:
        x = (canvas_size[0] - clip_size[0]) // 2  # default center
    
    if y_base == 'center':
        y = (canvas_size[1] - clip_size[1]) // 2
    elif y_base == 'top':
        y = 0
    elif y_base == 'bottom':
        y = canvas_size[1] - clip_size[1]
    elif isinstance(y_base, (int, float)):
        y = int(y_base)
    else:
        y = (canvas_size[1] - clip_size[1]) // 2  # default center
    
    # Apply offset
    return (int(x + x_offset), int(y + y_offset))


def create_video_segment(video_path, hook_text, duration, portrait_w, portrait_h, title_text=None):
    """
    Create a single video segment with text overlay and optional title.
    Returns a CompositeVideoClip with video + text overlay + title.
    """
    # Load video clip
    clip = VideoFileClip(video_path)
    
    # Extract segment (trim or loop to match duration)
    if clip.duration > duration:
        # Random start point for variety
        max_start = clip.duration - duration
        start_time = random.uniform(0, max_start) if RANDOM_VIDEO_SELECTION else 0
        clip = clip.subclipped(start_time, start_time + duration)
    elif clip.duration < duration:
        # Loop if too short
        num_loops = int(duration / clip.duration) + 1
        clip = concatenate_videoclips([clip] * num_loops)
        clip = clip.subclipped(0, duration)
    
    clip = clip.with_duration(duration)
    
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
    
    try:
        clip_resized = clip_resized.with_duration(duration)
    except Exception:
        pass
    
    # Create background
    try:
        from moviepy.video.VideoClip import ColorClip
        bg = ColorClip(size=(portrait_w, portrait_h), color=(0, 0, 0)).with_duration(duration)
    except Exception:
        bg = None
    
    # Center video on canvas
    video_layer = clip_resized.with_position(('center', 'center'))
    
    # Create layers
    layers = []
    if bg is not None:
        layers.append(bg)
    layers.append(video_layer)
    
    # Add text overlay
    if TEXT_OVERLAY_ENABLED and hook_text:
        max_width = int(portrait_w * TEXT_WIDTH_PERCENT)
        pil_img = make_rounded_text_image(hook_text, max_width=max_width)
        img_clip = ImageClip(np.array(pil_img)).with_duration(duration)
        
        # Get clip size for position calculation
        clip_size = (pil_img.width, pil_img.height)
        canvas_size = (portrait_w, portrait_h)
        
        # Position text with offset support
        if TEXT_CUSTOM_POSITION:
            position = calculate_position_with_offset(
                TEXT_CUSTOM_POSITION, 
                TEXT_POSITION_OFFSET, 
                clip_size, 
                canvas_size
            )
        else:
            position = calculate_position_with_offset(
                TEXT_POSITION, 
                TEXT_POSITION_OFFSET, 
                clip_size, 
                canvas_size
            )
        
        img_clip = img_clip.with_position(position)
        
        # Apply fade effects
        if TEXT_FADE_IN_DURATION > 0:
            try:
                img_clip = img_clip.crossfadein(TEXT_FADE_IN_DURATION)
            except Exception:
                pass
        if TEXT_FADE_OUT_DURATION > 0:
            try:
                img_clip = img_clip.crossfadeout(TEXT_FADE_OUT_DURATION)
            except Exception:
                pass
        
        layers.append(img_clip)
    
    # Add title overlay
    if TITLE_OVERLAY_ENABLED and title_text:
        max_title_width = int(portrait_w * TITLE_WIDTH_PERCENT)
        
        # Create title image (white bold text)
        try:
            font = ImageFont.truetype("arialbd.ttf", TITLE_FONT_SIZE)  # Bold Arial
        except:
            try:
                font = ImageFont.truetype("arial.ttf", TITLE_FONT_SIZE)
            except:
                font = ImageFont.load_default()
        
        # Calculate text size
        dummy_img = Image.new('RGBA', (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)
        
        # Word wrap for title
        words = title_text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = dummy_draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_title_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Calculate total size
        line_heights = []
        max_line_width = 0
        for line in lines:
            bbox = dummy_draw.textbbox((0, 0), line, font=font)
            # Add extra space for descenders (letters like g, j, p, q, y)
            line_height = (bbox[3] - bbox[1]) + 8  # Extra 8px padding for descenders
            line_heights.append(line_height)
            max_line_width = max(max_line_width, bbox[2] - bbox[0])
        
        total_height = sum(line_heights) + (len(lines) - 1) * 4  # 4px between lines
        
        # Add padding if background is used
        if TITLE_BG_COLOR:
            h_pad, v_pad = TITLE_PADDING
            img_width = max_line_width + 2 * h_pad
            img_height = total_height + 2 * v_pad
        else:
            h_pad, v_pad = 0, 0
            img_width = max_line_width
            img_height = total_height
        
        # Create title image
        title_img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
        title_draw = ImageDraw.Draw(title_img)
        
        # Draw background if specified
        if TITLE_BG_COLOR:
            if TITLE_BORDER_RADIUS > 0:
                # Draw rounded rectangle
                title_draw.rounded_rectangle(
                    [(0, 0), (img_width, img_height)],
                    radius=TITLE_BORDER_RADIUS,
                    fill=TITLE_BG_COLOR
                )
            else:
                title_draw.rectangle([(0, 0), (img_width, img_height)], fill=TITLE_BG_COLOR)
        
        # Draw text lines
        y = v_pad
        for i, line in enumerate(lines):
            bbox = title_draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            x = h_pad + (max_line_width - line_width) // 2  # Center each line
            
            # Draw text with white color
            title_draw.text((x, y), line, font=font, fill=TITLE_FONT_COLOR)
            y += line_heights[i] + 4
        
        # Create ImageClip for title
        title_clip = ImageClip(np.array(title_img)).with_duration(duration)
        
        # Position title
        title_clip_size = (title_img.width, title_img.height)
        title_position = calculate_position_with_offset(
            TITLE_POSITION,
            TITLE_POSITION_OFFSET,
            title_clip_size,
            canvas_size
        )
        title_clip = title_clip.with_position(title_position)
        
        # Apply fade effects
        if TEXT_FADE_IN_DURATION > 0:
            try:
                title_clip = title_clip.crossfadein(TEXT_FADE_IN_DURATION)
            except Exception:
                pass
        if TEXT_FADE_OUT_DURATION > 0:
            try:
                title_clip = title_clip.crossfadeout(TEXT_FADE_OUT_DURATION)
            except Exception:
                pass
        
        layers.append(title_clip)
    
    # Compose segment
    segment = CompositeVideoClip(layers, size=(portrait_w, portrait_h))
    return segment


# =============================================================================
# LOAD DATA
# =============================================================================

# Read CSV rows
rows = []
original_fieldnames = None
if os.path.isfile(csv_file_path):
    with open(csv_file_path, mode="r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        original_fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
else:
    print(f"Warning: CSV not found at {csv_file_path} — using sample rows for test")
    rows = [
        {"ID": "1", "Hook1": "Sample hook one", "Hook2": "Alternative hook", "Narrative": "Test narrative", "3 Long Tailed Keywords": "sample_keyword_one"},
        {"ID": "2", "Hook1": "Sample hook two", "Hook2": "Another hook", "Narrative": "Test narrative two", "3 Long Tailed Keywords": "sample_keyword_two"},
    ]

# Shuffle rows if configured
if SHUFFLE_CSV_ROWS:
    random.shuffle(rows)

# Store the complete rows list for CSV writing (preserve all rows)
all_rows = rows.copy()  # Keep original full list for CSV writing 

# Limit rows to process (but don't modify the original rows list)
rows_to_process = rows
if MAX_VIDEOS_TO_GENERATE and MAX_VIDEOS_TO_GENERATE > 0:
    rows_to_process = rows[:MAX_VIDEOS_TO_GENERATE]

print(f"Loaded {len(all_rows)} rows from CSV total")
print(f"Will process {len(rows_to_process)} rows (limited by MAX_VIDEOS_TO_GENERATE)")

# Get available video files
video_files = []
if os.path.isdir(video_src_dir):
    video_files = [f for f in os.listdir(video_src_dir) if f.lower().endswith((".mp4", ".mov", ".avi", ".mkv"))]
    print(f"Found {len(video_files)} video clips in source directory")
else:
    print(f"Warning: Video source directory not found: {video_src_dir}")


# =============================================================================
# TEXT OVERLAY FUNCTIONS
# =============================================================================

def get_font_variant(size, bold=False, family=FONT_FAMILY):
    """Load font with specified parameters."""
    try:
        font_name = f"{family}bd.ttf" if bold else f"{family}.ttf"
        return ImageFont.truetype(font_name, size)
    except Exception:
        try:
            font_path = f"C:\\Windows\\Fonts\\{family}bd.ttf" if bold else f"C:\\Windows\\Fonts\\{family}.ttf"
            return ImageFont.truetype(font_path, size)
        except Exception:
            # Fallback to default Arial
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


def make_rounded_text_image(text, max_width, font_size=FONT_SIZE, padding=TEXT_PADDING, 
                            radius=TEXT_BORDER_RADIUS, bg_color=FONT_BG_COLOR, 
                            text_color=FONT_COLOR, prefix_words=PREFIX_WORDS, 
                            prefix_color=PREFIX_COLOR):
    """
    Create a rounded text overlay image with optional prefix highlighting.
    """
    words = text.split()
    draw = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lines_words = []
    cur = []
    normal_font = get_font_variant(font_size, bold=False)
    
    # Word-wrap text to fit max_width
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

    # Calculate text dimensions
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

    # Draw rounded rectangle background
    rect = [0, 0, img_w, img_h]
    try:
        d.rounded_rectangle(rect, radius=radius, fill=bg_color)
    except Exception:
        d.rectangle(rect, fill=bg_color)

    # Draw text with prefix highlighting
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


# =============================================================================
# MAIN VIDEO PROCESSING LOOP
# =============================================================================

print(f"\n{'='*60}")
print(f"Starting video generation with the following settings:")
print(f"{'='*60}")
print(f"Videos to generate: {len(rows)}")
print(f"Target duration: {TARGET_VIDEO_DURATION}s")
print(f"Segment mode: {SEGMENT_MODE}")
if SEGMENT_MODE == "match_hooks":
    print(f"  → Segments will match available hooks (typically 8 segments)")
    print(f"  → Each segment duration: ~{TARGET_VIDEO_DURATION / 8:.1f}s (divided evenly)")
else:
    print(f"  → Segments use fixed duration: {MAX_SEGMENT_DURATION}s each")
    print(f"  → Total segments: ~{int(TARGET_VIDEO_DURATION / MAX_SEGMENT_DURATION)} (hooks may repeat)")
print(f"Random video selection: {RANDOM_VIDEO_SELECTION}")
print(f"Hook selection mode: {HOOK_SELECTION}")
print(f"Background music: {ENABLE_BACKGROUND_MUSIC} (volume: {BACKGROUND_MUSIC_VOLUME * 100:.2f}%)")
print(f"Voiceover: {ENABLE_VOICEOVER} (engine: {TTS_ENGINE})")
print(f"Output resolution: {OUTPUT_RESOLUTION[0]}x{OUTPUT_RESOLUTION[1]}")
print(f"{'='*60}")

# Check TTS availability
if ENABLE_VOICEOVER and not TTS_ENGINE:
    print(f"\n⚠️  WARNING: Voiceover is ENABLED but no TTS engine is installed!")
    print(f"   Videos will be generated WITHOUT voiceovers.")
    print(f"   To enable voiceover, install one of these:")
    print(f"   • pip install pyttsx3  (offline, recommended)")
    print(f"   • pip install gtts     (online, better quality)")
    print(f"   Then run the script again.\n")
elif ENABLE_VOICEOVER and TTS_ENGINE:
    print(f"\n✓ TTS engine '{TTS_ENGINE}' is ready for voiceover generation.")
    
    # Test TTS functionality
    print(f"  Testing TTS engine...")
    test_audio_path = os.path.join(target_dir, "_tts_test.mp3")
    test_result = generate_voiceover_audio("Testing voice over", test_audio_path)
    if test_result and os.path.exists(test_result):
        file_size = os.path.getsize(test_result)
        print(f"  ✓ TTS test successful! (Generated {file_size} bytes)")
        try:
            os.remove(test_result)  # Clean up test file
        except:
            pass
    else:
        print(f"  ⚠️ TTS test FAILED! Voiceovers may not work properly.")
        print(f"     Check error messages above and ensure TTS is properly configured.")
    print()

else:
    print()

# Determine row range for processing
start_idx = max(0, ROW_START - 1) if ROW_START else 0  # Convert 1-based to 0-based index
end_idx = min(len(rows_to_process), ROW_END) if ROW_END else len(rows_to_process)  # Convert 1-based to 0-based index

# Validate row range
if start_idx >= len(rows_to_process):
    print(f"❌ ERROR: ROW_START ({ROW_START}) is beyond the available data rows ({len(rows_to_process)})")
    print(f"   Available rows: 1-{len(rows_to_process)} (CSV has {len(all_rows)} total data rows)")
    print(f"   Please set ROW_START to a value between 1 and {len(rows_to_process)}")
    exit(1)
if ROW_END and ROW_START and ROW_END < ROW_START:
    print(f"❌ ERROR: ROW_END ({ROW_END}) cannot be less than ROW_START ({ROW_START})")
    exit(1)

total_to_process = end_idx - start_idx

print(f"\n{'='*60}")
print(f"ROW PROCESSING RANGE:")
print(f"  Total rows in CSV: {len(all_rows)}")
print(f"  Rows available for processing: {len(rows_to_process)}")
print(f"  Processing rows: {start_idx + 1} to {end_idx} (1-based)")
print(f"  Videos to generate: {total_to_process}")
print(f"{'='*60}")

# Process rows within specified range
for list_idx, idx in enumerate(range(start_idx, end_idx)):
    row = rows_to_process[idx]
    original_idx = idx  # Track the original index for CSV updates
    # Progress indicator
    print(f"\n[{list_idx+1}/{total_to_process}] Processing video for Row {original_idx+1}, ID: {row.get('ID', original_idx+1)}")
    
    # Select hook text based on configuration
    hook_text = select_hook_text(row, HOOK_SELECTION, idx)
    if not hook_text:
        print(f"  ⚠ No hook text found, skipping row {original_idx+1}")
        continue
    
    print(f"  📝 Hook: {hook_text[:60]}..." if len(hook_text) > 60 else f"  📝 Hook: {hook_text}")
    
    # Determine video source
    if RANDOM_VIDEO_SELECTION:
        selected_videos = get_random_videos(video_files, count=1, allow_reuse=ALLOW_VIDEO_REUSE)
        if not selected_videos:
            print(f"  ⚠ No video files available, skipping")
            continue
        video_path = os.path.join(video_src_dir, selected_videos[0])
        print(f"  🎬 Random video: {selected_videos[0]}")
    else:
        # Sequential selection (original behavior)
        fp = (row.get("FilePath") or "").strip()
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
                print(f"  ⚠ No video available, skipping")
                continue
    
    # Generate output filename from Title column
    row_id = (row.get("ID") or str(idx + 1)).strip()
    title = (row.get("Title") or "").strip()
    if title:
        # Sanitize title: convert to lowercase, replace spaces/special chars with underscores
        sanitized_title = re.sub(r'[^A-Za-z0-9]+', '_', title.lower()).strip('_')
        output_name = f"{row_id}_{OUTPUT_FILENAME_PREFIX}{sanitized_title}.mp4"
    else:
        # Fallback if no title: use ID and keyword
        lt = (row.get("3 Long Tailed Keywords") or row.get("LongTailKeywords") or "").split(",")[0].strip()
        sanitized = re.sub(r'[^A-Za-z0-9]+', '_', lt).strip('_') or f"row{row_id}"
        output_name = f"{row_id}_{OUTPUT_FILENAME_PREFIX}{sanitized}.mp4"
    output_path = os.path.join(target_dir, output_name)
    print(f"  📁 Output filename: {output_name}")
    
    # Build video with multiple segments (each with different Hook and video clip)
    print(f"  ⚙ Building multi-segment video...")
    
    # Target portrait (mobile) size: 9:16 aspect ratio
    portrait_w, portrait_h = OUTPUT_RESOLUTION
    
    # Get all hooks from the row first (needed for segment calculation)
    all_hooks = []
    for i in range(1, 9):  # Support Hook1 through Hook8
        hook = row.get(f"Hook{i}", "").strip()
        if hook:
            all_hooks.append(hook)
    
    # Ensure we have hooks (fallback to Hook1 if empty)
    if not all_hooks:
        all_hooks = [hook_text]
    
    # Calculate segments based on SEGMENT_MODE
    if SEGMENT_MODE == "match_hooks":
        # Number of segments matches number of available hooks
        num_segments = len(all_hooks)
        calculated_segment_duration = TARGET_VIDEO_DURATION / num_segments
        print(f"     Mode: Match Hooks - {num_segments} segments × {calculated_segment_duration:.1f}s each")
    else:
        # Default: "fixed_duration" - use MAX_SEGMENT_DURATION
        num_segments = max(1, int(TARGET_VIDEO_DURATION / MAX_SEGMENT_DURATION))
        if TARGET_VIDEO_DURATION % MAX_SEGMENT_DURATION != 0:
            num_segments += 1
        calculated_segment_duration = MAX_SEGMENT_DURATION
        print(f"     Mode: Fixed Duration - {num_segments} segments × ~{MAX_SEGMENT_DURATION}s each (hooks may repeat)")
    
    # Generate voiceover for each hook segment if enabled
    voiceover_audio_paths = []
    voiceover_durations = []  # Store actual voiceover durations
    print(f"  🔍 VOICEOVER DEBUG:")
    print(f"     ENABLE_VOICEOVER: {ENABLE_VOICEOVER}")
    print(f"     TTS_ENGINE: {TTS_ENGINE}")
    print(f"     num_segments: {num_segments}")
    print(f"     all_hooks count: {len(all_hooks)}")
    
    if ENABLE_VOICEOVER and TTS_ENGINE:
        print(f"  🎙 Generating voiceovers for hooks...")
        for seg_idx in range(num_segments):
            # Select hook for this segment
            hook_idx = seg_idx % len(all_hooks)
            segment_hook = all_hooks[hook_idx]
            
            # Generate voiceover for this hook
            vo_path = os.path.join(target_dir, f"voiceover_{row_id}_seg{seg_idx + 1}.mp3")
            print(f"    📝 Segment {seg_idx + 1}: Generating TTS for Hook{hook_idx + 1}")
            print(f"       Text: {segment_hook[:50]}...")
            print(f"       Output: {vo_path}")
            
            vo_generated = generate_voiceover_audio(segment_hook, vo_path)
            
            print(f"       Result: {vo_generated}")
            
            if vo_generated:
                # Get the actual duration of the voiceover
                try:
                    vo_clip = AudioFileClip(vo_generated)
                    vo_duration = vo_clip.duration
                    vo_clip.close()
                    voiceover_audio_paths.append(vo_generated)
                    voiceover_durations.append(vo_duration)
                    print(f"    ✓ Hook{hook_idx + 1} voiceover created ({vo_duration:.1f}s)")
                except Exception as e:
                    print(f"    ⚠ Could not read voiceover duration: {e}")
                    voiceover_durations.append(MAX_SEGMENT_DURATION)  # fallback
                    voiceover_audio_paths.append(vo_generated)
            else:
                print(f"    ⚠ Hook{hook_idx + 1} voiceover FAILED - returned None/empty")
                voiceover_durations.append(0)  # Mark as failed
        
        if voiceover_audio_paths:
            print(f"  ✓ {len(voiceover_audio_paths)} voiceovers generated successfully")
            print(f"     Durations: {[f'{d:.1f}s' for d in voiceover_durations]}")
        else:
            print(f"  ❌ NO voiceovers generated - all attempts failed!")
    elif ENABLE_VOICEOVER and not TTS_ENGINE:
        print(f"  ⚠ Voiceover enabled but TTS engine not available - skipping voiceovers")
    elif not ENABLE_VOICEOVER:
        print(f"  ⚠ Voiceover is DISABLED (ENABLE_VOICEOVER = False)")
    
    print(f"  🔍 POST-VOICEOVER CHECK:")
    print(f"     Final voiceover_audio_paths: {voiceover_audio_paths}")
    print(f"     Count: {len(voiceover_audio_paths)}")
    print(f"     Durations: {voiceover_durations}")

    
    # Create segments
    segments = []
    for seg_idx in range(num_segments):
        # Use voiceover duration if available, otherwise use calculated duration
        if seg_idx < len(voiceover_durations) and voiceover_durations[seg_idx] > 0:
            seg_duration = voiceover_durations[seg_idx]
            print(f"    ⏱ Segment {seg_idx + 1} duration synced to voiceover: {seg_duration:.1f}s")
        else:
            # Calculate segment duration based on mode
            if SEGMENT_MODE == "match_hooks":
                # Equal division of total duration
                seg_duration = calculated_segment_duration
            else:
                # Use remaining duration approach with MAX_SEGMENT_DURATION
                remaining_duration = TARGET_VIDEO_DURATION - sum(voiceover_durations[:seg_idx] if voiceover_durations else [MAX_SEGMENT_DURATION * seg_idx])
                seg_duration = min(MAX_SEGMENT_DURATION, remaining_duration)
        
        if seg_duration <= 0:
            break
        
        # Extend segment duration to account for crossfade overlap (except last segment)
        # This ensures each segment displays for its full duration even after overlapping
        if VIDEO_CROSSFADE_DURATION > 0 and seg_idx < num_segments - 1:
            seg_duration_extended = seg_duration + VIDEO_CROSSFADE_DURATION
            print(f"    ⏱ Extended segment {seg_idx + 1} duration to {seg_duration_extended:.1f}s (adding {VIDEO_CROSSFADE_DURATION}s for crossfade)")
        else:
            seg_duration_extended = seg_duration
        
        # Select hook for this segment (cycle through Hook1, Hook2, Hook3, Hook4)
        hook_idx = seg_idx % len(all_hooks)
        segment_hook = all_hooks[hook_idx]
        
        # Select random video for this segment
        if RANDOM_VIDEO_SELECTION:
            selected_video = get_random_videos(video_files, count=1, allow_reuse=ALLOW_VIDEO_REUSE)
            if not selected_video:
                print(f"    ⚠ No video for segment {seg_idx + 1}, using fallback")
                segment_video_path = video_path
            else:
                segment_video_path = os.path.join(video_src_dir, selected_video[0])
        else:
            # Use sequential or fallback to main video
            if seg_idx < len(video_files):
                segment_video_path = os.path.join(video_src_dir, video_files[seg_idx])
            else:
                segment_video_path = video_path
        
        print(f"    📹 Segment {seg_idx + 1}/{num_segments}: Hook{hook_idx + 1} ({seg_duration:.1f}s) - {os.path.basename(segment_video_path)}")
        if seg_duration_extended != seg_duration:
            print(f"       ✨ Extended to {seg_duration_extended:.1f}s for crossfade overlap")
        
        # Get title from CSV row
        title_text = row.get("Title", "").strip()
        
        # Create segment with video + text overlay + title
        try:
            segment = create_video_segment(
                segment_video_path, 
                segment_hook, 
                seg_duration_extended,  # Use extended duration for video creation
                portrait_w, 
                portrait_h,
                title_text=title_text
            )
            segments.append(segment)
        except Exception as e:
            print(f"    ⚠ Error creating segment {seg_idx + 1}: {e}")
            continue
    
    # Concatenate all segments into final video
    if not segments:
        print(f"  ⚠ No segments created, skipping video")
        continue
    
    print(f"  🔗 Concatenating {len(segments)} segments...")
    if len(segments) == 1:
        final = segments[0]
    else:
        # Apply crossfade transitions between segments
        if VIDEO_CROSSFADE_DURATION > 0:
            print(f"     ✨ Applying {VIDEO_CROSSFADE_DURATION}s crossfade transitions between segments")
            # Apply fade-out to all segments except the last, fade-in to all except first
            transition_segments = []
            for i in range(len(segments)):
                seg = segments[i]
                try:
                    # Fade out at the end (except last segment)
                    if i < len(segments) - 1:
                        seg = seg.crossfadeout(VIDEO_CROSSFADE_DURATION)
                    # Fade in at the start (except first segment)  
                    if i > 0:
                        seg = seg.crossfadein(VIDEO_CROSSFADE_DURATION)
                    transition_segments.append(seg)
                except Exception as e:
                    print(f"     ⚠ Could not apply transition to segment {i+1}: {e}")
                    transition_segments.append(segments[i])
            
            # Concatenate with padding to create overlap effect
            # Each segment overlaps by VIDEO_CROSSFADE_DURATION with the next
            final = transition_segments[0]
            for i in range(1, len(transition_segments)):
                try:
                    # Set next segment to start VIDEO_CROSSFADE_DURATION before previous ends
                    next_seg = transition_segments[i].with_start(final.duration - VIDEO_CROSSFADE_DURATION)
                    final = CompositeVideoClip([final, next_seg], size=(portrait_w, portrait_h))
                except Exception as e:
                    print(f"     ⚠ Could not composite segment {i+1}: {e}")
                    # Fallback to simple concatenation
                    final = concatenate_videoclips([final, transition_segments[i]], method="compose")
        else:
            final = concatenate_videoclips(segments, method="compose")

    # Handle audio mixing: background music + voiceover
    print(f"  🎵 Processing audio...")
    print(f"     Final video duration: {final.duration:.1f}s")
    audio_clips = []
    
    # Background music
    if ENABLE_BACKGROUND_MUSIC and os.path.isfile(audio_path):
        try:
            bg_audio = AudioFileClip(audio_path)
            print(f"     Background music loaded (duration: {bg_audio.duration:.1f}s)")
            
            # Apply start offset if configured
            if AUDIO_START_OFFSET > 0:
                bg_audio = bg_audio.subclipped(AUDIO_START_OFFSET)
            
            # Trim or loop to match actual video duration (not target duration)
            video_duration = final.duration
            if bg_audio.duration > video_duration:
                bg_audio = bg_audio.subclipped(0, video_duration)
            elif bg_audio.duration < video_duration:
                if audio_loop is not None:
                    try:
                        bg_audio = audio_loop(bg_audio, duration=video_duration)
                    except Exception:
                        try:
                            bg_audio = bg_audio.fx(audio_loop, duration=video_duration)
                        except Exception:
                            pass
            
            # Apply volume adjustment - CRITICAL: This must work!
            print(f"     Applying background music volume: {BACKGROUND_MUSIC_VOLUME} ({BACKGROUND_MUSIC_VOLUME * 100}%)")
            print(f"     volumex function available: {volumex is not None}")
            
            volume_applied = False
            if BACKGROUND_MUSIC_VOLUME != 1.0:
                # Try multiple methods to ensure volume is applied
                try:
                    # Method 1: Direct volumex function
                    if volumex:
                        bg_audio = volumex(bg_audio, BACKGROUND_MUSIC_VOLUME)
                        volume_applied = True
                        print(f"     ✓ Volume applied using volumex function")
                except Exception as e1:
                    print(f"     ✗ volumex method failed: {e1}")
                    try:
                        # Method 2: Using fx with volumex
                        from moviepy.audio.fx.volumex import volumex as volumex_fx
                        bg_audio = bg_audio.fx(volumex_fx, BACKGROUND_MUSIC_VOLUME)
                        volume_applied = True
                        print(f"     ✓ Volume applied using fx(volumex)")
                    except Exception as e2:
                        print(f"     ✗ fx(volumex) method failed: {e2}")
                        try:
                            # Method 3: Direct method call
                            bg_audio = bg_audio.volumex(BACKGROUND_MUSIC_VOLUME)
                            volume_applied = True
                            print(f"     ✓ Volume applied using direct volumex method")
                        except Exception as e3:
                            print(f"     ✗ direct volumex method failed: {e3}")
                            # Method 4: Manual audio array multiplication (guaranteed to work)
                            try:
                                def apply_volume(get_frame, t):
                                    return get_frame(t) * BACKGROUND_MUSIC_VOLUME
                                bg_audio = bg_audio.transform(apply_volume)
                                volume_applied = True
                                print(f"     ✓ Volume applied using manual transform")
                            except Exception as e4:
                                print(f"     ✗ ALL volume methods failed: {e4}")
            
            if not volume_applied and BACKGROUND_MUSIC_VOLUME != 1.0:
                print(f"     ⚠ WARNING: Background music volume could NOT be applied!")
            
            audio_clips.append(bg_audio)
            
        except Exception as e:
            print(f"  ⚠ Background audio error: {e}")
    
    # Voiceover audio - concatenate multiple hook voiceovers
    print(f"  🔍 AUDIO MIXING DEBUG:")
    print(f"     voiceover_audio_paths: {voiceover_audio_paths}")
    print(f"     voiceover_audio_paths count: {len(voiceover_audio_paths)}")
    
    if voiceover_audio_paths:
        try:
            # Load all voiceover audio clips
            vo_clips = []
            for vo_path in voiceover_audio_paths:
                print(f"     → Loading voiceover: {vo_path}")
                if os.path.isfile(vo_path):
                    file_size = os.path.getsize(vo_path)
                    print(f"       File exists: {file_size} bytes")
                    vo_clips.append(AudioFileClip(vo_path))
                else:
                    print(f"       ⚠ File not found: {vo_path}")
            
            print(f"     Loaded {len(vo_clips)} voiceover clips")
            
            if vo_clips:
                # Concatenate voiceover clips to match video segments
                if len(vo_clips) == 1:
                    vo_audio = vo_clips[0]
                else:
                    vo_audio = concatenate_audioclips(vo_clips)
                
                # Don't trim - segments are already synced to voiceover durations
                print(f"     Voiceover total duration: {vo_audio.duration:.1f}s")
                
                # Apply volume adjustment
                if VOICEOVER_VOLUME != 1.0:
                    try:
                        if volumex:
                            vo_audio = volumex(vo_audio, VOICEOVER_VOLUME)
                        else:
                            vo_audio = vo_audio.fx(lambda clip: clip.volumex(VOICEOVER_VOLUME))
                    except Exception:
                        try:
                            vo_audio = vo_audio.volumex(VOICEOVER_VOLUME)
                        except Exception:
                            pass
                
                audio_clips.append(vo_audio)
                print(f"  ✓ Voiceovers concatenated and synced")
            
        except Exception as e:
            print(f"  ⚠ Voiceover audio error: {e}")
    
    # Combine audio tracks
    if audio_clips:
        try:
            if len(audio_clips) == 1:
                final_audio = audio_clips[0]
            else:
                from moviepy.audio.AudioClip import CompositeAudioClip
                final_audio = CompositeAudioClip(audio_clips)
            
            final = final.with_audio(final_audio)
        except Exception as e:
            print(f"  ⚠ Audio mixing error: {e}")

    # Write output
    print(f"  💾 Rendering video...")
    fps = OUTPUT_FPS  # Use configured FPS for output
        
    final.write_videofile(
        output_path, 
        codec=VIDEO_CODEC, 
        audio_codec=AUDIO_CODEC, 
        fps=fps,
        bitrate=BITRATE
    )
    
    print(f"  ✅ Created: {output_name}")
    
    # Clean up voiceover temp files
    if voiceover_audio_paths:
        for vo_path in voiceover_audio_paths:
            if os.path.exists(vo_path):
                try:
                    os.remove(vo_path)
                except Exception:
                    pass
    
    # Update CSV with output path (update in the full all_rows list)
    try:
        # Update the in-memory row with absolute path
        abs_output = os.path.abspath(output_path)
        
        # Find the correct row in all_rows to update
        row_id = row.get('ID', '').strip()
        updated = False
        for i, full_row in enumerate(all_rows):
            if full_row.get('ID', '').strip() == row_id:
                all_rows[i]['FilePath'] = abs_output
                updated = True
                print(f"  📋 Updated CSV FilePath for ID {row_id} (all_rows[{i}]): {abs_output}")
                break
        
        if not updated:
            print(f"  ⚠️ Could not find matching row ID {row_id} in all_rows for FilePath update")

        # Determine base fieldnames (preserve original order when possible)
        if original_fieldnames:
            base_fns = [fn for fn in original_fieldnames if fn != 'FilePath']
        elif all_rows:
            base_fns = [k for k in all_rows[0].keys() if k != 'FilePath']
        else:
            base_fns = ['ID', 'Title', 'Hook1', 'Hook2', 'Hook3', 'Hook4', 'Hook5', 'Hook6', '3 Hashtags', '3 Long Tailed Keywords', 'Narrative']

        # Insert FilePath at appropriate position (after first 4 columns)
        insert_index = 4 if len(base_fns) >= 4 else len(base_fns)
        fns = list(base_fns)
        if 'FilePath' in fns:
            fns.remove('FilePath')
        fns.insert(insert_index, 'FilePath')

        # Atomic write to CSV (write ALL rows, not just processed ones)
        tmp_csv = csv_file_path + '.tmp'
        with open(tmp_csv, mode='w', encoding='utf-8', newline='') as wf:
            writer = csv.DictWriter(wf, fieldnames=fns)
            writer.writeheader()
            for i, r in enumerate(all_rows):  # Use all_rows to preserve all data
                out = {k: r.get(k, '') for k in fns}
                # Only update FilePath to absolute path if it's a real file path, not a placeholder
                current_filepath = out.get('FilePath', '').strip()
                if current_filepath and (current_filepath.startswith('/') or '\\' in current_filepath or ':' in current_filepath):
                    # This looks like a real file path, convert to absolute
                    if os.path.exists(current_filepath):
                        out['FilePath'] = os.path.abspath(current_filepath)
                    else:
                        # Keep the current value as-is if file doesn't exist
                        out['FilePath'] = current_filepath
                writer.writerow(out)
        
        # Replace original CSV with updated version
        try:
            os.replace(tmp_csv, csv_file_path)
            print(f"  ✅ CSV successfully updated")
            
            # Verify the FilePath was written correctly
            try:
                with open(csv_file_path, mode='r', encoding='utf-8') as verify_file:
                    verify_reader = csv.DictReader(verify_file)
                    verify_rows = list(verify_reader)
                    # Find the row by ID instead of using idx
                    for verify_row in verify_rows:
                        if verify_row.get('ID', '').strip() == row_id:
                            written_path = verify_row.get('FilePath', '').strip()
                            if written_path == abs_output:
                                print(f"  ✅ FilePath verification successful: {written_path}")
                            else:
                                print(f"  ⚠ FilePath verification failed. Expected: {abs_output}, Got: {written_path}")
                            break
            except Exception as ve:
                print(f"  ⚠ FilePath verification error: {ve}")
        except Exception:
            try:
                os.remove(csv_file_path)
            except Exception:
                pass
            os.replace(tmp_csv, csv_file_path)
            print(f"  ✅ CSV updated (with fallback method)")
            
    except Exception as e:
        print(f"  ⚠ CSV update warning: {e}")

print(f"\n{'='*60}")
print(f"✅ Video generation complete!")
print(f"{'='*60}")
print(f"Processed {total_to_process} videos (rows {start_idx + 1}-{end_idx})")
print(f"Total rows in CSV: {len(all_rows)}")
print(f"Output directory: {target_dir}")
print(f"{'='*60}\n")

