"""
Generate voiceover audio from video script segments.
Uses edge-tts (Microsoft Edge TTS) with Indonesian-accented English male voice,
then merges them with the demo video using ffmpeg.
"""
import asyncio
import os
import subprocess
import edge_tts

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.join(SCRIPT_DIR, '..', '..', '..', '..')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'docs', 'demo')
AUDIO_DIR = os.path.join(SCRIPT_DIR, 'audio')

# Voice: English US male (en-US-AndrewNeural) - 30yo, warm, confident
VOICE = "en-US-AndrewNeural"

# Voiceover segments synced with Playwright test timing (seconds)
SEGMENTS = [
    {
        'start': 0,
        'text': "Welcome to Vigil Station, an AI-powered ground station scheduling assistant. "
                "Designed for Southeast Asian coverage, monitoring Jakarta, Bandung, and Singapore."
    },
    {
        'start': 5,
        'text': "The Schedule tab displays satellite passes with filters for satellite and ground station. "
                "Each row shows satellite name, ground station, start time, end time, max elevation, and duration."
    },
    {
        'start': 12,
        'text': "The max elevation uses color coding: green for excellent signal above 45 degrees, "
                "yellow for moderate 30 to 44 degrees, and red for weak signal below 30 degrees."
    },
    {
        'start': 20,
        'text': "The Conflicts tab detects overlapping contact windows at the same ground station. "
                "41 active conflicts detected across 88 total passes. Each card shows both passes side by side."
    },
    {
        'start': 28,
        'text': "Clicking Generate AI Recommendation analyzes orbital data and provides a suggested action, "
                "alternative contact window, and detailed reasoning for conflict resolution."
    },
    {
        'start': 36,
        'text': "The Approval Dashboard gives operators full control. Stats cards track pending, approved, "
                "and overridden decisions. Operators can approve the AI suggestion or override with a mandatory reason."
    },
    {
        'start': 48,
        'text': "Every decision is logged in PostgreSQL for full traceability. AI never executes autonomously."
    },
    {
        'start': 55,
        'text': "The Map tab displays a dark-themed Leaflet map. Green pins mark ground stations. "
                "Blue dots represent satellites in orbit. Orange dashed lines show active pass windows."
    },
    {
        'start': 63,
        'text': "Space Weather conditions are monitored from NASA feeds. Current status shows quiet conditions "
                "with favorable communication environment."
    },
    {
        'start': 70,
        'text': "The Analytics dashboard tracks 1195 logged conflicts, 8 AI recommendations, "
                "and 100 percent approval rate. Singapore Ground Station identified as top contention point."
    },
    {
        'start': 78,
        'text': "Vigil Station transforms satellite operations from reactive troubleshooting "
                "into proactive, AI-assisted mission assurance. Advancing space exploration through intelligent automation."
    }
]


async def generate_audio_segments():
    """Generate audio files for each script segment using edge-tts."""
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    audio_files = []
    for i, seg in enumerate(SEGMENTS):
        output_path = os.path.join(AUDIO_DIR, f'segment_{i:02d}.mp3')
        
        if not os.path.exists(output_path):
            print(f"Generating audio for segment {i}: {seg['text'][:50]}...")
            communicate = edge_tts.Communicate(seg['text'], VOICE)
            await communicate.save(output_path)
        
        audio_files.append({
            'file': output_path,
            'start': seg['start']
        })
        print(f"  Saved: {output_path}")
    
    return audio_files


def create_silence(duration_sec, output_path):
    """Create a silent audio file."""
    subprocess.run([
        'ffmpeg', '-y', '-f', 'lavfi', '-i',
        f'anullsrc=r=24000:cl=mono',
        '-t', str(duration_sec),
        '-c:a', 'libmp3lame', '-q:a', '9',
        output_path
    ], capture_output=True)


def merge_audio_segments(audio_files):
    """Merge audio segments with proper timing gaps."""
    concat_list = os.path.join(AUDIO_DIR, 'concat.txt')
    silence_file = os.path.join(AUDIO_DIR, 'silence.mp3')
    
    with open(concat_list, 'w') as f:
        prev_end = 0
        for i, seg in enumerate(audio_files):
            gap = seg['start'] - prev_end
            if gap > 0:
                create_silence(gap, silence_file)
                f.write(f"file '{silence_file}'\n")
            
            f.write(f"file '{seg['file']}'\n")
            
            result = subprocess.run([
                'ffprobe', '-v', 'error', '-show_entries',
                'format=duration', '-of', 'csv=p=0',
                seg['file']
            ], capture_output=True, text=True)
            duration = float(result.stdout.strip()) if result.stdout.strip() else 5
            prev_end = seg['start'] + duration
    
    merged_audio = os.path.join(AUDIO_DIR, 'voiceover.mp3')
    subprocess.run([
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', concat_list,
        '-c:a', 'libmp3lame', '-q:a', '2',
        merged_audio
    ], capture_output=True)
    
    print(f"Merged audio: {merged_audio}")
    return merged_audio


def merge_video_audio(video_path, audio_path, output_path):
    """Merge video with voiceover audio."""
    cmd = f'ffmpeg -y -i {video_path} -i {audio_path} -c:v libx264 -c:a aac -b:a 128k -shortest {output_path}'
    os.system(cmd)
    print(f"Final video with voiceover: {output_path}")


def main():
    print("=== Vigil Station Demo Voiceover Generator ===")
    print(f"Voice: {VOICE} (English male, native, ~30yo)\n")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    video_dir = os.path.join(SCRIPT_DIR, '..', '..', 'test-results')
    video_files = []
    for root, dirs, files in os.walk(video_dir):
        for f in files:
            if f.endswith('.webm'):
                video_files.append(os.path.join(root, f))
    
    if not video_files:
        print("No video file found. Run Playwright demo first.")
        return
    
    video_path = video_files[0]
    print(f"Video: {video_path}\n")
    
    print("Generating audio segments...")
    audio_files = asyncio.run(generate_audio_segments())
    
    print("\nMerging audio segments...")
    merged_audio = merge_audio_segments(audio_files)
    
    output_path = os.path.join(OUTPUT_DIR, 'vigil-station-demo-voiceover.mp4')
    print("\nMerging video with voiceover...")
    merge_video_audio(video_path, merged_audio, output_path)
    
    import shutil
    screenshots_src = os.path.join(SCRIPT_DIR, 'screenshots')
    screenshots_dst = os.path.join(OUTPUT_DIR, 'screenshots')
    if os.path.exists(screenshots_dst):
        shutil.rmtree(screenshots_dst)
    shutil.copytree(screenshots_src, screenshots_dst)
    print(f"Screenshots copied to: {screenshots_dst}")
    
    print("\n=== Done! ===")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
