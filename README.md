<p align="center">
  <a href="README.md">简体中文</a> · <a href="README.zh-TW.md">繁體中文</a> · <a href="README.en.md">English</a>
</p>

<h1 align="center">
  🛡️ GuardPilot
</h1>

<p align="center">
  <strong>轻量级 AI Agent 行为合规规则引擎</strong><br>
  YAML 驱动规则定义 · 零外部依赖 · 多格式合规报告
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Dependencies-Zero-success.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-120%20Passed-brightgreen.svg" alt="120 Tests Passed">
  <img src="https://img.shields.io/badge/Version-1.0.0-orange.svg" alt="v1.0.0">
</p>

---

## 🎉 项目介绍

**GuardPilot** 是一款专为 AI/LLM Agent 设计的**行为合规规则引擎**，帮助开发者在生产环境中确保 Agent 的输出符合预定义的业务规则和行为准则。

### 💡 灵感来源

随着 AI Agent 在生产环境中的广泛应用，Agent 幻觉、指令不遵循、输出不当内容等问题日益突出。传统的解决方案依赖于编写冗长的 system prompt 来"约束" LLM 的行为，但这种方式脆弱且难以维护。

GuardPilot 从 GitHub Trending 热门项目 [parlant](https://github.com/emcie-co/parlant) 中汲取灵感，采用**独立自研**的方式，提供了一种更轻量、更灵活的 Agent 行为合规解决方案。

### 🌟 自研差异化亮点

| 特性 | GuardPilot | 其他方案 |
|------|-----------|---------|
| **部署方式** | 纯 CLI，零 GUI 依赖 | 需要完整服务端 |
| **规则定义** | YAML 驱动，简洁直观 | Gherkin/复杂 DSL |
| **外部依赖** | 零依赖（仅 Python 标准库） | 多个第三方库 |
| **中文支持** | 原生中文规则和报告 | 主要英文 |
| **报告格式** | JSON / HTML / Markdown | 格式有限 |
| **规则冲突** | 自动检测并告警 | 需手动排查 |

---

## ✨ 核心特性

- 🎯 **YAML 驱动规则定义** — 用简洁的 YAML 语法定义行为准则，支持关键词、正则、模式匹配、语义相似度等多种匹配方式
- 🔍 **多维度规则匹配** — 支持关键词匹配、正则表达式、模式匹配、长度检查、语义相似度（Jaccard）
- 📊 **合规评分系统** — 自动计算 0-100 合规评分，Block/Warning/Log 三级违规分级
- 📋 **多格式合规报告** — 支持 JSON、HTML（暗色主题）、Markdown 三种报告格式
- ⚠️ **规则冲突检测** — 自动检测规则间的逻辑冲突，避免规则互相矛盾
- 🏷️ **优先级管理** — High/Medium/Low 三级优先级，确保关键规则优先执行
- 🌐 **中英文双语** — 原生支持中文和英文规则定义、终端输出和合规报告
- 📦 **内置规则预设** — 内置内容安全、响应格式、领域合规、语气风格四类预设规则
- 🚀 **零外部依赖** — 仅使用 Python 标准库，无需安装任何第三方包
- 🧪 **120 个单元测试** — 完善的测试覆盖，确保引擎稳定可靠

---

## 🚀 快速开始

### 📋 环境要求

- **Python** >= 3.10（无需安装任何第三方依赖）

### 🔧 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/GuardPilot.git
cd GuardPilot

# 安装（开发模式）
pip install -e .
```

### 🎮 使用

```bash
# 1. 初始化示例规则文件
guardpilot init

# 2. 验证规则文件语法
guardpilot validate guardpilot_rules.yaml

# 3. 检查单条消息
guardpilot check --rules guardpilot_rules.yaml --message "这是一条测试消息"

# 4. 检查完整对话
guardpilot check --rules guardpilot_rules.yaml --conversation example_conversation.json

# 5. 生成合规报告（HTML 格式）
guardpilot report --rules guardpilot_rules.yaml --conversation example_conversation.json --format html

# 6. 查看已加载的规则列表
guardpilot rules list --rules guardpilot_rules.yaml
```

---

## 📖 详细使用指南

### 📝 规则文件格式

规则文件使用 YAML 格式定义，结构如下：

```yaml
rules:
  - id: no-harmful-content
    name: 禁止有害内容
    name_en: No Harmful Content
    description: 检测并阻止包含有害内容的输出
    category: content_safety
    priority: high
    severity: block
    enabled: true
    conditions:
      - type: keyword
        value:
          - 暴力
          - 色情
          - 赌博
        negate: false

  - id: max-response-length
    name: 响应长度限制
    name_en: Max Response Length
    description: 限制单条响应的最大字符数
    category: response_format
    priority: medium
    severity: warn
    enabled: true
    conditions:
      - type: length
        value: 2000
        operator: max

  - id: professional-tone
    name: 专业语气
    name_en: Professional Tone
    description: 确保输出使用专业、礼貌的语言
    category: tone_style
    priority: low
    severity: log
    enabled: true
    conditions:
      - type: keyword
        value:
          - 哈哈哈
          - 卧槽
          - nb
        negate: true
```

### 🎯 条件类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `keyword` | 关键词匹配 | 检测特定词汇是否存在/不存在 |
| `regex` | 正则表达式匹配 | 使用正则检测模式 |
| `pattern` | 预定义模式匹配 | 邮箱、手机号、身份证等 |
| `length` | 长度检查 | 限制响应最大/最小长度 |
| `custom` | 自定义表达式 | 灵活的自定义匹配逻辑 |

### ⚡ 严重级别

| 级别 | 说明 | 扣分 |
|------|------|------|
| `block` | **阻断级** — 严重违规，必须阻止 | -20 分 |
| `warn` | **警告级** — 需要注意的问题 | -10 分 |
| `log` | **记录级** — 轻微问题，仅记录 | -5 分 |

### 📊 合规评分

GuardPilot 自动计算 0-100 的合规评分：

- **90-100 (A)**: 🟢 优秀 — 完全合规
- **70-89 (B)**: 🟡 良好 — 存在少量问题
- **50-69 (C)**: 🟠 需改进 — 存在较多问题
- **0-49 (D)**: 🔴 不合格 — 严重违规

### 📋 内置规则预设

GuardPilot 内置了四类规则预设，可直接使用：

```bash
# 使用内置规则预设
guardpilot check --rules guardpilot/rules/content_safety.yaml --message "测试消息"
guardpilot check --rules guardpilot/rules/response_format.yaml --message "测试消息"
guardpilot check --rules guardpilot/rules/domain_compliance.yaml --message "测试消息"
guardpilot check --rules guardpilot/rules/tone_style.yaml --message "测试消息"
```

---

## 💡 设计思路与迭代规划

### 🏗️ 设计理念

1. **零依赖哲学** — 仅使用 Python 标准库，降低部署门槛，避免依赖冲突
2. **YAML 驱动** — 规则与代码分离，非技术人员也能轻松管理规则
3. **渐进式合规** — Block/Warning/Log 三级机制，灵活应对不同场景
4. **开发者友好** — 清晰的 CLI 输出、丰富的报告格式、完善的错误提示

### 🔮 后续迭代计划

- [ ] **v1.1** — 支持对话上下文感知的规则匹配（跨消息关联检查）
- [ ] **v1.2** — 添加 Web Dashboard 可视化规则管理界面
- [ ] **v1.3** — 集成 LLM API 进行语义级合规检测（GPT/Claude/DeepSeek）
- [ ] **v2.0** — 支持规则热更新和版本管理
- [ ] **v2.1** — 提供 SDK 供其他 Python 项目集成
- [ ] **v2.2** — 添加规则市场，支持社区共享规则模板

---

## 📦 打包与部署指南

### 💻 本地开发

```bash
# 克隆仓库
git clone https://github.com/gitstq/GuardPilot.git
cd GuardPilot

# 安装（开发模式）
pip install -e .

# 运行测试
python -m unittest discover -s tests

# 验证安装
guardpilot --version
```

### 🐍 作为库集成

```python
from guardpilot.engine import RuleEngine
from guardpilot.reporter import Reporter

# 加载规则
engine = RuleEngine()
rules = engine.load_rules("guardpilot_rules.yaml")

# 检查消息
result = engine.check_message("这是一条测试消息", rules)

# 生成报告
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

### 🔄 CI/CD 集成

```yaml
# GitHub Actions 示例
- name: Compliance Check
  run: |
    guardpilot check --rules rules.yaml --conversation output.json
    guardpilot report --rules rules.yaml --conversation output.json --format json > report.json
```

---

## 🤝 贡献指南

我们欢迎所有形式的贡献！请遵循以下步骤：

1. 🍴 Fork 本仓库
2. 🌿 创建特性分支：`git checkout -b feature/amazing-feature`
3. ✅ 确保所有测试通过：`python -m unittest discover -s tests`
4. 📝 提交变更：`git commit -m "feat: add amazing feature"`
5. 🚀 推送分支：`git push origin feature/amazing-feature`
6. 📮 提交 Pull Request

### 📋 提交规范

请使用 [Angular 提交规范](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#commit)：

- `feat:` 新增功能
- `fix:` 修复问题
- `docs:` 文档更新
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具变更

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/gitstq">gitstq</a>
</p>
