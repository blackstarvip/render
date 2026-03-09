"""
selenium_runner.py
==================
Selenium orqali eMaktab ga login qilish moduli.
app.py dan chaqiriladi.

Qaytaradi:
    dict: {'status': 'success'|'error'|'captcha', 'detail': str}
"""

import time
import logging
import os

log = logging.getLogger('selenium_runner')

EMAKTAB_URL    = os.environ.get('EMAKTAB_URL', 'https://login.emaktab.uz')
LOGIN_TIMEOUT  = int(os.environ.get('LOGIN_TIMEOUT', '15'))
PAGE_LOAD_WAIT = int(os.environ.get('PAGE_LOAD_WAIT', '3'))

# Captcha kalit so'zlari
CAPTCHA_KEYWORDS = [
    'captcha', 'recaptcha', 'hcaptcha', 'cf-turnstile',
    'robot', 'human verification', 'prove you are human',
]

# Muvaffaqiyatli login ko'rsatkichlari (URL da bo'lishi kerak)
SUCCESS_URL_PATTERNS = [
    'dashboard', 'cabinet', 'profile', 'home', 'main',
    'sahifa', 'bosh', 'asosiy', 'lk/', 'account',
]

# Xato ko'rsatkichlari (sahifa tarkibida)
ERROR_BODY_PATTERNS = [
    'incorrect', 'invalid', 'wrong', 'error',
    "noto'g'ri", 'xato', 'parol', 'notog',
    'неверный', 'ошибка', 'неправильный',
]


def _make_driver():
    """ChromeDriver yaratadi (Render uchun headless)."""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-software-rasterizer')
    opts.add_argument('--window-size=1280,720')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--disable-infobars')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)
    opts.add_argument(
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )

    # Render da chromedriver yo'li
    chromedriver_paths = [
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        '/opt/render/project/.render/chrome/chromedriver',
    ]

    driver = None
    for path in chromedriver_paths:
        if os.path.exists(path):
            try:
                service = Service(path)
                driver = webdriver.Chrome(service=service, options=opts)
                log.info(f"ChromeDriver topildi: {path}")
                break
            except Exception as e:
                log.warning(f"ChromeDriver {path} da ishlamadi: {e}")
                continue

    if driver is None:
        # Oxirgi urinish: PATH dan
        try:
            driver = webdriver.Chrome(options=opts)
            log.info("ChromeDriver PATH dan topildi")
        except Exception as e:
            log.error(f"ChromeDriver topilmadi: {e}")
            raise RuntimeError(f"ChromeDriver o'rnatilmagan: {e}")

    driver.set_page_load_timeout(LOGIN_TIMEOUT + 20)
    return driver


def _has_captcha(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in CAPTCHA_KEYWORDS)


def _find_element_multi(driver, selectors, wait=None):
    """Bir nechta selector urinib, birinchi topilganini qaytaradi."""
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
    """
    eMaktab ga Selenium bilan kiradi.

    Returns:
        {'status': 'success'|'error'|'captcha', 'detail': str}
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException

    driver = None

    try:
        log.info(f"eMaktab ga kirish boshlandi: {emaktab_login[:3]}***")
        driver = _make_driver()
        wait   = WebDriverWait(driver, LOGIN_TIMEOUT)

        # ── 1. Sahifani ochish ──────────────────────────────────────────────
        log.info(f"URL ochilyapti: {EMAKTAB_URL}")
        driver.get(EMAKTAB_URL)
        time.sleep(PAGE_LOAD_WAIT)

        # ── 2. Captcha tekshiruvi (sahifa yuklangandan so'ng) ────────────────
        if _has_captcha(driver.page_source):
            log.warning("Captcha aniqlandi (sahifa yuklanishida)")
            return {'status': 'captcha', 'detail': 'Sahifa yuklanishida captcha aniqlandi'}

        # ── 3. Login maydonini topish ────────────────────────────────────────
        login_selectors = [
            (By.NAME,        'login'),
            (By.NAME,        'username'),
            (By.NAME,        'user_login'),
            (By.ID,          'login'),
            (By.ID,          'username'),
            (By.CSS_SELECTOR, 'input[type="text"]:not([style*="display:none"])'),
            (By.CSS_SELECTOR, 'input[placeholder*="ogin"]'),
            (By.CSS_SELECTOR, 'input[autocomplete="username"]'),
        ]

        login_field = _find_element_multi(driver, login_selectors, wait)
        if not login_field:
            log.error("Login maydoni topilmadi")
            return {'status': 'error', 'detail': 'Login maydoni topilmadi (sahifa tuzilishi o\'zgangan bo\'lishi mumkin)'}

        login_field.clear()
        for char in emaktab_login:
            login_field.send_keys(char)
            time.sleep(0.03)

        # ── 4. Parol maydonini topish ────────────────────────────────────────
        password_selectors = [
            (By.NAME,        'password'),
            (By.NAME,        'user_password'),
            (By.ID,          'password'),
            (By.CSS_SELECTOR, 'input[type="password"]'),
            (By.CSS_SELECTOR, 'input[autocomplete="current-password"]'),
        ]

        password_field = _find_element_multi(driver, password_selectors)
        if not password_field:
            log.error("Parol maydoni topilmadi")
            return {'status': 'error', 'detail': 'Parol maydoni topilmadi'}

        password_field.clear()
        for char in emaktab_password:
            password_field.send_keys(char)
            time.sleep(0.03)

        time.sleep(0.5)

        # ── 5. Captcha tekshiruvi (credentials kiritilgandan so'ng) ─────────
        if _has_captcha(driver.page_source):
            log.warning("Captcha aniqlandi (credentials kiritishdan so'ng)")
            return {'status': 'captcha', 'detail': 'Login formida captcha mavjud'}

        # ── 6. Submit ────────────────────────────────────────────────────────
        submit_selectors = [
            (By.CSS_SELECTOR, 'button[type="submit"]'),
            (By.CSS_SELECTOR, 'input[type="submit"]'),
            (By.CSS_SELECTOR, 'button.login-btn'),
            (By.CSS_SELECTOR, 'button.btn-login'),
            (By.CSS_SELECTOR, 'button.submit'),
            (By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'kir')]"),
            (By.XPATH, "//button[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'login')]"),
            (By.XPATH, "//input[@type='submit']"),
        ]

        submit_btn = _find_element_multi(driver, submit_selectors)
        if submit_btn:
            submit_btn.click()
            log.info("Submit tugmasi bosildi")
        else:
            password_field.send_keys(Keys.RETURN)
            log.info("Enter bosildi (submit tugmasi topilmadi)")

        # ── 7. Natijani kutish ───────────────────────────────────────────────
        time.sleep(PAGE_LOAD_WAIT + 2)

        final_url    = driver.current_url.lower()
        final_source = driver.page_source.lower()

        log.info(f"So'nggi URL: {final_url}")

        # Captcha submit dan keyin
        if _has_captcha(final_source):
            log.warning("Submit dan so'ng captcha aniqlandi")
            return {'status': 'captcha', 'detail': 'Submit dan so\'ng captcha paydo bo\'ldi'}

        # Muvaffaqiyat tekshiruvi
        url_changed  = EMAKTAB_URL.lower().rstrip('/') not in final_url or 'login' not in final_url
        url_success  = any(p in final_url for p in SUCCESS_URL_PATTERNS)
        body_error   = any(p in final_source for p in ERROR_BODY_PATTERNS)

        if url_success:
            log.info("✅ Login muvaffaqiyatli (URL tekshiruvi)")
            return {'status': 'success', 'detail': f"Muvaffaqiyatli. URL: {final_url[:60]}"}

        if body_error and not url_success:
            log.warning("❌ Login xatosi (sahifa xato xabari)")
            return {'status': 'error', 'detail': "Login/parol noto'g'ri"}

        if url_changed and 'login' not in final_url:
            log.info("✅ Login muvaffaqiyatli (URL o'zgardi)")
            return {'status': 'success', 'detail': f"Muvaffaqiyatli. URL: {final_url[:60]}"}

        log.warning(f"❓ Natija aniqlanmadi. URL: {final_url}")
        return {'status': 'error', 'detail': f"Login sahifasidan o'tilmadi. URL: {final_url[:60]}"}

    except TimeoutException as e:
        log.error(f"Timeout: {e}")
        return {'status': 'error', 'detail': 'Sahifa yuklanishi vaqt tugadi (timeout)'}

    except RuntimeError as e:
        log.error(f"Runtime xato: {e}")
        return {'status': 'error', 'detail': str(e)}

    except WebDriverException as e:
        msg = str(e).split('\n')[0][:120]
        log.error(f"WebDriver xato: {msg}")
        return {'status': 'error', 'detail': f"Browser xatosi: {msg}"}

    except Exception as e:
        log.exception(f"Kutilmagan xato: {e}")
        return {'status': 'error', 'detail': f"Kutilmagan xato: {str(e)[:100]}"}

    finally:
        if driver:
            try:
                driver.quit()
                log.info("Driver to'xtatildi")
            except Exception:
                pass
