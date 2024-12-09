# Video Analiz ve Raporlama Uygulaması

Bu uygulama, belirttiğiniz klasördeki videolar üzerinde anahtar kelime analizi yapar ve sonuçları raporlar. Geliştirilen arayüz sayesinde kolayca video klasörlerini seçebilir, rapor oluşturabilir ve işlem sürelerini takip edebilirsiniz.

## Özellikler
- Videolarda belirli anahtar kelimeleri tespit etme.
- Anahtar kelimenin geçtiği çerçeveleri görüntü dosyası olarak kaydetme.
- Çıktıları bir CSV dosyası olarak raporlama.
- Kullanıcı dostu PyQt5 tabanlı arayüz.

## Gereksinimler
Bu uygulama, Python 3.8 veya üzeri bir sürümde çalışır. Gerekli kütüphaneleri kurmak için şu adımları takip edin:

1. Gerekli kütüphaneleri yüklemek için:
   ```bash
   pip install -r requirements.txt

2. Sistemde GPU kullanılacaksa EasyOCR için GPU sürücülerinin yüklü olduğundan emin olun.

# Kullanım

1. main.py dosyasını çalıştırarak uygulamayı başlatın:
python main.py

2. Açılan arayüzde:

   - Giriş ve çıkış klasörlerini seçin.
   - Anahtar kelimeleri girin (örneğin: keyword1, keyword2).
   - "Analizi Başlat" düğmesine tıklayın.

3. İşlem tamamlandığında sonuçlar şu şekilde kaydedilir:

   - CSV raporu: output_folder/combined_report.csv
   - Anahtar kelimelerin bulunduğu çerçeve görüntüleri: output_folder/<video_name>/

# Önemli Notlar

- Windows için: Uygulamayı bağımsız bir .exe dosyası olarak derlemek için PyInstaller kullanılabilir:
pyinstaller --onefile --icon=app_icon.ico main.py

- GPU Kullanımı: EasyOCR GPU kullanımı varsayılan olarak açıktır. Eğer sisteminizde GPU yoksa, video_analysis.py içinde gpu=False olarak ayarlayın:
reader = easyocr.Reader(["en"], gpu=False)

# Bilinen Sorunlar ve Çözümler

1. EasyOCR GPU hatası: Eğer GPU'nuz desteklenmiyorsa, yukarıdaki şekilde GPU kullanımını devre dışı bırakın.

2. Excel'de CSV sorunları: CSV verileri Excel'de tek bir sütunda görünüyorsa, açarken , ayırıcı seçeneğini kullandığınızdan emin olun.
