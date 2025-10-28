#!/bin/bash
set -e

# 创建临时 SSH 目录（可写）
SSH_DIR="/tmp/.ssh"
mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

# 复制 SSH 密钥到可写位置
if [ -f /root/.ssh/id_rsa ]; then
    cp /root/.ssh/id_rsa "$SSH_DIR/id_rsa"
    chmod 600 "$SSH_DIR/id_rsa"
fi

# 复制 SSH config
if [ -f /root/.ssh/config ]; then
    cp /root/.ssh/config "$SSH_DIR/config"
    chmod 600 "$SSH_DIR/config"
fi

# 复制 known_hosts
if [ -f /root/.ssh/known_hosts ]; then
    cp /root/.ssh/known_hosts "$SSH_DIR/known_hosts"
    chmod 644 "$SSH_DIR/known_hosts"
fi

# 配置 Git 使用 SSH（运行时再次确认）
git config --global url."ssh://git@bt.baishancloud.com:7999/".insteadOf "https://bt.baishancloud.com/"

# 配置 SSH 使用临时目录
export GIT_SSH_COMMAND="ssh -i $SSH_DIR/id_rsa -F $SSH_DIR/config -o UserKnownHostsFile=$SSH_DIR/known_hosts -o StrictHostKeyChecking=no"

# 启动 SSH agent 并添加密钥
eval $(ssh-agent -s)
if [ -f "$SSH_DIR/id_rsa" ]; then
    ssh-add "$SSH_DIR/id_rsa" 2>/dev/null || true
fi

# 执行传入的命令
exec "$@"

