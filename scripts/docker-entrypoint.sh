#!/bin/bash
# Docker容器启动脚本

set -e

echo "========================================"
echo "剧本JSON转换评估系统"
echo "环境: ${ENVIRONMENT:-unknown}"
echo "========================================"

# 等待依赖服务（如果有）
# if [ ! -z "$WAIT_FOR" ]; then
#     echo "等待依赖服务: $WAIT_FOR"
#     /wait-for-it.sh $WAIT_FOR --timeout=60
# fi

# 创建必要的目录
mkdir -p /app/outputs/reports/json
mkdir -p /app/outputs/reports/html
mkdir -p /app/outputs/logs

# 环境检查
echo "检查Python环境..."
python --version

echo "检查依赖..."
pip list | grep -E "deepeval|pydantic|openai" || echo "警告: 核心依赖可能未安装"

# 环境变量检查
if [ "$ENVIRONMENT" = "production" ]; then
    echo "生产环境检查..."

    if [ -z "$DEEPSEEK_API_KEY" ]; then
        echo "警告: DEEPSEEK_API_KEY未设置"
    fi

    # 设置Python优化
    export PYTHONOPTIMIZE=2
fi

if [ "$ENVIRONMENT" = "development" ]; then
    echo "开发环境配置..."

    # 安装开发依赖（如果需要）
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    fi
fi

# 运行数据库迁移（如果有）
# if [ "$RUN_MIGRATIONS" = "true" ]; then
#     echo "运行数据库迁移..."
#     python manage.py migrate
# fi

# 健康检查
echo "运行健康检查..."
python -c "
import sys
try:
    # 基础导入检查
    from src.models import scene_models
    from src.llm import deepseek_client
    from src.metrics import deepeval_metrics
    from src.evaluators import main_evaluator
    print('✓ 所有核心模块导入成功')
    sys.exit(0)
except Exception as e:
    print(f'✗ 模块导入失败: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "✓ 健康检查通过"
else
    echo "✗ 健康检查失败"
    exit 1
fi

echo "========================================"
echo "启动应用..."
echo "========================================"

# 执行传入的命令
exec "$@"
