import httpx
import json
import os
from datetime import datetime, timedelta
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

class Mumin:
    def __init__(self, sehir, ilce=None):
        self.sehir = sehir.upper()  
        self.ilce = ilce.upper() if ilce else None 
        self.sehir_id = None
        self.ilce_id = None
        self.today = datetime.today().strftime("%d.%m.%Y")
        self.gunluk_namaz_vakitleri = {}

    """API'den, girilen şehir ve ilçe ismine göre verileri JSON'a kaydeder."""
    async def get_prayer_times(self):
        async with httpx.AsyncClient() as client:
            api_url = "https://ezanvakti.herokuapp.com/sehirler/2"
            response = await client.get(api_url)
            data = response.json()

            for item in data:
                if item["SehirAdi"] == self.sehir or item["SehirAdiEn"] == self.sehir:
                    self.sehir_id = item["SehirID"]
                    break

            api_url = f"https://ezanvakti.herokuapp.com/ilceler/{self.sehir_id}"
            response = await client.get(api_url)
            data = response.json()

            for item in data:
                if item["IlceAdi"] == self.ilce or item["IlceAdiEn"] == self.ilce:
                    self.ilce_id = item["IlceID"]
                    break

            if self.ilce_id is None:
                return await Mumin(self.sehir, self.sehir).get_prayer_times()

            api_url = f"https://ezanvakti.herokuapp.com/vakitler/{self.ilce_id}"
            response = await client.get(api_url)
            data = response.json()

            filename = f'{self.sehir}_{self.ilce}_namaz_vakitleri.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            print(f"Namaz vakitleri '{filename}' dosyasına kaydedildi.")

    """JSON dosyasını açıp verileri alma"""    
    async def read_prayer_times(self):
        filename = f'{self.sehir}_{self.ilce}_namaz_vakitleri.json'
        
        if not os.path.exists(filename):
            self.ilce = self.sehir
            filename = f'{self.sehir}_{self.ilce}_namaz_vakitleri.json'  
        
        with open(filename, 'r', encoding='utf-8') as f:
            aylik_namaz_vakitleri = json.load(f)
        
        for i in aylik_namaz_vakitleri:
            if i["MiladiTarihKisa"] == self.today:
                self.gunluk_namaz_vakitleri["Tarih"] = i["MiladiTarihKisa"]
                self.gunluk_namaz_vakitleri["İkindi"] = i["Ikindi"]
                self.gunluk_namaz_vakitleri["Akşam"] = i["Aksam"]
                self.gunluk_namaz_vakitleri["Yatsı"] = i["Yatsi"]
                
        return self.gunluk_namaz_vakitleri
      
    """ Alınan verileri namaz saatine göre hesaplar ve kalan süreyi yazdırır"""  
    async def calc_time(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        while True:
            now = datetime.now()

            for namaz, vakit in self.gunluk_namaz_vakitleri.items():
                if namaz != "Tarih":  
                    namaz_vakti = datetime.strptime(vakit, "%H:%M").time()
                    suanki_saat = now.time()
                    bildirim_vakti = (datetime.combine(datetime.today(), namaz_vakti) - timedelta(minutes=30)).time()

                    if bildirim_vakti <= suanki_saat < namaz_vakti:
                        print_text = f"{namaz} ezanına yarım saat kaldı!"
                        await update.message.reply_text(print_text)
                        await asyncio.sleep(1800)  
                        break  

            await asyncio.sleep(300)  