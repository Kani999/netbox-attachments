"""
Tests for template extension registration based on configuration.
"""

from django.test import TestCase, override_settings


class TemplateExtensionRegistrationTestCase(TestCase):
    """Test template extension registration"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'additional_tab',
                'create_add_button': True,
            }
        }
    )
    def test_extensions_registered_with_tab_mode(self):
        """Verify template extensions are registered for tab mode"""
        import importlib
        from netbox_attachments import template_content
        importlib.reload(template_content)

        from netbox_attachments.template_content import template_extensions

        # Should have extensions registered
        self.assertGreater(len(template_extensions), 0)

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'left_page',
            }
        }
    )
    def test_extensions_registered_with_panel_mode(self):
        """Verify template extensions are registered for panel mode"""
        import importlib
        from netbox_attachments import template_content
        importlib.reload(template_content)

        from netbox_attachments.template_content import template_extensions

        # Should have panel extensions registered
        self.assertGreater(len(template_extensions), 0)

        # Check for panel extensions with left_page attribute
        panel_extensions = [
            ext for ext in template_extensions
            if hasattr(ext, 'left_page')
        ]
        self.assertGreater(len(panel_extensions), 0)

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'model',
                'scope_filter': [],
            }
        }
    )
    def test_no_extensions_with_empty_scope(self):
        """Verify no extensions registered when scope_filter is empty"""
        import importlib
        from netbox_attachments import template_content
        importlib.reload(template_content)

        from netbox_attachments.template_content import template_extensions

        # Should have no extensions when scope_filter is empty
        self.assertEqual(len(template_extensions), 0, "Should have no template extensions when scope_filter is empty")


class DisplayModeExtensionTestCase(TestCase):
    """Test extension types based on display mode"""

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'additional_tab',
                'create_add_button': True,
            }
        }
    )
    def test_button_extension_with_tab_mode(self):
        """Button extensions only created in tab mode with create_add_button=True"""
        import importlib
        from netbox_attachments import template_content
        importlib.reload(template_content)

        from netbox_attachments.template_content import template_extensions

        # Look for button extensions
        button_extensions = [
            ext for ext in template_extensions
            if 'button' in ext.__class__.__name__.lower()
        ]

        # Should have button extensions when create_add_button=True and display_default='additional_tab'
        self.assertIsInstance(template_extensions, list)
        self.assertGreater(len(button_extensions), 0, "Should have button extensions when create_add_button=True")
        # Verify each button extension has expected class characteristic
        for ext in button_extensions:
            self.assertIn('button', ext.__class__.__name__.lower())

    @override_settings(
        PLUGINS_CONFIG={
            'netbox_attachments': {
                'applied_scope': 'app',
                'scope_filter': ['dcim'],
                'display_default': 'full_width_page',
            }
        }
    )
    def test_panel_extension_attributes(self):
        """Panel extensions have correct display method attributes"""
        import importlib
        from netbox_attachments import template_content
        importlib.reload(template_content)

        from netbox_attachments.template_content import template_extensions

        # Find panel extensions
        panel_extensions = [
            ext for ext in template_extensions
            if hasattr(ext, 'full_width_page')
        ]

        # Should have panel extensions with full_width_page display mode
        self.assertGreater(len(panel_extensions), 0, "Should have panel extensions when display_default='full_width_page'")
        
        # Verify they have the models attribute
        for ext in panel_extensions:
            self.assertTrue(hasattr(ext, 'models'), f"Panel extension {ext.__class__.__name__} missing 'models' attribute")
