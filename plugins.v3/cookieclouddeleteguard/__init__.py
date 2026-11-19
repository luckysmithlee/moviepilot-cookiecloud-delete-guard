"""Keep individually deleted sites out of CookieCloud imports."""

from threading import RLock
from urllib.parse import urlsplit

from app.db.oper.site import SiteOper
from app.schemas.types import EventType
from app.sdk.config import settings
from app.sdk.events import Event, eventmanager
from app.sdk.logging import logger
from app.sdk.plugin import _PluginBase


def _hostname(value: str) -> str:
    """Accept both site domains and URLs already present in the blacklist."""
    value = value.strip().lstrip(".")
    try:
        host = urlsplit(value if "://" in value else f"//{value}").hostname
    except ValueError:
        return ""
    return (host or "").rstrip(".").lower()


class CookieCloudDeleteGuard(_PluginBase):
    """Remember site domains and blacklist each site after its deletion commits."""

    plugin_name = "删除站点后阻止 CookieCloud 回添"
    plugin_desc = "删除单个站点后，将域名追加到 CookieCloud 同步黑名单。"
    plugin_icon = "https://raw.githubusercontent.com/jxxghp/MoviePilot-Plugins/main/icons/Moviepilot_A.png"
    plugin_version = "1.0.0"
    plugin_author = "luckysmithlee"
    author_url = "https://github.com/luckysmithlee"
    plugin_config_prefix = "cookieclouddeleteguard_"
    plugin_order = 50
    auth_level = 1

    def __init__(self) -> None:
        super().__init__()
        self._lock = RLock()
        self._enabled = False
        self._domains: dict[int, str] = {}

    def init_plugin(self, config: dict | None = None) -> None:
        """Start watching sites only after the user enables the plugin."""
        with self._lock:
            self._domains.clear()
            self._enabled = (config or {}).get("enabled") is True
            if self._enabled:
                self._remember_sites()

    def get_state(self) -> bool:
        return self._enabled

    def get_api(self) -> list[dict]:
        return []

    def get_form(self) -> tuple[list[dict], dict]:
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VSwitch",
                        "props": {"model": "enabled", "label": "启用自动加入黑名单"},
                    },
                    {
                        "component": "VAlert",
                        "props": {
                            "type": "info",
                            "variant": "tonal",
                            "text": "删除单个站点时生效。重新允许同步时，请从 CookieCloud 同步黑名单移除对应域名。",
                        },
                    },
                ],
            },
        ], {"enabled": False}

    def get_page(self) -> None:
        return None

    def stop_service(self) -> None:
        """Stop processing events and discard the site snapshot."""
        with self._lock:
            self._enabled = False
            self._domains.clear()

    def _remember_sites(self) -> None:
        """Refresh live entries while retaining any pending deletion events."""
        try:
            for site in SiteOper().list():
                domain = _hostname(site.domain or "")
                if domain:
                    self._domains[site.id] = domain
        except Exception:
            logger.exception("CookieCloud 黑名单插件读取站点列表失败")

    @eventmanager.register(EventType.SiteUpdated)
    def site_updated(self, event: Event) -> None:
        """Capture newly added or edited sites while they still exist."""
        with self._lock:
            if self._enabled:
                self._remember_sites()

    @eventmanager.register(EventType.SiteDeleted)
    def site_deleted(self, event: Event) -> None:
        """Merge the deleted site's domain into the host's live setting."""
        site_id = event.event_data.get("site_id")
        with self._lock:
            if not self._enabled:
                return
            if site_id == "*":
                self._domains.clear()
                self._remember_sites()
                return
            if type(site_id) is not int or site_id <= 0:
                return
            domain = self._domains.get(site_id)
            if not domain:
                logger.warning("站点 ID %s 缺少域名快照，无法添加 CookieCloud 黑名单", site_id)
                return
            blacklist = settings.COOKIECLOUD_BLACKLIST or ""
            if domain not in {_hostname(entry) for entry in blacklist.split(",")}:
                updated = f"{blacklist},{domain}" if blacklist.strip() else domain
                success, message = settings.update_setting("COOKIECLOUD_BLACKLIST", updated)
                if success is False:
                    logger.error("写入 CookieCloud 黑名单失败（%s）：%s", domain, message)
                    return
                logger.info("已将 %s 加入 CookieCloud 同步黑名单", domain)
            del self._domains[site_id]
