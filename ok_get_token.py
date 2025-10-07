"""
Скрипт для получения Access Token для OK API
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

print("="*70)
print("ПОЛУЧЕНИЕ ACCESS TOKEN ДЛЯ OK API")
print("="*70)

print("\n📋 Шаг 1: Получите права разработчика")
print("-"*70)
print("1. Откройте: https://ok.ru/devaccess")
print("2. Нажмите 'Получить права разработчика'")

print("\n📋 Шаг 2: Создайте приложение на OK")
print("-"*70)
print("1. Откройте: https://ok.ru/vitrine/myuploaded")
print("2. Нажмите 'Добавить приложение'")
print("3. Заполните форму:")
print("   - Название: ТНС энерго Мониторинг")
print("   - Имя в ссылке: tns_monitoring (латиницей)")
print("   - Описание: Система мониторинга")
print("\n4. Добавьте платформу OAuth:")
print("   - Ссылка на страницу: http://localhost:5000")
print("   - Список redirect_uri: http://localhost:5000/oauth/callback")
print("\n5. Сохраните и проверьте email - там будут ключи:")
print("   - Application ID")
print("   - Public Key")
print("   - Secret Key")

print("\n" + "="*70)
print("📋 Шаг 3: Получите Access Token")
print("-"*70)
print("\n⭐ РЕКОМЕНДУЕТСЯ: Используйте встроенный генератор!")
print("-"*70)
print("1. Откройте настройки вашего приложения")
print("   URL: https://ok.ru/game/{ваш_app_id}")
print("2. Прокрутите вниз до блока 'Вечный access_token'")
print("3. Нажмите кнопку генерации")
print("4. Скопируйте access_token и session_secret_key")
print("\nЭто САМЫЙ ПРОСТОЙ способ!")

print("\n" + "="*70)
print("📋 Альтернатива: OAuth авторизация")
print("-"*70)
print("Если встроенный генератор не работает, используйте OAuth:")

print("\n" + "="*70)
print("📋 Шаг 4: Добавьте ключи в .env")
print("-"*70)
print("Откройте файл .env и добавьте:")
print("""
# OK API
OK_APP_ID=ваш_app_id
OK_PUBLIC_KEY=ваш_public_key
OK_SECRET_KEY=ваш_secret_key
OK_ACCESS_TOKEN=получите_на_шаге_3
""")

print("\n" + "="*70)
print("📋 Шаг 3: Получите Access Token")
print("-"*70)

# Запрашиваем APP_ID
app_id = input("\nВведите ваш Application ID: ").strip()

if not app_id:
    print("\n❌ Application ID не указан")
    sys.exit(1)

# Формируем URL для авторизации
redirect_uri = "http://localhost:5000/oauth/callback"
scope = "VALUABLE_ACCESS;LONG_ACCESS_TOKEN;GROUP_CONTENT"

auth_url = f"https://connect.ok.ru/oauth/authorize?client_id={app_id}&scope={scope}&response_type=token&redirect_uri={redirect_uri}&layout=w"

print("\n" + "="*70)
print("🔗 URL для получения токена:")
print("-"*70)
print(auth_url)

print("\n" + "="*70)
print("📋 Инструкция:")
print("-"*70)
print("1. Откройте URL выше в браузере")
print("2. Войдите в свой аккаунт OK")
print("3. Разрешите доступ приложению")
print("4. Вас перенаправит на:")
print("   http://localhost:5000/oauth/callback#access_token=...")
print("5. Скопируйте значение access_token из URL")
print("   (часть после #access_token= до & или до конца)")

print("\n" + "="*70)
input("\nНажмите Enter после получения токена...")

access_token = input("\nВставьте полученный Access Token: ").strip()

if not access_token:
    print("\n❌ Access Token не указан")
    sys.exit(1)

print("\n" + "="*70)
print("✅ Токен получен!")
print("-"*70)

# Показываем что добавить в .env
print("\nДобавьте в файл .env:")
print(f"""
OK_APP_ID={app_id}
OK_ACCESS_TOKEN={access_token}
""")

print("\n" + "="*70)
print("📋 Следующий шаг: Добавьте PUBLIC_KEY и SECRET_KEY")
print("-"*70)
print("Не забудьте также добавить:")
print("OK_PUBLIC_KEY=ваш_public_key")
print("OK_SECRET_KEY=ваш_secret_key")

print("\n" + "="*70)
print("🚀 После настройки запустите тест:")
print("-"*70)
print("python test_ok_api.py")

print("\n" + "="*70)
print("✅ Готово!")
print("="*70)
