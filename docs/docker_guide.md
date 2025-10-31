# Docker使用指南

## 概述

本项目提供完整的Docker容器化方案，支持在**仅安装Docker**的ECS服务器上进行开发、测试和部署，无需本地Python环境。

## 🎯 核心特性

- ✅ **多阶段构建**: 开发、测试、生产环境隔离
- ✅ **开发友好**: 支持代码热重载、Jupyter Notebook、VS Code Server
- ✅ **测试完备**: 单元测试、集成测试、系统测试
- ✅ **生产优化**: 资源限制、健康检查、日志管理
- ✅ **简化命令**: Makefile封装，一键操作

## 📋 前置要求

只需要在服务器上安装：
- Docker 20.10+
- Docker Compose 1.29+

检查版本：
```bash
docker --version
docker-compose --version
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/Script-JSON-Conversion-Evaluation-System.git
cd Script-JSON-Conversion-Evaluation-System
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑.env文件，添加DeepSeek API Key
vim .env  # 或使用nano、vi等编辑器
```

### 3. 一键启动开发环境

```bash
make quickstart
```

这个命令会：
1. 构建Docker镜像
2. 启动开发容器和Jupyter
3. 显示访问信息

### 4. 开始开发

```bash
# 进入开发容器
make dev-shell

# 在容器内运行测试
python scripts/test_system.py

# 或直接从宿主机运行
make test-all
```

## 📚 详细使用

### 开发环境

#### 启动开发环境

```bash
# 方式1: 使用Makefile（推荐）
make dev-up

# 方式2: 使用docker-compose
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

启动后可用服务：
- **应用容器**: 交互式开发环境
- **Jupyter Notebook**: http://localhost:8888
- **VS Code Server** (可选): http://localhost:8080

#### 进入开发容器

```bash
# 使用Makefile
make dev-shell

# 使用docker
docker exec -it script-eval-app bash
```

在容器内，你可以：
```bash
# 运行Python代码
python scripts/test_system.py

# 运行交互式Python
ipython

# 安装额外包
pip install <package-name>

# 格式化代码
black src/

# 运行测试
pytest tests/ -v
```

#### Jupyter Notebook

启动Jupyter：
```bash
make dev-jupyter
```

访问 http://localhost:8888（无需token）

在Jupyter中可以：
- 交互式开发和调试
- 数据探索和可视化
- 运行评估实验

#### VS Code Server（推荐用于Vibe Coding）

启动VS Code Server：
```bash
make dev-vscode
```

访问 http://localhost:8080，你会得到一个完整的VS Code环境，包括：
- 完整的IDE功能
- 代码补全和IntelliSense
- Git集成
- 终端访问
- 扩展支持

#### 查看日志

```bash
make dev-logs

# 或只看特定服务
docker-compose logs -f app
docker-compose logs -f jupyter
```

#### 停止开发环境

```bash
make dev-down
```

### 测试环境

#### 运行所有测试

```bash
make test-all
```

#### 运行特定类型的测试

```bash
# 单元测试
make test-unit

# 集成测试
make test-integration

# 系统测试
make test-system
```

#### 生成测试覆盖率报告

```bash
make test-coverage
```

报告会生成在 `htmlcov/index.html`，可以用浏览器打开查看。

#### 在容器内交互式测试

```bash
# 进入测试容器
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm app bash

# 运行特定测试文件
pytest tests/unit/test_models.py -v

# 运行特定测试用例
pytest tests/unit/test_models.py::test_scene_validation -v

# 带调试的测试
pytest tests/ -v --pdb
```

### 生产环境

#### 构建生产镜像

```bash
make prod-build
```

这会创建一个优化的生产镜像：
- 移除开发工具
- 优化层大小
- 非root用户运行
- 只读根文件系统

#### 启动生产环境

```bash
make prod-up
```

#### 查看生产环境状态

```bash
make prod-status
```

#### 查看生产日志

```bash
make prod-logs
```

#### 重启生产服务

```bash
make prod-restart
```

#### 停止生产环境

```bash
make prod-down
```

## 🛠️ 常用命令速查

### Makefile命令

```bash
# 查看所有可用命令
make help

# === 开发环境 ===
make dev-build       # 构建开发镜像
make dev-up          # 启动开发环境
make dev-shell       # 进入开发容器
make dev-jupyter     # 启动Jupyter
make dev-vscode      # 启动VS Code Server
make dev-logs        # 查看日志
make dev-down        # 停止开发环境

# === 测试环境 ===
make test-all        # 运行所有测试
make test-unit       # 运行单元测试
make test-integration # 运行集成测试
make test-system     # 运行系统测试
make test-coverage   # 生成覆盖率报告

# === 生产环境 ===
make prod-build      # 构建生产镜像
make prod-up         # 启动生产环境
make prod-down       # 停止生产环境
make prod-logs       # 查看生产日志
make prod-restart    # 重启生产服务

# === 维护命令 ===
make clean           # 清理Docker资源
make clean-outputs   # 清理输出文件
make prune           # 清理未使用的资源
make fmt             # 格式化代码
make lint            # 代码检查
make info            # 显示系统信息
```

### Docker Compose命令

如果不使用Makefile，也可以直接使用docker-compose：

```bash
# 开发环境
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# 测试环境
docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm app

# 生产环境
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📁 目录挂载说明

### 开发环境挂载

开发环境会挂载以下目录，支持代码热重载：

```yaml
./src → /app/src                    # 源代码
./tests → /app/tests                # 测试文件
./configs → /app/configs            # 配置文件
./prompts → /app/prompts            # Prompt模板
./scripts → /app/scripts            # 脚本文件
./outputs → /app/outputs            # 输出目录
./data → /app/data                  # 数据目录
```

所有在宿主机上的代码修改都会立即反映到容器中。

### 生产环境挂载

生产环境使用只读挂载和命名卷：

```yaml
./configs → /app/configs:ro         # 只读配置
./prompts → /app/prompts:ro         # 只读Prompt
outputs-prod → /app/outputs         # 输出卷
logs-prod → /app/logs               # 日志卷
```

## 🔧 高级配置

### 自定义端口

编辑 `docker-compose.dev.yml` 修改端口映射：

```yaml
services:
  app:
    ports:
      - "8001:8000"  # 改为8001

  jupyter:
    ports:
      - "8889:8888"  # 改为8889
```

### 资源限制

编辑各环境的docker-compose文件，调整资源限制：

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # CPU限制
      memory: 8G     # 内存限制
```

### 环境变量

在 `.env` 文件中配置：

```env
# API配置
DEEPSEEK_API_KEY=your_key_here

# 评估配置
USE_DEEPSEEK_JUDGE=true
PASS_THRESHOLD=0.70

# 日志配置
LOG_LEVEL=INFO

# 性能配置
BATCH_SIZE=10
MAX_WORKERS=5
```

## 🐛 故障排查

### 问题1: 容器启动失败

```bash
# 查看详细日志
docker-compose logs app

# 检查容器状态
docker ps -a

# 重新构建镜像
make clean
make dev-build
```

### 问题2: 端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep 8888

# 修改端口或停止占用进程
```

### 问题3: 权限问题

```bash
# 修复输出目录权限
sudo chown -R $USER:$USER outputs/

# 或在容器内
docker exec -it script-eval-app chown -R appuser:appuser /app/outputs
```

### 问题4: 镜像构建慢

```bash
# 使用国内镜像源（创建/修改 ~/.docker/daemon.json）
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com"
  ]
}

# 重启Docker
sudo systemctl restart docker
```

### 问题5: 磁盘空间不足

```bash
# 清理未使用的资源
make prune

# 查看磁盘使用
docker system df

# 彻底清理
docker system prune -a --volumes
```

## 💡 最佳实践

### 开发工作流

1. **启动环境**
   ```bash
   make dev-up
   ```

2. **进入容器开发**
   ```bash
   make dev-shell
   # 或使用VS Code Server: make dev-vscode
   ```

3. **编写代码**（在宿主机或容器内都可）

4. **运行测试**
   ```bash
   make test-all
   ```

5. **查看结果**
   ```bash
   make dev-logs
   ```

6. **提交代码**
   ```bash
   git add .
   git commit -m "feat: xxx"
   git push
   ```

### 持续集成

在CI/CD中使用测试环境：

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          make test-all
```

### 生产部署

```bash
# 1. 拉取最新代码
git pull

# 2. 构建生产镜像
make prod-build

# 3. 停止旧服务
make prod-down

# 4. 启动新服务
make prod-up

# 5. 查看状态
make prod-status
```

## 📊 性能优化

### 构建优化

1. **使用构建缓存**
   ```bash
   docker-compose build --parallel
   ```

2. **多阶段构建**（已实现）
   - 减少最终镜像大小
   - 分离构建和运行环境

3. **.dockerignore**（已配置）
   - 减少构建上下文大小
   - 加快构建速度

### 运行优化

1. **资源限制**
   - 设置合理的CPU和内存限制
   - 避免资源争用

2. **日志管理**
   - 限制日志文件大小
   - 使用日志轮转

3. **卷管理**
   - 使用命名卷存储持久数据
   - 定期清理无用卷

## 🔐 安全建议

1. **不要提交敏感信息**
   - .env文件不要提交到git
   - 使用环境变量传递密钥

2. **使用非root用户**（生产环境已实现）
   ```dockerfile
   USER appuser
   ```

3. **只读根文件系统**（生产环境已实现）
   ```yaml
   read_only: true
   ```

4. **网络隔离**
   - 使用Docker网络隔离服务
   - 只暴露必要端口

## 📝 总结

使用Docker容器化方案，你可以：

✅ 在任何有Docker的机器上开发（包括ECS）
✅ 环境一致性，避免"在我机器上能跑"问题
✅ 快速启动和销毁环境
✅ 隔离依赖，避免冲突
✅ 便于CI/CD集成
✅ 轻松扩展和部署

开始使用：
```bash
make quickstart
```

获取帮助：
```bash
make help
```

Happy Coding! 🎉
