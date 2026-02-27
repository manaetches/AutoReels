# Faceless Video Generator - Usage Guide

## 🎯 Overview
This reengineered script generates faceless videos by combining:
- **Random video clips** from your source directory
- **Text overlays** from multiple hooks (Hook1, Hook2, Hook3, Hook4)
- **Background music** with volume control
- **AI voiceover narration** using TTS (Text-to-Speech)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Core dependencies (required)
pip install moviepy pillow numpy

# TTS dependencies (optional - for voiceover)
pip install pyttsx3  # Offline TTS (recommended)
# OR
pip install gtts     # Online TTS (requires internet)
```

### 2. Configure Your Settings
Edit the **CONTROLS** section in `app-faceless-video.py`:

```python
# Generate only 10 videos for testing
MAX_VIDEOS_TO_GENERATE = 10

# Use random video clips
RANDOM_VIDEO_SELECTION = True

# Select Hook1 from CSV
HOOK_SELECTION = "Hook1"

# Enable voiceover
ENABLE_VOICEOVER = True
```

### 3. Run the Script
```bash
python app-faceless-video.py
```

## 📋 Control Variables Explained

### VIDEO GENERATION CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `MAX_VIDEOS_TO_GENERATE` | Limit number of videos to create | `10`, `50`, `None` (all) |
| `SHUFFLE_CSV_ROWS` | Randomize CSV processing order | `True`, `False` |

### VIDEO CLIP CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `RANDOM_VIDEO_SELECTION` | Use random clips vs sequential | `True`, `False` |
| `ALLOW_VIDEO_REUSE` | Allow same clip multiple times | `True`, `False` |
| `TARGET_VIDEO_DURATION` | Final video length in seconds | `15`, `30`, `60` |
| `CLIP_DURATION_RANGE` | Duration range per clip | `(3, 8)` = 3-8 seconds |

### HOOK TEXT CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `HOOK_SELECTION` | Which hook to use | `"Hook1"`, `"Hook2"`, `"Hook3"`, `"Hook4"`, `"random"`, `"rotate"` |
| `USE_NARRATIVE_FOR_TTS` | Use Narrative column for voiceover | `True`, `False` |

**Hook Selection Modes:**
- `"Hook1"`, `"Hook2"`, `"Hook3"`, `"Hook4"` - Use specific hook column
- `"random"` - Randomly select a hook for each video
- `"rotate"` - Cycle through Hook1→Hook2→Hook3→Hook4 sequentially

### AUDIO CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `ENABLE_BACKGROUND_MUSIC` | Toggle background music | `True`, `False` |
| `BACKGROUND_MUSIC_VOLUME` | Music volume (0.0-1.0) | `0.3` (30%), `0.5` (50%) |
| `AUDIO_START_OFFSET` | Delay audio start (seconds) | `0`, `2`, `5` |
| `ENABLE_VOICEOVER` | Toggle AI narration | `True`, `False` |
| `VOICEOVER_VOLUME` | Voiceover volume (0.0-1.0) | `1.0` (100%) |
| `TTS_VOICE_SPEED` | Speech rate (words/min) | `150`, `180`, `200` |
| `TTS_LANGUAGE` | Language code for gTTS | `"en"`, `"es"`, `"fr"` |

### TEXT OVERLAY CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `TEXT_OVERLAY_ENABLED` | Show text on video | `True`, `False` |
| `TEXT_POSITION` | Text placement | `('center', 'center')`, `('center', 'top')` |
| `TEXT_CUSTOM_POSITION` | Custom pixel position | `(540, 100)`, `None` |
| `TEXT_WIDTH_PERCENT` | Text width (% of video) | `0.85` (85%), `0.7` (70%) |
| `FONT_SIZE` | Text font size | `40`, `50`, `60` |
| `FONT_FAMILY` | Font name | `"arial"`, `"impact"`, `"times"` |
| `FONT_COLOR` | Text color RGBA | `(0, 0, 0, 255)` = black |
| `FONT_BG_COLOR` | Background color RGBA | `(255, 255, 255, 200)` = white semi-transparent |
| `PREFIX_WORDS` | Words to highlight | `2`, `3`, `0` (none) |
| `PREFIX_COLOR` | Highlight color RGBA | `(102, 0, 153, 255)` = purple |
| `TEXT_PADDING` | Padding around text | `(24, 16)` = (horizontal, vertical) |
| `TEXT_BORDER_RADIUS` | Rounded corner radius | `10`, `15`, `0` (square) |

### ANIMATION CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `TEXT_FADE_IN_DURATION` | Text fade-in time (sec) | `0.5`, `1.0`, `0` (instant) |
| `TEXT_FADE_OUT_DURATION` | Text fade-out time (sec) | `0.5`, `1.0`, `0` (instant) |
| `VIDEO_CROSSFADE_DURATION` | Clip transitions (sec) | `0.8`, `1.0`, `0` (cut) |

### OUTPUT CONTROLS
| Variable | Description | Example Values |
|----------|-------------|----------------|
| `OUTPUT_FPS` | Frames per second | `24`, `30`, `60` |
| `OUTPUT_RESOLUTION` | Video dimensions (W, H) | `(1080, 1920)` = 9:16 portrait |
| `VIDEO_CODEC` | Compression format | `'libx264'`, `'libx265'` |
| `AUDIO_CODEC` | Audio format | `'aac'`, `'mp3'` |
| `BITRATE` | Video quality | `"5000k"`, `"8000k"`, `"12000k"` |

## 🎨 Common Use Cases

### Example 1: Test Run (Quick Preview)
```python
MAX_VIDEOS_TO_GENERATE = 3          # Generate only 3 videos
TARGET_VIDEO_DURATION = 15          # Short 15-second videos
RANDOM_VIDEO_SELECTION = True       # Random clips
HOOK_SELECTION = "Hook1"            # Use Hook1
ENABLE_VOICEOVER = False            # Skip voiceover for faster test
```

### Example 2: Production Run (Full Quality)
```python
MAX_VIDEOS_TO_GENERATE = None       # Generate all CSV rows
TARGET_VIDEO_DURATION = 30          # 30-second Instagram Reels
RANDOM_VIDEO_SELECTION = True       # Vary the clips
HOOK_SELECTION = "random"           # Mix different hooks
ENABLE_VOICEOVER = True             # Add AI narration
BACKGROUND_MUSIC_VOLUME = 0.25      # Quiet music (25%)
VOICEOVER_VOLUME = 1.0              # Full voiceover (100%)
BITRATE = "12000k"                  # High quality
```

### Example 3: Batch Variations (A/B Testing)
```python
# Run 1: Hook1 + Narrative voiceover
HOOK_SELECTION = "Hook1"
USE_NARRATIVE_FOR_TTS = True

# Run 2: Hook2 + Hook text voiceover
HOOK_SELECTION = "Hook2"
USE_NARRATIVE_FOR_TTS = False

# Run 3: Random hooks
HOOK_SELECTION = "random"
```

### Example 4: Custom Styling
```python
# Bold impact font, larger text
FONT_FAMILY = "impact"
FONT_SIZE = 50
TEXT_WIDTH_PERCENT = 0.9            # 90% width

# Bright yellow text with dark background
FONT_COLOR = (255, 255, 0, 255)     # Yellow
FONT_BG_COLOR = (0, 0, 0, 200)      # Black semi-transparent

# No prefix highlighting
PREFIX_WORDS = 0

# Dramatic animations
TEXT_FADE_IN_DURATION = 1.0
TEXT_FADE_OUT_DURATION = 1.0
```

## 📊 CSV Requirements

Your CSV must include these columns:
- `ID` - Unique identifier
- `Hook1`, `Hook2`, `Hook3`, `Hook4` - Text overlay variations
- `Narrative` - Optional voiceover script
- `3 Long Tailed Keywords` - For filename generation

Example CSV row:
```csv
ID,Title,Hook1,Hook2,Hook3,Hook4,Narrative,3 Long Tailed Keywords
1,Video Title,First hook text,Second hook text,Third hook text,Fourth hook text,Full narration script,keyword1 keyword2 keyword3
```

## 🎥 Output

Videos are saved to `target_dir` with filenames like:
```
1_keyword1_keyword2_keyword3.mp4
2_wellness_relaxation_meditation.mp4
```

The CSV is automatically updated with output file paths in the `FilePath` column.

## 🛠️ Troubleshooting

### No TTS Engine Found
```bash
pip install pyttsx3
```

### Audio Not Working
- Verify `audio_path` points to valid audio file
- Check `ENABLE_BACKGROUND_MUSIC = True`

### Text Not Showing
- Set `TEXT_OVERLAY_ENABLED = True`
- Verify hook text exists in CSV

### Videos Too Short/Long
- Adjust `TARGET_VIDEO_DURATION`
- Check source video clip lengths

## 📝 Notes

- **TTS Engines**: `pyttsx3` (offline, faster) recommended over `gtts` (online, better quality)
- **Performance**: Disable voiceover for faster test runs
- **Quality**: Higher `BITRATE` = larger files but better quality
- **Memory**: Large video files may require significant RAM during processing

## 🎬 Advanced Features

### Random Video Selection
When `RANDOM_VIDEO_SELECTION = True`, each video:
1. Randomly selects a source clip
2. Randomly starts at different timestamps (for variety)
3. Can reuse clips if `ALLOW_VIDEO_REUSE = True`

### Hook Rotation
With `HOOK_SELECTION = "rotate"`:
- Video 1 uses Hook1
- Video 2 uses Hook2
- Video 3 uses Hook3
- Video 4 uses Hook4
- Video 5 uses Hook1 (cycles back)

### Audio Mixing
The script intelligently combines:
- Background music (reduced volume)
- Voiceover narration (full volume)
- Automatic duration matching and looping

---

**Ready to create amazing faceless videos? Start generating! 🚀**
