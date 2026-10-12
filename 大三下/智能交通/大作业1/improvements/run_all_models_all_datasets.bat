@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Running all models on all datasets
echo ========================================

set SCRIPT_DIR=%~dp0
set DATA_PATH=%SCRIPT_DIR%..\..\data
set RESULT_DIR=%SCRIPT_DIR%results

cd /d "%SCRIPT_DIR%"

echo Data path: %DATA_PATH%
echo Result dir: %RESULT_DIR%
echo.

echo [1/6] Copying training scripts...
copy /Y train_baseline.py "00_Baseline\" >nul 2>&1
copy /Y train.py "01_External_Feature_Fusion\" >nul 2>&1
copy /Y train.py "02_Dynamic_Graph_Learning\" >nul 2>&1
copy /Y train.py "03_Lightweight_Attention\" >nul 2>&1
copy /Y train.py "04_Multi_Scale_Time\" >nul 2>&1
echo Done.
echo.

set RESUME_FLAG=%1

for %%d in (PEMS08 PEMS04 PEMS07 METRLA PEMSBAY) do (
    echo.
    echo ========================================
    echo Dataset: %%d
    echo ========================================
    
    echo.
    echo [Baseline] %%d
    cd /d "%SCRIPT_DIR%00_Baseline"
    if "%RESUME_FLAG%"=="resume" (
        python train_baseline.py --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\baseline_%%d_checkpoint.pth"
    ) else (
        python train_baseline.py --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
    )
    if errorlevel 1 echo Baseline training failed!
    
    echo.
    echo [EFF] %%d
    cd /d "%SCRIPT_DIR%01_External_Feature_Fusion"
    if "%RESUME_FLAG%"=="resume" (
        python train.py --model eff --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\eff_%%d_checkpoint.pth"
    ) else (
        python train.py --model eff --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
    )
    if errorlevel 1 echo EFF training failed!
    
    echo.
    echo [DGL] %%d
    cd /d "%SCRIPT_DIR%02_Dynamic_Graph_Learning"
    if "%RESUME_FLAG%"=="resume" (
        python train.py --model dgl --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\dgl_%%d_checkpoint.pth"
    ) else (
        python train.py --model dgl --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
    )
    if errorlevel 1 echo DGL training failed!
    
    echo.
    echo [LA] %%d
    cd /d "%SCRIPT_DIR%03_Lightweight_Attention"
    if "%RESUME_FLAG%"=="resume" (
        python train.py --model la --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\la_%%d_checkpoint.pth"
    ) else (
        python train.py --model la --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
    )
    if errorlevel 1 echo LA training failed!
    
    echo.
    echo [MST] %%d
    cd /d "%SCRIPT_DIR%04_Multi_Scale_Time"
    if "%RESUME_FLAG%"=="resume" (
        python train.py --model mst --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%" --resume "%RESULT_DIR%\mst_%%d_checkpoint.pth"
    ) else (
        python train.py --model mst --dataset %%d --data_path "%DATA_PATH%\%%d" --epochs 200 --batch_size 16 --lr 0.001 --output_dir "%RESULT_DIR%"
    )
    if errorlevel 1 echo MST training failed!
)

echo.
echo ========================================
echo All training completed!
echo ========================================
echo.
echo Generating comparison plots...
cd /d "%SCRIPT_DIR%"
python generate_plots_all.py

echo.
echo Done! Check results/ directory
pause
