#!/bin/bash
# Docker环境快速启动和验证脚本
# 用于在全新的ECS服务器上快速验证环境

set -e

echo "=========================================="
echo "剧本JSON转换评估系统 - Docker快速启动"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查Docker
echo -e "${BLUE}[1/6] 检查Docker环境...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker未安装${NC}"
    echo ""
    echo "请先安装Docker:"
    echo "  Ubuntu/Debian: curl -fsSL https://get.docker.com | sh"
    echo "  或访问: https://docs.docker.com/engine/install/"
    exit 1
fi

DOCKER_VERSION=$(docker --version)
echo -e "${GREEN}✓ Docker已安装: $DOCKER_VERSION${NC}"

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker Compose未安装，尝试使用docker compose...${NC}"
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose未找到${NC}"
        exit 1
    else
        echo -e "${GREEN}✓ 使用Docker Compose插件${NC}"
        alias docker-compose='docker compose'
    fi
else
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose已安装: $COMPOSE_VERSION${NC}"
fi
echo ""

# 检查.env文件
echo -e "${BLUE}[2/6] 检查配置文件...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env文件不存在，从示例创建...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env文件已创建${NC}"
    echo -e "${YELLOW}请编辑.env文件，添加你的DEEPSEEK_API_KEY${NC}"
    echo ""
    read -p "是否现在编辑.env文件? (y/N): " edit_env
    if [ "$edit_env" = "y" ] || [ "$edit_env" = "Y" ]; then
        ${EDITOR:-vi} .env
    fi
else
    echo -e "${GREEN}✓ .env文件已存在${NC}"
fi
echo ""

# 询问运行模式
echo -e "${BLUE}[3/6] 选择运行模式${NC}"
echo "1) 开发环境 (带Jupyter和VS Code Server)"
echo "2) 测试环境 (运行所有测试)"
echo "3) 生产环境"
echo ""
read -p "请选择 (1-3, 默认1): " mode
mode=${mode:-1}

# 构建镜像
echo ""
echo -e "${BLUE}[4/6] 构建Docker镜像...${NC}"
echo "这可能需要几分钟，请耐心等待..."
echo ""

case $mode in
    1)
        echo -e "${GREEN}构建开发环境镜像...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml build
        ;;
    2)
        echo -e "${GREEN}构建测试环境镜像...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.test.yml build
        ;;
    3)
        echo -e "${GREEN}构建生产环境镜像...${NC}"
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
        ;;
esac

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 镜像构建成功${NC}"
else
    echo -e "${RED}✗ 镜像构建失败${NC}"
    exit 1
fi
echo ""

# 启动服务
echo -e "${BLUE}[5/6] 启动服务...${NC}"
case $mode in
    1)
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
        ;;
    2)
        echo "运行测试..."
        docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm app
        echo ""
        echo -e "${GREEN}测试完成！${NC}"
        exit 0
        ;;
    3)
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
        ;;
esac

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 服务启动成功${NC}"
else
    echo -e "${RED}✗ 服务启动失败${NC}"
    exit 1
fi
echo ""

# 显示状态
echo -e "${BLUE}[6/6] 检查服务状态...${NC}"
sleep 3  # 等待服务完全启动
docker-compose ps
echo ""

# 显示访问信息
echo -e "${GREEN}=========================================="
echo "🎉 启动成功！"
echo "==========================================${NC}"
echo ""

case $mode in
    1)
        echo -e "${BLUE}开发环境访问信息：${NC}"
        echo ""
        echo "  📦 应用容器："
        echo "     docker exec -it script-eval-app bash"
        echo "     或运行: make dev-shell"
        echo ""
        echo "  📓 Jupyter Notebook："
        echo "     http://localhost:8888"
        echo "     (无需token)"
        echo ""
        echo "  💻 VS Code Server (可选)："
        echo "     运行: make dev-vscode"
        echo "     访问: http://localhost:8080"
        echo ""
        echo -e "${YELLOW}提示：${NC}"
        echo "  - 查看日志: make dev-logs"
        echo "  - 运行测试: make test-all"
        echo "  - 查看帮助: make help"
        ;;
    3)
        echo -e "${BLUE}生产环境已启动${NC}"
        echo ""
        echo "  查看日志: make prod-logs"
        echo "  查看状态: make prod-status"
        echo "  重启服务: make prod-restart"
        ;;
esac

echo ""
echo -e "${GREEN}开始开发吧！Happy Coding! 🚀${NC}"
echo ""

# 询问是否进入容器
if [ $mode -eq 1 ]; then
    read -p "是否立即进入开发容器? (y/N): " enter_shell
    if [ "$enter_shell" = "y" ] || [ "$enter_shell" = "Y" ]; then
        echo ""
        echo -e "${GREEN}进入开发容器...${NC}"
        docker exec -it script-eval-app /bin/bash
    fi
fi
