# Docker 快速开始指南

## 🚀 在ECS服务器上的完整部署流程

### 前提条件

仅需要：
- ✅ 一台ECS服务器（Ubuntu 20.04+ / CentOS 7+ / Debian 10+）
- ✅ Root或sudo权限
- ✅ 互联网连接

**无需安装Python、pip或其他依赖！**

---

## 📝 步骤1: 安装Docker

### Ubuntu/Debian

```bash
# 更新包索引
sudo apt-get update

# 安装Docker
curl -fsSL https://get.docker.com | sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker-compose --version
```

### CentOS/RHEL

```bash
# 安装Docker
curl -fsSL https://get.docker.com | sh

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
docker --version
docker-compose --version
```

### 添加当前用户到docker组（可选）

```bash
sudo usermod -aG docker $USER
# 重新登录或运行
newgrp docker
```

---

## 📦 步骤2: 获取项目代码

```bash
# 克隆项目
git clone https://github.com/yourusername/Script-JSON-Conversion-Evaluation-System.git

# 进入项目目录
cd Script-JSON-Conversion-Evaluation-System
```

---

## ⚙️ 步骤3: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件
nano .env  # 或使用 vi、vim

# 添加你的DeepSeek API Key
# DEEPSEEK_API_KEY=your_api_key_here
```

---

## 🎯 步骤4: 一键启动

### 方式A: 使用快速启动脚本（推荐）

```bash
# 运行快速启动脚本
bash scripts/quick-start-docker.sh
```

这个脚本会：
1. ✅ 检查Docker环境
2. ✅ 检查配置文件
3. ✅ 让你选择运行模式（开发/测试/生产）
4. ✅ 构建镜像
5. ✅ 启动服务
6. ✅ 显示访问信息

### 方式B: 使用Makefile

```bash
# 开发环境（推荐新手使用）
make quickstart

# 或分步执行
make dev-build   # 构建镜像
make dev-up      # 启动服务
```

---

## 🎨 步骤5: 开始使用

### 开发模式

启动后，你有多种开发方式：

#### 1. 进入容器Shell（传统方式）

```bash
make dev-shell

# 在容器内
python scripts/test_system.py
pytest tests/ -v
ipython
```

#### 2. 使用Jupyter Notebook

访问: http://your-server-ip:8888

- 无需token
- 支持交互式开发
- 实时代码测试

#### 3. 使用VS Code Server（最佳体验）

```bash
# 启动VS Code Server
make dev-vscode
```

访问: http://your-server-ip:8080

- 完整的VS Code IDE体验
- 代码补全和IntelliSense
- Git集成
- 终端访问
- 扩展支持

### 运行测试

```bash
# 所有测试
make test-all

# 单元测试
make test-unit

# 系统测试
make test-system
```

### 查看日志

```bash
# 实时日志
make dev-logs

# 或直接使用docker-compose
docker-compose logs -f app
```

---

## 🔄 常用操作

### 停止服务

```bash
make dev-down
```

### 重启服务

```bash
make restart
```

### 清理环境

```bash
# 清理容器和镜像
make clean

# 清理所有（包括输出文件）
make clean-all
```

### 查看运行状态

```bash
make ps
# 或
docker-compose ps
```

---

## 🐛 常见问题

### 问题1: 端口被占用

```bash
# 查看端口占用
netstat -tulpn | grep 8888

# 方案1: 停止占用进程
sudo kill -9 <PID>

# 方案2: 修改端口
# 编辑 docker-compose.dev.yml
# 将 "8888:8888" 改为 "8889:8888"
```

### 问题2: 权限问题

```bash
# 方案1: 添加用户到docker组
sudo usermod -aG docker $USER
newgrp docker

# 方案2: 使用sudo
sudo make dev-up
```

### 问题3: 构建失败

```bash
# 清理并重新构建
make clean
make dev-build

# 查看详细日志
docker-compose build --no-cache --progress=plain
```

### 问题4: 网络问题

```bash
# 使用国内镜像源
# 创建/编辑 /etc/docker/daemon.json
sudo tee /etc/docker/daemon.json <<EOF
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://registry.docker-cn.com"
  ]
}
EOF

# 重启Docker
sudo systemctl restart docker
```

---

## 📊 完整的开发工作流

### 场景：在ECS上进行Vibe Coding

1. **连接到ECS服务器**
   ```bash
   ssh user@your-ecs-server
   ```

2. **启动开发环境**
   ```bash
   cd Script-JSON-Conversion-Evaluation-System
   make dev-up
   ```

3. **选择开发方式**

   **方式A: VS Code Server（推荐）**
   ```bash
   make dev-vscode
   # 访问 http://your-ecs-server:8080
   ```

   **方式B: Jupyter Notebook**
   ```bash
   # 访问 http://your-ecs-server:8888
   ```

   **方式C: SSH + 容器Shell**
   ```bash
   make dev-shell
   ```

4. **编写和测试代码**

   所有代码修改会实时同步到容器！

5. **运行测试**
   ```bash
   make test-all
   ```

6. **查看结果**
   ```bash
   make dev-logs
   ```

7. **提交代码**
   ```bash
   git add .
   git commit -m "feat: xxx"
   git push
   ```

8. **完成后停止**
   ```bash
   make dev-down
   ```

---

## 🎯 生产部署

### 构建和启动

```bash
# 构建生产镜像
make prod-build

# 启动生产环境
make prod-up

# 查看状态
make prod-status
```

### 监控和维护

```bash
# 查看日志
make prod-logs

# 重启服务
make prod-restart

# 查看资源使用
docker stats
```

---

## 💡 高级技巧

### 1. 后台运行并断开SSH

```bash
# 使用screen或tmux
screen -S docker-dev
make dev-up
# Ctrl+A, D 断开

# 重新连接
screen -r docker-dev
```

### 2. 自动重启

```bash
# 编辑 docker-compose.yml
# 将 restart: unless-stopped 改为 restart: always
```

### 3. 性能优化

```bash
# 调整资源限制
# 编辑 docker-compose.dev.yml 中的 deploy.resources
```

### 4. 备份数据

```bash
# 备份输出和日志
tar -czf backup-$(date +%Y%m%d).tar.gz outputs/ logs/

# 备份Docker卷
docker run --rm -v script-eval_outputs-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/volumes-backup.tar.gz -C /data .
```

---

## 📚 更多资源

- 详细Docker指南: [docs/docker_guide.md](docs/docker_guide.md)
- 完整README: [README.md](README.md)
- 项目结构: [docs/project_structure.md](docs/project_structure.md)

---

## ✅ 检查清单

完成以下检查，确保环境正常：

- [ ] Docker和Docker Compose已安装
- [ ] 项目代码已克隆
- [ ] .env文件已配置
- [ ] 镜像构建成功
- [ ] 容器正常运行
- [ ] 能够访问Jupyter/VS Code Server
- [ ] 测试运行通过

---

## 🎉 开始使用

一切就绪！现在你可以：

- 🚀 在浏览器中通过VS Code Server进行开发
- 📓 使用Jupyter进行交互式实验
- 🧪 运行完整的测试套件
- 📦 部署到生产环境

**享受Vibe Coding的乐趣！** 🎨

---

## 🆘 获取帮助

```bash
# 查看所有可用命令
make help

# 查看系统信息
make info

# 查看项目版本
make version
```

如有问题，请查看 [docs/docker_guide.md](docs/docker_guide.md) 获取详细故障排查指南。
