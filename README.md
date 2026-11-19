# 删除站点后阻止 CookieCloud 回添

MoviePilot V3 插件。启用后，在站点管理中删除单个站点，插件会把域名追加到 MoviePilot 的 CookieCloud 同步黑名单。其他站点按原有设置同步。

## 安装

1. 使用 MoviePilot V3.2.8 或更新版本。
2. 在「插件 → 插件市场设置」添加仓库 `https://github.com/luckysmithlee/moviepilot-cookiecloud-delete-guard`。
3. 刷新插件市场，安装「删除站点后阻止 CookieCloud 回添」，打开插件配置并启用。

## 使用

- 删除单个站点后，可在「设定 → 系统 → 站点设置 → CookieCloud 同步黑名单」查看追加的域名。
- 恢复某个站点的 CookieCloud 自动添加时，从黑名单移除它的域名。
- 插件启用时读取当前站点列表，并在站点更新后刷新记录。启用前已删除的站点需要手动加入黑名单。
- 清空全部站点不会自动批量加入黑名单。停用插件后，已保存的黑名单条目需要在站点设置中管理。

## 验证

在仓库根目录中，用 MoviePilot V3 的 Python 环境运行以下命令。宿主后端应在 `PYTHONPATH` 中，测试引导会创建临时配置目录。

```sh
env -u CONFIG_DIR python -c 'from pathlib import Path; import unittest; from app.testing.bootstrap import prepare_v3_backend; prepare_v3_backend(Path.cwd()); suite = unittest.defaultTestLoader.discover("tests/v3/cookieclouddeleteguard"); raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())'
```
