@echo off
setlocal
cd /d "%~dp0"
set GIT="C:\Program Files\Git\bin\git.exe"
set DEFAULT_REMOTE=https://github.com/milesliu2026-ux/FIll-in-Blank.git

echo === Fill In the Blank - push to GitHub ===
echo 默认仓库: %DEFAULT_REMOTE%
echo.

%GIT% status -sb
echo.
set /p REMOTE=GitHub 仓库地址 (直接回车使用默认): 
if "%REMOTE%"=="" set REMOTE=%DEFAULT_REMOTE%

%GIT% remote remove origin 2>nul
%GIT% remote add origin %REMOTE%
%GIT% branch -M main
echo.
echo 正在推送 main 分支（首次可能较慢，资源约 270MB+）...
%GIT% push -u origin main
echo.
if errorlevel 1 (
  echo 推送失败。请确认：1) 已在 GitHub 创建空仓库 2) 已登录 GitHub 凭据
) else (
  echo 推送成功！组员可用 git clone %REMOTE% 协作编辑。
)
pause
