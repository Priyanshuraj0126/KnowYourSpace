from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import requests
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)
import google.generativeai as genai
from datetime import datetime, timedelta
import json
import time
import re
import html as html_module
import threading

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_AVAILABLE = False
GEMINI_ACTIVE_MODEL = None
GEMINI_MODEL_CHAIN = []
model = None

def is_gemini_quota_error(error_message):
    """True when Gemini rejected the request due to rate limits."""
    msg = str(error_message).lower()
    return '429' in str(error_message) or (
        'quota' in msg and ('exceeded' in msg or 'limit' in msg)
    )

def generate_gemini_content(prompt):
    """Generate text with automatic model fallback when quota is hit."""
    if not GEMINI_AVAILABLE or not GEMINI_MODEL_CHAIN:
        raise RuntimeError("Gemini AI is not available")

    last_error = None
    for model_name in GEMINI_MODEL_CHAIN:
        try:
            gemini_model = genai.GenerativeModel(model_name)
            response = gemini_model.generate_content(prompt)
            return response.text.strip(), model_name
        except Exception as e:
            last_error = e
            if is_gemini_quota_error(e):
                print(f"Gemini quota hit on {model_name}, trying next model...")
                continue
            raise
    raise last_error or RuntimeError("All Gemini models failed")

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        available_models = [
            m.name for m in genai.list_models()
            if 'generateContent' in m.supported_generation_methods
        ]

        # Prefer models with separate quotas; 2.0-flash often hits free-tier limits first
        preferred_models = [
            'models/gemini-2.5-flash',
            'models/gemini-2.5-pro',
            'models/gemini-2.0-flash-001',
            'models/gemini-2.0-flash-lite',
            'models/gemini-2.0-flash',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
        ]
        GEMINI_MODEL_CHAIN = [m for m in preferred_models if m in available_models]
        if not GEMINI_MODEL_CHAIN and available_models:
            GEMINI_MODEL_CHAIN = [available_models[0]]

        if GEMINI_MODEL_CHAIN:
            GEMINI_ACTIVE_MODEL = GEMINI_MODEL_CHAIN[0]
            model = genai.GenerativeModel(GEMINI_ACTIVE_MODEL)
            GEMINI_AVAILABLE = True
            print(f"Gemini AI initialized with model: {GEMINI_ACTIVE_MODEL}", flush=True)
            if len(GEMINI_MODEL_CHAIN) > 1:
                print(f"Gemini fallback models: {', '.join(GEMINI_MODEL_CHAIN[1:3])}", flush=True)
        else:
            raise Exception("No suitable models found")
    except Exception as e:
        print(f"Failed to initialize Gemini AI: {e}")
        GEMINI_AVAILABLE = False
else:
    print("GEMINI_API_KEY not found in environment variables")

# Import configuration
from config import config

# NASA API Configuration
NASA_API_KEY = config.NASA_API_KEY
NASA_BASE_URL = config.NASA_BASE_URL
NASA_APOD_TIMEOUT = config.NASA_APOD_TIMEOUT
MARS_VISTA_API_KEY = config.MARS_VISTA_API_KEY
MARS_VISTA_BASE_URL = config.MARS_VISTA_BASE_URL

# Static rover metadata (used when Mars Vista key is not configured)
STATIC_MARS_ROVERS = {
    'rovers': [
        {
            'id': 5,
            'name': 'Curiosity',
            'landing_date': '2012-08-06',
            'launch_date': '2011-11-26',
            'status': 'active',
            'max_sol': 4500,
            'max_date': '2026-06-01',
            'total_photos': 600000,
            'cameras': [
                {'name': 'FHAZ', 'full_name': 'Front Hazard Avoidance Camera'},
                {'name': 'RHAZ', 'full_name': 'Rear Hazard Avoidance Camera'},
                {'name': 'MAST', 'full_name': 'Mast Camera'},
                {'name': 'CHEMCAM', 'full_name': 'Chemistry and Camera Complex'},
                {'name': 'MAHLI', 'full_name': 'Mars Hand Lens Imager'},
                {'name': 'MARDI', 'full_name': 'Mars Descent Imager'},
            ],
        },
        {
            'id': 6,
            'name': 'Perseverance',
            'landing_date': '2021-02-18',
            'launch_date': '2020-07-30',
            'status': 'active',
            'max_sol': 1500,
            'max_date': '2026-06-01',
            'total_photos': 400000,
            'cameras': [
                {'name': 'EDL_RUCAM', 'full_name': 'Rover Up-Look Camera'},
                {'name': 'EDL_DDCAM', 'full_name': 'Descent Stage Down-Look Camera'},
                {'name': 'EDL_PUCAM1', 'full_name': 'Parachute Up-Look Camera A'},
                {'name': 'EDL_PUCAM2', 'full_name': 'Parachute Up-Look Camera B'},
                {'name': 'NAVCAM_LEFT', 'full_name': 'Navigation Camera - Left'},
                {'name': 'NAVCAM_RIGHT', 'full_name': 'Navigation Camera - Right'},
                {'name': 'MCZ_RIGHT', 'full_name': 'Mast Camera Zoom - Right'},
                {'name': 'MCZ_LEFT', 'full_name': 'Mast Camera Zoom - Left'},
                {'name': 'FRONT_HAZCAM_LEFT_A', 'full_name': 'Front Hazard Avoidance Camera - Left A'},
                {'name': 'FRONT_HAZCAM_RIGHT_A', 'full_name': 'Front Hazard Avoidance Camera - Right A'},
                {'name': 'REAR_HAZCAM_LEFT', 'full_name': 'Rear Hazard Avoidance Camera - Left'},
                {'name': 'REAR_HAZCAM_RIGHT', 'full_name': 'Rear Hazard Avoidance Camera - Right'},
                {'name': 'SKYCAM', 'full_name': 'MEDA Skycam'},
                {'name': 'SUPERCAM_RMI', 'full_name': 'SuperCam Remote Micro Imager'},
                {'name': 'LCAM', 'full_name': 'Lander Vision System Camera'},
            ],
        },
        {
            'id': 7,
            'name': 'Opportunity',
            'landing_date': '2004-01-25',
            'launch_date': '2003-07-07',
            'status': 'complete',
            'max_sol': 5111,
            'max_date': '2018-06-10',
            'total_photos': 228771,
            'cameras': [
                {'name': 'FHAZ', 'full_name': 'Front Hazard Avoidance Camera'},
                {'name': 'RHAZ', 'full_name': 'Rear Hazard Avoidance Camera'},
                {'name': 'NAVCAM', 'full_name': 'Navigation Camera'},
                {'name': 'PANCAM', 'full_name': 'Panoramic Camera'},
                {'name': 'MINITES', 'full_name': 'Miniature Thermal Emission Spectrometer'},
            ],
        },
        {
            'id': 4,
            'name': 'Spirit',
            'landing_date': '2004-01-04',
            'launch_date': '2003-06-10',
            'status': 'complete',
            'max_sol': 2210,
            'max_date': '2010-03-22',
            'total_photos': 124754,
            'cameras': [
                {'name': 'FHAZ', 'full_name': 'Front Hazard Avoidance Camera'},
                {'name': 'RHAZ', 'full_name': 'Rear Hazard Avoidance Camera'},
                {'name': 'NAVCAM', 'full_name': 'Navigation Camera'},
                {'name': 'PANCAM', 'full_name': 'Panoramic Camera'},
                {'name': 'MINITES', 'full_name': 'Miniature Thermal Emission Spectrometer'},
            ],
        },
    ]
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explore')
def explore():
    return render_template('explore.html')

@app.route('/events')
def events():
    return render_template('events.html')

@app.route('/weather')
def weather():
    return render_template('weather.html')

@app.route('/ai-search')
def ai_search():
    return render_template('ai-search.html')

@app.route('/ai-chat')
def ai_chat():
    return render_template('ai-chat.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/apod')
def apod():
    return render_template('apod.html')

@app.route('/mars')
def mars():
    return render_template('mars.html')

@app.route('/neo')
def neo():
    return render_template('neo.html')

# ===== APOD (Astronomy Picture of the Day) API Endpoints =====

_apod_cache = {}
APOD_TODAY_CACHE_TTL = 6 * 3600
APOD_HISTORICAL_CACHE_TTL = 7 * 24 * 3600
APOD_WEB_BASE = "https://apod.nasa.gov/apod"

def apod_page_path(date_str):
    """Convert YYYY-MM-DD to APOD HTML page filename (ap260605.html)."""
    dt = datetime.strptime(date_str, '%Y-%m-%d')
    return f"ap{dt.strftime('%y%m%d')}.html"

def clean_apod_html(text):
    """Strip HTML tags from APOD page snippets."""
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'<p>', '\n', text, flags=re.I)
    text = re.sub(r'</p>', '\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html_module.unescape(text)
    return re.sub(r'\s+', ' ', text).strip()

def fetch_apod_from_webpage(date=None):
    """Fast APOD fetch from NASA's public website (~1-2s, no API key)."""
    date_str = date or datetime.now().strftime('%Y-%m-%d')
    page_url = f"{APOD_WEB_BASE}/{apod_page_path(date_str)}"
    response = requests.get(page_url, timeout=12)
    if response.status_code == 404:
        raise requests.RequestException(f"No APOD page for {date_str}")
    response.raise_for_status()
    page = response.text

    title_match = re.search(r'<title>\s*APOD:\s*[^–\-]+[–\-]\s*(.+?)\s*</title>', page, re.I | re.S)
    title = clean_apod_html(title_match.group(1)) if title_match else 'Astronomy Picture of the Day'

    image_match = re.search(r'<a\s+href="(image/[^"]+)"', page, re.I)
    preview_match = re.search(r'<img[^>]+src="(image/[^"]+)"', page, re.I)

    if image_match:
        image_path = image_match.group(1)
        full_image_url = f"{APOD_WEB_BASE}/{image_path}"
        preview_path = preview_match.group(1) if preview_match else image_path
        preview_url = f"{APOD_WEB_BASE}/{preview_path}"
        explanation_match = re.search(
            r'<b>\s*Explanation:\s*</b>\s*(.*?)(?:<p>\s*<center>|<p>\s*Tomorrow|<p>\s*<b>\s*Authors|\Z)',
            page,
            re.I | re.S,
        )
        copyright_match = re.search(
            r'Image Credit[^<]*</b>\s*(.*?)</center>',
            page,
            re.S | re.I,
        )
        return {
            'title': title,
            'date': date_str,
            'explanation': clean_apod_html(explanation_match.group(1)) if explanation_match else '',
            'url': full_image_url,
            'hdurl': full_image_url,
            'preview_url': preview_url,
            'media_type': 'image',
            'copyright': clean_apod_html(copyright_match.group(1)) if copyright_match else 'Public Domain',
            'thumbnail_url': preview_url,
        }

    youtube_match = re.search(
        r'(?:youtube\.com/embed/|www\.youtube\.com/embed/)([A-Za-z0-9_-]{11})',
        page,
        re.I,
    )
    if youtube_match:
        video_url = f"https://www.youtube.com/embed/{youtube_match.group(1)}"
        return {
            'title': title,
            'date': date_str,
            'explanation': clean_apod_html(
                re.search(
                    r'<b>\s*Explanation:\s*</b>\s*(.*?)(?:<p>\s*<center>|<p>\s*Tomorrow|\Z)',
                    page,
                    re.I | re.S,
                ).group(1)
            ) if re.search(r'<b>\s*Explanation:\s*</b>', page, re.I) else '',
            'url': video_url,
            'hdurl': '',
            'preview_url': '',
            'media_type': 'video',
            'copyright': clean_apod_html(
                re.search(r'Image Credit[^<]*</b>\s*(.*?)</center>', page, re.S | re.I).group(1)
            ) if re.search(r'Image Credit', page, re.I) else 'Public Domain',
            'thumbnail_url': '',
        }

    raise requests.RequestException("Could not parse APOD content from NASA page")

def fetch_nasa_apod(date=None, count=1):
    """Fetch APOD from NASA with retries (their API often returns 503/timeouts)."""
    url = f"{NASA_BASE_URL}/planetary/apod?api_key={NASA_API_KEY}"
    if date:
        url += f"&date={date}"
    if count > 1:
        url += f"&count={count}"

    last_error = None
    for attempt in range(2):
        try:
            response = requests.get(url, timeout=NASA_APOD_TIMEOUT)
            if response.status_code in (502, 503, 504) and attempt == 0:
                time.sleep(1)
                continue
            response.raise_for_status()
            if not response.text.strip():
                raise requests.RequestException("Empty response from NASA APOD API")
            data = response.json()
            if isinstance(data, dict) and data.get('error'):
                err = data['error']
                msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
                raise requests.RequestException(msg)
            if isinstance(data, dict) and 'title' not in data:
                raise requests.RequestException(data.get('msg', 'Invalid NASA APOD response'))
            return data
        except (requests.Timeout, requests.RequestException) as e:
            last_error = e
            if attempt == 0:
                time.sleep(1)
                continue
            raise last_error

def get_apod_cache_ttl(date=None):
    """Historical APOD never changes — cache longer."""
    today = datetime.now().strftime('%Y-%m-%d')
    if not date or date == today:
        return APOD_TODAY_CACHE_TTL
    return APOD_HISTORICAL_CACHE_TTL

def get_cached_apod(cache_key, date=None):
    """Return cached APOD payload if still fresh."""
    entry = _apod_cache.get(cache_key)
    if not entry:
        return None
    ttl = entry.get('ttl', APOD_TODAY_CACHE_TTL)
    if time.time() - entry['cached_at'] > ttl:
        del _apod_cache[cache_key]
        return None
    return entry['data']

def set_cached_apod(cache_key, data, date=None):
    """Cache processed APOD payload."""
    _apod_cache[cache_key] = {
        'data': data,
        'cached_at': time.time(),
        'ttl': get_apod_cache_ttl(date),
    }

def load_apod_entry(date=None, count=1):
    """Load a single APOD — fast website first, NASA API as backup."""
    if count == 1:
        try:
            return process_apod_data(fetch_apod_from_webpage(date)), 'nasa_web'
        except (requests.Timeout, requests.RequestException) as web_error:
            print(f"APOD web fetch failed, trying NASA API: {web_error}")

    data = fetch_nasa_apod(date=date, count=count)
    if isinstance(data, list):
        return [process_apod_data(apod) for apod in data], 'nasa_api'
    return process_apod_data(data), 'nasa_api'

def prefetch_todays_apod():
    """Warm cache on startup so the APOD page loads instantly."""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        cache_key = f"apod:{today}:count=1"
        if get_cached_apod(cache_key, today):
            return
        processed, _source = load_apod_entry(date=today, count=1)
        set_cached_apod(cache_key, processed, today)
        set_cached_apod(f"apod:today:count=1", processed, today)
        print(f"APOD cache warmed for {today}")
    except Exception as e:
        print(f"APOD prefetch skipped: {e}")

@app.route('/api/apod')
def get_apod():
    """Get NASA Astronomy Picture of the Day"""
    try:
        date = request.args.get('date')
        count = request.args.get('count', 1, type=int)
        
        if count > 10:  # Limit to prevent abuse
            count = 10

        cache_key = f"apod:{date or 'today'}:count={count}"
        cached = get_cached_apod(cache_key, date)
        if cached:
            return jsonify(cached)

        processed_data, source = load_apod_entry(date=date, count=count)
        if isinstance(processed_data, dict):
            processed_data['source'] = source
        set_cached_apod(cache_key, processed_data, date)
        return jsonify(processed_data)
            
    except requests.Timeout:
        fallback = get_fallback_apod_data(date)
        return jsonify(fallback), 200
    except requests.RequestException as e:
        print(f"NASA APOD request failed: {e}")
        fallback = get_fallback_apod_data(date)
        return jsonify(fallback), 200
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

_random_apod_pool = []
_random_pool_lock = threading.Lock()
RANDOM_POOL_TARGET = 6

def _fetch_one_random_apod():
    """Fetch a single random image APOD; returns processed dict or None."""
    import random
    start_date = datetime(1995, 6, 16)
    end_date = datetime.now()
    total_days = (end_date - start_date).days

    for _ in range(8):
        random_days = random.randint(0, total_days)
        random_date = start_date + timedelta(days=random_days)
        date_str = random_date.strftime('%Y-%m-%d')
        cache_key = f"apod:{date_str}:count=1"

        cached = get_cached_apod(cache_key, date_str)
        if cached and cached.get('media_type') == 'image':
            return cached

        try:
            processed_data, source = load_apod_entry(date=date_str, count=1)
            if processed_data.get('media_type') == 'video':
                continue
            processed_data['source'] = source
            set_cached_apod(cache_key, processed_data, date_str)
            return processed_data
        except (requests.Timeout, requests.RequestException):
            continue
    return None

def refill_random_apod_pool(count=3):
    """Background-fill pool so /api/apod/random can respond instantly."""
    def worker():
        added = 0
        attempts = 0
        while added < count and attempts < count * 4:
            attempts += 1
            item = _fetch_one_random_apod()
            if not item:
                continue
            with _random_pool_lock:
                if len(_random_apod_pool) >= RANDOM_POOL_TARGET:
                    return
                if any(p.get('date') == item.get('date') for p in _random_apod_pool):
                    continue
                _random_apod_pool.append(item)
                added += 1
        if added:
            print(f"APOD random pool: {len(_random_apod_pool)} ready")

    threading.Thread(target=worker, daemon=True).start()

@app.route('/api/apod/random')
def get_random_apod():
    """Get a random image APOD (instant when pool is warm)."""
    try:
        with _random_pool_lock:
            if _random_apod_pool:
                processed_data = _random_apod_pool.pop(0)
                refill_random_apod_pool(2)
                return jsonify(processed_data)

        processed_data = _fetch_one_random_apod()
        if processed_data:
            refill_random_apod_pool(2)
            return jsonify(processed_data)

        refill_random_apod_pool(3)
        return jsonify(get_fallback_apod_data()), 200
        
    except Exception as e:
        print(f"Random APOD failed: {e}")
        return jsonify(get_fallback_apod_data()), 200

@app.route('/api/apod/search')
def search_apod():
    """Search APOD by keyword in title or explanation"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        apods = fetch_nasa_apod(count=100)
        if not isinstance(apods, list):
            apods = [apods]
        results = []
        
        for apod in apods:
            if (query.lower() in apod.get('title', '').lower() or 
                query.lower() in apod.get('explanation', '').lower()):
                processed_apod = process_apod_data(apod)
                results.append(processed_apod)
                
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
        
    except requests.Timeout:
        # Return fallback search results when NASA API times out
        fallback_data = get_fallback_apod_data()
        return jsonify({
            'query': query,
            'results': [fallback_data],
            'total_found': 1,
            'is_fallback': True
        }), 200
    except Exception as e:
        # Return fallback search results when NASA API fails
        fallback_data = get_fallback_apod_data()
        return jsonify({
            'query': query,
            'results': [fallback_data],
            'total_found': 1,
            'is_fallback': True
        }), 200

# ===== Near-Earth Objects (NEO) API Endpoints =====

@app.route('/api/neo')
def get_neo():
    """Get Near-Earth Objects data"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = datetime.now().strftime('%Y-%m-%d')
        if not end_date:
            end_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
            
        url = f"{NASA_BASE_URL}/neo/rest/v1/feed?api_key={NASA_API_KEY}&start_date={start_date}&end_date={end_date}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        processed_data = process_neo_data(data)
        return jsonify(processed_data)
        
    except requests.Timeout:
        return jsonify({'error': 'NASA NEO API request timed out. Please try again.'}), 408
    except requests.RequestException as e:
        return jsonify({'error': f'NASA NEO API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/neo/lookup/<asteroid_id>')
def get_neo_lookup(asteroid_id):
    """Get detailed information about a specific asteroid"""
    try:
        url = f"{NASA_BASE_URL}/neo/rest/v1/lookup/{asteroid_id}?api_key={NASA_API_KEY}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        processed_data = process_neo_detail_data(data)
        return jsonify(processed_data)
        
    except requests.Timeout:
        return jsonify({'error': 'NASA NEO Lookup API request timed out. Please try again.'}), 408
    except requests.RequestException as e:
        return jsonify({'error': f'NASA NEO Lookup API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ===== Mars Rover Photos API Endpoints =====
# NASA Mars Photos API was retired Oct 2025; we use Mars Vista (drop-in replacement).

def get_mars_vista_headers():
    """Build auth headers for Mars Vista API."""
    if not MARS_VISTA_API_KEY:
        return None
    return {'X-API-Key': MARS_VISTA_API_KEY}

def mars_vista_get(url, **kwargs):
    """Call Mars Vista without inheriting broken system proxy settings."""
    with requests.Session() as session:
        session.trust_env = False
        return session.get(url, **kwargs)

def fetch_mars_photos(rover, sol, camera='', page=1):
    """Fetch Mars rover photos from Mars Vista API."""
    headers = get_mars_vista_headers()
    if not headers:
        return None, (
            'Mars Vista API key required. NASA retired their Mars Photos API in Oct 2025. '
            'Get a free key at https://marsvista.dev/signin and add MARS_VISTA_API_KEY to your .env file.'
        )

    url = f"{MARS_VISTA_BASE_URL}/api/v1/rovers/{rover.lower()}/photos"
    params = {'sol': sol, 'page': page, 'per_page': 25}
    if camera:
        params['camera'] = camera

    response = mars_vista_get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    return response.json(), None

def fetch_mars_rovers():
    """Fetch Mars rover metadata from Mars Vista API."""
    headers = get_mars_vista_headers()
    if not headers:
        return STATIC_MARS_ROVERS, 'static_fallback'

    url = f"{MARS_VISTA_BASE_URL}/api/v1/rovers"
    response = mars_vista_get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json(), 'mars_vista'

@app.route('/api/mars')
def get_mars():
    """Get Mars Rover photos"""
    try:
        rover = request.args.get('rover', 'curiosity')
        sol = request.args.get('sol', 1000, type=int)
        camera = request.args.get('camera', '')
        page = request.args.get('page', 1, type=int)

        data, error = fetch_mars_photos(rover, sol, camera, page)
        if error:
            return jsonify({'error': error, 'setup_url': 'https://marsvista.dev/signin'}), 503

        processed_data = process_mars_data(data)
        processed_data['source'] = 'mars_vista'
        return jsonify(processed_data)
        
    except requests.Timeout:
        return jsonify({'error': 'Mars Vista API request timed out. Please try again.'}), 408
    except requests.RequestException as e:
        return jsonify({'error': f'Mars Vista API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/mars/rovers')
def get_mars_rovers():
    """Get information about available Mars rovers"""
    try:
        data, source = fetch_mars_rovers()
        processed_data = process_rovers_data(data)
        processed_data['source'] = source
        if source == 'static_fallback':
            processed_data['note'] = (
                'Showing cached rover list. Add MARS_VISTA_API_KEY to .env for live Mars photos '
                '(free key at https://marsvista.dev/signin).'
            )
        return jsonify(processed_data)
        
    except requests.Timeout:
        return jsonify({'error': 'Mars Vista API request timed out. Please try again.'}), 408
    except requests.RequestException as e:
        return jsonify({'error': f'Mars Vista API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ===== Weather and Visibility API Endpoints =====

@app.route('/api/weather')
def get_weather():
    """Get weather data from Open Meteo API"""
    try:
        lat = request.args.get('lat', 40.7128, type=float)
        lon = request.args.get('lon', -74.0060, type=float)
        
        # Enhanced weather API call with more parameters
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,wind_speed_10m,precipitation_probability,pressure_msl&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,uv_index_max&timezone=auto"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        processed_data = process_weather_data(data)
        return jsonify(processed_data)
        
    except requests.RequestException as e:
        return jsonify({'error': f'Weather API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/weather/hourly')
def get_hourly_weather():
    """Get hourly weather forecast for the next 48 hours"""
    try:
        lat = request.args.get('lat', 40.7128, type=float)
        lon = request.args.get('lon', -74.0060, type=float)
        
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,wind_speed_10m,precipitation_probability,pressure_msl,weather_code&timezone=auto"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        hourly_data = process_hourly_weather_data(data)
        return jsonify(hourly_data)
        
    except requests.RequestException as e:
        return jsonify({'error': f'Hourly weather API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/weather/alerts')
def get_weather_alerts():
    """Get weather alerts and warnings for the location"""
    try:
        lat = request.args.get('lat', 40.7128, type=float)
        lon = request.args.get('lon', -74.0060, type=float)
        
        # Get current weather conditions to determine if alerts should be shown
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,cloud_cover,wind_speed_10m,precipitation_probability&timezone=auto"
        response = requests.get(weather_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        alerts = generate_weather_alerts(data)
        return jsonify(alerts)
        
    except requests.RequestException as e:
        return jsonify({'error': f'Weather alerts API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/weather/astronomical')
def get_astronomical_conditions():
    """Get astronomical viewing conditions including moon phase and light pollution"""
    try:
        lat = request.args.get('lat', 40.7128, type=float)
        lon = request.args.get('lon', -74.0060, type=float)
        
        # Get current date for astronomical calculations
        current_date = datetime.now()
        
        # Calculate moon phase and other astronomical data
        astronomical_data = calculate_astronomical_conditions(lat, lon, current_date)
        
        return jsonify(astronomical_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get astronomical conditions: {str(e)}'}), 500

@app.route('/api/weather/history')
def get_weather_history():
    """Get historical weather data for the past 7 days"""
    try:
        lat = request.args.get('lat', 40.7128, type=float)
        lon = request.args.get('lon', -74.0060, type=float)
        days = request.args.get('days', 7, type=int)
        
        # Calculate start date (days ago)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date.strftime('%Y-%m-%d')}&end_date={end_date.strftime('%Y-%m-%d')}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,wind_speed_10m,precipitation_probability&timezone=auto"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        historical_data = process_historical_weather_data(data, start_date, end_date)
        return jsonify(historical_data)
        
    except requests.RequestException as e:
        return jsonify({'error': f'Weather history API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/weather/summary')
def get_weather_summary():
    """Get comprehensive weather summary including current, forecast, and analysis"""
    try:
        lat = request.args.get('lat', 40.7128, type=float)
        lon = request.args.get('lon', -74.0060, type=float)
        
        # Get current weather
        current_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,wind_speed_10m,precipitation_probability,pressure_msl&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max,uv_index_max&timezone=auto"
        current_response = requests.get(current_url, timeout=10)
        current_response.raise_for_status()
        current_data = current_response.json()
        
        # Get hourly forecast
        hourly_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,cloud_cover,visibility,wind_speed_10m,precipitation_probability,pressure_msl,weather_code&timezone=auto"
        hourly_response = requests.get(hourly_url, timeout=10)
        hourly_response.raise_for_status()
        hourly_data = hourly_response.json()
        
        # Process all data
        current_weather = process_weather_data(current_data)
        hourly_forecast = process_hourly_weather_data(hourly_data)
        weather_alerts = generate_weather_alerts(current_data)
        
        # Create comprehensive summary
        summary = {
            'location': {
                'latitude': lat,
                'longitude': lon
            },
            'current_weather': current_weather.get('current', {}),
            'daily_forecast': current_weather.get('daily_forecast', []),
            'hourly_forecast': hourly_forecast.get('hourly_data', []),
            'stargazing_conditions': current_weather.get('stargazing_conditions', {}),
            'weather_alerts': weather_alerts.get('alerts', []),
            'summary_stats': generate_weather_summary_stats(current_data, hourly_data),
            'processed_at': datetime.now().isoformat()
        }
        
        return jsonify(summary)
        
    except requests.RequestException as e:
        return jsonify({'error': f'Weather summary API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/weather/geocode')
def geocode_place():
    """Convert place name to coordinates using Open Meteo Geocoding API"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({'error': 'Place name query is required'}), 400
        
        # Use Open Meteo Geocoding API (free, no API key required)
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={query}&count=10&language=en&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'results' in data and data['results']:
            # Process and format the results
            processed_results = []
            for result in data['results']:
                processed_result = {
                    'name': result.get('name', ''),
                    'country': result.get('country', ''),
                    'state': result.get('admin1', ''),
                    'lat': result.get('latitude', 0),
                    'lon': result.get('longitude', 0),
                    'display_name': f"{result.get('name', '')}, {result.get('country', '')}"
                }
                processed_results.append(processed_result)
            
            return jsonify({
                'query': query,
                'results': processed_results,
                'total_found': len(processed_results)
            })
        else:
            return jsonify({
                'query': query,
                'results': [],
                'total_found': 0,
                'message': 'No places found with that name'
            })
            
    except requests.RequestException as e:
        return jsonify({'error': f'Geocoding API request failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

# ===== AI Search API Endpoints =====

@app.route('/api/ai-search', methods=['POST'])
def ai_search_api():
    """AI-powered search using Gemini Pro"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        search_type = data.get('search_type', 'general')
        response_length = data.get('response_length', 'detailed')
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Check if Gemini AI is available
        if not GEMINI_AVAILABLE:
            # Use fallback system instead of returning error
            fallback_response = get_fallback_response(query, search_type)
            return jsonify({
                'query': query,
                'response': fallback_response,
                'search_type': search_type,
                'response_length': response_length,
                'ai_model': 'Fallback System',
                'timestamp': datetime.now().isoformat(),
                'status': 'fallback',
                'note': 'AI service is currently unavailable. Showing fallback response. To enable AI features, please set your GEMINI_API_KEY in the .env file.'
            })
        
        # Create a context-aware prompt based on search type and response length
        prompt = create_search_prompt(query, search_type, response_length)
        
        try:
            ai_response, model_used = generate_gemini_content(prompt)
            
            return jsonify({
                'query': query,
                'response': ai_response,
                'search_type': search_type,
                'response_length': response_length,
                'ai_model': model_used.replace('models/', ''),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
            
        except Exception as ai_error:
            error_message = str(ai_error)
            print(f"AI Error: {error_message}")  # Debug logging
            
            if is_gemini_quota_error(error_message):
                fallback_response = get_fallback_response(query, search_type)
                return jsonify({
                    'query': query,
                    'response': fallback_response,
                    'search_type': search_type,
                    'response_length': response_length,
                    'ai_model': 'Fallback System',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'quota_exceeded',
                    'note': 'AI quota exceeded for today, showing fallback response. Try again tomorrow or upgrade your plan.'
                })
            else:
                # For other errors, try to return the actual error instead of fallback
                return jsonify({
                    'query': query,
                    'response': f"AI service encountered an error: {error_message[:200]}... Please try again or contact support if the issue persists.",
                    'search_type': search_type,
                    'response_length': response_length,
                    'ai_model': 'Gemini Pro',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'error',
                    'note': f'Error details: {error_message[:100]}...'
                })
            
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}', 'status': 'error'}), 500

@app.route('/api/ai-chat', methods=['POST'])
def ai_chat_api():
    """AI chat endpoint used by ai-chat.html"""
    try:
        data = request.get_json() or {}
        question = data.get('question', '').strip()

        if not question:
            return jsonify({'error': 'Question is required'}), 400

        if not GEMINI_AVAILABLE:
            answer = get_fallback_response(question, 'general')
            return jsonify({
                'answer': answer,
                'status': 'fallback',
                'ai_model': 'Fallback System'
            })

        prompt = create_search_prompt(question, 'general', 'detailed')

        try:
            answer, model_used = generate_gemini_content(prompt)
            return jsonify({
                'answer': answer,
                'status': 'success',
                'ai_model': model_used.replace('models/', '')
            })
        except Exception as ai_error:
            error_message = str(ai_error)
            if is_gemini_quota_error(error_message):
                return jsonify({
                    'answer': get_fallback_response(question, 'general'),
                    'status': 'quota_exceeded',
                    'ai_model': 'Fallback System'
                })
            return jsonify({
                'answer': f"AI service encountered an error. Please try again.",
                'status': 'error',
                'ai_model': 'Gemini'
            }), 500

    except Exception as e:
        return jsonify({'error': f'Chat failed: {str(e)}'}), 500

def create_search_prompt(query, search_type, response_length):
    """Create a context-aware prompt for the AI search"""
    
    # Base prompt with space science context
    base_prompt = """You are an expert astrophysicist and space scientist. Provide accurate, engaging, and educational information about space, astronomy, and cosmic phenomena. 
    
    Always base your answers on current scientific understanding and research. Use clear language that both beginners and enthusiasts can understand.
    
    Question: {query}
    
    Search Type: {search_type}
    Response Length: {response_length}
    
    Please provide a comprehensive answer that is:"""
    
    # Add length-specific instructions
    if response_length == 'concise':
        base_prompt += "\n- Concise and to the point (2-3 paragraphs)"
        base_prompt += "\n- Focus on key facts and essential information"
    elif response_length == 'detailed':
        base_prompt += "\n- Detailed and informative (4-6 paragraphs)"
        base_prompt += "\n- Include relevant examples and explanations"
    else:  # comprehensive
        base_prompt += "\n- Comprehensive and thorough (6+ paragraphs)"
        base_prompt += "\n- Include detailed explanations, examples, and related concepts"
    
    # Add type-specific context
    type_contexts = {
        'planets': "Focus on planetary science, solar system dynamics, and planetary characteristics.",
        'stars': "Emphasize stellar evolution, star types, and galactic phenomena.",
        'cosmology': "Cover universe origins, expansion, dark matter, and fundamental physics.",
        'space-exploration': "Include current missions, technology, and future exploration plans.",
        'astronomy': "Focus on observational astronomy, instruments, and celestial mechanics.",
        'general': "Provide a well-rounded overview covering multiple aspects of the topic."
    }
    
    type_context = type_contexts.get(search_type, type_contexts['general'])
    base_prompt += f"\n\nContext: {type_context}"
    
    # Add formatting instructions
    base_prompt += """
    
    Format your response with:
    - Clear paragraphs
        - Scientific accuracy
    - Engaging explanations
    - Relevant examples when helpful
    - Current information (as of 2024)
    
    Answer:"""
    
    return base_prompt.format(query=query, search_type=search_type, response_length=response_length)

def get_fallback_response(query, search_type):
    """Provide fallback responses when AI is unavailable"""
    
    # Simple keyword-based fallback responses
    fallback_responses = {
        'big bang': "The Big Bang theory is the prevailing cosmological model explaining the origin of the universe. According to this theory, the universe began approximately 13.8 billion years ago from an extremely hot and dense state. The universe has been expanding ever since, cooling down and allowing matter to form. This theory is supported by multiple lines of evidence including cosmic microwave background radiation, the abundance of light elements, and the observed expansion of the universe.",
        
        'black hole': "Black holes are regions of spacetime where gravity is so strong that nothing, not even light, can escape. They form when massive stars collapse at the end of their life cycle, or when matter accumulates to a critical density. Black holes have an event horizon - a boundary beyond which escape is impossible. They play crucial roles in galaxy formation and evolution, and recent observations have provided direct evidence of their existence.",
        
        'solar system': "Our solar system consists of the Sun and everything that orbits around it, including eight planets, dwarf planets, moons, asteroids, comets, and other celestial bodies. The four inner planets (Mercury, Venus, Earth, Mars) are rocky, while the four outer planets (Jupiter, Saturn, Uranus, Neptune) are gas giants. The solar system formed about 4.6 billion years ago from a cloud of gas and dust.",
        
        'mars': "Mars is the fourth planet from the Sun and the second-smallest planet in our solar system. Often called the 'Red Planet' due to its reddish appearance, Mars has a thin atmosphere, polar ice caps, and evidence of ancient water flows. It's a primary target for human exploration, with multiple robotic missions studying its geology, climate, and potential for past or present life.",
        
        'galaxy': "Galaxies are vast systems of stars, gas, dust, and dark matter held together by gravity. Our Milky Way galaxy contains hundreds of billions of stars and is just one of trillions of galaxies in the observable universe. Galaxies come in various shapes including spiral, elliptical, and irregular, and they often contain supermassive black holes at their centers."
    }
    
    # Find the best matching fallback response
    query_lower = query.lower()
    for keyword, response in fallback_responses.items():
        if keyword in query_lower:
            return response
    
    # Generic fallback response
    return f"I apologize, but I'm unable to provide a detailed response about '{query}' at the moment. This appears to be a question about space or astronomy. For the most accurate and up-to-date information, I recommend consulting NASA's official website, the European Space Agency (ESA), or other reputable astronomical organizations. These sources provide current research findings and verified scientific information about space phenomena."

@app.route('/api/ai/search/history')
def get_ai_search_history():
    """Get recent AI search history (placeholder for future implementation)"""
    try:
        # This could be expanded to store search history in a database
        return jsonify({
            'message': 'AI search history feature coming soon',
            'recent_searches': []
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get AI search history: {str(e)}'}), 500

@app.route('/api/ai/search/popular')
def get_popular_searches():
    """Get popular search topics"""
    try:
        popular_topics = [
            {
                'topic': 'Black Holes',
                'description': 'Learn about these mysterious cosmic objects',
                'category': 'cosmology'
            },
            {
                'topic': 'Exoplanets',
                'description': 'Discover planets beyond our solar system',
                'category': 'planets'
            },
            {
                'topic': 'Dark Matter',
                'description': 'Understand the invisible matter in the universe',
                'category': 'cosmology'
            },
            {
                'topic': 'Mars Exploration',
                'description': 'Current and future missions to the Red Planet',
                'category': 'space-exploration'
            },
            {
                'topic': 'Stellar Evolution',
                'description': 'How stars are born, live, and die',
                'category': 'stars'
            }
        ]
        
        return jsonify({
            'popular_topics': popular_topics,
            'total_topics': len(popular_topics)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get popular searches: {str(e)}'}), 500

@app.route('/api/ai/search/suggestions')
def get_search_suggestions():
    """Get search suggestions based on query"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({'suggestions': [], 'total': 0})
        
        # Predefined suggestions based on common space topics
        all_suggestions = [
            'black holes', 'exoplanets', 'dark matter', 'mars exploration', 'stellar evolution',
            'solar system', 'galaxy formation', 'cosmic microwave background', 'neutron stars',
            'supernovae', 'asteroids', 'comets', 'moon phases', 'telescopes', 'space missions',
            'international space station', 'hubble telescope', 'james webb telescope', 'voyager missions',
            'apollo missions', 'saturn rings', 'jupiter moons', 'venus atmosphere', 'mercury surface',
            'pluto dwarf planet', 'kuiper belt', 'oort cloud', 'meteor showers', 'aurora borealis',
            'solar flares', 'sunspots', 'cosmic rays', 'dark energy', 'inflation theory',
            'multiverse theory', 'string theory', 'quantum mechanics', 'relativity', 'gravity waves'
        ]
        
        # Filter suggestions based on query
        filtered_suggestions = [
            suggestion for suggestion in all_suggestions 
            if query.lower() in suggestion.lower()
        ][:10]  # Limit to 10 suggestions
        
        return jsonify({
            'query': query,
            'suggestions': filtered_suggestions,
            'total': len(filtered_suggestions)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get suggestions: {str(e)}'}), 500

@app.route('/api/ai/search/advanced', methods=['POST'])
def advanced_ai_search():
    """Advanced AI search with multiple parameters"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        search_type = data.get('search_type', 'general')
        response_length = data.get('response_length', 'detailed')
        include_examples = data.get('include_examples', True)
        include_recent_discoveries = data.get('include_recent_discoveries', True)
        difficulty_level = data.get('difficulty_level', 'intermediate')
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Check if Gemini AI is available
        if not GEMINI_AVAILABLE:
            return jsonify({'error': 'AI service is currently unavailable. Please try again later.'}), 503
        
        # Create advanced prompt
        prompt = create_advanced_search_prompt(
            query, search_type, response_length, 
            include_examples, include_recent_discoveries, difficulty_level
        )
        
        try:
            ai_response, model_used = generate_gemini_content(prompt)
            
            return jsonify({
                'query': query,
                'response': ai_response,
                'search_type': search_type,
                'response_length': response_length,
                'include_examples': include_examples,
                'include_recent_discoveries': include_recent_discoveries,
                'difficulty_level': difficulty_level,
                'ai_model': model_used.replace('models/', ''),
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
            
        except Exception as ai_error:
            error_message = str(ai_error)
            print(f"Advanced AI Error: {error_message}")  # Debug logging
            
            if is_gemini_quota_error(error_message):
                fallback_response = get_fallback_response(query, search_type)
                return jsonify({
                    'query': query,
                    'response': fallback_response,
                    'search_type': search_type,
                    'response_length': response_length,
                    'ai_model': 'Fallback System',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'quota_exceeded',
                    'note': 'AI quota exceeded for today, showing fallback response. Try again tomorrow or upgrade your plan.'
                })
            else:
                # Other AI errors
                fallback_response = get_fallback_response(query, search_type)
                return jsonify({
                    'query': query,
                    'response': fallback_response,
                    'search_type': search_type,
                    'ai_model': 'Fallback System',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'fallback',
                    'note': f'AI service error: {error_message[:100]}... showing fallback response'
                })
        
    except Exception as e:
        return jsonify({'error': f'Advanced search failed: {str(e)}', 'status': 'error'}), 500

def create_advanced_search_prompt(query, search_type, response_length, include_examples, include_recent_discoveries, difficulty_level):
    """Create an advanced prompt for AI search"""
    
    base_prompt = f"""You are an expert astrophysicist and space scientist. Provide accurate, engaging, and educational information about space, astronomy, and cosmic phenomena.

Question: {query}
Search Type: {search_type}
Response Length: {response_length}
Difficulty Level: {difficulty_level}
Include Examples: {include_examples}
Include Recent Discoveries: {include_recent_discoveries}

Please provide a comprehensive answer that is:"""
    
    # Add length-specific instructions
    if response_length == 'concise':
        base_prompt += "\n- Concise and to the point (2-3 paragraphs)"
    elif response_length == 'detailed':
        base_prompt += "\n- Detailed and informative (4-6 paragraphs)"
    else:  # comprehensive
        base_prompt += "\n- Comprehensive and thorough (6+ paragraphs)"
    
    # Add difficulty level instructions
    if difficulty_level == 'beginner':
        base_prompt += "\n- Use simple language and basic concepts"
        base_prompt += "\n- Avoid complex mathematical explanations"
        base_prompt += "\n- Focus on fundamental understanding"
    elif difficulty_level == 'intermediate':
        base_prompt += "\n- Use moderate technical language"
        base_prompt += "\n- Include some scientific details"
        base_prompt += "\n- Balance accessibility with depth"
    else:  # advanced
        base_prompt += "\n- Use technical and scientific language"
        base_prompt += "\n- Include detailed explanations and theories"
        base_prompt += "\n- Assume prior knowledge of basic concepts"
    
    # Add type-specific context
    type_contexts = {
        'planets': "Focus on planetary science, solar system dynamics, and planetary characteristics.",
        'stars': "Emphasize stellar evolution, star types, and galactic phenomena.",
        'cosmology': "Cover universe origins, expansion, dark matter, and fundamental physics.",
        'space-exploration': "Include current missions, technology, and future exploration plans.",
        'astronomy': "Focus on observational astronomy, instruments, and celestial mechanics.",
        'general': "Provide a well-rounded overview covering multiple aspects of the topic."
    }
    
    type_context = type_contexts.get(search_type, type_contexts['general'])
    base_prompt += f"\n\nContext: {type_context}"
    
    # Add specific requirements
    if include_examples:
        base_prompt += "\n- Include relevant examples and analogies"
    
    if include_recent_discoveries:
        base_prompt += "\n- Mention recent discoveries and current research (2023-2024)"
    
    base_prompt += """
    
    Format your response with:
    - Clear paragraphs
    - Scientific accuracy
    - Engaging explanations
    - Current information (as of 2024)
    
    Answer:"""
    
    return base_prompt

@app.route('/api/ai/status')
def get_ai_status():
    """Get AI enhancement availability status"""
    return jsonify({
        'ai_available': GEMINI_AVAILABLE,
        'status': 'available' if GEMINI_AVAILABLE else 'unavailable',
        'active_model': GEMINI_ACTIVE_MODEL.replace('models/', '') if GEMINI_ACTIVE_MODEL else None,
        'fallback_models': [m.replace('models/', '') for m in GEMINI_MODEL_CHAIN[1:4]],
        'message': (
            f"Gemini AI ready ({GEMINI_ACTIVE_MODEL.replace('models/', '')})"
            if GEMINI_AVAILABLE else 'Gemini not initialized — restart the server after updating .env'
        )
    })

# ===== Astronomical Events API Endpoints =====

@app.route('/api/events')
def get_events():
    """Get upcoming astronomical events"""
    try:
        event_type = request.args.get('type', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        event_id = request.args.get('event_id')
        
        # If specific event ID is requested, return just that event
        if event_id:
            current_date = datetime.now()
            all_events = generate_upcoming_events(current_date, 'all', start_date, end_date)
            specific_event = next((event for event in all_events if event['id'] == event_id), None)
            
            if specific_event:
                return jsonify({
                    'events': [specific_event],
                    'total_events': 1,
                    'generated_at': current_date.isoformat()
                })
            else:
                return jsonify({'error': 'Event not found'}), 404
        
        # Get current date
        current_date = datetime.now()
        
        # Generate upcoming events data
        events = generate_upcoming_events(current_date, event_type, start_date, end_date)
        
        return jsonify({
            'events': events,
            'total_events': len(events),
            'generated_at': current_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get events: {str(e)}'}), 500

@app.route('/api/events/categories')
def get_event_categories():
    """Get event categories and descriptions"""
    try:
        categories = [
            {
                'id': 'meteor_showers',
                'name': 'Meteor Showers',
                'description': 'Track annual meteor showers with peak dates, viewing tips, and expected meteor rates for optimal stargazing experiences.',
                'icon': 'fas fa-meteor',
                'color': '#00d4ff'
            },
            {
                'id': 'eclipses',
                'name': 'Eclipses',
                'description': 'Monitor solar and lunar eclipses with precise timing, visibility maps, and safety guidelines for safe observation.',
                'icon': 'fas fa-moon',
                'color': '#ff6b6b'
            },
            {
                'id': 'planetary_events',
                'name': 'Planetary Events',
                'description': 'Follow planetary conjunctions, oppositions, and transits with detailed astronomical data and viewing recommendations.',
                'icon': 'fas fa-planet-ringed',
                'color': '#4ecdc4'
            },
            {
                'id': 'comets',
                'name': 'Comets',
                'description': 'Track bright comets and their visibility periods with magnitude predictions and observation tips.',
                'icon': 'fas fa-comet',
                'color': '#45b7d1'
            },
            {
                'id': 'space_missions',
                'name': 'Space Missions',
                'description': 'Stay updated on upcoming rocket launches, satellite deployments, and space exploration milestones.',
                'icon': 'fas fa-rocket',
                'color': '#96ceb4'
            },
            {
                'id': 'near_earth_objects',
                'name': 'NASA NEO Watch',
                'description': 'Live NASA near-Earth object close approach data for the next several days.',
                'icon': 'fas fa-satellite',
                'color': '#f9ca24'
            }
        ]
        
        return jsonify({
            'categories': categories,
            'total_categories': len(categories)
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get event categories: {str(e)}'}), 500

@app.route('/api/events/calendar')
def get_events_calendar():
    """Get events organized by calendar months"""
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        
        # Generate calendar data for the specified month
        calendar_data = generate_monthly_calendar(year, month)
        
        return jsonify({
            'year': year,
            'month': month,
            'month_name': datetime(year, month, 1).strftime('%B'),
            'calendar': calendar_data,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get calendar: {str(e)}'}), 500

@app.route('/api/events/search')
def search_events():
    """Search events by keyword or criteria"""
    try:
        query = request.args.get('q', '').strip()
        event_type = request.args.get('type', 'all')
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Generate search results
        search_results = search_astronomical_events(query, event_type)
        
        return jsonify({
            'query': query,
            'type': event_type,
            'results': search_results,
            'total_found': len(search_results)
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/events/featured')
def get_featured_events():
    """Get featured upcoming events for the homepage"""
    try:
        # Get current date
        current_date = datetime.now()
        
        # Generate featured events (next 30 days)
        featured_events = generate_featured_events(current_date)
        
        return jsonify({
            'featured_events': featured_events,
            'total_featured': len(featured_events),
            'generated_at': current_date.isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get featured events: {str(e)}'}), 500

# ===== Data Processing Functions =====

def get_fallback_apod_data(date=None):
    """Provide fallback APOD data when NASA API is unavailable"""
    if not date:
        date = datetime.now().strftime('%Y-%m-%d')
    
    # Sample fallback APOD data
    fallback_data = {
        'title': 'Hubble Space Telescope - A Window to the Universe',
        'date': date,
        'explanation': 'The Hubble Space Telescope has revolutionized our understanding of the cosmos since its launch in 1990. This iconic space observatory has captured stunning images of distant galaxies, nebulae, and cosmic phenomena, providing astronomers with unprecedented views of the universe. Hubble continues to make groundbreaking discoveries and inspire wonder about our place in the cosmos.',
        'url': 'https://images.unsplash.com/photo-1446776811953-b23d0bd843bc?q=80&w=1000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'hdurl': 'https://images.unsplash.com/photo-1446776811953-b23d0bd843bc?q=80&w=2000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'display_url': 'https://images.unsplash.com/photo-1446776811953-b23d0bd843bc?q=80&w=1000&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'video_url': '',
        'media_type': 'image',
        'copyright': 'NASA/ESA',
        'thumbnail_url': 'https://images.unsplash.com/photo-1446776811953-b23d0bd843bc?q=80&w=400&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D',
        'concept_tags': ['Hubble', 'Space Telescope', 'Astronomy', 'Cosmos'],
        'processed_at': datetime.now().isoformat(),
        'is_fallback': True
    }
    
    return fallback_data

def process_apod_data(apod):
    """Process and clean APOD data"""
    try:
        media_type = apod.get('media_type', 'image')
        url = apod.get('url', '') or ''
        hdurl = apod.get('hdurl', '') or ''
        thumbnail_url = apod.get('thumbnail_url', '') or ''

        preview_url = apod.get('preview_url', '') or thumbnail_url

        if media_type == 'video':
            display_url = ''
            video_url = url
        else:
            display_url = preview_url or url
            video_url = ''
            if not hdurl:
                hdurl = url

        return {
            'title': apod.get('title', 'Unknown'),
            'date': apod.get('date', ''),
            'explanation': apod.get('explanation', ''),
            'url': url,
            'hdurl': hdurl,
            'preview_url': preview_url,
            'display_url': display_url,
            'video_url': video_url,
            'media_type': media_type,
            'copyright': apod.get('copyright', 'Public Domain'),
            'thumbnail_url': thumbnail_url,
            'concept_tags': apod.get('concept_tags', []),
            'processed_at': datetime.now().isoformat(),
            'is_fallback': False
        }
    except Exception as e:
        return {'error': f'Failed to process APOD data: {str(e)}'}

def process_neo_data(data):
    """Process and clean NEO data"""
    try:
        neo_count = data.get('element_count', 0)
        near_earth_objects = data.get('near_earth_objects', {})
        
        processed_neos = []
        for date, neos in near_earth_objects.items():
            for neo in neos:
                processed_neo = {
                    'id': neo.get('id', ''),
                    'name': neo.get('name', ''),
                    'nasa_jpl_url': neo.get('nasa_jpl_url', ''),
                    'absolute_magnitude_h': neo.get('absolute_magnitude_h', 0),
                    'estimated_diameter': neo.get('estimated_diameter', {}),
                    'is_potentially_hazardous_asteroid': neo.get('is_potentially_hazardous_asteroid', False),
                    'close_approach_data': neo.get('close_approach_data', []),
                    'orbital_data': neo.get('orbital_data', {}),
                    'date': date
                }
                processed_neos.append(processed_neo)
        
        return {
            'element_count': neo_count,
            'near_earth_objects': processed_neos,
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to process NEO data: {str(e)}'}

def process_neo_detail_data(data):
    """Process and clean detailed NEO data"""
    try:
        return {
            'id': data.get('id', ''),
            'name': data.get('name', ''),
            'nasa_jpl_url': data.get('nasa_jpl_url', ''),
            'absolute_magnitude_h': data.get('absolute_magnitude_h', 0),
            'estimated_diameter': data.get('estimated_diameter', {}),
            'is_potentially_hazardous_asteroid': data.get('is_potentially_hazardous_asteroid', False),
            'close_approach_data': data.get('close_approach_data', []),
            'orbital_data': data.get('orbital_data', {}),
            'links': data.get('links', {}),
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to process NEO detail data: {str(e)}'}

def process_mars_data(data):
    """Process and clean Mars data"""
    try:
        photos = data.get('photos', [])
        processed_photos = []
        
        for photo in photos:
            processed_photo = {
                'id': photo.get('id', ''),
                'sol': photo.get('sol', ''),
                'camera': photo.get('camera', {}),
                'img_src': photo.get('img_src', ''),
                'earth_date': photo.get('earth_date', ''),
                'rover': photo.get('rover', {}),
                'processed_at': datetime.now().isoformat()
            }
            processed_photos.append(processed_photo)
        
        return {
            'photos': processed_photos,
            'total_photos': len(processed_photos),
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to process Mars data: {str(e)}'}

def process_rovers_data(data):
    """Process and clean Mars rovers data"""
    try:
        rovers = data.get('rovers', [])
        processed_rovers = []
        
        for rover in rovers:
            processed_rover = {
                'id': rover.get('id', ''),
                'name': rover.get('name', ''),
                'landing_date': rover.get('landing_date', ''),
                'launch_date': rover.get('launch_date', ''),
                'status': rover.get('status', ''),
                'max_sol': rover.get('max_sol', ''),
                'max_date': rover.get('max_date', ''),
                'total_photos': rover.get('total_photos', ''),
                'cameras': rover.get('cameras', []),
                'processed_at': datetime.now().isoformat()
            }
            processed_rovers.append(processed_rover)
        
        return {
            'rovers': processed_rovers,
            'total_rovers': len(processed_rovers),
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to process rovers data: {str(e)}'}

def process_weather_data(data):
    """Process and clean weather data"""
    try:
        hourly = data.get('hourly', {})
        daily = data.get('daily', {})
        
        # Get current conditions (first hour)
        current = {
            'temperature': hourly.get('temperature_2m', [0])[0] if hourly.get('temperature_2m') else 0,
            'humidity': hourly.get('relative_humidity_2m', [0])[0] if hourly.get('relative_humidity_2m') else 0,
            'cloud_cover': hourly.get('cloud_cover', [0])[0] if hourly.get('cloud_cover') else 0,
            'visibility': hourly.get('visibility', [0])[0] if hourly.get('visibility') else 0,
            'wind_speed': hourly.get('wind_speed_10m', [0])[0] if hourly.get('wind_speed_10m') else 0,
            'precipitation_probability': hourly.get('precipitation_probability', [0])[0] if hourly.get('precipitation_probability') else 0,
            'pressure': hourly.get('pressure_msl', [0])[0] if hourly.get('pressure_msl') else 0
        }
        
        # Get daily forecast
        daily_forecast = []
        if daily.get('time'):
            for i in range(len(daily['time'])):
                day = {
                    'date': daily['time'][i],
                    'max_temp': daily.get('temperature_2m_max', [0])[i] if daily.get('temperature_2m_max') else 0,
                    'min_temp': daily.get('temperature_2m_min', [0])[i] if daily.get('temperature_2m_min') else 0,
                    'precipitation_probability': daily.get('precipitation_probability_max', [0])[i] if daily.get('precipitation_probability_max') else 0,
                    'wind_speed': daily.get('wind_speed_10m_max', [0])[i] if daily.get('wind_speed_10m_max') else 0,
                    'uv_index': daily.get('uv_index_max', [0])[i] if daily.get('uv_index_max') else 0
                }
                daily_forecast.append(day)
        
        # Enhanced stargazing analysis
        stargazing_conditions = analyze_stargazing_conditions(current, daily_forecast)
        
        return {
            'current': current,
            'daily_forecast': daily_forecast,
            'stargazing_conditions': stargazing_conditions,
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to process weather data: {str(e)}'}

def process_hourly_weather_data(data):
    """Process and clean hourly weather data"""
    try:
        hourly = data.get('hourly', {})
        time = hourly.get('time', [])
        temperature = hourly.get('temperature_2m', [])
        relative_humidity = hourly.get('relative_humidity_2m', [])
        cloud_cover = hourly.get('cloud_cover', [])
        visibility = hourly.get('visibility', [])
        wind_speed = hourly.get('wind_speed_10m', [])
        precipitation_probability = hourly.get('precipitation_probability', [])
        weather_code = hourly.get('weather_code', [])

        processed_hourly_data = []
        for i in range(len(time)):
            processed_hour = {
                'time': time[i],
                'temperature': temperature[i],
                'relative_humidity': relative_humidity[i],
                'cloud_cover': cloud_cover[i],
                'visibility': visibility[i],
                'wind_speed': wind_speed[i],
                'precipitation_probability': precipitation_probability[i],
                'weather_code': weather_code[i]
            }
            processed_hourly_data.append(processed_hour)

        return {
            'hourly_data': processed_hourly_data,
            'total_hours': len(processed_hourly_data),
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to process hourly weather data: {str(e)}'}

def generate_weather_alerts(data):
    """Generate weather alerts and warnings based on current conditions"""
    try:
        current_cloud_cover = data.get('hourly', {}).get('cloud_cover', [0])[0]
        current_precipitation_probability = data.get('hourly', {}).get('precipitation_probability', [0])[0]
        current_wind_speed = data.get('hourly', {}).get('wind_speed_10m', [0])[0]
        current_temperature = data.get('hourly', {}).get('temperature_2m', [0])[0]

        alerts = []

        # Wind Speed Alert
        if current_wind_speed > 15:
            alerts.append({
                'type': 'wind',
                'message': 'High wind speed detected. Consider reducing telescope use or securing equipment.',
                'severity': 'warning'
            })

        # Precipitation Alert
        if current_precipitation_probability > 70:
            alerts.append({
                'type': 'precipitation',
                'message': 'High chance of precipitation. Outdoor observation may be limited or interrupted.',
                'severity': 'warning'
            })

        # Cloud Cover Alert
        if current_cloud_cover > 80:
            alerts.append({
                'type': 'cloud_cover',
                'message': 'Heavy cloud cover detected. Limited visibility and optimal stargazing conditions.',
                'severity': 'warning'
            })

        # Temperature Alert
        if current_temperature < 0:
            alerts.append({
                'type': 'temperature',
                'message': 'Extremely low temperatures detected. Outdoor observation may be challenging.',
                'severity': 'warning'
            })

        return {
            'alerts': alerts,
            'total_alerts': len(alerts),
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to generate weather alerts: {str(e)}'}

def calculate_astronomical_conditions(lat, lon, current_date):
    """Calculate astronomical conditions (moon phase, light pollution)"""
    try:
        # Get current date for moon phase calculation
        year = current_date.year
        month = current_date.month
        day = current_date.day
        hour = current_date.hour
        minute = current_date.minute

        # Calculate moon phase
        url = f"https://api.astronomyapi.com/api/v2/moon/phase?api_key={os.getenv('ASTRONOMY_API_KEY')}&latitude={lat}&longitude={lon}&date={year}-{month}-{day}&time={hour}:{minute}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        moon_phase_data = response.json()
        moon_phase = moon_phase_data.get('phase', {}).get('fraction', 0)

        # Calculate light pollution
        # This is a simplified example. A real implementation would involve a light pollution index API.
        # For now, we'll return a placeholder.
        light_pollution_index = 0 # 0 for dark sky, 1 for light-polluted

        return {
            'moon_phase': moon_phase,
            'light_pollution_index': light_pollution_index,
            'processed_at': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': f'Failed to calculate astronomical conditions: {str(e)}'}

def process_historical_weather_data(data, start_date, end_date):
    """Process historical weather data for trend analysis"""
    try:
        hourly = data.get('hourly', {})
        time = hourly.get('time', [])
        temperature = hourly.get('temperature_2m', [])
        cloud_cover = hourly.get('cloud_cover', [])
        visibility = hourly.get('visibility', [])
        wind_speed = hourly.get('wind_speed_10m', [])
        
        # Calculate daily averages
        daily_stats = {}
        for i in range(len(time)):
            date = time[i][:10]  # Extract date part
            if date not in daily_stats:
                daily_stats[date] = {
                    'temperatures': [],
                    'cloud_covers': [],
                    'visibilities': [],
                    'wind_speeds': []
                }
            
            daily_stats[date]['temperatures'].append(temperature[i])
            daily_stats[date]['cloud_covers'].append(cloud_cover[i])
            daily_stats[date]['visibilities'].append(visibility[i])
            daily_stats[date]['wind_speeds'].append(wind_speed[i])
        
        # Calculate averages for each day
        processed_daily = []
        for date, stats in daily_stats.items():
            processed_daily.append({
                'date': date,
                'avg_temperature': sum(stats['temperatures']) / len(stats['temperatures']),
                'avg_cloud_cover': sum(stats['cloud_covers']) / len(stats['cloud_covers']),
                'avg_visibility': sum(stats['visibilities']) / len(stats['visibilities']),
                'avg_wind_speed': sum(stats['wind_speeds']) / len(stats['wind_speeds']),
                'min_temperature': min(stats['temperatures']),
                'max_temperature': max(stats['temperatures']),
                'stargazing_score': calculate_daily_stargazing_score(
                    sum(stats['cloud_covers']) / len(stats['cloud_covers']),
                    sum(stats['visibilities']) / len(stats['visibilities']),
                    sum(stats['wind_speeds']) / len(stats['wind_speeds'])
                )
            })
        
        return {
            'historical_data': processed_daily,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_days': len(processed_daily),
            'processed_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {'error': f'Failed to process historical weather data: {str(e)}'}

def calculate_daily_stargazing_score(avg_cloud_cover, avg_visibility, avg_wind_speed):
    """Calculate stargazing score for historical data"""
    try:
        score = 100
        
        # Deduct points for poor conditions
        if avg_cloud_cover > 80:
            score -= 40
        elif avg_cloud_cover > 60:
            score -= 25
        elif avg_cloud_cover > 40:
            score -= 15
        elif avg_cloud_cover > 20:
            score -= 5
        
        if avg_visibility < 5000:
            score -= 30
        elif avg_visibility < 10000:
            score -= 15
        
        if avg_wind_speed > 20:
            score -= 20
        elif avg_wind_speed > 15:
            score -= 10
        
        return max(0, score)
        
    except Exception as e:
        return 0

def analyze_stargazing_conditions(current_weather, daily_forecast):
    """Analyze weather conditions for optimal stargazing"""
    try:
        cloud_cover = current_weather.get('cloud_cover', 100)
        visibility = current_weather.get('visibility', 0)
        wind_speed = current_weather.get('wind_speed', 0)
        precipitation_probability = current_weather.get('precipitation_probability', 100)
        
        # Calculate stargazing score (0-100)
        score = 100
        
        # Deduct points for poor conditions
        if cloud_cover > 80:
            score -= 40
        elif cloud_cover > 60:
            score -= 25
        elif cloud_cover > 40:
            score -= 15
        elif cloud_cover > 20:
            score -= 5
        
        if visibility < 5000:
            score -= 30
        elif visibility < 10000:
            score -= 15
        
        if wind_speed > 20:
            score -= 20
        elif wind_speed > 15:
            score -= 10
        
        if precipitation_probability > 70:
            score -= 25
        elif precipitation_probability > 40:
            score -= 15
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        # Generate recommendation based on score
        if score >= 80:
            recommendation = "Excellent conditions for stargazing!"
            best_time = "All night long"
        elif score >= 60:
            recommendation = "Good conditions for stargazing"
            best_time = "Late evening to early morning"
        elif score >= 40:
            recommendation = "Moderate conditions for stargazing"
            best_time = "Check conditions hourly"
        elif score >= 20:
            recommendation = "Poor conditions for stargazing"
            best_time = "Not recommended"
        else:
            recommendation = "Very poor conditions for stargazing"
            best_time = "Avoid observation"
        
        # Additional insights
        insights = []
        if cloud_cover < 20:
            insights.append("Clear skies - perfect for deep sky objects")
        if visibility > 10000:
            insights.append("Excellent visibility - great for faint objects")
        if wind_speed < 10:
            insights.append("Calm conditions - stable viewing")
        if precipitation_probability < 20:
            insights.append("Low chance of precipitation")
        
        return {
            'score': score,
            'recommendation': recommendation,
            'best_time': best_time,
            'cloud_cover': cloud_cover,
            'visibility': visibility,
            'wind_speed': wind_speed,
            'precipitation_probability': precipitation_probability,
            'insights': insights,
            'detailed_analysis': get_detailed_stargazing_analysis(cloud_cover, visibility, wind_speed, precipitation_probability)
        }
        
    except Exception as e:
        return {
            'score': 0,
            'recommendation': 'Unable to analyze conditions',
            'best_time': 'Check back later',
            'error': str(e)
        }

def get_detailed_stargazing_analysis(cloud_cover, visibility, wind_speed, precipitation_probability):
    """Get detailed analysis of stargazing conditions"""
    analysis = []
    
    # Cloud cover analysis
    if cloud_cover < 20:
        analysis.append("Cloud cover: Minimal clouds - ideal for all types of astronomical observation")
    elif cloud_cover < 40:
        analysis.append("Cloud cover: Scattered clouds - good for most observations with occasional interruptions")
    elif cloud_cover < 60:
        analysis.append("Cloud cover: Partly cloudy - suitable for bright objects and planets")
    else:
        analysis.append("Cloud cover: Heavy cloud cover - limited observation opportunities")
    
    # Visibility analysis
    if visibility > 10000:
        analysis.append("Visibility: Excellent - perfect for faint deep sky objects and detailed planetary observation")
    elif visibility > 5000:
        analysis.append("Visibility: Good - suitable for most astronomical objects")
    elif visibility > 3000:
        analysis.append("Visibility: Moderate - limited to bright objects and planets")
    else:
        analysis.append("Visibility: Poor - only bright planets and moon visible")
    
    # Wind analysis
    if wind_speed < 10:
        analysis.append("Wind: Calm conditions - stable viewing for high magnification observation")
    elif wind_speed < 15:
        analysis.append("Wind: Light breeze - generally good for most observations")
    elif wind_speed < 20:
        analysis.append("Wind: Moderate wind - may affect high magnification viewing")
    else:
        analysis.append("Wind: Strong winds - not recommended for telescope use")
    
    # Precipitation analysis
    if precipitation_probability < 20:
        analysis.append("Precipitation: Very low chance - excellent for extended observation sessions")
    elif precipitation_probability < 40:
        analysis.append("Precipitation: Low chance - good for observation with weather monitoring")
    elif precipitation_probability < 70:
        analysis.append("Precipitation: Moderate chance - plan for potential interruptions")
    else:
        analysis.append("Precipitation: High chance - not recommended for outdoor observation")
    
    return analysis

# ===== Astronomical Events Helper Functions =====

def generate_upcoming_events(current_date, event_type='all', start_date=None, end_date=None):
    """Generate upcoming astronomical events data"""
    try:
        # Define start and end dates for event generation
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
        else:
            start = current_date
            
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end = current_date + timedelta(days=365)  # Default to 1 year ahead
        
        # Generate events based on type
        if event_type == 'meteor_showers':
            events = generate_meteor_shower_events(start, end)
        elif event_type == 'eclipses':
            events = generate_eclipse_events(start, end)
        elif event_type == 'planetary_events':
            events = generate_planetary_events(start, end)
        elif event_type == 'comets':
            events = generate_comet_events(start, end)
        elif event_type == 'space_missions':
            events = generate_space_mission_events(start, end)
        elif event_type == 'near_earth_objects':
            events = generate_nasa_neo_events(start, end)
        else:
            # Generate all types of events
            events = []
            events.extend(generate_meteor_shower_events(start, end))
            events.extend(generate_eclipse_events(start, end))
            events.extend(generate_planetary_events(start, end))
            events.extend(generate_comet_events(start, end))
            events.extend(generate_space_mission_events(start, end))
            events.extend(generate_nasa_neo_events(start, end))
        
        # Sort events by date
        events.sort(key=lambda x: x['date'])
        
        return events
        
    except Exception as e:
        return [{'error': f'Failed to generate events: {str(e)}'}]

def generate_meteor_shower_events(start_date, end_date):
    """Generate meteor shower events for the given date range"""
    meteor_showers = [
        {
            'name': 'Quadrantids',
            'peak_date': '2027-01-03',
            'start_date': '2027-01-01',
            'end_date': '2027-01-05',
            'peak_rate': '120 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Boötes',
            'description': 'One of the year\'s best meteor showers, known for bright fireballs.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Lyrids',
            'peak_date': '2027-04-22',
            'start_date': '2027-04-16',
            'end_date': '2027-04-25',
            'peak_rate': '18 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Lyra',
            'description': 'Medium-strength meteor shower with occasional bright meteors.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Arietids',
            'peak_date': '2026-06-07',
            'start_date': '2026-05-29',
            'end_date': '2026-06-19',
            'peak_rate': '60 meteors/hour',
            'best_viewing': 'Pre-dawn twilight',
            'constellation': 'Aries',
            'description': 'A strong daytime meteor shower that can produce visible meteors near dawn.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Zeta Perseids',
            'peak_date': '2026-06-09',
            'start_date': '2026-05-20',
            'end_date': '2026-07-07',
            'peak_rate': '40 meteors/hour',
            'best_viewing': 'Pre-dawn twilight',
            'constellation': 'Perseus',
            'description': 'A daytime meteor shower best attempted in the early morning sky.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Delta Aquarids',
            'peak_date': '2026-07-28',
            'start_date': '2026-07-12',
            'end_date': '2026-08-19',
            'peak_rate': '20 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Aquarius',
            'description': 'A steady southern-sky meteor shower that overlaps with the Perseids.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Perseids',
            'peak_date': '2026-08-12',
            'start_date': '2026-07-17',
            'end_date': '2026-08-24',
            'peak_rate': '100 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Perseus',
            'description': 'One of the most spectacular meteor showers of the year.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Orionids',
            'peak_date': '2026-10-21',
            'start_date': '2026-10-02',
            'end_date': '2026-11-07',
            'peak_rate': '20 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Orion',
            'description': 'Medium-strength meteor shower associated with Halley\'s Comet.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Leonids',
            'peak_date': '2026-11-17',
            'start_date': '2026-11-06',
            'end_date': '2026-11-30',
            'peak_rate': '15 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Leo',
            'description': 'Variable meteor shower that can produce meteor storms.',
            'type': 'meteor_shower'
        },
        {
            'name': 'Geminids',
            'peak_date': '2026-12-14',
            'start_date': '2026-12-04',
            'end_date': '2026-12-17',
            'peak_rate': '120 meteors/hour',
            'best_viewing': 'After midnight',
            'constellation': 'Gemini',
            'description': 'One of the most reliable meteor showers of the year.',
            'type': 'meteor_shower'
        }
    ]
    
    events = []
    for shower in meteor_showers:
        peak_date = datetime.strptime(shower['peak_date'], '%Y-%m-%d')
        if start_date <= peak_date <= end_date:
            event = shower.copy()
            event['date'] = shower['peak_date']
            event['id'] = f"meteor_{shower['name'].lower().replace(' ', '_')}"
            enhanced_details = get_default_enhanced_data(event['type'])
            event.update(enhanced_details)
            events.append(event)
    
    return events

def generate_eclipse_events(start_date, end_date):
    """Generate solar and lunar eclipse events for the given date range"""
    eclipses = [
        {
            'name': 'Total Solar Eclipse',
            'date': '2026-08-12',
            'eclipse_type': 'total',
            'duration': 'Up to 2 minutes 18 seconds of totality',
            'max_coverage': '100% in the path of totality',
            'visibility': 'Greenland, Iceland, Spain, Russia, and surrounding partial-eclipse regions',
            'description': 'A major total solar eclipse crossing parts of the North Atlantic and Europe.',
            'safety_note': 'Never look directly at the Sun without proper eye protection.',
            'type': 'eclipse'
        },
        {
            'name': 'Partial Lunar Eclipse',
            'date': '2026-08-28',
            'eclipse_type': 'partial',
            'duration': 'Several hours',
            'max_coverage': 'Deep partial eclipse',
            'visibility': 'Best from parts of Europe, Africa, Asia, and Australia',
            'description': 'A deep partial lunar eclipse where much of the Moon passes through Earth\'s umbral shadow.',
            'safety_note': 'Safe to view with the naked eye.',
            'type': 'eclipse'
        }
    ]
    
    events = []
    for eclipse in eclipses:
        eclipse_date = datetime.strptime(eclipse['date'], '%Y-%m-%d')
        if start_date <= eclipse_date <= end_date:
            event = eclipse.copy()
            event['id'] = f"eclipse_{eclipse['type']}_{eclipse['date'].replace('-', '_')}"
            enhanced_details = get_default_enhanced_data(event['type'])
            event.update(enhanced_details)
            events.append(event)
    
    return events

def generate_planetary_events(start_date, end_date):
    """Generate planetary conjunction and opposition events for the given date range"""
    planetary_events = [
        {
            'name': 'June Solstice',
            'date': '2026-06-21',
            'planets': ['Earth'],
            'separation': 'N/A',
            'best_viewing': 'All day',
            'description': 'The June solstice marks astronomical summer in the Northern Hemisphere and winter in the Southern Hemisphere.',
            'type': 'planetary_event'
        },
        {
            'name': 'Saturn Opposition',
            'date': '2026-10-04',
            'planets': ['Saturn'],
            'separation': 'N/A',
            'best_viewing': 'All night',
            'description': 'Saturn reaches opposition, offering one of the best views of the ringed planet for the year.',
            'type': 'planetary_event'
        },
        {
            'name': 'Saturn Opposition',
            'date': '2026-10-05',
            'planets': ['Moon', 'Mars'],
            'separation': 'Close visual pairing',
            'best_viewing': 'Before sunrise',
            'description': 'The Moon and Mars appear close together in the morning sky.',
            'type': 'planetary_event'
        }
    ]
    
    events = []
    for event in planetary_events:
        event_date = datetime.strptime(event['date'], '%Y-%m-%d')
        if start_date <= event_date <= end_date:
            new_event = event.copy()
            new_event['id'] = f"planetary_{event['name'].lower().replace(' ', '_').replace('-', '_')}"
            enhanced_details = get_default_enhanced_data(new_event['type'])
            new_event.update(enhanced_details)
            events.append(new_event)
    
    return events

def generate_comet_events(start_date, end_date):
    """Generate comet visibility events for the given date range"""
    comets = [
        {
            'name': 'Comet Visibility Watch',
            'date': '2026-07-01',
            'magnitude': 'Forecast variable',
            'constellation': 'Check current ephemeris',
            'best_viewing': 'Dark skies with binoculars',
            'description': 'A comet watch entry for checking current visibility, brightness, and sky position as conditions change.',
            'type': 'comet'
        }
    ]
    
    events = []
    for comet in comets:
        comet_date = datetime.strptime(comet['date'], '%Y-%m-%d')
        if start_date <= comet_date <= end_date:
            event = comet.copy()
            event['id'] = f"comet_{comet['name'].lower().replace('/', '_').replace(' ', '_')}"
            enhanced_details = get_default_enhanced_data(event['type'])
            event.update(enhanced_details)
            events.append(event)
    
    return events

def generate_space_mission_events(start_date, end_date):
    """Generate upcoming space mission events for the given date range"""
    missions = [
        {
            'name': 'Artemis II Mission Watch',
            'date': '2026-09-01',
            'mission_type': 'manned_moon_mission',
            'agency': 'NASA',
            'description': 'Follow NASA updates for the first crewed Artemis mission around the Moon.',
            'type': 'space_mission'
        },
        {
            'name': 'Europa Clipper Cruise Update',
            'date': '2026-10-10',
            'mission_type': 'planetary_exploration',
            'agency': 'NASA',
            'description': 'A mission milestone watch for NASA\'s Europa Clipper as it continues its journey toward Jupiter.',
            'type': 'space_mission'
        }
    ]
    
    events = []
    for mission in missions:
        mission_date = datetime.strptime(mission['date'], '%Y-%m-%d')
        if start_date <= mission_date <= end_date:
            event = mission.copy()
            event['id'] = f"mission_{mission['name'].lower().replace(' ', '_')}"
            enhanced_details = get_default_enhanced_data(event['type'])
            event.update(enhanced_details)
            events.append(event)
    
    return events

def generate_nasa_neo_events(start_date, end_date):
    """Fetch live NASA near-Earth object close approaches for the next available week."""
    try:
        today = datetime.now().date()
        window_start = max(start_date.date(), today)
        window_end = min(end_date.date(), today + timedelta(days=7))

        if window_start > window_end:
            return []

        url = f"{NASA_BASE_URL}/neo/rest/v1/feed"
        params = {
            'api_key': NASA_API_KEY,
            'start_date': window_start.strftime('%Y-%m-%d'),
            'end_date': window_end.strftime('%Y-%m-%d')
        }
        with requests.Session() as session:
            session.trust_env = False
            response = session.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        events = []
        for date_key, objects in data.get('near_earth_objects', {}).items():
            for neo in objects[:3]:
                approach = (neo.get('close_approach_data') or [{}])[0]
                miss_distance = approach.get('miss_distance', {}).get('kilometers', '0')
                velocity = approach.get('relative_velocity', {}).get('kilometers_per_hour', '0')
                diameter = neo.get('estimated_diameter', {}).get('kilometers', {})
                min_diameter = diameter.get('estimated_diameter_min')
                max_diameter = diameter.get('estimated_diameter_max')
                size_text = 'Unknown'
                if min_diameter and max_diameter:
                    size_text = f"{min_diameter:.3f}-{max_diameter:.3f} km"

                events.append({
                    'id': f"neo_{neo.get('id', date_key)}",
                    'name': f"NEO Close Approach: {neo.get('name', 'Unknown object')}",
                    'date': date_key,
                    'agency': 'NASA NEO',
                    'best_viewing': 'Data event, not usually naked-eye visible',
                    'description': (
                        f"NASA-tracked near-Earth object close approach. Estimated diameter: {size_text}. "
                        f"Miss distance: {float(miss_distance):,.0f} km. "
                        f"Relative velocity: {float(velocity):,.0f} km/h."
                    ),
                    'visibility': 'Scientific tracking event',
                    'type': 'near_earth_object',
                    'source_url': neo.get('nasa_jpl_url')
                })

        return events
    except Exception as e:
        print(f"NASA NEO event fetch failed: {e}", flush=True)
        return []

def enhance_event_with_ai(event):
    """Enhance event details using Gemini AI"""
    # Check if Gemini AI is available
    if not GEMINI_AVAILABLE:
        print("Gemini AI not available, using default enhanced data")
        return get_default_enhanced_data(event.get('type', 'event'))
    
    try:
        event_type = event.get('type', 'event')
        event_name = event.get('name', 'Unknown Event')
        
        # Create AI prompt based on event type
        if event_type == 'meteor_shower':
            prompt = f"""As an expert astronomer, provide enhanced details for the {event_name} meteor shower. Include:

1. Viewing Tips (3-5 practical tips for optimal viewing)
2. Equipment Recommendations (what to bring, telescopes/binoculars if needed)
3. Photography Tips (if applicable)
4. Historical Significance (brief mention of discovery/origin)
5. Best Locations (general geographic recommendations)
6. Weather Considerations
7. Fun Facts (2-3 interesting facts)

Format as JSON with keys: viewing_tips, equipment_recommendations, photography_tips, historical_significance, best_locations, weather_considerations, fun_facts

Keep each section concise but informative for amateur astronomers."""
            
        elif event_type == 'eclipse':
            if event.get('type') == 'solar':
                prompt = f"""As an expert astronomer, provide enhanced details for the {event_name}. Include:

1. Safety Guidelines (detailed safety information)
2. Viewing Equipment (specific equipment needed)
3. Photography Tips (safe eclipse photography)
4. Historical Significance
5. Best Viewing Locations
6. Timing Details (specific phases)
7. Weather Considerations

Format as JSON with keys: safety_guidelines, viewing_equipment, photography_tips, historical_significance, best_locations, timing_details, weather_considerations

Emphasize safety for solar eclipse viewing."""
            else:
                prompt = f"""As an expert astronomer, provide enhanced details for the {event_name}. Include:

1. Viewing Tips (optimal viewing conditions)
2. Equipment Recommendations
3. Photography Tips
4. Historical Significance
5. Best Viewing Locations
6. Timing Details (specific phases)
7. Weather Considerations

Format as JSON with keys: viewing_tips, equipment_recommendations, photography_tips, historical_significance, best_locations, timing_details, weather_considerations"""
                
        elif event_type == 'planetary_event':
            prompt = f"""As an expert astronomer, provide enhanced details for the {event_name}. Include:

1. Viewing Tips (when and how to observe)
2. Equipment Recommendations (telescopes, binoculars, naked eye)
3. Photography Tips (if applicable)
4. Astronomical Significance (why this event is important)
5. Best Viewing Locations
6. Timing Details
7. Fun Facts

Format as JSON with keys: viewing_tips, equipment_recommendations, photography_tips, astronomical_significance, best_locations, timing_details, fun_facts"""
            
        elif event_type == 'comet':
            prompt = f"""As an expert astronomer, provide enhanced details for the {event_name}. Include:

1. Viewing Tips (how to spot the comet)
2. Equipment Recommendations (what you need to see it)
3. Photography Tips (comet photography)
4. Historical Significance
5. Best Viewing Locations
6. Expected Brightness Changes
7. Fun Facts

Format as JSON with keys: viewing_tips, equipment_recommendations, photography_tips, historical_significance, best_locations, brightness_changes, fun_facts"""
            
        elif event_type == 'space_mission':
            prompt = f"""As an expert astronomer, provide enhanced details for the {event_name}. Include:

1. Mission Objectives (what they're trying to achieve)
2. Scientific Significance (why this mission matters)
3. Technology Details (key instruments/technology)
4. Timeline (mission phases)
5. Public Viewing Opportunities (if any)
6. Historical Context
7. Fun Facts

Format as JSON with keys: mission_objectives, scientific_significance, technology_details, timeline, public_viewing, historical_context, fun_facts"""
        
        else:
            prompt = f"""As an expert astronomer, provide enhanced details for the {event_name}. Include:

1. Viewing Tips
2. Equipment Recommendations
3. Historical Significance
4. Best Viewing Locations
5. Fun Facts

Format as JSON with keys: viewing_tips, equipment_recommendations, historical_significance, best_locations, fun_facts"""

        # Generate AI response
        ai_text, _model_used = generate_gemini_content(prompt)
        
        try:
            # Try to parse JSON response
            import json
            enhanced_data = json.loads(ai_text)
            return enhanced_data
        except json.JSONDecodeError:
            # If JSON parsing fails, create structured data from text
            return create_structured_data_from_text(ai_text, event_type)
            
    except Exception as e:
        print(f"Error enhancing event with AI: {str(e)}")
        # Return default enhanced data
        return get_default_enhanced_data(event.get('type', 'event'))

def create_structured_data_from_text(ai_text, event_type):
    """Create structured data from AI text response when JSON parsing fails"""
    try:
        # Extract key information from AI response
        lines = ai_text.split('\n')
        viewing_tips = []
        equipment_recommendations = []
        fun_facts = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if 'viewing tip' in line.lower() or 'tip' in line.lower():
                if line and not line.startswith('#'):
                    viewing_tips.append(line)
            elif 'equipment' in line.lower() or 'telescope' in line.lower() or 'binocular' in line.lower():
                if line and not line.startswith('#'):
                    equipment_recommendations.append(line)
            elif 'fact' in line.lower() or 'interesting' in line.lower():
                if line and not line.startswith('#'):
                    fun_facts.append(line)
        
        return {
            'viewing_tips': viewing_tips[:3] if viewing_tips else get_default_viewing_tips(event_type),
            'equipment_recommendations': equipment_recommendations[:2] if equipment_recommendations else get_default_equipment(event_type),
            'fun_facts': fun_facts[:2] if fun_facts else get_default_fun_facts(event_type)
        }
        
    except Exception as e:
        print(f"Error creating structured data: {str(e)}")
        return get_default_enhanced_data(event_type)

def get_default_enhanced_data(event_type):
    """Get default enhanced data when AI enhancement fails"""
    if event_type == 'meteor_shower':
        return {
            'viewing_tips': [
                'Find a dark location away from city lights',
                'Allow your eyes to adjust to darkness for 20-30 minutes',
                'Look up at the sky, not at any specific point'
            ],
            'equipment_recommendations': [
                'No special equipment needed - visible to naked eye',
                'Optional: Red flashlight to preserve night vision'
            ],
            'fun_facts': [
                'Meteor showers occur when Earth passes through comet debris trails',
                'The Perseids are named after the constellation Perseus'
            ]
        }
    elif event_type == 'eclipse':
        return {
            'viewing_tips': [
                'Check local weather conditions before planning',
                'Arrive at viewing location early to set up',
                'Bring appropriate safety equipment for solar eclipses'
            ],
            'equipment_recommendations': [
                'Solar eclipse: Special solar viewing glasses or filters',
                'Lunar eclipse: No special equipment needed'
            ],
            'fun_facts': [
                'Eclipses have been recorded for thousands of years',
                'Solar eclipses are only visible from specific locations on Earth'
            ]
        }
    else:
        return {
            'viewing_tips': [
                'Find a clear, dark location',
                'Check weather conditions',
                'Allow time for your eyes to adjust to darkness'
            ],
            'equipment_recommendations': [
                'Basic equipment: Your eyes and patience',
                'Optional: Binoculars or small telescope'
            ],
            'fun_facts': [
                'Many astronomical events are visible without special equipment',
                'The best viewing often comes from patience and preparation'
            ]
        }

def get_default_viewing_tips(event_type):
    """Get default viewing tips for specific event types"""
    tips = {
        'meteor_shower': [
            'Find a dark location away from city lights',
            'Allow your eyes to adjust to darkness for 20-30 minutes',
            'Look up at the sky, not at any specific point'
        ],
        'eclipse': [
            'Check local weather conditions before planning',
            'Arrive at viewing location early to set up',
            'Bring appropriate safety equipment for solar eclipses'
        ],
        'planetary_event': [
            'Check when the planets are above the horizon',
            'Use a star chart or app to locate the event',
            'Look for the event during optimal viewing times'
        ],
        'comet': [
            'Find a dark location with clear skies',
            'Use binoculars for better visibility',
            'Look in the direction of the comet\'s constellation'
        ],
        'space_mission': [
            'Follow official mission updates and livestreams',
            'Check for public viewing events in your area',
            'Learn about the mission objectives beforehand'
        ]
    }
    return tips.get(event_type, tips['planetary_event'])

def get_default_equipment(event_type):
    """Get default equipment recommendations for specific event types"""
    equipment = {
        'meteor_shower': [
            'No special equipment needed - visible to naked eye',
            'Optional: Red flashlight to preserve night vision'
        ],
        'eclipse': [
            'Solar eclipse: Special solar viewing glasses or filters',
            'Lunar eclipse: No special equipment needed'
        ],
        'planetary_event': [
            'Basic equipment: Your eyes',
            'Optional: Small telescope or binoculars'
        ],
        'comet': [
            'Binoculars recommended for better visibility',
            'Optional: Small telescope for detailed views'
        ],
        'space_mission': [
            'Internet connection for live updates',
            'Optional: Visit local planetarium or observatory'
        ]
    }
    return equipment.get(event_type, equipment['planetary_event'])

def get_default_fun_facts(event_type):
    """Get default fun facts for specific event types"""
    facts = {
        'meteor_shower': [
            'Meteor showers occur when Earth passes through comet debris trails',
            'The Perseids are named after the constellation Perseus'
        ],
        'eclipse': [
            'Eclipses have been recorded for thousands of years',
            'Solar eclipses are only visible from specific locations on Earth'
        ],
        'planetary_event': [
            'Planetary conjunctions have guided navigation for centuries',
            'Some planetary events are visible even from light-polluted cities'
        ],
        'comet': [
            'Comets are often called "dirty snowballs" by astronomers',
            'Halley\'s Comet returns every 76 years'
        ],
        'space_mission': [
            'Space missions often carry instruments designed by international teams',
            'Many missions have discovered unexpected phenomena'
        ]
    }
    return facts.get(event_type, facts['planetary_event'])

def generate_monthly_calendar(year, month):
    """Generate calendar data for a specific month with astronomical events"""
    try:
        # Get the first day of the month
        first_day = datetime(year, month, 1)
        
        # Get the last day of the month
        if month == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month + 1, 1) - timedelta(days=1)
        
        # Generate events for this month
        calendar_data = generate_upcoming_events(
            datetime.now(), 
            'all', 
            first_day.strftime('%Y-%m-%d'),
            last_day.strftime('%Y-%m-%d')
        )
        
        # Create calendar structure
        calendar = []
        current_date = first_day
        
        # Add days before the first day of the month (from previous month)
        while current_date.weekday() != 0:  # Monday = 0
            prev_date = current_date - timedelta(days=1)
            calendar.append({
                'date': prev_date.strftime('%Y-%m-%d'),
                'day': prev_date.day,
                'is_current_month': False,
                'events': []
            })
            current_date = prev_date
        
        # Add all days of the current month
        while current_date <= last_day:
            # Find events for this date
            date_events = [event for event in calendar_data if event['date'] == current_date.strftime('%Y-%m-%d')]
            
            calendar.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day': current_date.day,
                'is_current_month': True,
                'events': date_events
            })
            current_date += timedelta(days=1)
        
        # Add days after the last day of the month (from next month)
        while current_date.weekday() != 0:  # Monday = 0
            calendar.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'day': current_date.day,
                'is_current_month': False,
                'events': []
            })
            current_date += timedelta(days=1)
        
        return calendar
        
    except Exception as e:
        return [{'error': f'Failed to generate calendar: {str(e)}'}]

def search_astronomical_events(query, event_type='all'):
    """Search astronomical events by keyword"""
    try:
        # Generate all events for the next year
        current_date = datetime.now()
        all_events = generate_upcoming_events(current_date, event_type)
        
        # Search through events
        query_lower = query.lower()
        results = []
        
        for event in all_events:
            # Search in name, description, and other relevant fields
            searchable_text = f"{event.get('name', '')} {event.get('description', '')} {event.get('constellation', '')} {event.get('planets', [])}"
            
            if query_lower in searchable_text.lower():
                results.append(event)
        
        return results
        
    except Exception as e:
        return [{'error': f'Search failed: {str(e)}'}]

def generate_featured_events(current_date):
    """Generate featured events for the next 30 days"""
    try:
        # Get events for the next 30 days
        end_date = current_date + timedelta(days=30)
        upcoming_events = generate_upcoming_events(current_date, 'all', current_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        
        # Select the most interesting events (limit to 6)
        featured = upcoming_events[:6]
        
        return featured
        
    except Exception as e:
        return [{'error': f'Failed to generate featured events: {str(e)}'}]

def generate_weather_summary_stats(current_data, hourly_data):
    """Generate comprehensive weather summary statistics"""
    try:
        current_hourly = current_data.get('hourly', {})
        current_daily = current_data.get('daily', {})
        
        # Current Conditions
        current_temp = current_hourly.get('temperature_2m', [0])[0]
        current_humidity = current_hourly.get('relative_humidity_2m', [0])[0]
        current_cloud_cover = current_hourly.get('cloud_cover', [0])[0]
        current_visibility = current_hourly.get('visibility', [0])[0]
        current_wind_speed = current_hourly.get('wind_speed_10m', [0])[0]
        current_precip_prob = current_hourly.get('precipitation_probability', [0])[0]
        
        # Daily Forecast
        daily_max_temp = current_daily.get('temperature_2m_max', [0])[0]
        daily_min_temp = current_daily.get('temperature_2m_min', [0])[0]
        daily_precip_prob_max = current_daily.get('precipitation_probability_max', [0])[0]
        daily_wind_speed_max = current_daily.get('wind_speed_10m_max', [0])[0]
        daily_uv_index_max = current_daily.get('uv_index_max', [0])[0]
        
        # Hourly Forecast (for the next 24 hours)
        next_hour_temp = hourly_data.get('hourly', {}).get('temperature_2m', [])[0]
        next_hour_humidity = hourly_data.get('hourly', {}).get('relative_humidity_2m', [])[0]
        next_hour_cloud_cover = hourly_data.get('hourly', {}).get('cloud_cover', [])[0]
        next_hour_visibility = hourly_data.get('hourly', {}).get('visibility', [])[0]
        next_hour_wind_speed = hourly_data.get('hourly', {}).get('wind_speed_10m', [])[0]
        next_hour_precip_prob = hourly_data.get('hourly', {}).get('precipitation_probability', [])[0]
        
        return {
            'current_conditions': {
                'temperature': current_temp,
                'humidity': current_humidity,
                'cloud_cover': current_cloud_cover,
                'visibility': current_visibility,
                'wind_speed': current_wind_speed,
                'precipitation_probability': current_precip_prob
            },
            'daily_forecast': {
                'max_temperature': daily_max_temp,
                'min_temperature': daily_min_temp,
                'max_precipitation_probability': daily_precip_prob_max,
                'max_wind_speed': daily_wind_speed_max,
                'max_uv_index': daily_uv_index_max
            },
            'hourly_forecast': {
                'next_hour_temperature': next_hour_temp,
                'next_hour_humidity': next_hour_humidity,
                'next_hour_cloud_cover': next_hour_cloud_cover,
                'next_hour_visibility': next_hour_visibility,
                'next_hour_wind_speed': next_hour_wind_speed,
                'next_hour_precipitation_probability': next_hour_precip_prob
            }
        }
    except Exception as e:
        return {'error': f'Failed to generate weather summary stats: {str(e)}'}

# ===== PROFILE MANAGEMENT =====

# Import Supabase manager
try:
    from supabase_config import get_supabase_manager, is_supabase_available
    SUPABASE_AVAILABLE = is_supabase_available()
    if SUPABASE_AVAILABLE:
        print("Supabase integration available")
    else:
        print("Supabase not available, using fallback storage")
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase config not found, using fallback storage")

def resolve_supabase_user_id(user_id):
    """Map frontend default_user to the Supabase demo user ID."""
    if user_id == 'default_user':
        from supabase_config import DEMO_USER_ID
        return DEMO_USER_ID
    return user_id

def prepare_profile_updates(data):
    """Flatten nested preferences for Supabase profile updates."""
    updates = {k: v for k, v in data.items() if k not in ('user_id', 'item', 'item_id', 'query', 'type', 'details', 'search_type')}
    if 'preferences' in updates and isinstance(updates['preferences'], dict):
        updates.update(updates.pop('preferences'))
    return updates

def enrich_stats(stats, profile=None, favorites_count=0, searches_count=0, activities_count=0):
    """Add computed fields expected by the profile frontend."""
    if not stats:
        return stats
    enriched = dict(stats)
    enriched.setdefault('total_favorites', favorites_count)
    enriched.setdefault('total_searches', searches_count)
    enriched.setdefault('total_activities', activities_count)
    if profile and profile.get('member_since'):
        try:
            member_since = profile['member_since']
            if 'T' in str(member_since):
                member_date = datetime.fromisoformat(str(member_since).replace('Z', '+00:00'))
                member_date = member_date.replace(tzinfo=None)
            else:
                member_date = datetime.strptime(str(member_since)[:10], '%Y-%m-%d')
            enriched.setdefault('member_days', (datetime.now() - member_date).days)
        except (ValueError, TypeError):
            enriched.setdefault('member_days', 0)
    else:
        enriched.setdefault('member_days', 0)
    return enriched

def merge_profile_response(profile, preferences):
    """Return profile dict with nested preferences for the frontend."""
    merged = dict(profile)
    if preferences:
        merged['preferences'] = preferences
    return merged

# Fallback in-memory storage (when Supabase is not available)
user_profiles = {
    'default_user': {
        'username': 'SpaceExplorer2025',
        'email': 'user@example.com',
        'location': 'New York, USA',
        'member_since': '2025-01-01',
        'preferences': {
            'theme': 'dark',
            'notifications': True,
            'language': 'en',
            'units': 'metric'
        },
        'stats': {
            'space_objects_explored': 0,
            'events_tracked': 0,
            'ai_questions_asked': 0,
            'pages_visited': 0,
            'last_login': None
        },
        'favorites': [],
        'search_history': [],
        'activity_log': []
    }
}

@app.route('/api/profile')
def get_profile():
    """Get user profile data"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            if user_id == 'default_user':
                # Get demo user data for development
                demo_data = supabase.get_demo_user_data()
                if demo_data['profile']:
                    return jsonify({
                        'success': True,
                        'profile': merge_profile_response(demo_data['profile'], demo_data['preferences']),
                        'stats': enrich_stats(
                            demo_data['stats'],
                            demo_data['profile'],
                            len(demo_data.get('favorites') or []),
                            len(demo_data.get('search_history') or []),
                            len(demo_data.get('activities') or [])
                        ),
                        'preferences': demo_data['preferences']
                    })
            
            # Get real user data
            resolved_id = resolve_supabase_user_id(user_id)
            profile = supabase.get_user_profile(resolved_id)
            if profile:
                stats = supabase.get_user_stats(resolved_id)
                preferences = supabase.get_user_preferences(resolved_id)
                favorites = supabase.get_user_favorites(resolved_id)
                searches = supabase.get_user_search_history(resolved_id)
                activities = supabase.get_user_activities(resolved_id)
                return jsonify({
                    'success': True,
                    'profile': merge_profile_response(profile, preferences),
                    'stats': enrich_stats(stats, profile, len(favorites), len(searches), len(activities)),
                    'preferences': preferences
                })
            else:
                return jsonify({'error': 'User not found'}), 404
        else:
            # Fallback to in-memory storage
            if user_id in user_profiles:
                return jsonify({
                    'success': True,
                    'profile': user_profiles[user_id]
                })
            else:
                return jsonify({'error': 'User not found'}), 404
                
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    """Update user profile information"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            resolved_id = resolve_supabase_user_id(user_id)
            if user_id == 'default_user':
                # Ensure demo user exists
                supabase.get_demo_user_data()

            updates = prepare_profile_updates(data)
            success = supabase.update_user_profile(resolved_id, updates)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Profile updated successfully'
                })
            else:
                return jsonify({'error': 'Failed to update profile'}), 500
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            # Update profile fields
            if 'username' in data:
                user_profiles[user_id]['username'] = data['username']
            if 'email' in data:
                user_profiles[user_id]['email'] = data['email']
            if 'location' in data:
                user_profiles[user_id]['location'] = data['location']
            if 'preferences' in data:
                user_profiles[user_id]['preferences'].update(data['preferences'])
                
            return jsonify({
                'success': True,
                'message': 'Profile updated successfully',
                'profile': user_profiles[user_id]
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

@app.route('/api/profile/stats')
def get_profile_stats():
    """Get user statistics and activity data"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            if user_id == 'default_user':
                # Get demo user stats
                demo_data = supabase.get_demo_user_data()
                if demo_data['stats']:
                    return jsonify({
                        'success': True,
                        'stats': enrich_stats(
                            demo_data['stats'],
                            demo_data['profile'],
                            len(demo_data.get('favorites') or []),
                            len(demo_data.get('search_history') or []),
                            len(demo_data.get('activities') or [])
                        )
                    })
            
            # Get real user stats
            resolved_id = resolve_supabase_user_id(user_id)
            profile = supabase.get_user_profile(resolved_id)
            stats = supabase.get_user_stats(resolved_id)
            if stats:
                favorites = supabase.get_user_favorites(resolved_id)
                searches = supabase.get_user_search_history(resolved_id)
                activities = supabase.get_user_activities(resolved_id)
                return jsonify({
                    'success': True,
                    'stats': enrich_stats(stats, profile, len(favorites), len(searches), len(activities))
                })
            else:
                return jsonify({'error': 'User not found'}), 404
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            profile = user_profiles[user_id]
            
            # Calculate additional stats
            total_favorites = len(profile['favorites'])
            total_searches = len(profile['search_history'])
            total_activities = len(profile['activity_log'])
            
            stats = {
                **profile['stats'],
                'total_favorites': total_favorites,
                'total_searches': total_searches,
                'total_activities': total_activities,
                'member_days': (datetime.now() - datetime.strptime(profile['member_since'], '%Y-%m-%d')).days
            }
            
            return jsonify({
                'success': True,
                'stats': stats
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@app.route('/api/profile/favorites')
def get_favorites():
    """Get user's favorite items"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            if user_id == 'default_user':
                # Get demo user favorites
                demo_data = supabase.get_demo_user_data()
                if demo_data['favorites'] is not None:
                    return jsonify({
                        'success': True,
                        'favorites': demo_data['favorites']
                    })
            
            # Get real user favorites
            favorites = supabase.get_user_favorites(user_id)
            return jsonify({
                'success': True,
                'favorites': favorites
            })
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            return jsonify({
                'success': True,
                'favorites': user_profiles[user_id]['favorites']
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to get favorites: {str(e)}'}), 500

@app.route('/api/profile/favorites/add', methods=['POST'])
def add_favorite():
    """Add item to user's favorites"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        item = data.get('item')
        
        if not item:
            return jsonify({'error': 'Item data is required'}), 400
            
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            resolved_id = resolve_supabase_user_id(user_id)
            if user_id == 'default_user':
                supabase.get_demo_user_data()

            success = supabase.add_favorite(
                resolved_id,
                item.get('title', 'Untitled'),
                item.get('type', 'space_object'),
                item.get('description'),
                item.get('id'),
                item.get('url')
            )
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Item added to favorites'
                })
            else:
                return jsonify({'error': 'Failed to add favorite'}), 500
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            # Check if item already exists
            existing_items = [f['id'] for f in user_profiles[user_id]['favorites']]
            if item.get('id') in existing_items:
                return jsonify({'error': 'Item already in favorites'}), 400
                
            # Add timestamp
            item['added_at'] = datetime.now().isoformat()
            user_profiles[user_id]['favorites'].append(item)
            
            return jsonify({
                'success': True,
                'message': 'Item added to favorites',
                'favorites_count': len(user_profiles[user_id]['favorites'])
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to add favorite: {str(e)}'}), 500

@app.route('/api/profile/favorites/remove', methods=['POST'])
def remove_favorite():
    """Remove item from user's favorites"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        item_id = data.get('item_id')
        
        if not item_id:
            return jsonify({'error': 'Item ID is required'}), 400
            
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            resolved_id = resolve_supabase_user_id(user_id)
            success = supabase.remove_favorite(resolved_id, item_id)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Item removed from favorites'
                })
            else:
                return jsonify({'error': 'Failed to remove favorite'}), 500
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            # Remove item
            user_profiles[user_id]['favorites'] = [
                f for f in user_profiles[user_id]['favorites'] 
                if f.get('id') != item_id
            ]
            
            return jsonify({
                'success': True,
                'message': 'Item removed from favorites',
                'favorites_count': len(user_profiles[user_id]['favorites'])
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to remove favorite: {str(e)}'}), 500

@app.route('/api/profile/activity')
def get_activity():
    """Get user's activity log"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        limit = request.args.get('limit', 50, type=int)
        activity_type = request.args.get('type', 'all')
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            if user_id == 'default_user':
                # Get demo user activities
                demo_data = supabase.get_demo_user_data()
                if demo_data['activities'] is not None:
                    activities = demo_data['activities'][:limit]
                    return jsonify({
                        'success': True,
                        'activities': activities,
                        'total_count': len(demo_data['activities'])
                    })
            
            # Get real user activities
            activities = supabase.get_user_activities(user_id, limit, activity_type)
            return jsonify({
                'success': True,
                'activities': activities,
                'total_count': len(activities)
            })
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            activities = user_profiles[user_id]['activity_log'][-limit:]
            
            return jsonify({
                'success': True,
                'activities': activities,
                'total_count': len(user_profiles[user_id]['activity_log'])
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to get activity: {str(e)}'}), 500

@app.route('/api/profile/activity/log', methods=['POST'])
def log_activity():
    """Log a new user activity"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        activity_type = data.get('type')
        details = data.get('details', {})
        
        if not activity_type:
            return jsonify({'error': 'Activity type is required'}), 400
            
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            resolved_id = resolve_supabase_user_id(user_id)
            if user_id == 'default_user':
                supabase.get_demo_user_data()
            success = supabase.log_activity(resolved_id, activity_type, details)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Activity logged successfully'
                })
            else:
                return jsonify({'error': 'Failed to log activity'}), 500
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            # Create activity entry
            activity = {
                'id': f"act_{len(user_profiles[user_id]['activity_log']) + 1}",
                'type': activity_type,
                'details': details,
                'timestamp': datetime.now().isoformat()
            }
            
            user_profiles[user_id]['activity_log'].append(activity)
            
            # Update stats based on activity type
            if activity_type == 'page_visit':
                user_profiles[user_id]['stats']['pages_visited'] += 1
            elif activity_type == 'ai_search':
                user_profiles[user_id]['stats']['ai_questions_asked'] += 1
            elif activity_type == 'event_view':
                user_profiles[user_id]['stats']['events_tracked'] += 1
            elif activity_type == 'object_explore':
                user_profiles[user_id]['stats']['space_objects_explored'] += 1
                
            return jsonify({
                'success': True,
                'message': 'Activity logged successfully'
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to log activity: {str(e)}'}), 500

@app.route('/api/profile/search-history')
def get_search_history():
    """Get user's search history"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        limit = request.args.get('limit', 20, type=int)
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            if user_id == 'default_user':
                # Get demo user search history
                demo_data = supabase.get_demo_user_data()
                if demo_data['search_history'] is not None:
                    searches = demo_data['search_history'][:limit]
                    return jsonify({
                        'success': True,
                        'searches': searches,
                        'total_count': len(demo_data['search_history'])
                    })
            
            # Get real user search history
            searches = supabase.get_user_search_history(user_id, limit)
            return jsonify({
                'success': True,
                'searches': searches,
                'total_count': len(searches)
            })
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            searches = user_profiles[user_id]['search_history'][-limit:]
            
            return jsonify({
                'success': True,
                'searches': searches,
                'total_count': len(user_profiles[user_id]['search_history'])
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to get search history: {str(e)}'}), 500

@app.route('/api/profile/search-history/add', methods=['POST'])
def add_search_history():
    """Add search query to user's history"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        query = data.get('query')
        search_type = data.get('search_type', 'general')
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            resolved_id = resolve_supabase_user_id(user_id)
            if user_id == 'default_user':
                supabase.get_demo_user_data()
            success = supabase.add_search_history(resolved_id, query, search_type)
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Search added to history'
                })
            else:
                return jsonify({'error': 'Failed to add search history'}), 500
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            # Create search entry
            search_entry = {
                'id': f"search_{len(user_profiles[user_id]['search_history']) + 1}",
                'query': query,
                'search_type': search_type,
                'timestamp': datetime.now().isoformat()
            }
            
            user_profiles[user_id]['search_history'].append(search_entry)
            
            return jsonify({
                'success': True,
                'message': 'Search added to history'
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to add search: {str(e)}'}), 500

@app.route('/api/profile/achievements')
def get_achievements():
    """Get user's achievements and badges"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        if SUPABASE_AVAILABLE:
            # Use Supabase
            supabase = get_supabase_manager()
            if user_id == 'default_user':
                # Get demo user achievements
                demo_data = supabase.get_demo_user_data()
                if demo_data['achievements'] is not None:
                    return jsonify({
                        'success': True,
                        'achievements': demo_data['achievements'],
                        'total_achievements': len(demo_data['achievements'])
                    })
            
            # Get real user achievements
            achievements = supabase.get_user_achievements(user_id)
            return jsonify({
                'success': True,
                'achievements': achievements,
                'total_achievements': len(achievements)
            })
        else:
            # Fallback to in-memory storage
            if user_id not in user_profiles:
                return jsonify({'error': 'User not found'}), 404
                
            profile = user_profiles[user_id]
            stats = profile['stats']
            
            # Calculate achievements based on stats
            achievements = []
            
            if stats['space_objects_explored'] >= 10:
                achievements.append({
                    'id': 'explorer_bronze',
                    'name': 'Bronze Explorer',
                    'description': 'Explored 10+ space objects',
                    'icon': 'fas fa-rocket',
                    'unlocked_at': datetime.now().isoformat()
                })
            
            if stats['ai_questions_asked'] >= 25:
                achievements.append({
                    'id': 'curious_mind',
                    'name': 'Curious Mind',
                    'description': 'Asked 25+ AI questions',
                    'icon': 'fas fa-brain',
                    'unlocked_at': datetime.now().isoformat()
                })
            
            if stats['events_tracked'] >= 15:
                achievements.append({
                    'id': 'event_tracker',
                    'name': 'Event Tracker',
                    'description': 'Tracked 15+ astronomical events',
                    'icon': 'fas fa-calendar-star',
                    'unlocked_at': datetime.now().isoformat()
                })
            
            if len(profile['favorites']) >= 20:
                achievements.append({
                    'id': 'collector',
                    'name': 'Space Collector',
                    'description': 'Saved 20+ favorite items',
                    'icon': 'fas fa-heart',
                    'unlocked_at': datetime.now().isoformat()
                })
                
            return jsonify({
                'success': True,
                'achievements': achievements,
                'total_achievements': len(achievements)
            })
            
    except Exception as e:
        return jsonify({'error': f'Failed to get achievements: {str(e)}'}), 500

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        if GEMINI_AVAILABLE:
            print(
                f"AI Search ready - live Gemini model: {GEMINI_ACTIVE_MODEL.replace('models/', '')}",
                flush=True,
            )
        else:
            print(
                "AI Search will use fallback answers — set GEMINI_API_KEY in .env and restart",
                flush=True,
            )
        threading.Thread(target=prefetch_todays_apod, daemon=True).start()
        refill_random_apod_pool(RANDOM_POOL_TARGET)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
