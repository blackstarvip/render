"""
eMaktab Automation Bot — Render.com Flask API
=============================================
Bu server:
  - InfinityFree PHP saytidan HTTP so'rovlar qabul qiladi
  - Selenium orqali eMaktab ga login qiladi
  - Natijani JSON formatda qaytaradi

Muhit o'zgaruvchilari (Render Dashboard > Environment):
  BOT_API_KEY   — PHP config dagi RENDER_API_KEY bilan bir xil bo'lishi kerak
  PORT          — Render avtomatik beradi (default: 10000)
"""

import os
import logging
import time
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify
from selenium_runner import run_login

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s'
)
log = logging.getLogger('emaktab_flask')

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['JSON_ENSURE_ASCII'] = False

# API kalitni muhit o'zgaruvchisidan olish
BOT_API_KEY = os.environ.get('BOT_API_KEY', '')

if not BOT_API_KEY:
    log.warning("⚠️  BOT_API_KEY muhit o'zgaruvchisi o'rnatilmagan!")


# ── Auth decorator ────────────────────────────────────────────────────────────
def require_api_key(f):
    """X-API-Key header tekshiradi."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key', '')
        if not BOT_API_KEY:
            log.error("BOT_API_KEY o'rnatilmagan — barcha so'rovlar rad etiladi")
            return jsonify({'status': 'error', 'detail': 'Server sozlanmagan'}), 503
        if key != BOT_API_KEY:
            log.warning(f"Noto'g'ri API kalit: IP={request.remote_addr}")
            return jsonify({'status': 'error', 'detail': 'Ruxsat yo\'q'}), 403
        return f(*args, **kwargs)
    return decorated


# ── Health Check ──────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def health():
    """Render health check uchun — API kalitsiz ishlaydi."""
    return jsonify({
        'service': 'eMaktab Bot API',
        'status':  'running',
        'time':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.1.0',
    })


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'ok': True}), 200


# ── Login Endpoint ─────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
@require_api_key
def api_login():
    """
    InfinityFree PHP dan kelgan login so'rovini qayta ishlaydi.

    Body (JSON):
        emaktab_login    : str
        emaktab_password : str
        student_id       : int

    Response (JSON):
        status  : "success" | "error" | "captcha"
        detail  : str (xato tavsifi)
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'detail': "So'rov tanasi bo'sh yoki JSON emas"}), 400

    login    = (data.get('emaktab_login') or '').strip()
    password = (data.get('emaktab_password') or '').strip()
    sid      = data.get('student_id', '?')

    if not login or not password:
        return jsonify({'status': 'error', 'detail': 'Login yoki parol bo\'sh'}), 400

    log.info(f"Login so'rovi: student_id={sid}, login={login[:3]}***")
    start = time.time()

    # ── Selenium bot ishga tushirish ──────────────────
    result = run_login(login, password)

    elapsed = round(time.time() - start, 2)
    log.info(f"Natija: student_id={sid}, status={result['status']}, vaqt={elapsed}s")

    return jsonify(result), 200


# ── 404 / 405 handler ─────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint topilmadi'}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': "Noto'g'ri HTTP metod"}), 405

@app.errorhandler(Exception)
def handle_exception(e):
    log.exception(f"Kutilmagan xato: {e}")
    return jsonify({'status': 'error', 'detail': 'Server ichki xatosi'}), 500


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)
