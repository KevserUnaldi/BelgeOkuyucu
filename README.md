# BelgeOkuyucu - Kimlik/Ehliyet/Pasaport/İkamet gibi belgeleri otomatik tespit ve OCR

Bu proje, seçtiğiniz bir klasör içindeki `.jpg`, `.jpeg` ve `.png` uzantılı görselleri tarayarak; **kimlik, ehliyet, pasaport ** gibi belirli belge türlerini algılar, üzerlerindeki metinleri **OCR** (Optik Karakter Tanıma) yöntemiyle okur ve ilgili bilgileri (TC Kimlik No, Ad Soyad, Doğum Tarihi vb.) çıkarmayı hedefler. Ayrıca, tespit ettiği belgelerin kopyalarını üzerine “belge türü” etiketi basarak ayrı bir **SONUÇLAR** klasörüne kaydeder. 

## İçindekiler
- [Özellikler](#özellikler)
- [Gereksinimler](#gereksinimler)
- [Kurulum](#kurulum)
  - [1. Python Kurulumu](#1-python-kurulumu)
  - [2. Gerekli Python Paketleri](#2-gerekli-python-paketleri)
  - [3. Tesseract Kurulumu](#3-tesseract-kurulumu)
- [Kullanım](#kullanım)
- [Kodun Genel Mimarisi ve Çalışma Mantığı](#kodun-genel-mimarisi-ve-çalışma-mantığı)
  - [1. Arayüz (PyQt5)](#1-arayüz-pyqt5)
  - [2. OCR (Tesseract & EasyOCR)](#2-ocr-tesseract--easyocr)
  - [3. Metin Analizi ve Belge Tespiti](#3-metin-analizi-ve-belge-tespiti)
  - [4. Sonuçların Görselleştirilmesi ve Kaydedilmesi](#4-sonuçların-görselleştirilmesi-ve-kaydedilmesi)
- [Olası Hatalar ve Çözümler](#olası-hatalar-ve-çözümler)


## Özellikler
- **Kolay kullanım**: Sürükle-bırak tarzı bir klasör seçimiyle içerikteki görüntüleri otomatik olarak işler.
- **Toplu tarama**: Seçilen klasör ve alt klasörlerdeki tüm `.jpg`, `.jpeg`, `.png` dosyaları aranır.
- **Türkçe ve İngilizce** destekli OCR: `pytesseract` ve `easyocr` ile çoklu denemeler yaparak doğruluk oranını artırır.
- **Belge türü tespiti**: Kimlik, ehliyet ve pasaport gibi belgeleri anahtar kelime analiziyle otomatik saptar.
- **Çıkarılan bilgi**: TC Kimlik No, Ad Soyad, Doğum Tarihi, Belge No, Geçerlilik Tarihi, Uyruk gibi bilgiler metinden ayrıştırılır.
- **Raporlama**: Tespit edilen metinlerin ve çıkarılan bilgilerin düzenli bir özetini kullanıcıya gösterir.
- **Sonuçların kaydedilmesi**: Tespit edilen belgelerin kopyaları üzerine belge türü etiketi basılarak `SONUCLAR` klasörüne kaydedilir.

## Gereksinimler
- Python 3.7 veya üzeri
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [PyQt5](https://pypi.org/project/PyQt5/)
- [OpenCV](https://pypi.org/project/opencv-python/)
- [pytesseract](https://pypi.org/project/pytesseract/)
- [easyocr](https://github.com/jaidedai/EasyOCR)

## Kurulum

### 1. Python Kurulumu
Eğer Python kurulu değilse [Python resmi internet sitesi](https://www.python.org/) üzerinden işletim sisteminize uygun sürümü indirip kurun.

> **Not**: Python 3.x sürümünü tercih ediniz.

### 2. Gerekli Python Paketleri
Kodun çalışması için gerekli paketleri aşağıdaki komutla kurabilirsiniz:

```bash
pip install PyQt5 opencv-python pytesseract easyocr
```

Veya gereksinimler dosyası oluşturduysanız:

```bash
pip install -r requirements.txt
```

### 3. Tesseract Kurulumu
**Tesseract** OCR kütüphanesinin sistemde kurulu olması gerekir. İşletim sisteminize göre kurulum yönergeleri:

- **macOS (Homebrew kullanarak)**  
  ```bash
  brew install tesseract
  ```
  Ardından, `pytesseract.pytesseract.tesseract_cmd` değişkeninin Tesseract konumunu gösterdiğinden emin olun (Kodda `/opt/homebrew/bin/tesseract` olarak ayarlanmıştır).

- **Windows (Chocolatey kullanarak)**  
  ```bash
  choco install tesseract
  ```
  veya resmi Tesseract [exe dosyasını](https://github.com/UB-Mannheim/tesseract/wiki) indirerek kurabilirsiniz.

- **Linux (Ubuntu/Debian tabanlı)**  
  ```bash
  sudo apt-get update
  sudo apt-get install tesseract-ocr
  ```
  Daha sonra `pytesseract.pytesseract.tesseract_cmd` değişkenine `/usr/bin/tesseract` gibi uygun bir path atayabilirsiniz.

> **Önemli**: Tesseract’ın Türkçe (`tur`) ve İngilizce (`eng`) dil veri dosyaları yüklü olmalıdır. Diller yüklü değilse:
> 
> ```bash
> sudo apt-get install tesseract-ocr-tur
> ```

## Kullanım

1. Proje dosyasına gidin:
   ```bash
   cd belge-okuyucu
   ```
2. Python ile kodu çalıştırın:
   ```bash
   python main.py
   ```
   (Burada `main.py`, gönderilen kod dosyanızın ismi neyse o olmalı.)

3. Arayüz açıldıktan sonra:
   - **Klasör Seç** düğmesine tıklayarak içindeki görselleri taramak istediğiniz klasörü seçin.
   - Klasör seçimi yapıldığında, klasördeki `.jpg`, `.jpeg`, `.png` dosyalarının sayısı otomatik olarak sağda gösterilir.
   - **TARA** düğmesine tıklayarak işlem başlatın. Kod, klasörü ve alt klasörleri tarar ve **SONUÇLAR** adlı bir klasör oluşturur. Tespit edilen her belge bu klasöre kaydedilir.
   - Tarama bitince, arayüzde tespit edilen belgelerin bir listesi ve OCR sonuçları görünecektir.
   - **Önceki** / **Sonraki** butonlarıyla tespit edilen belgeler arasında gezinip, sağ tarafta ayrıntılı metin ve çıkarılmış bilgiler kısmını inceleyebilirsiniz.

## Kodun Genel Mimarisi ve Çalışma Mantığı

### 1. Arayüz (PyQt5)

- **Ana Pencere (`BelgeOkuyucu` sınıfı)**: 
  - `QMainWindow` kalıtımı yaparak uygulamanın ana penceresini oluşturur. 
  - Üst kısımda klasör seçme (`QFileDialog`) ve tarama butonları bulunur, alt kısımda ise **görüntü gösterimi** ve **OCR sonuç metni** bulunur.

- **Gezinme Butonları**: 
  - `Önceki` ve `Sonraki` butonları tespit edilen belgeler arasında geçiş yapılmasını sağlar.
  - Metin alanı (`QTextEdit`) salt okunur olarak ayarlanmıştır ve tarama sırasında durum mesajlarını, tarama sonunda da OCR sonuçlarını gösterir.

### 2. OCR (Tesseract & EasyOCR)

- **`easyocr`**:  
  - Özellikle karmaşık karakter setlerinde veya farklı yazı tiplerinde iyi sonuç verebilen bir OCR kütüphanesidir. 
  - `easyocr.Reader(['tr', 'en'])` ile Türkçe ve İngilizce destekli okunur.

- **`pytesseract`**:  
  - Tesseract motorunu kullanan Python arayüzüdür. 
  - Farklı `psm` (page segmentation mode) değerleri (3, 4, 6) denenerek metnin daha iyi okunması hedeflenir. 
  - Ayrıca **ikili (thresholded) görüntü** üzerinden de deneme yapılır.

### 3. Metin Analizi ve Belge Tespiti

- Kod, OCR’dan dönen metinleri **büyük harfe** çevirerek filtreleme yapar.
- **Belge türü** tespitinde `zorunlu` ve `destekleyici` anahtar kelime listelerine bakılır. 
  - Örneğin, `Kimlik` için “T.C.”, “KİMLİK” gibi kelimeler zorunluyken, “NÜFUS” veya “CÜZDANİ” destekleyici olarak eklenir. 
  - Toplam skor yeterli olduğunda, ilgili belge türü olarak sınıflandırılır.
- **Metin içi tarama** ile:
  - **TC Kimlik No**, 
  - **Ad Soyad**,
  - **Doğum Tarihi**,
  - **Belge No**,
  - **Geçerlilik Tarihi** ve
  - **Uyruk** gibi temel bilgiler düzenli ifadeler ve basit string aramalarıyla tespit edilmeye çalışılır.

### 4. Sonuçların Görselleştirilmesi ve Kaydedilmesi

- Tespit edilen belge türü, üzerine **kırmızı yarı saydam bir dikdörtgen ve metin** basılarak görselleştirilir.
- **Sonuç görseli**, “`SONUCLAR`” klasörüne **`BelgeTürü_OrjinalDosyaAdı`** şeklinde kaydedilir.
- Kullanıcı arayüzünde (sağ panel) bulunan text edit alanında, belgeye ait özet sonuçlar **ASCII çerçeve** ile gösterilir.

## Olası Hatalar ve Çözümler

1. **Tesseract bulunamadı**:  
   - `pytesseract.pytesseract.tesseract_cmd` yolunu sisteminizde Tesseract’ın kurulduğu konuma göre güncelleyin.  
   - Örnek: `/opt/homebrew/bin/tesseract`, `/usr/bin/tesseract`, `C:\Program Files\Tesseract-OCR\tesseract.exe` gibi.

2. **Tesseract Türkçe dili yüklü değil**:  
   - `tur.traineddata` dosyasını Tesseract dizinine eklemelisiniz.  
   - Ubuntu/Debian tabanlı sistemlerde `sudo apt-get install tesseract-ocr-tur` ile yükleyebilirsiniz.

3. **EasyOCR paketinden kaynaklı hatalar**:  
   - EasyOCR, ilk kullanımda model dosyalarını indirir. İndirme sırasında kesinti olursa yarım kalabilir. Paketi yeniden yüklemeyi veya model dosyalarını manuel indirmeyi deneyin.

4. **PyQt5 arayüz açılmıyor veya gri ekran**:  
   - Kurulum sonrasında `pip show pyqt5` ile doğru kurulduğundan ve sisteminize uyumlu olduğundan emin olun.  
   - macOS için `os.environ['QT_MAC_WANTS_LAYER'] = '1'` gibi ayarların kodda uygulandığından emin olun.

5. **Performans sorunları**:  
   - Çok büyük boyutlu görsellerde işlem uzun sürebilir. Kodda `max_width = 2500` ile yeniden boyutlandırma yapılıyor, bu ayarı düşürerek hız kazanabilirsiniz.  
   - Ayrıca GPU desteğine sahip EasyOCR kurulumu (CUDA vb.) kullanmak, performansı artırabilir.
