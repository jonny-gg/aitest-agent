#!/bin/bash

# AI Test Agent 快速配置脚本

set -e

echo "================================================"
echo "  AI Test Agent - 快速配置向导"
echo "================================================"
echo ""

# 检查是否已存在.env文件
if [ -f ".env" ]; then
    echo "⚠️  发现已存在的 .env 文件"
    read -p "是否覆盖? (y/N): " overwrite
    if [[ ! "$overwrite" =~ ^[Yy]$ ]]; then
        echo "已取消。"
        exit 0
    fi
fi

# 复制模板
echo "📋 复制配置模板..."
cp env.example .env

echo ""
echo "================================================"
echo "  请提供以下配置信息"
echo "================================================"
echo ""

# OpenAI API Key
echo "【必需】OpenAI API 密钥"
echo "提示: 在 https://platform.openai.com/api-keys 获取"
read -p "请输入 OpenAI API Key: " openai_key

if [ -n "$openai_key" ]; then
    # macOS 使用 sed -i ''
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$openai_key|g" .env
    else
        sed -i "s|OPENAI_API_KEY=.*|OPENAI_API_KEY=$openai_key|g" .env
    fi
    echo "✅ OpenAI API Key 已配置"
else
    echo "⚠️  未设置 API Key，稍后请手动编辑 .env 文件"
fi

echo ""

# 数据库密码
echo "【推荐】数据库密码"
echo "提示: 生产环境建议修改默认密码"
read -p "设置 PostgreSQL 密码 (留空使用默认): " postgres_pass

if [ -n "$postgres_pass" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$postgres_pass|g" .env
    else
        sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$postgres_pass|g" .env
    fi
    echo "✅ 数据库密码已设置"
fi

echo ""

# Git配置
echo "【可选】Git 自动提交配置"
echo "提示: 如需自动提交测试代码到GitHub，请配置"
read -p "是否配置 Git 认证? (y/N): " config_git

if [[ "$config_git" =~ ^[Yy]$ ]]; then
    read -p "GitHub 用户名: " git_user
    read -sp "GitHub Token: " git_token
    echo ""
    
    if [ -n "$git_user" ] && [ -n "$git_token" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "s|GIT_USERNAME=.*|GIT_USERNAME=$git_user|g" .env
            sed -i '' "s|GIT_TOKEN=.*|GIT_TOKEN=$git_token|g" .env
        else
            sed -i "s|GIT_USERNAME=.*|GIT_USERNAME=$git_user|g" .env
            sed -i "s|GIT_TOKEN=.*|GIT_TOKEN=$git_token|g" .env
        fi
        echo "✅ Git 认证已配置"
    fi
fi

echo ""
echo "================================================"
echo "  配置完成！"
echo "================================================"
echo ""
echo "📝 配置文件已保存到: .env"
echo ""
echo "下一步:"
echo "  1. 检查配置: cat .env"
echo "  2. 启动服务: docker-compose up -d"
echo "  3. 验证服务: curl http://localhost:8000/health"
echo "  4. 查看文档: cat QUICKSTART.md"
echo ""
echo "🚀 准备就绪！运行以下命令启动:"
echo "   docker-compose up -d"
echo ""

