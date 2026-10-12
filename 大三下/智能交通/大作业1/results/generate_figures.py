"""
生成科研配图 - STAEformer 模型对比
"""

import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager

font_paths = [
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
    'C:/Windows/Fonts/simsun.ttc',
    '/System/Library/Fonts/PingFang.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
]

chinese_font = None
for path in font_paths:
    if os.path.exists(path):
        chinese_font = font_manager.FontProperties(fname=path)
        break

if chinese_font is None:
    chinese_font = font_manager.FontProperties(family='sans-serif')

matplotlib.rcParams['axes.unicode_minus'] = False

RESULTS_DIR = r"D:\大三下\智能交通\results"

MODEL_NAMES = {
    'baseline': 'Baseline',
    'dgl': 'DGL',
    'la': 'LA',
    'mst': 'MST'
}

MODEL_COLORS = {
    'baseline': '#2E86AB',
    'dgl': '#A23B72', 
    'la': '#F18F01',
    'mst': '#C73E1D'
}

DATASETS = ['METRLA', 'PEMS03', 'PEMS04', 'PEMS08', 'PEMSBAY']

CHINESE_DATASETS = {
    'METRLA': 'METRLA',
    'PEMS03': 'PEMS03',
    'PEMS04': 'PEMS04',
    'PEMS08': 'PEMS08',
    'PEMSBAY': 'PEMSBAY'
}

def load_all_results():
    """加载所有结果数据"""
    results = {}
    for dataset in DATASETS:
        results[dataset] = {}
        for model_id in MODEL_NAMES.keys():
            result_file = os.path.join(RESULTS_DIR, f"{model_id}_{dataset}_results.json")
            if os.path.exists(result_file):
                with open(result_file, 'r', encoding='utf-8') as f:
                    results[dataset][model_id] = json.load(f)
    return results

def get_title_font(self):
    return chinese_font

def plot_model_comparison_bar(results):
    """生成模型对比柱状图"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('STAEformer 模型性能对比', fontsize=14, fontweight='bold', y=1.02,
                 fontproperties=chinese_font)
    
    metrics = ['mae', 'rmse', 'mape']
    titles = ['MAE (越低越好)', 'RMSE (越低越好)', 'MAPE % (越低越好)']
    
    x = np.arange(len(DATASETS))
    width = 0.2
    
    for ax, metric, title in zip(axes, metrics, titles):
        for i, (model_id, model_name) in enumerate(MODEL_NAMES.items()):
            values = []
            for dataset in DATASETS:
                if model_id in results[dataset]:
                    values.append(float(results[dataset][model_id]['test_result'][metric]))
                else:
                    values.append(0)
            
            offset = (i - 1.5) * width
            bars = ax.bar(x + offset, values, width, label=model_name, 
                         color=MODEL_COLORS[model_id], edgecolor='white', linewidth=0.5)
        
        ax.set_ylabel(metric.upper(), fontsize=11)
        ax.set_title(title, fontsize=12, fontproperties=chinese_font)
        ax.set_xticks(x)
        ax.set_xticklabels(DATASETS, rotation=0, fontsize=10)
        ax.legend(prop=chinese_font, loc='upper left', fontsize=9)
        ax.set_ylim(0, ax.get_ylim()[1] * 1.15)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig1_model_comparison.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_heatmap(results):
    """生成性能热力图"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle('模型性能热力图', fontsize=14, fontweight='bold', y=1.02,
                 fontproperties=chinese_font)
    
    metrics = ['mae', 'rmse', 'mape']
    titles = ['MAE', 'RMSE', 'MAPE (%)']
    
    for ax, metric, title in zip(axes, metrics, titles):
        data = []
        for dataset in DATASETS:
            row = []
            for model_id in MODEL_NAMES.keys():
                if model_id in results[dataset]:
                    row.append(float(results[dataset][model_id]['test_result'][metric]))
                else:
                    row.append(np.nan)
            data.append(row)
        
        data = np.array(data)
        
        im = ax.imshow(data, cmap='RdYlGn_r', aspect='auto')
        
        ax.set_xticks(np.arange(len(MODEL_NAMES)))
        ax.set_yticks(np.arange(len(DATASETS)))
        ax.set_xticklabels(list(MODEL_NAMES.values()), fontsize=10)
        ax.set_yticklabels(DATASETS, fontsize=10)
        
        for i in range(len(DATASETS)):
            for j in range(len(MODEL_NAMES)):
                text = ax.text(j, i, f'{data[i, j]:.2f}',
                              ha="center", va="center", color="black", fontsize=9)
        
        ax.set_title(title, fontsize=12, fontproperties=chinese_font)
        plt.colorbar(im, ax=ax, shrink=0.8)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig2_heatmap.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_radar_chart(results):
    """生成雷达图"""
    fig, axes = plt.subplots(1, 5, figsize=(18, 4), subplot_kw=dict(polar=True))
    fig.suptitle('各数据集模型性能雷达图', fontsize=14, fontweight='bold', y=1.02,
                 fontproperties=chinese_font)
    
    num_metrics = 3
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]
    
    for idx, dataset in enumerate(DATASETS):
        ax = axes[idx]
        
        for model_id, model_name in MODEL_NAMES.items():
            if model_id in results[dataset]:
                r = results[dataset][model_id]
                rmse = float(r['test_result']['rmse'])
                mae = float(r['test_result']['mae'])
                mape = float(r['test_result']['mape'])
                values = [1/rmse, 1/mae, 1/mape]
                values += values[:1]
                ax.plot(angles, values, 'o-', linewidth=2, label=model_name, 
                       color=MODEL_COLORS[model_id])
                ax.fill(angles, values, alpha=0.25, color=MODEL_COLORS[model_id])
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(['RMSE', 'MAE', 'MAPE'], fontsize=9)
        ax.set_title(dataset, fontsize=12, fontweight='bold', pad=10)
        ax.legend(prop=chinese_font, loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=8)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig3_radar.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_training_curves(results):
    """生成训练曲线对比图"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('模型训练收敛曲线', fontsize=14, fontweight='bold',
                 fontproperties=chinese_font)
    
    datasets_to_plot = ['METRLA', 'PEMS03', 'PEMS04', 'PEMS08']
    
    for idx, dataset in enumerate(datasets_to_plot):
        ax = axes[idx // 2, idx % 2]
        
        for model_id, model_name in MODEL_NAMES.items():
            if model_id in results[dataset]:
                r = results[dataset][model_id]
                val_loss = r['train_result']['val_loss_list']
                epochs = range(1, len(val_loss) + 1)
                ax.plot(epochs, val_loss, '-', linewidth=1.5, 
                       label=model_name, color=MODEL_COLORS[model_id])
        
        ax.set_xlabel('Epoch', fontsize=10)
        ax.set_ylabel('Validation Loss', fontsize=10)
        ax.set_title(f'{dataset}', fontsize=12, fontweight='bold')
        ax.legend(prop=chinese_font, fontsize=9)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig4_training_curves.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_inference_time(results):
    """生成推理时间对比图"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(DATASETS))
    width = 0.2
    
    for i, (model_id, model_name) in enumerate(MODEL_NAMES.items()):
        times = []
        for dataset in DATASETS:
            if model_id in results[dataset]:
                times.append(float(results[dataset][model_id]['test_result']['inference_time']))
            else:
                times.append(0)
        
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, times, width, label=model_name, 
                     color=MODEL_COLORS[model_id], edgecolor='white', linewidth=0.5)
        
        for bar, val in zip(bars, times):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                       f'{val:.1f}', ha='center', va='bottom', fontsize=8)
    
    ax.set_ylabel('推理时间 (秒)', fontsize=11, fontproperties=chinese_font)
    ax.set_title('模型推理时间对比', fontsize=12, fontweight='bold', fontproperties=chinese_font)
    ax.set_xticks(x)
    ax.set_xticklabels(DATASETS, fontsize=10)
    ax.legend(prop=chinese_font, fontsize=10)
    ax.set_ylim(0, ax.get_ylim()[1] * 1.2)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig5_inference_time.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_params_count(results):
    """生成参数量对比图"""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    x = np.arange(len(DATASETS))
    width = 0.2
    
    for i, (model_id, model_name) in enumerate(MODEL_NAMES.items()):
        params = []
        for dataset in DATASETS:
            if model_id in results[dataset]:
                params.append(float(results[dataset][model_id]['total_params']) / 1e6)
            else:
                params.append(0)
        
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, params, width, label=model_name, 
                     color=MODEL_COLORS[model_id], edgecolor='white', linewidth=0.5)
    
    ax.set_ylabel('参数量 (M)', fontsize=11, fontproperties=chinese_font)
    ax.set_title('模型参数量对比', fontsize=12, fontweight='bold', fontproperties=chinese_font)
    ax.set_xticks(x)
    ax.set_xticklabels(DATASETS, fontsize=10)
    ax.legend(prop=chinese_font, fontsize=10)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig6_params.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_step_wise_performance(results):
    """生成逐步预测性能对比图"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.suptitle('不同预测步长的模型性能对比', fontsize=14, fontweight='bold',
                 fontproperties=chinese_font)
    
    datasets_to_plot = ['METRLA', 'PEMS03', 'PEMS04', 'PEMS08', 'PEMSBAY']
    
    for idx, dataset in enumerate(datasets_to_plot):
        ax = axes[idx // 3, idx % 3]
        
        for model_id, model_name in MODEL_NAMES.items():
            if model_id in results[dataset]:
                r = results[dataset][model_id]
                step_results = r['test_result']['step_results']
                steps = [s['step'] for s in step_results]
                rmse = [float(s['rmse']) for s in step_results]
                ax.plot(steps, rmse, '-', linewidth=2, label=model_name, 
                       color=MODEL_COLORS[model_id], marker='o', markersize=4)
        
        ax.set_xlabel('预测步长', fontsize=10, fontproperties=chinese_font)
        ax.set_ylabel('RMSE', fontsize=10)
        ax.set_title(f'{dataset}', fontsize=12, fontweight='bold')
        ax.legend(prop=chinese_font, fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.set_xticks(range(1, 13))
    
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig7_step_wise.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def plot_efficiency_comparison(results):
    """生成效率对比图 (性能/参数量)"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(DATASETS))
    width = 0.2
    
    for i, (model_id, model_name) in enumerate(MODEL_NAMES.items()):
        efficiency = []
        for dataset in DATASETS:
            if model_id in results[dataset]:
                rmse = float(results[dataset][model_id]['test_result']['rmse'])
                params = float(results[dataset][model_id]['total_params']) / 1e6
                eff = params / rmse
                efficiency.append(eff)
            else:
                efficiency.append(0)
        
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, efficiency, width, label=model_name, 
                     color=MODEL_COLORS[model_id], edgecolor='white', linewidth=0.5)
    
    ax.set_ylabel('参数量/RMSE', fontsize=11, fontproperties=chinese_font)
    ax.set_title('模型效率对比 (越低越好)', fontsize=12, fontweight='bold', fontproperties=chinese_font)
    ax.set_xticks(x)
    ax.set_xticklabels(DATASETS, fontsize=10)
    ax.legend(prop=chinese_font, fontsize=10)
    
    plt.tight_layout()
    output_path = os.path.join(RESULTS_DIR, "fig8_efficiency.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Saved: {output_path}")
    plt.close()

def generate_summary_table(results):
    """生成汇总表格"""
    output_path = os.path.join(RESULTS_DIR, "summary_table.txt")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("=" * 100 + "\n")
        f.write("STAEformer 模型性能汇总\n")
        f.write("=" * 100 + "\n\n")
        
        for dataset in DATASETS:
            f.write(f"\n{'='*40}\n")
            f.write(f"数据集: {dataset}\n")
            f.write(f"{'='*40}\n")
            f.write(f"{'模型':<15} {'MAE':>10} {'RMSE':>10} {'MAPE':>10} {'时间(s)':>10} {'参数量':>12}\n")
            f.write("-" * 100 + "\n")
            
            for model_id, model_name in MODEL_NAMES.items():
                if model_id in results[dataset]:
                    r = results[dataset][model_id]
                    mae = float(r['test_result']['mae'])
                    rmse = float(r['test_result']['rmse'])
                    mape = float(r['test_result']['mape'])
                    time = float(r['test_result']['inference_time'])
                    params = float(r['total_params']) / 1e6
                    f.write(f"{model_name:<15} {mae:>10.4f} {rmse:>10.4f} {mape:>10.4f} {time:>10.2f} {params:>10.2f}M\n")
        
        f.write("\n" + "=" * 100 + "\n")
        f.write("各数据集最佳模型 (按RMSE):\n")
        f.write("-" * 100 + "\n")
        
        for dataset in DATASETS:
            best_model = None
            best_rmse = float('inf')
            for model_id, model_name in MODEL_NAMES.items():
                if model_id in results[dataset]:
                    rmse = float(results[dataset][model_id]['test_result']['rmse'])
                    if rmse < best_rmse:
                        best_rmse = rmse
                        best_model = model_name
            f.write(f"{dataset}: {best_model} (RMSE={best_rmse:.4f})\n")
    
    print(f"Saved: {output_path}")

def main():
    print("Loading results...")
    results = load_all_results()
    
    print("\nGenerating figures...")
    plot_model_comparison_bar(results)
    plot_heatmap(results)
    plot_radar_chart(results)
    plot_training_curves(results)
    plot_inference_time(results)
    plot_params_count(results)
    plot_step_wise_performance(results)
    plot_efficiency_comparison(results)
    generate_summary_table(results)
    
    print("\nAll figures generated successfully!")

if __name__ == "__main__":
    main()