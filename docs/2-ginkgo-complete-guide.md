# 🎯 Ginkgo BDD 测试完全指南

本指南详细介绍如何使用 AI Test Agent 生成 Ginkgo BDD 测试，涵盖从基础到高级的所有内容。

---

## 📋 目录

1. [为什么选择 Ginkgo](#为什么选择-ginkgo)
2. [快速开始](#快速开始)
3. [Ginkgo vs 标准 Go Test](#ginkgo-vs-标准-go-test)
4. [测试示例](#测试示例)
5. [混合模式详解](#混合模式详解)
6. [最佳实践](#最佳实践)
7. [运行和调试](#运行和调试)

---

## 为什么选择 Ginkgo

Ginkgo 是 Go 语言的 BDD（行为驱动开发）测试框架，特别适合：

### ✅ 推荐场景

- **Kratos 微服务框架** - 完美支持依赖注入和 Wire
- **复杂业务场景** - 清晰的 Describe/Context/It 结构
- **团队协作** - 测试即文档，易于理解和维护
- **集成测试** - BeforeEach/AfterEach 管理复杂依赖
- **大型项目** - 层次化的测试组织结构

### 核心优势

1. **清晰的业务语义**
   - 测试读起来像自然语言文档
   - Describe/Context/It 结构一目了然

2. **依赖管理简单**
   - BeforeEach/AfterEach 统一管理测试依赖
   - 避免重复的初始化代码

3. **适合微服务**
   - 完美配合 Kratos 的 Wire 依赖注入
   - Mock 对象管理清晰

4. **并发执行**
   - 内置并发测试支持
   - 大幅加快测试速度

5. **丰富的断言**
   - Gomega 提供流畅的断言 API
   - 可读性强，易于维护

---

## 快速开始

### 方法 1: 使用 Python 脚本（最简单）

```bash
python example_kratos.py
```

**选择项目类型：** Ginkgo BDD 测试

### 方法 2: REST API

```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kratos User Service",
    "git_url": "https://github.com/username/kratos-service",
    "language": "golang",
    "test_framework": "ginkgo",
    "source_directory": "internal",
    "test_directory": "internal",
    "coverage_threshold": 80.0
  }'
```

### 方法 3: Python 客户端

```python
from example_client import AITestAgentClient

client = AITestAgentClient()

result = client.run_full_workflow(
    name="Kratos Service",
    git_url="https://github.com/username/kratos-service",
    language="golang",
    test_framework="ginkgo",  # 关键：使用 ginkgo
    coverage_threshold=80.0
)
```

---

## Ginkgo vs 标准 Go Test

### 对比表

| 特性 | go test | Ginkgo |
|------|---------|--------|
| **测试风格** | TDD（测试驱动开发） | BDD（行为驱动开发） |
| **代码可读性** | 中等 | 高（自然语言描述） |
| **依赖注入** | 需要手动管理 | BeforeEach/AfterEach |
| **测试组织** | 扁平结构 | 层次化（Describe/Context） |
| **断言语法** | if/t.Error | Expect().To() |
| **并发测试** | 支持 | 内置完善支持 |
| **适用场景** | 简单单元测试 | 单元测试 + 集成测试 |
| **学习曲线** | 低 | 中等 |
| **Kratos 支持** | 一般 | 优秀 |

### 代码对比

#### 标准 Go Test

```go
func TestUser_Validate(t *testing.T) {
    tests := []struct {
        name    string
        user    User
        wantErr bool
    }{
        {
            name: "valid user",
            user: User{ID: 1, Name: "John", Email: "john@example.com"},
            wantErr: false,
        },
        {
            name: "empty name",
            user: User{ID: 2, Name: "", Email: "test@example.com"},
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := tt.user.Validate()
            if (err != nil) != tt.wantErr {
                t.Errorf("Validate() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

#### Ginkgo BDD

```go
var _ = Describe("User", func() {
    Describe("Validate", func() {
        Context("when user is valid", func() {
            It("should pass validation", func() {
                user := User{ID: 1, Name: "John", Email: "john@example.com"}
                Expect(user.Validate()).To(Succeed())
            })
        })

        Context("when name is empty", func() {
            It("should return error", func() {
                user := User{ID: 2, Name: "", Email: "test@example.com"}
                Expect(user.Validate()).To(HaveOccurred())
            })
        })
    })
})
```

**Ginkgo 的优势：**
- ✅ 更清晰的业务语义
- ✅ 更容易理解测试意图
- ✅ 更易于维护和扩展

---

## 测试示例

### 示例 1: 简单服务测试

**源代码：**

```go
package service

type UserService struct {
    repo UserRepository
}

func (s *UserService) GetUserByID(id int64) (*User, error) {
    if id <= 0 {
        return nil, errors.New("invalid user id")
    }
    return s.repo.FindByID(id)
}
```

**AI 生成的 Ginkgo 测试：**

```go
package service_test

import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "errors"
    "your-project/service"
    "your-project/mocks"
)

var _ = Describe("UserService", func() {
    var (
        userService *service.UserService
        mockRepo    *mocks.MockUserRepository
    )

    BeforeEach(func() {
        // 初始化 Mock 依赖
        mockRepo = mocks.NewMockUserRepository()
        userService = &service.UserService{
            Repo: mockRepo,
        }
    })

    AfterEach(func() {
        // 清理工作
        mockRepo.Reset()
    })

    Describe("GetUserByID", func() {
        Context("when user id is valid", func() {
            It("should return the user", func() {
                // Arrange
                expectedUser := &service.User{
                    ID:   1,
                    Name: "John Doe",
                }
                mockRepo.On("FindByID", int64(1)).Return(expectedUser, nil)

                // Act
                user, err := userService.GetUserByID(1)

                // Assert
                Expect(err).NotTo(HaveOccurred())
                Expect(user).NotTo(BeNil())
                Expect(user.ID).To(Equal(int64(1)))
                Expect(user.Name).To(Equal("John Doe"))
                mockRepo.AssertExpectations(GinkgoT())
            })
        })

        Context("when user id is zero", func() {
            It("should return invalid id error", func() {
                // Act
                user, err := userService.GetUserByID(0)

                // Assert
                Expect(err).To(HaveOccurred())
                Expect(err.Error()).To(Equal("invalid user id"))
                Expect(user).To(BeNil())
            })
        })

        Context("when user id is negative", func() {
            It("should return invalid id error", func() {
                // Act
                user, err := userService.GetUserByID(-1)

                // Assert
                Expect(err).To(HaveOccurred())
                Expect(user).To(BeNil())
            })
        })

        Context("when repository returns error", func() {
            It("should propagate the error", func() {
                // Arrange
                mockRepo.On("FindByID", int64(1)).Return(nil, errors.New("db error"))

                // Act
                user, err := userService.GetUserByID(1)

                // Assert
                Expect(err).To(HaveOccurred())
                Expect(err.Error()).To(ContainSubstring("db error"))
                Expect(user).To(BeNil())
            })
        })
    })
})
```

### 示例 2: Kratos 服务测试

**Kratos gRPC Service：**

```go
package service

import (
    "context"
    pb "your-project/api/user/v1"
)

type UserService struct {
    pb.UnimplementedUserServiceServer
    uc *biz.UserUseCase
}

func NewUserService(uc *biz.UserUseCase) *UserService {
    return &UserService{uc: uc}
}

func (s *UserService) CreateUser(ctx context.Context, req *pb.CreateUserRequest) (*pb.CreateUserReply, error) {
    user, err := s.uc.CreateUser(ctx, &biz.User{
        Name:  req.Name,
        Email: req.Email,
    })
    if err != nil {
        return nil, err
    }
    
    return &pb.CreateUserReply{
        Id:    user.ID,
        Name:  user.Name,
        Email: user.Email,
    }, nil
}
```

**AI 生成的 Ginkgo 测试：**

```go
package service_test

import (
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    "context"
    "errors"
    
    pb "your-project/api/user/v1"
    "your-project/internal/service"
    "your-project/internal/biz"
    "your-project/mocks"
)

var _ = Describe("UserService", func() {
    var (
        svc        *service.UserService
        mockUC     *mocks.MockUserUseCase
        ctx        context.Context
    )

    BeforeEach(func() {
        // 初始化上下文
        ctx = context.Background()
        
        // 创建 Mock UseCase
        mockUC = mocks.NewMockUserUseCase()
        
        // 注入依赖
        svc = service.NewUserService(mockUC)
    })

    AfterEach(func() {
        mockUC.AssertExpectations(GinkgoT())
    })

    Describe("CreateUser", func() {
        var (
            validRequest *pb.CreateUserRequest
        )

        BeforeEach(func() {
            validRequest = &pb.CreateUserRequest{
                Name:  "John Doe",
                Email: "john@example.com",
            }
        })

        Context("when request is valid", func() {
            It("should create user successfully", func() {
                // Arrange
                expectedUser := &biz.User{
                    ID:    1,
                    Name:  "John Doe",
                    Email: "john@example.com",
                }
                mockUC.On("CreateUser", ctx, &biz.User{
                    Name:  "John Doe",
                    Email: "john@example.com",
                }).Return(expectedUser, nil)

                // Act
                reply, err := svc.CreateUser(ctx, validRequest)

                // Assert
                Expect(err).NotTo(HaveOccurred())
                Expect(reply).NotTo(BeNil())
                Expect(reply.Id).To(Equal(int64(1)))
                Expect(reply.Name).To(Equal("John Doe"))
                Expect(reply.Email).To(Equal("john@example.com"))
            })
        })

        Context("when name is empty", func() {
            It("should return validation error", func() {
                // Arrange
                invalidRequest := &pb.CreateUserRequest{
                    Name:  "",
                    Email: "john@example.com",
                }
                mockUC.On("CreateUser", ctx, &biz.User{
                    Name:  "",
                    Email: "john@example.com",
                }).Return(nil, errors.New("name is required"))

                // Act
                reply, err := svc.CreateUser(ctx, invalidRequest)

                // Assert
                Expect(err).To(HaveOccurred())
                Expect(err.Error()).To(ContainSubstring("name is required"))
                Expect(reply).To(BeNil())
            })
        })

        Context("when use case returns error", func() {
            It("should propagate the error", func() {
                // Arrange
                mockUC.On("CreateUser", ctx, &biz.User{
                    Name:  "John Doe",
                    Email: "john@example.com",
                }).Return(nil, errors.New("database error"))

                // Act
                reply, err := svc.CreateUser(ctx, validRequest)

                // Assert
                Expect(err).To(HaveOccurred())
                Expect(err.Error()).To(Equal("database error"))
                Expect(reply).To(BeNil())
            })
        })
    })
})
```

### 常用 Gomega 断言

```go
// 相等断言
Expect(actual).To(Equal(expected))
Expect(actual).NotTo(Equal(unexpected))

// 错误断言
Expect(err).NotTo(HaveOccurred())
Expect(err).To(HaveOccurred())
Expect(err.Error()).To(ContainSubstring("error message"))

// 空值断言
Expect(value).To(BeNil())
Expect(value).NotTo(BeNil())

// 集合断言
Expect(slice).To(ContainElement(item))
Expect(slice).To(HaveLen(5))
Expect(slice).To(BeEmpty())

// 数值断言
Expect(value).To(BeNumerically(">", 10))
Expect(value).To(BeNumerically("<=", 100))

// 布尔断言
Expect(condition).To(BeTrue())
Expect(condition).To(BeFalse())

// 字符串断言
Expect(str).To(ContainSubstring("substring"))
Expect(str).To(HavePrefix("prefix"))
Expect(str).To(HaveSuffix("suffix"))
Expect(str).To(MatchRegexp("pattern"))
```

---

## 混合模式详解

### 🚀 什么是混合模式？

混合模式是专门为 Ginkgo BDD 测试框架设计的创新测试生成策略，结合了本地工具生成和 AI 智能生成的优势。

### 📊 性能对比

| 生成方式 | 速度 | 成本 | 框架正确率 | 测试逻辑质量 |
|---------|------|------|-----------|-------------|
| **纯 AI 生成** | 2-5秒/文件 | $0.02/文件 | 95% | 高 |
| **混合模式** ⭐ | 1-3秒/文件 | $0.012/文件 | 99.9% | 高 |

**提升幅度：**
- ⚡ 速度提升：**40-50%**
- 💰 成本降低：**30-40%**
- ✅ 框架准确率：**99.9%**

### 🔧 工作原理

#### 传统纯 AI 模式

```
AI 生成完整文件
├── package 声明
├── import 语句
├── 测试套件注册
└── 测试逻辑（Describe/It）
```

#### 混合模式（推荐）

```
第一阶段：本地生成框架（<0.1秒）
├── package 声明
├── import 语句
└── 测试套件注册

第二阶段：AI 只生成测试逻辑（1-2秒）
└── 测试逻辑（Describe/It）

最终合并：框架 + 测试逻辑
```

### 适用场景

**✅ 推荐使用混合模式：**
- Ginkgo BDD 测试框架
- Kratos 微服务项目
- 需要大量生成测试的项目
- 对成本敏感的场景

**❌ 自动回退到纯 AI 模式：**
- 标准 Go test 框架（不支持混合模式）
- 混合模式生成失败时自动回退
- C/C++ 测试（暂不支持混合模式）

### 使用方法

**混合模式已默认启用**，无需额外配置：

```python
# 自动使用混合模式
project_data = {
    "name": "My Kratos Service",
    "language": "golang",
    "test_framework": "ginkgo",  # 自动使用混合模式
    "git_url": "https://github.com/user/repo.git"
}

response = requests.post("http://localhost:8000/api/projects", json=project_data)
```

### 生成的代码示例

**框架部分（本地生成，<0.1秒）：**

```go
package biz_test

import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
    
    "github.com/your-org/your-project/internal/biz"
)

func TestBiz(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Biz Suite")
}
```

**测试逻辑部分（AI 生成，1-2秒）：**

```go
var _ = Describe("UserService", func() {
    var (
        svc    *biz.UserService
        mockUC *mocks.MockUserUseCase
        ctx    context.Context
    )
    
    BeforeEach(func() {
        ctx = context.Background()
        mockUC = mocks.NewMockUserUseCase()
        svc = biz.NewUserService(mockUC)
    })
    
    Describe("CreateUser", func() {
        Context("when request is valid", func() {
            It("should create user successfully", func() {
                // 测试逻辑...
            })
        })
    })
})
```

---

## 最佳实践

### 1. 项目结构建议

对于 Kratos 项目，推荐以下测试目录结构：

```
your-project/
├── go.mod                          # 必需
├── internal/
│   ├── service/
│   │   ├── user.go
│   │   └── user_test.go          # Ginkgo 测试
│   ├── biz/
│   │   ├── user.go
│   │   └── user_test.go          # Ginkgo 测试
│   └── data/
│       ├── user.go
│       └── user_test.go          # Ginkgo 测试
├── mocks/                         # Mock 对象
│   ├── mock_repository.go
│   └── mock_usecase.go
└── test/
    └── suite_test.go              # 测试套件入口
```

### 2. 测试套件初始化

如果需要为整个包设置测试套件，创建 `suite_test.go`：

```go
package service_test

import (
    "testing"
    
    . "github.com/onsi/ginkgo/v2"
    . "github.com/onsi/gomega"
)

func TestService(t *testing.T) {
    RegisterFailHandler(Fail)
    RunSpecs(t, "Service Suite")
}
```

### 3. Mock 依赖注入

#### 定义接口

```go
// internal/biz/user.go
type UserRepository interface {
    FindByID(ctx context.Context, id int64) (*User, error)
    Create(ctx context.Context, user *User) error
}

type UserUseCase struct {
    repo UserRepository
}

func NewUserUseCase(repo UserRepository) *UserUseCase {
    return &UserUseCase{repo: repo}
}
```

#### 创建 Mock 实现

使用 [mockery](https://github.com/vektra/mockery) 或手动创建：

```go
// mocks/user_repository.go
type MockUserRepository struct {
    mock.Mock
}

func (m *MockUserRepository) FindByID(ctx context.Context, id int64) (*biz.User, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*biz.User), args.Error(1)
}
```

#### 在测试中使用

```go
var _ = Describe("UserUseCase", func() {
    var (
        uc       *biz.UserUseCase
        mockRepo *mocks.MockUserRepository
    )

    BeforeEach(func() {
        mockRepo = &mocks.MockUserRepository{}
        uc = biz.NewUserUseCase(mockRepo)
    })

    It("should work", func() {
        mockRepo.On("FindByID", mock.Anything, int64(1)).Return(&biz.User{ID: 1}, nil)
        // 测试逻辑...
    })
})
```

### 4. 确保 Go 环境正确

```bash
# 确保 go.mod 存在且正确
cat go.mod
# 应该包含: module github.com/your-org/your-project
```

### 5. 性能优化建议

对于大型项目（50+ 文件）：

```python
# 调整并发数
"max_concurrent_generations": 15  # 可提高到 15-20
```

---

## 运行和调试

### 安装 Ginkgo CLI

```bash
go install github.com/onsi/ginkgo/v2/ginkgo@latest
```

### 常用命令

```bash
# 运行测试
ginkgo -r -v

# 运行并生成覆盖率
ginkgo -r -v --cover --coverprofile=coverage.out

# 查看覆盖率
go tool cover -html=coverage.out

# 并发运行
ginkgo -r -v -p

# 运行特定测试
ginkgo -r -v --focus="CreateUser"

# 跳过特定测试
ginkgo -r -v --skip="integration"

# 监听文件变化自动运行
ginkgo watch -r
```

### CI/CD 集成

**GitHub Actions：**

```yaml
- name: Run Ginkgo Tests
  run: |
    go install github.com/onsi/ginkgo/v2/ginkgo@latest
    ginkgo -r -v --cover --coverprofile=coverage.out
    
- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    files: ./coverage.out
```

**GitLab CI：**

```yaml
test:
  script:
    - go install github.com/onsi/ginkgo/v2/ginkgo@latest
    - ginkgo -r -v --cover --coverprofile=coverage.out
  coverage: '/coverage: \d+.\d+% of statements/'
```

### 监控混合模式日志

```bash
# 查看 Celery worker 日志
docker-compose logs -f celery-worker

# 混合模式启用时会看到
🚀 使用混合模式为 config.go 生成Ginkgo测试
✅ 混合模式生成完成: config.go
```

### 故障排查

#### 问题：混合模式总是失败

**可能原因：**
1. 无法推断 Go 模块路径
2. test_dir 参数未正确传递

**解决方法：**

```bash
# 检查日志
docker-compose logs celery-worker | grep "混合模式"

# 验证 go.mod 存在
ls -la go.mod
```

#### 问题：生成的 import 路径错误

**解决方法：**

确保 `go.mod` 文件在仓库根目录：

```go
module github.com/your-org/your-project

go 1.21
```

---

## 📚 参考资源

- **[Ginkgo 官方文档](https://onsi.github.io/ginkgo/)** - 完整的框架文档
- **[Gomega 官方文档](https://onsi.github.io/gomega/)** - 断言库文档
- **[Kratos 官方文档](https://go-kratos.dev/)** - 微服务框架文档
- **[Go 测试最佳实践](https://go.dev/doc/tutorial/add-a-test)** - 官方指南

---

## 🎉 总结

Ginkgo BDD 测试框架为 Go 项目提供了：

✅ **清晰的业务语义** - Describe/Context/It 结构  
✅ **简化依赖管理** - BeforeEach/AfterEach  
✅ **完美支持 Kratos** - Wire 依赖注入  
✅ **混合模式加速** - 速度提升 40-50%  
✅ **丰富的断言** - Gomega 流畅 API  
✅ **并发执行** - 加快测试速度  

结合 AI Test Agent 的混合模式，您可以快速生成高质量的 Ginkgo BDD 测试！🚀

