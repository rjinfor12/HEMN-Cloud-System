import cv2
import os

def convert_webp_to_mp4_cv2(input_path, output_path, fps=10):
    print(f"Converting {input_path} to {output_path} with OpenCV...")
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error opening {input_path}")
        return
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Use MP4V or X264
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)
        frame_count += 1
    
    cap.release()
    out.release()
    print(f"Done. {frame_count} frames written.")

if __name__ == "__main__":
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    brain_dir = r"C:\Users\Junior T.I\.gemini\antigravity\brain\918c9b29-fac9-4fa5-8170-4f9be27a2bd5"
    
    # Conversar os arquivos GRANDES que tinham 8MB e 16MB
    files = [
        (os.path.join(brain_dir, "hemn_system_premium_promo_1774022161581.webp"), os.path.join(desktop, "Propaganda_HEMN_Mobile.mp4")),
        (os.path.join(brain_dir, "hemn_system_promo_1774021027779.webp"), os.path.join(desktop, "Propaganda_HEMN_Computador.mp4"))
    ]
    
    for input_p, output_p in files:
        if os.path.exists(input_p):
            convert_webp_to_mp4_cv2(input_p, output_p)
        else:
            print(f"File not found: {input_p}")
