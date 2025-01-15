import cv2
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import easyocr

"""
    Kullanılan Teknolojiler

    OpenCV: Video karelerini işlemek ve üzerinde çizimler yapmak için kullanılır.
    EasyOCR: Kareler üzerindeki metinleri tanımak için kullanılır.
    ThreadPoolExecutor: Paralel işlem yaparak işlemleri hızlandırır.
    Pandas: Raporları düzenlemek ve CSV dosyası oluşturmak için kullanılır.

    Önemli Noktalar

    Anahtar Kelime Tespiti: EasyOCR ile karelerdeki metinler analiz edilir ve anahtar kelimeler algılanır.
    Paralel İşlem: ThreadPoolExecutor ile kare işleme paralel çalışarak hız kazandırır.
    Zaman Etiketleme: Her kareye video zamanına göre zaman etiketi eklenir.
    Raporlama: Her bir kare için detaylı bilgi bir CSV dosyasına kaydedilir.
"""


def process_frame(frame, frame_count, fps, reader, keywords, output_folder):
    """
    Bu fonksiyon, bir video karesini işleyerek OCR yapar ve belirli anahtar kelimeleri tespit eder.

    Girdi Parametreleri:
        frame: İşlenecek video karesi.
        frame_count: Karedeki sıra numarası.
        fps: Videonun saniyedeki kare sayısı.
        reader: EasyOCR okuyucu nesnesi.
        keywords: Aranacak anahtar kelimelerin listesi.
        output_folder: İşlenmiş karelerin kaydedileceği klasör.
    İşlem Adımları:
        Zaman Hesaplama: Kare numarasından zaman hesaplanır.
        Görsel İşleme:
            Karesel büyütme ve gri tonlama yapılır.
            Gaussian blur ve adaptif eşikleme (adaptive thresholding) uygulanır.
        OCR Uygulaması:
            EasyOCR kullanılarak metin algılanır.
            Anahtar kelimeler karede bulunursa, bu kelimeler kaydedilir ve kare işaretlenir.
        Kaydetme: Anahtar kelime bulunan kareler işaretlenir ve bir dosyaya kaydedilir.
        Sonuç: Karede bulunan anahtar kelimeler, zaman bilgisi, dosya adı ve uyarı bilgisi döndürülür.
    """
    
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
    
    """
    Bu fonksiyon, bir video dosyasını kare kare analiz eder.

    Girdi Parametreleri:
        video_path: Analiz edilecek video dosyasının yolu.
        keywords: Aranacak anahtar kelimelerin listesi.
        output_folder: Karelerin kaydedileceği klasör.
        max_workers: Paralel işlem için kullanılacak işlemci sayısı.
    İşlem Adımları:
        EasyOCR okuyucu nesnesi oluşturulur.
        Video karesi kareler okunur ve belirli bir hızda (ör. her 2 saniyede bir kare) analiz edilir.
        Kareler process_frame fonksiyonu ile işlenir.
        İşlem tamamlandıktan sonra kareler serbest bırakılır ve sonuçlar döndürülür.
    """
    
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
    """
    Bu fonksiyon, bir klasördeki tüm videoları analiz eder ve sonuçları birleştirir.

    Girdi Parametreleri:
        folder_path: Videoların bulunduğu klasör yolu.
        keywords: Aranacak anahtar kelimelerin listesi.
        output_csv: Birleştirilmiş raporun kaydedileceği CSV dosyası.
        output_folder: Karelerin kaydedileceği ana klasör.
        max_workers: Paralel işlem için işlemci sayısı.
    İşlem Adımları:
        Klasördeki tüm .mp4 dosyaları listelenir.
        Her video için analyze_video fonksiyonu çağrılır ve sonuçlar toplanır.
        Sonuçlar bir pandas DataFrame'e kaydedilir ve birleştirilmiş bir rapor CSV dosyası oluşturulur.
    """
    
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
