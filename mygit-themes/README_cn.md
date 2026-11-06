# MyGIt · 原生主题系统

> **不再维护一套改造过的 SourceGit 客户端。** 以后只维护本目录里的主题文件；Git 功能、业务逻辑、程序窗口和界面布局全部来自上游 SourceGit，不需要改 C#、XAML 或 Git 命令。

[English](README.md) · [SourceGit 上游](https://github.com/sourcegit-scm/sourcegit) · [官方主题协议示例](https://github.com/sourcegit-scm/sourcegit-theme)

## 方案

复用 SourceGit 已有的 **Theme Overrides（主题覆盖）** 机制，JSON 文件可修改背景、文字、按钮、边框、Diff、冲突区、提交图等颜色，无须重新编译。

默认提供：

- **MyGIt Light**：明亮、克制的 macOS 风格，蓝紫强调色。
- **MyGIt Dark**：深蓝夜间风格，兼顾可读性。

**必须明确的限制：** 原生主题不能改变页面结构、三栏布局，也不能增加顶部最近仓库下拉按钮。因此之前的六页改造源码不会合入正式产品；若需要那些新功能，应争取 SourceGit 上游支持，而不是 MyGIt 私有长期维护。

## 安装与切换（不改程序）

1. 下载 [浅色主题](presets/MyGIt-Light.json) 或 [深色主题](presets/MyGIt-Dark.json)；也可以直接从本仓库 `mygit` 分支读取文件。
2. 打开未修改的 SourceGit。
3. 进入 **Preferences（偏好设置）→ Appearance（外观）**。
4. 将 **Theme（主题）** 设为对应的 **Light / Dark**。
5. 在 **Theme Overrides（主题覆盖）** 中选取相应 JSON 文件。

程序会通过原生配置记录主题文件路径，随时可以切换。要恢复默认主题，只需清空 Theme Overrides。

### 可选 Python 工具

不安装任何第三方包，Python 3.9+ 即可：

```bash
python3 mygit-themes/tools/theme.py list
python3 mygit-themes/tools/theme.py validate
python3 mygit-themes/tools/theme.py install light
python3 mygit-themes/tools/theme.py install dark
```

工具只负责校验主题与复制 JSON 到系统 SourceGit 配置目录下的 `Themes` 文件夹，并提示在 SourceGit 设置里选哪个路径。**不修改 `preference.json`、不碰密钥、不改客户端源码、不重启应用。** 需要覆盖旧版本时才显式加 `--force`。没有 Python 的机器直接选择下载好的 JSON 即可。

## 目录及协议

```text
mygit-themes/
├── manifest.json                 # 自己的预设列表，上游应用不会读取
├── presets/
│   ├── MyGIt-Light.json          # SourceGit 原生格式
│   └── MyGIt-Dark.json
├── tools/theme.py                # 可选的校验和复制工具
├── README.md
└── README_cn.md
```

主题 JSON 只使用 SourceGit 自身支持的 `BasicColors`、`GraphPenThickness`、`OpacityForNotMergedCommits` 和 `GraphColors`。具体颜色键以 SourceGit 的 `src/Resources/Themes.axaml` 为准。我们自己的 `manifest.json` 仅用于列出可用主题，不需要开发应用插件。

以后新增风格只需要增加一个 JSON 文件、在清单中登记、运行校验；不需要改页面代码。

## 如何直接同步上游

`master` 对应上游稳定版，`develop` 对应上游开发版，产品分支 `mygit` **只放独立的主题目录**。

在干净的本地仓库执行：

```bash
git remote add upstream https://github.com/sourcegit-scm/sourcegit.git # 首次一次
git fetch upstream develop
git switch develop
git merge --ff-only upstream/develop
git push origin develop

git switch mygit
git merge --no-ff develop
python3 mygit-themes/tools/theme.py validate
git push origin mygit
```

已配置 `upstream` 时跳过第一行。如果不能快进，或合并发生冲突，先停下来核对，不要强制推送。因为主题与源码分开，上游 Git 能力更新无需再手工重新维护 UI 文件。

**验收边界：** 已有原生主题格式和静态检查，但 JSON 有效不代表 macOS 画面已经和之前的六张设计图一致。当前选择的是轻维护方案，页面布局以最新 SourceGit 为准。
