# MyGIt Design · 布局主题

**不是一套新 Git 客户端。** 本主题提供已确认的六页 MyGIt 设计布局，同时继续使用 SourceGit 的 Git 引擎、配置、权限和业务功能。

## 页面映射

| 原始设计图 | 主题包模块 | 主要界面要素 |
|---|---|---|
| 01 · 仓库首页 | `10-shell-home.patch` | 工作区首页、最近仓库卡片、仓库搜索与分组 |
| 02 · 工作副本 | `20-working-copy.patch` | 左侧文件变化、中间代码 Diff、右侧提交编辑器 |
| 03 · 提交历史 | `30-history-branches.patch` | 提交图、提交详情、左右分栏 |
| 04 · 分支与 Worktrees | `30-history-branches.patch` | 完整分支页、HEAD/上游信息、工作树卡片 |
| 05 · 冲突解决 | `40-conflicts-settings.patch` | Ours/Theirs/Result 对比、冲突操作 |
| 06 · 设置 | `40-conflicts-settings.patch` | 左侧分类导航、宽窗口、原设置选项 |

`00-adapters.patch` 负责必要的 UI ViewModel 适配、顶栏仓库切换和最近使用记录；`50-visual-resources.patch` 提供样式、配色和多语言资源。这些文件都在主题包内，正常产品源代码不保存这些修改。

## 交付保证与边界

- **来源明确**：布局代码来自此前的六页改造分支 `task/20261106-1718-workspace-navigation-redesign`，基线 `develop@37bd1fbd`；拆分时按文件完整保留改动内容。
- **兼容检查**：每次装配先检查 Git 上游对应代码是否还能打补丁。遇到冲突即报错，并清理生成的工作树。
- **构建隔离**：使用 `git worktree add --detach`，绝不向 `develop` / `mygit` 写入这些布局改动。
- **外观切换**：Light/Dark 颜色在 SourceGit 原生设置里切换；布局需要重建，暂时不支持热切换。
- **未完成的验证**：尚未实际运行 .NET 10 编译和 macOS 逐页截图验收，所以“与设计图像素一致”仍是待核验条件。

## 操作入口

```bash
python3 mygit-themes/tools/theme.py validate
python3 mygit-themes/tools/theme.py check mygit-design
python3 mygit-themes/tools/theme.py prepare mygit-design --output ../MyGIt-Design
```

用户在自己的 Mac 上用 `dotnet run --project src/SourceGit.csproj` 从生成目录运行后，与最开始六张设计图对照即可。
