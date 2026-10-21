"""
运行所有模型并生成对比图表
"""

import os
import sys
import json
import subprocess
import time

def run_command(cmd, description):
    print("\n" + "=" * 60)
    print(f"运行: {description}")
    print("=" * 60)
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"ERROR: {description} 运行失败！")
        return False
    print(f"SUCCESS: {description} 完成")
    return True

def main():
    base_path = os.path.dirname(os.path.abspath(__file__))
    dataset = "PEMS08"
    results_dir = os.path.join(base_path, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    models = [
        ("baseline", "STAEformer 基线模型", "python train_baseline.py --dataset {} --epochs 200 --batch_size 16 --lr 0.001".format(dataset)),
        ("eff", "外部特征融合 (EFF)", "python train.py --model eff --dataset {} --epochs 200 --batch_size 16 --lr 0.001".format(dataset)),
        ("dgl", "动态图学习 (DGL)", "python train.py --model dgl --dataset {} --epochs 200 --batch_size 16 --lr 0.001".format(dataset)),
        ("la", "轻量化注意力 (LA)", "python train.py --model la --dataset {} --epochs 200 --batch_size 16 --lr 0.001".format(dataset)),
        ("mst", "多尺度时间建模 (MST)", "python train.py --model mst --dataset {} --epochs 200 --batch_size 16 --lr 0.001".format(dataset)),
    ]
    
    print("\n" + "#" * 60)
    print("# STAEformer 改进模型实验")
    print("# 数据集: {}".format(dataset))
    print("#" * 60)
    
    for model_id, model_name, cmd in models:
        success = run_command(cmd, model_name)
        if not success:
            print(f"Warning: {model_name} 运行失败，继续下一个模型")
    
    print("\n" + "#" * 60)
    print("# 所有模型训练完成！")
    print("#" * 60)
    
    generate_plots(results_dir, dataset)

def generate_plots(results_dir, dataset):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        print("请安装 matplotlib: pip install matplotlib")
        return
    
    model_names = {
        'baseline': 'STAEformer',
        'eff': 'EFF',
        'dgl': 'DGL',
        'la': 'LA',
        'mst': 'MST'
    }
    
    results = {}
    for model_id, model_name in model_names.items():
        result_file = os.path.join(results_dir, f"{model_id}_{dataset}_results.json")
        if os.path.exists(result_file):
            with open(result_file, 'r', encoding='utf-8') as f:
                results[model_id] = json.load(f)
        else:
            print(f"Warning: {result_file} not found")
    
    if not results:
        print("No results found to plot!")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'STAEformer Models Comparison - {dataset}', fontsize=14, fontweight='bold')
    
    metrics = ['mae', 'rmse', 'mape']
    titles = ['MAE (Lower is Better)', 'RMSE (Lower is Better)', 'MAPE % (Lower is Better)']
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
    
    for ax, metric, title in zip(axes, metrics, titles):
        model_ids = list(results.keys())
        values = [results[m]['test_result'][metric] for m in model_ids]
        labels = [model_names[m] for m in model_ids]
        
        bars = ax.bar(labels, values, color=colors[:len(values)])
        ax.set_title(title, fontsize=11)
        ax.set_ylabel(metric.upper())
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                   f'{val:.4f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plot_path = os.path.join(results_dir, f"comparison_{dataset}.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"\nComparison plot saved to: {plot_path}")
    
    summary_file = os.path.join(results_dir, f"summary_{dataset}.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("STAEformer Models Comparison Summary\n")
        f.write(f"Dataset: {dataset}\n")
        f.write("=" * 70 + "\n\n")
        
        header = f"{'Model':<20} {'MAE':<12} {'RMSE':<12} {'MAPE':<12}\n"
        f.write(header)
        f.write("-" * 70 + "\n")
        
        for model_id in ['baseline', 'eff', 'dgl', 'la', 'mst']:
            if model_id in results:
                r = results[model_id]
                name = model_names[model_id]
                mae = r['test_result']['mae']
                rmse = r['test_result']['rmse']
                mape = r['test_result']['mape']
                f.write(f"{name:<20} {mae:<12.5f} {rmse:<12.5f} {mape:<12.5f}\n")
        
        f.write("-" * 70 + "\n")
        f.write("\nPlots saved to: comparison_{}.png\n".format(dataset))
    
    print(f"Summary saved to: {summary_file}")
    print("\n" + "=" * 50)
    print("FINAL COMPARISON RESULTS")
    print("=" * 50)
    print(header)
    print("-" * 70)
    for model_id in ['baseline', 'eff', 'dgl', 'la', 'mst']:
        if model_id in results:
            r = results[model_id]
            name = model_names[model_id]
            mae = r['test_result']['mae']
            rmse = r['test_result']['rmse']
            mape = r['test_result']['mape']
            print(f"{name:<20} {mae:<12.5f} {rmse:<12.5f} {mape:<12.5f}")
    print("=" * 50)

if __name__ == "__main__":
    main()
