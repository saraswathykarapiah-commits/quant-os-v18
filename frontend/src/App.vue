<template>
  <div class="quant-os">
    <div class="glow-bg"></div>

    <aside class="sidebar glass-panel">
      <div class="brand-area">
        <div class="logo-icon">💠</div>
        <div class="app-name">短线 <span class="highlight">实战</span> V18</div>
      </div>
      <div class="control-panel">
        <button class="cyber-btn" @click="scanMarket" :disabled="loadingStocks">
          <span v-if="loadingStocks" class="spin">⟳</span>
          <span v-else>🚀 扫描全市场</span>
        </button>
      </div>
      <div class="stock-list-wrapper custom-scroll">
        <div class="list-header">主力优选池</div>
        <div v-if="stocks.length === 0 && !loadingStocks" class="empty-list">请点击上方按钮扫描</div>
        <div 
          v-for="(stock, index) in stocks" 
          :key="stock.code"
          class="ticker-card"
          :class="{ 'active': currentStock?.code === stock.code, 'gold-card': index === 0 }"
          @click="handleStockClick(stock)"
        >
          <div class="ticker-row">
            <span class="ticker-name">{{ stock.name }}</span>
            <span class="ticker-price mono" :class="getColor(stock.change)">{{ stock.price }}</span>
          </div>
          <div class="ticker-row sub">
            <span class="ticker-code mono">{{ stock.code }}</span>
            <span class="ticker-change mono" :class="getColor(stock.change)">
              {{ stock.change > 0 ? '+' : ''}}{{ stock.change }}%
            </span>
          </div>
          <div class="ticker-tags">
            <span v-if="index === 0" class="tag gold">👑 金股</span>
            <span v-else-if="stock.tags.includes('🔥主力扫货')" class="tag hot">🔥 扫货</span>
            <span v-if="stock.tags.includes('MACD金叉')" class="tag trend">📈 金叉</span>
          </div>
        </div>
      </div>
    </aside>

    <section class="market-center">
      <div class="market-dash glass-panel">
        <div class="dash-title">📊 市场全景 (上证)</div>
        <div class="index-row">
          <div class="index-main">
            <div class="idx-val mono" :class="getColor(marketInfo.index.change)">
              {{ marketInfo.index.price }}
            </div>
            <div class="idx-change mono" :class="getColor(marketInfo.index.change)">
              {{ marketInfo.index.change }}%
            </div>
          </div>
          <div class="breadth-chart">
            <div class="breadth-bar">
              <div class="up-bar" :style="{flex: marketInfo.index.up || 1}">涨 {{ marketInfo.index.up }}</div>
              <div class="down-bar" :style="{flex: marketInfo.index.down || 1}">跌 {{ marketInfo.index.down }}</div>
            </div>
            <div class="market-mood">情绪：<span class="mood-tag">{{ marketInfo.index.mood }}</span></div>
          </div>
        </div>
      </div>

      <div class="sector-panel glass-panel">
        <div class="panel-head">🔥 热门板块</div>
        <div class="sector-list custom-scroll">
          <div v-for="(sec, i) in marketInfo.hot_sectors" :key="i" class="sector-row">
            <div class="sec-info"><div class="sec-name">{{ sec.name }}</div></div>
            <div class="sec-change mono text-red">+{{ sec.change }}%</div>
          </div>
        </div>
      </div>

      <div class="sector-panel glass-panel">
        <div class="panel-head">💰 资金流向 (亿)</div>
        <div class="sector-list custom-scroll">
          <div v-for="(sec, i) in marketInfo.flow_sectors" :key="i" class="sector-row">
            <div class="sec-name">{{ sec.name }}</div>
            <div class="sec-flow mono text-red">+{{ sec.inflow }}</div>
          </div>
        </div>
      </div>
    </section>

    <main class="detail-deck">
      <div v-if="!currentStock && starStock" class="star-view glass-panel">
        <div class="star-header">
          <div class="star-icon">🌟</div>
          <div class="star-title">明日金股推荐</div>
          <div class="star-name">{{ starStock.name }} <span class="mono">{{ starStock.code }}</span></div>
        </div>
        <div class="star-body custom-scroll">
          <div class="tech-dashboard">
            <div class="tech-item">
              <div class="ti-label">MACD</div>
              <div class="ti-val" :class="(starStock.tech?.macd || 0) > 0 ? 'text-red' : 'text-green'">
                {{ starStock.tech?.macd || '-' }}
              </div>
              <div class="ti-sub">{{ starStock.tech?.macd_signal || '-' }}</div>
            </div>
            <div class="tech-item">
              <div class="ti-label">RSI (6)</div>
              <div class="ti-val text-blue">{{ starStock.tech?.rsi || '-' }}</div>
              <div class="ti-sub">{{ starStock.tech?.rsi_signal || '-' }}</div>
            </div>
            <div class="tech-item">
              <div class="ti-label">主力净流</div>
              <div class="ti-val text-red">{{ starStock.net_inflow }}万</div>
            </div>
          </div>
          <div class="ai-report-box">
             <div v-if="starReport" class="ai-text markdown-body">{{ starReport }}</div>
             <div v-else class="ai-placeholder">
               该股综合评分第一。<br>点击下方生成《决胜研报》。
             </div>
          </div>
        </div>
        <div class="star-footer">
          <button class="gold-btn" @click="generateStarReport" :disabled="analyzing">
            {{ analyzing ? '研报生成中(约30s)...' : '⚡️ 生成决胜研报' }}
          </button>
        </div>
      </div>

      <div v-else-if="currentStock" class="stock-detail">
        <div class="stock-header glass-panel">
          <div class="sh-top">
            <span class="sh-name">{{ currentStock.name }}</span>
            <span class="sh-code mono">{{ currentStock.code }}</span>
            <button class="close-btn" @click="currentStock = null">✕</button>
          </div>
          <div class="sh-data">
            <div class="sh-price mono" :class="getColor(currentStock.change)">{{ currentStock.price }}</div>
            <div class="sh-change mono" :class="getColor(currentStock.change)">{{ currentStock.change }}%</div>
          </div>
          <div class="tech-row">
             <span class="tech-badge">MA5: {{ currentStock.tech?.ma5 || '-' }}</span>
             <span class="tech-badge">MACD: {{ currentStock.tech?.macd || '-' }}</span>
             <span class="tech-badge">RSI: {{ currentStock.tech?.rsi || '-' }}</span>
          </div>
        </div>

        <div class="ai-box glass-panel">
          <div class="ai-head">
            <div class="ai-title">AI 策略分析</div>
            <button class="ai-btn" @click="triggerAI" :disabled="analyzing">{{ analyzing ? '...' : '开始分析' }}</button>
          </div>
          <div class="ai-body custom-scroll">
            <div v-if="aiCache[currentStock.code]" class="ai-text markdown-body">{{ aiCache[currentStock.code] }}</div>
            <div v-else class="ai-placeholder">点击右上角按钮进行分析...</div>
          </div>
        </div>
      </div>

      <div v-else class="empty-deck glass-panel">
        <div class="icon">🎯</div>
        <p>数据待加载</p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const stocks = ref([])
const marketInfo = ref({ index: { price: "0.00", change: 0, up: 1, down: 1, mood: "加载中" }, hot_sectors: [], flow_sectors: [] })
const currentStock = ref(null)
const loadingStocks = ref(false)
const analyzing = ref(false)
const aiCache = ref({})
const starReport = ref('')
const API = 'http://localhost:5001/api'
const api = axios.create({ timeout: 60000 }) 

const starStock = computed(() => stocks.value.length > 0 ? stocks.value[0] : null)

const fetchMarket = async () => {
  try {
    const res = await api.get(`${API}/market_overview`)
    if(res.data.code === 200) marketInfo.value = res.data.data
  } catch(e) {}
}

const scanMarket = async () => {
  loadingStocks.value = true
  stocks.value = []
  starReport.value = ''
  try {
    const res = await api.get(`${API}/smart_pick`)
    if(res.data.code === 200) stocks.value = res.data.data
  } catch(e) { ElMessage.error("扫描超时") }
  finally { loadingStocks.value = false }
}

const handleStockClick = (stock) => { currentStock.value = stock }
const triggerAI = async () => {
  analyzing.value = true
  try {
    const res = await api.post(`${API}/analyze`, currentStock.value)
    if (res.data.code === 200) aiCache.value[currentStock.value.code] = res.data.data
  } catch(e) { 
    ElMessage.error("分析失败") 
    aiCache.value[currentStock.value.code] = "AI 服务繁忙，请稍后再试。"
  } finally { analyzing.value = false }
}
const generateStarReport = async () => {
  if (!starStock.value) return
  analyzing.value = true
  try {
    const res = await api.post(`${API}/analyze_star`, starStock.value)
    if (res.data.code === 200) starReport.value = res.data.data
  } catch(e) { 
    ElMessage.error("分析失败") 
    starReport.value = "AI 服务繁忙，请检查 API Key 或网络连接。"
  } finally { analyzing.value = false }
}
const getColor = (v) => parseFloat(v) >= 0 ? 'text-red' : 'text-green'

onMounted(() => fetchMarket())
</script>

<style>
/* CSS 保持不变，请确保包含之前的 CSS 代码，否则界面会乱 */
:root {
  --bg-dark: #0f1115;
  --bg-panel: #161b22;
  --text-main: #e6edf3;
  --text-sub: #8b949e;
  --neon-red: #ff4d4f;
  --neon-green: #2ecc71;
  --accent: #2f81f7;
  --gold: #ffd700;
  --border: 1px solid rgba(255,255,255,0.1);
  --glass: rgba(22, 27, 34, 0.95);
  --font-mono: "SF Mono", "Consolas", monospace;
}
body { margin: 0; background: var(--bg-dark); color: var(--text-main); font-family: -apple-system, sans-serif; overflow: hidden; }
.quant-os { display: flex; height: 100vh; width: 100vw; gap: 12px; padding: 12px; box-sizing: border-box; background: radial-gradient(circle at top left, #1a202c 0%, #0d1117 100%); }
.glass-panel { background: var(--glass); backdrop-filter: blur(12px); border: var(--border); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); display: flex; flex-direction: column; }
.mono { font-family: var(--font-mono); }
.text-red { color: var(--neon-red); } .text-green { color: var(--neon-green); } .text-blue { color: var(--accent); }

/* Sidebar */
.sidebar { width: 280px; }
.brand-area { padding: 16px; font-weight: 800; border-bottom: var(--border); display: flex; gap: 8px; }
.control-panel { padding: 12px; }
.cyber-btn { width: 100%; background: var(--accent); color: white; border: none; padding: 10px; font-weight: bold; cursor: pointer; border-radius: 4px; }
.stock-list-wrapper { flex: 1; overflow-y: auto; padding: 8px; }
.list-header { font-size: 10px; color: var(--text-sub); margin-bottom: 8px; }
.ticker-card { background: rgba(255,255,255,0.03); padding: 10px; margin-bottom: 6px; border-radius: 4px; cursor: pointer; border: 1px solid transparent; }
.ticker-card.active { border-color: var(--accent); background: rgba(47, 129, 247, 0.1); }
.gold-card { border: 1px solid rgba(255, 215, 0, 0.3); background: linear-gradient(45deg, rgba(255,215,0,0.05), transparent); }
.ticker-row { display: flex; justify-content: space-between; }
.ticker-name { font-weight: bold; font-size: 13px; }
.tag { font-size: 9px; padding: 2px 4px; border-radius: 2px; margin-top: 4px; display: inline-block; margin-right: 4px; }
.tag.gold { background: var(--gold); color: black; font-weight: bold; }
.tag.hot { background: rgba(255, 77, 79, 0.2); color: var(--neon-red); }
.tag.normal { background: rgba(47, 129, 247, 0.2); color: var(--accent); }
.tag.trend { background: rgba(47, 129, 247, 0.1); border: 1px solid var(--accent); color: var(--accent); }

/* Market Center */
.market-center { flex: 1; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.market-dash, .sector-panel { padding: 16px; min-height: 150px; flex: 1; }
.dash-title, .panel-head { font-size: 11px; color: var(--text-sub); font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px; }
.index-row { display: flex; justify-content: space-between; align-items: center; }
.idx-val { font-size: 28px; font-weight: bold; }
.breadth-chart { flex: 1; margin-left: 20px; }
.breadth-bar { display: flex; height: 10px; background: #333; margin-bottom: 4px; border-radius: 5px; overflow: hidden; }
.up-bar { background: var(--neon-red); color: black; font-size: 8px; display: flex; align-items: center; justify-content: center; }
.down-bar { background: var(--neon-green); color: black; font-size: 8px; display: flex; align-items: center; justify-content: center; }
.sector-list { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 6px; }
.sector-row { display: flex; justify-content: space-between; font-size: 12px; background: rgba(255,255,255,0.02); padding: 6px; border-radius: 4px; }
.sec-bar-box { flex: 1; height: 4px; background: #222; margin: 0 10px; border-radius: 2px; align-self: center; }
.sec-bar { height: 100%; background: linear-gradient(90deg, #ff4d4f, #ff7875); }

/* Detail Deck */
.detail-deck { width: 340px; }
.stock-detail { height: 100%; display: flex; flex-direction: column; gap: 12px; }
.stock-header { padding: 20px; }
.sh-top { display: flex; justify-content: space-between; }
.sh-name { font-size: 20px; font-weight: bold; }
.close-btn { background: none; border: none; color: #666; cursor: pointer; }
.sh-price { font-size: 28px; font-weight: bold; margin-top: 5px; }
.tech-row { margin-top: 10px; display: flex; gap: 6px; }
.tech-badge { font-size: 10px; background: rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px; color: var(--text-sub); }

.star-view { height: 100%; display: flex; flex-direction: column; border: 1px solid var(--gold); box-shadow: 0 0 20px rgba(255, 215, 0, 0.1); }
.star-header { background: linear-gradient(to right, rgba(255,215,0,0.1), transparent); padding: 20px; text-align: center; }
.star-icon { font-size: 40px; margin-bottom: 10px; }
.star-title { color: var(--gold); font-weight: bold; letter-spacing: 2px; margin-bottom: 5px; }
.star-name { font-size: 24px; font-weight: bold; }
.star-body { flex: 1; padding: 20px; overflow-y: auto; }

.tech-dashboard { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 20px; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; }
.tech-item { text-align: center; }
.ti-label { font-size: 10px; color: var(--text-sub); }
.ti-val { font-size: 16px; font-weight: bold; }
.ti-sub { font-size: 9px; color: var(--text-sub); margin-top: 2px; }

.gold-btn { width: 100%; background: var(--gold); color: black; border: none; padding: 12px; font-weight: bold; cursor: pointer; margin-top: 10px; }
.gold-btn:disabled { opacity: 0.6; cursor: wait; }

.ai-box { flex: 1; display: flex; flex-direction: column; padding: 16px; }
.ai-head { display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px dashed #333; padding-bottom: 8px; }
.ai-btn { background: var(--accent); color: white; border: none; padding: 4px 10px; border-radius: 2px; cursor: pointer; }
.ai-body { flex: 1; overflow-y: auto; font-size: 12px; line-height: 1.6; }

.custom-scroll::-webkit-scrollbar { width: 4px; }
.custom-scroll::-webkit-scrollbar-thumb { background: #333; border-radius: 2px; }
.empty-deck { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: var(--text-sub); }
.icon { font-size: 40px; }
</style>