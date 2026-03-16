#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Memory Compass - 记忆罗盘 CLI 命令行工具

在数字沧海中，找到你的方向
Navigate your way through the digital sea.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime


class SimpleFileSystemMemory:
    """简化的文件系统记忆管理器"""
    
    def __init__(self, workspace_root=None):
        self.workspace_root = workspace_root or str(Path.home() / ".openclaw" / "workspace")
        self.session_state_file = Path(self.workspace_root) / "SESSION-STATE.md"
        self.memory_file = Path(self.workspace_root) / "MEMORY.md"
        self.working_buffer_file = Path(self.workspace_root) / "memory" / "working-buffer.md"
        self.checkpoints_dir = Path(self.workspace_root) / "memory" / "checkpoints"
        
        # 确保目录存在
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, checkpoint_data):
        """保存检查点到 JSON 文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_file = self.checkpoints_dir / f"checkpoint-{timestamp}.json"
        
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            json.dump(checkpoint_data, f, indent=2, ensure_ascii=False)
        
        return str(checkpoint_file)
    
    def list_checkpoints(self, days_back=7):
        """列出最近的检查点"""
        checkpoints = []
        cutoff_date = datetime.now().timestamp() - (days_back * 86400)
        
        for file in sorted(self.checkpoints_dir.glob("checkpoint-*.json"), 
                          key=lambda x: x.stat().st_mtime, reverse=True):
            if file.stat().st_mtime > cutoff_date:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        data["file"] = str(file)
                        checkpoints.append(data)
                except:
                    pass
        
        return checkpoints[:50]
    
    def get_latest_checkpoint(self):
        """获取最新的检查点"""
        checkpoints = self.list_checkpoints(days_back=7)
        return checkpoints[0] if checkpoints else None
    
    def cleanup_old_checkpoints(self, keep_days=7):
        """清理过期检查点"""
        deleted_count = 0
        cutoff_date = datetime.now().timestamp() - (keep_days * 86400)
        
        for file in self.checkpoints_dir.glob("checkpoint-*.json"):
            if file.stat().st_mtime < cutoff_date:
                try:
                    file.unlink()
                    deleted_count += 1
                except:
                    pass
        
        return deleted_count


def cmd_save(args):
    """保存检查点命令"""
    fs = SimpleFileSystemMemory()
    
    checkpoint_data = {
        "timestamp": datetime.now().isoformat(),
        "mode": args.mode or "auto",
        "version": "1.0.0",
        "message": args.message or "自动生成的检查点"
    }
    
    checkpoint_file = fs.save_checkpoint(checkpoint_data)
    
    print(f"\n✅ 已保存检查点")
    print(f"   文件：{Path(checkpoint_file).name}")
    print(f"   时间：{checkpoint_data['timestamp']}")
    
    return 0


def cmd_list(args):
    """列出检查点命令"""
    fs = SimpleFileSystemMemory()
    
    checkpoints = fs.list_checkpoints(days_back=args.days or 7)
    
    print(f"\n📋 发现 {len(checkpoints)} 个检查点")
    print("=" * 60)
    
    if not checkpoints:
        print("   暂无可用检查点")
        return 0
    
    for i, cp in enumerate(checkpoints[:10], 1):
        timestamp = cp.get("timestamp", "Unknown")[:19].replace("T", " ")
        message = cp.get("message", "无描述")
        
        print(f"{i}. [{timestamp}] {message}")
    
    return 0


def cmd_restore(args):
    """恢复检查点命令"""
    fs = SimpleFileSystemMemory()
    
    checkpoint = fs.get_latest_checkpoint()
    
    if not checkpoint:
        print("\n❌ 未找到可用的检查点")
        return 1
    
    print(f"\n✅ 找到最新检查点")
    print(f"   时间：{checkpoint.get('timestamp', 'Unknown')}")
    print(f"   模式：{checkpoint.get('mode', 'Unknown')}")
    print(f"   消息：{checkpoint.get('message', '无描述')}")
    
    return 0


def cmd_cleanup(args):
    """清理过期检查点命令"""
    fs = SimpleFileSystemMemory()
    
    deleted = fs.cleanup_old_checkpoints(keep_days=args.keep or 7)
    
    print(f"\n🧹 已删除 {deleted} 个过期检查点")
    
    return 0


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        prog="memory-compass",
        description="🧭 记忆罗盘 - 在数字沧海中，找到你的方向"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # save 命令
    save_parser = subparsers.add_parser("save", help="保存检查点")
    save_parser.add_argument("--mode", default="auto", choices=["auto", "manual"])
    save_parser.add_argument("--message", help="检查点描述")
    save_parser.set_defaults(func=cmd_save)
    
    # list 命令
    list_parser = subparsers.add_parser("list", help="列出检查点")
    list_parser.add_argument("--days", type=int, default=7, help="保留天数")
    list_parser.set_defaults(func=cmd_list)
    
    # restore 命令
    restore_parser = subparsers.add_parser("restore", help="恢复最近检查点")
    restore_parser.set_defaults(func=cmd_restore)
    
    # cleanup 命令
    cleanup_parser = subparsers.add_parser("cleanup", help="清理过期检查点")
    cleanup_parser.add_argument("--keep", type=int, default=7, help="保留天数")
    cleanup_parser.set_defaults(func=cmd_cleanup)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    exit(main())
