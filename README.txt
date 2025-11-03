How to run:

Open the folder containing main.py and appts/.


Open a terminal:

Hold Shift, right-click in a blank area of the folder,

Select “Open PowerShell window here”.


Activate the virtual environment by copying and pasting this exact line:

.\.venv\Scripts\Activate.ps1


Run the program:

python main.py


Use the app:

The window will open with the clients list.

Double-click a client to see their appointments.

Everything is saved automatically in the appts/ folder.


**NOTE**

If you see a message about script execution being blocked, copy and paste this into PowerShell:

Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
