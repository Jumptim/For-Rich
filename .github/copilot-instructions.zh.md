# LEAN 算法交易引擎 - AI 编码指南

## 项目概览
LEAN 是一个事件驱动的、模块化的算法交易引擎，使用 C# 构建，通过 pythonnet 支持 Python。该架构将关注点分离到不同的项目中：Algorithm 定义、Engine 执行、Data 管理、Brokerages 以及支持基础设施。

## 架构与组件结构

### 核心模块分离
- **Algorithm/**: 基础 `QCAlgorithm` 类 - 所有算法都继承自此类。定义核心方法如 `Initialize()`、`OnData()`、交易 API（`SetHoldings`、`MarketOrder`）以及 universe selection
- **Algorithm.CSharp/**: C# 算法示例，展示各种功能。文件名前缀 "Add" 展示特定 API 能力。后缀 "RegressionAlgorithm" 表示有自动化测试覆盖
- **Algorithm.Python/**: Python 算法示例，模式与 C# 版本相同
- **Algorithm.Framework/**: 可插拔的 framework 组件 - `AlphaModel`、`PortfolioConstructionModel`、`ExecutionModel`、`RiskManagementModel`。通过 `SetAlpha()`、`SetPortfolioConstruction()` 等方法使用
- **Engine/**: 核心执行引擎。运行算法、管理时间、处理数据源、执行订单。使用 pythonnet 支持 Python 算法
- **Common/**: 共享数据结构（`Symbol`、`Security`、`Order`、`Bar`、市场数据类型）。不依赖其他 LEAN 项目
- **Data/**: 市场数据处理、consolidators、universe 定义
- **Brokerages/**: Brokerage 集成，使用通用 `IBrokerage` 接口
- **Indicators/**: 技术指标，继承 `IndicatorBase<T>`
- **Tests/**: NUnit 测试，使用 `[Test]` 特性。Regression tests 验证端到端算法行为

### 关键数据流
1. Engine 通过 AlgorithmFactory 加载算法
2. Data feeds（SubscriptionManager）提供时间同步的市场数据
3. Algorithm 通过 `OnData(Slice data)` 回调接收数据
4. Algorithm 向 TransactionManager 发出订单
5. 订单通过 brokerage 连接执行
6. 结果在 ResultsHandler 中聚合

## 开发工作流

### 构建与运行
```bash
# 构建整个解决方案
dotnet build QuantConnect.Lean.sln

# 从 Launcher 运行（在 config.json 中配置算法）
cd Launcher/bin/Debug
dotnet QuantConnect.Lean.Launcher.dll
```

VS Code 可用任务：`build`、`rebuild`、`clean`（都使用 dotnet CLI 的 Debug 配置）

### 测试策略
- 使用 NUnit framework，带 `[Test]` 特性
- Algorithm.CSharp/ 中的 regression algorithms 是实际的回测，用于验证行为
- 所有 PR 必须附带测试 - 暴露 bug 或演示新功能
- 运行：`dotnet test`

### Python 集成
- Python 算法通过 pythonnet 编译（参见 Engine 引用 `QuantConnect.pythonnet`）
- Python 代码必须遵循与 C# 相同的结构（`Initialize()`、`OnData()`）
- Python 算法位于 Algorithm.Python/

## 编码约定与模式

### Algorithm 结构模式
```csharp
public class MyAlgorithm : QCAlgorithm
{
    public override void Initialize()
    {
        SetStartDate(2020, 1, 1);
        SetCash(100000);
        AddEquity("SPY", Resolution.Daily);
        // 配置 universe、framework models
    }

    public override void OnData(Slice data)
    {
        // 主要交易逻辑
        if (!Portfolio.Invested)
        {
            SetHoldings("SPY", 1.0);
        }
    }
}
```

### Framework Model 模式
Framework models 分离关注点 - 继承自基类：
- `AlphaModel.Update()` - 生成 `Insight` 对象，包含方向性预测
- `PortfolioConstructionModel.CreateTargets()` - 将 insights 转换为 `PortfolioTarget` 权重
- `ExecutionModel.Execute()` - 用实际订单填充 targets
- `RiskManagementModel.ManageRisk()` - 根据风险规则调整 targets

示例：[AddAlphaModelAlgorithm.cs](Algorithm.CSharp/AddAlphaModelAlgorithm.cs) 展示如何组合多个 alpha models

### 代码风格
- 遵循 Microsoft C# 指南（参见 [CONTRIBUTING.md](CONTRIBUTING.md)）
- 4 个空格缩进（软制表符）
- Framework modules 中禁止 logging/debugging - 保持生产代码静默
- Framework modules 应该专注于一个任务（关注点分离）

### Symbol 处理
使用 `Symbol` 对象，而非字符串：
```csharp
var spy = Symbol.Create("SPY", SecurityType.Equity, Market.USA);
AddEquity(spy);
```

### 配置
- Algorithm 行为通过 Launcher 中的 `config.json` 控制
- 指定 algorithm class、数据目录、brokerage 设置
- 参见 [.vscode/readme.md](.vscode/readme.md) 了解 IDE 特定设置

## 项目特定约定

### 命名约定
- Regression algorithms：`*RegressionAlgorithm.cs`
- 功能演示：`Add*Algorithm.cs`（例如 `AddAlphaModelAlgorithm.cs`）
- Framework modules：`*AlphaModel`、`*PortfolioConstructionModel`、`*ExecutionModel`

### 依赖规则
- Common/ 零 LEAN 项目依赖（仅外部 NuGet）
- Engine 依赖 Algorithm、Brokerages、Data 等
- Algorithm 项目不应依赖 Engine
- Tests 可以引用任何项目

### 数据组织
- 市场数据存储在 `Data/` 目录（不在 repo 中）
- 使用 resolution 类型：`Tick`、`Second`、`Minute`、`Hour`、`Daily`
- 通过 `History()` API 或 `OnData()` 回调访问数据

## CLI 工具（与 Engine 分离）
用户通常通过 `lean` CLI 交互（基于 Python，通过 pip 安装）：
- `lean backtest` - 在 Docker 中运行回测
- `lean research` - 启动 Jupyter notebooks
- `lean live` - 部署实盘交易
这与 C# LEAN engine 代码库是分离的

## 常见陷阱
- 不要将 LEAN 作为库从其他项目调用 - 它被设计为独立引擎
- Framework models 必须避免 logging/charting - 用户在 algorithm class 中完成这些
- 始终使用 `Symbol` 对象引用证券，而非原始字符串
- Tests 必须可重现 - 避免外部依赖或当前时间
- Python 算法必须匹配 C# API 表面（Initialize、OnData、相同的方法名）

## 关键参考文件
- [QCAlgorithm.cs](Algorithm/QCAlgorithm.cs) - 主要 algorithm 基类 API
- [CONTRIBUTING.md](CONTRIBUTING.md) - 分支工作流、PR 要求
- [QuantConnect.Lean.sln](QuantConnect.Lean.sln) - 解决方案结构
