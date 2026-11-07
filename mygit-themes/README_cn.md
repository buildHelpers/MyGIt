# MyGIt · 完整设计主题系统

**这套主题不只是颜色，还包含最初设计的六个页面、全局导航和交互。** 所有界面改动保存在独立主题包里，由构建工具装配；Git 核心继续跟随上游 SourceGit。

[最新逐页核查与剩余事项](UI_AUDIT_cn.md) · [MyGIt Design SVG 图标](assets/MyGIt-icon.svg)

## 实现范围

| 页面 | 已实现的主题内容 |
|---|---|
| 工作区首页 | 操作卡片、最近仓库横向滚动、管理仓库树和搜索 |
| 工作副本 | 文件变更、Diff、提交编辑器三栏；保留暂存与提交操作 |
| 提交历史 | 提交图和详情分栏、表头对齐、分支筛选 |
| 分支 / Worktrees | 独立管理页面、实时分支搜索、空结果提示、Worktree 打开 |
| 冲突解决 | 本地 / 合并结果 / 对方三列，以及原有解决冲突操作 |
| 设置 | 左侧类别导航、较宽窗口、浅色 / 深色 / 系统主题预览 |

顶部仓库切换只保留**一个**入口，鼠标点击和 `Ctrl/Cmd+P` 共用最近仓库与搜索面板。工作区入口独立保留。

主题目录提供两类可选布局：`mygit-design`（原设计）和 `upstream-classic`（上游原版）；配色则是 `MyGIt Light` 与 `MyGIt Dark`。

## 真实构建状态

GitHub Actions 在 **2026-11-07** 已成功完成 macOS 的主题完整装配、原生图标生成及 **.NET/Avalonia 编译**。验证记录：[成功的 Mac 构建](https://github.com/buildHelpers/MyGIt/actions/runs/42327030953)。

其后增补了布局补丁格式校验，避免再次出现旧补丁 hunk 行数错误。完整编译成功仅能证明项目可以编译，**仍未代表实际界面与六张设计图逐像素相同**；动态菜单、窄窗口、分支操作及冲突编辑等实际交互还需实机运行核验。

## 构建 MyGIt Design

需 Git、Python 3.9+、.NET 10 SDK。在 `mygit` 分支的干净工作区：

```bash
# 检查原生配色、布局清单、补丁格式和单元测试
python3 -m unittest discover -s mygit-themes/tools -p 'test_*.py'
python3 mygit-themes/tools/theme.py validate

# 在临时隔离目录测试当前上游能否应用主题
python3 mygit-themes/tools/theme.py check mygit-design

# 在仓库外生成独立构建目录并编译
python3 mygit-themes/tools/theme.py build mygit-design --output ../MyGIt-Design
```

每次使用一个**不存在**的输出目录。工具不修改 `mygit` / `develop` 的 `src/` 源文件，编译产物在独立 Git worktree。源仓库有已跟踪的未提交改动时会拒绝处理。

主题装配自动生成全套图标：

- `src/App.ico` —— Windows 应用图标
- `build/resources/app/App.icns` —— macOS 应用包图标
- `build/resources/_common/icons/sourcegit.png` —— Linux 图标

图标源文件：[MyGIt-icon.svg](assets/MyGIt-icon.svg)，可独立修改设计。三个平台的输出资源只会出现在**生成的构建目录**内。

如果想自行运行，不编译：

```bash
python3 mygit-themes/tools/theme.py prepare mygit-design --output ../MyGIt-Preview
cd ../MyGIt-Preview
git submodule update --init --recursive
dotnet run --project src/SourceGit.csproj
```

## 外观配色

SourceGit 的原生配色仍可热切换。进入 **Preferences → Appearance → Theme Overrides**，选择相应 JSON：

- [MyGIt Light](presets/MyGIt-Light.json)
- [MyGIt Dark](presets/MyGIt-Dark.json)

也可使用 `python3 mygit-themes/tools/theme.py install light` 或 `install dark` 将文件复制到用户配置目录。不会改密钥、Git 配置或原应用程序。

## 上游同步原则

保持 `develop` 跟随 SourceGit 上游，`mygit` 只维护独立的主题文件及验证工作流。布局会使用有序版本化补丁装配到独立目录。如果上游改动造成冲突，兼容检查会停止，不自动强制覆盖。

**需要维护的是主题包，包括布局适配**，而非修改上游 Git 后端。布局补丁依赖上游 XAML/ViewModel，因此不能承诺永远零维护。

完成状态和剩余风险请以 [最新审计记录](UI_AUDIT_cn.md) 和 [GitHub Mac CI](https://github.com/buildHelpers/MyGIt/actions) 为准。
