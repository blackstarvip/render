"""
selenium_runner.py — eMaktab login moduli
"""

import time
import logging
import os

log = logging.getLogger('selenium_runner')

EMAKTAB_URL    = os.environ.get('EMAKTAB_URL', 'https://login.emaktab.uz')
LOGIN_TIMEOUT  = int(os.environ.get('LOGIN_TIMEOUT', '15'))
PAGE_LOAD_WAIT = int(os.environ.get('PAGE_LOAD_WAIT', '3'))

# Faqat ANIQ captcha elementlari — oddiy so'zlar EMAS
CAPTCHA_SELECTORS = [
    'iframe[src*="recaptcha"]',
    'iframe[src*="hcaptcha"]',
    'iframe[src*="captcha"]',
    'div.g-recaptcha',
    'div.h-captcha',
    'div[class*="captcha"]',
    'input[name*="captcha"]',
    '.cf-turnstile',
    '#captcha',
]

SUCCESS_URL_PATTERNS = [
    'dashboard', 'cabinet', 'profile', 'home', 'main',
    'sahifa', 'bosh', 'asosiy', 'lk/', 'account', 'journal',
]

ERROR_BODY_PATTERNS = [
    "noto'g'ri", 'notogri', 'xato parol', 'login xato',
    'неверный пароль', 'incorrect password', 'wrong password',
    'invalid credentials',
]


def _make_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1280,720')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--disable-extensions')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument(
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    for path in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']:
        if os.path.exists(path):
            try:
                driver = webdriver.Chrome(service=Service(path), options=opts)
                driver.set_page_load_timeout(LOGIN_TIMEOUT + 20)
                return driver
            except Exception:
                continue

    # PATH dan urinib ko'rish
    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(LOGIN_TIMEOUT + 20)
    return driver


def _has_captcha(driver) -> bool:
    """
    Faqat REAL captcha elementlarini tekshiradi.
    Matn tahlili EMAS — DOM elementlari orqali.
    """
    from selenium.webdriver.common.by import By
    for sel in CAPTCHA_SELECTORS:
        try:
            els = driver.find_elements(By.CSS_SELECTOR, sel)
            if els:
                log.warning(f"Captcha element topildi: {sel}")
                return True
        except Exception:
            continue
    return False


def _find_element(driver, selectors, wait=None):
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    for by, sel in selectors:
        try:
            if wait:
                el = wait.until(EC.presence_of_element_located((by, sel)))
            else:
                el = driver.find_element(by, sel)
            if el and el.is_displayed():
                return el
        except (TimeoutException, NoSuchElementException):
            continue
    return None


def run_login(emaktab_login: str, emaktab_password: str) -> dict:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.common.exceptions import TimeoutException, WebDriverException

    driver = None
    try:
        log.info(f"Login boshlandi: {emaktab_login[:3]}***")
        driver = _make_driver()
        wait   = WebDriverWait(driver, LOGIN_TIMEOUT)

        # ── 1. Sahifani ochish ────────────────────────────────────────────────
        driver.get(EMAKTAB_URL)
        time.sleep(PAGE_LOAD_WAIT)
        log.info(f"Sahifa yuklandi. URL: {driver.current_url}")

        # ── 2. Captcha — faqat DOM elementi orqali ────────────────────────────
        if _has_captcha(driver):
            return {'status': 'captcha', 'detail': 'Sahifada captcha widget topildi'}

        # ── 3. Login maydoni ──────────────────────────────────────────────────
        login_field = _find_element(driver, [
            (By.NAME,         'login'),
            (By.NAME,         'username'),
            (By.ID,           'login'),
            (By.ID,           'username'),
            (By.CSS_SELECTOR, 'input[autocomplete="username"]'),
            (By.CSS_SELECTOR, 'input[type="text"]'),
        ], wait)

        if not login_field:
            return {'status': 'error', 'detail': 'Login maydoni topilmadi'}

        login_field.clear()
        login_field.send_keys(emaktab_login)
        time.sleep(0.3)

        # ── 4. Parol maydoni ──────────────────────────────────────────────────
        password_field = _find_element(driver, [
            (By.NAME,         'password'),
            (By.ID,           'password'),
            (By.CSS_SELECTOR, 'input[type="password"]'),
            (By.CSS_SELECTOR, 'input[autocomplete="current-password"]'),
        ])

        if not password_field:
            return {'status': 'error', 'detail': 'Parol maydoni topilmadi'}

        password_field.clear()
        password_field.send_keys(emaktab_password)
        time.sleep(0.3)

        # ── 5. Captcha tekshiruvi (credentials kiritilgandan so'ng) ──────────
        if _has_captcha(driver):
            return {'status': 'captcha', 'detail': 'Formada captcha widget paydo bo\'ldi'}

        # ── 6. Submit ─────────────────────────────────────────────────────────
        submit = _find_element(driver, [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'input[type="submit"]'),
            (By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'kir')]"),
            (By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'login')]"),
        ])

        if submit:
            submit.click()
        else:
            password_field.send_keys(Keys.RETURN)

        time.sleep(PAGE_LOAD_WAIT + 2)

        # ── 7. Natija ─────────────────────────────────────────────────────────
        final_url    = driver.current_url.lower()
        final_source = driver.page_source.lower()
        log.info(f"So'nggi URL: {final_url}")

        # Captcha submit dan keyin — faqat DOM elementi
        if _has_captcha(driver):
            return {'status': 'captcha', 'detail': 'Submit dan so\'ng captcha paydo bo\'ldi'}

        # Muvaffaqiyat: URL o'zgardi va login sahifasi emas
        if any(p in final_url for p in SUCCESS_URL_PATTERNS):
            log.info("Login muvaffaqiyatli (URL pattern)")
            return {'status': 'success', 'detail': f'URL: {final_url[:80]}'}

        # Muvaffaqiyat: login URL dan chiqildi
        login_domain = EMAKTAB_URL.lower().replace('https://', '').replace('http://', '').split('/')[0]
        if login_domain not in final_url or 'login' not in final_url:
            if final_url != EMAKTAB_URL.lower().rstrip('/') + '/':
                log.info("Login muvaffaqiyatli (URL o'zgardi)")
                return {'status': 'success', 'detail': f'URL: {final_url[:80]}'}

        # Xato: aniq xato matni
        if any(p in final_source for p in ERROR_BODY_PATTERNS):
            return {'status': 'error', 'detail': "Login yoki parol noto'g'ri"}

        # Hali login sahifasida
        log.warning(f"Login sahifasida qolindi: {final_url}")
        return {'status': 'error', 'detail': "Login muvaffaqiyatsiz — sahifa o'zgarmadi"}

    except TimeoutException:
        return {'status': 'error', 'detail': 'Sahifa yuklanmadi (timeout)'}
    except WebDriverException as e:
        msg = str(e).split('\n')[0][:120]
        log.error(f"WebDriver xato: {msg}")
        return {'status': 'error', 'detail': f'Browser xatosi: {msg}'}
    except Exception as e:
        log.exception(f"Kutilmagan xato: {e}")
        return {'status': 'error', 'detail': str(e)[:120]}
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
    
