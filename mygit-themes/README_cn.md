# MyGIt · 设计主题系统（进行中）

**目标：主题包含页面布局、导航、控件样式及深浅配色，而不只是换颜色。当前只完成部分改造，尚未完整还原六张设计稿。**

[本轮整改与逐页未完成项](UI_AUDIT_cn.md) · [English](README.md)

## 当前方案

`mygit-design` 将六组初始界面补丁和一组整合修正应用到独立 Git worktree，再构建。`upstream-classic` 保留原 SourceGit。Light/Dark JSON 继续使用 SourceGit 原生 Theme Overrides。

自定义内容集中在 `mygit-themes/`；产品分支不直接保存对上游 `src/` 的改动。但布局补丁仍依赖上游页面与 ViewModel，因此上游改动相关文件时需要适配，**不是零维护，也不是运行时热切换布局**。

## 本轮纠正

顶部仓库切换现在只有一个入口，沿用 `Ctrl/Cmd+P`，点击和快捷键共用最近仓库/搜索面板。移除仓库页面重复的顶部分类导航；同步历史图与表头高度；修正三栏工作副本的宽度计算。具体代码、已执行检查和未完成页面见审计记录。

## 本地使用

要求 Git、Python 3.9+；构建要求 .NET 10 及 SourceGit 原有依赖。请从 `mygit` 分支的干净工作区执行：

```bash
python3 mygit-themes/tools/theme.py layouts
python3 mygit-themes/tools/theme.py validate
python3 -m unittest discover -s mygit-themes/tools -p 'test_*.py'
python3 mygit-themes/tools/theme.py check mygit-design
python3 mygit-themes/tools/theme.py build mygit-design --output ../MyGIt-Design-Fixed
```

输出目录必须不存在且在源码仓库外。仅准备源码、不编译：

```bash
python3 mygit-themes/tools/theme.py prepare mygit-design --output ../MyGIt-Design-Source
cd ../MyGIt-Design-Source
git submodule update --init --recursive
dotnet run --project src/SourceGit.csproj
```

使用原版布局：

```bash
python3 mygit-themes/tools/theme.py prepare upstream-classic --output ../SourceGit-Classic
```

旧生成目录和已安装程序不会随 `git pull` 自动更新，需重新生成、编译。

## 配色与同步

在应用 Preferences → Appearance 中选择 Light 或 Dark，并将相应 JSON 设为 Theme Overrides：

- [MyGIt Light](presets/MyGIt-Light.json)
- [MyGIt Dark](presets/MyGIt-Dark.json)

```bash
python3 mygit-themes/tools/theme.py install light
python3 mygit-themes/tools/theme.py install dark
```

安装工具只复制 JSON，不修改 `preference.json` 或密钥。外观配色可在运行时切换，页面布局需要重建。

同步时保留 `develop` 跟随上游，更新 `mygit` 后运行 `check mygit-design`。补丁不兼容会停止，不应强制覆盖。第七组补丁的顺序修订目标必须在清单中逐一声明。

**验收状态：** 本轮规则测试和取回源码样本上的补丁检查已通过；完整装配、.NET 构建、Mac 实际运行和逐页视觉验收未完成。新图标仍未接入程序资源。
