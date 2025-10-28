FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    g++ \
    make \
    cmake \
    lcov \
    curl \
    wget \
    bison \
    bzip2 \
    openssh-client \
    bsdmainutils \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# 直接安装 Go 1.23.7
RUN curl -OL https://go.dev/dl/go1.23.7.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.23.7.linux-amd64.tar.gz && \
    rm go1.23.7.linux-amd64.tar.gz

# 设置Go环境变量
ENV GOPATH="/root/go"
ENV GO111MODULE=on
ENV GOPRIVATE=bt.baishancloud.com/*
ENV GONOSUMDB=bt.baishancloud.com/*
ENV GOPROXY=https://goproxy.cn,direct
ENV PATH="/usr/local/go/bin:${GOPATH}/bin:${PATH}"

# 配置 Git 使用 SSH 访问私有仓库
RUN git config --global url."ssh://git@bt.baishancloud.com:7999/".insteadOf "https://bt.baishancloud.com/" && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh

# 安装Ginkgo和Gomega（BDD测试框架）
RUN go install github.com/onsi/ginkgo/v2/ginkgo@latest && \
    go install github.com/onsi/gomega/...@latest

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/workspace /app/reports /app/logs

# 暴露端口
EXPOSE 8000

# 使用 entrypoint 脚本
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# 默认命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

