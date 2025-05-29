import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
from pathlib import Path

# 设置支持中文的字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决坐标轴负号显示问题

def read_tiff(file_path):
    """读取 TIFF 图像并返回数据和元数据"""
    try:
        with rasterio.open(file_path) as src:
            data = src.read(1)
            meta = src.meta
            return data, meta
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None, None

def preprocess_data(observed, predicted):
    """预处理两个数据集，处理无效值并裁剪范围"""
    # 替换无效值（NoData 值、inf、NaN）为 NaN 而不是 0
    observed = np.where(np.isnan(observed) | np.isinf(observed), np.nan, observed)
    predicted = np.where(np.isnan(predicted) | np.isinf(predicted), np.nan, predicted)
    
    # 限制数据范围，防止极端值导致溢出
    observed = np.clip(observed, -10, 10)
    predicted = np.clip(predicted, -10, 10)
    
    # 创建 mask，筛选出两幅图像中都存在有效值的像素
    mask = ~np.isnan(observed) & ~np.isnan(predicted)
    
    return observed, predicted, mask

def calculate_metrics(observed, predicted, mask):
    """计算各种评价指标"""
    # 获取有效数据
    obs_valid = observed[mask]
    pred_valid = predicted[mask]
    
    # 计算误差指标
    difference = obs_valid - pred_valid
    mse = np.mean(difference ** 2)
    mae = np.mean(np.abs(difference))
    rmse = np.sqrt(mse)
    
    # 计算相关系数
    corr, p_value = pearsonr(obs_valid, pred_valid)
    
    # 线性拟合和 R^2 计算
    slope, intercept = np.polyfit(obs_valid, pred_valid, 1)
    trendline = slope * obs_valid + intercept
    ss_tot = np.sum((pred_valid - np.mean(pred_valid)) ** 2)
    ss_res = np.sum((pred_valid - trendline) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    return {
        'mse': mse, 
        'mae': mae, 
        'rmse': rmse, 
        'correlation': corr,
        'p_value': p_value,
        'r_squared': r_squared,
        'slope': slope,
        'intercept': intercept
    }

def visualize_results(observed, predicted, mask, difference_map, metrics):
    """可视化比较结果"""
    # 创建图像网格
    fig = plt.figure(figsize=(16, 12))
    
    # 1. 差值的空间分布
    ax1 = fig.add_subplot(221)
    masked_difference = np.ma.masked_where(~mask, difference_map)
    im = ax1.imshow(masked_difference, cmap='coolwarm', vmin=-5, vmax=5)
    plt.colorbar(im, ax=ax1, label='差异 (预测 - 观测)')
    ax1.set_title('观测与预测LAI的空间差异')
    ax1.set_xlabel('像素列')
    ax1.set_ylabel('像素行')
    
    # 2. 散点图比较
    ax2 = fig.add_subplot(222)
    ax2.scatter(observed[mask], predicted[mask], alpha=0.5, s=1)
    
    # 添加拟合线
    x_range = np.linspace(np.min(observed[mask]), np.max(observed[mask]), 100)
    ax2.plot(x_range, metrics['slope'] * x_range + metrics['intercept'], 'r-')
    
    # 添加1:1线
    ax2.plot([-10, 10], [-10, 10], 'k--')
    
    ax2.set_xlabel('观测值')
    ax2.set_ylabel('预测值')
    ax2.set_title('观测值 vs 预测值')
    ax2.grid(True)
    
    # 添加统计信息文本
    stats_text = f"RMSE: {metrics['rmse']:.4f}\n" \
                f"相关系数: {metrics['correlation']:.4f}\n" \
                f"R²: {metrics['r_squared']:.4f}"
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes, 
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 3. 直方图展示误差分布
    ax3 = fig.add_subplot(223)
    differences = observed[mask] - predicted[mask]
    ax3.hist(differences, bins=50, alpha=0.75)
    ax3.set_xlabel('误差 (观测 - 预测)')
    ax3.set_ylabel('频率')
    ax3.set_title('误差分布直方图')
    
    # 4. 累积误差分布
    ax4 = fig.add_subplot(224)
    sorted_errors = np.sort(np.abs(differences))
    cumulative = np.arange(1, len(sorted_errors) + 1) / len(sorted_errors)
    ax4.plot(sorted_errors, cumulative)
    ax4.set_xlabel('绝对误差')
    ax4.set_ylabel('累积比例')
    ax4.set_title('累积误差分布')
    ax4.grid(True)
    
    plt.tight_layout()
    return fig

def main():
    # 用户输入两张TIFF图像的路径
    print("请输入需要比较的两张TIFF图像路径")
    observed_path_input = input("请输入第一张TIFF图像路径 (观测值): ").strip()
    predicted_path_input = input("请输入第二张TIFF图像路径 (预测值): ").strip()
    
    # 去除可能存在的引号
    observed_path_input = observed_path_input.strip('"\'')
    predicted_path_input = predicted_path_input.strip('"\'')
    
    # 转换为Path对象
    observed_lai_path = Path(observed_path_input)
    predicted_lai_path = Path(predicted_path_input)
    
    # 检查文件是否存在
    for path in [observed_lai_path, predicted_lai_path]:
        if not path.exists():
            print(f"错误: 文件不存在: {path}")
            return
    
    # 读取数据
    observed_LAI, observed_meta = read_tiff(observed_lai_path)
    predicted_LAI, predicted_meta = read_tiff(predicted_lai_path)
    
    if observed_LAI is None or predicted_LAI is None:
        print("读取数据失败。")
        return
        
    # 检查两个栅格的尺寸是否匹配
    if observed_LAI.shape != predicted_LAI.shape:
        print(f"错误: 栅格尺寸不匹配: {observed_LAI.shape} vs {predicted_LAI.shape}")
        return
    
    # 数据预处理
    observed_LAI, predicted_LAI, mask = preprocess_data(observed_LAI, predicted_LAI)
    
    # 计算差值图
    difference_map = predicted_LAI - observed_LAI
    
    # 计算评价指标
    metrics = calculate_metrics(observed_LAI, predicted_LAI, mask)
    
    # 可视化结果
    fig = visualize_results(observed_LAI, predicted_LAI, mask, difference_map, metrics)
    
    # 打印结果
    print("\n--- 评价指标 ---")
    print(f"均方误差 (MSE): {metrics['mse']:.6f}")
    print(f"平均绝对误差 (MAE): {metrics['mae']:.6f}")
    print(f"均方根误差 (RMSE): {metrics['rmse']:.6f}")
    print(f"Pearson 相关系数: {metrics['correlation']:.6f} (p值={metrics['p_value']:.6f})")
    print(f"决定系数 (R²): {metrics['r_squared']:.6f}")
    print(f"线性拟合: y = {metrics['slope']:.4f}x + {metrics['intercept']:.4f}")
    
    # 保存图像(可选)
    # fig.savefig("LAI_comparison_results.png", dpi=300, bbox_inches='tight')
    
    plt.show()

if __name__ == "__main__":
    main()