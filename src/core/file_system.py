# -*- coding: utf-8 -*-
"""文件系统 WAL 协议接口

提供基于文件系统的记忆存储，作为 LanceDB 的后备方案。
"""
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import os


class FileSystemMemory:
    """文件系统 WAL 协议管理器
    
    负责管理基于文件系统的记忆存储，包括：
    - SESSION-STATE.md: 会话状态（WAL 目标）
    - MEMORY.md: 长期精选记忆
    - working-buffer.md: 危险区存活日志
    - checkpoints/: 检查点存储目录
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """初始化文件系统记忆管理器
        
        Args:
            workspace_root: 工作空间根目录，默认 ~/.openclaw/workspace
        """
        self.workspace_root = workspace_root or str(
            Path.home() / ".openclaw" / "workspace"
        )
        
        # 核心文件路径
        self.session_state_file = Path(self.workspace_root) / "SESSION-STATE.md"
        self.memory_file = Path(self.workspace_root) / "MEMORY.md"
        self.working_buffer_file = Path(self.workspace_root) / "memory" / "working-buffer.md"
        self.checkpoints_dir = Path(self.workspace_root) / "memory" / "checkpoints"
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """确保所有必要目录存在"""
        directories = [
            Path(self.workspace_root),
            Path(self.workspace_root) / "memory",
            self.checkpoints_dir
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def write_to_session_state(
        self, 
        content: str, 
        section: Optional[str] = None
    ) -> bool:
        """写入 SESSION-STATE.md（WAL 目标）
        
        Args:
            content: 要写入的内容
            section: 可选的区块标题
            
        Returns:
            是否写入成功
        """
        try:
            # 确保文件存在
            if not self.session_state_file.exists():
                self.session_state_file.write_text(
                    "# SESSION-STATE\n\n## 🎯 当前任务\n\n",
                    encoding="utf-8"
                )
            
            # 追加内容
            with open(self.session_state_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if section:
                    f.write(f"\n## {section} - {timestamp}\n\n")
                    f.write(f"{content}\n")
                else:
                    f.write(f"- **{timestamp}**: {content}\n")
                
                f.flush()
            
            return True
            
        except (IOError, OSError) as e:
            print(f"❌ 写入 SESSION-STATE.md 失败：{e}")
            return False
        except Exception as e:
            print(f"❌ 写入 SESSION-STATE.md 发生未知错误：{e}")
            return False
    
    def append_to_memory(
        self, 
        entry: str, 
        category: str = "observation"
    ) -> bool:
        """追加到 MEMORY.md（长期精选记忆）
        
        Args:
            entry: 记忆条目内容
            category: 记忆类别 (observation, decision, preference, fact)
            
        Returns:
            是否写入成功
        """
        try:
            if not self.memory_file.exists():
                self.memory_file.write_text(
                    "# MEMORY.md - 长期记忆\n\n",
                    encoding="utf-8"
                )
            
            with open(self.memory_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                f.write(f"## {category} ({timestamp})\n\n")
                f.write(f"{entry}\n\n---\n\n")
                f.flush()
            
            return True
            
        except (IOError, OSError) as e:
            print(f"❌ 写入 MEMORY.md 失败：{e}")
            return False
        except Exception as e:
            print(f"❌ 写入 MEMORY.md 发生未知错误：{e}")
            return False
    
    def log_to_working_buffer(self, event: str) -> bool:
        """记录到 Working Buffer（危险区存活）
        
        Args:
            event: 事件描述
            
        Returns:
            是否写入成功
        """
        try:
            # 确保目录存在
            self.working_buffer_file.parent.mkdir(parents=True, exist_ok=True)
            
            if not self.working_buffer_file.exists():
                self.working_buffer_file.write_text(
                    "# Working Buffer - Danger Zone Log\n\n",
                    encoding="utf-8"
                )
            
            with open(self.working_buffer_file, "a", encoding="utf-8") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"- [{timestamp}] {event}\n")
                f.flush()
            
            return True
            
        except (IOError, OSError) as e:
            print(f"❌ 写入 Working Buffer 失败：{e}")
            return False
        except Exception as e:
            print(f"❌ 写入 Working Buffer 发生未知错误：{e}")
            return False
    
    def read_session_state(self, max_lines: int = 100) -> str:
        """读取 SESSION-STATE.md（最近的内容）
        
        Args:
            max_lines: 最大读取行数
            
        Returns:
            文件内容字符串
        """
        try:
            if not self.session_state_file.exists():
                return ""
            
            lines = self.session_state_file.read_text(
                encoding="utf-8"
            ).split("\n")
            return "\n".join(lines[-max_lines:])
            
        except (IOError, OSError) as e:
            print(f"❌ 读取 SESSION-STATE.md 失败：{e}")
            return ""
        except Exception as e:
            print(f"❌ 读取 SESSION-STATE.md 发生未知错误：{e}")
            return ""
    
    def save_checkpoint_json(self, checkpoint_data: Dict[str, Any]) -> Optional[str]:
        """保存检查点到 JSON 文件
        
        Args:
            checkpoint_data: 检查点数据字典
            
        Returns:
            检查点文件路径，失败返回 None
        """
        try:
            # 使用微秒精度避免文件名冲突
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            checkpoint_file = self.checkpoints_dir / f"checkpoint-{timestamp}.json"
            
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
            
            return str(checkpoint_file)
            
        except (IOError, OSError, json.JSONEncodeError) as e:
            print(f"❌ 保存检查点失败：{e}")
            return None
        except Exception as e:
            print(f"❌ 保存检查点发生未知错误：{e}")
            return None
    
    def load_checkpoint(self, checkpoint_file: str) -> Optional[Dict[str, Any]]:
        """从 JSON 文件加载检查点
        
        Args:
            checkpoint_file: 检查点文件路径
            
        Returns:
            检查点数据字典，失败返回 None
        """
        try:
            file_path = Path(checkpoint_file)
            if not file_path.exists():
                return None
            
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"❌ 加载检查点失败：{e}")
            return None
        except Exception as e:
            print(f"❌ 加载检查点发生未知错误：{e}")
            return None
    
    def get_recent_checkpoints(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """获取最近 N 天的检查点
        
        Args:
            days_back: 回溯天数
            
        Returns:
            检查点列表，按时间倒序排列
        """
        checkpoints: List[Dict[str, Any]] = []
        cutoff_timestamp = datetime.now().timestamp() - (days_back * 86400)
        
        if not self.checkpoints_dir.exists():
            return checkpoints
        
        try:
            # 获取所有检查点文件并按修改时间排序
            checkpoint_files = sorted(
                self.checkpoints_dir.glob("checkpoint-*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for file in checkpoint_files:
                # 检查文件修改时间
                if file.stat().st_mtime > cutoff_timestamp:
                    checkpoint = self.load_checkpoint(str(file))
                    if checkpoint:
                        checkpoint["file"] = str(file)
                        checkpoints.append(checkpoint)
                        
                        # 限制最多返回 50 个
                        if len(checkpoints) >= 50:
                            break
        
        except (IOError, OSError) as e:
            print(f"⚠️ 获取检查点列表时出错：{e}")
        
        return checkpoints
    
    def delete_checkpoint(self, checkpoint_file: str) -> bool:
        """删除指定检查点
        
        Args:
            checkpoint_file: 检查点文件路径
            
        Returns:
            是否删除成功
        """
        try:
            file_path = Path(checkpoint_file)
            if file_path.exists():
                os.remove(file_path)
                return True
            return False
        except (IOError, OSError) as e:
            print(f"❌ 删除检查点失败：{e}")
            return False


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
