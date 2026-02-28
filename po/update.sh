xgettext --files-from po/POTFILES --output po/picker.pot --add-comments
xgettext --join-existing --output po/picker.pot --add-comments  --language javascript src/window.blp
xgettext --join-existing --output po/picker.pot --add-comments  --language javascript src/shortcuts-dialog.blp
msgmerge -NU po/bg.po po/picker.pot
msgmerge -NU po/it.po po/picker.pot
msgmerge -NU po/nl.po po/picker.pot
msgmerge -NU po/oc.po po/picker.pot
