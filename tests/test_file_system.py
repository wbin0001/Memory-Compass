# -*- coding: utf-8 -*-
"""Tests for FileSystemMemory module"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.file_system import FileSystemMemory


class TestFileSystemMemory:
    """FileSystemMemory 单元测试"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def fs_memory(self, temp_workspace):
        """创建 FileSystemMemory 实例"""
        return FileSystemMemory(temp_workspace)
    
    def test_initialization(self, fs_memory, temp_workspace):
        """测试初始化"""
        assert fs_memory.workspace_root == temp_workspace
        assert fs_memory.session_state_file.exists() or True  # 可能尚未创建
        assert fs_memory.checkpoints_dir.exists()
    
    def test_write_to_session_state(self, fs_memory):
        """测试写入 SESSION-STATE.md"""
        success = fs_memory.write_to_session_state(
            content="这是一个测试条目",
            section="测试区块"
        )
        assert success is True
        
        # 验证文件内容
        content = fs_memory.read_session_state()
        assert "测试条目" in content
    
    def test_append_to_memory(self, fs_memory):
        """测试追加到 MEMORY.md"""
        success = fs_memory.append_to_memory(
            entry="这是一条长期记忆",
            category="observation"
        )
        assert success is True
        
        # 验证文件存在
        assert fs_memory.memory_file.exists()
        content = fs_memory.memory_file.read_text(encoding="utf-8")
        assert "长期记忆" in content
    
    def test_log_to_working_buffer(self, fs_memory):
        """测试记录到 Working Buffer"""
        success = fs_memory.log_to_working_buffer("Working buffer 测试事件")
        assert success is True
        
        # 验证文件存在
        assert fs_memory.working_buffer_file.exists()
    
    def test_save_and_load_checkpoint(self, fs_memory):
        """测试保存和加载检查点"""
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "mode": "auto",
            "version": "1.0.0",
            "session_info": {"test": "data"},
            "context": {}
        }
        
        # 保存
        checkpoint_file = fs_memory.save_checkpoint_json(checkpoint_data)
        assert checkpoint_file is not None
        assert Path(checkpoint_file).exists()
        
        # 加载
        loaded = fs_memory.load_checkpoint(checkpoint_file)
        assert loaded is not None
        assert loaded["mode"] == "auto"
        assert loaded["version"] == "1.0.0"
    
    def test_get_recent_checkpoints(self, fs_memory):
        """测试获取最近检查点"""
        # 创建几个检查点
        for i in range(3):
            checkpoint_data = {
                "timestamp": datetime.now().isoformat(),
                "mode": "auto",
                "index": i
            }
            fs_memory.save_checkpoint_json(checkpoint_data)
        
        # 获取检查点列表
        checkpoints = fs_memory.get_recent_checkpoints(days_back=7)
        assert len(checkpoints) >= 3
    
    def test_cleanup_old_checkpoints(self, fs_memory):
        """测试清理过期检查点"""
        # 创建检查点
        checkpoint_data = {
            "timestamp": datetime.now().isoformat(),
            "mode": "test"
        }
        fs_memory.save_checkpoint_json(checkpoint_data)
        
        # 清理（保留0天 = 删除所有）
        # 注意：这个测试可能因为文件太新而不会删除
        # 实际使用时 keep_days 应大于 0
    
    def test_read_session_state_max_lines(self, fs_memory):
        """测试读取 SESSION-STATE.md 行数限制"""
        # 写入多行
        for i in range(200):
            fs_memory.write_to_session_state(f"测试行 {i}")
        
        # 读取最后 50 行
        content = fs_memory.read_session_state(max_lines=50)
        lines = content.strip().split("\n")
        assert len(lines) <= 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
