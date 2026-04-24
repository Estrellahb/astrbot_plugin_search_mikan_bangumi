# astrbot_plugin_search_mikan_bangumi

AstrBot 插件：通过消息平台搜索 Mikan 番剧 RSS，并把搜索结果回复到当前会话。

当前插件使用 Mikan RSS 搜索接口，根据用户输入的番剧关键词模糊搜索资源，返回标题、发布时间、资源大小、页面链接和 Torrent 下载链接。

## 功能

- 支持在 AstrBot 消息平台中通过命令触发搜索。
- 使用标准库请求和解析 RSS，不需要额外 Python 依赖。
- 自动对中文、空格和特殊字符搜索词进行 URL 编码。
- 默认返回前 3 条结果，避免在群聊或私聊中刷屏。
- 将 Mikan 返回的 ISO 时间格式从 `2023-01-14T10:48:00` 显示为 `2023-01-14 10:48:00`。

## 安装

将本仓库放到 AstrBot 的插件目录：

```text
data/plugins/astrbot_plugin_search_mikan_bangumi
```

然后在 AstrBot 管理面板中重载插件，或重启 AstrBot。

## 使用方式

在已接入 AstrBot 的消息平台中发送：

```text
/蜜柑搜番 孤独摇滚
```

也可以替换成其他番剧关键词：

```text
/蜜柑搜番 葬送的芙莉莲
```

如果没有输入关键词，插件会回复：

```text
请输入番剧名
```

## 返回示例

```text
找到 3 条 Mikan RSS 结果：

1. [字幕组] 番剧标题
发布时间: 2023-01-14 10:48:00
大小: 1.23 GB
页面: https://mikan.tangbai.cc/Home/Episode/...
Torrent: https://mikan.tangbai.cc/Download/...
```

## 支持平台

当前 `metadata.yaml` 标记支持：

- QQ 官方适配器

只要 AstrBot 已经正确接入 QQ，并且插件已启用，就可以在 QQ 私聊或群聊中使用 `/蜜柑搜番 番剧名`。

## 本地检查

提交或部署前可以运行：

```powershell
python -m py_compile main.py
```

如果后续添加测试，可以运行：

```powershell
python -m pytest
```

## 注意事项

- 插件依赖 Mikan RSS 接口可访问性；如果 Mikan 无法连接，插件会返回请求失败信息。
- 当前不会监听所有普通聊天消息，必须使用 `/蜜柑搜番` 命令触发，避免群聊误触发。
- 当前默认最多返回 3 条结果，如需调整可修改 `main.py` 中的 `MAX_RESULT_COUNT`。
