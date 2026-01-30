import time
import sqlite3
import requests
import threading
import os
from datetime import datetime
from flask import Flask

# --- ⚙️ CONFIGURATION (Railway Variables se uthayega) ---
# Railway Dashboard -> Settings -> Variables mein ye dono add karein
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8397695441:AAERO7gATlrWTECQqFGYUdbeAnCfGH6aaXw")
CHAT_ID = os.environ.get("CHAT_ID", "421311524")
MEN_API_URL = "https://www.sheinindia.in/api/category/sverse-5939-37961?pageSize=45&format=json&sort=9&query=%3Anewest%3Agenderfilter%3AMen"

CHECK_DELAY = 30 
DB_FILE = "sheinverse_pro_v5.db"

app = Flask('')
@app.route('/')
def home(): return "Sniper is LIVE 🚀"

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

    def update_status_msg(self, total_count):
        now_dt = datetime.now()
        last_scan = now_dt.strftime('%H:%M:%S')
        next_scan = datetime.fromtimestamp(time.time() + CHECK_DELAY).strftime('%H:%M:%S')
        
        text = (
            f"📊 <b>SHEINVERSE LIVE TRACKER</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>TOTAL LIVE:</b> <code>{total_count}</code>\n"
            f"⏱️ <b>LAST SCAN:</b> <code>{last_scan}</code>\n"
            f"⏭️ <b>NEXT SCAN:</b> <code>{next_scan}</code>\n"
            f"📡 <b>STATUS:</b> 🟢 <b>SNIPER ACTIVE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        try:
            if self.status_msg_id is None:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).json()
                if r.get("ok"): self.status_msg_id = r["result"]["message_id"]
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                requests.post(url, json={"chat_id": CHAT_ID, "message_id": self.status_msg_id, "text": text, "parse_mode": "HTML"})
        except Exception as e:
            print(f"Telegram Status Error: {e}")

    def get_inventory_details(self, goods_id):
        try:
            detail_url = f"https://www.sheinindia.in/api/product/detail?goods_id={goods_id}"
            resp = self.session.get(detail_url, timeout=10)
            if resp.status_code != 200: return "• Error", 0
            
            data = resp.json()
            grid_parts = []
            is_currently_instock = 0
            
            skus = data.get('info', {}).get('mainSaleAttribute', {}).get('skus', []) or \
                   data.get('productIntroData', {}).get('mainSaleAttribute', {}).get('skus', [])
            
            for s in skus:
                size = s.get('attr_value_name', '?')
                qty = s.get('inventory', 0)
                if qty > 0:
                    is_currently_instock = 1
                    badge = "🟢" if qty > 2 else "🟠"
                    grid_parts.append(f"<code>[{size}: {qty} {badge}]</code>")
                else:
                    grid_parts.append(f"<code>[{size}: ❌]</code>")
            
            return " ".join(grid_parts) if grid_parts else "⚠️ OOS", is_currently_instock
        except: return "• Stock Error", 0

    def _send_alert(self, item, inv_grid, alert_type="STOCK ADDED"):
        emoji = "⚡" if "ADDED" in alert_type else "🔄"
        caption = (
            f"{emoji} <b>{alert_type}!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👕 <b>ITEM:</b> {item['name']}\n"
            f"💰 <b>PRICE:</b> <code>Rs.{item['price']}</code>\n"
            f"📏 <b>SIZES:</b>\n{inv_grid}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <a href='{item['url']}'>OPEN SHEIN</a>"
        )
        
        payload = {
            "chat_id": CHAT_ID, "photo": item['image'], "caption": caption, "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": [[{"text": "🛒 BUY NOW", "url": item['url']}]]}
        }
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", json=payload)

    def fetch_api(self):
        try:
            resp = self.session.get(MEN_API_URL, timeout=15)
            if resp.status_code == 403:
                print("❌ ERROR 403: Shein ne Railway IP block kar di hai!")
                return [], 0
            data = resp.json()
            products = data.get('products', [])
            total = data.get('totalResults', len(products))
            return products, total
        except Exception as e:
            print(f"API Fetch Error: {e}")
            return [], 0

    def start(self):
        print("🚀 Sniper is running...")
        # Pehli baar mein alert chahiye toh ise False kar dein, 
        # lekin 100+ message aa sakte hain!
        first_run = True 
        
        while True:
            prods, total_live = self.fetch_api()
            if total_live > 0:
                self.update_status_msg(total_live)
            
            conn = sqlite3.connect(DB_FILE)
            for p in prods:
                pid = str(p.get('id') or p.get('goods_id'))
                img = p.get('goods_img') or p.get('img') or ""
                price = str(p.get('price', {}).get('ext_info', {}).get('sale_price_format', '0')).replace('INR','').replace('Rs.','').strip()
                
                item_data = {
                    'id': pid, 'name': p.get('name'), 'price': price,
                    'url': f"https://www.sheinindia.in/p/{pid}", 
                    'image': f"https:{img}" if not img.startswith('http') else img
                }

                row = conn.execute("SELECT last_stock_status FROM products WHERE id=?", (pid,)).fetchone()
                inv_grid, current_status = self.get_inventory_details(pid)

                if row is None:
                    conn.execute("INSERT INTO products (id, last_stock_status) VALUES (?, ?)", (pid, current_status))
                    if not first_run and current_status == 1:
                        self._send_alert(item_data, inv_grid, "STOCK ADDED")
                else:
                    if row[0] == 0 and current_status == 1:
                        if not first_run: self._send_alert(item_data, inv_grid, "RESTOCKED")
                    conn.execute("UPDATE products SET last_stock_status = ? WHERE id = ?", (current_status, pid))
                
            conn.commit()
            conn.close()
            first_run = False
            time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=port), daemon=True).start()
    SheinLiveMonitor().start()
