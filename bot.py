import os
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

LOGIN_URL = "https://www.biletix.com/auth/TURKIYE/tr/login"
QUEUE_URL = "https://tmturkiye.queue-it.net/?c=tmturkiye&e=sebnemferah&t=https%3A%2F%2Fwww.biletix.com%2Fetkinlik%2F5PSF0%2FTURKIYE%2Ftr&cid=tr-TR&l=Sebnem%20Ferah"

BILETIX_EMAIL = os.environ["BILETIX_EMAIL"]
BILETIX_PASSWORD = os.environ["BILETIX_PASSWORD"]
GMAIL_SENDER = os.environ["GMAIL_SENDER"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
NOTIFY_EMAIL = os.environ["NOTIFY_EMAIL"]


def send_email(subject, body):
    msg = MIMEMultipart()
    msg["From"] = GMAIL_SENDER
    msg["To"] = NOTIFY_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SENDER, NOTIFY_EMAIL, msg.as_string())
    print(f"Mail gönderildi: {subject}")


def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


def dismiss_cookie_banner(driver):
    try:
        wait = WebDriverWait(driver, 5)
        accept_btn = wait.until(EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler")))
        accept_btn.click()
        print("Cookie banner kapatıldı.")
        time.sleep(1)
    except Exception:
        print("Cookie banner yok veya zaten kapalı.")


def login(driver):
    print("Biletix'e giriş yapılıyor...")
    driver.get(LOGIN_URL)
    wait = WebDriverWait(driver, 20)

    # Cookie banner'ı kapat
    dismiss_cookie_banner(driver)

    # E-posta
    email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email'], input[formcontrolname='email']")))
    email_input.clear()
    email_input.send_keys(BILETIX_EMAIL)

    # Şifre
    pass_input = driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[formcontrolname='password']")
    pass_input.clear()
    pass_input.send_keys(BILETIX_PASSWORD)

    # JavaScript ile tıkla (popup engellemesin)
    login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    driver.execute_script("arguments[0].click();", login_btn)

    time.sleep(4)
    print(f"Giriş sonrası URL: {driver.current_url}")


def wait_for_queue(driver):
    print("Queue-it sayfasına gidiliyor...")
    driver.get(QUEUE_URL)

    send_email(
        "🎵 Şebnem Ferah Botu Başladı",
        "Bot çalışıyor, geri sayım bekleniyor. Satış açılınca haber vereceğim."
    )

    while True:
        current_url = driver.current_url
        print(f"Mevcut URL: {current_url}")

        if "biletix.com" in current_url:
            print("Yönlendirme algılandı!")
            return True

        time.sleep(3)


def click_queue_image(driver):
    print("Sıraya giriş görseli aranıyor...")
    wait = WebDriverWait(driver, 15)

    try:
        img = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "img.img_ad")))
        driver.execute_script("arguments[0].click();", img)
        print("Görsele tıklandı.")
    except Exception:
        print("img_ad bulunamadı, devam ediliyor...")

    time.sleep(3)
    return driver.current_url


def main():
    driver = get_driver()
    try:
        login(driver)
        wait_for_queue(driver)
        final_url = click_queue_image(driver)

        send_email(
            "🚨 SIRAYA GİRDİN! Şebnem Ferah",
            f"Sıraya başarıyla girdin!\n\nŞu anki URL:\n{final_url}\n\nHemen tarayıcından bu linke git ve sepete ekle!"
        )

        print("İşlem tamamlandı. 5 dakika bekleniyor...")
        time.sleep(300)

    except Exception as e:
        send_email(
            "❌ Bot Hatası - Şebnem Ferah",
            f"Bot bir hatayla karşılaştı:\n\n{str(e)}"
        )
        print(f"HATA: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
