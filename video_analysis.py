import cv2
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import easyocr

def process_frame(frame, frame_count, fps, reader, keywords, output_folder):
    # Frame üzerinde OCR işlemini gerçekleştirir ve bulunan anahtar kelimeleri döner.
    timestamp = frame_count / fps
    resized_frame = cv2.resize(frame, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
    blurred_frame = cv2.GaussianBlur(gray_frame, (5, 5), 0)
    adaptive_thresh = cv2.adaptiveThreshold(
        blurred_frame, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    found_keywords = set()
    file_name = None

    # EasyOCR işlemi
    results = reader.readtext(adaptive_thresh)
    for bbox, word, confidence in results:
        if any(keyword.lower() in word.lower() for keyword in keywords):
            found_keywords.add(word)
            (x_min, y_min), (x_max, y_max) = bbox[0], bbox[2]
            cv2.rectangle(resized_frame, (int(x_min), int(y_min)), (int(x_max), int(y_max)), (0, 255, 0), 2)
            cv2.putText(resized_frame, word, (int(x_min), int(y_min) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    if found_keywords:
        file_name = f"frame_motion_{frame_count}.png"
        output_frame_path = os.path.join(output_folder, file_name)
        if cv2.imwrite(output_frame_path, resized_frame):
            print(f"Frame saved successfully: {output_frame_path}")
        else:
            print(f"Failed to save frame: {output_frame_path}")

    return {
        "Exact Time (s)": round(timestamp, 2),
        "File Name": file_name if found_keywords else "None",
        "Detected Keywords": ", ".join(sorted(found_keywords)) if found_keywords else "None",
        "Warning": 1 if found_keywords else 0,
    }

def analyze_video(video_path, keywords, output_folder, max_workers=4):
    # Bir video dosyasını analiz eder ve sonuçları döner.
    reader = easyocr.Reader(["en"], gpu=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_rate = int(fps * 2)  # 2 saniyede bir analiz yapılacak
    frame_count = 0

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    report_data = []
    tasks = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % frame_rate == 0:
                tasks.append(executor.submit(
                    process_frame, frame, frame_count, fps, reader, keywords, output_folder
                ))

        for task in tasks:
            report_data.append(task.result())

    cap.release()
    return report_data

def analyze_videos_in_folder(folder_path, keywords, output_csv, output_folder, max_workers=4):
    # Bir klasördeki tüm videoları analiz eder ve birleşik bir rapor oluşturur.
    all_report_data = []

    video_files = [f for f in os.listdir(folder_path) if f.endswith(".mp4")]
    for video_file in video_files:
        video_path = os.path.join(folder_path, video_file)
        print(f"Analyzing video: {video_file}")

        video_output_folder = os.path.join(output_folder, os.path.splitext(video_file)[0])
        os.makedirs(video_output_folder, exist_ok=True)

        report_data = analyze_video(video_path, keywords, video_output_folder, max_workers)

        for entry in report_data:
            entry["Video Source"] = video_file

        all_report_data.extend(report_data)

    # Raporu CSV dosyasına kaydetme
    report_df = pd.DataFrame(all_report_data)
    report_df = report_df[["Exact Time (s)", "File Name", "Detected Keywords", "Warning", "Video Source"]]
    report_df.to_csv(output_csv, index=False, sep=",")

    print(f"Analysis complete. Combined report saved to {output_csv}.")
