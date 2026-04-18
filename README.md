# LinkedIn Job Monitor

## Kurulum

```bash
pip install -r requirements.txt
```

`.env.example` dosyasını kopyala, token'larını gir:
```bash
cp .env.example .env
```

## LinkedIn Giriş Gerekiyor mu?

Hayır. Sistem LinkedIn'e **giriş yapmadan** çalışır. Public iş ilanı sayfaları login gerektirmiyor. Hesap riski sıfır.

## Çalıştırma

```bash
python main.py
```

## Arama Sorgularını Değiştirmek

`config.py` dosyasındaki `SEARCH_QUERIES` listesini düzenle:

```python
SEARCH_QUERIES = [
    "machine learning engineer",
    "backend developer python",
    # istediğini ekle/çıkar
]
```

Konumu değiştirmek için `SEARCH_LOCATION` değerini güncelle (boş bırakırsan global arama yapar).

## Zamanlama (Cron) — günde 3 kez

```bash
0 8,13,19 * * * cd /path/to/project && python main.py
```

## Dosyalar

| Dosya | Açıklama |
|-------|----------|
| `config.py` | Tüm ayarlar, sorgular |
| `scraper.py` | LinkedIn scraper |
| `scorer.py` | Ollama LLM skorlama |
| `notifier.py` | Telegram bildirimleri |
| `storage.py` | Duplicate engelleme (JSON) |
| `main.py` | Ana çalıştırma scripti |
| `seen_jobs.json` | İşlenmiş iş ID'leri (otomatik oluşur) |
