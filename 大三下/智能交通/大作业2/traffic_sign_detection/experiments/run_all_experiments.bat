@echo off
echo ========================================
echo  TT100K Improvement Experiments
echo  4070 Laptop Optimized
echo ========================================
echo.

cd /d "%~dp0..\.."
echo Root: %cd%
echo.

echo [0/3] Installing dependencies...
pip install -r experiments/requirements.txt -q
pip install sahi -q
echo.

echo [1/3] Focaler-IoU Training (50 epochs)
echo -------------------------------------------------------
python experiments/focaler_iou/train_focaler_iou.py --epochs 50 --batch 16 --imgsz 704 --device 0
echo.

echo [2/3] Gold-YOLO GD Training (50 epochs)
echo -------------------------------------------------------
python experiments/gold_yolo_gd/train_gold_yolo_gd.py --epochs 50 --batch 8 --imgsz 704 --device 0
echo.

echo [3/3] SAHI Inference on best model
echo -------------------------------------------------------
python experiments/sahi/run_sahi.py --weights runs/tt100k/yolo11n_focaler_iou_704_e50/weights/best.pt --source data/tt100k_yolo/images/val
echo.

echo All experiments done!
pause
