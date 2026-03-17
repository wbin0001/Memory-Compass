# -*- coding: utf-8 -*-
"""Tests for UnifiedSearch module"""
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

from src.core.unified_search import UnifiedSearch
from src.core.file_system import FileSystemMemory


class TestUnifiedSearch:
    """UnifiedSearch 单元测试"""
    
    @pytest.fixture
    def temp_workspace(self):
        """创建临时工作空间"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def unified_search(self, temp_workspace):
        """创建 UnifiedSearch 实例"""
        return UnifiedSearch(temp_workspace)
    
    @pytest.fixture
    def populated_workspace(self, temp_workspace):
        """创建带有测试数据的工作空间"""
        fs = FileSystemMemory(temp_workspace)
        
        # 写入 SESSION-STATE.md
        fs.write_to_session_state("这是一个关于图像生成的讨论")
        fs.write_to_session_state("决策：使用 ModelScope 作为主要模型")
        
        # 写入 MEMORY.md
        fs.append_to_memory("用户偏好：喜欢蓝色主题", category="preference")
        fs.append_to_memory("重要决策：启用 WAL 协议", category="decision")
        
        # 保存检查点
        checkpoint = {
            "timestamp": datetime.now().isoformat(),
            "mode": "auto",
            "context": {"test": "data"}
        }
        fs.save_checkpoint_json(checkpoint)
        
        return temp_workspace
    
    def test_initialization(self, unified_search, temp_workspace):
        """测试初始化"""
        assert unified_search.workspace_root == temp_workspace
        assert unified_search.filesystem is not None
        assert unified_search.initialized is True
    
    def test_find_memory_file_system(self, unified_search, populated_workspace):
        """测试文件系统搜索"""
        results = unified_search.find_memory(
            query="图像生成",
            top_k=5,
            strategy="file_system"
        )
        
        assert len(results) > 0
        assert any("图像生成" in r.get("matched_line", "") for r in results)
    
    def test_find_memory_hybrid(self, unified_search, populated_workspace):
        """测试混合搜索"""
        results = unified_search.find_memory(
            query="决策",
            top_k=10,
            strategy="hybrid"
        )
        
        # 应该找到包含"决策"的结果
        assert isinstance(results, list)
    
    def test_find_memory_lancedb_fallback(self, unified_search):
        """测试 LanceDB 不可用时的回退"""
        # LanceDB 未安装时应该返回空列表而不是报错
        results = unified_search._search_lancedb("test query", 5, None)
        assert isinstance(results, list)
    
    def test_keyword_search(self, unified_search, populated_workspace):
        """测试关键词搜索"""
        content = """# Test Content
这是一个测试行，包含关键词 openclaw。
另一行不包含关键词。
openclaw 再次出现。"""
        
        results = unified_search._keyword_search(
            query="openclaw",
            content=content,
            source="test"
        )
        
        assert len(results) == 2  # 应该找到 2 个匹配
    
    def test_deduplicate_and_rank(self, unified_search):
        """测试去重和排序"""
        results = [
            {"source": "A", "line_number": 1, "score": 0.8},
            {"source": "A", "line_number": 1, "score": 0.9},  # 重复
            {"source": "B", "line_number": 2, "score": 0.7},
            {"source": "C", "line_number": 3, "score": 0.95},
        ]
        
        deduped = unified_search._deduplicate_and_rank(results)
        
        # 应该去重
        assert len(deduped) == 3
        # 应该按分数排序
        assert deduped[0]["score"] == 0.95
    
    def test_get_context(self, unified_search, populated_workspace):
        """测试获取完整上下文"""
        context = unified_search.get_context(days_back=7)
        
        assert "checkpoints" in context
        assert "decisions" in context
        assert "tasks" in context
        assert "tokens" in context
        
        assert isinstance(context["checkpoints"], list)
    
    def test_extract_decisions(self, unified_search):
        """测试提取决策"""
        content = """
# Session State
这是普通内容。
决策：启用 WAL 协议
Decision: Use LanceDB as primary storage
另一个决策是关闭自动更新。
"""
        
        decisions = unified_search._extract_decisions(content)
        
        assert len(decisions) >= 2
    
    def test_extract_tasks(self, unified_search):
        """测试提取任务"""
        content = """
# Tasks
- [ ] 完成单元测试
□ 待办：添加文档
TODO: 清理代码
"""
        
        tasks = unified_search._extract_tasks(content)
        
        assert len(tasks) >= 2
    
    def test_filter_by_keywords(self, unified_search):
        """测试关键词过滤"""
        context = {
            "checkpoints": [
                {"text": "图像生成相关"},
                {"text": "无关内容"}
            ],
            "tokens": {"total": 1000}
        }
        
        filtered = unified_search._filter_by_keywords(context, ["图像"])
        
        assert len(filtered["checkpoints"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
