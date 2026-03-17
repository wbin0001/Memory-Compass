# -*- coding: utf-8 -*-
"""Memory Compass - 记忆罗盘

在数字沧海中，找到你的方向
Navigate your way through the digital sea.

Usage:
    from skills.memory_compass import MemoryCompass
    
    compass = MemoryCompass()
    compass.save_checkpoint(mode="auto")
    results = compass.find_memory("query")
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import json

# 添加 parent 目录到路径以便导入
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

from core.lance_db import LanceDBMemory, LANCEDB_AVAILABLE
from core.file_system import FileSystemMemory
from core.unified_search import UnifiedSearch


__version__ = "1.0.0"
__author__ = "Winde (沧海一粟 AI COO)"
__all__ = ["MemoryCompass", "LANCEDB_AVAILABLE"]


class MemoryCompass:
    """记忆罗盘主类 - 统一的记忆管理接口
    
    提供三层混合记忆系统的统一访问入口：
    - LanceDB 向量记忆库（可选）
    - 文件系统 WAL 协议
    - 检查点系统
    
    Example:
        >>> compass = MemoryCompass()
        >>> # 保存检查点
        >>> result = compass.save_checkpoint(mode="auto")
        >>> # 搜索记忆
        >>> results = compass.find_memory("图像生成", top_k=5)
        >>> # 恢复检查点
        >>> recovered = compass.recover_checkpoint(latest=True)
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """初始化记忆罗盘
        
        Args:
            workspace_root: 工作空间根目录，默认 ~/.openclaw/workspace
        """
        self.workspace_root = workspace_root or str(
            Path.home() / ".openclaw" / "workspace"
        )
        
        # 初始化底层服务
        self.lancedb: Optional[LanceDBMemory] = None
        try:
            self.lancedb = LanceDBMemory()
        except Exception:
            pass
        
        try:
            self.filesystem = FileSystemMemory(self.workspace_root)
            self.unified_search = UnifiedSearch(self.workspace_root)
        except Exception as e:
            raise RuntimeError(f"记忆罗盘初始化失败：{e}") from e
        
        # 打印状态
        print(f"✅ 记忆罗盘已初始化 (v{__version__})")
        print(f"   • 工作空间：{self.workspace_root}")
        print(f"   • LanceDB: {'可用' if self._is_lancedb_available() else '未安装'}")
    
    def _is_lancedb_available(self) -> bool:
        """检查 LanceDB 是否可用"""
        return self.lancedb is not None and self.lancedb.is_available
    
    # ==================== 检查点相关 ====================
    
    def save_checkpoint(
        self, 
        mode: str = "auto",
        include_sessions: bool = True,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """保存会话检查点
        
        Args:
            mode: 模式 ("auto" | "manual")
            include_sessions: 是否包含当前会话信息
            message: 可选的检查点描述消息
            
        Returns:
            包含成功状态、文件路径和数据的字典
        """
        checkpoint_data: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "version": __version__,
            "message": message,
            "session_info": self._collect_session_info() if include_sessions else {},
            "context": self.get_context(days_back=7),
            "recent_events": []
        }
        
        # 保存到文件系统
        checkpoint_file = self.filesystem.save_checkpoint_json(checkpoint_data)
        
        # 同步到 LanceDB（如果可用）
        if self._is_lancedb_available() and checkpoint_file:
            self.lancedb.capture_memory(
                content=f"检查点：{checkpoint_file}",
                memory_type="checkpoint",
                importance=0.9,
                metadata={"file": checkpoint_file, "mode": mode}
            )
        
        return {
            "success": checkpoint_file is not None,
            "file": checkpoint_file,
            "data": checkpoint_data
        }
    
    def recover_checkpoint(
        self, 
        latest: bool = True,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """恢复检查点
        
        Args:
            latest: 是否恢复最近一次
            date: 指定日期时间戳 (YYYYMMDD_HHMMSS_ffffff，包含微秒)
            
        Returns:
            包含成功状态和检查点数据的字典
        """
        checkpoint_file: Optional[str] = None
        
        if latest:
            checkpoints = self.filesystem.get_recent_checkpoints(days_back=7)
            if not checkpoints:
                return {"success": False, "error": "未找到任何检查点"}
            checkpoint_file = checkpoints[0].get("file")
            
        elif date:
            file_pattern = f"checkpoint-{date}.json"
            checkpoint_path = (
                Path(self.workspace_root) / "memory" / 
                "checkpoints" / file_pattern
            )
            if checkpoint_path.exists():
                checkpoint_file = str(checkpoint_path)
            else:
                return {
                    "success": False, 
                    "error": f"未找到检查点：{file_pattern}"
                }
        else:
            return {
                "success": False, 
                "error": "请指定 latest=True 或 date"
            }
        
        # 加载检查点
        if checkpoint_file:
            checkpoint_data = self.filesystem.load_checkpoint(checkpoint_file)
            
            if checkpoint_data:
                return {
                    "success": True,
                    "file": checkpoint_file,
                    "data": checkpoint_data
                }
        
        return {"success": False, "error": "无法解析检查点"}
    
    def list_checkpoints(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """列出所有可用的检查点
        
        Args:
            days_back: 回溯天数
            
        Returns:
            检查点列表
        """
        return self.filesystem.get_recent_checkpoints(days_back)
    
    # ==================== 查询相关 ====================
    
    def find_memory(
        self, 
        query: str, 
        top_k: int = 10,
        strategy: str = "hybrid"
    ) -> List[Dict[str, Any]]:
        """查找记忆
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量上限
            strategy: 搜索策略 ("hybrid" | "lancedb" | "file_system")
            
        Returns:
            匹配的记忆列表
        """
        return self.unified_search.find_memory(query, top_k, strategy)
    
    def get_context(
        self, 
        keywords: Optional[List[str]] = None,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """获取完整上下文
        
        Args:
            keywords: 过滤关键词列表
            days_back: 回溯天数
            
        Returns:
            上下文信息字典
        """
        return self.unified_search.get_context(keywords, days_back)
    
    # ==================== 维护相关 ====================
    
    def cleanup_old_checkpoints(self, keep_days: int = 7) -> Dict[str, Any]:
        """清理过期检查点
        
        Args:
            keep_days: 保留天数
            
        Returns:
            包含删除统计的字典
        """
        checkpoints_dir = Path(self.workspace_root) / "memory" / "checkpoints"
        cutoff_timestamp = datetime.now().timestamp() - (keep_days * 86400)
        
        deleted_count = 0
        deleted_files: List[str] = []
        
        try:
            for file in checkpoints_dir.glob("checkpoint-*.json"):
                if file.stat().st_mtime < cutoff_timestamp:
                    if self.filesystem.delete_checkpoint(str(file)):
                        deleted_count += 1
                        deleted_files.append(file.name)
        except Exception as e:
            print(f"⚠️ 清理检查点时出错：{e}")
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "deleted_files": deleted_files
        }
    
    # ==================== 内部方法 ====================
    
    def _collect_session_info(self) -> Dict[str, Any]:
        """收集会话信息
        
        Returns:
            会话信息字典
        """
        try:
            total_files = len(list(Path(self.workspace_root).rglob("*")))
        except Exception:
            total_files = 0
        
        # Token 使用情况
        today_token = "0"
        token_file = (
            Path(self.workspace_root) / "ai-company" / 
            "shared" / "token-summary.json"
        )
        if token_file.exists():
            try:
                with open(token_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    today_token = str(data.get("todayTotal", "0"))
            except Exception:
                pass
        
        return {
            "total_files": total_files,
            "today_token": today_token
        }


def quick_start_demo() -> None:
    """快速开始演示"""
    print("=" * 60)
    print(f"🧭 记忆罗盘 - Quick Start Demo (v{__version__})")
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
        matched = r.get('matched_line', '')[:60]
        print(f"  • [{r['source']}] {matched}...")
    
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
