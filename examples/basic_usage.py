# -*- coding: utf-8 -*-
"""Memory Compass - 基本使用示例"""

import sys
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from file_system import FileSystemMemory


def demo_basic():
    """演示基础功能"""
    print("=" * 60)
    print("🧭 Memory Compass - Basic Demo")
    print("=" * 60)
    
    # 1. 初始化文件系统管理器
    fs = FileSystemMemory()
    
    print("\n✅ 文件系统记忆管理器已初始化")
    
    # 2. 写入 WAL 日志
    success = fs.write_to_session_state("这是第一次测试条目", section="测试区块")
    if success:
        print("✅ 已成功写入 SESSION-STATE.md")
    else:
        print("❌ 写入失败")
    
    # 3. 写入 Working Buffer
    success = fs.log_to_working_buffer("Working buffer 测试事件")
    if success:
        print("✅ 已成功写入 Working Buffer")
    
    # 4. 读取最近内容
    content = fs.read_session_state(max_lines=5)
    print(f"\n📄 SESSION-STATE.md 预览:\n{content[:300] if content else '无内容'}...")
    
    # 5. 保存检查点
    checkpoint_data = {
        "timestamp": "2026-03-17T07:30:00",
        "test_data": "这是一个测试检查点"
    }
    checkpoint_file = fs.save_checkpoint_json(checkpoint_data)
    
    if checkpoint_file:
        print(f"\n✅ 已保存检查点：{Path(checkpoint_file).name}")
    
    # 6. 加载检查点
    loaded = fs.load_checkpoint(checkpoint_file)
    if loaded:
        print(f"✅ 已加载检查点数据: {loaded.get('test_data')}")
    
    # 7. 获取最近检查点
    checkpoints = fs.get_recent_checkpoints(days_back=7)
    print(f"📊 发现 {len(checkpoints)} 个最近的检查点")
    
    print("\n" + "=" * 60)
    print("🎉 Demo 完成!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        demo_basic()
    except Exception as e:
        print(f"\n❌ Demo 失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
