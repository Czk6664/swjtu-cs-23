@echo off
chcp 65001
setlocal EnableDelayedExpansion

echo ========================================
echo 运行 STAEformer 基线模型
echo ========================================

cd /d "%~dp0"
copy /Y ..\train_baseline.py .\train_baseline.py >nul 2>&1

python train_baseline.py --dataset PEMS08 --epochs 200 --batch_size 16 --lr 0.001 --output_dir ..\results

if errorlevel 1 (
    echo 基线模型训练失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 基线模型训练完成！
echo ========================================
echo.
echo 结果已保存到 ..\results\ 目录
pause
