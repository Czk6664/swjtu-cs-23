"""
统一训练脚本 - 支持所有优化方法
训练并测试模型，输出完整信息，自动生成结果报告
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
    model,
    trainset_loader,
    valset_loader,
    optimizer,
    scheduler,
    criterion,
    device,
    scaler,
    max_epochs=200,
    early_stop=30,
    verbose=1,
    log=None,
    checkpoint_path=None,
    start_epoch=0,
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
                datetime.datetime.now(),
                "Epoch", epoch + 1,
                "\tTrain Loss = %.5f" % train_loss,
                "Val Loss = %.5f" % val_loss,
                log=log,
            )

        if val_loss < min_val_loss:
            wait = 0
            min_val_loss = val_loss
            best_epoch = epoch
            best_state_dict = copy.deepcopy(model.state_dict())
            if checkpoint_path:
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


def run_experiment(
    model_class,
    model_name,
    model_args,
    data_path,
    device,
    max_epochs=200,
    early_stop=30,
    batch_size=16,
    lr=0.001,
    log=None,
    checkpoint_path=None,
    resume_path=None,
):
    print_log("=" * 60, log=log)
    print_log(f"Model: {model_name}", log=log)
    print_log("=" * 60, log=log)
    print_log(f"Model Args: {json.dumps(model_args, indent=2)}", log=log)
    print_log(log=log)
    
    print_log("Loading dataset...", log=log)
    trainset_loader, valset_loader, testset_loader, scaler = get_dataloaders_from_index_data(
        data_path, tod=True, dow=True, batch_size=batch_size, log=log
    )
    print_log(log=log)
    
    print_log("Initializing model...", log=log)
    model = model_class(**model_args)
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print_log(f"Total parameters: {total_params:,}", log=log)
    print_log(f"Trainable parameters: {trainable_params:,}", log=log)
    print_log(log=log)
    
    criterion = nn.HuberLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.MultiStepLR(
        optimizer, milestones=[20, 30], gamma=0.1
    )
    
    start_epoch = 0
    if resume_path and os.path.exists(resume_path):
        print_log(f"Loading checkpoint from: {resume_path}", log=log)
        checkpoint = torch.load(resume_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        min_val_loss = checkpoint['min_val_loss']
        print_log(f"Resumed from epoch {start_epoch}, val_loss={min_val_loss:.5f}", log=log)
        print_log(log=log)
    elif checkpoint_path and os.path.exists(checkpoint_path):
        print_log(f"Found existing checkpoint: {checkpoint_path}", log=log)
        print_log("Use --resume to continue training", log=log)
        print_log(log=log)
    
    print_log("Training...", log=log)
    train_result, model = train(
        model, trainset_loader, valset_loader,
        optimizer, scheduler, criterion, device, scaler,
        max_epochs=max_epochs, early_stop=early_stop, verbose=5, log=log,
        checkpoint_path=checkpoint_path, start_epoch=start_epoch,
    )
    print_log(log=log)
    
    print_log("Testing...", log=log)
    test_result = test_model(model, testset_loader, device, scaler, log=log)
    print_log(log=log)
    
    return {
        'model_name': model_name,
        'model_args': model_args,
        'total_params': total_params,
        'trainable_params': trainable_params,
        'train_result': train_result,
        'test_result': test_result,
    }


def save_results_to_markdown(results, output_path, dataset_name):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# {results['model_name']} 实验结果\n\n")
        f.write(f"**数据集**: {dataset_name}\n\n")
        f.write(f"**实验时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. 模型配置\n\n")
        f.write("```json\n")
        f.write(json.dumps(results['model_args'], indent=2, ensure_ascii=False))
        f.write("\n```\n\n")
        
        f.write("## 2. 模型参数\n\n")
        f.write(f"- 总参数量: {results['total_params']:,}\n")
        f.write(f"- 可训练参数量: {results['trainable_params']:,}\n\n")
        
        f.write("## 3. 训练结果\n\n")
        train_res = results['train_result']
        f.write(f"- 最佳Epoch: {train_res['best_epoch']}\n")
        f.write(f"- 训练损失: {train_res['train_loss']:.5f}\n")
        f.write(f"- 验证损失: {train_res['val_loss']:.5f}\n")
        f.write(f"- 训练集 RMSE: {train_res['train_rmse']:.5f}\n")
        f.write(f"- 训练集 MAE: {train_res['train_mae']:.5f}\n")
        f.write(f"- 训练集 MAPE: {train_res['train_mape']:.5f}%\n")
        f.write(f"- 验证集 RMSE: {train_res['val_rmse']:.5f}\n")
        f.write(f"- 验证集 MAE: {train_res['val_mae']:.5f}\n")
        f.write(f"- 验证集 MAPE: {train_res['val_mape']:.5f}%\n\n")
        
        f.write("## 4. 测试结果\n\n")
        test_res = results['test_result']
        f.write(f"- **RMSE**: {test_res['rmse']:.5f}\n")
        f.write(f"- **MAE**: {test_res['mae']:.5f}\n")
        f.write(f"- **MAPE**: {test_res['mape']:.5f}%\n")
        f.write(f"- 推理时间: {test_res['inference_time']:.2f}s\n\n")
        
        if test_res['step_results']:
            f.write("### 各时间步结果\n\n")
            f.write("| Step | RMSE | MAE | MAPE |\n")
            f.write("|------|------|-----|------|\n")
            for step_res in test_res['step_results']:
                f.write(f"| {step_res['step']} | {step_res['rmse']:.5f} | {step_res['mae']:.5f} | {step_res['mape']:.5f}% |\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True, help="Model name: eff, dgl, la, mst")
    parser.add_argument("--dataset", type=str, default="PEMS08", help="Dataset name")
    parser.add_argument("--data_path", type=str, default=None, help="Data path")
    parser.add_argument("--gpu", type=int, default=0, help="GPU ID")
    parser.add_argument("--epochs", type=int, default=200, help="Max epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--early_stop", type=int, default=30, help="Early stop patience")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for results")
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
    
    log_path = os.path.join(result_dir, f"{args.model}_{dataset}_train.log")
    mode = "a" if args.resume else "w"
    log = open(log_path, mode, encoding='utf-8')
    
    model_configs = {
        'PEMS08': {'num_nodes': 170, 'in_steps': 12, 'out_steps': 12},
        'PEMS04': {'num_nodes': 307, 'in_steps': 12, 'out_steps': 12},
        'PEMS07': {'num_nodes': 883, 'in_steps': 12, 'out_steps': 12},
        'METRLA': {'num_nodes': 207, 'in_steps': 12, 'out_steps': 12},
        'PEMSBAY': {'num_nodes': 325, 'in_steps': 12, 'out_steps': 12},
    }
    
    if dataset not in model_configs:
        raise ValueError(f"Unknown dataset: {dataset}")
    
    base_config = model_configs[dataset].copy()
    base_config.update({
        'input_embedding_dim': 24,
        'tod_embedding_dim': 24,
        'dow_embedding_dim': 24,
        'adaptive_embedding_dim': 80,
        'feed_forward_dim': 256,
        'num_heads': 4,
        'num_layers': 3,
        'dropout': 0.1,
    })
    
    if args.model == 'eff':
        import sys
        sys.path.insert(0, os.path.join(base_path, "01_External_Feature_Fusion"))
        from model import STAEformer_EFF
        model_class = STAEformer_EFF
        model_name = "STAEformer-EFF (External Feature Fusion)"
        base_config['num_external_features'] = 4
        base_config['external_embedding_dim'] = 32
    elif args.model == 'dgl':
        import sys
        sys.path.insert(0, os.path.join(base_path, "02_Dynamic_Graph_Learning"))
        from model import STAEformer_DGL
        model_class = STAEformer_DGL
        model_name = "STAEformer-DGL (Dynamic Graph Learning)"
        base_config['graph_hidden_dim'] = 64
    elif args.model == 'la':
        import sys
        sys.path.insert(0, os.path.join(base_path, "03_Lightweight_Attention"))
        from model import STAEformer_LA
        model_class = STAEformer_LA
        model_name = "STAEformer-LA (Lightweight Attention)"
        base_config['attention_type'] = 'linear'
        base_config['sparsity_ratio'] = 0.5
    elif args.model == 'mst':
        import sys
        sys.path.insert(0, os.path.join(base_path, "04_Multi_Scale_Time"))
        from model import STAEformer_MST
        model_class = STAEformer_MST
        model_name = "STAEformer-MST (Multi-Scale Time)"
        base_config['multi_scale_dim'] = 32
    else:
        raise ValueError(f"Unknown model: {args.model}")
    
    results = run_experiment(
        model_class=model_class,
        model_name=model_name,
        model_args=base_config,
        data_path=data_path,
        device=device,
        max_epochs=args.epochs,
        early_stop=args.early_stop,
        batch_size=args.batch_size,
        lr=args.lr,
        log=log,
        checkpoint_path=os.path.join(result_dir, f"{args.model}_{dataset}_checkpoint.pth"),
        resume_path=args.resume,
    )
    
    result_md_path = os.path.join(result_dir, f"{args.model}_{dataset}_results.md")
    save_results_to_markdown(results, result_md_path, dataset)
    print_log(f"Results saved to: {result_md_path}", log=log)
    
    log.close()
