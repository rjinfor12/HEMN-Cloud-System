import os
from PIL import Image, ImageSequence
from moviepy import VideoClip
import numpy as np

def convert_webp_to_mp4(input_path, output_path, fps=10):
    print(f"Converting {input_path} to {output_path}...")
    
    # Abrir o WebP animado com Pillow
    with Image.open(input_path) as img:
        frames = []
        for frame in ImageSequence.Iterator(img):
            # Converter frame para RGB (Pillow para Numpy)
            frames.append(np.array(frame.convert("RGB")))
        
        duration = len(frames) / fps
        
        def make_frame(t):
            frame_idx = int(t * fps)
            if frame_idx >= len(frames):
                frame_idx = len(frames) - 1
            return frames[frame_idx]
        
        clip = VideoClip(make_frame, duration=duration)
        clip.write_videofile(output_path, fps=fps, codec="libx264")

if __name__ == "__main__":
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    
    files_to_convert = [
        ("Propaganda_HEMN_Mobile.webp", "Propaganda_HEMN_Mobile.mp4"),
        ("Propaganda_HEMN_Computador.webp", "Propaganda_HEMN_Computador.mp4")
    ]
    
    for webp_name, mp4_name in files_to_convert:
        input_f = os.path.join(desktop, webp_name)
        output_f = os.path.join(desktop, mp4_name)
        
        if os.path.exists(input_f):
            try:
                convert_webp_to_mp4(input_f, output_f)
                print(f"SUCCESS: {mp4_name} created.")
            except Exception as e:
                print(f"ERROR converting {webp_name}: {e}")
        else:
            print(f"File not found: {input_f}")
