# 🧭 Memory Compass - 记忆罗盘

> **「在数字沧海中，找到你的方向」**  
> Navigate your way through the digital sea.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-green.svg)](https://github.com/openclaw/skills)
[![Python](https://img.shields.io/badge/Python-3.7+-yellow.svg)](https://python.org)
[![Version](https://img.shields.io/badge/Version-1.0.0-orange.svg)](UPDATES.md)

---

## 🌟 简介

`memory-compass` 是一个**三层混合记忆系统**，专为 AI Agent 设计的持久化、可搜索、可恢复的记忆管理能力。

**核心特性：**
- ✅ **LanceDB 向量记忆库** - 高速语义搜索（O(log n)）
- ✅ **文件系统 WAL 协议** - 关键信息立即固化
- ✅ **任务续传系统** - API 中断后秒级恢复上下文
- ✅ **统一查询接口** - 自动路由到最佳存储轨道

---

## ⚡ 快速开始

### Python API

```python
from skills.memory_compass import MemoryCompass

compass = MemoryCompass()

# 保存检查点
checkpoint = compass.save_checkpoint(mode="auto")

# 恢复检查点
recovered = compass.recover_checkpoint(latest=True)

# 搜索记忆
results = compass.find_memory("图像生成任务进度", top_k=5)

# 获取完整上下文
context = compass.get_context(days_back=7)
```

### CLI 命令行工具

```bash
cd skills/memory-compass

# 保存检查点
python memory_compass_cli.py save --mode auto --message "任务描述"

# 列出检查点
python memory_compass_cli.py list --days 7

# 恢复检查点
python memory_compass_cli.py restore

# 清理过期数据
python memory_compass_cli.py cleanup --keep 7
```

---

## 🏗️ 架构设计

### 三层混合架构

```
┌─────────────────────────────────────────┐
│          用户输入/对话事件                │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      【轨道 A: LanceDB 自动捕获】          │
│  └─ ml.capture({                       │
│       content: "对话内容",               │
│       type: "conversation"              │
│     })                                  │
│  ✅ 高速存储，可语义搜索                  │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      【轨道 B: 文件系统 WAL 协议】           │
│  └─ write_to("SESSION-STATE.md", ...)  │
│  ✅ 关键信息立即固化                     │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│      【轨道 C: 定时检查点】               │
│  └─ save-checkpoint.ps1                │
│  ✅ 15min/45min 自动保存                 │
└─────────────────────────────────────────┘
```

---

## 📊 性能指标

| 操作 | 耗时 | 说明 |
|------|------|------|
| **保存检查点** | < 0.5 秒 | JSON 序列化 + 文件写入 |
| **恢复检查点** | < 0.1 秒 | JSON 解析 |
| **关键词搜索** | < 0.2 秒 | 文件系统线性扫描 |
| **向量搜索** | O(log n) | LanceDB 索引查找 |

---

## 📦 安装

### 方式一：NPM (推荐)

```bash
npx skills install winde/memory-compass
```

### 方式二：手动复制

```bash
git clone https://github.com/winde/memory-compass.git
cp -r memory-compass ~/.openclaw/workspace/skills/
```

### 方式三：依赖安装

```bash
cd memory-compass
pip install -r requirements.txt
```

---

## 📂 目录结构

```
memory-compass/
├── SKILL.md                       ← 官方文档
├── README.md                      ← 本文件
├── LICENSE                        ← MIT 许可证
├── package.json                   ← NPM 配置
├── memory_compass_cli.py         ← CLI 工具
├── src/
│   ├── __init__.py              ← MemoryCompass 主类
│   ├── core/
│   │   ├── lance_db.py          ← LanceDB 接口
│   │   ├── file_system.py       ← 文件系统 WAL
│   │   └── unified_search.py    ← 统一搜索
│   └── checkpoints/             ← （待实现）
├── tests/                        ← 单元测试
└── examples/                     ← 使用示例
    ├── basic_usage.py
    └── full_demo.py
```

---

## 🎯 典型用例

### 1. 自动保存检查点（心跳前）

```python
result = compass.save_checkpoint(mode="auto")
print(f"已保存：{result['file']}")
```

### 2. 断网后恢复任务

```python
recovered = compass.recover_checkpoint(latest=True)
if recovered["success"]:
    print(f"恢复了 {recovered['data']['timestamp']} 的检查点")
else:
    print("未找到可用的检查点")
```

### 3. 智能搜索历史对话

```python
results = compass.find_memory(
    query="上次我们讨论的图像生成方案是什么？",
    top_k=10,
    strategy="hybrid"
)

for r in results:
    print(f"[{r['source']}] {r['matched_line'][:80]}...")
```

---

## 🔧 Cron Job 集成

### 高频快照 (每 15 分钟)

```json
{
  "name": "memory-compass-snapshot-high",
  "schedule": {"kind": "every", "everyMs": 900000},
  "payload": {
    "kind": "systemEvent",
    "text": "python memory_compass_cli.py save --mode auto --message \"高频心跳\""
  }
}
```

### 低频快照 (每 45 分钟)

```json
{
  "name": "memory-compass-snapshot-low",
  "schedule": {"kind": "every", "everyMs": 2700000},
  "payload": {
    "kind": "systemEvent",
    "text": "python memory_compass_cli.py save --mode auto --message \"低频心跳\""
  }
}
```

### 每周清理 (周日 9:00)

```json
{
  "name": "memory-compass-weekly-cleanup",
  "schedule": {"kind": "cron", "expr": "0 9 * * 0", "tz": "Asia/Shanghai"},
  "payload": {
    "kind": "systemEvent",
    "text": "./cleanup-old-checkpoints.ps1 -KeepDays 7"
  }
}
```

---

## 🛠️ 开发指南

### 运行示例

```bash
python examples/basic_usage.py
python examples/full_demo.py
```

### 运行测试

```bash
pytest tests/
```

### 贡献代码

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. Push 到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 👥 致谢

感谢以下开源项目：
- [LanceDB](https://lancedb.ai/) - 向量数据库
- [Jina AI](https://jina.ai/) - Embedding & Rerank 模型
- [OpenClaw](https://openclaw.ai/) - Agent 框架

---

## 🙋‍♂️ 支持

遇到问题或有建议？

- 💬 在 GitHub 上创建 Issue
- 📧 联系作者：Winde (沧海一粟 AI COO)
- 📖 查看文档：[SKILL.md](SKILL.md)

---

**作者**: Winde (沧海一粟 AI COO)  
**版本**: v1.0.0  
**最后更新**: 2026-03-17  

⭐ **如果这个项目对你有帮助，请给一个 Star!**
