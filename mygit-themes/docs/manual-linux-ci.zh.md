# MyGIt · 手动 Linux 自托管检查

> 2026-11-07：使用 buildHelpers 组织现有的共享 Linux Runner，不安装新 Runner，也不恢复 GitHub 托管或自动 CI。

## 已配置

工作流：[`mygit-linux-manual.yml`](../../.github/workflows/mygit-linux-manual.yml)

对应的组织接入规则：[Chumen 共享 Linux Runner 接入指南](https://github.com/buildHelpers/Chumen/blob/master/docs/organization-linux-ci.zh.md)。

| 配置 | 实际值 |
|---|---|
| 触发方式 | **仅 workflow_dispatch 手动运行** |
| 组织 Runner 组 | `buildhelpers-linux` |
| 标签 | `self-hosted, linux, x64, buildhelpers-linux` |
| 权限 | 只读 `contents: read`，`checkout` 不持久化令牌 |
| 分支 | 使用 **`task/20261107-0945-design-completion`** 测试最新六页主题；产品基线 `mygit` 用于单独对照 |
| 任务 | Python 回归测试、原生颜色与布局校验、完整布局补丁隔离应用与检查、校验工作区未修改 |
| 不执行 | .NET 编译、Mac 运行、打包、远程部署、自动清理其他项目数据 |

共享 Runner 当前为 Ubuntu x86_64，约 1.5 CPU 和 2 GB 内存，无 sudo、Docker 组权限。一个 Runner 同一时刻只运行一个 Job，组织内其他仓库使用时本项目会排队。

## 你自己怎么运行

1. 打开 [MyGIt GitHub Actions](https://github.com/buildHelpers/MyGIt/actions)。
2. 选择 **MyGIt · Manual Linux Self-Hosted Checks**。
3. 点击 **Run workflow**。
4. 分支选择 **`task/20261107-0945-design-completion`**。
5. 再点击绿色 **Run workflow**，运行后查看每一步日志。

不选择默认的 `master`：默认分支只用于向 GitHub 注册手动工作流，Job 特意排除了 `master` 和 `develop`，避免把无主题包的上游基线当作产品检查。

也可以在**你自己的已登录机器**执行：

```bash
gh workflow run mygit-linux-manual.yml \
  --repo buildHelpers/MyGIt \
  --ref task/20261107-0945-design-completion

gh run list \
  --repo buildHelpers/MyGIt \
  --workflow mygit-linux-manual.yml \
  --limit 5
```

以上命令只给你手动操作，**Agent 不主动启动 CI**。Linux 共享 Runner 跑的是用户明确选定的本仓库分支，不接收外部 PR 源码，不申请任何主机令牌。

## 这一步通过证明什么？

- `PASS`：说明主题内容和 Python 单元测试通过，并能在 GitHub 当前检出的代码上生成完整的隔离布局工作树（含 MyGIt 图标）。
- `FAILED`：以实际报错为准，不能视为通过；常见问题是上游 UI 结构改动导致布局补丁不兼容。
- `QUEUED`：检查组织共享 Runner 是否在线/是否正在处理其他仓库任务。
- `NOT_RUN`：本 Linux Job **不会**执行 .NET/Avalonia 构建、Mac GUI 操作、包签名、截图对比或发布。这些必须另行在用户的 Mac 本地验证。

Mac 本地完整构建命令：

```bash
git switch task/20261107-0945-design-completion
python3 mygit-themes/tools/theme.py build mygit-design --output ../MyGIt-Local
```

需要 Git、Python 3.9+ 和 .NET 10；`../MyGIt-Local` 必须尚不存在。

## 安全与额度

- 该新工作流不含 `push`、`pull_request`、`schedule` 事件。
- 旧的 `mygit-design.yml` 托管 Mac 工作流仍处于暂停状态，**不重新启用**。
- 新工作流只在本组织自托管 Runner 运行，不占用 GitHub 托管计算分钟数。GitHub 仍可能对 Actions 存储等项目另行计费；本工作流不上传工件，不使用 Actions 缓存。
- 不安装 Runner、不要求 PAT、不访问用户的服务器管理凭据、不改变现有 Chumen 配置，也不清理其他项目任务目录。
