@echo.
@echo exe�t�@�C���𐶐����܂��B
@pause

python setup.py py2exe

@echo.
@echo css��help�t�@�C�����R�s�[���܂��B
@pause

xcopy css dist\css\ /Y
xcopy help dist\help\ /Y
xcopy resource dist\resource\ /Y
