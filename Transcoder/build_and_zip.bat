@echo off
REM Run python setup.py build
python setup.py build

REM Get the version from setup.py
setlocal enabledelayedexpansion
set filepath=setup.py
set version=

REM Read the setup.py file line by line
for /f "tokens=*" %%i in (%filepath%) do (
    set line=%%i
    REM Check if the line contains the version
    echo !line! | findstr /r /c:"version=.*" >nul
    if !errorlevel! == 0 (
        REM Extract the version value
        for /f "tokens=2 delims==, " %%j in ("!line!") do (
            set version=%%j
            set version=!version:"=!
        )
        goto :endloop
    )
)

:endloop
REM Trim leading and trailing spaces
for /f "tokens=* delims= " %%A in ("%version%") do set version=%%A

REM Define the build directory and zip name
set build_dir=build\exe.win-amd64-3.12
set zip_name=HBJSON_Transcoder_v%version%.zip

REM Check if Compress-Archive is available
powershell -Command "Get-Command Compress-Archive" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    REM Use Compress-Archive if available
    powershell -Command "Compress-Archive -Path '%build_dir%\*' -DestinationPath '%cd%\%zip_name%' -Force"
) else (
    REM Use tar as a fallback
    tar -a -c -f "%zip_name%" -C "%build_dir%" .
)

echo Build and zip completed successfully.
pause
endlocal
