@echo off
echo ========================================
echo  TT100K Traffic Sign Detection - Experiments
echo ========================================
echo.

if not exist "data\tt100k_yolo\images\train" (
    echo [ERROR] Dataset not found!
    echo Expected: data\tt100k_yolo\images\train\
    pause
    exit /b 1
)
echo [OK] Dataset found

echo.
echo [1/3] Installing dependencies...
pip install -r requirements.txt -q

echo.
echo [2/3] Training: YOLO11n + CBAM (704, 50 epochs, batch 8)
echo -------------------------------------------------------
python train.py --config configs/experiments/yolo11n_cbam.yaml

echo.
echo [3/3] Training: YOLO11n + P2 + CBAM (704, 50 epochs, batch 8)
echo -------------------------------------------------------
python train.py --config configs/experiments/yolo11n_p2_cbam.yaml

echo.
echo All done! Results in runs/tt100k/
pause
