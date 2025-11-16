@echo off
chcp 65001 >nul
title Weak Signals App - 仮想環境有効化

echo ========================================
echo   仮想環境を有効化します
echo ========================================
echo.

REM プロジェクトルートに移動
cd /d "%~dp0"

REM 仮想環境の存在確認
if not exist "venv\Scripts\activate.bat" (
    echo [エラー] 仮想環境が見つかりません。
    echo.
    echo まず、setup.batまたはsetup_python311.batを実行して仮想環境を作成してください。
    echo.
    pause
    exit /b 1
)

REM 仮想環境を有効化
echo 仮想環境を有効化中...
call venv\Scripts\activate.bat

echo.
echo ========================================
echo   仮想環境が有効化されました
echo ========================================
echo.
echo Pythonバージョン:
python --version
echo.
echo 仮想環境のパス:
where python
echo.
echo このウィンドウでPythonコマンドを使用できます。
echo 仮想環境を無効化するには、deactivate と入力してください。
echo.
echo このウィンドウを閉じると仮想環境は無効化されます。
echo.

REM コマンドプロンプトを開いたままにする
cmd /k

