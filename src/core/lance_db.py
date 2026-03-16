# -*- coding: utf-8 -*-
"""LanceDB 向量记忆库接口"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from lancedb import connect as lancedb_connect
    from lancedb.table import Table
except ImportError:
    lancedb_connect = None

# 配置
CONFIG = {
    "api_provider": "jina-ai",
    "embedding_model": "jina-embeddings-v5-text-small",
    "dimensions": 1024,
    "rerank_model": "jina-reranker-v3",
    "db_path": str(Path.home() / ".openclaw" / "memory_lance.db")
}


class LanceDBMemory:
    """LanceDB 向量记忆库管理类"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or CONFIG["db_path"]
        self.db = None
        self.memories_table: Table = None
        self.checkpoints_table: Table = None
        
        if lancedb_connect is not None:
            try:
                self._initialize_database()
            except Exception as e:
                print(f"⚠️ LanceDB 初始化失败：{e}")
                print("   可能原因：未安装 lance-db-pro skill")
                return
    
    def _initialize_database(self):
        """初始化数据库连接"""
        # 确保目录存在
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # 连接数据库
        self.db = lancedb_connect(self.db_path)
        
        # 创建表（如果不存在）
        if "memories" not in self.db.table_names():
            self._create_memories_table()
        
        if "checkpoints" not in self.db.table_names():
            self._create_checkpoints_table()
    
    def _create_memories_table(self):
        """创建记忆表"""
        schema = [
            ("id", "string"),
            ("content", "string"),
            ("type", "string"),
            ("source", "string"),
            ("timestamp", "datetime"),
            ("importance", "float"),
            ("metadata", "json")
        ]
        self.db.create_table("memories", schema=schema)
    
    def _create_checkpoints_table(self):
        """创建检查点表"""
        schema = [
            ("checkpoint_id", "string"),
            ("session_key", "string"),
            ("timestamp", "datetime"),
            "data_json",
            "status"
        ]
        self.db.create_table("checkpoints", schema=schema)
    
    async def capture_memory(self, content: str, memory_type: str, 
                           importance: float = 0.7, metadata: Dict = None) -> str:
        """捕获一条记忆到 LanceDB"""
        if self.memories_table is None:
            raise RuntimeError("LanceDB 未初始化")
        
        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
        
        record = {
            "id": memory_id,
            "content": content,
            "type": memory_type,
            "source": metadata.get("source", "unknown") if metadata else "unknown",
            "timestamp": datetime.now(),
            "importance": importance,
            "metadata": str(metadata) if metadata else "{}"
        }
        
        self.memories_table.insert([record])
        return memory_id
    
    async def search_memories(self, query: str, limit: int = 10,
                            memory_types: List[str] = None) -> List[Dict]:
        """搜索记忆"""
        if self.memories_table is None:
            return []
        
        # TODO: 实现混合检索（向量 + BM25）
        results = self.memories_table.search(query).limit(limit).to_list()
        
        # 过滤类型
        if memory_types:
            results = [r for r in results if r.get("type") in memory_types]
        
        return results
    
    async def get_recent_checkpoints(self, days_back: int = 7) -> List[Dict]:
        """获取最近的检查点"""
        if self.checkpoints_table is None:
            return []
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        results = self.checkpoints_table.search("").where(
            f"timestamp > '{cutoff_date.isoformat()}'"
        ).limit(100).to_list()
        
        return results
    
    def close(self):
        """关闭数据库连接"""
        if self.db:
            self.db.close()


# 快速测试函数
def quick_test():
    """快速测试 LanceDB 功能"""
    db = LanceDBMemory()
    
    print("🔍 LanceDB Memory 测试:")
    print("=" * 50)
    
    if db.memories_table is None:
        print("❌ LanceDB 未正确初始化")
        return False
    
    print("✅ 数据库连接成功")
    
    # 测试插入
    test_id = await db.capture_memory(
        content="这是一个测试记忆",
        memory_type="test",
        importance=0.5
    )
    print(f"✅ 测试记忆已保存：{test_id}")
    
    # 测试搜索
    results = await db.search_memories("测试记忆", limit=5)
    print(f"✅ 搜索结果：{len(results)} 条")
    
    db.close()
    return True


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
