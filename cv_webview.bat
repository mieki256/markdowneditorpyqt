@echo ## .uiファイルを .pyファイルに変換します。

pyrcc4 -o resources_rc.py resources.qrc
pyuic4 -o mywebview.py mywebview.ui
