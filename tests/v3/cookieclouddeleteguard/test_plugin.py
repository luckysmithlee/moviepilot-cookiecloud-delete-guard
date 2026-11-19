"""Exercise plugin behavior with MoviePilot's actual event and plugin classes."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from app.plugins.cookieclouddeleteguard import CookieCloudDeleteGuard
from app.schemas.types import EventType
from app.sdk.events import Event


MODULE = "app.plugins.cookieclouddeleteguard"


class CookieCloudDeleteGuardTest(TestCase):
    def setUp(self):
        self.enterContext(patch("app.sdk.plugin.base.PluginChain"))
        self.site_oper = self.enterContext(patch(f"{MODULE}.SiteOper"))
        self.sites = self.site_oper.return_value.list
        self.sites.return_value = [SimpleNamespace(id=1, domain="demo.example")]
        self.settings = self.enterContext(patch(f"{MODULE}.settings"))
        self.settings.COOKIECLOUD_BLACKLIST = "keep.example"
        self.settings.update_setting = Mock(return_value=(True, ""))
        self.plugin = CookieCloudDeleteGuard()
        self.addCleanup(self.plugin.stop_service)

    def delete(self, site_id):
        self.plugin.site_deleted(Event(EventType.SiteDeleted, {"site_id": site_id}))

    def enable(self):
        self.plugin.init_plugin({"enabled": True})

    def test_delete_merges_with_existing_entries(self):
        self.enable()
        self.sites.return_value = []
        self.delete(1)
        self.settings.update_setting.assert_called_once_with(
            "COOKIECLOUD_BLACKLIST", "keep.example,demo.example"
        )

    def test_repeated_delivery_does_not_write_twice(self):
        self.enable()
        self.delete(1)
        self.delete(1)
        self.settings.update_setting.assert_called_once()

    def test_existing_domain_url_is_not_duplicated(self):
        self.settings.COOKIECLOUD_BLACKLIST = "keep.example, https://DEMO.example:443/"
        self.enable()
        self.delete(1)
        self.settings.update_setting.assert_not_called()

    def test_update_captures_new_sites_and_keeps_pending_deletions(self):
        self.enable()
        self.sites.return_value = [SimpleNamespace(id=2, domain="new.example")]
        self.plugin.site_updated(Event(EventType.SiteUpdated, {"domain": "new.example"}))
        self.delete(1)
        self.settings.COOKIECLOUD_BLACKLIST = "keep.example,demo.example"
        self.delete(2)
        self.assertEqual(self.settings.update_setting.call_args_list[0].args[-1],
                         "keep.example,demo.example")
        self.assertEqual(self.settings.update_setting.call_args_list[1].args[-1],
                         "keep.example,demo.example,new.example")

    def test_bulk_reset_does_not_blacklist_sites(self):
        self.enable()
        self.sites.return_value = []
        self.delete("*")
        self.delete(1)
        self.settings.update_setting.assert_not_called()

    def test_disabled_plugin_does_not_write(self):
        self.plugin.init_plugin({})
        self.delete(1)
        self.enable()
        self.plugin.stop_service()
        self.delete(1)
        self.settings.update_setting.assert_not_called()

    def test_failed_write_retains_domain_for_a_retried_event(self):
        self.enable()
        self.settings.update_setting.side_effect = [(False, "read-only"), (True, "")]
        self.delete(1)
        self.delete(1)
        self.assertEqual(self.settings.update_setting.call_count, 2)
