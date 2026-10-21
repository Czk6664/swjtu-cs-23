"""
STAEformer 基线模型训练脚本
"""

import argparse
import numpy as np
import os
import torch
import torch.nn as nn
import datetime
import time
import json
import sys
import copy

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.utils import (
    MaskedMAELoss,
    print_log,
    seed_everything,
    set_cpu_num,
    StandardScaler,
)
from lib.metrics import RMSE_MAE_MAPE
from lib.data_prepare import get_dataloaders_from_index_data


def eval_model(model, valset_loader, criterion, device, scaler):
    model.eval()
    batch_loss_list = []
    for x_batch, y_batch in valset_loader:
        x_batch = x_batch.to(device)
        y_batch = y_batch.to(device)
        out_batch = model(x_batch)
        out_batch = scaler.inverse_transform(out_batch)
        loss = criterion(out_batch, y_batch)
        batch_loss_list.append(loss.item())
    return np.mean(batch_loss_list)


def predict(model, loader, device, scaler):
    model.eval()
    y = []
    out = []
    for x_batch, y_batch in loader:
        x_batch = x_batch.to(device)
        y_batch = y_batch.to(device)
        out_batch = model(x_batch)
        out_batch = scaler.inverse_transform(out_batch)
        out_batch = out_batch.detach().cpu().numpy()
        y_batch = y_batch.detach().cpu().numpy()
        out.append(out_batch)
        y.append(y_batch)
    out = np.vstack(out).squeeze()
    y = np.vstack(y).squeeze()
    return y, out


def train_one_epoch(model, trainset_loader, optimizer, scheduler, criterion, device, scaler):
    model.train()
    batch_loss_list = []
    for x_batch, y_batch in trainset_loader:
        x_batch = x_batch.to(device)
        y_batch = y_batch.to(device)
        out_batch = model(x_batch)
        out_batch = scaler.inverse_transform(out_batch)
        loss = criterion(out_batch, y_batch)
        batch_loss_list.append(loss.item())
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    epoch_loss = np.mean(batch_loss_list)
    scheduler.step()
    return epoch_loss


def train(
    model, trainset_loader, valset_loader,
    optimizer, scheduler, criterion, device, scaler,
    max_epochs=200, early_stop=30, verbose=1, log=None,
    checkpoint_path=None, start_epoch=0,
):
    model = model.to(device)
    wait = 0
    min_val_loss = np.inf
    best_epoch = start_epoch
    best_state_dict = None
    train_loss_list = []
    val_loss_list = []

    for epoch in range(start_epoch, max_epochs):
        train_loss = train_one_epoch(
            model, trainset_loader, optimizer, scheduler, criterion, device, scaler
        )
        train_loss_list.append(train_loss)
        val_loss = eval_model(model, valset_loader, criterion, device, scaler)
        val_loss_list.append(val_loss)

        if (epoch + 1) % verbose == 0:
            print_log(
                datetime.datetime.now(), "Epoch", epoch + 1,
                "\tTrain Loss = %.5f" % train_loss,
                "Val Loss = %.5f" % val_loss,
                log=log,
            )

        if val_loss < min_val_loss:
            wait = 0
            min_val_loss = val_loss
            best_epoch = epoch
            best_state_dict = copy.deepcopy(model.state_dict())
            torch.save({
                'epoch': epoch,
                'model_state_dict': best_state_dict,
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'min_val_loss': min_val_loss,
                'wait': wait,
                'train_loss_list': train_loss_list,
                'val_loss_list': val_loss_list,
            }, checkpoint_path)
        else:
            wait += 1
            if wait >= early_stop:
                break

    model.load_state_dict(best_state_dict)
    train_rmse, train_mae, train_mape = RMSE_MAE_MAPE(*predict(model, trainset_loader, device, scaler))
    val_rmse, val_mae, val_mape = RMSE_MAE_MAPE(*predict(model, valset_loader, device, scaler))

    return {
        'best_epoch': best_epoch + 1,
        'train_loss': train_loss_list[best_epoch],
        'val_loss': val_loss_list[best_epoch],
        'train_rmse': train_rmse,
        'train_mae': train_mae,
        'train_mape': train_mape,
        'val_rmse': val_rmse,
        'val_mae': val_mae,
        'val_mape': val_mape,
        'train_loss_list': train_loss_list[:best_epoch + 1],
        'val_loss_list': val_loss_list[:best_epoch + 1],
    }, model


def test_model(model, testset_loader, device, scaler, log=None):
    model.eval()
    print_log("--------- Test ---------", log=log)
    start = time.time()
    y_true, y_pred = predict(model, testset_loader, device, scaler)
    end = time.time()
    
    rmse_all, mae_all, mape_all = RMSE_MAE_MAPE(y_true, y_pred)
    out_str = "All Steps RMSE = %.5f, MAE = %.5f, MAPE = %.5f\n" % (
        rmse_all, mae_all, mape_all,
    )
    
    out_steps = y_pred.shape[1] if len(y_pred.shape) > 2 else 1
    step_results = []
    if len(y_pred.shape) > 2:
        for i in range(out_steps):
            rmse, mae, mape = RMSE_MAE_MAPE(y_true[:, i, :], y_pred[:, i, :])
            out_str += "Step %d RMSE = %.5f, MAE = %.5f, MAPE = %.5f\n" % (
                i + 1, rmse, mae, mape,
            )
            step_results.append({'step': i + 1, 'rmse': rmse, 'mae': mae, 'mape': mape})
    
    print_log(out_str, log=log, end="")
    print_log("Inference time: %.2f s" % (end - start), log=log)
    
    return {
        'rmse': rmse_all,
        'mae': mae_all,
        'mape': mape_all,
        'inference_time': end - start,
        'step_results': step_results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=str, default="PEMS08", help="Dataset name")
    parser.add_argument("--data_path", type=str, default=None, help="Data path")
    parser.add_argument("--gpu", type=int, default=0, help="GPU ID")
    parser.add_argument("--epochs", type=int, default=200, help="Max epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--early_stop", type=int, default=30, help="Early stop patience")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory")
    parser.add_argument("--resume", type=str, default=None, help="Resume from checkpoint path")
    args = parser.parse_args()
    
    seed_everything(42)
    set_cpu_num(1)
    
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    
    dataset = args.dataset.upper()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(script_dir)
    
    if args.data_path is None:
        data_path = os.path.join(base_path, "data", dataset)
        if not os.path.exists(data_path):
            data_path = os.path.join(os.path.dirname(base_path), "data", dataset)
    else:
        data_path = args.data_path
    
    if args.output_dir is None:
        result_dir = os.path.join(base_path, "results")
        if not os.path.exists(os.path.dirname(os.path.join(base_path, "data"))):
            result_dir = os.path.join(os.path.dirname(base_path), "results")
    else:
        result_dir = args.output_dir
    os.makedirs(result_dir, exist_ok=True)
    
    log_path = os.path.join(result_dir, f"baseline_{dataset}_train.log")
    mode = "a" if args.resume else "w"
    log = open(log_path, mode, encoding='utf-8')
    
    print_log("=" * 60, log=log)
    print_log(f"Model: STAEformer (Baseline)", log=log)
    print_log(f"Dataset: {dataset}", log=log)
    print_log("=" * 60, log=log)
    
    model_configs = {
        'PEMS08': {'num_nodes': 170, 'in_steps': 12, 'out_steps': 12},
        'PEMS04': {'num_nodes': 307, 'in_steps': 12, 'out_steps': 12},
        'PEMS07': {'num_nodes': 883, 'in_steps': 12, 'out_steps': 12},
        'METRLA': {'num_nodes': 207, 'in_steps': 12, 'out_steps': 12},
        'PEMSBAY': {'num_nodes': 325, 'in_steps': 12, 'out_steps': 12},
    }
    
    if dataset not in model_configs:
        raise ValueError(f"Unknown dataset: {dataset}")
    
    model_args = model_configs[dataset].copy()
    model_args.update({
        'input_embedding_dim': 24,
        'tod_embedding_dim': 24,
        'dow_embedding_dim': 24,
        'adaptive_embedding_dim': 80,
        'feed_forward_dim': 256,
        'num_heads': 4,
        'num_layers': 3,
        'dropout': 0.1,
    })
    
    print_log(f"Model Args: {json.dumps(model_args, indent=2)}", log=log)
    print_log(log=log)
    
    print_log("Loading dataset...", log=log)
    from models.base_staeformer import STAEformer
    trainset_loader, valset_loader, testset_loader, scaler = get_dataloaders_from_index_data(
        data_path, tod=True, dow=True, batch_size=args.batch_size, log=log
    )
    print_log(log=log)
    
    print_log("Initializing model...", log=log)
    model = STAEformer(**model_args)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print_log(f"Total parameters: {total_params:,}", log=log)
    print_log(f"Trainable parameters: {trainable_params:,}", log=log)
    print_log(log=log)
    
    criterion = nn.HuberLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(
        optimizer, milestones=[20, 30], gamma=0.1
    )
    
    checkpoint_path = os.path.join(result_dir, f"baseline_{dataset}_checkpoint.pth")
    start_epoch = 0
    
    if args.resume and os.path.exists(args.resume):
        print_log(f"Loading checkpoint from: {args.resume}", log=log)
        checkpoint = torch.load(args.resume, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        min_val_loss = checkpoint['min_val_loss']
        print_log(f"Resumed from epoch {start_epoch}, val_loss={min_val_loss:.5f}", log=log)
        print_log(log=log)
    elif os.path.exists(checkpoint_path):
        print_log(f"Found existing checkpoint: {checkpoint_path}", log=log)
        print_log("Use --resume to continue training", log=log)
        print_log(log=log)
    
    print_log("Training...", log=log)
    train_result, model = train(
        model, trainset_loader, valset_loader,
        optimizer, scheduler, criterion, device, scaler,
        max_epochs=args.epochs, early_stop=args.early_stop, verbose=1, log=log,
        checkpoint_path=checkpoint_path, start_epoch=start_epoch,
    )
    print_log(log=log)
    
    print_log("Testing...", log=log)
    test_result = test_model(model, testset_loader, device, scaler, log=log)
    print_log(log=log)
    
    results = {
        'model_name': 'STAEformer (Baseline)',
        'model_args': model_args,
        'total_params': total_params,
        'trainable_params': trainable_params,
        'train_result': train_result,
        'test_result': test_result,
    }
    
    result_json_path = os.path.join(result_dir, f"baseline_{dataset}_results.json")
    with open(result_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print_log(f"Results saved to: {result_json_path}", log=log)
    
    log.close()
    
    print("\n" + "=" * 50)
    print("FINAL RESULTS")
    print("=" * 50)
    print(f"Model: STAEformer (Baseline)")
    print(f"Dataset: {dataset}")
    print(f"Test RMSE: {test_result['rmse']:.5f}")
    print(f"Test MAE: {test_result['mae']:.5f}")
    print(f"Test MAPE: {test_result['mape']:.5f}%")
    print("=" * 50)
