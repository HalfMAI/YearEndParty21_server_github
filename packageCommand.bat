setlocal
cd /d %~dp0
.\yep21ServerPackage\Scripts\activate
pip install -r .\requirements.txt
pyinstaller --clean --onefile --hidden-import=main --name=yep21Server_release .\main.py
.\yep21ServerPackage\Scripts\deactivate