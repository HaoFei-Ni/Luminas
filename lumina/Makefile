# Makefile — lumina Python 工具链本地入口
# 缓存统一收敛至 .cache/（测试源码在 tests/）；命令经 uv run，保证与 pyproject 锁版一致。
# 入口：make lint / make test / make test-ci / make all / make clean-cache

SHELL := /bin/bash
CACHE_ROOT := ./.cache

export UV_CACHE_DIR := $(CACHE_ROOT)/uv
export HF_HOME := $(CACHE_ROOT)/huggingface
export HUGGINGFACE_HUB_CACHE := $(CACHE_ROOT)/huggingface/hub
export TORCH_HOME := $(CACHE_ROOT)/torch

CACHE_SUBDIRS := ruff pytest mypy uv huggingface torch hypothesis

.PHONY: all prep-cache lint test test-ci test-cov clean-cache help

all: prep-cache lint test

prep-cache:
	mkdir -p $(foreach d,$(CACHE_SUBDIRS),$(CACHE_ROOT)/$(d))

# 静态：Ruff 检查 + 格式校验（配置取自 pyproject.toml）
lint: prep-cache
	uv run ruff check .
	uv run ruff format . --check
	uv run mypy .

# 单元/集成测试（纯 Python 必绿；native/cuda 缺扩展时 skip）
test: prep-cache
	uv run pytest

# CI 确定性档：Hypothesis derandomize + xdist + JUnit
test-ci: prep-cache
	HYPOTHESIS_PROFILE=ci uv run pytest -n auto --junitxml=$(CACHE_ROOT)/pytest/junit.xml

# 覆盖率（quality_metrics 公共面，fail_under 见 pyproject）
test-cov: prep-cache
	uv run pytest --cov --cov-report=term-missing --cov-report=xml:$(CACHE_ROOT)/pytest/coverage.xml

clean-cache:
	rm -rf $(CACHE_ROOT)/*
	mkdir -p $(foreach d,$(CACHE_SUBDIRS),$(CACHE_ROOT)/$(d))

help:
	@echo "可用命令："
	@echo "  make all        lint + test"
	@echo "  make lint       ruff + mypy"
	@echo "  make test       pytest（本地默认）"
	@echo "  make test-ci    pytest CI 档（-n auto + junit）"
	@echo "  make test-cov   pytest + coverage"
	@echo "  make clean-cache 清空 .cache/"
