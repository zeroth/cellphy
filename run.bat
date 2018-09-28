set root=C:\ProgramData\Anaconda3
call %root%\Scripts\activate.bat %root%
call conda activate cellphy
call python main.py gui
call deactivate