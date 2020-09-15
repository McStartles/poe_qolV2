Compiled with pyinstaller.

Recreate a minimal anaconda (preferred. try miniconda) or virtual environment with the libraries from the included YAML file (environment.yml).
Otherwise the exe file will be larger than necssary because pyinstaller blindly adds everything it finds in the PYTHONPATH.

The CLI command to compile the exe with pyinstaller requires the 'hidden-imports' flag. Use the following command to make it open without a terminal (-w flag) and make it one exe file (--onefile flag):
pyinstaller --hidden-import=pygubu.builder.ttkstdwidgets -w --onefile POE_QOL2.py

You can also use the following during testing, since it is faster compiling:
pyinstaller --hidden-import=pygubu.builder.tkstdwidgets POE_QOL2.py

If editing the source code, there is a DEBUG flag at the top of the script. You can turn it on and some key actions will print out to terminal.

Capitalization might be important in the Setup.ini file, so follow the example. Same with the default_filter.filter file; try not to change the comments for now.