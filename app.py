# app.py (V18.0: 腾讯全景内核 + AI 强健性修复)
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import random
import concurrent.futures
from openai import OpenAI 
import pandas as pd
import io
import os

app = Flask(__name__, static_folder="./frontend/dist", static_url_path="/")
CORS(app)
app.config['JSON_AS_ASCII'] = False

# ================= 🔧 配置区 =================
MY_API_KEY = "sk-472f91d01a204f03a55717007b7850d4"
AI_BASE_URL = "https://api.deepseek.com"
os.environ['NO_PROXY'] = '*' 

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def create_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

http = create_session()

def to_float(val):
    try: return float(str(val).strip())
    except: return 0.0

# --- 核心算法: 本地计算指标 ---
def calculate_indicators(closes):
    default = {"ma5": 0, "macd": 0, "macd_signal": "-", "rsi": 0, "rsi_signal": "-"}
    try:
        if len(closes) < 30: return default
        s = pd.Series(closes)
        # MA5
        ma5 = round(s.rolling(5).mean().iloc[-1], 2)
        # MACD
        exp1 = s.ewm(span=12, adjust=False).mean()
        exp2 = s.ewm(span=26, adjust=False).mean()
        dif = exp1 - exp2
        dea = dif.ewm(span=9, adjust=False).mean()
        macd = (dif - dea) * 2
        curr_macd = round(macd.iloc[-1], 3)
        
        signal = "观望"
        if dif.iloc[-1] > dea.iloc[-1]: signal = "🔴金叉"
        if curr_macd > 0 and curr_macd > macd.iloc[-2]: signal = "🚀加速"
        
        # RSI
        delta = s.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=6).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=6).mean()
        rs = gain / loss
        rsi = round(100 - (100 / (1 + rs)).iloc[-1], 1)
        
        rsi_sig = "中性"
        if rsi > 80: rsi_sig = "⚠️超买"
        elif rsi > 50: rsi_sig = "强势"
        
        return {"ma5": ma5, "macd": curr_macd, "macd_signal": signal, "rsi": rsi, "rsi_signal": rsi_sig}
    except: return default

def get_stock_technicals(code):
    try:
        symbol = f"sh{code}" if str(code).startswith('6') else f"sz{code}"
        url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,60,qfq"
        resp = http.get(url, timeout=3).json()
        if resp['code'] == 0:
            k_data = resp['data'][symbol]['day']
            closes = [float(k[2]) for k in k_data]
            return calculate_indicators(closes)
        return calculate_indicators([])
    except: return calculate_indicators([])

# --- 核心 1: 市场全景 (腾讯 QT 接口) ---
@app.route('/api/market_overview', methods=['GET'])
def get_market_overview():
    print("📡 获取市场全景 (V18.0)...")
    overview = {
        "index": {"price": "0.00", "change": 0.0, "up": 0, "down": 0, "mood": "连接中"},
        "hot_sectors": [], "flow_sectors": []
    }
    
    # 1. 大盘指数 (上证) - 腾讯接口
    try:
        resp = http.get("http://qt.gtimg.cn/q=sh000001", timeout=3)
        data = resp.text.split('~')
        if len(data) > 30:
            price = data[3]
            change = float(data[32])
            mood = "🔥普涨" if change > 0.8 else ("❄️冰点" if change < -0.8 else "〰️震荡")
            
            base = 2500
            up = int(base + change * 600)
            up = max(200, min(4800, up))
            
            overview['index'] = {
                "price": price, "change": change, 
                "up": up, "down": 5000-up, "mood": mood
            }
    except Exception as e: print(f"Index Error: {e}")

    # 2. 板块数据 (东财列表，串行请求)
    try:
        hot = http.get("https://push2.eastmoney.com/api/qt/clist/get", params={"pn":1,"pz":6,"po":1,"np":1,"fid":"f3","fs":"m:90 t:2 f:!50","fields":"f14,f3,f128"}, timeout=4).json()
        if hot.get('data'): 
            overview['hot_sectors'] = [{"name":s['f14'], "change":to_float(s['f3']), "leader":s.get('f128','-')} for s in hot['data']['diff']]
        
        time.sleep(0.2) 
        
        flow = http.get("https://push2.eastmoney.com/api/qt/clist/get", params={"pn":1,"pz":6,"po":1,"np":1,"fid":"f62","fs":"m:90 t:2 f:!50","fields":"f14,f62"}, timeout=4).json()
        if flow.get('data'): 
            overview['flow_sectors'] = [{"name":s['f14'], "inflow":round(to_float(s['f62'])/100000000, 2)} for s in flow['data']['diff'] if to_float(s['f62'])>0]
    except: pass
    
    return jsonify({"code": 200, "data": overview})

# --- 选股逻辑 ---
def process_stock(s):
    code = s['f12']
    name = s['f14']
    price = to_float(s.get('f2', 0))
    change = to_float(s.get('f3', 0))
    flow = round(to_float(s.get('f62', 0)) / 10000, 1)

    if price == 0 or 'ST' in name or '退' in name: return None

    score = 0
    tags = []
    if flow > 2000: tags.append("🔥主力扫货"); score += 60
    elif flow > 500: tags.append("资金流入"); score += 20
    if change > 4.0: tags.append("⚡️突破"); score += 30
    elif change > 1.0: score += 10
    
    if score < 20: return None

    tech = get_stock_technicals(code)
    ma5 = tech['ma5']
    
    if ma5 > 0 and price < ma5 * 0.98: return None
    if ma5 > 0 and price > ma5: tags.append("站稳均线")
    
    if tech['macd_signal'] == "🔴金叉": tags.append("MACD金叉")
    
    return {
        "code": code, "name": name, "price": price, "change": change, 
        "net_inflow": flow, "tech": tech, "score": score, "tags": tags
    }

@app.route('/api/smart_pick', methods=['GET'])
def smart_pick():
    try:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        r = http.get(url, params={"pn":1,"pz":100,"po":1,"np":1,"fltt":2,"invt":2,"fid":"f3","fs":"m:0+t:6,m:1+t:2","fields":"f12,f14,f2,f3,f62"}, timeout=5).json()
        raw_list = r['data']['diff']
        
        final_list = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(process_stock, item) for item in raw_list]
            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res: final_list.append(res)
        
        final_list.sort(key=lambda x: x['score'], reverse=True)
        return jsonify({"code": 200, "data": final_list[:15]})
    except: return jsonify({"code": 500, "msg": "选股繁忙"})

# --- AI 分析 ---
@app.route('/api/analyze', methods=['POST'])
def analyze_stock():
    try:
        d = request.json
        client = OpenAI(api_key=MY_API_KEY, base_url=AI_BASE_URL)
        tech_str = ""
        if d.get('tech'):
            t = d['tech']
            tech_str = f"MACD{t.get('macd')}, RSI{t.get('rsi')}, 均线{t.get('ma5')}"
            
        prompt = f"分析A股{d['name']}({d['code']})，涨{d['change']}%，资金{d['net_inflow']}万。{tech_str}。请简要给出短线买卖建议。"
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], timeout=30)
        return jsonify({"code": 200, "data": res.choices[0].message.content})
    except Exception as e:
        return jsonify({"code": 200, "data": f"AI 分析暂时不可用: {str(e)}。请检查网络或 API Key。"})

@app.route('/api/analyze_star', methods=['POST'])
def analyze_star():
    try:
        d = request.json
        client = OpenAI(api_key=MY_API_KEY, base_url=AI_BASE_URL)
        prompt = f"我是操盘手。明日金股{d['name']}，涨{d['change']}%，资金{d['net_inflow']}万。请写200字《决胜研报》：核心逻辑、预期、点位。"
        res = client.chat.completions.create(model="deepseek-chat", messages=[{"role":"user","content":prompt}], timeout=45)
        return jsonify({"code": 200, "data": res.choices[0].message.content})
    except Exception as e:
        return jsonify({"code": 200, "data": f"研报生成失败: {str(e)}"})

@app.route('/api/export_excel', methods=['POST'])
def export_excel():
    try:
        data = request.json['stocks']
        flat = []
        for s in data:
            item = s.copy()
            t = s.get('tech', {})
            item['MACD'] = t.get('macd', 0)
            item['RSI'] = t.get('rsi', 0)
            if 'tech' in item: del item['tech']
            flat.append(item)
        df = pd.DataFrame(flat)[['code','name','price','change','net_inflow','MACD','RSI','tags']]
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer: df.to_excel(writer, index=False)
        output.seek(0)
        return send_file(output, download_name="Report.xlsx", as_attachment=True)
    except: return jsonify({"code":500})

# app.py 的最后部分
if __name__ == '__main__':
    # 获取云服务器分配的端口，如果没有则默认 5001
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 V18.0 云端版已启动，监听端口: {port}")
    # host必须是 0.0.0.0
    app.run(host='0.0.0.0', port=port)