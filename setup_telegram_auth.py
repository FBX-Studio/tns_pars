"""
Скрипт авторизации в Telegram через пользовательский аккаунт
"""
import asyncio
from telethon import TelegramClient
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def setup_telegram():
    """Настройка авторизации Telegram"""
    
    api_id = Config.TELEGRAM_API_ID
    api_hash = Config.TELEGRAM_API_HASH
    phone = Config.TELEGRAM_PHONE
    
    if not api_id or not api_hash:
        print("\n[ERROR] API_ID i API_HASH ne nastroeny v .env fajle!")
        print("\nDlya polucheniya:")
        print("1. Perejdite na https://my.telegram.org")
        print("2. Vojdite s vashim nomerom telefona")
        print("3. Perejdite v 'API Development Tools'")
        print("4. Sozdajte novoe prilozhenie")
        print("5. Skopirujte API_ID i API_HASH v .env fajl")
        return False
    
    print("\n" + "="*60)
    print("NASTROYKA TELEGRAM POLZOVATELSKOGO AKKAUNTA")
    print("="*60)
    print(f"\nAPI ID: {api_id}")
    print(f"API Hash: {api_hash[:10]}...")
    print(f"Telefon: {phone}")
    print("\n" + "="*60)
    
    try:
        # Создаем клиента
        client = TelegramClient('telegram_session', int(api_id), api_hash)
        
        print("\n[+] Podklyuchenie k Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print("\n[!] Trebuetsya avtorizatsiya!")
            print(f"Otpravlyaem kod na nomer: {phone}")
            
            await client.send_code_request(phone)
            
            print("\n[+] Kod otpravlen na vash Telegram!")
            code = input("Vvedite kod iz Telegram: ")
            
            try:
                await client.sign_in(phone, code)
            except Exception as e:
                if 'password' in str(e).lower():
                    print("\n[!] Trebuetsya dvuhfaktornaya autentifikatsiya")
                    password = input("Vvedite parol 2FA: ")
                    await client.sign_in(password=password)
                else:
                    raise
        
        # Проверяем что авторизованы
        me = await client.get_me()
        print("\n[OK] Uspeshno avtorizovany!")
        print(f"   Imya: {me.first_name} {me.last_name or ''}")
        print(f"   Username: @{me.username if me.username else 'ne ustanovlen'}")
        print(f"   ID: {me.id}")
        
        # Тестируем доступ к каналам
        print("\n[+] Proverka dostupa k kanalam...")
        
        test_channels = Config.TELEGRAM_CHANNELS[:5]  # Первые 5 каналов
        print(f"\nProveryaem pervye {len(test_channels)} kanalov:")
        
        accessible_count = 0
        for channel in test_channels:
            try:
                entity = await client.get_entity(channel)
                print(f"  [OK] {channel}: {entity.title}")
                accessible_count += 1
            except Exception as e:
                print(f"  [X] {channel}: {str(e)[:50]}...")
        
        print(f"\nDostupno: {accessible_count}/{len(test_channels)} kanalov")
        
        if accessible_count == 0:
            print("\n[WARNING] Net dostupa ni k odnomu kanalu!")
            print("Vozmozhnye prichiny:")
            print("  1. Ne podpisany na eti kanaly")
            print("  2. Kanaly privatnye ili ne sushhestvuyut")
            print("  3. Nevernye imena kanalov")
        else:
            print("\n[OK] Avtorizatsiya uspeshna! Mozhno zapuskat parsing.")
        
        await client.disconnect()
        
        print("\n" + "="*60)
        print("NASTROYKA ZAVERSHENA")
        print("="*60)
        print("\nFajl sessii sozdan: telegram_session.session")
        print("Teper mozhno zapuskat parsing cherez:")
        print("  python app_enhanced.py")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Oshibka: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("TELEGRAM USER API - NASTROYKA AVTORIZATSII")
    print("="*60)
    print("\nEtot skript nastroit avtorizatsiyu v Telegram cherez vash")
    print("polzovatelskiy akkaunt dlya dostupa k kanalam.\n")
    
    result = asyncio.run(setup_telegram())
    
    if result:
        print("\nGotovo! Mozhno nachinat parsing.")
    else:
        print("\nNastroyka ne zavershena. Proverte konfiguratsiyu.")
