@echo off
REM =====================================================================
REM  ALPSbox GUI launcher - double-click this file to start
REM
REM  Requires:
REM    - Windows 11 (or Windows 10 21H2+ with WSLg) for the GUI window
REM    - a WSL2 Linux distribution with FSL installed
REM
REM  The launcher finds the WSL distribution automatically. If yours is
REM  not the default one, either make it default:
REM      wsl -s Ubuntu-24.04
REM  or tell this launcher which one to use, once per user:
REM      setx ALPSBOX_WSL_DISTRO Ubuntu-24.04
REM  then open a new window and double-click this file again.
REM =====================================================================
setlocal EnableExtensions
title ALPSbox - DTI-ALPS Toolbox

REM ---- folder of this file, WITHOUT a trailing backslash ----
REM A trailing backslash immediately before a quote is passed on as a
REM literal quote by Windows argument parsing and makes wslpath fail.
set "HERE=%~dp0"
if "%HERE:~-1%"=="\" set "HERE=%HERE:~0,-1%"
cd /d "%HERE%"

echo ============================================================
echo   ALPSbox  -  DTI-ALPS automated processing toolbox
echo ============================================================
echo.

if not exist "%HERE%\run_gui.sh" goto :err_launcher
where wsl.exe >nul 2>&1
if errorlevel 1 goto :err_nowsl

set "WPATH="
set "DISTRO_USED="

REM ---- 1) distribution explicitly requested via environment variable ----
REM Note: the distro name must NOT be quoted on the wsl.exe command line
REM (some WSL versions treat the quotes as part of the name).
if not defined ALPSBOX_WSL_DISTRO goto :try_default
for /f "usebackq tokens=*" %%i in (`wsl.exe -d %ALPSBOX_WSL_DISTRO% -- wslpath -a "%HERE%" 2^>nul`) do set "WPATH=%%i"
if defined WPATH if not "%WPATH:~0,1%"=="/" set "WPATH="
if not defined WPATH goto :err_bad_env
set "DISTRO_USED=%ALPSBOX_WSL_DISTRO%"
goto :resolved

REM ---- 2) the default WSL distribution ----
:try_default
for /f "usebackq tokens=*" %%i in (`wsl.exe -- wslpath -a "%HERE%" 2^>nul`) do set "WPATH=%%i"
if defined WPATH if not "%WPATH:~0,1%"=="/" set "WPATH="
if defined WPATH goto :resolved

REM ---- 3) common distribution names (e.g. Docker Desktop is default) ----
for %%d in (Ubuntu Ubuntu-24.04 Ubuntu-22.04 Ubuntu-20.04 Debian) do call :try_distro %%d
if defined WPATH goto :resolved
goto :err_nodistro

:try_distro
set "WPATH="
for /f "usebackq tokens=*" %%i in (`wsl.exe -d %1 -- wslpath -a "%HERE%" 2^>nul`) do set "WPATH=%%i"
if defined WPATH if not "%WPATH:~0,1%"=="/" set "WPATH="
if defined WPATH set "DISTRO_USED=%1"
exit /b 0

:resolved
if "%WPATH:~-1%"=="/" set "WPATH=%WPATH:~0,-1%"
set "LAUNCHER=%WPATH%/run_gui.sh"

if defined DISTRO_USED goto :distro_named
set "WSL_CMD=wsl.exe"
echo Distro    : default WSL distribution
goto :distro_done

:distro_named
set "WSL_CMD=wsl.exe -d %DISTRO_USED%"
echo Distro    : %DISTRO_USED%

:distro_done
echo Folder    : %HERE%
echo In WSL    : %WPATH%
echo.

%WSL_CMD% -- test -f "%LAUNCHER%" 2>nul
if errorlevel 1 goto :err_launcher_wsl

if defined ALPSBOX_DRY_RUN goto :dry_run

echo Launching. A window should appear within a few seconds.
echo.
echo Keep this console window OPEN while using ALPSbox.
echo Closing it will close the GUI.
echo.

%WSL_CMD% -- bash "%LAUNCHER%"
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" goto :ok
goto :err_run

:ok
echo ALPSbox closed normally.
timeout /t 2 >nul
endlocal
exit /b 0

:dry_run
echo [dry-run] WSL launcher found: %LAUNCHER%
endlocal
exit /b 0

REM ============================ errors ============================
:err_launcher
echo [ERROR] run_gui.sh was not found next to this launcher.
echo         Keep ALPSbox-GUI.bat and run_gui.sh in the same folder.
echo.
pause
exit /b 3

:err_launcher_wsl
echo [ERROR] run_gui.sh was not found inside WSL:
echo         %LAUNCHER%
echo         Keep this .bat file next to run_gui.sh in the ALPSbox folder.
echo.
pause
exit /b 3

:err_nowsl
echo [ERROR] wsl.exe not found.
echo         Windows Subsystem for Linux is required.
echo         Install it from an admin PowerShell:
echo             wsl --install -d Ubuntu
echo.
pause
exit /b 1

:err_bad_env
echo [ERROR] Could not use WSL distro "%ALPSBOX_WSL_DISTRO%".
echo         List your distributions:  wsl -l -v
echo         Then set the right name:  setx ALPSBOX_WSL_DISTRO ^<name^>
echo.
pause
exit /b 2

:err_nodistro
echo [ERROR] Could not find an accessible WSL distribution.
echo.
echo   1. List installed distributions:   wsl -l -v
echo   2. If none is installed, run in an admin PowerShell:
echo          wsl --install -d Ubuntu
echo   3. If a distribution exists but is not the default, either:
echo          wsl -s ^<name^>                     make it the default
echo          setx ALPSBOX_WSL_DISTRO ^<name^>    this launcher only
echo   4. Check that FSL is installed inside that distribution.
echo      See docs/INSTALL.md, section "Windows + WSL".
echo.
pause
exit /b 2

:err_run
echo [ERROR] Launcher returned code %RC%
echo.
echo Possible reasons:
echo   1. WSLg is unavailable, so the GUI window cannot be shown.
echo      Test:  wsl -- echo $DISPLAY
echo      Fix:   use Windows 11, or run the CLI instead:  alpsbox --help
echo   2. FSL is not installed or not found inside WSL.
echo      Fix:   source $FSLDIR/etc/fslconf/fsl.sh, then  alpsbox check
echo   3. Python tkinter is missing:
echo      Fix:   sudo apt install -y python3-tk
echo   4. Log:   ~/.alpsbox/gui.log  inside WSL
echo.
echo ---- last 30 lines of log ----
%WSL_CMD% -- bash -c "tail -30 ~/.alpsbox/gui.log 2>/dev/null"
echo -----------------------------
echo.
pause
endlocal
exit /b %RC%
