@echo off
setlocal
cd /d "%~dp0"
set GIT="C:\Program Files\Git\bin\git.exe"

echo === Fill In the Blank - push to GitHub ===
echo.

%GIT% status -sb
echo.
set /p REMOTE=GitHub 仓库地址 (例如 https://github.com/用户名/仓库名.git): 
if "%REMOTE%"=="" (
  echo 未输入地址，已取消。
  pause
  exit /b 1
)

%GIT% remote remove origin 2>nul
%GIT% remote add origin %REMOTE%
%GIT% branch -M main
echo.
echo 正在推送 main 分支（首次可能较慢，资源约 500MB+）...
%GIT% push -u origin main
echo.
if errorlevel 1 (
  echo 推送失败。请确认：1) 已在 GitHub 创建空仓库 2) 已登录 GitHub 凭据
) else (
  echo 推送成功！组员可用 git clone %REMOTE% 协作编辑。
)
pause
