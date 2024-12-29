# Copyright 2024 MezoAhmedII
# SPDX-License-Identifier: GPL-3.0-or-later

from random import choice
import json
from gi.repository import Gtk, Gio, Adw, Gdk, GLib


@Gtk.Template(resource_path="/io/github/mezoahmedii/Picker/window.ui")
class PickerWindow(Adw.ApplicationWindow):
    __gtype_name__ = "PickerWindow"

    toast_overlay = Gtk.Template.Child()
    header_bar = Gtk.Template.Child()
    elementsList = Gtk.Template.Child()
    entryRow = Adw.EntryRow(title=_("Add something…"), show_apply_button=True)

    latest_removed_item = None
    currentFile = ""
    currentFileTitle = "New File"
    currentFileContent = {"datatype": "raw", "data": []}
    currentFileType = "plaintext"
    currentFileIsSaved = True
    action = None
    loadedFile = None
    loadedFileText = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gio.Settings(schema_id="io.github.mezoahmedii.Picker")

        self.settings.bind(
            "width", self, "default-width", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "height", self, "default-height", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "is-maximized", self, "maximized", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "is-fullscreen", self, "fullscreened", Gio.SettingsBindFlags.DEFAULT
        )

        self.createAction("choose-element", self.onChooseElement)
        self.createAction("restore-element", self.onRestoreElement)
        self.createAction("open-file", self.onOpenFile)
        self.createAction("save-file", self.onSaveFile)
        self.createAction("save-file-as", self.onSaveFileAs)
        self.createAction("save-file-as-plaintext", self.onSaveFileAsPlaintext)
        self.createAction("save-file-as-wheelofnames",
                          self.onSaveFileAsWheelofnames)

        self.entryRow.connect("apply", self.onEnterElement)
        self.elementsList.add(self.entryRow)
        self.header_bar.set_title_widget(Adw.WindowTitle())

        self.connect("close-request", self.onCloseApp)

        self.checkFileSaved()

    def onEnterElement(self, widget):
        if bool(self.entryRow.get_text().strip()):
            self.createElement(self.entryRow.get_text().strip())

            self.entryRow.set_text("")
            self.entryRow.set_show_apply_button(False)
            self.entryRow.set_show_apply_button(True)

            self.checkFileSaved()

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
            dialog.set_response_appearance(
                "copy", Adw.ResponseAppearance.SUGGESTED)
            dialog.add_response("remove", _("Remove"))
            dialog.set_response_appearance(
                "remove", Adw.ResponseAppearance.DESTRUCTIVE)

        dialog.choose(self, None, self.onChosenDialogResponse, chosenElement)

    def onRestoreElement(self, widget, __):
        self.elementsList.add(self.latest_removed_item)
        self.checkFileSaved()

    def onOpenFile(self, widget, __):
        filters = Gio.ListStore()
        filters.append(
            Gtk.FileFilter(name=_("Supported Files"),
                           suffixes=["txt", "json", "wheel"])
        )
        filters.append(Gtk.FileFilter(name=_("All Files"), patterns=["*"]))

        native = Gtk.FileDialog(filters=filters)
        native.open(self, None, self.onOpenFileResponse)

    def onSaveFile(self, widget, __):
        if self.currentFile == "":
            Gio.ActionMap.lookup_action(self, "save-file-as").activate()
        else:
            self.saveFile(Gio.File.new_for_path(self.currentFile))

    def onSaveFileAs(self, widget, __):
        filters = Gio.ListStore()
        if self.currentFileType == "wheelofnames":
            filters.append(
                Gtk.FileFilter(
                    name=_("Wheel Of Names Wheels"), suffixes=["json", "wheel"]
                )
            )
            initname = "New File.wheel"
        else:
            filters.append(Gtk.FileFilter(
                name=_("Text Files"), suffixes=["txt"]))
            initname = "New File.txt"

        filters.append(Gtk.FileFilter(name=_("All Files"), patterns=["*"]))

        native = Gtk.FileDialog(filters=filters, initial_name=initname)
        native.save(self, None, self.onSaveFileResponse)

    def onSaveFileAsPlaintext(self, widget, __):
        self.currentFileType = "plaintext"
        Gio.ActionMap.lookup_action(self, "save-file-as").activate()

    def onSaveFileAsWheelofnames(self, widget, __):
        self.currentFileType = "wheelofnames"
        Gio.ActionMap.lookup_action(self, "save-file-as").activate()

    def onCloseApp(self, __):
        if not self.currentFileIsSaved and not self.action:
            self.action = self.close
            self.saveAlert()
            return True

    def createElement(self, element):
        actionRow = Adw.ActionRow(
            title=element.replace("&", "&amp;")
        )

        removeButton = Gtk.Button(icon_name="remove-symbolic", valign="center")
        removeButton.get_style_context().add_class("destructive-action")
        removeButton.connect("clicked", self.removeElement, actionRow)

        actionRow.add_suffix(removeButton)
        self.elementsList.add(actionRow)

    def removeElement(self, widget, element):
        self.latest_removed_item = element
        self.elementsList.remove(element)

        self.toast_overlay.add_toast(
            Adw.Toast(
                title=_("Removed item from the list"),
                button_label=_("Undo"),
                action_name="win.restore-element",
            )
        )

        self.checkFileSaved()

    def onChosenDialogResponse(self, dialog, task, element):
        response = dialog.choose_finish(task)
        if response == "copy":
            Gdk.Display.get_default().get_clipboard().set(element.get_title())
            self.toast_overlay.add_toast(
                Adw.Toast(title=_("Copied item to clipboard")))
        if response == "remove":
            self.removeElement(None, element)

    def onOpenFileResponse(self, dialog, result):
        file = dialog.open_finish(result)
        if file is not None:
            file.load_contents_async(None, self.openFileComplete)

    def openFileComplete(self, file, result):
        contents = file.load_contents_finish(result)
        if not contents[0]:
            self.toast_overlay.add_toast(
                Adw.Toast(title=_("Unable to open file: ") + {contents[1]})
            )
            return

        try:
            text = contents[1].decode("utf-8")
        except UnicodeError as err:
            self.toast_overlay.add_toast(
                Adw.Toast(
                    title=_("Unable to open file: The file isn't encoded properly")
                )
            )
            return

        self.loadedFile = file
        self.loadedFileText = contents[1]
        if self.currentFileIsSaved:
            self.loadFile()
        else:
            self.action = self.loadFile
            self.saveAlert()

    def loadFile(self):
        info = self.loadedFile.query_info(
            "standard::display-name", Gio.FileQueryInfoFlags.NONE
        )
        if info:
            self.currentFileTitle = info.get_attribute_string(
                "standard::display-name")
        else:
            self.currentFileTitle = self.loadedFile.get_basename()

        self.currentFile = self.loadedFile.peek_path()

        try:
            fileJson = json.loads(self.loadedFileText)
            if fileJson["entries"] is not None:
                self.currentFileType = "wheelofnames"
            else:
                self.currentFileType = "plaintext"
        except Exception:
            self.currentFileType = "plaintext"

        self.currentFileContent = {
            "datatype": self.currentFileType,
            "data": self.loadedFileText.decode("utf-8"),
        }

        child = self.entryRow.get_parent().get_last_child().get_prev_sibling()
        while child is not None:
            self.elementsList.remove(child.get_next_sibling())
            child = child.get_prev_sibling()

        for element in self.convertData(
            {
                "datatype": self.currentFileType,
                "data": self.loadedFileText.decode("utf-8"),
            },
            "raw",
        )["data"]:
            self.createElement(element)

        self.checkFileSaved()

    def onSaveFileResponse(self, dialog, result):
        file = dialog.save_finish(result)
        if file is not None:
            if self.getElements() == "":
                self.currentFile = file.peek_path()
                self.currentFileTitle = file.get_basename()

            self.saveFile(file)

    def saveFile(self, file):
        if self.getElements() == "":
            self.currentFileContent = ""
            self.checkFileSaved()

            if self.action:
                self.action()
                self.action = None

        bytes = GLib.Bytes.new(
            self.convertData(self.getElements(), self.currentFileType)["data"].encode(
                "utf-8"
            )
        )
        file.replace_contents_bytes_async(
            bytes, None, False, Gio.FileCreateFlags.NONE, None, self.saveFileComplete
        )

    def saveFileComplete(self, file, result):
        res = file.replace_contents_finish(result)
        if not res:
            self.toast_overlay.add_toast(
                Adw.Toast(title=_("Unable to save file")))
            return

        info = file.query_info("standard::display-name",
                               Gio.FileQueryInfoFlags.NONE)
        if info:
            self.currentFileTitle = info.get_attribute_string(
                "standard::display-name")
        else:
            self.currentFileTitle = file.get_basename()

        self.currentFile = file.peek_path()
        self.currentFileContent = self.getElements()

        if self.action:
            self.action()
            self.action = None

        self.checkFileSaved()

    def saveAlert(self):
        dialog = Adw.AlertDialog()

        dialog.set_heading(_("Save Changes?"))
        dialog.set_body(_("Any unsaved changes will be lost."))

        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("discard", _("Discard"))
        dialog.set_response_appearance(
            "discard", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.add_response("save", _("Save"))
        dialog.set_response_appearance(
            "save", Adw.ResponseAppearance.SUGGESTED)
        dialog.set_default_response("save")

        dialog.choose(self, None, self.onSaveAlertResponse)

    def onSaveAlertResponse(self, dialog, event):
        response = dialog.choose_finish(event)
        if response == "close":
            self.action = None
        if response == "discard":
            self.action()
            self.action = None
        if response == "save":
            Gio.ActionMap.lookup_action(self, "save-file").activate()

    def convertData(self, data, datatype):
        originalType = data["datatype"]
        if originalType == datatype:
            return data

        rawData = {"datatype": "raw", "data": []}
        if originalType == "raw":
            rawData = data
        if originalType == "plaintext":
            for element in data["data"].splitlines():
                rawData["data"].append({"name": element})
        if originalType == "wheelofnames":
            dataJson = json.loads(data["data"])
            for element in dataJson["entries"]:
                rawData["data"].append({"name": element["text"]})
            rawData["extraData"] = json.dumps(dataJson)

        if datatype == "raw":
            return rawData
        if datatype == "plaintext":
            elements = []
            for element in rawData["data"]:
                elements.append(element["name"])
            return {"datatype": "plaintext", "data": "\n".join(elements)}
        if datatype == "wheelofnames":
            elements = []
            for element in rawData["data"]:
                elements.append({"text": element["name"]})
            finalData = {}
            if "extraData" in rawData:
                finalData = json.loads(rawData["extraData"])
                finalData["entries"] = elements
            else:
                finalData = {"entries": elements}
            return {"datatype": "wheelofnames", "data": json.dumps(finalData)}

    def checkFileSaved(self):
        if (
            self.getElements()["data"]
            == self.convertData(self.currentFileContent, "raw")["data"]
        ):
            self.set_title(f"{self.currentFileTitle} - " + _("Picker"))
            self.header_bar.get_title_widget().set_title(
                f"{self.currentFileTitle}")
            self.currentFileIsSaved = True
        else:
            self.set_title(f"• {self.currentFileTitle} - " + _("Picker"))
            self.header_bar.get_title_widget().set_title(
                f"• {self.currentFileTitle}")
            self.currentFileIsSaved = False

    def getElements(self):
        elements = {"datatype": "raw", "data": []}
        child = self.entryRow.get_parent().get_first_child().get_next_sibling()
        while child is not None:
            elements["data"].append(
                {"name": child.get_title().replace("&amp;", "&")})
            child = child.get_next_sibling()

        try:
            if "extraData" in self.convertData(self.currentFileContent, "raw"):
                elements["extraData"] = self.convertData(
                    self.currentFileContent, "raw"
                )["extraData"]
        except Exception:
            pass
        return elements

    def createAction(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
