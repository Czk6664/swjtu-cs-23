"""
生成模型对比图表
"""

import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np

def generate_plots():
    base_path = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_path, "results")
    dataset = "PEMS08"
    
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
    
    if not results:
        print("No results found to plot!")
        return
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(f'STAEformer Models Comparison - {dataset}', fontsize=14, fontweight='bold')
    
    metrics = ['mae', 'rmse', 'mape']
    titles = ['MAE (Lower is Better)', 'RMSE (Lower is Better)', 'MAPE % (Lower is Better)']
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
    
    model_ids = list(results.keys())
    
    for ax, metric, title in zip(axes, metrics, titles):
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
    print(f"Comparison plot saved to: {plot_path}")
    
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
    generate_plots()
