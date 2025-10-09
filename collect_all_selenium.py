"""
Сбор данных со всех источников + Selenium для Дзена
Этот скрипт использует Selenium для обхода капчи Яндекс.Дзен
"""
import subprocess
import sys

if __name__ == '__main__':
    print("=" * 70)
    print("ЗАПУСК ПОЛНОГО СБОРА ДАННЫХ")
    print("=" * 70)
    print("✓ VK")
    print("✓ Telegram")
    print("✓ Новости (Google News)")
    print("✓ Яндекс.Дзен (Selenium - обход капчи)")
    print("✓ Одноклассники")
    print("=" * 70)
    print()
    
    # Запуск final_collection.py (Selenium используется по умолчанию)
    result = subprocess.run([sys.executable, 'final_collection.py'], cwd='.')
    sys.exit(result.returncode)
