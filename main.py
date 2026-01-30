import time
import sqlite3
import requests
import threading
from datetime import datetime
from flask import Flask

# --- ⚙️ CONFIGURATION ---
BOT_TOKEN = "8397695441:AAERO7gATlrWTECQqFGYUdbeAnCfGH6aaXw"
CHAT_ID = "421311524"
MEN_API_URL = "https://www.sheinindia.in/api/category/sverse-5939-37961?pageSize=45&format=json&sort=9&query=%3Anewest%3Agenderfilter%3AMen"

CHECK_DELAY = 30 
DB_FILE = "sheinverse_pro_v5.db"

app = Flask('')
@app.route('/')
def home(): return "Steroids UI Sniper with Compact Grid is ACTIVE."

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
        """Steroids UI with Bold Targets and Next Scan Timing"""
        now_dt = datetime.now()
        last_scan = now_dt.strftime('%H:%M:%S')
        
        # Next Scan Calculation (current time + 30 seconds)
        next_scan_time = time.time() + CHECK_DELAY
        next_scan = datetime.fromtimestamp(next_scan_time).strftime('%H:%M:%S')
        
        # Premium Steroids UI Design
        text = (
            f"📊 <b>SHEINVERSE LIVE TRACKER</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>TARGET:</b> <b><u>MEN'S ONLY</u></b> 💎\n"
            f"📦 <b>TOTAL LIVE:</b> <code>{total_count}</code>\n"
            f"⏱️ <b>LAST SCAN:</b> <code>{last_scan}</code>\n"
            f"⏭️ <b>NEXT SCAN:</b> <code>{next_scan}</code>\n"
            f"📡 <b>STATUS:</b> 🟢 <b>SNIPER ACTIVE</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🚀 <i>Tracking Drops & Restocks...</i>\n"
            f"⚡ <i>Logic: Restock + New Drop Detection</i>"
        )
        
        try:
            if self.status_msg_id is None:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}).json()
                if r.get("ok"): self.status_msg_id = r["result"]["message_id"]
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageText"
                requests.post(url, json={"chat_id": CHAT_ID, "message_id": self.status_msg_id, "text": text, "parse_mode": "HTML"})
        except: pass

    def get_inventory_details(self, goods_id):
        """Fetch stock with Compact Grid and Urgency Badges"""
        try:
            detail_url = f"https://www.sheinindia.in/api/product/detail?goods_id={goods_id}"
            data = self.session.get(detail_url, timeout=10).json()
            grid_parts = []
            is_currently_instock = 0
            
            skus = data.get('info', {}).get('mainSaleAttribute', {}).get('skus', []) or \
                   data.get('productIntroData', {}).get('mainSaleAttribute', {}).get('skus', [])
            
            for s in skus:
                size = s.get('attr_value_name', '?')
                qty = s.get('inventory', 0)
                
                if qty > 0:
                    is_currently_instock = 1
                    # Badges logic
                    badge = "🟢" if qty > 2 else ("🟠" if qty == 2 else "🔴")
                    grid_parts.append(f"<code>[{size}: {qty} {badge}]</code>")
                else:
                    # Replacing OOS with ❌ emoji
                    grid_parts.append(f"<code>[{size}: ❌]</code>")
            
            compact_grid = " ".join(grid_parts)
            return compact_grid if compact_grid else "⚠️ Data Error", is_currently_instock
        except: return "• Stock Loaded", 1

    def _send_alert(self, item, inv_grid, alert_type="STOCK ADDED"):
        """Matching Premium UI Alert with Grid View"""
        emoji = "⚡" if "ADDED" in alert_type else "🔄"
        api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        
        caption = (
            f"{emoji} <b>{alert_type}!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👕 <b>ITEM:</b> {item['name']}\n"
            f"💰 <b>PRICE:</b> <code>Rs.{item['price']}</code>\n"
            f"🆔 <b>ID:</b> <code>{item['id']}</code>\n\n"
            f"📏 <b>SIZES & STOCK:</b>\n{inv_grid}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔗 <a href='{item['url']}'>TAP TO OPEN SHEIN APP</a>\n\n"
            f"✨ <b>Loot it fast! 🫶</b>"
        )
        
        payload = {
            "chat_id": CHAT_ID, 
            "photo": item['image'], 
            "caption": caption, 
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [[{"text": f"🛒 BUY NOW @ Rs.{item['price']}", "url": item['url']}]]
            }
        }
        requests.post(api_url, json=payload, timeout=10)

    def fetch_api(self):
        try:
            resp = self.session.get(MEN_API_URL, timeout=15).json()
            total = resp.get('totalResults', 0)
            return resp.get('products', []), (total if total > 0 else len(resp.get('products', [])))
        except: return [], 0

    def start(self):
        print("🚀 Steroids UI + Compact Grid Sniper Activated...")
        first_run = True
        
        while True:
            prods, total_live = self.fetch_api()
            self.update_status_msg(total_live)
            
            for p in prods:
                pid = str(p.get('id') or p.get('goods_id'))
                img = p.get('goods_img') or p.get('img') or ""
                price = p.get('price', {}).get('ext_info', {}).get('sale_price_format', '0').replace('INR','').replace('Rs.','').strip()
                item_data = {
                    'id': pid, 'name': p.get('name'), 'price': price,
                    'url': f"https://www.sheinindia.in/p/{pid}", 
                    'image': f"https:{img}" if not img.startswith('http') else img
                }

                conn = sqlite3.connect(DB_FILE)
                row = conn.execute("SELECT last_stock_status FROM products WHERE id=?", (pid,)).fetchone()
                
                inv_grid, current_status = self.get_inventory_details(pid)

                if row is None:
                    conn.execute("INSERT INTO products (id, last_stock_status) VALUES (?, ?)", (pid, current_status))
                    conn.commit()
                    if not first_run and current_status == 1:
                        self._send_alert(item_data, inv_grid, "STOCK ADDED")
                        time.sleep(2)
                else:
                    last_status = row[0]
                    if last_status == 0 and current_status == 1:
                        if not first_run:
                            self._send_alert(item_data, inv_grid, "RESTOCKED")
                            time.sleep(2)
                    
                    if last_status != current_status:
                        conn.execute("UPDATE products SET last_stock_status = ? WHERE id = ?", (current_status, pid))
                        conn.commit()
                conn.close()
            
            first_run = False
            time.sleep(CHECK_DELAY)

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()
    SheinLiveMonitor().start()
