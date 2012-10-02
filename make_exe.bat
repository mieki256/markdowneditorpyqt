@echo.
@echo exeファイルを生成します。
@pause

python setup.py py2exe

@echo.
@echo cssやhelpファイルをコピーします。
@pause

xcopy css dist\css\ /Y
xcopy help dist\help\ /Y
xcopy resource dist\resource\ /Y
