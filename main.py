import time, sqlite3, requests, threading, os
from datetime import datetime
from flask import Flask

# --- ⚙️ CONFIGURATION ---
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
MEN_API_URL = "https://www.sheinindia.in/api/category/sverse-5939-37961?pageSize=45&format=json&sort=9&query=%3Anewest%3Agenderfilter%3AMen"
CHECK_DELAY = 30 
DB_FILE = "sheinverse_pro_v5.db"

app = Flask('')
@app.route('/')
def home(): return "Sniper is ACTIVE 🟢"

class SheinLiveMonitor:
    def __init__(self):
        self.setup_db()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        self.status_msg_id = None 

    def setup_db(self):
        conn = sqlite3.connect(DB_FILE)
        conn.execute('CREATE TABLE IF NOT EXISTS products (id TEXT PRIMARY KEY, last_stock_status INTEGER)')
        conn.close()

    def _send_simple_text(self, text):
        """Debug message bhejta hai seedha Telegram par"""
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"})

    def fetch_api(self):
        try:
            print(f"📡 API Request bhej raha hoon... {datetime.now()}")
            resp = self.session.get(MEN_API_URL, timeout=15)
            print(f"🌐 Response Status: {resp.status_code}")
            
            if resp.status_code == 403:
                self._send_simple_text("⚠️ <b>ERROR 403:</b> Shein ne Railway ka IP block kar diya hai! Proxy ki zaroorat hai.")
                return [], 0
            
            data = resp.json()
            products = data.get('products', [])
            return products, len(products)
        except Exception as e:
            print(f"❌ API Error: {e}")
            return [], 0

    def _send_alert(self, item, alert_type="LIVE NOW"):
        caption = f"🔥 <b>{alert_type}!</b>\n\n👕 {item['name']}\n💰 Rs.{item['price']}\n🔗 <a href='{item['url']}'>Shop Now</a>"
        payload = {"chat_id": CHAT_ID, "photo": item['image'], "caption": caption, "parse_mode": "HTML"}
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json=payload)

    def start(self):
        print("✅ Sniper Logic Shuru...")
        self._send_simple_text("🚀 <b>BOT START HO GAYA!</b>\nChecking for items now...")
        
        # Testing ke liye False rakha hai taki turant messages aayein
        first_run = False 
        
        while True:
            prods, total = self.fetch_api()
            print(f"📦 Total items mile: {total}")
            
            conn = sqlite3.connect(DB_FILE)
            for p in prods:
                pid = str(p.get('id') or p.get('goods_id'))
                img = p.get('goods_img') or ""
                price = "Check App"
                
                item_data = {
                    'id': pid, 'name': p.get('name', 'Product'), 'price': price,
                    'url': f"https://www.sheinindia.in/p/{pid}", 
                    'image': f"https:{img}" if img and not img.startswith('http') else img
                }

                row = conn.execute("SELECT id FROM products WHERE id=?", (pid,)).fetchone()
                if row is None:
                    conn.execute("INSERT INTO products (id, last_stock_status) VALUES (?, 1)", (pid,))
                    if not first_run:
                        self._send_alert(item_data)
                        time.sleep(1) # Spam na ho isliye delay
            
            conn.commit()
            conn.close()
            first_run = False 
            print(f"💤 Next scan in {CHECK_DELAY}s...")
            time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    SheinLiveMonitor().start()
