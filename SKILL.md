# Memory Compass - 记忆罗盘 ⭐⭐⭐⭐⭐

> **「在数字沧海中，找到你的方向」**
> Navigate your way through the digital sea.

---

## 📖 简介

`memory-compass` 是一个**三层混合记忆系统**，为 AI Agent 提供持久化、可搜索、可恢复的记忆管理能力。

**核心特性：**
- ✅ **LanceDB 向量记忆库** - 高速语义搜索（O(log n)）
- ✅ **文件系统 WAL 协议** - 关键信息立即固化
- ✅ **任务续传系统** - API 中断后秒级恢复上下文
- ✅ **统一查询接口** - 自动路由到最佳存储轨道

---

## 🔧 安装

```bash
# NPM 安装（开发版）
cd ~/AppData/Roaming/npm/node_modules
git clone https://github.com/winde/memory-compass.git skills/memory-compass
npm install --prefix skills/memory-compass

# 或者手动复制到 workspace
cp -r skills/memory-compass ~/.openclaw/workspace/skills/
```

---

## 🚀 快速开始

### Python API 使用

```python
from skills.memory_compass import MemoryCompass

# 初始化
compass = MemoryCompass()

# 1. 保存检查点
checkpoint = compass.save_checkpoint(mode="auto")

# 2. 恢复检查点
recovered = compass.recover_checkpoint(latest=True)

# 3. 搜索记忆
results = compass.find_memory(
    query="上次画图的任务进度",
    top_k=5
)

# 4. 获取完整上下文
context = compass.navigate_context(days_back=7)

# 5. 清理过期数据
report = compass.cleanup_old_checkpoints(keep_days=7)
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

## 📦 模块说明

### `src/core/` - 核心模块

| 文件 | 功能 | 状态 |
|------|------|------|
| `lance_db.py` | LanceDB 接口封装 | ✅ |
| `file_system.py` | 文件系统操作（WAL） | ✅ |
| `unified_search.py` | 统一查询入口 | ✅ |

### `src/checkpoints/` - 检查点管理

| 文件 | 功能 | 状态 |
|------|------|------|
| `save.py` | 保存检查点 | ✅ |
| `recover.py` | 恢复检查点 | ✅ |
| `cleanup.py` | 清理过期数据 | ✅ |

### `tests/` - 单元测试

- `test_lancedb_integration.py`
- `test_checkpoint_recovery.py`
- `test_unified_search.py`

### `examples/` - 使用示例

- `basic_usage.py` - 基础用法
- `checkpoint_recovery.py` - 断点续传演示
- `hybrid_architecture.py` - 三层架构协同

---

## 🎯 高级用法

### 智能降级策略

```python
results = compass.find_memory(
    query="图像生成失败的原因",
    strategy="hybrid"  # lance_db -> file_system -> checkpoints
)
```

### 跨会话上下文迁移

```python
# 导出旧会话记忆
old_memories = compass.export_session(session_key="agent:main:main")

# 导入到新会话
compass.import_memories(old_memories)
```

### 定期整理记忆

```python
# 每周压缩 LanceDB 中重要的对话
compass.compress_memories(
    filter_type="important",
    target_file="memory/MEMORY.md"
)
```

---

## 🛠️ PowerShell 工具脚本

### 保存检查点

```powershell
# 位置：ai-company/scripts/save-checkpoint.ps1
. .\scripts\save-checkpoint.ps1 -Mode "auto"
. .\scripts\save-checkpoint.ps1 -Mode "manual"
```

### 恢复检查点

```powershell
# 列出所有检查点
.\scripts\recover-from-checkpoint.ps1

# 恢复最近一次
.\scripts\recover-from-checkpoint.ps1 -Latest

# 恢复指定日期
.\scripts\recover-from-checkpoint.ps1 -Date "20260317_065132"
```

### 清理过期检查点

```powershell
# 保留最近 7 天的检查点
.\scripts\cleanup-old-checkpoints.ps1 -KeepDays 7
```

---

## 📊 配置参数

### `config.json` (可选)

```json
{
  "lancedb": {
    "api_provider": "jina-ai",
    "embedding_model": "jina-embeddings-v5-text-small",
    "dimensions": 1024,
    "rerank_model": "jina-reranker-v3"
  },
  "checkpoints": {
    "high_frequency_minutes": 15,
    "low_frequency_minutes": 45,
    "keep_days": 7
  },
  "wal": {
    "session_state_file": "SESSION-STATE.md",
    "memory_file": "MEMORY.md",
    "working_buffer_file": "memory/working-buffer.md"
  }
}
```

---

## 🔍 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **检索速度** | O(log n) | LanceDB 索引查找 |
| **保存耗时** | < 1s | 本地写入无网络延迟 |
| **存储容量** | TB 级 | LanceDB 支持 |
| **并发支持** | 多会话 | 独立 Session Key |

---

## 📈 路线图

### v1.0.0 (当前版本)

- ✅ 三层混合架构实现
- ✅ LanceDB + 文件系统
- ✅ 检查点保存/恢复
- ✅ 统一查询接口

### v1.1.0 (待规划)

- [ ] 添加 Web UI 管理界面
- [ ] 支持更多存储后端（MongoDB, PostgreSQL）
- [ ] 智能记忆压缩算法
- [ ] 自动化测试覆盖率 > 80%

### v2.0.0 (未来愿景)

- [ ] 分布式记忆网络（多实例同步）
- [ ] 联邦学习集成
- [ ] 情感记忆分析
- [ ] 跨平台记忆桥接

---

## 👨‍💻 贡献指南

欢迎提交 Issue 和 Pull Request！

**开发环境设置：**

```bash
# 进入技能目录
cd skills/memory-compass

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/

# 运行示例
python examples/basic_usage.py
```

---

## 📄 许可证

MIT License

---

## 🙏 致谢

感谢以下开源项目：
- [LanceDB](https://lancedb.ai/) - 向量数据库
- [Jina AI](https://jina.ai/) - Embedding & Rerank 模型
- [OpenClaw](https://openclaw.ai/) - Agent 框架

---

**最后更新：** 2026-03-17  
**作者：** Winde (沧海一粟 AI COO)  
**版本：** v1.0.0
