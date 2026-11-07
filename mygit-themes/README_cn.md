# MyGIt 历史主题包（不再用于构建产品）

> **当前已切换为直接修改 SourceGit 源码**。正常编译不再使用本目录的 14 组有序补丁。请使用 [MyGIt 正式产品构建说明](../docs/MyGIt-Direct-UI.zh.md)。

本目录保留以前设计过程中生成的资源和补丁，方便追溯与向上游对照；这里的旧 `theme.py prepare` / `layout.py build` 不适用于已经直接修改的 `mygit` 产品源码，重复运行可能报冲突，请不要把它当作正常使用入口。

仍然使用的资源：
- `presets/MyGIt-Light.json`、`presets/MyGIt-Dark.json`：MyGIt 原生配色。
- `assets/MyGIt-icon.svg`：MyGIt 应用图标矢量源。
- `tools/icons.py`：仅在执行 `bash tools/build-mygit.sh` 时生成平台图标。

**Mac 单命令：** `bash tools/build-mygit.sh ../MyGIt-Preview`。

Git 核心来自 [SourceGit](https://github.com/sourcegit-scm/sourcegit)，后续直接把 `develop` 上游更新合并进 `mygit`，在冲突时审查真实页面源码。
