# -*- coding: utf-8 -*-
"""文件系统 WAL 协议接口"""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import json


class FileSystemMemory:
    """文件系统 WAL 协议管理器"""
    
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or str(Path.home() / ".openclaw" / "workspace")
        
        # 核心文件路径
        self.session_state_file = Path(self.workspace_root) / "SESSION-STATE.md"
        self.memory_file = Path(self.workspace_root) / "MEMORY.md"
        self.working_buffer_file = Path(self.workspace_root) / "memory" / "working-buffer.md"
        self.checkpoints_dir = Path(self.workspace_root) / "memory" / "checkpoints"
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所有必要目录存在"""
        directories = [
            Path(self.workspace_root),
            Path(self.workspace_root) / "memory",
            Path(self.workspace_root) / "memory" / "checkpoints"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def write_to_session_state(self, content: str, section: str = None):
        """写入 SESSION-STATE.md（WAL 目标）"""
        try:
            if not self.session_state_file.exists():
                self.session_state_file.write_text("# SESSION-STATE\n\n## 🎯 当前任务\n\n", encoding="utf-8")
            
            mode = "a" if self.session_state_file.exists() else "w"
            
            with open(self.session_state_file, mode, encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if section:
                    f.write(f"\n### {section} - {timestamp}\n\n")
                else:
                    f.write(f"- **{timestamp}**: {content}\n")
                
                f.flush()
            
            return True
            
        except Exception as e:
            print(f"❌ 写入 SESSION-STATE.md 失败：{e}")
            return False
    
    def append_to_memory(self, entry: str, category: str = "observation"):
        """追加到 MEMORY.md（长期精选记忆）"""
        try:
            if not self.memory_file.exists():
                self.memory_file.write_text("# MEMORY.md - 长期记忆\n\n", encoding="utf-8")
            
            with open(self.memory_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                f.write(f"## {category} ({timestamp})\n\n")
                f.write(f"{entry}\n\n---\n\n")
                f.flush()
            
            return True
            
        except Exception as e:
            print(f"❌ 写入 MEMORY.md 失败：{e}")
            return False
    
    def log_to_working_buffer(self, event: str):
        """记录到 Working Buffer（危险区存活）"""
        try:
            if not self.working_buffer_file.exists():
                self.working_buffer_file.write_text("# Working Buffer - Danger Zone Log\n\n", encoding="utf-8")
            
            with open(self.working_buffer_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"- [{timestamp}] {event}\n")
                f.flush()
            
            return True
            
        except Exception as e:
            print(f"❌ 写入 Working Buffer 失败：{e}")
            return False
    
    def read_session_state(self, max_lines: int = 100) -> str:
        """读取 SESSION-STATE.md（最近的内容）"""
        try:
            if not self.session_state_file.exists():
                return ""
            
            lines = self.session_state_file.read_text(encoding="utf-8").split("\n")
            return "\n".join(lines[-max_lines:])
            
        except Exception as e:
            print(f"❌ 读取 SESSION-STATE.md 失败：{e}")
            return ""
    
    def save_checkpoint_json(self, checkpoint_data: Dict) -> str:
        """保存检查点到 JSON 文件"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint_file = self.checkpoints_dir / f"checkpoint-{timestamp}.json"
            
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            return str(checkpoint_file)
            
        except Exception as e:
            print(f"❌ 保存检查点失败：{e}")
            return None
    
    def load_checkpoint(self, checkpoint_file: str) -> Optional[Dict]:
        """从 JSON 文件加载检查点"""
        try:
            if not Path(checkpoint_file).exists():
                return None
            
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            print(f"❌ 加载检查点失败：{e}")
            return None
    
    def get_recent_checkpoints(self, days_back: int = 7) -> List[Dict]:
        """获取最近 N 天的检查点"""
        checkpoints = []
        cutoff_date = datetime.now().timestamp() - (days_back * 86400)
        
        if not self.checkpoints_dir.exists():
            return checkpoints
        
        for file in sorted(self.checkpoints_dir.glob("checkpoint-*.json"), 
                          key=lambda x: x.stat().st_mtime, reverse=True):
            # 检查文件修改时间
            if file.stat().st_mtime > cutoff_date:
                checkpoint = self.load_checkpoint(str(file))
                if checkpoint:
                    checkpoint["file"] = str(file)
                    checkpoints.append(checkpoint)
        
        return checkpoints[:50]  # 最多返回 50 个


if __name__ == "__main__":
    # 快速测试
    fs = FileSystemMemory()
    
    print("🔍 文件系统 WAL 测试:")
    print("=" * 50)
    
    # 测试写入
    success = fs.write_to_session_state("这是一个测试条目", section="测试区块")
    print(f"✅ 写入 Session State: {'成功' if success else '失败'}")
    
    success = fs.log_to_working_buffer("Working buffer 测试事件")
    print(f"✅ 写入 Working Buffer: {'成功' if success else '失败'}")
    
    # 测试读取
    content = fs.read_session_state(max_lines=10)
    print(f"📄 Session State 内容预览:\n{content[:200]}...")
    
    print("\n✅ 测试完成!")
