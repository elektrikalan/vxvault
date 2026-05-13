# VX Vault Collector & Scraper 🛡️

VX Vault üzerinden güncel zararlı yazılım (malware) verilerini toplamak, analiz etmek ve yönetmek için geliştirilmiş kapsamlı bir araç setidir. Bu proje, hem hızlı veri çekme işlemleri için bir komut satırı betiği (`vxvault_scraper.py`) hem de gelişmiş özelliklere sahip modern bir masaüstü arayüzü (`vxvault_collector`) sunar.

## 🚀 Temel Özellikler

- **Otomatik Giriş:** `vxvault.net` üzerindeki dinamik giriş şifresini otomatik olarak tespit eder ve giriş yapar.
- **Veri Kazıma (Scraping):** Tüm malware listesini (Tarih, URL, MD5, IP, Araçlar) sayfa sayfa tarayarak çeker.
- **Çoklu Kayıt Formatı:** Toplanan verileri hem **SQLite** veritabanında saklar hem de **CSV** formatında dışa aktarır.
- **Modern GUI (vxvault_collector):** CustomTkinter kullanılarak tasarlanmış, kullanıcı dostu bir masaüstü uygulaması.
- **Zararlı Örneği İndirme:** Tespit edilen URL'lerden zararlı yazılım örneklerini güvenli bir şekilde indirme altyapısı (opsiyonel).
- **Veri Filtreleme:** Büyük veri setleri içinde hızlı arama ve filtreleme imkanı.

## 📁 Proje Yapısı

```text
vxvault/
├── vxvault_scraper.py      # Bağımsız, hızlı veri kazıma betiği
├── vxvault_collector/      # Gelişmiş GUI uygulaması ve modüler yapı
│   ├── app/                # Uygulama mantığı ve GUI bileşenleri
│   ├── core/               # Çekirdek fonksiyonlar
│   ├── models/             # Veri modelleri
│   └── zararlilar/         # İndirilen örneklerin saklandığı klasör
├── .gitignore              # Git tarafından takip edilmeyecek dosyalar
└── README.md               # Proje dökümantasyonu
```

## 🛠️ Kurulum

1. Projeyi bilgisayarınıza indirin.
2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r vxvault_collector/requirements.txt
   ```
   *(Not: Pandas ve BeautifulSoup4 gereklidir.)*

## 📖 Kullanım

### 1. Hızlı Veri Kazıyıcı (CLI)
Sadece verileri hızlıca çekip CSV/DB olarak kaydetmek istiyorsanız:
```bash
python vxvault_scraper.py
```
Program size kaç kayıt çekmek istediğinizi soracaktır.

### 2. Gelişmiş Uygulama (GUI)
Görsel bir arayüz üzerinden yönetmek ve ek özellikleri kullanmak istiyorsanız:
```bash
cd vxvault_collector
python -m app.main
```

## ⚠️ Önemli Uyarı
Bu araç **zararlı yazılım (malware)** verileri ile çalışmaktadır. İndirilen dosyalar sisteminize zarar verebilir. Bu aracı sadece izole edilmiş (Sandboxed) analiz ortamlarında ve eğitim/araştırma amaçlı kullanınız. Oluşabilecek zararlardan kullanıcı sorumludur.

---
*Bu proje, siber güvenlik araştırmacıları için veri toplama sürecini otomatize etmek amacıyla geliştirilmiştir.*
