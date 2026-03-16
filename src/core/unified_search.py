# -*- coding: utf-8 -*-
"""统一查询接口 - 自动路由到最佳存储轨道"""
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from .lance_db import LanceDBMemory
from .file_system import FileSystemMemory


class UnifiedSearch:
    """统一记忆查询入口 - Hybrid Search"""
    
    def __init__(self, workspace_root: str = None):
        self.workspace_root = workspace_root or str(Path.home() / ".openclaw" / "workspace")
        
        # 初始化底层服务
        self.lancedb = LanceDBMemory()
        self.filesystem = FileSystemMemory(self.workspace_root)
        
        self.initialized = True
    
    def find_memory(self, query: str, top_k: int = 10, 
                   strategy: str = "hybrid",
                   memory_types: List[str] = None) -> List[Dict]:
        """
        查找记忆 - 统一接口
        
        Args:
            query: 自然语言查询
            top_k: 返回结果数量
            strategy: 搜索策略 (lancedb | file_system | hybrid)
            memory_types: 过滤记忆类型列表
            
        Returns:
            list[Dict]: 包含来源和分数的结果列表
        """
        results = []
        
        if strategy == "hybrid":
            # 优先 LanceDB（如果有）
            lancedb_results = self._search_lancedb(query, top_k // 2, memory_types)
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
    
    def _search_lancedb(self, query: str, limit: int, memory_types: List[str]) -> List[Dict]:
        """在 LanceDB 中搜索"""
        try:
            if not self.lancedb.memories_table:
                return []
            
            results = []
            
            # TODO: 实现真正的向量搜索
            # current_results = await self.lancedb.search_memories(
            #     query=query, limit=limit, memory_types=memory_types
            # )
            
            # 临时：模拟返回空
            return results
            
        except Exception as e:
            print(f"⚠️ LanceDB 搜索失败：{e}")
            return []
    
    def _search_filesystem(self, query: str, limit: int) -> List[Dict]:
        """在文件系统中搜索（关键词匹配）"""
        results = []
        
        # 1. 搜索 SESSION-STATE.md
        session_state = self.filesystem.read_session_state()
        state_matches = self._keyword_search(query, session_state, source="SESSION-STATE.md")
        results.extend(state_matches)
        
        # 2. 搜索 MEMORY.md
        memory_file = Path(self.workspace_root) / "MEMORY.md"
        if memory_file.exists():
            memory_content = memory_file.read_text(encoding="utf-8")
            memory_matches = self._keyword_search(query, memory_content, source="MEMORY.md")
            results.extend(memory_matches)
        
        # 3. 搜索 Working Buffer
        wb_content = self.filesystem.working_buffer_file.read_text(encoding="utf-8") \
            if self.filesystem.working_buffer_file.exists() else ""
        wb_matches = self._keyword_search(query, wb_content, source="Working Buffer")
        results.extend(wb_matches)
        
        return results[:limit]
    
    def _keyword_search(self, query: str, content: str, source: str) -> List[Dict]:
        """关键词搜索"""
        results = []
        
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if query.lower() in line.lower():
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
    
    def _deduplicate_and_rank(self, results: List[Dict]) -> List[Dict]:
        """去重并排序"""
        seen = set()
        unique_results = []
        
        for result in results:
            key = (result.get("source"), result.get("line_number", result.get("id")))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        # 按分数排序
        return sorted(unique_results, key=lambda x: x.get("score", 0), reverse=True)
    
    def get_context(self, keywords: List[str] = None, days_back: int = 7) -> Dict:
        """
        获取完整上下文
        
        Args:
            keywords: 过滤关键词列表
            days_back: 回溯天数
            
        Returns:
            dict: 包含检查点、决策、任务、Token 等信息的上下文对象
        """
        context = {
            "checkpoints": [],
            "decisions": [],
            "tasks": [],
            "tokens": {},
            "recent_events": []
        }
        
        # 1. 加载最近的检查点
        checkpoints = self.filesystem.get_recent_checkpoints(days_back)
        context["checkpoints"] = checkpoints[-10:]  # 最近 10 个
        
        # 2. 提取 SESSION-STATE 中的决策
        session_state = self.filesystem.read_session_state()
        decisions = self._extract_decisions(session_state)
        context["decisions"] = decisions
        
        # 3. 提取待办事项
        tasks = self._extract_tasks(session_state)
        context["tasks"] = tasks
        
        # 4. Token 使用情况
        token_file = Path(self.workspace_root) / "ai-company" / "shared" / "token-summary.json"
        if token_file.exists():
            import json
            with open(token_file, "r", encoding="utf-8") as f:
                context["tokens"] = json.load(f)
        
        # 5. 过滤关键词
        if keywords:
            context = self._filter_by_keywords(context, keywords)
        
        return context
    
    def _extract_decisions(self, content: str) -> List[Dict]:
        """从内容中提取决策记录"""
        decisions = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ["决策", "decision", "决定", "approved"]):
                start = max(0, i - 1)
                end = min(len(lines), i + 3)
                context = "\n".join(lines[start:end])
                
                decisions.append({
                    "line": i,
                    "text": line.strip(),
                    "context": context
                })
        
        return decisions
    
    def _extract_tasks(self, content: str) -> List[Dict]:
        """从内容中提取任务"""
        tasks = []
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ["□ ", "- [ ] ", "TODO", "待办"]):
                tasks.append({
                    "line": i,
                    "text": line.strip()
                })
        
        return tasks
    
    def _filter_by_keywords(self, context: Dict, keywords: List[str]) -> Dict:
        """根据关键词过滤上下文"""
        filtered = {}
        
        for key, value in context.items():
            if isinstance(value, list):
                matched = [item for item in value if 
                          any(kw.lower() in str(item).lower() for kw in keywords)]
                filtered[key] = matched
            elif isinstance(value, dict):
                if any(kw.lower() in str(value).lower() for kw in keywords):
                    filtered[key] = value
            else:
                if any(kw.lower() in str(value).lower() for kw in keywords):
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
    print(f"  • Tokens: 今日消耗 {context['tokens'].get('todayTotal', 'N/A')}")
    
    print("\n✅ 测试完成!")
