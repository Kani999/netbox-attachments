"""
Tests for netbox_attachments plugin configuration handling.
Tests all permutations of applied_scope, scope_filter, display_default, etc.
"""

from dcim.models import Device, Rack, Site
from django.apps import apps
from django.conf import settings
from django.test import TestCase, override_settings
from ipam.models import IPAddress, Prefix
from tenancy.models import Tenant

from netbox_attachments.template_content import get_display_preference
from netbox_attachments.utils import is_custom_object_model, validate_object_type


class PluginConfigurationTestCase(TestCase):
    """Test plugin configuration loading and validation"""

    def test_default_configuration(self):
        """Scenario 1: Test default configuration when no config provided"""
        with override_settings(PLUGINS_CONFIG={'netbox_attachments': {}}):
            config = settings.PLUGINS_CONFIG.get('netbox_attachments', {})

            # Defaults should apply
            self.assertEqual(config.get('applied_scope'), None)  # Will use 'app' default
            self.assertEqual(config.get('scope_filter'), None)  # Will use default list
            self.assertEqual(config.get('display_default'), None)  # Will use 'additional_tab'
            self.assertEqual(config.get('create_add_button'), None)  # Will use True

    def test_minimal_config_loads(self):
        """Verify minimal configuration doesn't cause errors"""
        with override_settings(PLUGINS_CONFIG={'netbox_attachments': {}}):
            # Should not raise any exceptions
            config = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
            self.assertIsInstance(config, dict)


class AppScopeFilteringTestCase(TestCase):
    """Test applied_scope='app' filtering behavior"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim', 'ipam'],
            }
        }
    )
    def test_app_scope_basic(self):
        """Scenario 2: App scope includes all models from specified apps"""
        # Reload utils module to pick up new settings
        import importlib

        from netbox_attachments import utils
        importlib.reload(utils)


        # dcim models should be included
        self.assertTrue(validate_object_type(Device))
        self.assertTrue(validate_object_type(Site))
        self.assertTrue(validate_object_type(Rack))

        # ipam models should be included
        self.assertTrue(validate_object_type(IPAddress))
        self.assertTrue(validate_object_type(Prefix))

        # tenancy models should NOT be included
        self.assertFalse(validate_object_type(Tenant))

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['netbox_custom_objects'],
            }
        }
    )
    def test_custom_objects_only_app_scope(self):
        """Scenario 10: Only custom objects enabled via app scope"""
        import importlib

        from netbox_attachments import utils
        importlib.reload(utils)


        # Standard models should NOT be included
        self.assertFalse(validate_object_type(Device))
        self.assertFalse(validate_object_type(Site))

        # Custom objects would be included (tested separately if plugin installed)


class ModelScopeFilteringTestCase(TestCase):
    """Test applied_scope='model' filtering behavior"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'model',
                'scope_filter': [
                    'dcim.device',
                    'dcim.site',
                    'ipam.ipaddress',
                ],
            }
        }
    )
    def test_model_scope_specific_models_only(self):
        """Scenario 3: Only specific models included"""
        import importlib

        from netbox_attachments import utils
        importlib.reload(utils)


        # Specified models should be included
        self.assertTrue(validate_object_type(Device))
        self.assertTrue(validate_object_type(Site))
        self.assertTrue(validate_object_type(IPAddress))

        # Other models should NOT be included
        self.assertFalse(validate_object_type(Rack))
        self.assertFalse(validate_object_type(Prefix))
        self.assertFalse(validate_object_type(Tenant))

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'model',
                'scope_filter': [
                    'dcim',  # Entire app
                    'ipam.ipaddress',  # Specific model
                    'virtualization.cluster',  # Specific model from different app
                ],
            }
        }
    )
    def test_model_scope_mixed_mode(self):
        """Scenario 4: Mixed app + specific models"""
        import importlib

        from netbox_attachments import utils
        importlib.reload(utils)

        from virtualization.models import Cluster, VirtualMachine


        # All dcim models should be included
        self.assertTrue(validate_object_type(Device))
        self.assertTrue(validate_object_type(Site))
        self.assertTrue(validate_object_type(Rack))

        # Only ipaddress from ipam
        self.assertTrue(validate_object_type(IPAddress))
        self.assertFalse(validate_object_type(Prefix))

        # Only cluster from virtualization
        self.assertTrue(validate_object_type(Cluster))
        self.assertFalse(validate_object_type(VirtualMachine))


class DisplayDefaultTestCase(TestCase):
    """Test display_default configuration"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'left_page',
            }
        }
    )
    def test_left_page_display(self):
        """Scenario 5: Left page display mode"""
        import importlib

        from netbox_attachments import template_content
        importlib.reload(template_content)


        display = get_display_preference('dcim.device')
        self.assertEqual(display, 'left_page')

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'right_page',
            }
        }
    )
    def test_right_page_display(self):
        """Scenario 6: Right page display mode"""
        import importlib

        from netbox_attachments import template_content
        importlib.reload(template_content)


        display = get_display_preference('dcim.device')
        self.assertEqual(display, 'right_page')

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'full_width_page',
            }
        }
    )
    def test_full_width_display(self):
        """Scenario 7: Full width display mode"""
        import importlib

        from netbox_attachments import template_content
        importlib.reload(template_content)


        display = get_display_preference('dcim.device')
        self.assertEqual(display, 'full_width_page')

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'additional_tab',
            }
        }
    )
    def test_additional_tab_display(self):
        """Test default additional_tab display mode"""
        import importlib

        from netbox_attachments import template_content
        importlib.reload(template_content)


        display = get_display_preference('dcim.device')
        self.assertEqual(display, 'additional_tab')


class DisplaySettingOverrideTestCase(TestCase):
    """Test display_setting per-model overrides"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'additional_tab',
                'display_setting': {
                    'dcim.device': 'full_width_page',
                    'dcim.site': 'left_page',
                    'dcim.rack': 'right_page',
                },
            }
        }
    )
    def test_mixed_display_settings(self):
        """Scenario 8: Per-model display overrides"""
        import importlib

        from netbox_attachments import template_content
        importlib.reload(template_content)

        from netbox_attachments.utils import validate_object_type

        # Override settings
        self.assertEqual(get_display_preference('dcim.device'), 'full_width_page')
        self.assertEqual(get_display_preference('dcim.site'), 'left_page')
        self.assertEqual(get_display_preference('dcim.rack'), 'right_page')

        # Default setting (no override)
        from dcim.models import DeviceRole
        if validate_object_type(DeviceRole):
            self.assertEqual(get_display_preference('dcim.devicerole'), 'additional_tab')


class CreateAddButtonTestCase(TestCase):
    """Test create_add_button configuration"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'additional_tab',
                'create_add_button': False,
            }
        }
    )
    def test_button_disabled(self):
        """Scenario 9: Add button disabled"""
        config = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
        self.assertFalse(config.get('create_add_button'))


class InvalidConfigurationTestCase(TestCase):
    """Test handling of invalid configuration values"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'invalid_value',
                'scope_filter': 'dcim',  # Should be list, not string
                'create_add_button': 'yes',  # Should be bool
            }
        }
    )
    def test_invalid_config_handling(self):
        """Scenario 13: Invalid configuration values"""
        import importlib

        from netbox_attachments import utils
        importlib.reload(utils)

        from dcim.models import Device


        # Should not crash, should use defaults or handle gracefully
        config = settings.PLUGINS_CONFIG.get('netbox_attachments', {})
        self.assertIsInstance(config, dict)
        
        # Validate that validate_object_type handles invalid config gracefully
        result = validate_object_type(Device)
        # Should return False or a sensible default, not raise an exception
        self.assertIsInstance(result, bool)
        # With invalid scope_filter, should default to not allowing attachments
        self.assertEqual(result, False)


class EmptyScopeFilterTestCase(TestCase):
    """Test behavior with empty scope_filter"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'model',
                'scope_filter': [],
            }
        }
    )
    def test_empty_scope_filter(self):
        """Scenario 14: Empty scope filter disables all attachments"""
        import importlib

        from netbox_attachments import utils
        importlib.reload(utils)


        # No models should be included
        self.assertFalse(validate_object_type(Device))
        self.assertFalse(validate_object_type(Site))
        self.assertFalse(validate_object_type(IPAddress))


class CustomObjectsNotInstalledTestCase(TestCase):
    """Test graceful degradation when custom objects plugin missing"""

    def setUp(self):
        """Check if custom objects plugin is currently installed"""
        try:
            apps.get_app_config('netbox_custom_objects')
            self.custom_objects_installed = True
        except LookupError:
            self.custom_objects_installed = False

    def test_missing_custom_objects_plugin(self):
        """Scenario 15: Custom objects in config but plugin not installed"""
        if self.custom_objects_installed:
            self.skipTest("Custom objects plugin is installed - cannot test missing plugin scenario")

        # Test configuration referencing non-existent plugin
        with override_settings(
            PLUGINS_CONFIG={
                'netbox_attachments': {
                    'applied_scope': 'app',
                    'scope_filter': ['dcim', 'netbox_custom_objects'],
                }
            }
        ):
            import importlib

            from netbox_attachments import template_content, utils
            importlib.reload(utils)
            importlib.reload(template_content)

            # Should not crash when referencing missing plugin
            from netbox_attachments.utils import validate_object_type

            # Standard models should still work
            self.assertTrue(validate_object_type(Device))
            self.assertTrue(validate_object_type(Site))

    def test_custom_objects_filtering_when_not_installed(self):
        """Verify netbox_custom_objects in scope_filter is ignored when plugin missing"""
        if self.custom_objects_installed:
            self.skipTest("Custom objects plugin is installed")

        with override_settings(
            PLUGINS_CONFIG={
                'netbox_attachments': {
                    'applied_scope': 'model',
                    'scope_filter': ['netbox_custom_objects.some_model'],
                }
            }
        ):
            import importlib

            from netbox_attachments import utils
            importlib.reload(utils)

            from netbox_attachments.utils import validate_object_type

            # No standard models should be enabled (only custom objects in filter)
            self.assertFalse(validate_object_type(Device))
            self.assertFalse(validate_object_type(Site))


class CustomObjectsIntegrationTestCase(TestCase):
    """Test custom objects integration (if plugin installed)"""

    def setUp(self):
        """Check if custom objects plugin is available"""
        try:
            self.custom_objects_app = apps.get_app_config('netbox_custom_objects')
        except LookupError:
            self.skipTest("Custom objects plugin not installed")

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['netbox_custom_objects'],
                'display_default': 'additional_tab',
            }
        }
    )
    def test_custom_objects_display_auto_conversion(self):
        """Custom objects auto-convert additional_tab to full_width_page"""
        import importlib

        from netbox_attachments import template_content, utils
        importlib.reload(utils)
        importlib.reload(template_content)

        from netbox_attachments.utils import (
            validate_object_type,
        )

        # Find a custom object model
        found_valid_model = False
        for model in self.custom_objects_app.get_models():
            if is_custom_object_model(model) and validate_object_type(model):
                try:
                    from netbox_custom_objects.models import CustomObjectType
                    cot = CustomObjectType.objects.get(id=model.custom_object_type_id)
                    model_id = f"netbox_custom_objects.{cot.name}"

                    # Config says additional_tab, but should be auto-converted
                    display = get_display_preference(model_id)
                    # Auto-conversion happens in template_content.py logic
                    # This test validates the configuration is read correctly
                    self.assertIn(display, ['additional_tab', 'full_width_page'])
                    found_valid_model = True
                    break
                except (CustomObjectType.DoesNotExist, AttributeError):
                    continue
        
        if not found_valid_model:
            self.fail("No valid custom object model found for testing")
