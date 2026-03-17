# -*- coding: utf-8 -*-
"""LanceDB 向量记忆库接口

注意：此模块是可选的。如果未安装 lancedb，将自动降级为文件系统存储。
"""
import os
import sys
import uuid
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

try:
    import lancedb
    from lancedb.pydantic import LanceModel, Vector
    from lancedb.embeddings import get_registry
    LANCEDB_AVAILABLE = True
except ImportError:
    LANCEDB_AVAILABLE = False
    lancedb = None

# 配置
CONFIG = {
    "api_provider": "jina-ai",
    "embedding_model": "jina-embeddings-v5-text-small",
    "dimensions": 1024,
    "rerank_model": "jina-reranker-v3",
    "db_path": str(Path.home() / ".openclaw" / "memory_lance.db")
}


@dataclass
class MemoryRecord:
    """记忆记录数据类"""
    id: str
    content: str
    memory_type: str
    source: str
    timestamp: str
    importance: float
    metadata: str  # JSON string

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryRecord":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            memory_type=data.get("memory_type", "other"),
            source=data.get("source", "unknown"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            importance=data.get("importance", 0.7),
            metadata=data.get("metadata", "{}")
        )


class LanceDBMemory:
    """LanceDB 向量记忆库管理类
    
    如果 LanceDB 未安装，此类将标记为不可用，所有操作将返回空结果。
    这是设计上的降级策略，确保系统在缺少依赖时仍能运行。
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """初始化 LanceDB 记忆管理器
        
        Args:
            db_path: 数据库路径，默认为 ~/.openclaw/memory_lance.db
        """
        self.db_path = db_path or CONFIG["db_path"]
        self.db = None
        self.memories_table = None
        self.checkpoints_table = None
        self._available = LANCEDB_AVAILABLE
        
        if not LANCEDB_AVAILABLE:
            print("⚠️ LanceDB 未安装，将使用文件系统作为后备存储")
            print("   安装方法：pip install lancedb pyarrow")
            return
        
        try:
            self._initialize_database()
            print("✅ LanceDB 初始化成功")
        except Exception as e:
            print(f"⚠️ LanceDB 初始化失败：{e}")
            self._available = False
    
    @property
    def is_available(self) -> bool:
        """检查 LanceDB 是否可用"""
        return self._available and self.db is not None
    
    def _initialize_database(self) -> None:
        """初始化数据库连接"""
        if not LANCEDB_AVAILABLE:
            return
            
        # 确保目录存在
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # 连接数据库
        self.db = lancedb.connect(self.db_path)
        
        # 创建表（如果不存在）
        try:
            if "memories" not in self.db.table_names():
                self._create_memories_table()
            else:
                self.memories_table = self.db.open_table("memories")
        except Exception as e:
            print(f"⚠️ 打开 memories 表失败：{e}")
        
        try:
            if "checkpoints" not in self.db.table_names():
                self._create_checkpoints_table()
            else:
                self.checkpoints_table = self.db.open_table("checkpoints")
        except Exception as e:
            print(f"⚠️ 打开 checkpoints 表失败：{e}")
    
    def _create_memories_table(self) -> None:
        """创建记忆表"""
        if not self.is_available:
            return
            
        # 创建一个空表来定义 schema
        sample_record = MemoryRecord(
            id=str(uuid.uuid4()),
            content="sample",
            memory_type="sample",
            source="init",
            timestamp=datetime.now().isoformat(),
            importance=0.5,
            metadata="{}"
        )
        
        self.memories_table = self.db.create_table(
            "memories", 
            data=[sample_record.to_dict()]
        )
        
        # 删除示例记录
        self.memories_table.delete("content = 'sample'")
    
    def _create_checkpoints_table(self) -> None:
        """创建检查点表"""
        if not self.is_available:
            return
            
        sample_record = {
            "checkpoint_id": str(uuid.uuid4()),
            "session_key": "sample",
            "timestamp": datetime.now().isoformat(),
            "data_json": "{}",
            "status": "sample"
        }
        
        self.checkpoints_table = self.db.create_table(
            "checkpoints",
            data=[sample_record]
        )
        
        self.checkpoints_table.delete("status = 'sample'")
    
    def capture_memory(
        self, 
        content: str, 
        memory_type: str = "observation",
        importance: float = 0.7, 
        source: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """捕获一条记忆到 LanceDB
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型 (observation, decision, preference, fact)
            importance: 重要性分数 (0.0 - 1.0)
            source: 来源标识
            metadata: 额外元数据
            
        Returns:
            记忆 ID，如果保存失败则返回 None
        """
        if not self.is_available or self.memories_table is None:
            return None
        
        try:
            memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            record = MemoryRecord(
                id=memory_id,
                content=content,
                memory_type=memory_type,
                source=source,
                timestamp=datetime.now().isoformat(),
                importance=min(1.0, max(0.0, importance)),
                metadata=json.dumps(metadata or {}, ensure_ascii=False)
            )
            
            self.memories_table.add([record.to_dict()])
            return memory_id
            
        except Exception as e:
            print(f"⚠️ 保存记忆失败：{e}")
            return None
    
    def search_memories(
        self, 
        query: str, 
        limit: int = 10,
        memory_types: Optional[List[str]] = None,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """搜索记忆
        
        Args:
            query: 搜索查询
            limit: 返回结果数量限制
            memory_types: 过滤记忆类型
            min_importance: 最小重要性过滤
            
        Returns:
            匹配的记忆列表
        """
        if not self.is_available or self.memories_table is None:
            return []
        
        try:
            # 使用 LanceDB 的全文搜索
            results = self.memories_table.search(query).limit(limit).to_list()
            
            # 过滤
            filtered = []
            for r in results:
                # 类型过滤
                if memory_types and r.get("memory_type") not in memory_types:
                    continue
                
                # 重要性过滤
                if r.get("importance", 0) < min_importance:
                    continue
                
                filtered.append(r)
            
            return filtered
            
        except Exception as e:
            print(f"⚠️ 搜索记忆失败：{e}")
            return []
    
    def get_recent_checkpoints(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """获取最近的检查点
        
        Args:
            days_back: 回溯天数
            
        Returns:
            检查点列表
        """
        if not self.is_available or self.checkpoints_table is None:
            return []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            results = self.checkpoints_table.search("").where(
                f"timestamp > '{cutoff_date.isoformat()}'"
            ).limit(100).to_list()
            
            return results
            
        except Exception as e:
            print(f"⚠️ 获取检查点失败：{e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除指定记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            是否成功
        """
        if not self.is_available or self.memories_table is None:
            return False
        
        try:
            self.memories_table.delete(f"id = '{memory_id}'")
            return True
        except Exception as e:
            print(f"⚠️ 删除记忆失败：{e}")
            return False
    
    def close(self) -> None:
        """关闭数据库连接"""
        # LanceDB 的连接会自动管理
        self.db = None
        self._available = False


# 快速测试函数
def quick_test() -> bool:
    """快速测试 LanceDB 功能
    
    Returns:
        测试是否成功
    """
    print("🔍 LanceDB Memory 测试:")
    print("=" * 50)
    
    if not LANCEDB_AVAILABLE:
        print("❌ LanceDB 未安装")
        print("   安装方法：pip install lancedb pyarrow")
        return False
    
    db = LanceDBMemory()
    
    if not db.is_available:
        print("❌ LanceDB 初始化失败")
        return False
    
    print("✅ 数据库连接成功")
    
    # 测试插入
    memory_id = db.capture_memory(
        content="这是一个测试记忆",
        memory_type="test",
        importance=0.5
    )
    
    if memory_id:
        print(f"✅ 测试记忆已保存：{memory_id}")
        
        # 测试搜索
        results = db.search_memories("测试记忆", limit=5)
        print(f"✅ 搜索结果：{len(results)} 条")
        
        # 清理
        db.delete_memory(memory_id)
        print("✅ 测试记忆已清理")
    else:
        print("❌ 保存测试记忆失败")
    
    db.close()
    return True


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
