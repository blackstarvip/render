"""
eMaktab Automation Bot — Render.com Flask API
"""

import os
import logging
import time
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify
from selenium_runner import run_login

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s — %(message)s'
)
log = logging.getLogger('emaktab_flask')

app = Flask(__name__)
app.config['JSON_ENSURE_ASCII'] = False


# ── Auth decorator — kalit har so'rovda o'qiladi (cache yo'q) ─────────────────
def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = os.environ.get('BOT_API_KEY', '')
        if not api_key:
            log.error("BOT_API_KEY o'rnatilmagan — Render Dashboard > Environment ni tekshiring")
            return jsonify({'status': 'error', 'detail': "Server sozlanmagan: BOT_API_KEY yo'q"}), 503
        incoming = request.headers.get('X-API-Key', '')
        if incoming != api_key:
            log.warning(f"Noto'g'ri API kalit: IP={request.remote_addr}")
            return jsonify({'status': 'error', 'detail': "Ruxsat yo'q"}), 403
        return f(*args, **kwargs)
    return decorated


# ── Health Check ──────────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'service': 'eMaktab Bot API',
        'status':  'running',
        'time':    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.1.0',
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'ok': True}), 200


# ── Login Endpoint ────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
@require_api_key
def api_login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'status': 'error', 'detail': "So'rov tanasi bo'sh yoki JSON emas"}), 400

    login    = (data.get('emaktab_login') or '').strip()
    password = (data.get('emaktab_password') or '').strip()
    sid      = data.get('student_id', '?')

    if not login or not password:
        return jsonify({'status': 'error', 'detail': "Login yoki parol bo'sh"}), 400

    log.info(f"Login so'rovi: student_id={sid}, login={login[:3]}***")
    start = time.time()

    result  = run_login(login, password)
    elapsed = round(time.time() - start, 2)
    log.info(f"Natija: student_id={sid}, status={result['status']}, vaqt={elapsed}s")

    return jsonify(result), 200


# ── Error handlers ────────────────────────────────────────────────────────────
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
  
