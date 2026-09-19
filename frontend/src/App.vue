<template>
  <div class="app-layout" @mousemove="onDrag" @mouseup="stopDrag" @mouseleave="stopDrag">
    <!-- 侧边栏 -->
    <aside class="sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="sidebar-header" @click="goHome" title="点击回到首页" style="cursor: pointer">
        <div class="logo">V</div>
        <div class="header-info">
          <div class="logo-text">万能估值终端</div>
          <div class="logo-sub">Universal Valuation Pro</div>
        </div>
      </div>

      <!-- 搜索输入区域 (支持模糊联想与示例指引) -->
      <div class="search-section" @click.stop>
        <div class="search-input-wrap">
          <div class="search-bar">
            <input
              v-model="tickerInput"
              class="field search-field"
              placeholder="代码/名称/简拼 (如 00700/腾讯/tx)"
              @input="onSearchInput"
              @focus="onSearchFocus"
              @keyup.enter="handleEnterKey"
              @keydown.down.prevent="navigateResults(1)"
              @keydown.up.prevent="navigateResults(-1)"
              @keydown.esc="showSuggestions = false"
            />
            <select v-model="marketInput" class="field market-select">
              <option value="HK">HK 港股</option>
              <option value="US">US 美股</option>
              <option value="CN">CN A股</option>
            </select>
            <button class="btn btn-primary analyze-btn" @click="handleEnterKey" :disabled="state.loading">
              {{ state.loading ? '...' : '分析' }}
            </button>
          </div>

          <!-- 模糊查找实时联想列表浮层 -->
          <div class="search-dropdown" v-if="showSuggestions && suggestions.length > 0">
            <div class="dropdown-header">
              <span>智能联想匹配 ({{ suggestions.length }})</span>
              <span class="dropdown-tip">↑↓选择 / 回车或点击直接分析</span>
            </div>
            <div
              v-for="(s, index) in suggestions"
              :key="s.ticker + s.market"
              class="dropdown-item"
              :class="{ active: selectedIndex === index }"
              @click="chooseSuggestion(s)"
            >
              <div class="item-main">
                <span class="item-name">{{ s.name }}</span>
                <span class="item-ticker mono">{{ s.ticker }}</span>
              </div>
              <div class="item-meta">
                <span class="item-sector">{{ s.sector }}</span>
                <span class="item-badge" :class="'market-' + s.market.toLowerCase()">{{ s.market }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 查找指引与分类示例展开面板 -->
        <div class="search-guide-box">
          <div class="guide-header" @click="showGuide = !showGuide">
            <span class="guide-title">💡 查找指引与示例</span>
            <span class="guide-toggle">{{ showGuide ? '▲ 收起' : '▼ 展开' }}</span>
          </div>

          <div class="guide-content" v-show="showGuide">
            <div class="guide-tip">
              支持输入 <b>股票代码</b>、<b>公司名称</b> 或 <b>拼音首字母</b> 智能联想。点击下方任意示例即刻分析：
            </div>

            <div class="guide-category">
              <div class="guide-cat-title">🇭🇰 港股精选:</div>
              <div class="guide-pills">
                <span class="guide-pill" @click="selectQuick({ name: 'MiniMax', ticker: '00100', market: 'HK' })">00100 MiniMax</span>
                <span class="guide-pill" @click="selectQuick({ name: '智谱', ticker: '02513', market: 'HK' })">02513 智谱</span>
                <span class="guide-pill" @click="selectQuick({ name: '腾讯控股', ticker: '00700', market: 'HK' })">00700 腾讯</span>
                <span class="guide-pill" @click="selectQuick({ name: '泡泡玛特', ticker: '09992', market: 'HK' })">09992 泡泡玛特</span>
                <span class="guide-pill" @click="selectQuick({ name: '美团', ticker: '03690', market: 'HK' })">03690 美团</span>
                <span class="guide-pill" @click="selectQuick({ name: '小米集团', ticker: '01810', market: 'HK' })">01810 小米</span>
                <span class="guide-pill" @click="selectQuick({ name: '快手', ticker: '01024', market: 'HK' })">01024 快手</span>
              </div>
            </div>

            <div class="guide-category">
              <div class="guide-cat-title">🇺🇸 美股精选:</div>
              <div class="guide-pills">
                <span class="guide-pill" @click="selectQuick({ name: '苹果公司', ticker: 'AAPL', market: 'US' })">AAPL 苹果</span>
                <span class="guide-pill" @click="selectQuick({ name: '英伟达', ticker: 'NVDA', market: 'US' })">NVDA 英伟达</span>
                <span class="guide-pill" @click="selectQuick({ name: '微软', ticker: 'MSFT', market: 'US' })">MSFT 微软</span>
                <span class="guide-pill" @click="selectQuick({ name: '特斯拉', ticker: 'TSLA', market: 'US' })">TSLA 特斯拉</span>
                <span class="guide-pill" @click="selectQuick({ name: '拼多多', ticker: 'PDD', market: 'US' })">PDD 拼多多</span>
              </div>
            </div>

            <div class="guide-category">
              <div class="guide-cat-title">🇨🇳 A股精选:</div>
              <div class="guide-pills">
                <span class="guide-pill" @click="selectQuick({ name: '工业富联', ticker: '601138', market: 'CN' })">601138 工业富联</span>
                <span class="guide-pill" @click="selectQuick({ name: '联创电子', ticker: '002036', market: 'CN' })">002036 联创电子</span>
                <span class="guide-pill" @click="selectQuick({ name: '贵州茅台', ticker: '600519', market: 'CN' })">600519 茅台</span>
                <span class="guide-pill" @click="selectQuick({ name: '比亚迪', ticker: '002594', market: 'CN' })">002594 比亚迪</span>
                <span class="guide-pill" @click="selectQuick({ name: '宁德时代', ticker: '300750', market: 'CN' })">300750 宁德时代</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 导航切换 (支持估值模型二级菜单折叠展开) -->
      <nav class="nav">
        <!-- 01 公司概况与估值指引 (核验标的身份与适配方法) -->
        <button
          class="nav-item"
          :class="{ active: tab === 'profile' }"
          @click="tab = 'profile'"
        >
          <span class="nav-num">01</span>
          <span class="nav-icon">🏢</span>
          <span class="nav-label">公司概况与估值指引</span>
        </button>

        <!-- 02 财务全景总览 -->
        <button
          class="nav-item"
          :class="{ active: tab === 'overview' }"
          @click="tab = 'overview'"
        >
          <span class="nav-num">02</span>
          <span class="nav-icon">📊</span>
          <span class="nav-label">财务全景总览</span>
        </button>

        <!-- 03 模型假设参数 -->
        <button
          class="nav-item"
          :class="{ active: tab === 'assumptions' }"
          @click="tab = 'assumptions'"
        >
          <span class="nav-num">03</span>
          <span class="nav-icon">⚙️</span>
          <span class="nav-label">模型假设参数</span>
        </button>

        <!-- 04 核心估值模型 (一级父菜单 + 二级子菜单) -->
        <div class="nav-group" :class="{ 'group-active': isValuationTabActive }">
          <div
            class="nav-item nav-group-header"
            :class="{ active: isValuationTabActive }"
            @click="toggleModelsMenu"
          >
            <span class="nav-num">04</span>
            <span class="nav-icon">🏛️</span>
            <span class="nav-label">核心估值模型</span>
            <span class="nav-badge">5大方法</span>
            <span class="group-caret">{{ modelsMenuOpen ? '▼' : '▶' }}</span>
          </div>

          <!-- 5种估值方法二级菜单 -->
          <div class="sub-nav" v-show="modelsMenuOpen">
            <button
              v-for="m in valuationSubModels"
              :key="m.id"
              class="sub-nav-item"
              :class="{ active: tab === m.id }"
              @click="tab = m.id"
            >
              <span class="sub-dot"></span>
              <span class="sub-num">{{ m.num }}</span>
              <span class="sub-icon">{{ m.icon }}</span>
              <div class="sub-info">
                <span class="sub-label">{{ m.label }}</span>
                <span class="sub-type">{{ m.sub }}</span>
              </div>
            </button>
          </div>
        </div>

        <!-- 05 综合决策看板 -->
        <button
          class="nav-item"
          :class="{ active: tab === 'summary' }"
          @click="tab = 'summary'"
        >
          <span class="nav-num">05</span>
          <span class="nav-icon">🎯</span>
          <span class="nav-label">综合决策看板</span>
        </button>
      </nav>

      <!-- 侧边栏底部与个性化 -->
      <div class="sidebar-footer">
        <div class="personalization-panel" v-if="showSettings">
          <div class="settings-title">外观与主题定制</div>
          <div class="theme-toggles">
            <button
              class="theme-btn"
              :class="{ active: state.theme === 'light' }"
              @click="state.theme = 'light'"
            >
              🌞 亮色模式
            </button>
            <button
              class="theme-btn"
              :class="{ active: state.theme === 'dark' }"
              @click="state.theme = 'dark'"
            >
              🌙 暗色模式
            </button>
          </div>
          <div class="accent-toggles">
            <span class="accent-label">主题强调色:</span>
            <div class="dots-wrap">
              <button
                v-for="color in ['teal', 'blue', 'purple', 'rose']"
                :key="color"
                class="color-dot"
                :class="{ active: state.accent === color }"
                :style="`--dot-color: var(--${color})`"
                @click="state.accent = color"
                :data-color="color"
              ></button>
            </div>
          </div>
        </div>

        <!-- 数据源信息卡片 (左下角核心展示) -->
        <div class="data-source-card">
          <div class="ds-header">
            <span class="ds-title">📡 数据源服务</span>
            <span class="ds-status-badge" :class="state.analyzeResult ? 'active' : 'standby'">
              {{ state.analyzeResult ? '● 已连接' : '○ 待命中' }}
            </span>
          </div>
          <div class="ds-details" v-if="state.analyzeResult">
            <div class="ds-row">
              <span class="ds-key">提供接口:</span>
              <span class="ds-val accent font-bold">{{ formatProvider(state.analyzeResult.source) }}</span>
            </div>
            <div class="ds-row">
              <span class="ds-key">覆盖市场:</span>
              <span class="ds-val mono">{{ state.market }} ({{ state.analyzeResult.currency || 'CNY' }})</span>
            </div>
            <div class="ds-row">
              <span class="ds-key">清洗健康度:</span>
              <span class="ds-val" :class="healthClass">
                {{ formatHealth(state.analyzeResult.health) }} · {{ state.analyzeResult.elapsed_seconds }}s
              </span>
            </div>
            <div class="ds-row" v-if="state.updateTime">
              <span class="ds-key">抓取时间:</span>
              <span class="ds-val mono">{{ fmtTime(state.updateTime) }}</span>
            </div>
          </div>
          <div class="ds-details ds-empty" v-else>
            <div class="ds-row">
              <span class="ds-key">主数据源:</span>
              <span class="ds-val mono">AkShare / Yahoo Finance</span>
            </div>
            <div class="ds-row">
              <span class="ds-key">支持市场:</span>
              <span class="ds-val text-muted">港股 / 美股 / A股 财报</span>
            </div>
          </div>
        </div>

        <div v-if="state.recalcTime" class="recalc-info">
          模型重算响应: {{ state.recalcTime.toFixed(0) }}ms
        </div>

        <div class="project-actions">
          <button class="btn btn-sm" @click="saveCurrent" :disabled="!state.assumptions">💾 保存项目</button>
          <button class="btn btn-sm" @click="openProjects">📂 项目库</button>
          <button
            class="btn btn-sm icon-btn"
            @click="showSettings = !showSettings"
            :class="{ active: showSettings }"
            title="个性化设置"
          >
            ⚙️
          </button>
        </div>
        <div class="disclaimer" @click="showDisclaimer = true">⚠ 免责声明与数据来源</div>
      </div>
    </aside>

    <!-- 可拉伸拖拽手柄 -->
    <div class="resizer" @mousedown.prevent="startDrag"></div>

    <!-- 主展示内容区 -->
    <main class="content">
      <!-- 顶部状态栏 -->
      <div class="top-nav" v-if="state.ticker && state.analyzeResult">
        <div class="breadcrumbs">
          <span class="bc-home" @click="goHome" title="点击回到首页">万能估值终端</span>
          <span class="bc-slash">/</span>
          <span class="bc-market">{{ state.market }}</span>
          <span class="bc-slash">/</span>
          <span class="bc-ticker accent">{{ state.ticker }}</span>
          <span class="bc-price" v-if="state.analyzeResult?.standard_financials?.price">
            现价: <b>¥{{ state.analyzeResult.standard_financials.price }}</b>
          </span>
        </div>

        <div class="top-actions">
          <button class="btn btn-sm" @click="exportCurrentPDF" title="快速导出当前报告PDF">
            📄 导出当前PDF
          </button>
        </div>
      </div>

      <!-- 错误警告提示 -->
      <div v-if="state.error" class="error-banner">
        <div class="error-title">数据加载或计算异常</div>
        <div class="error-desc">{{ state.error }}</div>
      </div>

      <!-- 加载中态 -->
      <div v-if="state.loading" class="loading-state">
        <div class="spinner"></div>
        <div class="loading-title">正在抓取财报并构建全维估值模型...</div>
        <div class="loading-desc">自动清洗勾稽财报科目 · 动态推演 WACC 折现率 · 测算 DCF/可比公司/SOTP</div>
      </div>

      <!-- 主视图路由内容 -->
      <template v-else-if="state.result && tab !== 'home'">
        <div class="view-transition">
          <!-- 01 公司档案与估值诊断 -->
          <CompanyProfileView v-if="tab === 'profile'" @navigate="handleModelNavigation" />
          <!-- 02 财务总览 -->
          <Overview v-else-if="tab === 'overview'" />
          <!-- 03 假设参数 -->
          <Assumptions v-else-if="tab === 'assumptions'" @navigate="handleModelNavigation" />
          <!-- 04 DCF 估值: Gordon 永续法 或 Exit 退出乘数法 -->
          <DCFView v-else-if="tab === 'dcf_gordon' || tab === 'dcf_exit' || tab === 'dcf'" :focusMethod="tab" />
          <!-- 04 可比公司估值: P/E 市盈率法 或 EV/EBITDA 倍数法 -->
          <CompsView v-else-if="tab === 'comps_pe' || tab === 'comps_ev_ebitda' || tab === 'comps'" :focusMultiple="tab" />
          <!-- 04 SOTP 分部加总估值 -->
          <SOTPView v-else-if="tab === 'sotp'" />
          <!-- 05 综合决策看板 -->
          <SummaryView v-else-if="tab === 'summary'" />
        </div>
      </template>

      <!-- 欢迎空状态 Hub / 首页 -->
      <div v-else class="welcome-hub">
        <div class="welcome-header">
          <div class="welcome-icon">📈</div>
          <h1 class="welcome-title">专业级上市公司智能估值终端</h1>
          <p class="welcome-sub">
            融合内生价值（DCF 现金流折现）、相对估值（可比公司行业倍数）、分部加总（SOTP）与敏感性决策矩阵
          </p>
          <div v-if="state.result" style="margin-top:16px">
            <button class="btn btn-primary" @click="tab = 'profile'">
              ➔ 继续查看当前已分析标的 ({{ state.ticker }})
            </button>
          </div>
        </div>

        <!-- 首页居中超大主搜索框 -->
        <div class="hero-search-container">
          <!-- 市场快速切换分类 Tabs -->
          <div class="hero-market-tabs">
            <button
              class="hero-tab-btn"
              :class="{ active: heroMarket === 'ALL' }"
              @click="setHeroMarket('ALL')"
            >
              🌐 全市场检索
            </button>
            <button
              class="hero-tab-btn"
              :class="{ active: heroMarket === 'HK' }"
              @click="setHeroMarket('HK')"
            >
              🇭🇰 港股 (HK)
            </button>
            <button
              class="hero-tab-btn"
              :class="{ active: heroMarket === 'US' }"
              @click="setHeroMarket('US')"
            >
              🇺🇸 美股 (US)
            </button>
            <button
              class="hero-tab-btn"
              :class="{ active: heroMarket === 'CN' }"
              @click="setHeroMarket('CN')"
            >
              🇨🇳 A股 (沪深北)
            </button>
          </div>

          <!-- 搜索输入主容器 -->
          <div class="hero-search-bar-wrap">
            <span class="hero-search-icon">🔍</span>
            <input
              v-model="heroSearchInput"
              class="hero-search-input"
              type="text"
              placeholder="输入代码、公司名或简拼 (如 00700 / 腾讯 / 泡泡玛特 / 00100 / NVDA / 601138)"
              @input="onHeroSearchInput"
              @focus="onHeroSearchFocus"
              @keyup.enter="handleHeroEnterKey"
              @keydown.down.prevent="navigateHeroResults(1)"
              @keydown.up.prevent="navigateHeroResults(-1)"
              @keydown.esc="showHeroSuggestions = false"
            />
            <button
              v-if="heroSearchInput"
              class="hero-clear-btn"
              @click="clearHeroInput"
              title="清除输入"
            >
              ✕
            </button>
            <button
              class="hero-submit-btn"
              @click="handleHeroEnterKey"
              :disabled="state.loading"
            >
              <span v-if="state.loading">估值分析中...</span>
              <span v-else>⚡ 开始深度估值</span>
            </button>

            <!-- 首页主搜索联想下拉浮层 -->
            <div
              class="hero-search-dropdown"
              v-if="showHeroSuggestions && heroSuggestions.length > 0"
            >
              <div class="hero-dropdown-header">
                <span>智能联想上市公司 ({{ heroSuggestions.length }})</span>
                <span class="hero-dropdown-tip">↑↓ 选择 · 回车/点击一键直达估值报告</span>
              </div>
              <div
                v-for="(s, index) in heroSuggestions"
                :key="s.ticker + s.market"
                class="hero-dropdown-item"
                :class="{ active: heroSelectedIndex === index }"
                @click="chooseHeroSuggestion(s)"
              >
                <div class="hero-item-main">
                  <span class="hero-item-name">{{ s.name }}</span>
                  <span class="hero-item-ticker mono">{{ s.ticker }}</span>
                </div>
                <div class="hero-item-meta">
                  <span class="hero-item-sector">{{ s.sector }}</span>
                  <span class="hero-item-badge" :class="'market-' + s.market.toLowerCase()">
                    {{ s.market === 'HK' ? '🇭🇰 港股' : (s.market === 'US' ? '🇺🇸 美股' : '🇨🇳 A股') }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 热门标的快速直达标签 -->
          <div class="hero-hot-tags">
            <span class="hero-hot-label">🔥 热门标的直达:</span>
            <button class="hero-hot-tag" @click="selectQuick({ name: 'MiniMax', ticker: '00100', market: 'HK' })">
              <span class="hot-badge-hk">HK</span> 00100 MiniMax
            </button>
            <button class="hero-hot-tag" @click="selectQuick({ name: '智谱', ticker: '02513', market: 'HK' })">
              <span class="hot-badge-hk">HK</span> 02513 智谱
            </button>
            <button class="hero-hot-tag" @click="selectQuick({ name: '腾讯控股', ticker: '00700', market: 'HK' })">
              <span class="hot-badge-hk">HK</span> 00700 腾讯控股
            </button>
            <button class="hero-hot-tag" @click="selectQuick({ name: '工业富联', ticker: '601138', market: 'CN' })">
              <span class="hot-badge-cn">CN</span> 601138 工业富联
            </button>
            <button class="hero-hot-tag" @click="selectQuick({ name: '联创电子', ticker: '002036', market: 'CN' })">
              <span class="hot-badge-cn">CN</span> 002036 联创电子
            </button>
            <button class="hero-hot-tag" @click="selectQuick({ name: '英伟达', ticker: 'NVDA', market: 'US' })">
              <span class="hot-badge-us">US</span> NVDA 英伟达
            </button>
            <button class="hero-hot-tag" @click="selectQuick({ name: '泡泡玛特', ticker: '09992', market: 'HK' })">
              <span class="hot-badge-hk">HK</span> 09992 泡泡玛特
            </button>
          </div>
        </div>

        <div class="welcome-cards">
          <div class="welcome-card" @click="selectQuick({ name: '泡泡玛特', ticker: '09992', market: 'HK' })">
            <div class="wc-badge">港股消费潮流</div>
            <div class="wc-name">泡泡玛特 (09992.HK)</div>
            <div class="wc-desc">IP 全球化高增长标的，体验 5 年预测与 DCF 敏感性分析</div>
            <div class="wc-action">一键快速分析 ➔</div>
          </div>
          <div class="welcome-card" @click="selectQuick({ name: '腾讯控股', ticker: '00700', market: 'HK' })">
            <div class="wc-badge">港股互联网龙头</div>
            <div class="wc-name">腾讯控股 (00700.HK)</div>
            <div class="wc-desc">成熟多元业务集团，体验 SOTP 分部加总与可比对标</div>
            <div class="wc-action">一键快速分析 ➔</div>
          </div>
          <div class="welcome-card" @click="selectQuick({ name: '苹果公司', ticker: 'AAPL', market: 'US' })">
            <div class="wc-badge">美股硬科技巨头</div>
            <div class="wc-name">苹果公司 (AAPL.US)</div>
            <div class="wc-desc">高自由现金流标的，体验动态 WACC 与 Exit 退出倍数</div>
            <div class="wc-action">一键快速分析 ➔</div>
          </div>
        </div>

        <div class="feature-pills">
          <span class="f-pill">✨ 自动勾稽平衡校验</span>
          <span class="f-pill">📊 历年双轴趋势图与费用拆解</span>
          <span class="f-pill">⚡ 秒级联动动态重算</span>
          <span class="f-pill">📄 投行级 PDF 研报一键导出</span>
        </div>
      </div>
    </main>

    <!-- 项目列表弹窗 -->
    <div v-if="showProjects" class="modal-overlay" @click.self="showProjects = false">
      <div class="modal">
        <div class="modal-title">已保存估值项目库</div>
        <div v-if="projects.length === 0" class="modal-empty">暂无保存的项目</div>
        <div v-if="projects.length > 0" class="export-all-bar">
          <button class="btn btn-primary" @click="exportAllPDF">一键全部导出 (PDF ZIP)</button>
          <button class="btn" @click="exportSelected" :disabled="selectedIds.length === 0">
            导出选中 ({{ selectedIds.length }})
          </button>
          <button class="btn" @click="exportAll">全部导出 (JSON)</button>
        </div>
        <div v-for="p in projects" :key="p.id" class="project-row">
          <input type="checkbox" :value="p.id" v-model="selectedIds" class="proj-checkbox" />
          <div class="project-info">
            <div class="project-name">{{ p.name }}</div>
            <div class="project-meta">{{ p.ticker }} · {{ p.market }} · {{ p.updated_at.slice(0, 10) }}</div>
          </div>
          <button class="btn btn-xs" @click="loadProj(p.id)">载入</button>
          <button class="btn btn-xs" @click="exportProj(p.id)">JSON</button>
          <button class="btn btn-xs" @click="exportPDF(p.id)">PDF</button>
          <button class="btn btn-xs btn-danger" @click="delProj(p.id)">删除</button>
        </div>
        <div style="text-align:right;margin-top:16px">
          <button class="btn" @click="showProjects = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 免责声明弹窗 -->
    <div v-if="showDisclaimer" class="modal-overlay" @click.self="showDisclaimer = false">
      <div class="modal">
        <div class="modal-title">免责声明与数据说明</div>
        <div class="disclaimer-text">
          <p>本系统是一款专业的估值分析计算工具，计算结果完全基于公开财报及用户设定的假设参数。</p>
          <p>重要提醒：</p>
          <ul>
            <li>本工具生成的所有内在价值、目标价与评级<b>不构成任何投资建议或要约</b>。</li>
            <li>DCF 永续增长模型及可比公司模型对参数（如 WACC、g、Exit 倍数）具有极高敏感性，不同假设会带来显著结论差异。</li>
            <li>用户应结合行业真实基本面进行独立研究与审慎决策。</li>
          </ul>
        </div>
        <div style="text-align:right;margin-top:16px">
          <button class="btn btn-primary" @click="showDisclaimer = false">我已了解并同意</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { state, runAnalyze } from './store.js'
import {
  saveProject, listProjects, loadProject, deleteProject,
  exportProject, exportProjectPDF, exportAllProjects, exportAllProjectsPDF, exportSelectedProjects,
  searchStocks
} from './api.js'
import CompanyProfileView from './components/CompanyProfileView.vue'
import Overview from './components/Overview.vue'
import Assumptions from './components/Assumptions.vue'
import DCFView from './components/DCFView.vue'
import CompsView from './components/CompsView.vue'
import SOTPView from './components/SOTPView.vue'
import SummaryView from './components/SummaryView.vue'
import { fuzzySearchStocks } from './utils/stockDictionary.js'

const tickerInput = ref('09992')
const marketInput = ref('HK')
const tab = ref('profile')
const showDisclaimer = ref(false)
const showProjects = ref(false)
const showSettings = ref(false)
const projects = ref([])
const selectedIds = ref([])

// 模糊搜索联想与指引状态
const showSuggestions = ref(false)
const suggestions = ref([])
const selectedIndex = ref(-1)
const showGuide = ref(true)
let searchTimer = null

function onSearchInput() {
  selectedIndex.value = -1
  const raw = (tickerInput.value || '').trim()
  if (!raw) {
    suggestions.value = []
    showSuggestions.value = false
    return
  }
  // 智能市场识别：支持 HK/SH/SZ/BJ 前后缀及纯数字位数
  if (/^HK\d+/i.test(raw) || /\.HK$/i.test(raw) || /^\d{5}$/.test(raw)) {
    marketInput.value = 'HK'
  } else if (/^(SH|SZ|BJ)\d+/i.test(raw) || /\.(SS|SZ|BJ)$/i.test(raw) || /^\d{6}$/.test(raw)) {
    marketInput.value = 'CN'
  }

  // 1. 本地即时响应
  const local = fuzzySearchStocks(raw, marketInput.value)
  suggestions.value = local
  showSuggestions.value = suggestions.value.length > 0

  // 2. 远端接口联想补全（支持全市场 5000+ A股、港美股与拼音）
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(async () => {
    try {
      const remote = await searchStocks(raw, marketInput.value)
      if (remote && remote.length > 0) {
        const map = new Map()
        // 先放本地精选（以 market:ticker 复合键去重防串台）
        suggestions.value.forEach(item => map.set(`${item.market}:${item.ticker}`, item))
        // 追加远程结果
        remote.forEach(item => {
          const k = `${item.market}:${item.ticker}`
          if (!map.has(k)) {
            map.set(k, item)
          }
        })
        suggestions.value = Array.from(map.values()).slice(0, 10)
        showSuggestions.value = suggestions.value.length > 0
      }
    } catch (e) {}
  }, 250)
}

function onSearchFocus() {
  const raw = (tickerInput.value || '').trim()
  if (raw) {
    suggestions.value = fuzzySearchStocks(raw, marketInput.value)
    showSuggestions.value = suggestions.value.length > 0
  }
}

function chooseSuggestion(s) {
  tickerInput.value = s.ticker
  marketInput.value = s.market
  showSuggestions.value = false
  doAnalyze()
}

function navigateResults(direction) {
  if (!showSuggestions.value || suggestions.value.length === 0) return
  selectedIndex.value = (selectedIndex.value + direction + suggestions.value.length) % suggestions.value.length
}

function handleEnterKey() {
  const raw = (tickerInput.value || '').trim()
  const rawLower = raw.toLowerCase()
  const rawDigits = raw.replace(/\D/g, '')

  if (showSuggestions.value && selectedIndex.value >= 0 && suggestions.value[selectedIndex.value]) {
    chooseSuggestion(suggestions.value[selectedIndex.value])
    return
  }

  if (showSuggestions.value && suggestions.value.length > 0) {
    const topMatch = suggestions.value[0]
    const topName = (topMatch.name || '').toLowerCase()
    const topTicker = (topMatch.ticker || '').toLowerCase()
    const topTickerDigits = topTicker.replace(/\D/g, '')

    // 智能容错：精确名称/代码/去零数字/包含/拼音匹配
    if (
      topName === rawLower
      || topTicker === rawLower
      || (rawDigits && topTickerDigits.replace(/^0+/, '') === rawDigits.replace(/^0+/, ''))
      || topName.includes(rawLower)
      || (topMatch.pinyin && Array.isArray(topMatch.pinyin) && topMatch.pinyin.some(p => p.toLowerCase() === rawLower))
    ) {
      chooseSuggestion(topMatch)
      return
    }
  }

  showSuggestions.value = false
  if (/^HK\d+/i.test(raw) || /\.HK$/i.test(raw) || /^\d{5}$/.test(raw)) {
    marketInput.value = 'HK'
  } else if (/^(SH|SZ|BJ)\d+/i.test(raw) || /\.(SS|SZ|BJ)$/i.test(raw) || /^\d{6}$/.test(raw)) {
    marketInput.value = 'CN'
  }
  doAnalyze()
}

// ==================== 首页主搜索框逻辑 ====================
const heroSearchInput = ref('')
const heroMarket = ref('ALL') // 'ALL' | 'HK' | 'US' | 'CN'
const heroSuggestions = ref([])
const showHeroSuggestions = ref(false)
const heroSelectedIndex = ref(-1)
let heroSearchTimer = null

function setHeroMarket(m) {
  heroMarket.value = m
  if (heroSearchInput.value.trim()) {
    onHeroSearchInput()
  }
}

function clearHeroInput() {
  heroSearchInput.value = ''
  heroSuggestions.value = []
  showHeroSuggestions.value = false
  heroSelectedIndex.value = -1
}

function onHeroSearchInput() {
  heroSelectedIndex.value = -1
  const raw = (heroSearchInput.value || '').trim()
  if (!raw) {
    heroSuggestions.value = []
    showHeroSuggestions.value = false
    return
  }

  // 智能识别市场
  if (/^HK\d+/i.test(raw) || /\.HK$/i.test(raw) || /^\d{5}$/.test(raw)) {
    if (heroMarket.value !== 'HK') heroMarket.value = 'HK'
  } else if (/^(SH|SZ|BJ)\d+/i.test(raw) || /\.(SS|SZ|BJ)$/i.test(raw) || /^\d{6}$/.test(raw)) {
    if (heroMarket.value !== 'CN') heroMarket.value = 'CN'
  }

  const queryMarket = heroMarket.value === 'ALL' ? undefined : heroMarket.value

  // 1. 本地精准与前缀/拼音字典匹配
  const local = fuzzySearchStocks(raw, queryMarket)
  heroSuggestions.value = local
  showHeroSuggestions.value = local.length > 0

  // 2. 远端接口联想补全
  if (heroSearchTimer) clearTimeout(heroSearchTimer)
  heroSearchTimer = setTimeout(async () => {
    try {
      const remote = await searchStocks(raw, queryMarket)
      if (remote && remote.length > 0) {
        const map = new Map()
        heroSuggestions.value.forEach(item => map.set(`${item.market}:${item.ticker}`, item))
        remote.forEach(item => {
          const k = `${item.market}:${item.ticker}`
          if (!map.has(k)) {
            map.set(k, item)
          }
        })
        heroSuggestions.value = Array.from(map.values()).slice(0, 10)
        showHeroSuggestions.value = heroSuggestions.value.length > 0
      }
    } catch (e) {}
  }, 250)
}

function onHeroSearchFocus() {
  const raw = (heroSearchInput.value || '').trim()
  if (raw) {
    const queryMarket = heroMarket.value === 'ALL' ? undefined : heroMarket.value
    heroSuggestions.value = fuzzySearchStocks(raw, queryMarket)
    showHeroSuggestions.value = heroSuggestions.value.length > 0
  }
}

function chooseHeroSuggestion(s) {
  tickerInput.value = s.ticker
  marketInput.value = s.market
  heroSearchInput.value = `${s.ticker} ${s.name}`
  showHeroSuggestions.value = false
  doAnalyze()
}

function navigateHeroResults(direction) {
  if (!showHeroSuggestions.value || heroSuggestions.value.length === 0) return
  heroSelectedIndex.value = (heroSelectedIndex.value + direction + heroSuggestions.value.length) % heroSuggestions.value.length
}

function handleHeroEnterKey() {
  const raw = (heroSearchInput.value || '').trim()
  if (!raw) return
  const rawLower = raw.toLowerCase()
  const rawDigits = raw.replace(/\D/g, '')

  if (showHeroSuggestions.value && heroSelectedIndex.value >= 0 && heroSuggestions.value[heroSelectedIndex.value]) {
    chooseHeroSuggestion(heroSuggestions.value[heroSelectedIndex.value])
    return
  }

  if (showHeroSuggestions.value && heroSuggestions.value.length > 0) {
    const topMatch = heroSuggestions.value[0]
    const topName = (topMatch.name || '').toLowerCase()
    const topTicker = (topMatch.ticker || '').toLowerCase()
    const topTickerDigits = topTicker.replace(/\D/g, '')

    if (
      topName === rawLower
      || topTicker === rawLower
      || (rawDigits && topTickerDigits.replace(/^0+/, '') === rawDigits.replace(/^0+/, ''))
      || topName.includes(rawLower)
      || (topMatch.pinyin && Array.isArray(topMatch.pinyin) && topMatch.pinyin.some(p => p.toLowerCase() === rawLower))
    ) {
      chooseHeroSuggestion(topMatch)
      return
    }
  }

  showHeroSuggestions.value = false

  // 市场推断
  let targetMarket = heroMarket.value === 'ALL' ? 'CN' : heroMarket.value
  if (/^HK\d+/i.test(raw) || /\.HK$/i.test(raw) || /^\d{5}$/.test(raw)) {
    targetMarket = 'HK'
  } else if (/^(SH|SZ|BJ)\d+/i.test(raw) || /\.(SS|SZ|BJ)$/i.test(raw) || /^\d{6}$/.test(raw)) {
    targetMarket = 'CN'
  } else if (/^[A-Z]{1,5}$/i.test(raw) && heroMarket.value === 'US') {
    targetMarket = 'US'
  }

  tickerInput.value = raw
  marketInput.value = targetMarket
  doAnalyze()
}





// 侧边栏拖拽调宽
const sidebarWidth = ref(270)
const isDragging = ref(false)

function startDrag() {
  isDragging.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onDrag(e) {
  if (!isDragging.value) return
  let newWidth = e.clientX
  if (newWidth < 220) newWidth = 220
  if (newWidth > 550) newWidth = 550
  sidebarWidth.value = newWidth
}

function stopDrag() {
  if (isDragging.value) {
    isDragging.value = false
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    window.dispatchEvent(new Event('resize'))
  }
}

// 5大核心估值方法二级子菜单定义
const valuationSubModels = [
  { id: 'dcf_gordon', num: '3.1', icon: '📈', label: 'Gordon 永续增长法', sub: '内生估值 · DCF' },
  { id: 'dcf_exit', num: '3.2', icon: '📊', label: 'Exit 退出乘数法', sub: 'EV/EBITDA · DCF' },
  { id: 'comps_pe', num: '3.3', icon: '🏢', label: 'P/E 市盈率相对估值', sub: '同行对标 · Comps' },
  { id: 'comps_ev_ebitda', num: '3.4', icon: '🏭', label: 'EV/EBITDA 倍数估值', sub: '企业价值 · Comps' },
  { id: 'sotp', num: '3.5', icon: '🧩', label: 'SOTP 分部加总估值', sub: '业务分拆 · Sum of Parts' },
]

const modelsMenuOpen = ref(true)

const isValuationTabActive = computed(() => {
  return ['dcf_gordon', 'dcf_exit', 'dcf', 'comps_pe', 'comps_ev_ebitda', 'comps', 'sotp'].includes(tab.value)
})

function toggleModelsMenu() {
  modelsMenuOpen.value = !modelsMenuOpen.value
  // 如果子菜单折叠时点击，展开并默认选中第一项（若当前未在估值模型内）
  if (modelsMenuOpen.value && !isValuationTabActive.value) {
    tab.value = 'dcf_gordon'
  }
}

function handleModelNavigation(methodKey) {
  tab.value = methodKey
  modelsMenuOpen.value = true
}

function goHome() {
  tab.value = 'home'
}

async function doAnalyze() {
  if (!tickerInput.value) return
  await runAnalyze(tickerInput.value.trim(), marketInput.value)
  if (state.ticker) {
    tickerInput.value = state.ticker
  }
  if (state.market) {
    marketInput.value = state.market
  }
  tab.value = 'profile'
}

function selectQuick(q) {
  tickerInput.value = q.ticker
  marketInput.value = q.market
  doAnalyze()
}

async function saveCurrent() {
  if (!state.assumptions) return
  const name = `${state.ticker} (${state.market}) ${new Date().toLocaleDateString('zh-CN')}`
  await saveProject(name, state.ticker, state.market, state.assumptions)
  projects.value = (await listProjects()).projects
  showProjects.value = true
}

async function openProjects() {
  try {
    projects.value = (await listProjects()).projects
  } catch (e) {}
  showProjects.value = true
}

async function loadProj(id) {
  const p = await loadProject(id)
  state.ticker = p.ticker
  state.market = p.market
  state.assumptions = p.payload
  showProjects.value = false
  tab.value = 'profile'
}

async function delProj(id) {
  await deleteProject(id)
  projects.value = (await listProjects()).projects
}

async function exportProj(id) {
  const data = await exportProject(id)
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${data.project.name}_${data.project.ticker}_估值结果.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function exportPDF(id) {
  const blob = await exportProjectPDF(id)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `估值报告_${id}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

async function exportCurrentPDF() {
  // 如果保存了项目可直接导出
  try {
    await saveCurrent()
    const latest = projects.value[projects.value.length - 1]
    if (latest) exportPDF(latest.id)
  } catch (e) {
    alert('请先保存项目后再导出PDF')
  }
}

async function exportAll() {
  const data = await exportAllProjects()
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `全部项目导出_${new Date().toLocaleDateString('zh-CN')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function exportAllPDF() {
  const blob = await exportAllProjectsPDF()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `全部估值报告_${new Date().toLocaleDateString('zh-CN')}.zip`
  a.click()
  URL.revokeObjectURL(url)
}

async function exportSelected() {
  if (selectedIds.value.length === 0) return
  const blob = await exportSelectedProjects(selectedIds.value)
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `选中估值报告_${new Date().toLocaleDateString('zh-CN')}.zip`
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  try {
    projects.value = (await listProjects()).projects
  } catch (e) {}

  window.addEventListener('click', () => {
    showSuggestions.value = false
  })
})

function fmtTime(ts) {
  const d = new Date(ts)
  return d.toLocaleTimeString('zh-CN', { hour12: false })
}

function formatProvider(src) {
  if (!src) return '公开财经接口'
  const s = String(src).toLowerCase()
  if (s.includes('akshare')) return 'AkShare (东财/新浪/同花顺)'
  if (s.includes('yfinance') || s.includes('yahoo')) return 'Yahoo Finance (雅虎财经)'
  if (s.includes('manual')) return '本地标杆数据库'
  return src
}

function formatHealth(h) {
  if (h === 'good') return '数据完整 ✓'
  if (h === 'partial') return '部分推导 ⚠'
  return '降级运行 !'
}

const healthClass = computed(() => {
  const h = state.analyzeResult?.health
  if (h === 'good') return 'good'
  if (h === 'partial') return 'warn'
  return 'danger'
})
</script>

<style scoped>
.app-layout { display: flex; height: 100%; overflow: hidden; }

/* 侧边栏 */
.sidebar {
  background: var(--bg-1);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: background 0.3s;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
  transition: all 0.2s ease;
}

.sidebar-header:hover {
  background: var(--bg-2);
}

.sidebar-header:hover .logo {
  transform: scale(1.05);
  box-shadow: 0 0 16px var(--accent);
}

.sidebar-header:hover .logo-text {
  color: var(--accent);
}

.logo {
  width: 36px; height: 36px;
  background: var(--accent-dim);
  border: 1px solid var(--accent);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  color: var(--accent);
  font-weight: 800; font-size: 18px;
  box-shadow: 0 0 12px var(--accent-dim);
  flex-shrink: 0;
}

.logo-text { font-size: 14px; font-weight: 700; color: var(--text-0); }
.logo-sub { font-size: 10px; color: var(--text-3); letter-spacing: 0.04em; }

.search-section {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.search-input-wrap { position: relative; width: 100%; }
.search-bar { display: flex; gap: 6px; }
.search-field { flex: 1; min-width: 0; }
.market-select { width: 78px; font-size: 11px; }
.analyze-btn { flex-shrink: 0; }

/* 智能联想下拉浮层 */
.search-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--bg-1);
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  box-shadow: var(--shadow-md), 0 10px 25px -5px rgba(0,0,0,0.5);
  z-index: 100;
  max-height: 280px;
  overflow-y: auto;
}
.dropdown-header {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--bg-2);
  border-bottom: 1px solid var(--border);
  font-size: 10px;
  color: var(--text-3);
  font-weight: 600;
}
.dropdown-tip { font-family: var(--font-mono); }

.dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}
.dropdown-item:last-child { border-bottom: none; }
.dropdown-item:hover, .dropdown-item.active {
  background: var(--accent-dim);
}
.item-main { display: flex; flex-direction: column; gap: 2px; }
.item-name { font-size: 12px; font-weight: 600; color: var(--text-0); }
.item-ticker { font-size: 11px; color: var(--accent); font-weight: 600; }
.item-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.item-sector { font-size: 10px; color: var(--text-3); }
.item-badge {
  font-size: 9px;
  font-family: var(--font-mono);
  padding: 1px 4px;
  border-radius: 3px;
  font-weight: bold;
}
.market-hk { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.market-us { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.market-cn { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }

/* 查找指引与分类示例展开面板 */
.search-guide-box {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow: hidden;
}
.guide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-2);
  user-select: none;
  background: var(--bg-2);
  transition: color 0.15s;
}
.guide-header:hover { color: var(--accent); }
.guide-toggle { font-size: 10px; color: var(--text-3); }

.guide-content {
  padding: 8px 10px;
  border-top: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.guide-tip { font-size: 10px; color: var(--text-3); line-height: 1.4; }
.guide-tip code { background: var(--bg-3); padding: 1px 4px; border-radius: 3px; color: var(--accent); font-family: var(--font-mono); }

.guide-category { display: flex; flex-direction: column; gap: 4px; }
.guide-cat-title { font-size: 10px; color: var(--text-3); font-weight: 600; }
.guide-pills { display: flex; flex-wrap: wrap; gap: 4px; }
.guide-pill {
  font-size: 10px;
  padding: 2px 6px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
}
.guide-pill:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-dim);
}

.nav { flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 4px; overflow-y: auto; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  width: 100%; padding: 9px 12px;
  background: transparent; border: none; border-radius: 8px;
  color: var(--text-2); cursor: pointer; font-size: 13px; font-weight: 500;
  text-align: left; transition: all 0.15s;
}
.nav-item:hover { background: var(--bg-2); color: var(--text-0); transform: translateX(2px); }
.nav-item.active { background: var(--accent-dim); color: var(--accent); font-weight: 600; }
.nav-num { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); }
.nav-icon { font-size: 14px; }
.nav-item.active .nav-num { color: var(--accent); }

/* 一级分组与二级子菜单 */
.nav-group { display: flex; flex-direction: column; gap: 2px; }
.nav-group-header { cursor: pointer; user-select: none; }
.nav-group-header .nav-label { flex: 1; }
.nav-badge { font-size: 9px; background: var(--bg-3); color: var(--accent); padding: 1px 5px; border-radius: 10px; border: 1px solid var(--border); font-weight: 600; }
.group-caret { font-size: 9px; color: var(--text-3); margin-left: 4px; transition: transform 0.2s; }

.sub-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-left: 14px;
  margin: 2px 0 4px 14px;
  border-left: 1px dashed var(--border-strong);
}

.sub-nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 6px 8px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: var(--text-2);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
}
.sub-nav-item:hover { background: var(--bg-2); color: var(--text-0); transform: translateX(2px); }
.sub-nav-item.active { background: var(--accent-dim); color: var(--accent); }

.sub-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--border-strong); flex-shrink: 0; }
.sub-nav-item.active .sub-dot { background: var(--accent); box-shadow: 0 0 6px var(--accent); }
.sub-num { font-family: var(--font-mono); font-size: 9px; color: var(--text-3); }
.sub-icon { font-size: 12px; }
.sub-info { display: flex; flex-direction: column; gap: 1px; flex: 1; min-width: 0; }
.sub-label { font-size: 11px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: var(--text-1); }
.sub-nav-item.active .sub-label { color: var(--accent); font-weight: 600; }
.sub-type { font-size: 9px; color: var(--text-3); }

/* 侧边栏脚部 */
.sidebar-footer { border-top: 1px solid var(--border); padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; }

.personalization-panel {
  padding: 12px; background: var(--bg-2); border-radius: 8px;
  margin-bottom: 6px; border: 1px solid var(--border); display: flex; flex-direction: column; gap: 8px;
}
.settings-title { font-size: 11px; color: var(--text-2); font-weight: 600; }
.theme-toggles { display: flex; gap: 6px; }
.theme-btn {
  flex: 1; padding: 5px 0; border-radius: 4px; border: 1px solid var(--border);
  background: var(--bg-1); color: var(--text-1); font-size: 11px; cursor: pointer; transition: all 0.15s;
}
.theme-btn.active { border-color: var(--accent); color: var(--accent); background: var(--accent-dim); }

.accent-toggles { display: flex; justify-content: space-between; align-items: center; }
.accent-label { font-size: 11px; color: var(--text-3); }
.dots-wrap { display: flex; gap: 8px; }
.color-dot {
  width: 18px; height: 18px; border-radius: 50%; border: 2px solid transparent;
  background: var(--dot-color); cursor: pointer; transition: transform 0.2s;
}
.color-dot:hover { transform: scale(1.15); }
.color-dot.active { border-color: var(--text-0); box-shadow: 0 0 0 2px var(--bg-1), 0 0 0 4px var(--dot-color); }

.update-info { display: flex; justify-content: space-between; font-family: var(--font-mono); font-size: 10px; color: var(--accent); }
.recalc-info { font-family: var(--font-mono); font-size: 10px; color: var(--text-3); text-align: right; }

/* 数据源信息卡片 (左下角核心展示) */
.data-source-card {
  background: var(--bg-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  transition: border-color 0.2s, background 0.2s;
}
.data-source-card:hover {
  border-color: var(--border-strong);
}
.ds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
  padding-bottom: 4px;
}
.ds-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--text-0);
  display: flex;
  align-items: center;
  gap: 4px;
}
.ds-status-badge {
  font-size: 9px;
  font-family: var(--font-mono);
  padding: 1px 5px;
  border-radius: 4px;
}
.ds-status-badge.active {
  background: rgba(74, 222, 128, 0.15);
  color: var(--good);
  font-weight: 600;
}
.ds-status-badge.standby {
  background: var(--bg-3);
  color: var(--text-3);
}

.ds-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ds-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
}
.ds-key {
  color: var(--text-3);
}
.ds-val {
  color: var(--text-1);
}
.ds-val.font-bold {
  font-weight: 600;
}
.ds-val.accent {
  color: var(--accent);
}
.ds-val.good {
  color: var(--good);
}
.ds-val.warn {
  color: var(--warn);
}
.ds-val.danger {
  color: var(--danger);
}

.project-actions { display: flex; gap: 6px; }
.btn-sm { padding: 6px 10px; font-size: 12px; }
.icon-btn { flex: 0 0 auto; padding: 6px 8px; }
.icon-btn.active { border-color: var(--accent); background: var(--accent-dim); }

.disclaimer { font-size: 11px; color: var(--text-3); cursor: pointer; text-align: center; padding: 2px; }
.disclaimer:hover { color: var(--warn); }

/* 拉伸器 */
.resizer {
  width: 5px;
  background: transparent;
  cursor: col-resize;
  z-index: 20;
  transition: background 0.2s;
  flex-shrink: 0;
}
.resizer:hover, .resizer:active { background: var(--accent); }

/* 主区域 */
.content { flex: 1; overflow-y: auto; padding: 0; display: flex; flex-direction: column; background: var(--bg-0); }
.top-nav {
  padding: 10px 28px; border-bottom: 1px solid var(--border);
  background: var(--bg-1); display: flex; justify-content: space-between; align-items: center;
}
.breadcrumbs { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-2); font-weight: 500; }
.bc-home { cursor: pointer; transition: color 0.15s; font-weight: 600; }
.bc-home:hover { color: var(--accent); }
.bc-slash { color: var(--text-3); font-size: 12px; }
.bc-ticker { font-weight: 700; }
.bc-price { margin-left: 12px; font-family: var(--font-mono); font-size: 12px; color: var(--text-0); background: var(--bg-2); padding: 2px 8px; border-radius: 4px; }

.top-actions { display: flex; align-items: center; gap: 10px; }


.view-transition { padding: 24px 28px; animation: fade-in 0.25s ease-out; }

@keyframes fade-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

.error-banner { background: rgba(239, 68, 68, 0.1); border-left: 4px solid var(--danger); padding: 12px 16px; margin: 20px 28px 0; border-radius: 4px; }
.error-title { font-size: 13px; font-weight: 600; color: var(--danger); margin-bottom: 2px; }
.error-desc { font-size: 12px; color: var(--text-1); }

.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 14px; padding: 40px; }
.spinner { width: 44px; height: 44px; border: 3px solid var(--border-strong); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-title { font-size: 16px; font-weight: 600; color: var(--text-0); }
.loading-desc { font-size: 12px; color: var(--text-3); }

/* 欢迎 Hub */
.welcome-hub { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; padding: 40px 24px; text-align: center; }
.welcome-header { max-width: 600px; margin-bottom: 32px; }
.welcome-icon { font-size: 48px; margin-bottom: 12px; }
.welcome-title { font-size: 26px; font-weight: 800; color: var(--text-0); margin-bottom: 8px; }
.welcome-sub { font-size: 14px; color: var(--text-2); line-height: 1.6; }

/* 首页 Hero 主搜索框 */
.hero-search-container {
  max-width: 860px;
  width: 100%;
  margin: 0 auto 36px auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.hero-market-tabs {
  display: flex;
  background: var(--bg-1);
  padding: 4px;
  border-radius: 24px;
  border: 1px solid var(--border);
  gap: 4px;
}

.hero-tab-btn {
  background: transparent;
  border: none;
  color: var(--text-2);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.hero-tab-btn:hover {
  color: var(--text-0);
  background: var(--bg-2);
}

.hero-tab-btn.active {
  background: var(--accent);
  color: #fff;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
}

.hero-search-bar-wrap {
  position: relative;
  width: 100%;
  display: flex;
  align-items: center;
  background: var(--bg-1);
  border: 2px solid var(--border-strong);
  border-radius: 32px;
  padding: 6px 8px 6px 20px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  transition: all 0.25s ease;
}

.hero-search-bar-wrap:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 4px rgba(56, 189, 248, 0.15), 0 10px 30px rgba(0, 0, 0, 0.2);
}

.hero-search-icon {
  font-size: 20px;
  color: var(--text-3);
  margin-right: 12px;
}

.hero-search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 15px;
  color: var(--text-0);
  font-family: inherit;
}

.hero-search-input::placeholder {
  color: var(--text-3);
  font-size: 14px;
}

.hero-clear-btn {
  background: transparent;
  border: none;
  color: var(--text-3);
  font-size: 14px;
  cursor: pointer;
  padding: 6px 10px;
  border-radius: 50%;
  transition: color 0.15s;
}

.hero-clear-btn:hover {
  color: var(--text-0);
}

.hero-submit-btn {
  background: var(--accent);
  color: #fff;
  border: none;
  border-radius: 24px;
  padding: 10px 22px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
}

.hero-submit-btn:hover:not(:disabled) {
  opacity: 0.92;
  transform: translateY(-1px);
}

.hero-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 首页联想下拉菜单 */
.hero-search-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: var(--bg-1);
  border: 1px solid var(--border-strong);
  border-radius: 12px;
  box-shadow: 0 14px 35px rgba(0, 0, 0, 0.3);
  max-height: 380px;
  overflow-y: auto;
  z-index: 50;
  text-align: left;
}

.hero-dropdown-header {
  display: flex;
  justify-content: space-between;
  padding: 10px 16px;
  background: var(--bg-2);
  border-bottom: 1px solid var(--border);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-2);
}

.hero-dropdown-tip {
  color: var(--text-3);
  font-weight: 400;
}

.hero-dropdown-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 11px 16px;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.15s;
}

.hero-dropdown-item:last-child {
  border-bottom: none;
}

.hero-dropdown-item:hover,
.hero-dropdown-item.active {
  background: var(--bg-2);
}

.hero-item-main {
  display: flex;
  align-items: center;
  gap: 10px;
}

.hero-item-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-0);
}

.hero-item-ticker {
  font-size: 12px;
  color: var(--accent);
  background: var(--bg-3);
  padding: 2px 6px;
  border-radius: 4px;
}

.hero-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.hero-item-sector {
  font-size: 11px;
  color: var(--text-3);
}

.hero-item-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 7px;
  border-radius: 4px;
}

/* 热门标的标签条 */
.hero-hot-tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 4px;
}

.hero-hot-label {
  font-size: 12px;
  color: var(--text-3);
  font-weight: 500;
}

.hero-hot-tag {
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-1);
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.hero-hot-tag:hover {
  background: var(--bg-2);
  border-color: var(--accent);
  color: var(--accent);
  transform: translateY(-1px);
}

.hot-badge-hk {
  background: rgba(239, 68, 68, 0.12);
  color: #f87171;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
}

.hot-badge-cn {
  background: rgba(245, 158, 11, 0.12);
  color: #fbbf24;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
}

.hot-badge-us {
  background: rgba(59, 130, 246, 0.12);
  color: #60a5fa;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
}


.welcome-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; max-width: 860px; width: 100%; margin-bottom: 30px; }
.welcome-card {
  background: var(--bg-1); border: 1px solid var(--border); border-radius: 10px; padding: 20px;
  text-align: left; cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; gap: 8px;
}
.welcome-card:hover { transform: translateY(-3px); border-color: var(--accent); box-shadow: var(--shadow-md); }
.wc-badge { font-size: 10px; color: var(--accent); font-weight: 600; text-transform: uppercase; }
.wc-name { font-size: 15px; font-weight: 700; color: var(--text-0); }
.wc-desc { font-size: 12px; color: var(--text-3); line-height: 1.5; flex: 1; }
.wc-action { font-size: 12px; font-weight: 600; color: var(--accent); margin-top: 6px; }

.feature-pills { display: flex; gap: 10px; flex-wrap: wrap; justify-content: center; }
.f-pill { padding: 4px 12px; background: var(--bg-1); border: 1px solid var(--border); border-radius: 20px; font-size: 12px; color: var(--text-2); }

/* 弹窗 */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; z-index: 100; }
.modal { background: var(--bg-1); border: 1px solid var(--border-strong); border-radius: 12px; padding: 24px; max-width: 600px; width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: var(--shadow-md); }
.modal-title { font-size: 18px; font-weight: 700; margin-bottom: 16px; color: var(--text-0); }
.modal-empty { color: var(--text-3); text-align: center; padding: 30px; }
.export-all-bar { margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; }
.project-row { display: flex; align-items: center; gap: 8px; padding: 10px 0; border-bottom: 1px solid var(--border); }
.project-info { flex: 1; }
.project-name { font-size: 13px; font-weight: 600; color: var(--text-0); }
.project-meta { font-size: 11px; color: var(--text-3); font-family: var(--font-mono); }
.btn-danger { color: var(--danger); }
.btn-danger:hover { border-color: var(--danger); }
.disclaimer-text { font-size: 13px; color: var(--text-1); line-height: 1.7; }
.disclaimer-text ul { padding-left: 20px; margin-top: 8px; }
.disclaimer-text li { margin-bottom: 6px; }

@media (max-width: 900px) {
  .welcome-cards { grid-template-columns: 1fr; }
}
</style>