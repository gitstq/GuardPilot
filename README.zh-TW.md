<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.zh-TW.md">繁體中文</a> · <a href="README.en.md">English</a>
</p>

<h1 align="center">
  🛡️ GuardPilot
</h1>

<p align="center">
  <strong>輕量級 AI Agent 行為合規規則引擎</strong><br>
  YAML 驅動規則定義 · 零外部依賴 · 多格式合規報告
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Dependencies-Zero-success.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-120%20Passed-brightgreen.svg" alt="120 Tests Passed">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange.svg" alt="v1.0.0">
</p>

---

## 🎉 專案介紹

**GuardPilot** 是一款專為 AI/LLM Agent 設計的**行為合規規則引擎**，幫助開發者在生產環境中確保 Agent 的輸出符合預定義的業務規則和行為準則。

### 💡 靈感來源

隨著 AI Agent 在生產環境中的廣泛應用，Agent 幻覺、指令不遵循、輸出不當內容等問題日益突出。傳統的解決方案依賴於編寫冗長的 system prompt 來「約束」 LLM 的行為，但這種方式脆弱且難以維護。

GuardPilot 從 GitHub Trending 熱門專案 [parlant](https://github.com/emcie-co/parlant) 中汲取靈感，採用**獨立自研**的方式，提供了一種更輕量、更靈活的 Agent 行為合規解決方案。

### 🌟 自研差異化亮點

| 特性 | GuardPilot | 其他方案 |
|------|-----------|---------|
| **部署方式** | 純 CLI，零 GUI 依賴 | 需要完整服務端 |
| **規則定義** | YAML 驅動，簡潔直觀 | Gherkin/複雜 DSL |
| **外部依賴** | 零依賴（僅 Python 標準庫） | 多個第三方庫 |
| **中文支援** | 原生中文規則和報告 | 主要英文 |
| **報告格式** | JSON / HTML / Markdown | 格式有限 |
| **規則衝突** | 自動偵測並告警 | 需手動排查 |

---

## ✨ 核心特性

- 🎯 **YAML 驅動規則定義** — 用簡潔的 YAML 語法定義行為準則，支援關鍵詞、正則、模式匹配、語義相似度等多種匹配方式
- 🔍 **多維度規則匹配** — 支援關鍵詞匹配、正則表達式、模式匹配、長度檢查、語義相似度（Jaccard）
- 📊 **合規評分系統** — 自動計算 0-100 合規評分，Block/Warning/Log 三級違規分級
- 📋 **多格式合規報告** — 支援 JSON、HTML（暗色主題）、Markdown 三種報告格式
- ⚠️ **規則衝突偵測** — 自動偵測規則間的邏輯衝突，避免規則互相矛盾
- 🏷️ **優先級管理** — High/Medium/Low 三級優先級，確保關鍵規則優先執行
- 🌐 **中英文雙語** — 原生支援中文和英文規則定義、終端輸出和合規報告
- 📦 **內建規則預設** — 內建內容安全、回應格式、領域合規、語氣風格四類預設規則
- 🚀 **零外部依賴** — 僅使用 Python 標準庫，無需安裝任何第三方套件
- 🧪 **120 個單元測試** — 完善的測試覆蓋，確保引擎穩定可靠

---

## 🚀 快速開始

### 📋 環境需求

- **Python** >= 3.10（無需安裝任何第三方依賴）

### 🔧 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/GuardPilot.git
cd GuardPilot

# 安裝（開發模式）
pip install -e .
```

### 🎮 使用

```bash
# 1. 初始化範例規則檔案
guardpilot init

# 2. 驗證規則檔案語法
guardpilot validate guardpilot_rules.yaml

# 3. 檢查單條訊息
guardpilot check --rules guardpilot_rules.yaml --message "這是一條測試訊息"

# 4. 檢查完整對話
guardpilot check --rules guardpilot_rules.yaml --conversation example_conversation.json

# 5. 生成合規報告（HTML 格式）
guardpilot report --rules guardpilot_rules.yaml --conversation example_conversation.json --format html

# 6. 查看已載入的規則列表
guardpilot rules list --rules guardpilot_rules.yaml
```

---

## 📖 詳細使用指南

### 📝 規則檔案格式

規則檔案使用 YAML 格式定義，結構如下：

```yaml
rules:
  - id: no-harmful-content
    name: 禁止有害內容
    name_en: No Harmful Content
    description: 偵測並阻止包含有害內容的輸出
    category: content_safety
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value:
          - 暴力
          - 色情
          - 賭博
        negate: false

  - id: max-response-length
    name: 回應長度限制
    name_en: Max Response Length
    description: 限制單條回應的最大字元數
    category: response_format
    priority: medium
    severity: warn
    enabled: true
    conditions:
      - type: length
        value: 2000
        operator: max

  - id: professional-tone
    name: 專業語氣
    name_en: Professional Tone
    description: 確保輸出使用專業、禮貌的語言
    category: tone_style
    priority: low
    severity: log
    enabled: true
    conditions:
      - type: keyword
        value:
          - 哈哈哈
          - 臥槽
          - nb
        negate: true
```

### 🎯 條件類型

| 類型 | 說明 | 範例 |
|------|------|------|
| `keyword` | 關鍵詞匹配 | 偵測特定詞彙是否存在/不存在 |
| `regex` | 正則表達式匹配 | 使用正則偵測模式 |
| `pattern` | 預定義模式匹配 | 信箱、手機號、身分證等 |
| `length` | 長度檢查 | 限制回應最大/最小長度 |
| `custom` | 自訂表達式 | 靈活的自訂匹配邏輯 |

### ⚡ 嚴重級別

| 級別 | 說明 | 扣分 |
|------|------|------|
| `block` | **阻斷級** — 嚴重違規，必須阻止 | -20 分 |
| `warn` | **警告級** — 需要注意的問題 | -10 分 |
| `log` | **記錄級** — 輕微問題，僅記錄 | -5 分 |

### 📊 合規評分

GuardPilot 自動計算 0-100 的合規評分：

- **90-100 (A)**: 🟢 優秀 — 完全合規
- **70-89 (B)**: 🟡 良好 — 存在少量問題
- **50-69 (C)**: 🟠 需改進 — 存在較多問題
- **0-49 (D)**: 🔴 不合格 — 嚴重違規

### 📋 內建規則預設

GuardPilot 內建了四類規則預設，可直接使用：

```bash
# 使用內建規則預設
guardpilot check --rules guardpilot/rules/content_safety.yaml --message "測試訊息"
guardpilot check --rules guardpilot/rules/response_format.yaml --message "測試訊息"
guardpilot check --rules guardpilot/rules/domain_compliance.yaml --message "測試訊息"
guardpilot check --rules guardpilot/rules/tone_style.yaml --message "測試訊息"
```

---

## 💡 設計思路與迭代規劃

### 🏗️ 設計理念

1. **零依賴哲學** — 僅使用 Python 標準庫，降低部署門檻，避免依賴衝突
2. **YAML 驅動** — 規則與程式碼分離，非技術人員也能輕鬆管理規則
3. **漸進式合規** — Block/Warning/Log 三級機制，靈活應對不同場景
4. **開發者友善** — 清晰的 CLI 輸出、豐富的報告格式、完善的錯誤提示

### 🔮 後續迭代計畫

- [ ] **v1.1** — 支援對話上下文感知的規則匹配（跨訊息關聯檢查）
- [ ] **v1.2** — 新增 Web Dashboard 視覺化規則管理介面
- [ ] **v1.3** — 整合 LLM API 進行語義級合規偵測（GPT/Claude/DeepSeek）
- [ ] **v2.0** — 支援規則熱更新和版本管理
- [ ] **v2.1** — 提供 SDK 供其他 Python 專案整合
- [ ] **v2.2** — 新增規則市場，支援社群共享規則模板

---

## 📦 打包與部署指南

### 💻 本地開發

```bash
# 克隆倉庫
git clone https://github.com/gitstq/GuardPilot.git
cd GuardPilot

# 安裝（開發模式）
pip install -e .

# 執行測試
python -m unittest discover -s tests

# 驗證安裝
guardpilot --version
```

### 🐍 作為庫整合

```python
from guardpilot.engine import RuleEngine
from guardpilot.reporter import Reporter

# 載入規則
engine = RuleEngine()
rules = engine.load_rules("guardpilot_rules.yaml")

# 檢查訊息
result = engine.check_message("這是一條測試訊息", rules)

# 生成報告
reporter = Reporter()
print(reporter.generate_markdown(result))
```

### 🐳 Docker 部署

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -e .
ENTRYPOINT ["guardpilot"]
```

### 🔄 CI/CD 整合

```yaml
# GitHub Actions 範例
- name: Compliance Check
  run: |
    guardpilot check --rules rules.yaml --conversation output.json
    guardpilot report --rules rules.yaml --conversation output.json --format json > report.json
```

---

## 🤝 貢獻指南

我們歡迎所有形式的貢獻！請遵循以下步驟：

1. 🍴 Fork 本倉庫
2. 🌿 建立特性分支：`git checkout -b feature/amazing-feature`
3. ✅ 確保所有測試通過：`python -m unittest discover -s tests`
4. 📝 提交變更：`git commit -m "feat: add amazing feature"`
5. 🚀 推送分支：`git push origin feature/amazing-feature`
6. 📮 提交 Pull Request

### 📋 提交規範

請使用 [Angular 提交規範](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)：

- `feat:` 新增功能
- `fix:` 修復問題
- `docs:` 文件更新
- `refactor:` 程式碼重構
- `test:` 測試相關
- `chore:` 建構/工具變更

---

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
