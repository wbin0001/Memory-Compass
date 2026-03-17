# -*- coding: utf-8 -*-
"""统一查询接口 - 自动路由到最佳存储轨道

提供统一的记忆查询入口，自动在 LanceDB 和文件系统之间路由。
"""
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import json

from .lance_db import LanceDBMemory, LANCEDB_AVAILABLE
from .file_system import FileSystemMemory


class UnifiedSearch:
    """统一记忆查询入口 - Hybrid Search
    
    自动在多个存储轨道之间路由查询请求：
    - LanceDB: 向量语义搜索（优先）
    - 文件系统: 关键词搜索（后备）
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """初始化统一查询接口
        
        Args:
            workspace_root: 工作空间根目录
        """
        self.workspace_root = workspace_root or str(
            Path.home() / ".openclaw" / "workspace"
        )
        
        # 初始化底层服务
        self.lancedb = LanceDBMemory()
        self.filesystem = FileSystemMemory(self.workspace_root)
        
        self.initialized = True
    
    def find_memory(
        self, 
        query: str, 
        top_k: int = 10,
        strategy: str = "hybrid",
        memory_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """查找记忆 - 统一接口
        
        Args:
            query: 自然语言查询
            top_k: 返回结果数量上限
            strategy: 搜索策略
                - "hybrid": 混合搜索（LanceDB + 文件系统）
                - "lancedb": 仅使用 LanceDB
                - "file_system": 仅使用文件系统
            memory_types: 过滤记忆类型列表
            
        Returns:
            包含来源和分数的结果列表
        """
        results: List[Dict[str, Any]] = []
        
        if strategy == "hybrid":
            # 优先 LanceDB（如果有）
            lancedb_results = self._search_lancedb(
                query, top_k // 2, memory_types
            )
            results.extend(lancedb_results)
            
            # 回退文件系统
            fs_results = self._search_filesystem(query, top_k // 2 + 5)
            results.extend(fs_results)
            
            # 去重并排序
            results = self._deduplicate_and_rank(results)[:top_k]
            
        elif strategy == "lancedb":
            results = self._search_lancedb(query, top_k, memory_types)
            
        elif strategy == "file_system":
            results = self._search_filesystem(query, top_k)
        
        return results
    
    def _search_lancedb(
        self, 
        query: str, 
        limit: int,
        memory_types: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """在 LanceDB 中搜索
        
        Args:
            query: 查询字符串
            limit: 结果数量限制
            memory_types: 记忆类型过滤
            
        Returns:
            搜索结果列表
        """
        if not self.lancedb.is_available:
            return []
        
        try:
            results = self.lancedb.search_memories(
                query=query,
                limit=limit,
                memory_types=memory_types
            )
            
            # 标准化结果格式
            standardized = []
            for r in results:
                standardized.append({
                    "source": "LanceDB",
                    "id": r.get("id", ""),
                    "matched_line": r.get("content", "")[:200],
                    "context": r.get("content", ""),
                    "score": r.get("_distance", 1.0),
                    "type": r.get("memory_type", "unknown"),
                    "timestamp": r.get("timestamp", "")
                })
            
            return standardized
            
        except Exception as e:
            print(f"⚠️ LanceDB 搜索失败：{e}")
            return []
    
    def _search_filesystem(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """在文件系统中搜索（关键词匹配）
        
        Args:
            query: 查询字符串
            limit: 结果数量限制
            
        Returns:
            搜索结果列表
        """
        results: List[Dict[str, Any]] = []
        
        # 1. 搜索 SESSION-STATE.md
        try:
            session_state = self.filesystem.read_session_state()
            if session_state:
                state_matches = self._keyword_search(
                    query, session_state, source="SESSION-STATE.md"
                )
                results.extend(state_matches)
        except Exception as e:
            print(f"⚠️ 搜索 SESSION-STATE.md 失败：{e}")
        
        # 2. 搜索 MEMORY.md
        try:
            if self.filesystem.memory_file.exists():
                memory_content = self.filesystem.memory_file.read_text(
                    encoding="utf-8"
                )
                memory_matches = self._keyword_search(
                    query, memory_content, source="MEMORY.md"
                )
                results.extend(memory_matches)
        except Exception as e:
            print(f"⚠️ 搜索 MEMORY.md 失败：{e}")
        
        # 3. 搜索 Working Buffer
        try:
            if self.filesystem.working_buffer_file.exists():
                wb_content = self.filesystem.working_buffer_file.read_text(
                    encoding="utf-8"
                )
                wb_matches = self._keyword_search(
                    query, wb_content, source="Working Buffer"
                )
                results.extend(wb_matches)
        except Exception as e:
            print(f"⚠️ 搜索 Working Buffer 失败：{e}")
        
        return results[:limit]
    
    def _keyword_search(
        self, 
        query: str, 
        content: str, 
        source: str
    ) -> List[Dict[str, Any]]:
        """关键词搜索
        
        Args:
            query: 查询关键词
            content: 要搜索的内容
            source: 来源标识
            
        Returns:
            匹配结果列表
        """
        results: List[Dict[str, Any]] = []
        query_lower = query.lower()
        
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if query_lower in line.lower():
                # 提取上下文（前后各 2 行）
                start = max(0, i - 2)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])
                
                results.append({
                    "source": source,
                    "line_number": i,
                    "matched_line": line.strip(),
                    "context": context,
                    "score": 1.0,
                    "type": "keyword_match"
                })
        
        return results
    
    def _deduplicate_and_rank(
        self, 
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """去重并排序
        
        Args:
            results: 原始结果列表
            
        Returns:
            去重排序后的结果列表
        """
        seen: set = set()
        unique_results: List[Dict[str, Any]] = []
        
        for result in results:
            # 使用来源和行号/ID 作为唯一标识
            key = (
                result.get("source"),
                result.get("line_number", result.get("id"))
            )
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # 按分数排序（分数越高越好）
        return sorted(
            unique_results,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
    
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
            包含检查点、决策、任务、Token 等信息的上下文对象
        """
        context: Dict[str, Any] = {
            "checkpoints": [],
            "decisions": [],
            "tasks": [],
            "tokens": {},
            "recent_events": [],
            "lancedb_available": self.lancedb.is_available
        }
        
        # 1. 加载最近的检查点
        try:
            checkpoints = self.filesystem.get_recent_checkpoints(days_back)
            context["checkpoints"] = checkpoints[-10:]  # 最近 10 个
        except Exception as e:
            print(f"⚠️ 获取检查点失败：{e}")
        
        # 2. 提取 SESSION-STATE 中的决策
        try:
            session_state = self.filesystem.read_session_state()
            decisions = self._extract_decisions(session_state)
            context["decisions"] = decisions
        except Exception as e:
            print(f"⚠️ 提取决策失败：{e}")
        
        # 3. 提取待办事项
        try:
            tasks = self._extract_tasks(session_state)
            context["tasks"] = tasks
        except Exception as e:
            print(f"⚠️ 提取任务失败：{e}")
        
        # 4. Token 使用情况
        try:
            token_file = (
                Path(self.workspace_root) / "ai-company" / 
                "shared" / "token-summary.json"
            )
            if token_file.exists():
                with open(token_file, "r", encoding="utf-8") as f:
                    context["tokens"] = json.load(f)
        except Exception:
            pass  # Token 文件是可选的
        
        # 5. 过滤关键词
        if keywords:
            context = self._filter_by_keywords(context, keywords)
        
        return context
    
    def _extract_decisions(self, content: str) -> List[Dict[str, Any]]:
        """从内容中提取决策记录
        
        Args:
            content: 要提取的内容
            
        Returns:
            决策列表
        """
        decisions: List[Dict[str, Any]] = []
        decision_keywords = ["决策", "decision", "决定", "approved", "adopted"]
        
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in decision_keywords):
                start = max(0, i - 1)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])
                
                decisions.append({
                    "line": i,
                    "text": line.strip(),
                    "context": context
                })
        
        return decisions
    
    def _extract_tasks(self, content: str) -> List[Dict[str, Any]]:
        """从内容中提取任务
        
        Args:
            content: 要提取的内容
            
        Returns:
            任务列表
        """
        tasks: List[Dict[str, Any]] = []
        task_patterns = ["□ ", "- [ ] ", "TODO", "待办", "FIXME"]
        
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if any(pattern in line for pattern in task_patterns):
                tasks.append({
                    "line": i,
                    "text": line.strip()
                })
        
        return tasks
    
    def _filter_by_keywords(
        self, 
        context: Dict[str, Any], 
        keywords: List[str]
    ) -> Dict[str, Any]:
        """根据关键词过滤上下文
        
        Args:
            context: 原始上下文
            keywords: 关键词列表
            
        Returns:
            过滤后的上下文
        """
        filtered: Dict[str, Any] = {}
        
        for key, value in context.items():
            if isinstance(value, list):
                matched = [
                    item for item in value
                    if any(
                        kw.lower() in str(item).lower() 
                        for kw in keywords
                    )
                ]
                filtered[key] = matched
            elif isinstance(value, dict):
                if any(
                    kw.lower() in str(value).lower() 
                    for kw in keywords
                ):
                    filtered[key] = value
            else:
                if any(
                    kw.lower() in str(value).lower() 
                    for kw in keywords
                ):
                    filtered[key] = value
        
        return filtered


if __name__ == "__main__":
    # 快速测试
    search = UnifiedSearch()
    
    print("🔍 统一查询接口测试:")
    print("=" * 50)
    
    # 测试搜索
    query = "图像生成"
    results = search.find_memory(query, top_k=5, strategy="file_system")
    print(f"\n📝 搜索结果 ('{query}'): {len(results)} 条")
    
    for r in results[:3]:
        print(f"  • [{r['source']}] {r.get('matched_line', '')[:80]}")
    
    # 测试上下文获取
    print("\n\n🌐 获取完整上下文...")
    context = search.get_context(days_back=7)
    print(f"  • Checkpoints: {len(context['checkpoints'])} 个")
    print(f"  • Decisions: {len(context['decisions'])} 个")
    print(f"  • Tasks: {len(context['tasks'])} 个")
    print(f"  • LanceDB: {'可用' if context['lancedb_available'] else '不可用'}")
    
    print("\n✅ 测试完成!")
