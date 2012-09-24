#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python;Encoding: utf8n -*-

'''
MarkdownEditorPyQt

Python + PyQt4 + markdown2 で markdownのリアルタイムプレビューを行う。

'''

import sys
import os
from PyQt4 import QtCore, QtGui, QtWebKit
from mywebview import Ui_MyWebView
import codecs
import markdown2
import glob
import csv


__version__ = '0.0.1'
WDW_TITLE_DEF = "MarkdownEditorPyQt"

DBG = False

# 編集するたび逐一HTMLを更新せず、一定時間毎に更新するならTrueに
ONENTER_JOB = False

# html,markdownのテンプレートファイル名
TEMPLETE_HTML_FNAME = "templete.html"
TEMPLETE_MD_FNAME = "templete_markdown.csv"

# htmlの雛形。%s には、css部分、html本文が入る。
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
                   "idlink": "[Text] [ID]\n[ID]: URL \"Opt Title\"",
                   "img": '![Alt Text](/path/to/img.jpg "Opt Title")'}


class StartQT4(QtGui.QMainWindow):

    def __init__(self, parent=None):
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

        self.filename = ""
        self.basename = ""
        self.last_dir = ""
        self.wdw_title = WDW_TITLE_DEF
        self.html_data = self.get_html_data("")
        self.converting = False
        self.count = 0
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

        # メニューやボタン等に動作を割り当てる
        self.ui.action_open.triggered.connect(self.open_file)
        self.ui.action_save.triggered.connect(self.save_file)
        self.ui.action_saveas.triggered.connect(self.saveas_file)
        self.ui.action_export_html.triggered.connect(self.export_html)
        self.ui.action_exit.triggered.connect(self.close)

        self.ui.action_html_reload.triggered.connect(self.reload_webview)
        self.ui.action_font.triggered.connect(self.select_font)
        self.ui.action_preview_set.triggered.connect(self.chg_auto_reload)

        self.ui.action_about.triggered.connect(self.display_about)

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
        self.ui.action_ins_link.triggered.connect(self.ins_link)
        self.ui.action_ins_image.triggered.connect(self.ins_img)
        self.ui.action_ins_code_word.triggered.connect(self.ins_code_word)
        self.ui.action_ins_em.triggered.connect(self.ins_em)
        self.ui.action_ins_strong.triggered.connect(self.ins_strong)
        self.ui.action_ins_br.triggered.connect(self.ins_br)

        self.ui.editor_window.textChanged.connect(self.chg_text)
        self.ui.css_combobox.activated.connect(self.chg_css)
        self.ui.checkbox_preview.stateChanged.connect(self.chg_cb_preview)

        # objectNameを使って自動で動作を割り当てる
        ## QtCore.QMetaObject.connectSlotsByName(self)

        self.statusBar().showMessage('Ready.')

    def get_script_dirname(self):
        """スクリプトファイルのあるフォルダ名を取得"""
        return os.path.dirname(__file__)

    def get_last_dir(self):
        """最後にアクセスしたフォルダ名を取得"""
        if self.last_dir == "":
            return os.path.expanduser("~")
        else:
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
        """ファイルを開く"""
        if self.check_saved():
            # 開くファイル名を入力してもらう
            fn = QtGui.QFileDialog.getOpenFileName(self, u"ファイルを開く",
                                                   self.get_last_dir())
            self.filename = fn
            if self.filename == "":
                # キャンセルされた
                self.statusBar().showMessage("Cancel.")
                return False

            if os.path.isfile(self.filename):
                # ファイルが存在する
                try:
                    with codecs.open(self.filename, 'r', 'utf-8') as f:
                        s = f.read()
                        self.ui.editor_window.setPlainText(s)
                        self.statusBar().showMessage("Load " + self.filename)
                        self.set_saved()
                        self.set_last_dir(self.filename)
                except IOError, inst:
                    sys.stderr.write(str(inst) + "\n")
                    msg = "Can not load " + self.filename
                    self.statusBar().showMessage(msg)

    def save_file(self):
        """ファイルを保存する。
        Trueなら成功。Falseならキャンセルもしくは失敗。"""

        if self.filename == "":
            return self.saveas_file()
        elif os.path.isfile(self.filename):
            self.save_file_exec(self.filename)
            return True
        return False

    def saveas_file(self):
        """ファイルを別名保存する。
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
        """ファイルを実際に保存"""
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
        """テキスト修正時に呼ばれる処理"""
        self.saved = False
        self.store_wdw_title()
        if ONENTER_JOB:
            self.conv_req = 1
        else:
            if self.auto_reload:
                self.reload_html()

    def set_saved(self):
        """テキストを修正してないことを記録"""
        self.saved = True
        self.store_wdw_title()

    def store_wdw_title(self):
        """ウインドウタイトル文字列を設定"""
        if self.filename == "":
            # まだ何のファイルも開いていない
            self.wdw_title = u"無題 - %s" % WDW_TITLE_DEF
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
        """HTML文字列を取得する"""
        s = self.html_template % (self.css_data, text)
        return s

    def convert_md_to_html(self):
        """左ウインドウ内のMarkdownをhtmlに変換"""
        self.md_text = unicode(self.ui.editor_window.toPlainText())
        self.html_text = markdown2.markdown(self.md_text)
        self.html_data = self.get_html_data(self.html_text)
        return self.html_data

    def reload_html(self):
        """WebViewを更新"""
        if not self.converting:
            self.converting = True
            self.ui.my_webview.settings().clearMemoryCaches()
            self.convert_md_to_html()
            self.ui.my_webview.setHtml(self.html_data)
            self.ui.my_webview.show()
            self.converting = False

    def reload_webview(self):
        """更新ボタンが押された時の処理"""
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
        """HTML自動更新チェックボックスの値を反転させる"""
        cb = self.ui.checkbox_preview
        if cb.checkState() == QtCore.Qt.Checked:
            cb.setCheckState(QtCore.Qt.Unchecked)
        else:
            cb.setCheckState(QtCore.Qt.Checked)

    def chg_cb_preview(self):
        """HTML自動更新チェックボックスの値が変わったら呼ばれる処理"""
        if self.ui.checkbox_preview.checkState() == QtCore.Qt.Checked:
            self.auto_reload = True
            ## print "Auto Reload On."
        else:
            self.auto_reload = False
            ## print "Auto Reload Off."

    def chg_css(self):
        """cssを選択し直し"""
        idx = self.ui.css_combobox.currentIndex()
        self.load_css(self.css_list[idx])
        self.reload_html()

    def select_font(self):
        """フォントを選択"""
        old_font = self.ui.editor_window.currentFont()
        font, ok = QtGui.QFontDialog.getFont(old_font)
        if ok:
            self.ui.editor_window.setFont(font)

    def display_about(self):
        """Aboutダイアログを表示"""
        s = "%s\n%s" % (WDW_TITLE_DEF, __version__)
        QtGui.QMessageBox.information(self, "About", s, QtGui.QMessageBox.Ok)

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

    def ins_idlink(self):
        """IDリンクを挿入"""
        self.ins_bol_and_newline("idlink")

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
        self.ui.editor_window.insertPlainText(self.md_dic[kind])

    def ins_bol_and_newline(self, kind):
        """行頭にmarkdown用記号と改行を挿入"""
        self.ui.editor_window.insertPlainText(self.md_dic[kind] + "\n")

    def ins_middle(self, kind):
        """行中にmarkdown用記号を挿入"""
        self.ui.editor_window.insertPlainText(self.md_dic[kind])

    def ins_and_newline(self, kind):
        """行中にmarkdown用記号と改行を挿入"""
        self.ui.editor_window.insertPlainText(self.md_dic[kind] + "\n")

    def ins_put(self, kind):
        """行中で単語をmarkdown用記号で挟み込む"""
        mark = self.md_dic[kind]
        s = mark + "Text" + mark
        self.ui.editor_window.insertPlainText(s)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    myapp = StartQT4()
    myapp.show()

    app.exec_()
    ## sys.exit(app.exec_())
