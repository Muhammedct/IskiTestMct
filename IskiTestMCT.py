import requests
from bs4 import BeautifulSoup
import os

# --- BURAYI KENDİNİZE GÖRE DÜZENLEYİN ---
# Takip etmek istediğiniz ilçeleri ve mahalleleri buraya yazın.
# Eğer bir ilçedeki tüm mahalleleri takip etmek isterseniz, mahalle listesini boş bırakın: "İlçe Adı": []
# Mahalle adlarını İSKİ'nin sitesindeki gibi yazmaya özen gösterin.
TAKIP_EDILEN_BOLGELER = {
    "SARIYER": []
}
# --- DÜZENLEME SONU ---

# GitHub Actions'tan alacağımız gizli bilgiler
TELEGRAM_BOT_TOKEN = os.environ.get('8009738525:AAFlhuc_25MqbvzqhJOoQ3xu37XpOcBF6MY')
TELEGRAM_CHAT_ID = os.environ.get('1041245012')

ISKI_URL = "https://iski.istanbul/abone-hizmetleri/ariza-kesinti/"

def bildirim_gonder(mesaj):
    """Belirtilen Telegram kanalına mesaj gönderir."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Hata: Telegram token veya chat ID bulunamadı.")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mesaj,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("Bildirim başarıyla gönderildi.")
        else:
            print(f"Bildirim gönderilemedi. Hata: {response.text}")
    except Exception as e:
        print(f"Mesaj gönderilirken bir istisna oluştu: {e}")

def kesintileri_kontrol_et():
    """İSKİ web sitesini kontrol eder ve ilgili kesintileri bildirir."""
    print("İSKİ web sitesi kontrol ediliyor...")
    try:
        response = requests.get(ISKI_URL, timeout=30)
        response.raise_for_status() # HTTP hatası varsa istisna fırlat
    except requests.RequestException as e:
        print(f"Web sitesine ulaşılamadı: {e}")
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    
    # İSKİ'nin kesinti listesini içeren ana bölümü bul
    kesinti_listesi = soup.find('div', class_='bolge-kesinti-list')

    if not kesinti_listesi:
        print("Kesinti listesi bulunamadı. Site yapısı değişmiş olabilir.")
        return

    bulunan_kesintiler = []
    
    # Her bir kesinti öğesini işle
    for item in kesinti_listesi.find_all('div', class_='kesinti-item'):
        ilce_tag = item.find('h3')
        ilce = ilce_tag.text.strip().upper() if ilce_tag else "Bilinmiyor"

        # Takip listemizdeki bir ilçe mi?
        if ilce in TAKIP_EDILEN_BOLGELER:
            mahalleler_tag = item.find('div', class_='etkilenen-mahalleler')
            kesinti_mahalleleri_str = mahalleler_tag.text.replace("Etkilenen Mahalleler:", "").strip()
            kesinti_mahalleleri = [m.strip().upper() for m in kesinti_mahalleleri_str.split(',')]
            
            takip_edilen_mahalleler = TAKIP_EDILEN_BOLGELER[ilce]
            
            # Eğer ilçe için özel mahalle belirtilmemişse veya kesinti olan mahallelerden en az biri takip listemizdeyse
            if not takip_edilen_mahalleler or any(m in kesinti_mahalleleri for m in takip_edilen_mahalleler):
                ariza_nedeni_tag = item.find('p', string=lambda t: t and "Arıza Nedeni" in t)
                ariza_nedeni = ariza_nedeni_tag.text.replace("Arıza Nedeni:", "").strip() if ariza_nedeni_tag else "Belirtilmemiş"

                kesinti_mesaji = (
                    f"<b>💧 SU KESİNTİSİ BİLDİRİMİ 💧</b>\n\n"
                    f"<b>İlçe:</b> {ilce.title()}\n"
                    f"<b>Mahalleler:</b> {', '.join(m.title() for m in kesinti_mahalleleri)}\n"
                    f"<b>Neden:</b> {ariza_nedeni}"
                )
                bulunan_kesintiler.append(kesinti_mesaji)

    if bulunan_kesintiler:
        print(f"{len(bulunan_kesintiler)} adet ilgili kesinti bulundu.")
        # Tüm bulunan kesintileri tek bir mesajda birleştir
        full_mesaj = "\n\n---\n\n".join(bulunan_kesintiler)
        bildirim_gonder(full_mesaj)
    else:
        print("Sizi ilgilendiren bir kesinti bulunamadı.")


if __name__ == "__main__":
    kesintileri_kontrol_et()