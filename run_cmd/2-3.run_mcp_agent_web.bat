@echo off
chcp 65001 >nul
set PORT_NUM=8000
FOR /F "tokens=5" %%P IN ('netstat -aon ^| findstr :%PORT_NUM% ^| findstr LISTENING') DO (
    echo Port %PORT_NUM% is in use by process %%P. Terminating...
    taskkill /F /PID %%P
    timeout /t 3 >nul
)
cd .. 
call .venv\Scripts\activate
cd mcp_agents_adk
cmd /c "adk web"
