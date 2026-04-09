"""
selenium_runner.py — tezlashtirilgan versiya
sleep() o'rniga WebDriverWait ishlatiladi
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
from selenium.common.exceptions import TimeoutException, WebDriverException

log = logging.getLogger('selenium_runner')

EMAKTAB_URL   = os.environ.get('EMAKTAB_URL', 'https://login.emaktab.uz')
LOGIN_TIMEOUT = int(os.environ.get('LOGIN_TIMEOUT', '5'))


def _make_driver():
    opts = Options()
    opts.add_argument('--headless=new')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-software-rasterizer')
    opts.add_argument('--single-process')
    opts.add_argument('--no-zygote')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--disable-background-networking')
    opts.add_argument('--disable-default-apps')
    opts.add_argument('--disable-sync')
    opts.add_argument('--disable-translate')
    opts.add_argument('--blink-settings=imagesEnabled=false')
    opts.add_argument('--window-size=1024,600')
    opts.add_argument('--memory-pressure-off')
    opts.add_argument('--js-flags=--max-old-space-size=256')

    prefs = {
        'profile.managed_default_content_settings.images': 2,
        'profile.default_content_setting_values.notifications': 2,
    }
    opts.add_experimental_option('prefs', prefs)

    for path in ['/usr/bin/chromedriver', '/usr/local/bin/chromedriver']:
        if os.path.exists(path):
            return webdriver.Chrome(service=Service(path), options=opts)
    return webdriver.Chrome(options=opts)


def run_login(emaktab_login: str, emaktab_password: str) -> dict:
    driver = None
    t0 = time.time()

    try:
        try:
            driver = _make_driver()
            driver.set_page_load_timeout(LOGIN_TIMEOUT)
        except Exception as e:
            return {'status': 'error', 'detail': f"Chrome can't start: {str(e)[:100] or 'unknown'}"}

        wait = WebDriverWait(driver, LOGIN_TIMEOUT)

        try:
            driver.get(EMAKTAB_URL)
        except Exception as e:
            return {'status': 'error', 'detail': f"Page not found: {str(e)[:100] or 'timeout'}"}

        # sleep(5) o'rniga — element tayyor bo'lishi bilan darhol davom etadi
        try:
            login_input = wait.until(EC.element_to_be_clickable((By.NAME, 'login')))
        except TimeoutException:
            return {'status': 'error', 'detail': "Login field not found"}

        try:
            password_input = wait.until(EC.element_to_be_clickable((By.NAME, 'password')))
        except TimeoutException:
            return {'status': 'error', 'detail': "Password field not found"}

        try:
            submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']")))
        except TimeoutException:
            return {'status': 'error', 'detail': "Submit button not found"}

        login_input.clear()
        login_input.send_keys(emaktab_login)
        password_input.clear()
        password_input.send_keys(emaktab_password)
        submit.click()

        # sleep(8) o'rniga — URL o'zgari bilan darhol davom etadi (max 10s)
        try:
            WebDriverWait(driver, 10).until(EC.url_changes(driver.current_url))
        except TimeoutException:
            pass  # URL o'zgarmadi — login xato deb hisoblanadi

        final_url = driver.current_url.lower()
        elapsed   = round(time.time() - t0, 1)
        log.info(f"URL: {final_url} | Vaqt: {elapsed}s")

        if 'login.emaktab.uz' in final_url:
            return {'status': 'error', 'detail': "Login/Pass error"}

        return {'status': 'success', 'detail': f'OK ({elapsed}s)'}

    except WebDriverException as e:
        msg = str(e).split('\n')[0][:120] if str(e) else 'WebDriver error'
        return {'status': 'error', 'detail': msg}

    except Exception as e:
        msg = str(e).split('\n')[0][:120] if str(e) else 'Unexpected error'
        return {'status': 'error', 'detail': msg}

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
            
