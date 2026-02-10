<template>
  <div class="quant-os">
    <div class="mobile-header" v-if="isMobile">
      <div class="brand-area">
        <span class="logo-icon">💠</span> QUANT <span class="highlight">PRO</span>
      </div>
      <div class="connection-status" :class="loadingStocks ? 'blink' : 'online'"></div>
    </div>

    <aside class="sidebar" v-show="!isMobile || activeTab === 'stocks'">
      <div class="panel-title-mobile" v-if="isMobile">主力优选池</div>
      
      <div class="control-panel" v-if="!isMobile">
        <button class="cyber-btn" @click="scanMarket" :disabled="loadingStocks">
          <span v-if="loadingStocks" class="spin">⟳</span>
          <span v-else>🚀 扫描全市场</span>
        </button>
      </div>

      <div class="stock-list-wrapper">
        <div class="list-header" v-if="!isMobile">TOP 15 关注池</div>
        
        <div v-if="stocks.length === 0 && !loadingStocks" class="empty-list">
          <div class="empty-icon">📡</div>
          <p>暂无数据，请点击扫描</p>
        </div>

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

      <button v-if="isMobile && activeTab === 'stocks'" class="mobile-scan-btn" @click="scanMarket" :disabled="loadingStocks">
        {{ loadingStocks ? '扫描中...' : '🚀 开始扫描' }}
      </button>
    </aside>

    <section class="market-center" v-show="!isMobile || activeTab === 'market'">
      <div class="panel-title-mobile" v-if="isMobile">市场全景</div>
      
      <div class="market-dash">
        <div class="dash-title">📊 上证指数</div>
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
              <div class="up-bar" :style="{flex: marketInfo.index.up || 1}"></div>
              <div class="down-bar" :style="{flex: marketInfo.index.down || 1}"></div>
            </div>
            <div class="market-mood">
              涨: {{ marketInfo.index.up }} &nbsp; 跌: {{ marketInfo.index.down }}
              <span class="mood-tag">{{ marketInfo.index.mood }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="sector-panel">
        <div class="panel-head">🔥 热门板块</div>
        <div class="sector-list">
          <div v-for="(sec, i) in marketInfo.hot_sectors" :key="i" class="sector-row">
            <div class="sec-info"><div class="sec-name">{{ sec.name }}</div></div>
            <div class="sec-change mono text-red">+{{ sec.change }}%</div>
          </div>
        </div>
      </div>

      <div class="sector-panel">
        <div class="panel-head">💰 资金流向 (亿)</div>
        <div class="sector-list">
          <div v-for="(sec, i) in marketInfo.flow_sectors" :key="i" class="sector-row">
            <div class="sec-name">{{ sec.name }}</div>
            <div class="sec-flow mono text-red">+{{ sec.inflow }}</div>
          </div>
        </div>
      </div>
    </section>

    <main class="detail-deck" v-show="!isMobile || activeTab === 'analyze'">
      <div class="panel-title-mobile" v-if="isMobile">深度分析</div>

      <div v-if="!currentStock && starStock" class="star-view">
        <div class="star-header">
          <div class="star-icon">🌟</div>
          <div class="star-title">明日金股推荐</div>
          <div class="star-name">{{ starStock.name }} <span class="mono">{{ starStock.code }}</span></div>
        </div>
        <div class="star-body">
          <div class="tech-dashboard">
            <div class="tech-item">
              <div class="ti-label">MACD</div>
              <div class="ti-val" :class="(starStock.tech?.macd || 0) > 0 ? 'text-red' : 'text-green'">
                {{ starStock.tech?.macd || '-' }}
              </div>
            </div>
            <div class="tech-item">
              <div class="ti-label">RSI</div>
              <div class="ti-val text-blue">{{ starStock.tech?.rsi || '-' }}</div>
            </div>
            <div class="tech-item">
              <div class="ti-label">资金</div>
              <div class="ti-val text-red">{{ starStock.net_inflow }}</div>
            </div>
          </div>
          <div class="ai-report-box">
             <div v-if="starReport" class="ai-text markdown-body">{{ starReport }}</div>
             <div v-else class="ai-placeholder">
               该股综合评分第一。<br>点击下方生成 AI 决胜研报。
             </div>
          </div>
        </div>
        <div class="star-footer">
          <button class="gold-btn" @click="generateStarReport" :disabled="analyzing">
            {{ analyzing ? 'AI 深度思考中...' : '⚡️ 生成决胜研报' }}
          </button>
        </div>
      </div>

      <div v-else-if="currentStock" class="stock-detail">
        <div class="stock-header">
          <div class="sh-top">
            <span class="sh-name">{{ currentStock.name }}</span>
            <span class="sh-code mono">{{ currentStock.code }}</span>
            <button class="close-btn" @click="backToGold">✕</button>
          </div>
          <div class="sh-data">
            <div class="sh-price mono" :class="getColor(currentStock.change)">{{ currentStock.price }}</div>
            <div class="sh-change mono" :class="getColor(currentStock.change)">{{ currentStock.change }}%</div>
          </div>
          <div class="tech-row">
             <span class="tech-badge">MA5: {{ currentStock.tech?.ma5 || '-' }}</span>
             <span class="tech-badge">MACD: {{ currentStock.tech?.macd || '-' }}</span>
          </div>
        </div>

        <div class="ai-box">
          <div class="ai-head">
            <div class="ai-title">AI 短线策略</div>
            <button class="ai-btn" @click="triggerAI" :disabled="analyzing">{{ analyzing ? '...' : '分析' }}</button>
          </div>
          <div class="ai-body">
            <div v-if="aiCache[currentStock.code]" class="ai-text markdown-body">{{ aiCache[currentStock.code] }}</div>
            <div v-else class="ai-placeholder">点击右上角分析获取操作建议...</div>
          </div>
        </div>
      </div>

      <div v-else class="empty-deck">
        <div class="icon">🎯</div>
        <p>请先在 [选股] 页点击股票</p>
      </div>
    </main>

    <nav class="mobile-nav" v-if="isMobile">
      <div class="nav-item" :class="{active: activeTab === 'market'}" @click="activeTab = 'market'">
        <span class="nav-icon">📊</span>
        <span class="nav-text">市场</span>
      </div>
      <div class="nav-item" :class="{active: activeTab === 'stocks'}" @click="activeTab = 'stocks'">
        <span class="nav-icon">🚀</span>
        <span class="nav-text">选股</span>
      </div>
      <div class="nav-item" :class="{active: activeTab === 'analyze'}" @click="activeTab = 'analyze'">
        <span class="nav-icon">🧠</span>
        <span class="nav-text">研报</span>
      </div>
    </nav>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

// ==========================================
// 🔴 请把下面这行改成你的 Render 网址！例如：
// const API = 'https://你的项目名.onrender.com/api'
const API = 'https://wo-de-niu-gu.onrender.com/api' 
// ==========================================

// 🔴 关键修复：超时时间改为 120秒，防止 Render 冷启动报错
const api = axios.create({ timeout: 120000 })

const stocks = ref([])
const marketInfo = ref({ index: { price: "0.00", change: 0, up: 1, down: 1, mood: "Init" }, hot_sectors: [], flow_sectors: [] })
const currentStock = ref(null)
const loadingStocks = ref(false)
const analyzing = ref(false)
const aiCache = ref({})
const starReport = ref('')

// 手机端适配逻辑
const isMobile = ref(window.innerWidth < 768)
const activeTab = ref('market') // 默认显示市场

const updateLayout = () => { isMobile.value = window.innerWidth < 768 }
onMounted(() => {
  window.addEventListener('resize', updateLayout)
  fetchMarket()
})
onUnmounted(() => window.removeEventListener('resize', updateLayout))

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
  
  if (isMobile.value) {
     ElMessage.info({
        message: "正在唤醒云服务器，首次扫描约需 1 分钟，请耐心等待...",
        duration: 5000
     })
  }

  try {
    const res = await api.get(`${API}/smart_pick`)
    if(res.data.code === 200) {
      stocks.value = res.data.data
      if(isMobile.value) {
        ElMessage.success("扫描完成")
        activeTab.value = 'stocks' // 扫完留在选股页
      }
    }
  } catch(e) { ElMessage.error("扫描失败，请稍后重试") }
  finally { loadingStocks.value = false }
}

const handleStockClick = (stock) => { 
  currentStock.value = stock
  if(isMobile.value) activeTab.value = 'analyze' 
}

const backToGold = () => { currentStock.value = null }

const triggerAI = async () => {
  analyzing.value = true
  try {
    const res = await api.post(`${API}/analyze`, currentStock.value)
    if (res.data.code === 200) aiCache.value[currentStock.value.code] = res.data.data
  } catch(e) { aiCache.value[currentStock.value.code] = "AI 服务繁忙，请稍后重试。" } 
  finally { analyzing.value = false }
}

const generateStarReport = async () => {
  if (!starStock.value) return
  analyzing.value = true
  try {
    const res = await api.post(`${API}/analyze_star`, starStock.value)
    if (res.data.code === 200) starReport.value = res.data.data
  } catch(e) { starReport.value = "AI 服务繁忙，请稍后重试。" } 
  finally { analyzing.value = false }
}

const getColor = (v) => parseFloat(v) >= 0 ? 'text-red' : 'text-green'
</script>

<style>
/* Quant OS V18 - Mobile Pro Theme 
   适配 iPhone 14 Pro / OLED 屏幕 
*/

:root {
  --bg-dark: #000000;
  --panel-bg: #111111;
  --text-main: #ffffff;
  --text-sub: #86868b;
  --accent: #0A84FF; /* iOS Blue */
  --danger: #FF453A; /* iOS Red */
  --success: #30D158; /* iOS Green */
  --gold: #FFD60A;
  --nav-height: 84px;
}

body {
  margin: 0;
  background: var(--bg-dark);
  color: var(--text-main);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", sans-serif;
  -webkit-tap-highlight-color: transparent;
  overflow: hidden;
}

/* 布局容器：处理安全区 */
.quant-os {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  background: black;
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  box-sizing: border-box;
}

/* 手机端顶部栏 */
.mobile-header {
  height: 44px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  background: rgba(10, 10, 10, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 0.5px solid #222;
  z-index: 50;
  flex-shrink: 0;
}
.brand-area { font-size: 17px; font-weight: 700; }
.highlight { color: var(--accent); }
.connection-status { width: 6px; height: 6px; border-radius: 50%; background: #333; }
.connection-status.online { background: var(--success); box-shadow: 0 0 6px var(--success); }
.connection-status.blink { background: var(--gold); animation: blink 1s infinite; }

/* 核心内容区 */
.sidebar, .market-center, .detail-deck {
  flex: 1;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
  padding: 16px;
  padding-bottom: 100px;
}

/* 电脑端才显示的元素 */
@media (min-width: 768px) {
  .quant-os {
    flex-direction: row;
    padding: 12px;
    gap: 12px;
    background: radial-gradient(circle at top left, #1c1c1e 0%, #000 100%);
  }
  .sidebar, .market-center, .detail-deck {
    height: 100%;
    padding: 12px;
    border-radius: 12px;
    background: rgba(28, 28, 30, 0.6);
    border: 1px solid rgba(255,255,255,0.1);
    backdrop-filter: blur(20px);
  }
  .sidebar { width: 300px; flex: none; }
  .detail-deck { width: 360px; flex: none; }
  .mobile-header, .mobile-nav, .mobile-scan-btn, .panel-title-mobile { display: none !important; }
}

/* 卡片样式 */
.ticker-card, .market-dash, .sector-panel, .star-view, .stock-header, .ai-box {
  background: #1C1C1E;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,0.05);
}

/* 列表项 */
.ticker-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.ticker-name { font-size: 16px; font-weight: 600; }
.ticker-price { font-size: 16px; font-weight: 600; font-family: "SF Mono", monospace; }
.sub { opacity: 0.6; font-size: 13px; }

/* 标签 */
.tag { font-size: 10px; padding: 3px 6px; border-radius: 4px; font-weight: 600; margin-right: 6px; display: inline-block; }
.tag.gold { background: var(--gold); color: black; }
.tag.hot { background: rgba(255, 69, 58, 0.2); color: var(--danger); }
.tag.trend { background: rgba(10, 132, 255, 0.2); color: var(--accent); }

/* 市场全景 */
.idx-val { font-size: 36px; font-weight: 700; letter-spacing: -1px; }
.breadth-bar { height: 6px; border-radius: 3px; background: #333; overflow: hidden; display: flex; margin: 12px 0; }
.up-bar { background: var(--danger); } .down-bar { background: var(--success); }
.market-mood { font-size: 12px; color: var(--text-sub); display: flex; justify-content: space-between; }
.panel-title-mobile { font-size: 22px; font-weight: 800; padding: 10px 0 16px; color: white; }

/* 底部导航 */
.mobile-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  height: var(--nav-height);
  background: rgba(10, 10, 10, 0.9);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 0.5px solid #333;
  display: flex;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 100;
}
.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  height: 50px;
  margin-top: 5px;
}
.nav-item.active { color: var(--accent); }
.nav-icon { font-size: 22px; margin-bottom: 2px; }
.nav-text { font-size: 10px; font-weight: 500; }

/* 悬浮按钮 */
.mobile-scan-btn {
  position: fixed;
  bottom: 100px;
  right: 20px;
  background: var(--accent);
  color: white;
  border: none;
  padding: 14px 24px;
  border-radius: 40px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 4px 20px rgba(10, 132, 255, 0.4);
  z-index: 90;
}
.mobile-scan-btn:disabled { opacity: 0.7; transform: scale(0.98); }

/* 详情页 */
.star-header { text-align: center; padding: 20px; border-bottom: 1px solid #333; margin-bottom: 16px; }
.star-icon { font-size: 48px; margin-bottom: 10px; display: block; }
.star-name { font-size: 24px; font-weight: 800; }
.tech-dashboard { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 20px; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; }
.tech-item { text-align: center; }
.ti-label { font-size: 11px; color: var(--text-sub); }
.ti-val { font-size: 15px; font-weight: 700; margin-top: 4px; }
.gold-btn { width: 100%; background: var(--gold); color: black; border: none; padding: 14px; font-weight: 700; border-radius: 10px; font-size: 16px; }
.ai-text { font-size: 15px; line-height: 1.6; color: #eee; }
.empty-list { text-align: center; padding-top: 60px; color: var(--text-sub); }
.empty-icon { font-size: 40px; margin-bottom: 10px; }

/* 颜色类 */
.text-red { color: var(--danger); }
.text-green { color: var(--success); }
.text-blue { color: var(--accent); }
.mono { font-family: "SF Mono", monospace; }

@keyframes blink { 50% { opacity: 0.5; } }
</style>
