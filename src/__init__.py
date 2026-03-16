# -*- coding: utf-8 -*-
"""Memory Compass - 记忆罗盘

在数字沧海中，找到你的方向
Navigate your way through the digital sea.
"""

from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import sys

# 添加 parent 目录到路径以便导入
sys.path.insert(0, str(Path(__file__).parent))

from lance_db import LanceDBMemory
from file_system import FileSystemMemory
from unified_search import UnifiedSearch


class MemoryCompass:
    """记忆罗盘主类 - 统一的记忆管理接口"""
    
    def __init__(self, workspace_root: str = None):
        """
        初始化记忆罗盘
        
        Args:
            workspace_root: 工作空间根目录，默认 ~/.openclaw/workspace
        """
        self.workspace_root = workspace_root or str(Path.home() / ".openclaw" / "workspace")
        
        # 初始化底层服务
        try:
            self.lancedb = LanceDBMemory()
        except:
            self.lancedb = None
        
        try:
            self.filesystem = FileSystemMemory(self.workspace_root)
            self.unified_search = UnifiedSearch(self.workspace_root)
        except Exception as e:
            print(f"❌ 初始化失败：{e}")
            raise
        
        print(f"✅ 记忆罗盘已初始化")
        print(f"   • 工作空间：{self.workspace_root}")
        print(f"   • LanceDB: {'可用' if self.lancedb else '未安装'}")
    
    # ==================== 检查点相关 ====================
    
    def save_checkpoint(self, mode: str = "auto", include_sessions: bool = True) -> Dict:
        """
        保存会话检查点
        
        Args:
            mode: 模式 ("auto" | "manual")
            include_sessions: 是否包含当前会话
            
        Returns:
            dict: 检查点数据
        """
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "version": "1.0.0",
            "session_info": self._collect_session_info(),
            "context": self.get_context(days_back=7),
            "recent_events": []
        }
        
        # 保存到 JSON 文件
        checkpoint_file = self.filesystem.save_checkpoint_json(checkpoint_data)
        
        # TODO: 同步到 LanceDB
        # await self.lancedb.capture_memory(
        #     content=f"检查点：{checkpoint_file}",
        #     memory_type="checkpoint",
        #     importance=0.9,
        #     metadata={"file": checkpoint_file}
        # )
        
        return {
            "success": True,
            "file": checkpoint_file,
            "data": checkpoint_data
        }
    
    def recover_checkpoint(self, latest: bool = True, 
                          date: str = None) -> Dict:
        """
        恢复检查点
        
        Args:
            latest: 是否恢复最近一次
            date: 指定日期时间戳 (YYYYMMDD_HHMMSS)
            
        Returns:
            dict: 恢复的检查点数据
        """
        if latest:
            checkpoints = self.filesystem.get_recent_checkpoints(days_back=7)
            if not checkpoints:
                return {"success": False, "error": "未找到任何检查点"}
            
            checkpoint_file = checkpoints[0]["file"]
        elif date:
            file_pattern = f"checkpoint-{date}.json"
            checkpoint_path = Path(self.workspace_root) / "memory" / "checkpoints" / file_pattern
            if checkpoint_path.exists():
                checkpoint_file = str(checkpoint_path)
            else:
                return {"success": False, "error": f"未找到检查点：{file_pattern}"}
        else:
            return {"success": False, "error": "请指定 latest=True 或 date"}
        
        # 加载检查点
        checkpoint_data = self.filesystem.load_checkpoint(checkpoint_file)
        
        if checkpoint_data:
            return {
                "success": True,
                "file": checkpoint_file,
                "data": checkpoint_data
            }
        else:
            return {"success": False, "error": "无法解析检查点"}
    
    def list_checkpoints(self, days_back: int = 7) -> List[Dict]:
        """列出所有可用的检查点"""
        return self.filesystem.get_recent_checkpoints(days_back)
    
    # ==================== 查询相关 ====================
    
    def find_memory(self, query: str, top_k: int = 10,
                   strategy: str = "hybrid") -> List[Dict]:
        """查找记忆"""
        return self.unified_search.find_memory(query, top_k, strategy)
    
    def get_context(self, keywords: List[str] = None, 
                   days_back: int = 7) -> Dict:
        """获取完整上下文"""
        return self.unified_search.get_context(keywords, days_back)
    
    # ==================== 维护相关 ====================
    
    def cleanup_old_checkpoints(self, keep_days: int = 7) -> Dict:
        """清理过期检查点"""
        from pathlib import Path
        import os
        
        checkpoints_dir = Path(self.workspace_root) / "memory" / "checkpoints"
        cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
        
        deleted_count = 0
        deleted_files = []
        
        for file in checkpoints_dir.glob("checkpoint-*.json"):
            if file.stat().st_mtime < cutoff_date:
                try:
                    os.remove(file)
                    deleted_count += 1
                    deleted_files.append(file.name)
                except Exception as e:
                    print(f"⚠️ 无法删除 {file}: {e}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_files": deleted_files
        }
    
    # ==================== 内部方法 ====================
    
    def _collect_session_info(self) -> Dict:
        """收集会话信息"""
        total_files = len(list(Path(self.workspace_root).rglob("*")))
        
        # Token 使用情况
        token_file = Path(self.workspace_root) / "ai-company" / "shared" / "token-summary.json"
        today_token = "0"
        if token_file.exists():
            import json
            with open(token_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                today_token = str(data.get("todayTotal", "0"))
        
        return {
            "total_files": total_files,
            "today_token": today_token
        }


def quick_start_demo():
    """快速开始演示"""
    print("=" * 60)
    print("🧭 记忆罗盘 - Quick Start Demo")
    print("=" * 60)
    
    compass = MemoryCompass()
    
    # 1. 保存检查点
    print("\n📝 保存检查点...")
    result = compass.save_checkpoint(mode="auto")
    if result["success"]:
        print(f"✅ 已保存：{result['file']}")
    
    # 2. 搜索记忆
    print("\n🔍 搜索记忆...")
    results = compass.find_memory("图像生成", top_k=5)
    print(f"✅ 找到 {len(results)} 条结果")
    
    for r in results[:3]:
        print(f"  [{r['source']}] {r.get('matched_line', '')[:60]}...")
    
    # 3. 获取上下文
    print("\n🌐 获取上下文...")
    context = compass.get_context(days_back=7)
    print(f"✅ Checkpoints: {len(context['checkpoints'])} 个")
    print(f"✅ Tasks: {len(context['tasks'])} 个待办")
    
    print("\n" + "=" * 60)
    print("🎉 Demo 完成!")
    print("=" * 60)


if __name__ == "__main__":
    quick_start_demo()
