import pandas as pd
import numpy as np
import os

def calculate_statistics(data_column):
    """
    计算单个数据列的统计指标
    
    参数:
    data_column: 数据列（pandas.Series）
    
    返回:
    包含各项统计指标的字典
    """
    # 移除NaN值
    valid_data = data_column.dropna()
    
    if len(valid_data) == 0:
        return {
            'count': 0,
            'max': np.nan,
            'min': np.nan,
            'median': np.nan,
            'mean': np.nan,
            'percentile_2': np.nan,
            'percentile_5': np.nan,
            'percentile_10': np.nan,
            'percentile_20': np.nan,
            'percentile_80': np.nan,
            'percentile_90': np.nan,
            'percentile_95': np.nan,
            'percentile_98': np.nan,  # 添加98%分位数
            'std': np.nan,
            'cv': np.nan
        }
    
    # 基本统计量
    stats = {}
    stats['count'] = len(valid_data)
    stats['max'] = valid_data.max()
    stats['min'] = valid_data.min()
    stats['median'] = valid_data.median()
    stats['mean'] = valid_data.mean()
    
    # 百分位数计算 - 先将数据排序，然后按照数据点数量的百分比位置取值
    sorted_data = np.sort(valid_data)
    total_points = len(sorted_data)
    
    print(f"计算百分位数：共有{total_points}个有效数据点")
    
    # 手动计算百分位数，确保索引向上取整
    percentiles = [2, 5, 10, 20, 80, 90, 95, 98]  # 添加98%分位数
    for p in percentiles:
        # 计算索引位置（从0开始），并向上取整
        index = int(np.ceil(total_points * p / 100)) - 1
        
        # 确保索引不超出范围
        index = max(0, min(index, total_points - 1))
        
        value = sorted_data[index]
        stats[f'percentile_{p}'] = value
        
        # 打印详细信息
        exact_position = total_points * p / 100
        print(f"{p}%分位数：理论位置={exact_position:.2f}，实际取第{index+1}个数据点（索引{index}），值={value}")
    
    # 标准差和变异系数
    stats['std'] = valid_data.std()
    
    # 计算变异系数 (CV = 标准差/平均值)
    if stats['mean'] != 0:
        stats['cv'] = stats['std'] / abs(stats['mean'])
    else:
        stats['cv'] = np.nan
        
    return stats

def analyze_dataset(file_path, sheet_name=0):
    """
    分析数据集中所有数值列的分布
    
    参数:
    file_path: 数据文件路径
    sheet_name: Excel表格名称或索引
    
    返回:
    包含统计结果的DataFrame
    """
    try:
        # 读取数据
        if file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
        print(f"成功读取数据，共 {len(df)} 行，{len(df.columns)} 列")
        
        # 获取所有数值型列
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not numeric_cols:
            print("警告: 未找到任何数值型列")
            return None
        
        print(f"检测到 {len(numeric_cols)} 个数值型列: {', '.join(numeric_cols)}")
        
        # 为用户提供选择列的机会
        print("\n请选择要分析的列 (输入ALL分析所有数值列):")
        for i, col in enumerate(numeric_cols):
            print(f"{i+1}. {col}")
        
        choice = input("\n请输入列编号 (多个列用逗号分隔，例如'1,3,5'): ").strip().upper()
        
        if choice == 'ALL':
            selected_cols = numeric_cols
        else:
            try:
                indices = [int(idx.strip()) - 1 for idx in choice.split(',') if idx.strip()]
                selected_cols = [numeric_cols[i] for i in indices if 0 <= i < len(numeric_cols)]
            except:
                print("输入有误，将分析所有数值列")
                selected_cols = numeric_cols
        
        print(f"\n将分析以下 {len(selected_cols)} 个列: {', '.join(selected_cols)}")
        
        # 存储结果
        results = {}
        
        # 计算每列的统计指标
        for col in selected_cols:
            stats = calculate_statistics(df[col])
            results[col] = stats
        
        # 将结果转换为DataFrame形式，按照指定顺序
        result_df = pd.DataFrame({
            '指标': [
                '样本数',
                '2%分位数',
                '5%分位数',
                '10%分位数',
                '20%分位数',
                '80%分位数',
                '90%分位数',
                '95%分位数',
                '98%分位数',  # 添加98%分位数
                '最小值',
                '最大值',
                '中位值',
                '平均值',
                '标准差',
                '变异系数'
            ]
        })
        
        # 添加每列的结果，按照指定顺序
        for col in selected_cols:
            result_df[col] = [
                results[col]['count'],
                results[col].get('percentile_2', np.nan),  # 使用get方法防止KeyError
                results[col]['percentile_5'],
                results[col]['percentile_10'],
                results[col]['percentile_20'],
                results[col]['percentile_80'],
                results[col]['percentile_90'],
                results[col]['percentile_95'],
                results[col].get('percentile_98', np.nan),  # 使用get方法防止KeyError
                results[col]['min'],
                results[col]['max'],
                results[col]['median'],
                results[col]['mean'],
                results[col]['std'],
                results[col]['cv']
            ]
        
        return result_df
        
    except Exception as e:
        print(f"分析数据时发生错误: {str(e)}")
        return None

def main():
    print("=" * 50)
    print("数值分布统计分析工具")
    print("=" * 50)
    
    # 获取文件路径并自动处理引号
    file_path = input("请输入数据文件路径 (Excel或CSV): ").strip()
    
    # 自动去除路径两端的引号（支持单引号和双引号）
    if (file_path.startswith('"') and file_path.endswith('"')) or \
       (file_path.startswith("'") and file_path.endswith("'")):
        file_path = file_path[1:-1]
    
    if not os.path.exists(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        return
    
    # 如果是Excel文件，询问sheet名称
    sheet_name = 0  # 默认第一个sheet
    if file_path.lower().endswith(('.xls', '.xlsx', '.xlsm')):
        sheet_input = input("请输入要分析的工作表名称 (直接回车使用第一个工作表): ").strip()
        if sheet_input:
            sheet_name = sheet_input
    
    # 分析数据
    result_df = analyze_dataset(file_path, sheet_name)
    
    if result_df is not None:
        # 显示结果
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print("\n计算结果:")
        print(result_df.to_string(index=False))
        
        # 自动保存结果到Excel文件
        try:
            # 生成输出文件名
            base_name = os.path.splitext(file_path)[0]
            output_path = f"{base_name}_统计结果.xlsx"
            
            # 保存结果
            result_df.to_excel(output_path, index=False, sheet_name='统计结果')
            print(f"\n结果已自动保存到: {output_path}")
        except Exception as e:
            print(f"\n保存结果时出错: {str(e)}")
        
        print("\n分析完成!")

if __name__ == "__main__":
    main()
