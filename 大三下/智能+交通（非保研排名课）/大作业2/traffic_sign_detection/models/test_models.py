"""Quick smoke tests for AutoCBAM and model yaml loading."""
import torch
from ultralytics import YOLO

from models import AutoCBAM, patch_ultralytics


def test_autocbam_auto_init():
    """AutoCBAM should auto-detect channels on first forward."""
    patch_ultralytics()
    x = torch.randn(2, 64, 32, 32)
    m = AutoCBAM()
    y = m(x)
    assert y.shape == x.shape, f"Shape mismatch: {y.shape} != {x.shape}"
    assert m._initialized
    assert m.cbam is not None
    print("PASS: autocbam_auto_init")


def test_autocbam_different_channels():
    """AutoCBAM should work with any channel count."""
    patch_ultralytics()
    for c in [32, 64, 128, 256]:
        x = torch.randn(1, c, 16, 16)
        m = AutoCBAM()
        y = m(x)
        assert y.shape == x.shape
    print("PASS: autocbam_different_channels")


def test_model_yaml_load():
    """All three model yamls should load without error."""
    import os
    os.chdir(r"D:\大三下\智能交通\大作业2\traffic_sign_detection")
    patch_ultralytics()

    for name in [
        "models/yolo11n-cbam.yaml",
        "models/yolo11n-p2.yaml",
        "models/yolo11n-p2-cbam.yaml",
    ]:
        model = YOLO(name)
        params = sum(p.numel() for p in model.model.parameters())
        print(f"  {name}: {params:,} params")
    print("PASS: model_yaml_load")


if __name__ == "__main__":
    test_autocbam_auto_init()
    test_autocbam_different_channels()
    test_model_yaml_load()
