# Copyright 2024 MezoAhmedII
# SPDX-License-Identifier: GPL-3.0-or-later

import sys

from gi.repository import Gtk, Gio, Adw
from .window import PickerWindow


class PickerApplication(Adw.Application):
    """The main application singleton class."""

    __gtype_name__ = "PickerApplication"

    def __init__(self):
        super().__init__(
            application_id="io.github.mezoahmedii.Picker",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )

        self.create_action(
            "quit", lambda *_: self.props.active_window.close(), ["<primary>q"])
        self.create_action(
            "preferences", self.on_preferences_action, ["<Ctrl>comma"])
        self.create_action("about", self.on_about_action)

        self.set_accels_for_action("win.choose-element", ["<primary>Return"])
        self.set_accels_for_action("win.open-file", ["<primary>o"])
        self.set_accels_for_action("win.save-file", ["<primary>s"])
        self.set_accels_for_action("win.save-file-as", ["<primary><shift>s"])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = PickerWindow(application=self)
        win.present()

    def on_about_action(self, widget, __):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name=_("Picker"),
            application_icon="io.github.mezoahmedii.Picker",
            developer_name="MezoAhmedII",
            website="https://github.com/mezoahmedii/picker",
            issue_url="https://github.com/mezoahmedii/picker/issues",
            version="1.3.0",
            developers=["MezoAhmedII"],
            copyright="© 2024 MezoAhmedII",
            license_type=Gtk.License.GPL_3_0,
        )
        about.present(parent=self.props.active_window)

    def on_preferences_action(self, widget, __):
        hideLogoPreference = Adw.SwitchRow(title=_("Hide App Logo"))
        Gio.Settings(schema_id="io.github.mezoahmedii.Picker").bind(
            "hide-logo", hideLogoPreference, "active", Gio.SettingsBindFlags.DEFAULT)
        hideLogoPreference.connect("notify::active", lambda widget,
                                   __: self.props.active_window.changeLogoVisibility(not widget.get_active()))

        generalPreferences = Adw.PreferencesGroup(title="General")
        generalPreferences.add(hideLogoPreference)

        preferencesPage = Adw.PreferencesPage()
        preferencesPage.add(generalPreferences)

        dialogContent = Adw.ToolbarView(content=preferencesPage)
        dialogContent.add_top_bar(Adw.HeaderBar())

        dialog = Adw.PreferencesDialog(child=dialogContent)
        dialog.present(parent=self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    """The application's entry point."""
    app = PickerApplication()
    return app.run(sys.argv)
