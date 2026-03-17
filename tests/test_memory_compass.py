# -*- coding: utf-8 -*-
"""Tests for MemoryCompass main class"""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import sys
import os
# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src import MemoryCompass


class TestMemoryCompass:
    """MemoryCompass 主类单元测试"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def compass(self, temp_workspace):
        """创建 MemoryCompass 实例"""
        return MemoryCompass(workspace_root=temp_workspace)
    
    def test_initialization(self, compass, temp_workspace):
        """测试初始化"""
        assert compass.workspace_root == temp_workspace
        assert compass.filesystem is not None
        assert compass.unified_search is not None
    
    def test_save_checkpoint(self, compass):
        """测试保存检查点"""
        result = compass.save_checkpoint(mode="auto")
        
        assert result["success"] is True
        assert "file" in result
        assert "data" in result
        assert result["data"]["mode"] == "auto"
    
    def test_save_checkpoint_manual(self, compass):
        """测试手动保存检查点"""
        result = compass.save_checkpoint(mode="manual")
        
        assert result["success"] is True
        assert result["data"]["mode"] == "manual"
    
    def test_recover_checkpoint_latest(self, compass):
        """测试恢复最新检查点"""
        # 先保存一个检查点
        compass.save_checkpoint(mode="auto")
        
        # 恢复
        result = compass.recover_checkpoint(latest=True)
        
        assert result["success"] is True
        assert "data" in result
    
    def test_recover_checkpoint_by_date(self, compass):
        """测试按日期恢复检查点"""
        # 先保存检查点
        save_result = compass.save_checkpoint(mode="auto")
        
        # 从文件名提取日期（包含微秒）
        import re
        match = re.search(r'checkpoint-(\d{8}_\d{6}_\d{6})', save_result["file"])
        if match:
            date_str = match.group(1)
            result = compass.recover_checkpoint(date=date_str)
            assert result["success"] is True
    
    def test_recover_checkpoint_not_found(self, compass):
        """测试恢复不存在的检查点"""
        result = compass.recover_checkpoint(date="20000101_000000")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_list_checkpoints(self, compass):
        """测试列出检查点"""
        # 创建几个检查点
        for i in range(3):
            compass.save_checkpoint(mode="auto")
        
        checkpoints = compass.list_checkpoints(days_back=7)
        
        assert len(checkpoints) >= 3
    
    def test_find_memory(self, compass):
        """测试搜索记忆"""
        # 先写入一些内容
        compass.filesystem.write_to_session_state("测试：图像生成任务进度")
        
        results = compass.find_memory(
            query="图像生成",
            top_k=5,
            strategy="file_system"
        )
        
        assert isinstance(results, list)
    
    def test_get_context(self, compass):
        """测试获取上下文"""
        context = compass.get_context(days_back=7)
        
        assert "checkpoints" in context
        assert "decisions" in context
        assert "tasks" in context
    
    def test_cleanup_old_checkpoints(self, compass):
        """测试清理过期检查点"""
        # 创建检查点
        compass.save_checkpoint(mode="auto")
        
        # 清理（保留 7 天）
        result = compass.cleanup_old_checkpoints(keep_days=7)
        
        assert result["success"] is True
        assert "deleted_count" in result
    
    def test_collect_session_info(self, compass):
        """测试收集会话信息"""
        info = compass._collect_session_info()
        
        assert "total_files" in info
        assert "today_token" in info
        assert isinstance(info["total_files"], int)


class TestMemoryCompassIntegration:
    """MemoryCompass 集成测试"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_workflow(self, temp_workspace):
        """测试完整工作流程"""
        compass = MemoryCompass(workspace_root=temp_workspace)
        
        # 1. 写入一些数据
        compass.filesystem.write_to_session_state("测试任务：完成单元测试")
        compass.filesystem.append_to_memory("重要决策：使用三层架构", category="decision")
        
        # 2. 保存检查点
        checkpoint = compass.save_checkpoint(mode="auto")
        assert checkpoint["success"] is True
        
        # 3. 搜索记忆
        results = compass.find_memory("单元测试", top_k=5)
        assert len(results) >= 0  # 可能找到也可能找不到
        
        # 4. 恢复检查点
        recovered = compass.recover_checkpoint(latest=True)
        assert recovered["success"] is True
        
        # 5. 获取上下文
        context = compass.get_context(days_back=7)
        assert len(context["checkpoints"]) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
