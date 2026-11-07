# MyGIt 组织 Linux Runner 手动验证（直接源码版）

**仅手动触发；不启用 GitHub 托管 Runner、Push/PR 自动检查。** 共享 Runner 组、标签均为 `buildhelpers-linux`，可参考 [Chumen 组织接入指南](https://github.com/buildHelpers/Chumen/blob/master/docs/organization-linux-ci.zh.md)。

工作流：[`mygit-linux-manual.yml`](../../.github/workflows/mygit-linux-manual.yml)

操作方法：打开 [MyGIt GitHub Actions](https://github.com/buildHelpers/MyGIt/actions/workflows/mygit-linux-manual.yml) → Run workflow → 选择 **`mygit`**（产品版本）→ Run workflow。

手动 Linux 任务使用现有 `buildhelpers-linux` 自托管 Runner，进行 Python 回归测试、直接源码的界面结构检查和身份隔离检查；不会执行已经废弃的 UI 补丁装配，更不会运行 macOS GUI。资源上限约 1.5 CPU / 2GB RAM，无 Docker 或 sudo，组织单 Runner 排队。

你也可以直接在自己的 Mac 上验证，不用 Actions：

```bash
git switch mygit
python3 tools/check-mygit.py
bash tools/build-mygit.sh ../MyGIt-Preview
```

Mac 应用、图标和双应用共存需要实际安装、启动及截图验收。**任何静态 PASS 不等于六张设计图已实现像素级一致。**

`develop`、`master` 仍是上游基线，不属于 MyGIt 产品。这里不会自动执行托管 CI；需要真实运行时由用户自己触发。
