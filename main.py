from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton,
    QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIcon
import os
from video_analysis import analyze_videos_in_folder

class VideoAnalysisWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, input_folder, output_folder, keywords, parent=None):
        super().__init__(parent)
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.keywords = keywords

    def run(self):
        try:
            output_csv = os.path.join(self.output_folder, "combined_report.csv")
            analyze_videos_in_folder(self.input_folder, self.keywords, output_csv, self.output_folder)
            self.progress.emit(100)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.finished.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Video Analiz ve Raporlama Uygulaması")
        self.setGeometry(100, 100, 600, 400)

        # Uygulama simgesini ayarlama
        self.setWindowIcon(QIcon("app_icon.ico"))

        self.input_folder = ""
        self.output_folder = ""
        self.keywords = []
        self.timer = QTimer()
        self.elapsed_seconds = 0

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Giriş klasörü seçimi
        self.input_label = QLabel("Giriş Klasörü:")
        layout.addWidget(self.input_label)

        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Giriş klasörünü seçin...")
        layout.addWidget(self.input_line)

        self.input_button = QPushButton("Gözat")
        self.input_button.clicked.connect(self.select_input_folder)
        layout.addWidget(self.input_button)

        # Çıkış klasörü seçimi
        self.output_label = QLabel("Çıkış Klasörü:")
        layout.addWidget(self.output_label)

        self.output_line = QLineEdit()
        self.output_line.setPlaceholderText("Çıkış klasörünü seçin...")
        layout.addWidget(self.output_line)

        self.output_button = QPushButton("Gözat")
        self.output_button.clicked.connect(self.select_output_folder)
        layout.addWidget(self.output_button)

        # Anahtar kelimeler girişi
        self.keywords_label = QLabel("Anahtar Kelimeler (virgülle ayırarak yazın):")
        layout.addWidget(self.keywords_label)

        self.keywords_line = QLineEdit()
        self.keywords_line.setPlaceholderText("Örneğin: kelime1, kelime2, kelime3")
        layout.addWidget(self.keywords_line)

        # Analiz başlat düğmesi
        self.start_button = QPushButton("Analizi Başlat")
        self.start_button.clicked.connect(self.start_analysis)
        layout.addWidget(self.start_button)

        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Zaman sayaçı
        self.timer_label = QLabel("Geçen Süre: 0 dakika 0 saniye")
        layout.addWidget(self.timer_label)

        # Ana widget
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Giriş Klasörü Seç")
        if folder:
            self.input_folder = folder
            self.input_line.setText(folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Çıkış Klasörü Seç")
        if folder:
            self.output_folder = folder
            self.output_line.setText(folder)

    def start_analysis(self):
        if not self.input_folder or not self.output_folder:
            QMessageBox.warning(self, "Hata", "Giriş ve çıkış klasörlerini seçmelisiniz!")
            return

        self.keywords = self.keywords_line.text().split(",")
        if not self.keywords:
            QMessageBox.warning(self, "Hata", "Anahtar kelimeler boş olamaz!")
            return

        self.elapsed_seconds = 0
        self.timer.timeout.connect(self.update_timer)
        self.timer.start(1000)

        self.worker = VideoAnalysisWorker(self.input_folder, self.output_folder, self.keywords)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.start()

    def update_timer(self):
        self.elapsed_seconds += 1
        minutes, seconds = divmod(self.elapsed_seconds, 60)
        self.timer_label.setText(f"Geçen Süre: {minutes} dakika {seconds} saniye")

    def analysis_finished(self):
        self.timer.stop()
        QMessageBox.information(self, "Tamamlandı", "Analiz tamamlandı!")
        self.progress_bar.setValue(0)
        self.timer_label.setText("Geçen Süre: 0 dakika 0 saniye")

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
