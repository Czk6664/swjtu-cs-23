@echo off
echo ============================================
echo STAEformer Environment Setup
echo ============================================
echo.

REM Check Python version
python --version
echo.

REM Check pip version
pip --version
echo.

REM Check CUDA availability
echo Checking CUDA...
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
echo.

echo ============================================
echo Installing dependencies...
echo ============================================
echo.

REM Install PyTorch with CUDA 11.8 (most compatible)
echo Installing PyTorch with CUDA 11.8...
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
echo.

REM Install other dependencies
echo Installing other dependencies...
pip install numpy pandas matplotlib torchinfo pyyaml scikit-learn tqdm scipy seaborn
echo.

echo ============================================
echo Verifying installation...
echo ============================================
python -c "import torch; import numpy; import pandas; import matplotlib; print('All packages installed successfully!')"
echo.

echo ============================================
echo Environment setup complete!
echo ============================================
pause
