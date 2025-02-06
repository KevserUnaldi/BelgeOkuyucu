import sys
import cv2
import numpy as np
import pytesseract
import easyocr
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QWidget, QFileDialog, QLabel, QTextEdit, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt

# macOS için gerekli ayarlar
os.environ['QT_MAC_WANTS_LAYER'] = '1'

# Qt özniteliklerini uygulama oluşturulmadan önce ayarla
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

class BelgeOkuyucu(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Secure coding için gerekli ayar
        if hasattr(self, 'setWindowFlag'):
            self.setWindowFlag(Qt.WindowFullscreenButtonHint, False)
        
        # Bellek yönetimi için
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.setWindowTitle("Belge Okuyucu")
        self.setGeometry(100, 100, 1200, 800)
        
        # Ana widget ve layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Üst kısım - Butonlar
        top_layout = QHBoxLayout()
        self.klasor_sec_btn = QPushButton("Klasör Seç")
        self.tara_btn = QPushButton("TARA")
        self.klasor_yolu_label = QLabel("Seçilen klasör: ")
        
        top_layout.addWidget(self.klasor_sec_btn)
        top_layout.addWidget(self.tara_btn)
        top_layout.addWidget(self.klasor_yolu_label)
        top_layout.addStretch()
        
        # Orta kısım - Görüntü ve metin
        middle_layout = QHBoxLayout()
        
        # Sol taraf - Görüntü gösterimi ve navigasyon butonları
        left_layout = QVBoxLayout()
        
        # Görüntü gösterimi
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_scroll = QScrollArea()
        self.image_scroll.setWidget(self.image_label)
        self.image_scroll.setWidgetResizable(True)
        
        # Navigasyon butonları
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Önceki")
        self.next_btn = QPushButton("Sonraki")
        self.image_counter_label = QLabel("0/0")
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.image_counter_label)
        nav_layout.addWidget(self.next_btn)
        
        left_layout.addWidget(self.image_scroll)
        left_layout.addLayout(nav_layout)
        
        # Sağ taraf - Metin gösterimi
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        
        middle_layout.addLayout(left_layout, 2)
        middle_layout.addWidget(self.text_edit, 1)
        
        # Layout'ları ana layout'a ekle
        layout.addLayout(top_layout)
        layout.addLayout(middle_layout)
        
        # Buton bağlantıları
        self.klasor_sec_btn.clicked.connect(self.klasor_sec)
        self.tara_btn.clicked.connect(self.tara)
        self.prev_btn.clicked.connect(self.show_previous_image)
        self.next_btn.clicked.connect(self.show_next_image)
        
        # Değişkenler
        self.secilen_klasor = ""
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        
        # Görüntü listesi ve mevcut görüntü indeksi
        self.detected_images = []  # [(image_path, text), ...]
        self.current_image_index = -1
        
        # Başlangıçta navigasyon butonlarını devre dışı bırak
        self.update_nav_buttons()

    def klasor_sec(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        
        if dialog.exec_():
            self.secilen_klasor = dialog.selectedFiles()[0]
            self.klasor_yolu_label.setText(f"Seçilen klasör: {self.secilen_klasor}")
            
            # Seçilen klasördeki dosya sayısını göster
            supported_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
            file_count = sum(1 for root, _, files in os.walk(self.secilen_klasor) 
                            if "SONUCLAR" not in root
                            for f in files if f.endswith(supported_extensions))
            
            self.text_edit.setText(f"Seçilen klasörde {file_count} adet görüntü dosyası bulundu.")

    def detect_id_documents(self, image_path):
        try:
            # Görüntüyü oku
            image = cv2.imread(image_path)
            if image is None:
                return False
            
            # OCR için görüntü ön işleme
            # Boyut optimizasyonu
            max_width = 2500
            height, width = image.shape[:2]
            if width > max_width:
                scale = max_width / width
                image = cv2.resize(image, None, fx=scale, fy=scale)
            
            # Görüntü iyileştirme teknikleri
            # 1. Gri tonlama
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 2. Gürültü azaltma
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # 3. Kontrast iyileştirme
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # 4. Keskinleştirme
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            sharpened = cv2.filter2D(enhanced, -1, kernel)
            
            # 5. Eşikleme
            _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # OCR işlemi - çoklu deneme
            texts = []
            
            # EasyOCR ile deneme
            reader = easyocr.Reader(['tr', 'en'])
            easyocr_results = reader.readtext(enhanced)
            texts.append(' '.join([result[1] for result in easyocr_results]))
            
            # Tesseract ile farklı modlarda deneme
            psm_modes = [3, 4, 6]  # Farklı sayfa segmentasyon modları
            for psm in psm_modes:
                config = f'--psm {psm} --oem 3'
                texts.append(pytesseract.image_to_string(enhanced, lang='tur+eng', config=config))
                texts.append(pytesseract.image_to_string(binary, lang='tur+eng', config=config))
            
            # Tüm metinleri birleştir ve temizle
            combined_text = ' '.join(texts).upper()
            
            # Belge türleri ve geliştirilmiş anahtar kelimeler
            document_types = {
                'Kimlik': {
                    'zorunlu': ['T.C.', 'KİMLİK', 'TC'],
                    'destekleyici': ['NÜFUS', 'CÜZDANİ', 'REPUBLIC', 'TURKEY', 'TÜRKIYE', 
                                   'IDENTIFICATION', 'CARD', 'SERIAL', 'SERİ', 'NO']
                },
                'Ehliyet': {
                    'zorunlu': ['SÜRÜCÜ', 'BELGESİ', 'SURUCU'],
                    'destekleyici': ['DRIVING', 'LICENCE', 'LICENSE', 'MOTORLU', 'TAŞIT', 
                                   'SINIF', 'CLASS', 'TARİH', 'DATE']
                },
                'Pasaport': {
                    'zorunlu': ['PASAPORT', 'PASSPORT'],
                    'destekleyici': ['REPUBLIC OF TURKEY', 'TÜRKIYE CUMHURIYETI', 
                                   'HOLDER', 'VALID', 'GEÇERLİ', 'TYPE', 'TİP']
                },
                'İkamet': {
                    'zorunlu': ['İKAMET', 'IKAMET', 'RESIDENCE'],
                    'destekleyici': ['PERMIT', 'İZNİ', 'IZNI', 'YABANCI', 'FOREIGNER', 
                                   'DOCUMENT', 'BELGE']
                }
            }
            
            # En iyi eşleşmeyi bul
            best_match = None
            max_score = 0
            
            for doc_type, keywords in document_types.items():
                # Zorunlu kelimelerden en az birinin olması gerekiyor
                if not any(keyword in combined_text for keyword in keywords['zorunlu']):
                    continue
                    
                # Toplam skor hesapla
                zorunlu_matches = sum(2 for keyword in keywords['zorunlu'] 
                                    if keyword in combined_text)
                destekleyici_matches = sum(1 for keyword in keywords['destekleyici'] 
                                         if keyword in combined_text)
                total_score = zorunlu_matches + destekleyici_matches
                
                if total_score > max_score:
                    max_score = total_score
                    best_match = doc_type
            
            # Minimum skor eşiği (en az 1 zorunlu + 2 destekleyici kelime)
            if max_score >= 4:
                # Metin düzenleme fonksiyonu
                def format_text(text):
                    # Gereksiz boşlukları temizle
                    text = ' '.join(text.split())
                    # Türkçe karakter düzeltmeleri
                    replacements = {
                        'I': 'İ', 'i': 'ı',
                        'KIMLIK': 'KİMLİK', 'SURUCÜ': 'SÜRÜCÜ',
                        'TURKIYE': 'TÜRKİYE', 'CUMHURIYETI': 'CUMHURİYETİ',
                        'IKAMET': 'İKAMET', 'IZNI': 'İZNİ'
                    }
                    for old, new in replacements.items():
                        text = text.replace(old, new)
                    return text
                
                # Metin çıkarma ve düzenleme
                extracted_info = {
                    'TC_NO': '',
                    'AD_SOYAD': '',
                    'DOGUM_TARIHI': '',
                    'BELGE_NO': '',
                    'GECERLILIK': '',
                    'UYRUK': ''
                }
                
                # Metni satırlara böl
                lines = combined_text.split('\n')
                
                for line in lines:
                    line = format_text(line)
                    
                    # TC Kimlik No tespiti
                    if any(x in line for x in ['TC:', 'T.C.', 'KIMLIK NO']):
                        numbers = ''.join(filter(str.isdigit, line))
                        if len(numbers) == 11:  # TC Kimlik No 11 haneli olmalı
                            extracted_info['TC_NO'] = numbers
                    
                    # Ad Soyad tespiti
                    elif any(x in line for x in ['ADI', 'SOYADI', 'SURNAME', 'NAME']):
                        # Sayı ve özel karakterleri temizle
                        name = ''.join(c for c in line if c.isalpha() or c.isspace())
                        if len(name) > 5:  # Minimum uzunluk kontrolü
                            extracted_info['AD_SOYAD'] = name.strip()
                    
                    # Doğum tarihi tespiti
                    elif any(x in line for x in ['DOGUM', 'BIRTH']):
                        # Tarih formatını bul (GG.AA.YYYY veya DD.MM.YYYY)
                        import re
                        date_match = re.search(r'\d{2}[./-]\d{2}[./-]\d{4}', line)
                        if date_match:
                            extracted_info['DOGUM_TARIHI'] = date_match.group()
                    
                    # Belge numarası tespiti
                    elif any(x in line for x in ['BELGE NO', 'SERI NO', 'SERIAL']):
                        # Alfanumerik karakterleri al
                        doc_no = ''.join(c for c in line if c.isalnum())
                        if len(doc_no) >= 5:  # Minimum uzunluk kontrolü
                            extracted_info['BELGE_NO'] = doc_no
                    
                    # Geçerlilik tarihi tespiti
                    elif any(x in line for x in ['GECERLI', 'VALID', 'EXPIRE']):
                        date_match = re.search(r'\d{2}[./-]\d{2}[./-]\d{4}', line)
                        if date_match:
                            extracted_info['GECERLILIK'] = date_match.group()
                    
                    # Uyruk tespiti
                    elif any(x in line for x in ['UYRUK', 'NATIONALITY']):
                        # Sayı ve özel karakterleri temizle
                        nationality = ''.join(c for c in line if c.isalpha() or c.isspace())
                        if len(nationality) > 3:  # Minimum uzunluk kontrolü
                            extracted_info['UYRUK'] = nationality.strip()
                
                # Görüntü üzerine belge türü etiketi ekle
                height, width = image.shape[:2]
                overlay = image.copy()
                
                # Etiket metnini küçük harfe çevir ve Türkçe karakter düzeltmesi yap
                label_map = {
                    'Kimlik': 'kimlik belgesi',
                    'Ehliyet': 'ehliyet belgesi',
                    'Pasaport': 'pasaport belgesi',
                    'İkamet': 'ikamet belgesi'
                }
                label = label_map.get(best_match, best_match.lower())
                
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = width / 1000  # Görüntü genişliğine göre ölçekle
                thickness = max(2, int(font_scale * 2))
                
                # Metin boyutunu hesapla
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, font, font_scale, thickness)
                
                # Etiket için arka plan dikdörtgeni
                padding = 10
                rect_coords = [
                    (0, 0),
                    (text_width + 2 * padding, text_height + 2 * padding)
                ]
                
                # Yarı saydam arka plan çiz
                cv2.rectangle(overlay, rect_coords[0], rect_coords[1], 
                             (0, 0, 255), -1)
                cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)
                
                # Metni yaz
                cv2.putText(image, label,
                           (padding, text_height + padding),
                           font, font_scale, (255, 255, 255), thickness)
                
                # Metin formatlamayı geliştir
                def format_extracted_text(text, max_length=50):
                    words = text.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        if len(' '.join(current_line + [word])) <= max_length:
                            current_line.append(word)
                        else:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    return '\n'.join(lines)
                
                # Sonuç metnini formatla
                full_text = f"""
╔══════════════════════════════════════
║ BELGE TESPİT SONUCU
╠══════════════════════════════════════
║ Belge Türü: {best_match}
║ Eşleşme Puanı: {max_score}
╠══════════════════════════════════════
║ ÇIKARILAN BİLGİLER
╠══════════════════════════════════════
║ TC Kimlik No: {extracted_info['TC_NO'] or 'Tespit Edilemedi'}
║ Ad Soyad: {extracted_info['AD_SOYAD'] or 'Tespit Edilemedi'}
║ Doğum Tarihi: {extracted_info['DOGUM_TARIHI'] or 'Tespit Edilemedi'}
║ Belge No: {extracted_info['BELGE_NO'] or 'Tespit Edilemedi'}
║ Geçerlilik: {extracted_info['GECERLILIK'] or 'Tespit Edilemedi'}
║ Uyruk: {extracted_info['UYRUK'] or 'Tespit Edilemedi'}
╠══════════════════════════════════════
║ TESPIT EDİLEN METİN
╠══════════════════════════════════════
║ {format_extracted_text(combined_text[:1000])}
╚══════════════════════════════════════
"""
                
                # Görüntüyü kaydet
                if not os.path.exists(self.sonuclar_klasoru):
                    os.makedirs(self.sonuclar_klasoru)
                    
                output_path = os.path.join(self.sonuclar_klasoru, 
                    f'{best_match}_{os.path.basename(image_path)}')
                cv2.imwrite(output_path, image)
                
                # Sonuçları listeye ekle
                self.detected_images.append((output_path, full_text))
                print(f"Belge tespit edildi: {best_match} - {image_path}")
                return True
                
            return False
            
        except Exception as e:
            print(f"OCR hatası: {str(e)}")
            return False

    def tara(self):
        if not self.secilen_klasor:
            self.text_edit.setText("Lütfen önce bir klasör seçin!")
            return
            
        # GUI'yi dondurma
        self.tara_btn.setEnabled(False)
        self.klasor_sec_btn.setEnabled(False)
        QApplication.processEvents()
        
        try:
            # Sonuçlar klasörünü oluştur
            self.sonuclar_klasoru = os.path.join(self.secilen_klasor, "SONUCLAR")
            if not os.path.exists(self.sonuclar_klasoru):
                os.makedirs(self.sonuclar_klasoru)
            
            # Önceki sonuçları temizle
            self.detected_images.clear()
            self.current_image_index = -1
            self.text_edit.clear()
            
            # Desteklenen dosya uzantıları
            supported_extensions = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')
            
            # Toplam dosya sayısını bul
            total_files = sum(1 for root, _, files in os.walk(self.secilen_klasor) 
                             if "SONUCLAR" not in root
                             for f in files if f.endswith(supported_extensions))
            
            processed_count = 0
            detected_count = 0
            
            for root, _, files in os.walk(self.secilen_klasor):
                # SONUCLAR klasörünü atla
                if "SONUCLAR" in root:
                    continue
                    
                for filename in files:
                    if filename.endswith(supported_extensions):
                        processed_count += 1
                        image_path = os.path.join(root, filename)
                        
                        # İlerleme durumunu göster
                        progress_text = f"\nİşlenen: {processed_count}/{total_files} - {filename}"
                        self.text_edit.append(progress_text)
                        self.text_edit.moveCursor(self.text_edit.textCursor().End)
                        QApplication.processEvents()
                        
                        try:
                            if self.detect_id_documents(image_path):
                                detected_count += 1
                                self.text_edit.append("✓ Belge tespit edildi!")
                            else:
                                self.text_edit.append("✗ Belge tespit edilemedi!")
                        except Exception as e:
                            self.text_edit.append(f"Hata: {str(e)}")
                        
                        # Her dosyadan sonra GUI'yi güncelle
                        QApplication.processEvents()
                        
                        # İşlem çok uzun sürüyorsa kontrol
                        if processed_count % 5 == 0:  # Her 5 dosyada bir kontrol
                            QApplication.processEvents()
            
            # Sonuçları göster
            self.text_edit.append(f"\nTarama tamamlandı!")
            self.text_edit.append(f"Toplam taranan dosya: {total_files}")
            self.text_edit.append(f"Tespit edilen belge: {detected_count}")
            self.text_edit.append(f"Benzersiz tespit: {len(self.detected_images)}")
            
            # İlk görüntüyü göster
            if self.detected_images:
                self.current_image_index = 0
                self.show_current_image()
            
            # Navigasyon butonlarını güncelle
            self.update_nav_buttons()
            
        except Exception as e:
            self.text_edit.append(f"\nHata oluştu: {str(e)}")
        finally:
            # GUI'yi tekrar aktif et
            self.tara_btn.setEnabled(True)
            self.klasor_sec_btn.setEnabled(True)
            QApplication.processEvents()

    def show_current_image(self):
        if not self.detected_images or self.current_image_index < 0:
            print("Gösterilecek görüntü yok")
            return
        
        try:
            # Mevcut görüntü bilgilerini al
            image_path, text = self.detected_images[self.current_image_index]
            
            # QPixmap ile görüntüyü yükle
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                print("Pixmap yüklenemedi")
                return
            
            # Görüntüyü pencere boyutuna sığdır
            scaled_pixmap = pixmap.scaled(
                self.image_scroll.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            
            # Görüntüyü göster
            self.image_label.setPixmap(scaled_pixmap)
            
            # Metni göster - koyu arka plan ve beyaz yazı
            self.text_edit.setStyleSheet("""
                QTextEdit {
                    font-family: 'Courier New';
                    font-size: 12pt;
                    line-height: 1.5;
                    background-color: #1e1e1e;
                    color: #ffffff;
                    padding: 10px;
                    border: none;
                }
            """)
            self.text_edit.setText(text)
            
            # Sayacı güncelle
            self.image_counter_label.setText(
                f"{self.current_image_index + 1}/{len(self.detected_images)}"
            )
            
        except Exception as e:
            print(f"Görüntü gösterme hatası: {str(e)}")

    def show_previous_image(self):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.show_current_image()
            self.update_nav_buttons()

    def show_next_image(self):
        if self.current_image_index < len(self.detected_images) - 1:
            self.current_image_index += 1
            self.show_current_image()
            self.update_nav_buttons()

    def update_nav_buttons(self):
        # Navigasyon butonlarını güncelle
        has_images = len(self.detected_images) > 0
        self.prev_btn.setEnabled(has_images and self.current_image_index > 0)
        self.next_btn.setEnabled(has_images and 
                                self.current_image_index < len(self.detected_images) - 1)
        
        if has_images:
            print(f"Mevcut görüntü indeksi: {self.current_image_index + 1}/{len(self.detected_images)}")

    def show_image(self, cv_img):
        try:
            # Görüntüyü pencere boyutuna göre ölçekle
            window_size = self.image_scroll.size()
            height, width = cv_img.shape[:2]
            
            # En-boy oranını koru
            scale = min(window_size.width() / width, window_size.height() / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Görüntüyü yeniden boyutlandır
            resized = cv2.resize(cv_img, (new_width, new_height))
            
            # Qt görüntüsüne dönüştür
            rgb_image = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            self.image_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Görüntü gösterme hatası: {str(e)}")

if __name__ == '__main__':
    try:
        # QApplication'ı en başta oluştur
        app = QApplication(sys.argv)
        
        # macOS için ek güvenlik ayarları
        if hasattr(app, 'setDesktopFileName'):
            app.setDesktopFileName('BelgeOkuyucu')
            
        # NSApplicationDelegate ayarları
        if sys.platform == 'darwin':  # macOS kontrolü
            app.setAttribute(Qt.AA_DontShowIconsInMenus, False)
            
        window = BelgeOkuyucu()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Uygulama hatası: {str(e)}")