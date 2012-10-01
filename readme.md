# MarkdownEditorPyQt

Python + PyQt4 で作った、markdown記述用の簡易エディタです。

* Windows7 x64上でのみ動作確認しています。
* PyQtはクロスプラットフォームのはずですので、Mac や Linux で動作させることも、容易なのかもしれません。

## 特徴

### 長所

* markdownからHTMLへの変換結果を、リアルタイムにプレビューできます。
* markdown用の記号がいくつか挿入できます。
* cssを切替えて、プレビューの見た目を変えられます。
* 変換結果をhtmlとしてエクスポートできます。
* 只のスクリプトなので、動作を自分好みに修正することが容易です。

### 短所

* utf8n で書かれたファイルの読み書きにしか対応していません。
* 動作には Python + PyQt4 + markdown2 が必要です。(環境によっては、.exe を実行できるかもしれません。)

## スクリーンショット

<!-- ![ScreenShot](screenshot_mep.png) -->
![ScreenShot](https://dl.dropbox.com/u/84075965/screenshot/markdowneditorpyqt/screenshot_mep.png)

## 動作に必要なもの

* [Python](http://www.python.org/download/)
* [PyQt4](http://www.riverbankcomputing.co.uk/software/pyqt/download)
* [markdown2](https://github.com/trentm/python-markdown2)

## 実行

Python +  PyQt4 + markdown2 がインストールされている環境で、以下を実行します。

    markdowneditorpyqt.pyw

(環境によっては、Python等がインストールされてなくても、dist\markdowneditorpyqt.exe を実行することができるかもしれません。)

## ライセンス

GPLです。

そもそもPyQtがGPLですので、PyQtを使ったプログラムは、GPLを継承しなければならないそうです。

改変や、exe化をして配布・公開する場合は、そのスクリプトソースも一緒に同梱すれば問題無いのでは…と思います。(誰でもソースを見れて、誰でも改変OKにすることが、GPLの目的のはずなので、ソースも同梱しておけば文句ないはず…。)

## 挿入機能について

* テキスト選択をしていない状態で挿入機能を呼べば、行頭や行末に記号を挿入したり、書き方の一例を挿入したりします。

* テキスト選択してから挿入機能を呼ぶと、複数行に対して同じ記号を挿入したり、選択した単語を装飾用記号で挟むこともできます。
   * 行単位で処理したい場合は、基本的に行単位で選択してから呼んでください。

## cssについて

css\ 以下に、自分好みの .css ファイルを置けば、選べるようになります。

## htmlエクスポートについて

resource\templete.html を修正すれば、エクスポートするhtml内の記述を自分好みに変更できます。

## markdown用の記号について

resource\templete_markdown.csv を修正すれば、自分好みの markdown用記号を使えます。

## GUIレイアウトを変更したい場合

Qt Designer で mywebview.ui を開いて変更・保存後、cv_webview.bat を実行して、.ui ファイルと、.qrcファイルをPythonスクリプトに変換すれば、変更内容が反映されます。

cv_webview.bat の内容は以下の通りです。

    pyrcc4 -o resources_rc.py resources.qrc
    pyuic4 -o mywebview.py mywebview.ui

## exe化について

py2exe、PythonWin(pywin32？)等がインストール済みの環境なら、py2exe を使ってexe化することができるかもしれません。

その場合、setup.py の、

        WIN32UI_DIR = r"C:\Python27\Lib\site-packages\pythonwin"
        IMAGELIB_DIR = r"C:\Python27\Lib\site-packages\PyQt4\plugins\imageformats"

の2行を自分の環境に合わせて修正した上で、make_exe.bat を実行してください。distフォルダ以下に markdowneditorpyqt.exe その他が生成されます。

一応、生成した .exe は、以下の環境で動作することを確認しました。

* Windows7 x64
* Windows7 x64 上のXPモード


## 動作確認環境

* Windows7 x64
* Python 2.7.3 (python-2.7.3.msi)
* PyQt 4.9.4-1 (PyQt-Py2.7-x86-gpl-4.9.4-1.exe)
* markdown2 2.1.0

## 履歴

2012/10/02 ver. 0.0.4

* exe化できるように修正。
* py2exe用のsetup.py等を追加。

2012/10/01 ver. 0.0.3

* ドラッグアンドドロップでファイルを開けるようにした。
* 日本語フォルダ・ファイル名も開けるように修正。

2012/09/30 ver. 0.0.2

* htmlプレビューをカーソル位置と(大味に)合わせてスクロールさせるようにした。

2012/09/29 ver. 0.0.1

* 編集機能を実装。

