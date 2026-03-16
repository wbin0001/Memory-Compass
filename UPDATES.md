# Memory Compass - 更新日志

## v1.0.0 (2026-03-17) ⭐ 初始发布

### ✨ 新增功能

#### 核心功能
- ✅ **三层混合记忆架构**
  - LanceDB 向量记忆库 (高速语义搜索)
  - 文件系统 WAL 协议 (关键信息固化)
  - 检查点系统 (任务断点续传)

- ✅ **统一查询接口** (`UnifiedSearch`)
  - 自动路由到最佳存储轨道
  - Hybrid Search (LanceDB + 文件系统)
  - 去重和排名算法

- ✅ **CLI 命令行工具** (`memory_compass_cli.py`)
  ```bash
  python memory_compass_cli.py save --mode auto --message "xxx"
  python memory_compass_cli.py list --days 7
  python memory_compass_cli.py restore
  python memory_compass_cli.py cleanup --keep 7
  ```

- ✅ **PowerShell 工具脚本**
  - `save-checkpoint.ps1` - 保存会话检查点
  - `recover-from-checkpoint.ps1` - 恢复检查点
  - `cleanup-old-checkpoints.ps1` - 清理过期数据

#### 核心模块
| 文件 | 功能 | 大小 |
|------|------|------|
| `src/core/lance_db.py` | LanceDB 接口封装 | 4,805 bytes |
| `src/core/file_system.py` | 文件系统 WAL 协议 | 6,221 bytes |
| `src/core/unified_search.py` | 统一查询入口 | 8,686 bytes |
| `src/__init__.py` | MemoryCompass 主类 | 6,705 bytes |

#### 文档与示例
| 文件 | 说明 |
|------|------|
| `SKILL.md` | 官方 API 文档 |
| `README.md` | 快速参考手册 |
| `examples/basic_usage.py` | 基础用法演示 |
| `examples/full_demo.py` | 完整场景演示 |

---

## 🎯 集成建议

### 1. 心跳流程集成

**修改 `ai-company/scripts/heartbeat-brief.ps1`:**

```powershell
# 在发送简报前添加：
cd $WorkspaceRoot\skills\memory-compass
python memory_compass_cli.py save --mode auto --message "心跳简报完成"
```

### 2. Cron Job 配置

**高频检查点 (15 分钟):**
```json
{
  "name": "session-snapshot-high-frequency",
  "schedule": {"kind": "every", "everyMs": 900000},
  "payload": {
    "kind": "agentTurn",
    "message": "调用 memory-compsss CLI 保存检查点"
  },
  "sessionTarget": "isolated"
}
```

### 3. API 使用示例

```python
from skills.memory_compass import MemoryCompass

compass = MemoryCompass()

# 1. 保存检查点
checkpoint = compass.save_checkpoint(mode="auto")

# 2. 恢复检查点
recovered = compass.recover_checkpoint(latest=True)

# 3. 搜索记忆
results = compass.find_memory("图像生成任务进度", top_k=5)

# 4. 获取上下文
context = compass.get_context(days_back=7)
```

---

## 📊 性能基准

| 操作 | 耗时 | 说明 |
|------|------|------|
| **保存检查点** | < 0.5 秒 | JSON 序列化 + 文件写入 |
| **恢复检查点** | < 0.1 秒 | JSON 解析 |
| **关键词搜索** | < 0.2 秒 | 文件系统线性扫描 |
| **向量搜索** | O(log n) | LanceDB 索引查找 |
| **清理过期** | < 1 秒 | 批量删除文件 |

---

## 🔜 后续计划

### v1.1.0 (待规划)
- [ ] Web UI 管理界面
- [ ] MongoDB / PostgreSQL 后端支持
- [ ] 智能记忆压缩算法
- [ ] 单元测试覆盖率 > 80%

### v2.0.0 (未来愿景)
- [ ] 分布式记忆网络（多实例同步）
- [ ] 联邦学习集成
- [ ] 情感记忆分析
- [ ] 跨平台记忆桥接

---

## 👨‍💻 贡献者

**作者**: Winde (沧海一粟 AI COO)  
**版本**: v1.0.0  
**日期**: 2026-03-17  
**许可证**: MIT

---

*在数字沧海中，找到你的方向* 🧭🌊
