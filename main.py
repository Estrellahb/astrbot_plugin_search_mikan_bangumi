import asyncio
from html import unescape
from xml.etree import ElementTree
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

MIKAN_RSS_SEARCH_URL = "https://mikan.tangbai.cc/RSS/Search?searchstr="
MAX_RESULT_COUNT = 3


class MikanSearchPlugin(Star):
    """通过 AstrBot 命令搜索 Mikan RSS，并把结果返回到当前消息会话。"""

    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """插件初始化钩子。当前阶段不需要额外初始化逻辑。"""

    def _build_search_url(self, keyword: str) -> str:
        # 对用户输入进行 URL 编码，避免空格、中文和特殊字符破坏查询字符串。
        return f"{MIKAN_RSS_SEARCH_URL}{quote_plus(keyword.strip())}"

    def _fetch_rss_sync(self, keyword: str) -> str:
        """同步请求 Mikan RSS。调用方负责把它放到线程里执行。"""
        # 使用标准库发请求，减少插件依赖；timeout 防止外部接口长时间阻塞。
        url = self._build_search_url(keyword)
        request = Request(
            url,
            headers={
                "User-Agent": "AstrBot-Mikan-Plugin/1.0",
            },
        )

        with urlopen(request, timeout=15) as response:
            return response.read().decode("utf-8", errors="replace")

    def _local_name(self, tag: str) -> str:
        """去掉 XML 命名空间，只保留标签本名。"""
        return tag.rsplit("}", 1)[-1]

    def _clean_text(self, value: str) -> str:
        """清理 RSS 文本中的 HTML 实体和零宽空白。"""
        return unescape(value.replace("\u200b", "").strip())

    def _child_text(self, element: ElementTree.Element, child_name: str) -> str:
        """读取当前节点的直接子节点文本。"""
        for child in element:
            if self._local_name(child.tag) == child_name:
                return self._clean_text(child.text or "")
        return ""

    def _child_attr(self, element: ElementTree.Element, child_name: str, attr_name: str) -> str:
        """读取当前节点的直接子节点属性。"""
        for child in element:
            if self._local_name(child.tag) == child_name:
                return self._clean_text(child.attrib.get(attr_name) or "")
        return ""

    def _descendant_text(self, element: ElementTree.Element, child_name: str) -> str:
        """读取任意后代节点文本，用于兼容 Mikan 自定义 torrent 节点。"""
        for child in element.iter():
            if child is element:
                continue
            if self._local_name(child.tag) == child_name:
                return self._clean_text(child.text or "")
        return ""

    def _format_content_length(self, content_length: str) -> str:
        """把 RSS 中的字节数转换成适合聊天阅读的文件大小。"""
        if not content_length.isdigit():
            return ""

        size = float(content_length)
        units = ["B", "KB", "MB", "GB", "TB"]
        for unit in units:
            if size < 1024 or unit == units[-1]:
                return f"{size:.2f} {unit}"
            size /= 1024

        return ""

    def _format_pub_date(self, pub_date: str) -> str:
        """把 ISO 时间里的 T 替换为空格，提升聊天消息可读性。"""
        return pub_date.replace("T", " ", 1)

    def _parse_rss_items(self, rss_text: str) -> list[dict[str, str]]:
        """解析 RSS 条目，提取聊天回复需要展示的字段。"""
        root = ElementTree.fromstring(rss_text)
        items = []

        for item in root.iter():
            if self._local_name(item.tag) != "item":
                continue

            link = self._child_text(item, "link")
            torrent_url = self._child_attr(item, "enclosure", "url") or link
            # Mikan 的大小可能在 enclosure.length，也可能在 torrent.contentLength。
            content_length = self._child_attr(item, "enclosure", "length") or self._descendant_text(
                item,
                "contentLength",
            )
            pub_date = self._child_text(item, "pubDate") or self._descendant_text(item, "pubDate")
            items.append(
                {
                    "title": self._child_text(item, "title") or "未命名条目",
                    "link": link,
                    "torrent_url": torrent_url,
                    "pub_date": self._format_pub_date(pub_date),
                    "size": self._format_content_length(content_length),
                }
            )

            if len(items) >= MAX_RESULT_COUNT:
                break

        return items

    def _format_search_result(self, keyword: str, items: list[dict[str, str]]) -> str:
        """把解析后的 RSS 条目格式化为消息平台可直接发送的纯文本。"""
        if not items:
            return f"没有找到与“{keyword}”相关的 Mikan RSS 结果。"

        lines = [f"找到 {len(items)} 条 Mikan RSS 结果："]
        for index, item in enumerate(items, start=1):
            lines.append("")
            lines.append(f"{index}. {item['title']}")
            if item["pub_date"]:
                lines.append(f"发布时间: {item['pub_date']}")
            if item["size"]:
                lines.append(f"大小: {item['size']}")
            if item["link"]:
                lines.append(f"页面: {item['link']}")
            if item["torrent_url"]:
                lines.append(f"Torrent: {item['torrent_url']}")

        return "\n".join(lines)

    def _extract_keyword(self, event: AstrMessageEvent) -> str:
        """从原始消息里取命令后的完整搜索词，保留搜索词内部空格。"""
        message = (event.message_str or "").strip()
        if not message:
            return ""

        parts = message.split(maxsplit=1)
        if len(parts) < 2:
            return ""

        return parts[1].strip()

    @filter.command("蜜柑搜番")
    async def search_mikan(self, event: AstrMessageEvent):
        """根据番剧名搜索 Mikan RSS 并返回格式化结果。"""
        keyword = self._extract_keyword(event)
        if not keyword:
            yield event.plain_result("请输入番剧名")
            return

        # AstrBot 的 handler 是异步函数，阻塞式网络请求必须放到线程中执行。
        try:
            rss_text = await asyncio.to_thread(self._fetch_rss_sync, keyword)
        except Exception as exc:
            logger.exception("Request Mikan RSS failed")
            yield event.plain_result(f"请求 Mikan RSS 失败: {exc}")
            return

        try:
            items = self._parse_rss_items(rss_text)
        except ElementTree.ParseError as exc:
            logger.exception("Parse Mikan RSS failed")
            yield event.plain_result(f"解析 Mikan RSS 失败: {exc}")
            return

        logger.info("Mikan RSS request succeeded for keyword=%s", keyword)
        yield event.plain_result(self._format_search_result(keyword, items))

    async def terminate(self):
        """插件销毁钩子。当前阶段不需要清理逻辑。"""
