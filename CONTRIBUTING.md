# Contributing to Memory Compass 🧭

感谢您对 Memory Compass 感兴趣！我们欢迎所有人的贡献。

## 💡 如何贡献

### 报告 Bug

如果您发现 bug，请在 GitHub 上创建一个 Issue：
1. **标题清晰描述问题**
2. **提供复现步骤**
3. **说明预期行为和实际行为**
4. **附上相关日志或截图（如适用）**

### 提出新功能

对于新功能建议：
1. **先查看现有 Issues**，看是否已有类似提议
2. **详细说明功能目的和使用场景**
3. **如果可能，提供代码示例**

### Pull Request 流程

1. **Fork 仓库**
2. **创建功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **提交更改**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **推送到分支**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **打开 Pull Request**

## 📋 开发指南

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/winde/memory-compass.git
cd memory-compass

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -e .[dev]
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 生成覆盖率报告
pytest --cov=src tests/
```

### 代码风格

我们使用以下工具保持代码质量：

```bash
# 格式化代码
black src/

# 检查代码风格
flake8 src/
```

请遵循 [PEP 8](https://www.python.org/dev/peps/pep-0008/) 规范。

## 📄 License

通过贡献代码，您同意您的贡献将按 MIT 许可证发布。

---

🌊 **在数字沧海中，找到你的方向**
