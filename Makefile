# Makefile for Script JSON Conversion Evaluation System
# 简化Docker命令，支持开发、测试和生产环境

.PHONY: help build up down restart logs shell test clean

# 默认目标
.DEFAULT_GOAL := help

# 颜色定义
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

##@ 帮助

help: ## 显示帮助信息
	@echo "$(BLUE)剧本JSON转换评估系统 - Docker命令$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "使用方式:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ 开发环境

dev-build: ## 构建开发环境镜像
	@echo "$(GREEN)构建开发环境镜像...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

dev-up: ## 启动开发环境（带Jupyter）
	@echo "$(GREEN)启动开发环境...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "$(GREEN)✓ 开发环境已启动$(NC)"
	@echo "$(BLUE)  - 应用容器: docker exec -it script-eval-app bash$(NC)"
	@echo "$(BLUE)  - Jupyter: http://localhost:8888$(NC)"

dev-shell: ## 进入开发容器Shell
	@echo "$(GREEN)进入开发容器...$(NC)"
	docker exec -it script-eval-app /bin/bash

dev-jupyter: ## 只启动Jupyter
	@echo "$(GREEN)启动Jupyter...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d jupyter
	@echo "$(GREEN)✓ Jupyter已启动: http://localhost:8888$(NC)"

dev-vscode: ## 启动VS Code Server
	@echo "$(GREEN)启动VS Code Server...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile vscode up -d vscode
	@echo "$(GREEN)✓ VS Code Server已启动: http://localhost:8080$(NC)"

dev-down: ## 停止开发环境
	@echo "$(YELLOW)停止开发环境...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

dev-logs: ## 查看开发环境日志
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml logs -f

##@ 测试环境

test-build: ## 构建测试环境镜像
	@echo "$(GREEN)构建测试环境镜像...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml build

test-all: ## 运行所有测试
	@echo "$(GREEN)运行所有测试...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm app

test-unit: ## 运行单元测试
	@echo "$(GREEN)运行单元测试...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml --profile test run --rm unit-test

test-integration: ## 运行集成测试
	@echo "$(GREEN)运行集成测试...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml --profile test run --rm integration-test

test-system: ## 运行系统测试
	@echo "$(GREEN)运行系统测试...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml --profile test run --rm system-test

test-coverage: ## 生成测试覆盖率报告
	@echo "$(GREEN)生成测试覆盖率报告...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.test.yml run --rm app
	@echo "$(GREEN)✓ 覆盖率报告已生成: htmlcov/index.html$(NC)"

##@ 生产环境

prod-build: ## 构建生产环境镜像
	@echo "$(GREEN)构建生产环境镜像...$(NC)"
	VERSION=$$(git describe --tags --always) docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

prod-up: ## 启动生产环境
	@echo "$(GREEN)启动生产环境...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "$(GREEN)✓ 生产环境已启动$(NC)"

prod-down: ## 停止生产环境
	@echo "$(YELLOW)停止生产环境...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

prod-logs: ## 查看生产环境日志
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml logs -f

prod-restart: ## 重启生产环境
	@echo "$(YELLOW)重启生产环境...$(NC)"
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml restart

prod-status: ## 查看生产环境状态
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps

##@ 通用命令

build: dev-build ## 构建镜像（默认开发环境）

up: dev-up ## 启动服务（默认开发环境）

down: dev-down ## 停止服务（默认开发环境）

restart: ## 重启服务
	@echo "$(YELLOW)重启服务...$(NC)"
	docker-compose restart

logs: dev-logs ## 查看日志（默认开发环境）

shell: dev-shell ## 进入容器Shell（默认开发环境）

ps: ## 查看运行中的容器
	docker-compose ps

##@ 维护命令

clean: ## 清理容器、镜像和卷
	@echo "$(RED)清理Docker资源...$(NC)"
	@read -p "确定要清理所有Docker资源吗？(y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down -v --remove-orphans; \
		docker image prune -f; \
		docker volume prune -f; \
		echo "$(GREEN)✓ 清理完成$(NC)"; \
	else \
		echo "$(YELLOW)已取消$(NC)"; \
	fi

clean-outputs: ## 清理输出文件
	@echo "$(YELLOW)清理输出文件...$(NC)"
	rm -rf outputs/* htmlcov/* .pytest_cache/
	@echo "$(GREEN)✓ 输出文件已清理$(NC)"

clean-all: clean clean-outputs ## 清理所有（Docker + 输出文件）

prune: ## 清理未使用的Docker资源
	@echo "$(YELLOW)清理未使用的Docker资源...$(NC)"
	docker system prune -f
	@echo "$(GREEN)✓ 清理完成$(NC)"

##@ 实用工具

fmt: ## 格式化代码（在容器中运行black）
	@echo "$(GREEN)格式化代码...$(NC)"
	docker-compose run --rm app black src/ tests/

lint: ## 代码检查（在容器中运行flake8）
	@echo "$(GREEN)代码检查...$(NC)"
	docker-compose run --rm app flake8 src/ tests/

type-check: ## 类型检查（在容器中运行mypy）
	@echo "$(GREEN)类型检查...$(NC)"
	docker-compose run --rm app mypy src/

install: ## 安装项目到容器
	@echo "$(GREEN)安装项目...$(NC)"
	docker-compose run --rm app pip install -e .

requirements: ## 更新requirements.txt
	@echo "$(GREEN)更新requirements.txt...$(NC)"
	docker-compose run --rm app pip freeze > requirements.txt
	@echo "$(GREEN)✓ requirements.txt已更新$(NC)"

##@ 快速开始

quickstart: ## 快速开始（构建并启动开发环境）
	@echo "$(BLUE)=== 快速开始 ===$(NC)"
	@echo "$(GREEN)1. 构建镜像...$(NC)"
	@make dev-build
	@echo "$(GREEN)2. 启动服务...$(NC)"
	@make dev-up
	@echo ""
	@echo "$(GREEN)✓ 开发环境已就绪！$(NC)"
	@echo ""
	@echo "$(BLUE)接下来你可以:$(NC)"
	@echo "  $(CYAN)make dev-shell$(NC)     - 进入开发容器"
	@echo "  $(CYAN)make test-all$(NC)      - 运行测试"
	@echo "  $(CYAN)make dev-logs$(NC)      - 查看日志"
	@echo "  Jupyter: http://localhost:8888"

##@ 信息

info: ## 显示系统信息
	@echo "$(BLUE)=== 系统信息 ===$(NC)"
	@echo "Docker版本:"
	@docker --version
	@echo ""
	@echo "Docker Compose版本:"
	@docker-compose --version
	@echo ""
	@echo "运行中的容器:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "磁盘使用:"
	@docker system df

version: ## 显示项目版本
	@echo "$(BLUE)=== 项目版本 ===$(NC)"
	@echo "Git版本: $$(git describe --tags --always 2>/dev/null || echo 'N/A')"
	@echo "Git分支: $$(git branch --show-current 2>/dev/null || echo 'N/A')"
	@echo "最后提交: $$(git log -1 --pretty=format:'%h - %s (%cr)' 2>/dev/null || echo 'N/A')"
