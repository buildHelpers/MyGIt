# MyGIt · 直接修改源码的版本（macOS 首验）

> 设计标准：[六张原始效果图](../mygit-themes/README_cn.md)；本分支直接维护 `src/` 的 XAML、ViewModel 和原有 SourceGit Git 操作。**不再使用 14 组补丁装配页面。**

## 唯一推荐的构建入口

先在 GitHub 的 `mygit` 产品分支更新本机仓库；不需要下载旧的「主题预览包」。

```bash
git fetch origin
git switch mygit
git pull --ff-only origin mygit

# 无需 .NET 的本地结构检查
python3 tools/check-mygit.py

# 在 Mac 上直接从当前 MyGIt 源码生成应用
bash tools/build-mygit.sh ../MyGIt-Preview

# 编译完成后
open ../MyGIt-Preview/MyGIt.app
```

需要 macOS、Git、Python 3.9+、.NET SDK 10、Xcode Command Line Tools。脚本自动识别 Intel / Apple Silicon，生成 `MyGIt.app` 和 `MyGIt-osx-arm64.zip` 或 `MyGIt-osx-x64.zip`。

- **只要这一条构建命令。** 它直接取 `src/` 已修改的 MyGIt 界面，运行 `dotnet publish`，不会运行 `theme.py prepare`、`git apply` 或重复打 UI 补丁。
- 编译在临时 Git worktree 中执行，只是为了隔离图标生成与输出，不额外维护一套 SourceGit 改造源码。
- 生成的应用有自己的 `com.buildhelpers.mygit` Bundle ID、macOS/Linux/Windows 配置目录、IPC 管道名与运行锁；保留原 SourceGit 现有安装，不覆盖它。
- `SourceGit` 内部 C# 命名空间和可执行文件名仍保留，避免重写上游 Git 实现与项目引用；用户看到的 macOS App 名称是 `MyGIt`。
- 已关闭原版 SourceGit 更新提示，避免错误地将 SourceGit 更新当成 MyGIt 发布。
- 输出目录若已有 `MyGIt.app` 或 ZIP，脚本会拒绝覆盖。可另选新目录，例如 `../MyGIt-Preview-2`。
- 仅用于本地验收：构建产物是 ad-hoc 签名，**未经过 Apple 公证**，不作为面向公众的正式安装包发布。

## 界面和设计状态

- 顶栏：MyGIt 品牌、工作区入口、居中仓库搜索（`Cmd+P`）、紧凑仓库标签、设置入口。
- 左侧仓库导航：当前仓库名称与分支、提交历史、工作副本、Stashes、分支/Worktrees；沿用上游的 `SelectedViewIndex` 与实际 Git 操作。
- 工作副本：变更/代码 Diff/提交编辑器三栏。
- 历史：默认收起多余作者、SHA 和提交时间表格列，保留在高级选项内重新显示的能力；提交详情依然使用上游现有组件。
- 分支：搜索、签出确认、Worktree 打开与管理。
- 冲突：本地、结果、对方三列，使用现有冲突操作。
- 设置：原有设置分类与 MyGIt Light / Dark / System 的可操作外观卡片。

**这些是代码层已实现的组件和结构，并不等同于六张图片达到逐像素一致。** 下一步真实验收要用新包的实际截图对比，不要把静态设计图当作运行成果。

## 和上游 SourceGit 同步

从现在起接受直接改源码带来的合并成本，不再叠加修订补丁：

```bash
git remote add upstream https://github.com/sourcegit-scm/sourcegit.git  # 首次添加
git fetch upstream
git switch develop
git merge --ff-only upstream/develop
git switch mygit
git merge develop
# 如果同一页面被上游修改，逐文件审查和解决冲突
python3 tools/check-mygit.py
bash tools/build-mygit.sh ../MyGIt-After-Upstream
```

`develop` 保持原版上游基线，`mygit` 是 MyGIt 产品分支；不要把自定义界面直接写回 `develop`。保留旧 `mygit-themes/layouts` 补丁仅用于历史追溯，**不再作为任何正式构建入口**。

## 验证边界

当前 ChatGPT 编辑环境不能运行完整 macOS 桌面应用。提交源代码后需要 Mac 上的 `dotnet publish`、`codesign`、实际 GUI 操作、原图对照；没有这些结果时不能报告「全部验收完成」。

**GitHub 托管 CI 保持关闭。** 不会自动触发托管任务。组织自托管 Linux Runner 仅在用户主动选择 `workflow_dispatch` 后用于 Python 静态检查，不能证明 Mac GUI。
