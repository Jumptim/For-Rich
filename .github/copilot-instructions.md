# LEAN Algorithmic Trading Engine - AI Coding Guide

## Project Overview
LEAN is an event-driven, modular algorithmic trading engine built in C# with Python support via pythonnet. The architecture separates concerns into distinct projects: Algorithm definitions, Engine execution, Data management, Brokerages, and supporting infrastructure.

## Architecture & Component Structure

### Core Module Separation
- **Algorithm/**: Base `QCAlgorithm` class - all algorithms inherit from this. Defines core methods like `Initialize()`, `OnData()`, trading APIs (`SetHoldings`, `MarketOrder`), and universe selection
- **Algorithm.CSharp/**: C# algorithm examples demonstrating features. Files prefixed with "Add" showcase specific API capabilities. Suffix "RegressionAlgorithm" indicates automated test coverage
- **Algorithm.Python/**: Python algorithm examples with same patterns as C# versions
- **Algorithm.Framework/**: Pluggable framework components - `AlphaModel`, `PortfolioConstructionModel`, `ExecutionModel`, `RiskManagementModel`. Used via `SetAlpha()`, `SetPortfolioConstruction()`, etc.
- **Engine/**: Core execution engine. Runs algorithms, manages time, processes data feeds, executes orders. Uses pythonnet for Python algorithm support
- **Common/**: Shared data structures (`Symbol`, `Security`, `Order`, `Bar`, market data types). No dependencies on other LEAN projects
- **Data/**: Market data handling, consolidators, universe definitions
- **Brokerages/**: Brokerage integrations with common `IBrokerage` interface
- **Indicators/**: Technical indicators extending `IndicatorBase<T>`
- **Tests/**: NUnit tests using `[Test]` attribute. Regression tests validate end-to-end algorithm behavior

### Key Data Flow
1. Engine loads algorithm via AlgorithmFactory
2. Data feeds (SubscriptionManager) provide time-synchronized market data
3. Algorithm receives data through `OnData(Slice data)` callback
4. Algorithm emits orders to TransactionManager
5. Orders executed through brokerage connection
6. Results aggregated in ResultsHandler

## Development Workflows

### Building & Running
```bash
# Build entire solution
dotnet build QuantConnect.Lean.sln

# Run from Launcher (pass algorithm in config.json)
cd Launcher/bin/Debug
dotnet QuantConnect.Lean.Launcher.dll
```

VS Code tasks available: `build`, `rebuild`, `clean` (all use dotnet CLI with Debug config)

### Testing Strategy
- Use NUnit framework with `[Test]` attribute
- Regression algorithms in Algorithm.CSharp/ are actual backtests that verify behavior
- Tests must accompany all PRs - expose bugs or demonstrate new features
- Run: `dotnet test`

### Python Integration
- Python algorithms compiled via pythonnet (see Engine references `QuantConnect.pythonnet`)
- Python code must follow same structure as C# (`Initialize()`, `OnData()`)
- Python algorithms live in Algorithm.Python/

## Coding Conventions & Patterns

### Algorithm Structure Pattern
```csharp
public class MyAlgorithm : QCAlgorithm
{
    public override void Initialize()
    {
        SetStartDate(2020, 1, 1);
        SetCash(100000);
        AddEquity("SPY", Resolution.Daily);
        // Configure universe, framework models
    }

    public override void OnData(Slice data)
    {
        // Main trading logic
        if (!Portfolio.Invested)
        {
            SetHoldings("SPY", 1.0);
        }
    }
}
```

### Framework Model Pattern
Framework models separate concerns - inherit from base classes:
- `AlphaModel.Update()` - generates `Insight` objects with directional predictions
- `PortfolioConstructionModel.CreateTargets()` - converts insights to `PortfolioTarget` weights
- `ExecutionModel.Execute()` - fills targets with actual orders
- `RiskManagementModel.ManageRisk()` - adjusts targets based on risk rules

Example: [AddAlphaModelAlgorithm.cs](Algorithm.CSharp/AddAlphaModelAlgorithm.cs) shows combining multiple alpha models

### Code Style
- Microsoft C# guidelines (see [CONTRIBUTING.md](CONTRIBUTING.md))
- 4-space indentation (soft tabs)
- No logging/debugging in framework modules - keep production code silent
- Framework modules should do ONE focused task (separation of concerns)

### Symbol Handling
Use `Symbol` objects, not strings:
```csharp
var spy = Symbol.Create("SPY", SecurityType.Equity, Market.USA);
AddEquity(spy);
```

### Configuration
- Algorithm behavior controlled via `config.json` in Launcher
- Specify algorithm class, data directories, brokerage settings
- See [.vscode/readme.md](.vscode/readme.md) for IDE-specific setup

## Project-Specific Conventions

### Naming Conventions
- Regression algorithms: `*RegressionAlgorithm.cs`
- Feature demos: `Add*Algorithm.cs` (e.g., `AddAlphaModelAlgorithm.cs`)
- Framework modules: `*AlphaModel`, `*PortfolioConstructionModel`, `*ExecutionModel`

### Dependency Rules
- Common/ has zero LEAN project dependencies (only external NuGet)
- Engine depends on Algorithm, Brokerages, Data, etc.
- Algorithm projects should not depend on Engine
- Tests can reference any project

### Data Organization
- Market data stored in `Data/` directory (not in repo)
- Use resolution types: `Tick`, `Second`, `Minute`, `Hour`, `Daily`
- Data access through `History()` API or `OnData()` callbacks

## CLI Tool (Separate from Engine)
Users typically interact via `lean` CLI (Python-based, installed via pip):
- `lean backtest` - run backtests in Docker
- `lean research` - launch Jupyter notebooks
- `lean live` - deploy live trading
This is separate from the C# LEAN engine codebase

## Common Pitfalls
- Don't call LEAN from other projects as a library - it's designed as a standalone engine
- Framework models must avoid logging/charting - users do this in algorithm class
- Always use `Symbol` objects for security references, not raw strings
- Tests must be reproducible - avoid external dependencies or current time
- Python algorithms must match C# API surface (Initialize, OnData, same method names)

## Key Files for Context
- [QCAlgorithm.cs](Algorithm/QCAlgorithm.cs) - main algorithm base class API
- [CONTRIBUTING.md](CONTRIBUTING.md) - branch workflow, PR requirements
- [QuantConnect.Lean.sln](QuantConnect.Lean.sln) - solution structure
