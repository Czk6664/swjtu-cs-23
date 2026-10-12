"""
生成所有模型在所有数据集上的对比图表
"""

import os
import sys
import json
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def generate_plots_all():
    base_path = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_path, "results")
    
    datasets = ["PEMS08", "PEMS04", "PEMS07", "METRLA", "PEMSBAY"]
    model_names = {
        'baseline': 'Baseline',
        'eff': 'EFF',
        'dgl': 'DGL',
        'la': 'LA',
        'mst': 'MST'
    }
    model_ids = ['baseline', 'eff', 'dgl', 'la', 'mst']
    
    all_results = {}
    for dataset in datasets:
        all_results[dataset] = {}
        for model_id in model_ids:
            result_file = os.path.join(results_dir, f"{model_id}_{dataset}_results.json")
            if os.path.exists(result_file):
                with open(result_file, 'r', encoding='utf-8') as f:
                    all_results[dataset][model_id] = json.load(f)
    
    found_datasets = [d for d in datasets if all_results[d]]
    if not found_datasets:
        print("No results found!")
        return
    
    fig = plt.figure(figsize=(20, 16))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
    
    row_labels = ['MAE', 'RMSE', 'MAPE']
    metrics = ['mae', 'rmse', 'mape']
    
    for idx, (metric, row_label) in enumerate(zip(metrics, row_labels)):
        for col_idx, dataset in enumerate(found_datasets):
            ax = plt.subplot(3, len(found_datasets), idx * len(found_datasets) + col_idx + 1)
            
            available_models = [m for m in model_ids if m in all_results[dataset]]
            values = [all_results[dataset][m]['test_result'][metric] for m in available_models]
            labels = [model_names[m] for m in available_models]
            bar_colors = [colors[model_ids.index(m)] for m in available_models]
            
            bars = ax.bar(labels, values, color=bar_colors)
            ax.set_title(f'{dataset} - {row_label}', fontsize=11, fontweight='bold')
            ax.set_ylabel(row_label)
            ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
            
            for bar, val in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{val:.3f}', ha='center', va='bottom', fontsize=8)
            
            ax.grid(axis='y', alpha=0.3)
    
    plt.suptitle('STAEformer Models Comparison Across All Datasets', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    plot_path = os.path.join(results_dir, "comparison_all_datasets.png")
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"Plot saved to: {plot_path}")
    
    summary_file = os.path.join(results_dir, "summary_all_results.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("STAEformer Models Complete Comparison\n")
        f.write("=" * 100 + "\n\n")
        
        for dataset in found_datasets:
            f.write(f"\n{'='*50}\n")
            f.write(f"Dataset: {dataset}\n")
            f.write(f"{'='*50}\n\n")
            
            header = f"{'Model':<15} {'MAE':<12} {'RMSE':<12} {'MAPE':<12} {'Params':<15} {'Time(s)':<10}\n"
            f.write(header)
            f.write("-" * 100 + "\n")
            
            for model_id in model_ids:
                if model_id in all_results[dataset]:
                    r = all_results[dataset][model_id]
                    name = model_names[model_id]
                    mae = r['test_result']['mae']
                    rmse = r['test_result']['rmse']
                    mape = r['test_result']['mape']
                    params = r['total_params']
                    time_val = r['test_result']['inference_time']
                    f.write(f"{name:<15} {mae:<12.5f} {rmse:<12.5f} {mape:<12.5f} {params:<15,} {time_val:<10.2f}\n")
            
            f.write("\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("BEST MODEL PER DATASET (by MAE)\n")
        f.write("=" * 100 + "\n\n")
        
        for dataset in found_datasets:
            best_model = None
            best_mae = float('inf')
            for model_id in model_ids:
                if model_id in all_results[dataset]:
                    mae = all_results[dataset][model_id]['test_result']['mae']
                    if mae < best_mae:
                        best_mae = mae
                        best_model = model_id
            if best_model:
                f.write(f"{dataset}: {model_names[best_model]} (MAE={best_mae:.5f})\n")
    
    print(f"Summary saved to: {summary_file}")
    
    print("\n" + "=" * 80)
    print("COMPLETE RESULTS TABLE")
    print("=" * 80)
    print()
    print(f"{'Dataset':<10} {'Model':<12} {'MAE':<12} {'RMSE':<12} {'MAPE':<12}")
    print("-" * 80)
    for dataset in found_datasets:
        for model_id in model_ids:
            if model_id in all_results[dataset]:
                r = all_results[dataset][model_id]
                name = model_names[model_id]
                mae = r['test_result']['mae']
                rmse = r['test_result']['rmse']
                mape = r['test_result']['mape']
                print(f"{dataset:<10} {name:<12} {mae:<12.5f} {rmse:<12.5f} {mape:<12.5f}")
        print("-" * 80)
    print()
    
    fig2, axes2 = plt.subplots(1, 3, figsize=(18, 6))
    fig2.suptitle('Average Performance Across All Datasets', fontsize=14, fontweight='bold')
    
    avg_results = {model_id: {'mae': [], 'rmse': [], 'mape': []} for model_id in model_ids}
    
    for dataset in found_datasets:
        for model_id in model_ids:
            if model_id in all_results[dataset]:
                avg_results[model_id]['mae'].append(all_results[dataset][model_id]['test_result']['mae'])
                avg_results[model_id]['rmse'].append(all_results[dataset][model_id]['test_result']['rmse'])
                avg_results[model_id]['mape'].append(all_results[dataset][model_id]['test_result']['mape'])
    
    for ax, metric, title in zip(axes2, metrics, ['Average MAE', 'Average RMSE', 'Average MAPE (%)']):
        model_ids_with_data = [m for m in model_ids if avg_results[m][metric]]
        values = [np.mean(avg_results[m][metric]) for m in model_ids_with_data]
        labels = [model_names[m] for m in model_ids_with_data]
        bar_colors = [colors[model_ids.index(m)] for m in model_ids_with_data]
        
        bars = ax.bar(labels, values, color=bar_colors)
        ax.set_title(title, fontsize=12)
        ax.set_ylabel(metric.upper())
        ax.set_xticklabels(labels, rotation=45, ha='right')
        
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                   f'{val:.4f}', ha='center', va='bottom', fontsize=10)
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plot_path2 = os.path.join(results_dir, "comparison_average.png")
    plt.savefig(plot_path2, dpi=150, bbox_inches='tight')
    print(f"Average comparison saved to: {plot_path2}")
    
    fig3, axes3 = plt.subplots(len(found_datasets), 3, figsize=(18, 4 * len(found_datasets)))
    if len(found_datasets) == 1:
        axes3 = axes3.reshape(1, -1)
    
    for row_idx, dataset in enumerate(found_datasets):
        for col_idx, (metric, row_label) in enumerate(zip(metrics, row_labels)):
            ax = axes3[row_idx, col_idx]
            
            steps = range(1, 13)
            for model_id in model_ids:
                if model_id in all_results[dataset]:
                    step_results = all_results[dataset][model_id]['test_result'].get('step_results', [])
                    if step_results:
                        values = [step_results[s]['mae' if metric == 'mae' else metric] for s in range(len(step_results))]
                        ax.plot(steps[:len(values)], values, marker='o', label=model_names[model_id], 
                               color=colors[model_ids.index(model_id)], linewidth=2, markersize=4)
            
            ax.set_xlabel('Forecast Horizon (Steps)')
            ax.set_ylabel(metric.upper())
            ax.set_title(f'{dataset} - {row_label} per Step', fontsize=11)
            ax.legend(loc='upper right', fontsize=8)
            ax.grid(alpha=0.3)
            ax.set_xticks(steps)
    
    plt.tight_layout()
    plot_path3 = os.path.join(results_dir, "comparison_per_step.png")
    plt.savefig(plot_path3, dpi=150, bbox_inches='tight')
    print(f"Per-step comparison saved to: {plot_path3}")
    
    print("\n" + "=" * 50)
    print("ALL PLOTS GENERATED SUCCESSFULLY")
    print("=" * 50)
    print(f"1. {plot_path}")
    print(f"2. {plot_path2}")
    print(f"3. {plot_path3}")
    print(f"4. {summary_file}")

if __name__ == "__main__":
    generate_plots_all()
