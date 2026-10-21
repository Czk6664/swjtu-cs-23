"""
Focaler-IoU: Improved IoU Loss for Small Object Detection
Paper: arXiv:2401.00945 (2024)

Usage:
    cd traffic_sign_detection
    python experiments/focaler_iou/train_focaler_iou.py --epochs 50 --batch 16
"""

import sys
import argparse
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

FOCALER_M = 0.7


def focaler_iou_weight(iou, m=0.7):
    gamma = 2.0
    w = ((1.0 - iou.clamp(0, 1)) / (1.0 - m + 1e-7)).clamp(0, 5)
    return w.pow(gamma).unsqueeze(-1)


def make_patched_forward(original_forward):
    """Create a patched forward that wraps the original with Focaler-IoU."""
    import torch.nn.functional as F

    def patched_forward(self, *args, **kwargs):
        from ultralytics.utils.metrics import bbox_iou
        from ultralytics.utils.torch_utils import bbox2dist

        # Call original to get iou loss shape, then override
        # Parse args by position (matches original signature)
        if len(args) >= 9:
            pred_dist, pred_bboxes, anchor_points, target_bboxes, target_scores, target_scores_sum, fg_mask, imgsz, stride = args[:9]
        elif len(args) >= 7:
            pred_dist, pred_bboxes, anchor_points, target_bboxes, target_scores, target_scores_sum, fg_mask = args[:7]
            imgsz = kwargs.get('imgsz', None)
            stride = kwargs.get('stride', None)
        else:
            return original_forward(self, *args, **kwargs)

        weight = target_scores.sum(-1)[fg_mask].unsqueeze(-1)
        iou = bbox_iou(pred_bboxes[fg_mask], target_bboxes[fg_mask], xywh=False, CIoU=True)

        # Focaler-IoU weighting
        focaler_w = focaler_iou_weight(iou, m=FOCALER_M)
        loss_iou = ((1.0 - iou) * weight * focaler_w).sum() / target_scores_sum

        # DFL loss (unchanged from original)
        if self.dfl_loss:
            target_ltrb = bbox2dist(anchor_points, target_bboxes, self.dfl_loss.reg_max - 1)
            loss_dfl = self.dfl_loss(pred_dist[fg_mask].view(-1, self.dfl_loss.reg_max), target_ltrb[fg_mask]) * weight
            loss_dfl = loss_dfl.sum() / target_scores_sum
        else:
            target_ltrb = bbox2dist(anchor_points, target_bboxes)
            if imgsz is not None and stride is not None:
                target_ltrb = target_ltrb * stride
                target_ltrb[..., 0::2] /= imgsz[1]
                target_ltrb[..., 1::2] /= imgsz[0]
                pred_dist = pred_dist * stride
                pred_dist[..., 0::2] /= imgsz[1]
                pred_dist[..., 1::2] /= imgsz[0]
            loss_dfl = (F.l1_loss(pred_dist[fg_mask], target_ltrb[fg_mask], reduction="none").mean(-1, keepdim=True) * weight)
            loss_dfl = loss_dfl.sum() / target_scores_sum

        return loss_iou, loss_dfl

    return patched_forward


def apply_patch():
    from ultralytics.utils.loss import BboxLoss
    original = BboxLoss.forward
    BboxLoss.forward = make_patched_forward(original)
    print(f"[Focaler-IoU] Patched BboxLoss (m={FOCALER_M})")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=50)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--imgsz", type=int, default=704)
    p.add_argument("--device", default="0")
    p.add_argument("--data", default=str(ROOT / "configs" / "dataset" / "tt100k.yaml"))
    p.add_argument("--model", default="yolo11n.pt")
    p.add_argument("--focaler-m", type=float, default=0.7)
    p.add_argument("--name", default="yolo11n_focaler_iou_704_e50")
    return p.parse_args()


def main():
    args = parse_args()
    global FOCALER_M
    FOCALER_M = args.focaler_m
    apply_patch()

    from ultralytics import YOLO
    model = YOLO(args.model)
    model.train(
        data=args.data, epochs=args.epochs, imgsz=args.imgsz,
        batch=args.batch, device=args.device, workers=4,
        project=str(ROOT / "runs" / "tt100k"), name=args.name,
        pretrained=True, optimizer="auto", lr0=0.01, lrf=0.01,
        momentum=0.937, weight_decay=0.0005, warmup_epochs=3.0,
        close_mosaic=10, mixup=0.15, cos_lr=True,
    )
    print(f"\n[DONE] Results in runs/tt100k/{args.name}")


if __name__ == "__main__":
    main()
