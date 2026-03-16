"""
selenium_runner.py — eMaktab login moduli
Ishlaydigan oddiy yondashuv asosida yozilgan.
"""

import time
import logging
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

log = logging.getLogger('selenium_runner')

EMAKTAB_URL    = os.environ.get('EMAKTAB_URL', 'https://login.emaktab.uz')
LOGIN_TIMEOUT  = int(os.environ.get('LOGIN_TIMEOUT', '15'))
AFTER_LOAD     = int(os.environ.get('PAGE_LOAD_WAIT', '5'))
AFTER_SUBMIT   = 5   # ishlaydigan kod bilan bir xil


def _make_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1280,720')

    # Render da chromedriver yo'li
    for path in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']:
        if os.path.exists(path):
            return webdriver.Chrome(service=Service(path), options=opts)

    return webdriver.Chrome(options=opts)


def run_login(emaktab_login: str, emaktab_password: str) -> dict:
    driver = None
    try:
        log.info(f"Login boshlandi: {emaktab_login[:3]}***")
        driver = _make_driver()
        wait   = WebDriverWait(driver, LOGIN_TIMEOUT)

        # ── Sahifani och ─────────────────────────────
        driver.get(EMAKTAB_URL)
        time.sleep(AFTER_LOAD)

        # ── Login maydonini top ───────────────────────
        login_input = wait.until(
            EC.presence_of_element_located((By.NAME, 'login'))
        )

        # ── Parol maydonini top ───────────────────────
        password_input = driver.find_element(By.NAME, 'password')

        # ── Kiritish ──────────────────────────────────
        login_input.clear()
        password_input.clear()
        login_input.send_keys(emaktab_login)
        password_input.send_keys(emaktab_password)

        # ── Submit ────────────────────────────────────
        submit = driver.find_element(By.CSS_SELECTOR, "input[type='submit']")
        submit.click()

        time.sleep(AFTER_SUBMIT)

        # ── Natijani aniqlash ─────────────────────────
        current_url = driver.current_url.lower()
        log.info(f"Submit dan keyin URL: {current_url}")

        # Hali login sahifasida tursa — login xato
        if 'login.emaktab.uz' in current_url:
            log.warning(f"Login muvaffaqiyatsiz — hali login sahifasida: {emaktab_login}")
            return {'status': 'error', 'detail': "Login/parol noto'g'ri yoki kirish rad etildi"}

        # URL o'zgardi — muvaffaqiyatli
        log.info(f"Login muvaffaqiyatli: {emaktab_login}")
        return {'status': 'success', 'detail': f'OK. URL: {current_url[:60]}'}

    except Exception as e:
        msg = str(e).split('\n')[0][:120]
        log.error(f"Xato: {msg}")
        return {'status': 'error', 'detail': msg}

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
                