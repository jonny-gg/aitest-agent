# Go 版本动态管理功能

## 概述

本系统现已支持根据项目的 `go.mod` 文件自动检测并切换到所需的 Go 版本，确保测试在正确的 Go 环境下运行。

## 核心特性

### 1. 自动版本检测
系统会在执行测试前自动读取项目的 `go.mod` 文件，提取其中声明的 Go 版本：

```go
// go.mod 示例
module github.com/example/project

go 1.20  // 系统会检测到需要 Go 1.20
```

### 2. 多版本管理方案

#### 方案一：GVM (Go Version Manager) - 推荐
使用 GVM 管理多个 Go 版本，支持快速切换：

- **预装版本**: 
  - Go 1.20.14
  - Go 1.21.13
  - Go 1.22.5
  - Go 1.23.2

- **动态安装**: 如果需要的版本未预装，系统会自动下载安装

- **版本切换**: 自动执行 `gvm use goX.XX` 切换到所需版本

#### 方案二：GOTOOLCHAIN - 备用方案
当 GVM 不可用时，使用 Go 1.21+ 的原生工具链管理功能：

```bash
export GOTOOLCHAIN=go1.20
```

Go 会自动下载并使用指定版本的工具链。

## 工作流程

```
开始测试
    ↓
检测 go.mod 文件
    ↓
提取 Go 版本要求 (如: 1.20)
    ↓
检查当前 Go 版本
    ↓
版本匹配? ──[是]──→ 继续执行测试
    ↓[否]
检查 GVM 是否可用
    ↓
GVM 可用? ──[是]──→ 使用 GVM 切换版本
    ↓[否]              ↓
使用 GOTOOLCHAIN       验证切换成功
    ↓                  ↓
继续执行测试 ←─────────┘
```

## 技术实现

### 修改的文件

#### 1. `backend/Dockerfile`
```dockerfile
# 安装 GVM (Go Version Manager)
RUN bash -c "bash < <(curl -s -S -L https://raw.githubusercontent.com/moovweb/gvm/master/binscripts/gvm-installer)"

# 预装常用 Go 版本
RUN bash -c "source ${GVM_ROOT}/scripts/gvm && \
    gvm install go1.4 -B && \
    gvm use go1.4 --default && \
    gvm install go1.20.14 && \
    gvm install go1.21.13 && \
    gvm install go1.22.5 && \
    gvm install go1.23.2 && \
    gvm use go1.21.13 --default"
```

#### 2. `backend/app/services/test_executor.py`

新增的核心方法：

- `_detect_go_version_from_mod()`: 从 go.mod 检测版本
- `_check_gvm_available()`: 检查 GVM 是否可用
- `_install_go_version_with_gvm()`: 使用 GVM 安装指定版本
- `_setup_go_version()`: 设置/切换 Go 版本（整合多种方案）

修改的方法：
- `_run_command()`: 新增 `use_bash` 参数支持 GVM 环境
- `execute_tests()`: 在测试前自动检测并设置 Go 版本
- 所有 Go 命令执行都改为使用 `use_bash=True`

## 使用示例

### 示例 1：项目使用 Go 1.20
```
项目结构：
├── go.mod (声明 go 1.20)
├── main.go
└── main_test.go

执行流程：
1. 系统检测到 go.mod 中的 "go 1.20"
2. 当前环境是 Go 1.21.13
3. 使用 GVM 切换到 Go 1.20.14
4. 执行测试
```

### 示例 2：项目使用 Go 1.23
```
项目结构：
├── go.mod (声明 go 1.23)
├── main.go
└── main_test.go

执行流程：
1. 系统检测到 go.mod 中的 "go 1.23"
2. 检查 GVM 中是否已安装 Go 1.23
3. 已预装 Go 1.23.2，直接切换
4. 执行测试
```

### 示例 3：项目使用未预装版本（如 Go 1.19）
```
执行流程：
1. 系统检测到 go.mod 中的 "go 1.19"
2. 检查 GVM，发现未安装
3. 自动执行 gvm install go1.19.x
4. 切换到新安装的版本
5. 执行测试
```

## 日志输出示例

```
[INFO] 执行Go测试: 10 个文件 (框架: ginkgo)
[INFO] ✅ 检测到项目Go版本: 1.20
[INFO] 当前Go版本: go version go1.21.13 linux/amd64
[INFO] 当前Go版本号: 1.21, 需要版本: 1.20
[INFO] ⚠️  当前Go版本 1.21 与项目要求 1.20 不匹配
[INFO] ✅ GVM 可用
[INFO] 使用 GVM 切换到 Go 1.20...
[INFO] ✅ Go 1.20 已安装
[INFO] ✅ 已通过 GVM 切换到 Go 1.20
[INFO] 验证版本: go version go1.20.14 linux/amd64
[INFO] 执行命令: ginkgo -r -v --cover ...
```

## 优势

1. **自动化**: 无需手动管理 Go 版本，系统自动适配
2. **兼容性**: 确保测试在正确的 Go 版本下运行，避免版本不匹配问题
3. **灵活性**: 支持任意 Go 版本，包括新发布的版本
4. **容错性**: 多重备用方案，确保在不同环境下都能工作
5. **透明性**: 详细的日志输出，便于调试和监控

## 环境变量

系统自动设置以下环境变量：

```bash
GVM_ROOT=/root/.gvm
GOPATH=/root/go
GO111MODULE=on
GOPRIVATE=bt.baishancloud.com/*
GONOSUMDB=bt.baishancloud.com/*
GOPROXY=https://goproxy.cn,direct
```

## 故障排查

### 问题 1：GVM 安装失败
**症状**: 日志显示 "⚠️  GVM 不可用，将使用备用方案"

**解决方案**: 
- 系统会自动回退到 GOTOOLCHAIN 方案
- 或使用预装的默认 Go 版本

### 问题 2：无法安装特定版本
**症状**: 日志显示 "⚠️  无法找到可安装的 Go X.XX 版本"

**解决方案**:
- 系统会尝试使用 GOTOOLCHAIN 自动下载
- 或使用最接近的已安装版本

### 问题 3：版本切换不生效
**症状**: 切换后 `go version` 仍显示旧版本

**解决方案**:
- 检查是否正确加载了 GVM 脚本
- 确保所有 Go 命令都通过 `use_bash=True` 执行

## 扩展支持

### 添加新的 Go 版本
编辑 `backend/Dockerfile`：

```dockerfile
RUN bash -c "source ${GVM_ROOT}/scripts/gvm && \
    gvm install go1.24.0 && \  # 添加新版本
    ..."
```

### 修改默认版本
```dockerfile
gvm use go1.22.5 --default  # 修改默认版本
```

## 兼容性

- **支持的 Go 版本**: 1.4 及以上所有版本
- **测试框架**: 
  - 标准 `go test`
  - Ginkgo BDD 框架
- **操作系统**: Linux (容器环境)
- **架构**: amd64

## 注意事项

1. **首次构建时间**: 由于需要安装多个 Go 版本，首次构建 Docker 镜像可能需要较长时间
2. **磁盘空间**: 多个 Go 版本会占用额外的磁盘空间（每个版本约 100-150MB）
3. **网络依赖**: 首次安装 GVM 和下载 Go 版本需要网络连接
4. **版本匹配**: 系统会匹配主版本号（如 1.20），具体补丁版本（如 1.20.14）可能不完全一致

## 更新日志

### 2025-10-27
- ✅ 集成 GVM (Go Version Manager)
- ✅ 实现自动版本检测和切换
- ✅ 预装常用 Go 版本 (1.20, 1.21, 1.22, 1.23)
- ✅ 添加 GOTOOLCHAIN 备用方案
- ✅ 修改所有 Go 命令执行以支持 GVM 环境
- ✅ 添加详细的日志输出和错误处理

## 参考资料

- [GVM 官方文档](https://github.com/moovweb/gvm)
- [Go 工具链管理](https://go.dev/doc/toolchain)
- [go.mod 文件规范](https://go.dev/ref/mod#go-mod-file-go)

