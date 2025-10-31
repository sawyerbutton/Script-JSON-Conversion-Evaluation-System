# 剧本JSON转换评估系统 - Docker镜像
# 多阶段构建：支持开发、测试和生产环境

# ============================================
# 基础镜像阶段
# ============================================
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ============================================
# 依赖安装阶段
# ============================================
FROM base as dependencies

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# ============================================
# 开发环境阶段
# ============================================
FROM dependencies as development

# 安装开发工具
RUN pip install \
    ipython \
    jupyter \
    black \
    flake8 \
    mypy \
    pytest-watch \
    ipdb

# 复制项目文件
COPY . .

# 设置环境变量
ENV ENVIRONMENT=development

# 暴露端口（用于Jupyter等）
EXPOSE 8888 8000

# 默认命令
CMD ["python", "scripts/test_system.py"]

# ============================================
# 测试环境阶段
# ============================================
FROM dependencies as test

# 安装测试工具
RUN pip install \
    pytest \
    pytest-cov \
    pytest-asyncio \
    pytest-xdist

# 复制项目文件
COPY . .

# 设置环境变量
ENV ENVIRONMENT=test

# 运行测试
CMD ["pytest", "tests/", "-v", "--cov=src"]

# ============================================
# 生产环境阶段
# ============================================
FROM dependencies as production

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/outputs /app/logs && \
    chown -R appuser:appuser /app

# 复制项目文件
COPY --chown=appuser:appuser . .

# 切换到非root用户
USER appuser

# 设置环境变量
ENV ENVIRONMENT=production \
    PYTHONPATH=/app/src

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# 暴露端口（如果需要Web服务）
EXPOSE 8000

# 启动脚本
COPY --chown=appuser:appuser scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "scripts/test_system.py"]
