:@echo off
setlocal
set RESSIM_DIR=C:\Local_Software\HEC-ResSim-3.5.0.390
set SCRIPT_PY=C:\workspace\git_clones\folsom-hindcast-processing\jythonResSim\RunningResSimHEADLESS\Example1-simple\script.py
set HECLOGS=c:\Temp
@REM set RESSIM_DIR=%1
@REM set SCRIPT_PY=%2
@REM set HECLOGS=%3


cd %RESSIM_DIR%


:------------------------------------------------------:
: memory parameters                                    :
:------------------------------------------------------:
set MEMPARAMS=-ms4M -mx400M

:---------------------------------------------------------------------------------------------:
: File Formatting - AsciiSerializedObject files...                                            :
:   This setting will format the ascii-serialized files so that they can be more easily read. :
:   NOTE: formatting makes these files as much as 30-40% larger than they otherwise would be. :
:         If you remove this option, the next time the file is written, the formatting will   :
:         be removed and the file will be smaller.                                            :
:         These file never get exceedingly big when compared to the output dss files so you   :
:         really won't gain much by changing this setting.
:---------------------------------------------------------------------------------------------:
:set ASCII_FORMATTED= 
set ASCII_FORMATTED=-DAsciiSerializer.formatFile=true

:------------------------------------------------------:
: Video Properties                                     :
:   Uncomment the second line below if you are seeing  :
:   screen glitches while running this app.  This      :
:   problem is especially common under Windows 95/98.  :
:------------------------------------------------------:
set VIDEO_DEFS= 
:set VIDEO_DEFS=-Dsun.java2d.noddraw -Dsun.java2d.d3d=false

:------------------------------------------------------:
: Log Definitions                                      :
: - output to System.out and System.err will go to a   :
:      log file as named in LOGFILE below.             :
: - to stop logging:                                   :
:      comment out the "set LOGFILE_DEF" line below.   :
:------------------------------------------------------:
set LOG_DIR_DEF=-Dlogfile.directory=%HECLOGS%

set LOGFILE_DEF=-DLOGFILE=%HECLOGS%\ResSim.log
set LOG_DEFS= %LOG_DIR_DEF% %LOGFILE_DEF%

:------------------------------------------------------:
: Select which jre to execute:                         :
:  - java.exe opens a DOS background window            :
:  - javaw.exe does not use a DOS window               :
:------------------------------------------------------:
set JAVA="java\bin\java"
: set JAVA="java\jre\1.5\bin\javaw"


:!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!:
:***************************************************************************:
:*                                                                         *:
:*          !!HANDS OFF!!                                                  *:
:*                                                                         *:
:* The variables below are required for proper operation of this program.  *:
:* Do not modify without instruction from HEC or their representative.     *:
:*                                                                         *:
:***************************************************************************:
:!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!:

:-------------------------------------------:
:  program to be run
:-------------------------------------------:
set PROG_NAME="hec.rss.client.RSS"

:-------------------------------------------:
:  Some Directories 
:-------------------------------------------:
set APPEXE=.
set APPHOME=%APPDATA%/HEC/HEC-ResSim/3.5.0.390
set SUP_DIR=config
set PROP_DIR=config\properties
set JNILIB=java
set JARDIR=jar
set SYSJARDIR=jar\sys

:---------------------------------------------------------------------------------------------------------:
: directory holding the login.properties file.  
: (Since this file is essentially user specific, it should write to the user area, not the PROP_DIR area.)
:---------------------------------------------------------------------------------------------------------:
set USER_PROP_DIR="%APPHOME%\properties"
if not exist %USER_PROP_DIR% mkdir %USER_PROP_DIR%
set LOGINPROP_DEF=-Dlogin.properties.path=%USER_PROP_DIR%/login.properties

:-------------------------------------------:
:  System Jars
:-------------------------------------------:
set SYSJARS=%SYSJARDIR%\bbtools.jar
set SYSJARS=%SYSJARDIR%\symbeans.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\com.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\codebase.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\jgraphx.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\jython-standalone-2.7.2.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\flogger-0.3.1.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\flogger-system-backend-0.3.1.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\apache-commons.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\commons-vfs2-2.1.jar;%SYSJARS%
@REM set SYSJARS=%SYSJARDIR%\jythonlib.jar;%SYSJARS%
set SYSJARS=%SYSJARDIR%\jythonUtils.jar;%SYSJARS%

:-------------------------------------------:
:  Application Jars
:-------------------------------------------:
set APPJARS=%JARDIR%\heclib.jar
set APPJARS=%JARDIR%\data.jar;%APPJARS%
set APPJARS=%JARDIR%\font.jar;%APPJARS%
set APPJARS=%JARDIR%\hec.jar;%APPJARS%
set APPJARS=%JARDIR%\images.jar;%APPJARS%
set APPJARS=%JARDIR%\javaDocs.jar;%APPJARS%
set APPJARS=%JARDIR%\msgsystem.jar;%APPJARS%
set APPJARS=%JARDIR%\resprm.jar;%APPJARS%
set APPJARS=%JARDIR%\rma.jar;%APPJARS%
set APPJARS=%JARDIR%\rss.jar;%APPJARS%
set APPJARS=%JARDIR%\hecPlots-v1.1-dev.jar;%APPJARS%
set APPJARS=%JARDIR%\hecMaps-v1.1-dev.jar;%APPJARS%
set APPJARS=%JARDIR%\hecRmi-v1.1-dev.jar;%APPJARS%
set APPJARS=%JARDIR%\hecSecurity-v1.1-dev.jar;%APPJARS%
set APPJARS=%JARDIR%\ensemblePlugin.jar;%APPJARS%
set APPJARS=%JARDIR%\callbackServices.jar;%APPJARS%
set APPJARS=%JARDIR%\hecClientServer-v1.1-dev.jar;%APPJARS%
set APPJARS=%JARDIR%\hecData.jar;%APPJARS%
set APPJARS=%JARDIR%\lookup.jar;%APPJARS%
set APPJARS=%JARDIR%\hec-dssmapvue-dev.jar;%APPJARS%
set APPJARS=%JARDIR%\rma-geojson-1.0.jar;%APPJARS%
@REM set APPJARS=%JARDIR%\lib\jfxrt.jar;%APPJARS%
set JARS=%APPJARS%;%SYSJARS%

:-------------------------------------------:
:  Python Definitions                 
:-------------------------------------------:
set PYTHONPATH_DEF=-Dpython.path=%SYSJARDIR%\jythonLib.jar\lib;%SYSJARDIR%\jythonUtils.jar
set PYTHONHOME_DEF=-Dpython.home="%TEMP%"
set PYTHON_DEFS=%PYTHONPATH_DEF% %PYTHONHOME_DEF%

:-------------------------------------------:
:  Assembling the definitions...
:-------------------------------------------:
set MINUS_DS=-Djava.library.path=lib
set MINUS_DS=%MINUS_DS% -Dproperties.path=%PROP_DIR%
set MINUS_DS=%MINUS_DS% -DCWMS_HOME="%APPHOME%"
set MINUS_DS=%MINUS_DS% -DCWMS_EXE=%APPEXE%
set MINUS_DS=%MINUS_DS% -Djava.security.policy=%SUP_DIR%\java.policy
set MINUS_DS=%MINUS_DS% -DstatePlane.directory=%SUP_DIR%
set MINUS_DS=%MINUS_DS% %LOGINPROP_DEF% %PYTHON_DEFS% %LOG_DEFS% %VIDEO_DEFS% %ASCII_FORMATTED%

:-------------------------------------------:
:  Run the Program...
:-------------------------------------------:
@echo on
cd
%JAVA% %MEMPARAMS% %MINUS_DS% -cp "%JARS%" %PROG_NAME% "%SCRIPT_PY%"
:%JAVA% %MEMPARAMS% %MINUS_DS% -cp "%JARS%" %PROG_NAME%

endlocal
