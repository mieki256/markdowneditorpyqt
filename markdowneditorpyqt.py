#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python;Encoding: utf8n -*-

'''
MarkdownEditorPyQt

* Python + PyQt4 + markdown2 で markdownのリアルタイムプレビューを行う。
* utf8nで書かれたMarkdownファイルのみに対応。

'''

import sys
import os
from PyQt4 import QtCore, QtGui, QtWebKit
from mywebview import Ui_MyWebView
import codecs
import markdown2
import glob
import csv
import webbrowser


__version__ = '0.0.2'
WDW_TITLE_DEF = "MarkdownEditorPyQt"

DBG = False

# 初期フォルダをホームディレクトリにするか、スクリプトのある場所にするか
FIRST_DIR_IS_HOME = False

# 編集するたび逐一HTMLを更新せず、一定時間毎に更新するならTrueに
ONENTER_JOB = False

# スクリプトから開く各ファイル名の定義
TEMPLETE_HTML_FNAME = "templete.html"
TEMPLETE_MD_FNAME = "templete_markdown.csv"
HELP_FNAME = "help.html"
SAMPLE_FNAME = "sample.md"

# htmlの雛形。
# %s には、css部分、html本文が入る。
# テンプレートファイルが見つからない場合に使う。
HTML_DT_INIT = """<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8" /><title>Title</title>
<style>%s</style></head><body>%s</body></html>
"""

# markdownで使う記号群。テンプレートファイルが見つからない場合に使う。
MD_KEYWORD_LIST = {"h1": "# ", "h2": "## ", "h3": "### ", "h4": "#### ",
                   "h5": "##### ", "h6": "###### ", "ul": "* ", "ol": "1. ",
                   "cite": "> ", "pre": "    ", "hr": "----", "code": "`",
                   "em": "*", "strong": "**", "br": "  ",
                   "href": '[Text](URL "Title")',
                   "img": '![Text](/path/to/img.jpg)',
                   "idlink": '[Text] [ID]',
                   "idurl": '[ID]: <URL> "Opt Title"'}

# 「全て消去」を呼んだ時のダイアログメッセージ
MSG_CLEAR = (u"全てのテキストを消去します。" "\n"
             u"「元に戻す」ことはできません。" "\n\n"
             u"実行しますか？")


class StartQT4(QtGui.QMainWindow):

    def __init__(self, open_file=None, parent=None):
        """初期化処理"""
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MyWebView()
        self.ui.setupUi(self)

        # css一覧を取得
        self.css_list = ["default.css"]
        self.css_dir = os.path.join(self.get_script_dirname(), 'css')
        dname = os.path.join(self.css_dir, '*.css')
        for fn in glob.glob(dname):
            bn = os.path.basename(fn)
            if bn != "default.css":
                self.css_list.append(bn)

        for fn in self.css_list:
            self.ui.css_combobox.addItem(fn)

        self.load_css(self.css_list[0])   # CSSをロード
        self.load_html_templete()         # HTMLテンプレートをロード
        self.load_markdown_dic()          # markdownテンプレートをロード

        os.chdir(self.get_script_dirname())

        self.filename = ""
        self.basename = ""
        self.last_dir = ""
        self.wdw_title = WDW_TITLE_DEF
        self.html_data = self.get_html_data("")
        self.converting = False
        self.count = 0
        self.mainframe_w = 0
        self.mainframe_h = 0
        self.mainframe_vw = 0
        self.mainframe_vh = 0
        self.scrlCmd = ""
        self.load_success = True
        self.set_saved()

        self.auto_reload = True
        self.ui.checkbox_preview.setChecked(True)

        # 一定時間毎に変換する場合の初期化処理
        if ONENTER_JOB:
            self.conv_req = 0
            self.timer = QtCore.QTimer()
            self.timer.setInterval(1000)
            self.timer.timeout.connect(self.on_enter_frame)
            self.timer.start()

        # メニューを設定(ツールバーボタンはメニュー項目と同じ)
        self.setup_file_actions()
        self.setup_view_actions()
        self.setup_help_actions()
        self.setup_insert_actions()
        self.setup_edit_actions()

        # 編集ウインドウが変更された際に呼ばれる処理を指定
        self.ui.editor_window.textChanged.connect(self.chg_text)

        # 編集ウインドウ内でカーソル位置が変更された際に呼ばれる処理
        self.ui.editor_window.cursorPositionChanged.connect(self.chg_position)

        # QWebView内サイズが変更された際に呼ばれる処理を指定
        self.mainframe = self.ui.my_webview.page().mainFrame()
        self.mainframe.contentsSizeChanged.connect(self.chg_contents_size)
        self.mainframe.loadFinished.connect(self.load_finished)

        # チェックボックス、ComboBoxを設定
        self.ui.css_combobox.activated.connect(self.chg_css)
        self.ui.checkbox_preview.stateChanged.connect(self.chg_cb_preview)

        # 開発・実験用のメニュー項目を設定
        self.ui.action_test1.triggered.connect(self.action_test1)
        self.ui.action_test2.triggered.connect(self.action_test2)
        self.ui.action_test3.triggered.connect(self.action_test3)

        # objectNameを使って自動で動作を割り当てる
        ## QtCore.QMetaObject.connectSlotsByName(self)

        # 開くファイル名を与えられた状態で起動しているかどうか
        if open_file is not None:
            self.open_file_exec(open_file)

        # ステータスバーにメッセージ表示
        self.statusBar().showMessage('Ready.')

        # 編集ウインドウにフォーカスを当てる
        self.ui.editor_window.setFocus()

    def setup_file_actions(self):
        """ファイルメニューの設定"""
        self.ui.action_new.triggered.connect(self.make_new_file)
        self.ui.action_open.triggered.connect(self.open_file)
        self.ui.action_save.triggered.connect(self.save_file)
        self.ui.action_saveas.triggered.connect(self.saveas_file)
        self.ui.action_export_html.triggered.connect(self.export_html)
        self.ui.action_exit.triggered.connect(self.close)

    def setup_view_actions(self):
        """表示メニューの設定"""
        self.ui.action_html_reload.triggered.connect(self.reload_webview)
        self.ui.action_font.triggered.connect(self.select_font)
        self.ui.action_preview_set.triggered.connect(self.chg_auto_reload)

    def setup_help_actions(self):
        """ヘルプメニューの設定"""
        self.ui.action_help.triggered.connect(self.display_help)
        self.ui.action_open_sample.triggered.connect(self.open_sample_file)
        self.ui.action_about.triggered.connect(self.display_about)

    def setup_insert_actions(self):
        """挿入メニューの設定"""
        self.ui.action_ins_head1.triggered.connect(self.ins_h1)
        self.ui.action_ins_head2.triggered.connect(self.ins_h2)
        self.ui.action_ins_head3.triggered.connect(self.ins_h3)
        self.ui.action_ins_head4.triggered.connect(self.ins_h4)
        self.ui.action_ins_head5.triggered.connect(self.ins_h5)
        self.ui.action_ins_head6.triggered.connect(self.ins_h6)

        self.ui.action_ins_ul.triggered.connect(self.ins_ul)
        self.ui.action_ins_ol.triggered.connect(self.ins_ol)
        self.ui.action_ins_cite.triggered.connect(self.ins_cite)
        self.ui.action_ins_code_multi.triggered.connect(self.ins_code_multi)
        self.ui.action_ins_hr.triggered.connect(self.ins_hr)
        self.ui.action_ins_idlink.triggered.connect(self.ins_idlink)
        self.ui.action_ins_idurl.triggered.connect(self.ins_idurl)
        self.ui.action_ins_link.triggered.connect(self.ins_link)
        self.ui.action_ins_image.triggered.connect(self.ins_img)
        self.ui.action_ins_code_word.triggered.connect(self.ins_code_word)
        self.ui.action_ins_em.triggered.connect(self.ins_em)
        self.ui.action_ins_strong.triggered.connect(self.ins_strong)
        self.ui.action_ins_br.triggered.connect(self.ins_br)

    def setup_edit_actions(self):
        """編集メニューの設定"""
        # コピー、貼り付け、切り取り等の設定
        self.textEdit = self.ui.editor_window
        self.ui.action_copy.triggered.connect(self.textEdit.copy)
        self.ui.action_cut.triggered.connect(self.textEdit.cut)
        self.ui.action_paste.triggered.connect(self.textEdit.paste)
        self.ui.action_select_all.triggered.connect(self.textEdit.selectAll)

        self.ui.action_clear.triggered.connect(self.edit_clear)
        self.ui.action_duplicate.triggered.connect(self.duplicate_line)

        # undo/redo状態が変わった時に呼ばれる処理を設定
        self.textEdit.undoAvailable.connect(self.ui.action_undo.setEnabled)
        self.textEdit.redoAvailable.connect(self.ui.action_redo.setEnabled)

        self.doc = self.textEdit.document()
        self.ui.action_undo.setEnabled(self.doc.isUndoAvailable())
        self.ui.action_redo.setEnabled(self.doc.isRedoAvailable())

        self.ui.action_undo.triggered.connect(self.textEdit.undo)
        self.ui.action_redo.triggered.connect(self.textEdit.redo)

    def get_script_dirname(self):
        """スクリプトファイルのあるフォルダ名を取得"""
        return os.path.dirname(__file__)

    def get_dirname(self, path):
        """与えれたパスからフォルダ名を取得して返す"""
        return os.path.dirname(path)

    def get_last_dir(self):
        """最後にアクセスしたフォルダ名を取得"""
        if self.last_dir == "":
            # アクセスフォルダの記録が無いので、所定のフォルダ名を返す。
            if FIRST_DIR_IS_HOME:
                return os.path.expanduser("~")
            else:
                return self.get_script_dirname()
        else:
            # アクセスフォルダ名を返す。
            return self.last_dir

    def set_last_dir(self, filepath):
        """最後にアクセスしたフォルダ名を記憶"""
        self.last_dir = os.path.dirname(str(self.filename))

    def load_html_templete(self):
        """HTMLテンプレートファイルを開く"""
        fn = os.path.join(self.get_script_dirname(), TEMPLETE_HTML_FNAME)
        try:
            with codecs.open(fn, 'r', 'utf-8') as f:
                self.html_template = f.read()
        except IOError, inst:
            sys.stderr.write(str(inst) + "\n")
            self.html_template = HTML_DT_INIT

    def load_markdown_dic(self):
        """markdownテンプレートを開く"""
        self.md_dic = {}
        fn = os.path.join(self.get_script_dirname(), TEMPLETE_MD_FNAME)
        try:
            with open(fn, 'rt') as f:
                reader = csv.reader(f)
                for row in reader:
                    self.md_dic[row[0]] = row[1]
        except IOError, inst:
            sys.stderr.write(str(inst) + "\n")
            for key, value in MD_KEYWORD_LIST.items():
                self.md_dic[key] = value

    def load_css(self, basename):
        """CSSファイルを開く"""
        self.css_dir = os.path.join(self.get_script_dirname(), 'css')
        self.current_css = basename
        fn = os.path.join(self.css_dir, self.current_css)
        try:
            with codecs.open(fn, 'r', 'utf-8') as f:
                self.css_data = f.read()
        except IOError, inst:
            sys.stderr.write(str(inst) + "\n")
            self.css_data = ""

    def open_file(self):
        """Markdownファイルを開く"""
        if self.check_saved():
            # 開くファイル名を入力してもらう
            fn = QtGui.QFileDialog.getOpenFileName(self, u"ファイルを開く",
                                                   self.get_last_dir())
            if fn == "":
                # キャンセルされた
                self.statusBar().showMessage("Cancel.")
                return False

            return self.open_file_exec(fn)

    def open_sample_file(self):
        """サンプルファイルを開く"""
        if self.check_saved():
            fn = os.path.join(self.get_script_dirname(), SAMPLE_FNAME)
            return self.open_file_exec(fn)

    def make_new_file(self):
        """ファイルを新規作成"""
        if self.check_saved():
            self.filename = ""
            self.ui.editor_window.clear()
            self.set_saved()

    def open_file_exec(self, fn):
        """ファイルを実際に開く処理"""
        if os.path.isfile(fn):
            # ファイルが存在する
            try:
                with codecs.open(fn, 'r', 'utf-8') as f:
                    s = f.read()
                    self.ui.editor_window.setPlainText(s)
                    self.filename = fn
                    self.statusBar().showMessage("Load " + fn)
                    self.set_saved()
                    self.set_last_dir(self.filename)
                    return True
            except IOError, inst:
                sys.stderr.write(str(inst) + "\n")
                msg = "Can not load " + fn
                self.statusBar().showMessage(msg)

        return False

    def save_file(self):
        """ファイルを保存。
        Trueなら成功。Falseならキャンセルもしくは失敗。"""

        if self.filename == "":
            return self.saveas_file()
        elif os.path.isfile(self.filename):
            self.save_file_exec(self.filename)
            return True
        return False

    def saveas_file(self):
        """ファイルを別名保存。
        現在ファイル名も変更される。"""

        fn = QtGui.QFileDialog.getSaveFileName(self, u"別名で保存",
                                               self.get_last_dir())
        if fn == "":
            self.statusBar().showMessage("Cancel.")
            return False
        self.filename = fn
        self.save_file_exec(self.filename)
        self.set_last_dir(self.filename)
        return True

    def save_file_exec(self, fname):
        """ファイルを実際に保存する処理"""
        s = codecs.open(fname, 'w', 'utf-8')
        s.write(unicode(self.ui.editor_window.toPlainText()))
        s.close()
        self.statusBar().showMessage("Save " + fname)
        self.set_saved()
        if DBG:
            print "Save : [%s]" % fname

    def export_html(self):
        """htmlコードをエクスポートする"""
        f_filter = u"Webページ (*.html);;All files (*.*)"
        fn = QtGui.QFileDialog.getSaveFileName(self, u"htmlをエクスポート",
                                               self.get_last_dir(), f_filter)
        if fn == "":
            self.statusBar().showMessage("Cancel.")
            return False
        s = codecs.open(fn, 'w', 'utf-8')
        s.write(unicode(self.convert_md_to_html()))
        s.close()
        self.statusBar().showMessage("Export " + fn)
        return True

    def chg_text(self):
        """編集ウインドウが変更された時に呼ばれる処理"""
        self.saved = False
        self.store_wdw_title()
        if ONENTER_JOB:
            self.conv_req = 1
        else:
            if self.auto_reload:
                self.reload_html()

    def set_saved(self):
        """編集ウインドウが変更されてないことを記録"""
        self.saved = True
        self.store_wdw_title()

    def chg_position(self):
        """編集ウインドウ内でカーソル位置が変更された時に呼ばれる処理"""
        self.scroll_webview()

    def store_wdw_title(self):
        """ウインドウタイトル文字列を設定"""
        if self.filename == "":
            # まだ何のファイルも開いていない
            self.wdw_title = u"untitled - %s" % WDW_TITLE_DEF
        else:
            # 既に何かファイルを開いている
            self.basename = os.path.basename(str(self.filename))
            self.wdw_title = u"%s - %s" % (self.basename, WDW_TITLE_DEF)

        if self.saved:
            # テキストウインドウは変更されていない
            self.setWindowTitle(self.wdw_title)
        else:
            # テキストウインドウは変更されている
            self.setWindowTitle("* " + self.wdw_title)

    def check_saved(self):
        """ファイルが変更されているなら保存するか問い合わせする。
        Trueなら処理を続けていい。Falseなら今後の処理をキャンセル。"""

        if not self.saved:
            # ファイルは変更されている
            lmsg = u"ファイルが変更されています。保存しますか？"
            kind = (QtGui.QMessageBox.Yes | QtGui.QMessageBox.No |
                    QtGui.QMessageBox.Cancel)
            res = QtGui.QMessageBox.question(self, "Message",
                                             lmsg, kind, QtGui.QMessageBox.No)
            if res == QtGui.QMessageBox.Yes:
                if not self.file_save():
                    return False

            if res == QtGui.QMessageBox.Cancel:
                return False

        return True

    def closeEvent(self, event):
        """アプリを閉じようとした際の処理"""
        if self.check_saved():
            event.accept()
        else:
            event.ignore()

    def get_css_path(self):
        """現在選択中のcssのpathを取得"""
        dname = self.css_dir
        fname = self.current_css
        s = "file:///" + os.path.abspath(os.path.join(dname, fname))
        return s.replace("\\", "/")

    def get_html_data(self, text):
        """HTMLテキストにhtml,head,bodyタグ等を追加して返す"""
        s = self.html_template % (self.css_data, text)
        return s

    def convert_md_to_html(self):
        """編集ウインドウ内のMarkdownをhtmlに変換"""
        self.md_text = unicode(self.ui.editor_window.toPlainText())
        self.html_text = markdown2.markdown(self.md_text)
        self.html_data = self.get_html_data(self.html_text)
        return self.html_data

    def reload_html(self):
        """QWebViewを更新"""
        if not self.converting:
            self.converting = True
            self.load_success = False

            self.ui.my_webview.settings().clearMemoryCaches()
            self.convert_md_to_html()

            # mdファイルのある場所をベースURLとする
            dname = self.get_dirname(os.path.abspath(self.filename))
            uri = "file:///" + dname + "/"

            # QWebView にhtmlテキストを渡す
            self.ui.my_webview.setHtml(self.html_data, QtCore.QUrl(uri))
            ## self.ui.my_webview.show()

            self.converting = False

    def chg_contents_size(self):
        """QWebView内のサイズが変更された際に呼ばれる処理"""

        # ページサイズを取得する
        c_size = self.ui.my_webview.page().mainFrame().contentsSize()
        self.mainframe_w = c_size.width()
        self.mainframe_h = c_size.height()
        ## print "frame w,h=%d,%d" % (self.mainframe_w, self.mainframe_h)

        if False:
            self.mainframe = self.ui.my_webview.page().mainFrame()
            self.mainframe_vw = self.mainframe.geometry().width()
            self.mainframe_vh = self.mainframe.geometry().height()
            print "view w,h=%d,%d" % (self.mainframe_w, self.mainframe_h)

    def load_finished(self):
        """QwebViewのロード終了時に呼ばれる処理"""
        self.load_success = True
        ## self.mainframe.setScrollPosition(self.old_scr_pos)
        ## print "load finished"

        # 編集ウインドウ内カーソル位置によって、
        # スクロールバーの値を変更する
        self.scroll_webview()

    def scroll_page_start(self):
        """QWebViewに対してページ文頭までスクロール"""
        self.mainframe = self.ui.my_webview.page().mainFrame()
        orient = QtCore.Qt.Vertical
        svmin = self.mainframe.scrollBarMinimum(orient)
        self.mainframe.setScrollBarValue(orient, svmin)

    def scroll_page_end(self):
        """QWebViewに対してページ文末までスクロール"""
        self.mainframe = self.ui.my_webview.page().mainFrame()
        orient = QtCore.Qt.Vertical
        svmax = self.mainframe.scrollBarMaximum(orient)
        self.mainframe.setScrollBarValue(orient, svmax)

    def scroll_page_per(self, per):
        """QWebViewに対して指定の割合でスクロール。
        割合は、0～100 を与える。"""
        self.mainframe = self.ui.my_webview.page().mainFrame()
        orient = QtCore.Qt.Vertical
        svmin = self.mainframe.scrollBarMinimum(orient)
        svmax = self.mainframe.scrollBarMaximum(orient)
        v = int(((svmax - svmin) * per / 100) + svmin)
        self.mainframe.setScrollBarValue(orient, v)

    def scroll_webview(self):
        """カーソル位置に合わせてWebViewのスクロール位置を調整"""
        if self.load_success and self.auto_reload:
            self.textEdit = self.ui.editor_window
            c = self.textEdit.textCursor()
            bcnt = self.textEdit.document().blockCount()        # 文書行数
            ncnt = self.textEdit.textCursor().blockNumber()     # 現在の行位置
            if c.atEnd():
                # ページ文末までスクロール
                self.scroll_page_end()
                self.scrl_per = 100
            elif c.atStart():
                # ページ文頭までスクロール
                self.scroll_page_start()
                self.scrl_per = 0
            else:
                # 大味の割合でスクロール
                self.scrl_per = int(ncnt * 100 / (bcnt - 1))
                self.scroll_page_per(self.scrl_per)

    def reload_webview(self):
        """html表示更新ボタンが押された時の処理"""
        self.reload_html()

    def on_enter_frame(self):
        """一定時間毎に呼ばれる処理"""
        if ONENTER_JOB:
            if self.conv_req <= 0:
                # 何もしない
                return
            elif self.conv_req == 1:
                # 1ターン待つ
                self.conv_req += 1
            else:
                # htmlを更新
                self.reload_html()
                self.conv_req = 0

    def chg_auto_reload(self):
        """HTML自動更新CheckBoxの値を反転させる。
        反転後、chg_cb_preview()が自動的に呼ばれる。"""
        cb = self.ui.checkbox_preview
        if cb.checkState() == QtCore.Qt.Checked:
            cb.setCheckState(QtCore.Qt.Unchecked)
        else:
            cb.setCheckState(QtCore.Qt.Checked)

    def chg_cb_preview(self):
        """HTML自動更新CheckBoxの値が変更された際の処理"""
        if self.ui.checkbox_preview.checkState() == QtCore.Qt.Checked:
            self.auto_reload = True
            ## print "Auto Reload On."
        else:
            self.auto_reload = False
            ## print "Auto Reload Off."

    def chg_css(self):
        """css選択ComboBoxが選択された際の処理"""
        idx = self.ui.css_combobox.currentIndex()
        self.load_css(self.css_list[idx])    # CSSファイルを読み込み
        self.reload_html()

    def select_font(self):
        """フォント選択ダイアログを開く"""
        old_font = self.ui.editor_window.currentFont()
        font, ok = QtGui.QFontDialog.getFont(old_font)
        if ok:
            self.ui.editor_window.setFont(font)

    def display_about(self):
        """Aboutダイアログを表示"""
        s = "%s\n%s" % (WDW_TITLE_DEF, __version__)
        QtGui.QMessageBox.information(self, "About", s, QtGui.QMessageBox.Ok)

    def display_help(self):
        """ヘルプをブラウザで表示"""
        uri = os.path.join(self.get_script_dirname(), HELP_FNAME)
        webbrowser.open(uri)    # ブラウザを起動して読み込ませる

    def edit_clear(self):
        """編集ウインドウで全テキストを消去。
        undo不可であることに注意。"""
        kind = (QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        res = QtGui.QMessageBox.question(self, "Message",
                                         MSG_CLEAR, kind, QtGui.QMessageBox.No)
        if res == QtGui.QMessageBox.Yes:
            self.ui.editor_window.clear()

    def ins_h1(self):
        """見出し1を挿入"""
        self.ins_bol("h1")

    def ins_h2(self):
        """見出し2を挿入"""
        self.ins_bol("h2")

    def ins_h3(self):
        """見出し3を挿入"""
        self.ins_bol("h3")

    def ins_h4(self):
        """見出し4を挿入"""
        self.ins_bol("h4")

    def ins_h5(self):
        """見出し5を挿入"""
        self.ins_bol("h5")

    def ins_h6(self):
        """見出し6を挿入"""
        self.ins_bol("h6")

    def ins_ul(self):
        """番号無しリストを挿入"""
        self.ins_bol("ul")

    def ins_ol(self):
        """番号付きリストを挿入"""
        self.ins_bol("ol")

    def ins_cite(self):
        """引用を挿入"""
        self.ins_bol("cite")

    def ins_code_multi(self):
        """コード複数行を挿入"""
        self.ins_bol("pre")

    def ins_hr(self):
        """水平線を挿入"""
        self.ins_bol_and_newline("hr")

    def ins_idurl(self):
        """参照リンク元URLを挿入"""
        self.ins_bol_and_newline("idurl")

    def ins_idlink(self):
        """参照リンクを挿入"""
        self.ins_middle("idlink")

    def ins_link(self):
        """リンクを挿入"""
        self.ins_middle("href")

    def ins_img(self):
        """画像を挿入"""
        self.ins_middle("img")

    def ins_code_word(self):
        """コード断片を挿入"""
        self.ins_put("code")

    def ins_em(self):
        """斜体を挿入"""
        self.ins_put("em")

    def ins_strong(self):
        """強調を挿入"""
        self.ins_put("strong")

    def ins_br(self):
        """改行を挿入"""
        self.ins_and_newline("br")

    def ins_bol(self, kind):
        """行頭にmarkdown用記号を挿入"""
        mark = self.md_dic[kind]
        str = ""
        ol_fg = False
        list_fg = False
        if kind == "ol":
            # 数字付きリストの時だけ処理を変える
            ol_fg = True
            list_fg = True
        elif kind == "ul":
            # 番号無しリストの場合も処理を少し変える
            list_fg = True

        c = self.ui.editor_window.textCursor()
        c.beginEditBlock()                  # undo履歴を制御
        if c.hasSelection():
            # 選択範囲有り
            selstr = c.selectedText()       # 選択範囲の文字列を取得
            lis = selstr.split(u"\u2029")   # パラグラフ区切り？でリストに分割

            if list_fg:
                # リストの時は、挿入前後に改行を入れる
                str += "\n"

            # 1行ごとに記号を追加する
            cnt = 1
            for s in lis:
                if s != "":
                    if ol_fg:
                        # 数字付きリストの場合
                        str += "%d. %s\n" % (cnt, s)
                        cnt += 1
                    else:
                        # 数字付きリストではない場合
                        str += (mark + s + "\n")

            if list_fg:
                str += "\n"

            c.removeSelectedText()          # 選択範囲を削除
        else:
            # 選択範囲無し
            str = mark

        c.movePosition(QtGui.QTextCursor.StartOfLine)   # 行頭に移動
        c.insertText(str)                               # 文字列挿入
        self.ui.editor_window.setTextCursor(c)          # カーソル位置を反映
        c.endEditBlock()                                # undo履歴を制御

    def ins_bol_and_newline(self, kind):
        """行頭にmarkdown用記号と改行を挿入"""
        mark = self.md_dic[kind]
        str = "\n" + mark + "\n"
        c = self.ui.editor_window.textCursor()
        if c.hasSelection():
            c.beginEditBlock()
            c.clearSelection()          # 選択範囲を無しにする
            c.insertText(str)
            self.ui.editor_window.setTextCursor(c)
            c.endEditBlock()
        else:
            self.ui.editor_window.insertPlainText(str)

    def ins_middle(self, kind):
        """行中にmarkdown用記号を挿入"""
        mark = self.md_dic[kind]
        c = self.ui.editor_window.textCursor()
        if c.hasSelection():
            c.beginEditBlock()
            selstr = c.selectedText()   # 選択範囲の文字列を取得
            s = QtCore.QString(mark)    # markdown記号をQStringに変換
            s.replace("Text", selstr)   # 「Text」を選択範囲の文字列で置換
            c.removeSelectedText()      # 選択範囲を削除
            c.insertText(s)             # 文字列を挿入
            self.ui.editor_window.setTextCursor(c)  # カーソル位置を反映
            c.endEditBlock()
        else:
            self.ui.editor_window.insertPlainText(mark)

    def ins_and_newline(self, kind):
        """行中にmarkdown用記号と改行を挿入"""
        mark = self.md_dic[kind]
        c = self.ui.editor_window.textCursor()
        if c.hasSelection():
            c.beginEditBlock()
            selstr = c.selectedText()       # 選択範囲の文字列を取得
            lis = selstr.split(u"\u2029")   # パラグラフ区切り？でリストに分割

            # 1行ごとに記号を追加
            str = ""
            for s in lis:
                if s != "":
                    str += (s + mark + "\n")

            c.removeSelectedText()          # 選択範囲を削除
            c.insertText(str)               # 文字列を挿入
            self.ui.editor_window.setTextCursor(c)  # カーソル位置を反映
            c.endEditBlock()
        else:
            self.ui.editor_window.insertPlainText(mark + "\n")

    def ins_put(self, kind):
        """行中で単語をmarkdown用記号で挟み込む"""
        mark = self.md_dic[kind]
        c = self.ui.editor_window.textCursor()
        if c.hasSelection():
            # 選択範囲有り
            c.beginEditBlock()
            selstr = c.selectedText()    # 選択範囲の文字列を取得
            c.deleteChar()                      # 選択範囲を削除
            c.insertText(mark + selstr + mark)  # 文字列挿入
            self.ui.editor_window.setTextCursor(c)
            c.endEditBlock()
        else:
            # 選択範囲無し
            self.ui.editor_window.insertPlainText(mark + "Text" + mark)

    def duplicate_line(self):
        """行を複製"""
        self.textEdit = self.ui.editor_window
        c = self.textEdit.textCursor()
        if c.hasSelection():
            # 選択範囲有り
            c.beginEditBlock()          # Undo履歴の制御
            s = c.selectedText()        # 選択範囲の文字列を取得

            sel_s = c.selectionStart()  # 選択範囲の開始位置を取得
            sel_e = c.selectionEnd()    # 選択範囲の終了位置を取得

            c.clearSelection()          # 選択範囲を解除
            c.setPosition(sel_e)        # 元選択範囲の終了位置にカーソル移動
            c.insertText(s)             # 文字列挿入

            # 選択状態を復元する。
            # アンカー変更を伴うカーソル移動後に、
            # アンカー変更をしないカーソル移動をして、選択状態にする。
            sel_s = sel_e
            sel_e = c.position()
            c.setPosition(sel_s, QtGui.QTextCursor.MoveAnchor)
            c.setPosition(sel_e, QtGui.QTextCursor.KeepAnchor)

            c.endEditBlock()                # Undo履歴の制御
            self.textEdit.setTextCursor(c)  # QTextEdit上でカーソル位置反映

        else:
            # 選択範囲無し
            qb = c.block()              # QTextBlock を取得
            qs = qb.text()              # QTextBlock内の文字列を取得
            c.beginEditBlock()
            if not c.atBlockStart():
                # Block頭(行頭)にカーソルが無い。
                # (内部的に)カーソルを行頭に移動
                c.movePosition(QtGui.QTextCursor.StartOfBlock)
            c.insertText(qs + "\n")     # Block文字列を挿入
            c.endEditBlock()

            # QTextEdit上ではカーソル位置を反映させてないので、
            # カーソル位置は以前のまま

    def action_test1(self):
        """実験用処理1。自由に書き換えて実験してください。"""
        s = ("abcdefghijklmn\n"
             "opqrstuvwxyz\n"
             "0123456789\n"
             u"新しい朝が来た" "\n"
             u"希望の朝だ" "\n"
             u"喜びに胸を開け" "\n")
        self.ui.editor_window.insertPlainText(s)

    def action_test2(self):
        """実験用処理2。自由に書き換えて実験してください。"""
        self.ins_link()
        pass

    def action_test3(self):
        """実験用処理3。自由に書き換えて実験してください。"""

        # カーソル位置の情報をprint
        res = ""
        self.textEdit = self.ui.editor_window
        c = self.textEdit.textCursor()
        pos = c.position()
        column = c.columnNumber()
        bloackstart = "BlockStart" if c.atBlockStart() else "not BlockStart"
        res = "pos %d , column %d , %s" % (pos, column, bloackstart)
        print res
        qb = c.block()
        print "block length=%d lineCount=%d" % (qb.length(), qb.lineCount())

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    fn = None if len(sys.argv) < 2 else sys.argv[1]
    myapp = StartQT4(fn)
    myapp.show()

    app.exec_()
    ## sys.exit(app.exec_())
