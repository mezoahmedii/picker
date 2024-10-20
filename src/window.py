# Copyright 2024 MezoAhmedII
# SPDX-License-Identifier: GPL-3.0-or-later

from random import choice
from gi.repository import Gtk, Gio, Adw, Gdk, GLib

@Gtk.Template(resource_path='/io/github/mezoahmedii/Picker/window.ui')
class PickerWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'PickerWindow'

    toast_overlay = Gtk.Template.Child()
    elementsList = Gtk.Template.Child()
    entryRow = Adw.EntryRow(title=_("Add something…"), show_apply_button=True)

    latest_removed_item = None
    currentFile = ""
    currentFileTitle = "New File"
    currentFileContent = ""
    currentFileIsSaved = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings(schema_id="io.github.mezoahmedii.Picker")

        self.settings.bind("width", self, "default-width",
                           Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("height", self, "default-height",
                           Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-maximized", self, "maximized",
                           Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("is-fullscreen", self, "fullscreened",
                           Gio.SettingsBindFlags.DEFAULT)

        self.createAction("choose-element", self.onChooseElement)
        self.createAction("restore-element", self.onRestoreElement)
        self.createAction("open-file", self.onOpenFile)
        self.createAction("save-file", self.onSaveFile)
        self.createAction("save-file-as", self.onSaveFileAs)

        self.entryRow.connect("apply", self.onEnterElement, _)
        self.elementsList.add(self.entryRow)

        self.checkFileSaved()

    def onEnterElement(self, widget, _):
        if bool(self.entryRow.get_text().strip()):
            actionRow = Adw.ActionRow(title=self.entryRow.get_text().strip().replace("&", "&amp;"))

            removeButton = Gtk.Button(icon_name="remove-symbolic", valign="center")
            removeButton.get_style_context().add_class("destructive-action")
            removeButton.connect("clicked", self.removeElement, actionRow)

            actionRow.add_suffix(removeButton)

            self.addElement(actionRow)

            self.entryRow.set_text("")
            self.entryRow.set_show_apply_button(False)
            self.entryRow.set_show_apply_button(True)

    def onChooseElement(self, widget, __):
        elements = []
        child = self.entryRow.get_parent().get_first_child().get_next_sibling()
        while child is not None:
            elements.append(child)
            child = child.get_next_sibling()

        chosenElement = ""

        dialog = Adw.AlertDialog()

        dialog.add_response("dismiss", _("Okay"))
        dialog.set_default_response("dismiss")

        if elements == []:
            dialog.set_heading(_("Nothing to Choose"))
            dialog.set_body(_("Please enter some things to be chosen from."))
        else:
            chosenElement = choice(elements)
            dialog.set_heading(chosenElement.get_title().replace("&amp;", "&"))
            dialog.set_body(_("has been chosen!"))
            dialog.add_response("copy", _("Copy"))
            dialog.set_response_appearance("copy",
                                           Adw.ResponseAppearance.SUGGESTED)
            dialog.add_response("remove", _("Remove"))
            dialog.set_response_appearance("remove",
                                           Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.choose(self, None, self.onChosenDialogResponse, chosenElement)

    def onRestoreElement(self, widget, _):
        self.addElement(self.latest_removed_item)

    def onOpenFile(self, widget, _):
        native = Gtk.FileDialog()
        native.open(self, None, self.onOpenFileResponse)

    def onSaveFile(self, widget, __):
        if self.currentFile == "":
            Gio.ActionMap.lookup_action(self, "save-file-as").activate()
        else:
            self.saveFile(Gio.File.new_for_path(self.currentFile))

    def onSaveFileAs(self, widget, __):
        native = Gtk.FileDialog()
        native.save(self, None, self.onSaveFileResponse)

    def addElement(self, element):
        self.elementsList.add(element)

        self.checkFileSaved()

    def removeElement(self, widget, element):
        self.latest_removed_item = element
        self.elementsList.remove(element)

        self.toast_overlay.add_toast(
            Adw.Toast(title=_("Removed item from the list"),
                button_label=_("Undo"),
                action_name="win.restore-element")
        )

        self.checkFileSaved()

    def onChosenDialogResponse(self, dialog, task, element):
        response = dialog.choose_finish(task)
        if response == "copy":
            Gdk.Display.get_default().get_clipboard().set(element.get_title())
            self.toast_overlay.add_toast(Adw.Toast(title=_("Copied item to clipboard")))
        if response == "remove":
            self.removeElement(None, element)

    def onOpenFileResponse(self, dialog, result):
        file = dialog.open_finish(result)
        if file is not None:
            file.load_contents_async(None, self.openFileComplete)

    def openFileComplete(self, file, result):
        contents = file.load_contents_finish(result)
        if not contents[0]:
            self.toast_overlay.add_toast(Adw.Toast(title=_("Unable to open file: ") + {contents[1]}))
            return

        try:
            text = contents[1].decode('utf-8')
        except UnicodeError as err:
            self.toast_overlay.add_toast(Adw.Toast(title=_("Unable to open file: The file isn't encoded properly")))
            return

        info = file.query_info("standard::display-name", Gio.FileQueryInfoFlags.NONE)
        if info:
            display_name = info.get_attribute_string("standard::display-name")
        else:
            display_name = file.get_basename()
        self.set_title(display_name)

        self.currentFile = file.peek_path()
        self.currentFileContent = text
        self.currentFileTitle = display_name

        child = self.entryRow.get_parent().get_last_child().get_prev_sibling()
        while child is not None:
            self.elementsList.remove(child.get_next_sibling())
            child = child.get_prev_sibling()

        for element in text.splitlines():
            actionRow = Adw.ActionRow(title=element.replace("&", "&amp;"))

            removeButton = Gtk.Button(icon_name="remove-symbolic", valign="center")
            removeButton.get_style_context().add_class("destructive-action")
            removeButton.connect("clicked", self.removeElement, actionRow)

            actionRow.add_suffix(removeButton)

            self.elementsList.add(actionRow)

    def onSaveFileResponse(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            self.saveFile(file)

    def saveFile(self, file):
        bytes = GLib.Bytes.new(self.getElements().encode("utf-8"))
        file.replace_contents_bytes_async(bytes, None, False, Gio.FileCreateFlags.NONE, None, self.saveFileComplete)

    def saveFileComplete(self, file, result):
        res = file.replace_contents_finish(result)
        info = file.query_info("standard::display-name", Gio.FileQueryInfoFlags.NONE)
        if info:
            display_name = info.get_attribute_string("standard::display-name")
        else:
            display_name = file.get_basename()

        if not res:
            self.toast_overlay.add_toast(Adw.Toast(title=_("Unable to save file")))
            return

        self.currentFile = file.peek_path()
        self.currentFileContent = self.getElements()
        self.currentFileTitle = display_name

        self.checkFileSaved()

    def checkFileSaved(self):
        if self.getElements() == self.currentFileContent:
            self.set_title(f"{self.currentFileTitle} -" + _("Picker"))
            self.currentFileIsSaved = True
        else:
            self.set_title(f"• {self.currentFileTitle} -" + _("Picker"))
            self.currentFileIsSaved = False

    def getElements(self):
        elements = []
        child = self.entryRow.get_parent().get_first_child().get_next_sibling()
        while child is not None:
            elements.append(child.get_title().replace("&amp;", "&"))
            child = child.get_next_sibling()

        return "\n".join(elements)

    def createAction(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
