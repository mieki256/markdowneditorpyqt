#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python;Encoding: utf8n -*-
#
# py2exeでexe化するための設定？ファイル

from distutils.core import setup
from glob import glob
import os
import sys
import shutil

if sys.platform == 'win32':
    """Windows用"""

    import py2exe

    # 開発環境のパスに合わせて修正すること
    
    WIN32UI_DIR = r"C:\Python27\Lib\site-packages\pythonwin"
    IMAGELIB_DIR = r"C:\Python27\Lib\site-packages\PyQt4\plugins\imageformats"
    
    # MFC dll を追加
    mfcfiles = [os.path.join(WIN32UI_DIR, i) for i in [
        "mfc90.dll", 
        "mfc90u.dll", 
        "mfcm90.dll", 
        "mfcm90u.dll", 
        "Microsoft.VC90.MFC.manifest"]]

    # 任意の画像フォーマットの dll を追加
    imgfiles = [os.path.join(IMAGELIB_DIR, i) for i in [
        "qgif4.dll",
        "qico4.dll",
        "qjpeg4.dll",
        "qmng4.dll",
        "qsvg4.dll",
        "qtiff4.dll",]]
    
    data_files = [
        ("Microsoft.VC90.MFC", mfcfiles), 
        ("imageformats", imgfiles), 
    ]
    
    py2exe_options = {
        "compressed": 1,
        "optimize": 2,
        "bundle_files": 3,
        "includes" : ["sip", "PyQt4", "PyQt4.QtGui", "PyQt4.QtWebKit", "PyQt4.QtNetwork"]
    }
    setup(
        data_files = data_files,
        options={"py2exe" : py2exe_options},
        windows=[{"script" : "markdowneditorpyqt.pyw"}],
        zipfile="zipped.lib",
    )
