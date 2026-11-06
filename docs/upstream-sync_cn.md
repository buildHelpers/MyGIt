# MyGIt · 上游同步与分支维护规则

上游项目：[SourceGit](https://github.com/sourcegit-scm/sourcegit)，MIT 许可。

## 分支职责

| 分支 | 作用 |
|---|---|
| `master` | 保持上游稳定版基线，不混入 MyGIt 定制 |
| `develop` | 专门跟进 SourceGit 的 `develop`，不合入 MyGIt 界面改动 |
| `mygit` | MyGIt 产品集成分支；定制功能的 PR 应以它为目标 |
| `task/YYYYMMDD-HHMM-...` | 独立任务分支，按照验收结果并入 `mygit` |

2026-11-06 创建 `mygit` 时，`mygit` 和本 Fork 的 `develop` 同在 `37bd1fbd8c56a872ebb6033c0639d3cb930f8aa9`。上游最新 `develop` 为 `76fe14863ac484635989a3feef36c4ff3c2f3dc7`，比当前基线多三个提交，涉及 `src/Commands/Command.cs`、`src/Models/User.cs`、`src/ViewModels/DiffContext.cs`，目前与本轮 UI 改造文件不直接重合。**这是低冲突预期，不代表实际合并已经验证。**

## 今后如何同步

在工作区干净、已设置 `origin` 为自己 Fork 的本地克隆执行：

```bash
git remote add upstream https://github.com/sourcegit-scm/sourcegit.git
# 如果已有 upstream，跳过上面这一行。
git fetch upstream develop
git switch develop
git merge --ff-only upstream/develop
git push origin develop

# 完成 MyGIt 自身 PR 的合并后，才更新产品分支：
git switch mygit
git merge --no-ff develop
# 如遇冲突，只修复涉及的文件，编译检查通过再推送。
git push origin mygit
```

如果 `develop` 不能快进，**立即停止**，先查明基线是否被修改，不要使用强制重置。如果 `mygit` 合并有冲突，逐块核对 UI 文件，不要简单选“全部用上游”或“全部用本地”。未验证的代码不要自动合入产品分支。

只检查上游有没有新代码（不改分支）：

```bash
git fetch upstream develop
git log --oneline develop..upstream/develop
git diff --stat develop..upstream/develop
```

## 降低未来冲突的规则

1. 新页面和新组件尽量独立放置，公共视觉效果归入主题和自定义样式，避免在原项目 XAML 中重复改大块布局。
2. Git 命令、存储和协议层尽量沿用上游，定制功能通过界面或少量 ViewModel 适配。
3. 以后按页面或功能提交小 PR，不再把数十个独立功能长期堆在一个改造提交里。
4. 保留 SourceGit 原 MIT 许可声明。重命名程序集或本地配置目录前必须有迁移方案。
5. 合并上游后还需要 .NET 编译、静态检查、Mac 实际操作验收；Git 合并成功不代表运行正常。

**现实边界：** 当前六页重设计依然直接修改了 SourceGit 的若干原生 XAML 和 ViewModel。将来上游改动这些文件，仍可能需要人工解决冲突。分支隔离可以降低维护风险，但无法做到完全无冲突。
