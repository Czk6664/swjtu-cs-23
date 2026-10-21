@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Running all STAEformer models (PEMS08)
echo ========================================

set SCRIPT_DIR=%~dp0
set DATA_PATH=%SCRIPT_DIR%..\..\data
set RESULT_DIR=%SCRIPT_DIR%results

cd /d "%SCRIPT_DIR%"

echo Data path: %DATA_PATH%
echo Result dir: %RESULT_DIR%
echo.

set RESUME_FLAG=%1

echo [1/6] Copying training scripts...
copy /Y train_baseline.py "00_Baseline\" >nul 2>&1
copy /Y train.py "01_External_Feature_Fusion\" >nul 2>&1
copy /Y train.py "02_Dynamic_Graph_Learning\" >nul 2>&1
copy /Y train.py "03_Lightweight_Attention\" >nul 2>&1
copy /Y train.py "04_Multi_Scale_Time\" >nul 2>&1
echo Done.

echo.
echo ========================================
echo [2/6] Running STAEformer Baseline
echo ========================================
cd /d "%SCRIPT_DIR%00_Baseline"
if "%RESUME_FLAG%"=="resume" (
    python train_baseline.py --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\baseline_PEMS08_checkpoint.pth"
) else (
    python train_baseline.py --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
)
if errorlevel 1 (
    echo Baseline training failed!
    goto :error
)

echo.
echo ========================================
echo [3/6] Running External Feature Fusion (EFF)
echo ========================================
cd /d "%SCRIPT_DIR%01_External_Feature_Fusion"
if "%RESUME_FLAG%"=="resume" (
    python train.py --model eff --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\eff_PEMS08_checkpoint.pth"
) else (
    python train.py --model eff --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
)
if errorlevel 1 (
    echo EFF training failed!
    goto :error
)

echo.
echo ========================================
echo [4/6] Running Dynamic Graph Learning (DGL)
echo ========================================
cd /d "%SCRIPT_DIR%02_Dynamic_Graph_Learning"
if "%RESUME_FLAG%"=="resume" (
    python train.py --model dgl --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\dgl_PEMS08_checkpoint.pth"
) else (
    python train.py --model dgl --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
)
if errorlevel 1 (
    echo DGL training failed!
    goto :error
)

echo.
echo ========================================
echo [5/6] Running Lightweight Attention (LA)
echo ========================================
cd /d "%SCRIPT_DIR%03_Lightweight_Attention"
if "%RESUME_FLAG%"=="resume" (
    python train.py --model la --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\la_PEMS08_checkpoint.pth"
) else (
    python train.py --model la --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
)
if errorlevel 1 (
    echo LA training failed!
    goto :error
)

echo.
echo ========================================
echo [6/6] Running Multi-Scale Time (MST)
echo ========================================
cd /d "%SCRIPT_DIR%04_Multi_Scale_Time"
if "%RESUME_FLAG%"=="resume" (
    python train.py --model mst --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\mst_PEMS08_checkpoint.pth"
) else (
    python train.py --model mst --dataset PEMS08 --data_path "%DATA_PATH%\PEMS08" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
)
if errorlevel 1 (
    echo MST training failed!
    goto :error
)

echo.
echo ========================================
echo All models training completed!
echo ========================================
echo.
echo Generating comparison plots...
cd /d "%SCRIPT_DIR%"
python generate_plots.py

echo.
echo Done! Results saved to results/ directory
pause
exit /b 0

:error
echo.
echo Training error occurred!
pause
exit /b 1
