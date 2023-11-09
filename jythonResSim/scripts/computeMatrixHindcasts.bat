set RESSIM_DIR=C:\Local_Software\HEC-ResSim-3.5.0.390
set WORKING_DIR=C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim
cd /D %RESSIM_DIR%
HEC-ResSimHeadless.exe "C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\scripts\computeMatrixHindcastsJython.py"
cd %WORKING_DIR%
