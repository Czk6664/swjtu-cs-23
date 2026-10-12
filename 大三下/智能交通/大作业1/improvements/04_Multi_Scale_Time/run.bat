@echo off
chcp 65001
echo ========================================
echo 运行 STAEformer-MST (多尺度时间建模)
echo ========================================

cd /d "%~dp0"
copy /Y ..\train.py .\train.py >nul 2>&1

python train.py --model mst --dataset PEMS08 --epochs 200 --batch_size 16 --lr 0.001 --output_dir ..\results

echo.
echo 训练完成！结果已保存到 ..\results\ 目录
pause
