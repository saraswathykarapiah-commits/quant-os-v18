<template>
  <div class="quant-os">
    <div class="glow-bg"></div>

    <div class="mobile-header">
      <div class="brand-area">
        <span class="logo-icon">💠</span> QUANT <span class="highlight">PRO</span>
      </div>
      <div class="connection-status" :class="loadingStocks ? 'blink' : 'online'"></div>
    </div>

    <aside class="sidebar glass-panel" v-show="!isMobile || activeTab === 'stocks'">
      <div class="panel-title-mobile" v-if="isMobile">主力优选池</div>
      
      <div class="control-panel" v-if="!isMobile">
        <button class="cyber-btn" @click="scanMarket" :disabled="loadingStocks">
          <span v-if="loadingStocks" class="spin">⟳</span>
          <span v-else>🚀 扫描全市场</span>
        </button>
      </div>

      <button v-if="isMobile && activeTab === 'stocks'" class="mobile-scan-btn" @click="scanMarket">
        {{ loadingStocks ? '扫描中...' : '🚀 开始扫描' }}
      </button>

      <div class="stock-list-wrapper custom-scroll">
        <div class="list-header" v-if="!isMobile">TOP 15 关注池</div>
        <div v-if="stocks.length === 0 && !loadingStocks" class="empty-list">
          暂无数据，请点击扫描
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
    </aside>

    <section class="market-center" v-show="!isMobile || activeTab === 'market'">
      <div class="panel-title-mobile" v-if="isMobile">市场全景</div>
      
      <div class="market-dash glass-panel">
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

    <main class="detail-deck" v-show="!isMobile || activeTab === 'analyze'">
      <div class="panel-title-mobile" v-if="isMobile">深度分析</div>

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
               该股综合评分第一。<br>点击下方生成 AI 研报。
             </div>
          </div>
        </div>
        <div class="star-footer">
          <button class="gold-btn" @click="generateStarReport" :disabled="analyzing">
            {{ analyzing ? 'AI思考中...' : '⚡️ 生成决胜研报' }}
          </button>
        </div>
      </div>

      <div v-else-if="currentStock" class="stock-detail">
        <div class="stock-header glass-panel">
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

        <div class="ai-box glass-panel">
          <div class="ai-head">
            <div class="ai-title">AI 短线策略</div>
            <button class="ai-btn" @click="triggerAI" :disabled="analyzing">{{ analyzing ? '...' : '分析' }}</button>
          </div>
          <div class="ai-body custom-scroll">
            <div v-if="aiCache[currentStock.code]" class="ai-text markdown-body">{{ aiCache[currentStock.code] }}</div>
            <div v-else class="ai-placeholder">点击分析获取操作建议...</div>
          </div>
        </div>
      </div>

      <div v-else class="empty-deck glass-panel">
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
// ⚠️ 重要：部署到 Netlify 前，请修改这里！
// 换成你在 Render 获得的后端网址，例如：
// const API = 'https://wo-de-niu-gu.onrender.com/api'
const API = 'http://localhost:5001/api' 
// ==========================================

const api = axios.create({ timeout: 60000 })
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
  try {
    const res = await api.get(`${API}/smart_pick`)
    if(res.data.code === 200) {
      stocks.value = res.data.data
      if(isMobile.value) {
        ElMessage.success("扫描完成")
        activeTab.value = 'analyze' // 扫完直接看金股
      }
    }
  } catch(e) { ElMessage.error("扫描超时") }
  finally { loadingStocks.value = false }
}

const handleStockClick = (stock) => { 
  currentStock.value = stock
  if(isMobile.value) activeTab.value = 'analyze' // 手机上点击股票自动跳到分析页
}

const backToGold = () => { currentStock.value = null }

const triggerAI = async () => {
  analyzing.value = true
  try {
    const res = await api.post(`${API}/analyze`, currentStock.value)
    if (res.data.code === 200) aiCache.value[currentStock.value.code] = res.data.data
  } catch(e) { aiCache.value[currentStock.value.code] = "Error: " + e.message } 
  finally { analyzing.value = false }
}

const generateStarReport = async () => {
  if (!starStock.value) return
  analyzing.value = true
  try {
    const res = await api.post(`${API}/analyze_star`, starStock.value)
    if (res.data.code === 200) starReport.value = res.data.data
  } catch(e) { starReport.value = "Error: " + e.message } 
  finally { analyzing.value = false }
}

const getColor = (v) => parseFloat(v) >= 0 ? 'text-red' : 'text-green'
</script>

<style>
/* 全局变量 */
:root {
  --bg-dark: #000000; /* iPhone OLED 纯黑 */
  --bg-panel: #111111;
  --text-main: #ffffff;
  --text-sub: #888888;
  --neon-red: #ff3b30; /* Apple Red */
  --neon-green: #34c759; /* Apple Green */
  --accent: #0a84ff; /* Apple Blue */
  --gold: #ffd60a;
  --border: 1px solid rgba(255,255,255,0.12);
  --glass: rgba(28, 28, 30, 0.85); /* iOS Glass */
  --nav-height: 60px; /* 底部导航高度 */
}

body { margin: 0; background: var(--bg-dark); color: var(--text-main); font-family: -apple-system, BlinkMacSystemFont, sans-serif; overflow: hidden; }

/* 桌面布局 */
.quant-os { display: flex; height: 100vh; width: 100vw; gap: 12px; padding: 12px; box-sizing: border-box; background: radial-gradient(circle at top left, #1c1c1e 0%, #000 100%); }
.glass-panel { background: var(--glass); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); border: var(--border); border-radius: 12px; display: flex; flex-direction: column; }

/* 通用字体颜色 */
.text-red { color: var(--neon-red); } 
.text-green { color: var(--neon-green); } 
.text-blue { color: var(--accent); }
.mono { font-family: "SF Mono", "Menlo", monospace; letter-spacing: -0.5px; }

/* 侧边栏 & 列表 */
.sidebar { width: 300px; }
.brand-area { padding: 16px; font-weight: 800; border-bottom: var(--border); font-size: 16px; letter-spacing: 1px; display: flex; align-items: center; gap: 8px; }
.control-panel { padding: 12px; }
.cyber-btn { width: 100%; background: var(--accent); color: white; border: none; padding: 12px; font-weight: 600; cursor: pointer; border-radius: 8px; font-size: 14px; }
.stock-list-wrapper { flex: 1; overflow-y: auto; padding: 8px; }
.ticker-card { background: rgba(255,255,255,0.05); padding: 12px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; border: 1px solid transparent; transition: 0.2s; }
.ticker-card.active { border-color: var(--accent); background: rgba(10, 132, 255, 0.15); }
.gold-card { border: 1px solid rgba(255, 214, 10, 0.4); background: linear-gradient(135deg, rgba(255,214,10,0.1), transparent); }
.ticker-row { display: flex; justify-content: space-between; align-items: center; }
.ticker-name { font-weight: 600; font-size: 15px; }
.ticker-price { font-weight: 700; font-size: 15px; }
.sub { margin-top: 4px; font-size: 12px; opacity: 0.8; }
.tag { font-size: 10px; padding: 3px 6px; border-radius: 4px; margin-top: 6px; display: inline-block; margin-right: 4px; font-weight: 600; }
.tag.gold { background: var(--gold); color: black; }
.tag.hot { background: rgba(255, 59, 48, 0.2); color: var(--neon-red); }
.tag.trend { border: 1px solid var(--accent); color: var(--accent); }

/* 中间区域 */
.market-center { flex: 1; display: flex; flex-direction: column; gap: 12px; overflow-y: auto; }
.market-dash, .sector-panel { padding: 16px; flex: 1; min-height: 160px; }
.dash-title, .panel-head { font-size: 13px; color: var(--text-sub); font-weight: 600; margin-bottom: 12px; text-transform: uppercase; }
.idx-val { font-size: 36px; font-weight: 800; letter-spacing: -1px; }
.idx-change { font-size: 14px; margin-top: 4px; font-weight: 600; }
.breadth-bar { height: 8px; background: #333; border-radius: 4px; overflow: hidden; display: flex; margin-top: 15px; }
.up-bar { background: var(--neon-red); } .down-bar { background: var(--neon-green); }
.sector-row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 14px; }

/* 右侧详情 */
.detail-deck { width: 360px; }
.star-view { height: 100%; display: flex; flex-direction: column; }
.star-header { padding: 30px 20px; text-align: center; border-bottom: var(--border); }
.star-icon { font-size: 48px; margin-bottom: 10px; display: block; }
.star-name { font-size: 28px; font-weight: 800; }
.star-body { flex: 1; padding: 20px; overflow-y: auto; }
.tech-dashboard { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-bottom: 20px; background: rgba(255,255,255,0.05); padding: 15px; border-radius: 12px; }
.tech-item { text-align: center; }
.ti-label { font-size: 11px; color: var(--text-sub); }
.ti-val { font-size: 16px; font-weight: 700; margin-top: 4px; }
.gold-btn { width: 100%; background: var(--gold); color: black; border: none; padding: 16px; font-weight: 700; border-radius: 12px; font-size: 16px; cursor: pointer; }
.ai-text { font-size: 14px; line-height: 1.6; color: #ddd; }

/* 📱 移动端适配 (Media Queries) */
.mobile-nav, .mobile-header, .mobile-scan-btn { display: none; }

@media (max-width: 768px) {
  .quant-os { padding: 0; padding-bottom: var(--nav-height); background: #000; }
  .glass-panel { border-radius: 0; border: none; background: #000; border-bottom: 1px solid #222; }
  
  /* 隐藏电脑端不需要的 */
  .brand-area { display: none; } 
  .list-header { display: none; }

  /* 手机顶部 */
  .mobile-header { display: flex; justify-content: space-between; align-items: center; height: 44px; padding: 0 16px; background: rgba(0,0,0,0.8); backdrop-filter: blur(10px); position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #222; padding-top: env(safe-area-inset-top); }
  .mobile-header .brand-area { display: block; border: none; padding: 0; font-size: 16px; }
  .connection-status { width: 8px; height: 8px; border-radius: 50%; background: #333; }
  .connection-status.online { background: var(--neon-green); box-shadow: 0 0 5px var(--neon-green); }
  
  /* 布局改为单栏 */
  .sidebar, .market-center, .detail-deck { width: 100%; height: 100%; overflow-y: auto; padding-top: 10px; }
  
  /* 手机端样式微调 */
  .ticker-card { margin: 0 12px 10px; padding: 16px; }
  .market-dash, .sector-panel { margin-bottom: 10px; min-height: auto; }
  .panel-title-mobile { font-size: 20px; font-weight: 800; padding: 10px 16px; color: var(--text-main); }
  
  /* 悬浮扫描按钮 */
  .mobile-scan-btn { display: block; position: fixed; bottom: 80px; right: 20px; background: var(--accent); color: white; border: none; padding: 12px 24px; border-radius: 30px; font-weight: bold; box-shadow: 0 4px 15px rgba(10, 132, 255, 0.4); z-index: 50; }

  /* 底部导航栏 */
  .mobile-nav { display: flex; position: fixed; bottom: 0; left: 0; width: 100%; height: var(--nav-height); background: rgba(20,20,20,0.95); backdrop-filter: blur(20px); border-top: 1px solid #333; z-index: 100; padding-bottom: env(safe-area-inset-bottom); }
  .nav-item { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #666; transition: 0.2s; }
  .nav-item.active { color: var(--accent); }
  .nav-icon { font-size: 20px; margin-bottom: 2px; }
  .nav-text { font-size: 10px; font-weight: 500; }
  
  /* 详情页全屏覆盖 */
  .stock-detail, .star-view { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 60; padding-top: env(safe-area-inset-top); padding-bottom: 80px; overflow-y: auto; }
  .close-btn { font-size: 24px; padding: 10px; }
}
</style>
