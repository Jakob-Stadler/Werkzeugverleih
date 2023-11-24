@echo off
for %%i in (.\tests\scratch\*) do if not "%%~i" == ".\tests\scratch\.gitignore" del "%%~i"
.\venv\Scripts\pytest.exe --cov=werkzeugverleih --cov-report xml:cov.xml --cov-report html:htmlcov --cov-report term-missing
