import pandas as pd


def determine_soil_texture(sand_2_0_2, sand_0_2_0_02, silt_0_02_0_002, clay_lt_0_002):
    """
    根据机械组成数据确定土壤质地（改进版）

    参数:
    sand_2_0_2: 2~0.2mm颗粒含量 (%)
    sand_0_2_0_02: 0.2~0.02mm颗粒含量 (%)
    silt_0_02_0_002: 0.02~0.002mm颗粒含量 (%)
    clay_lt_0_002: <0.002mm颗粒含量 (%)

    返回:
    土壤质地名称
    """
    # 计算总砂粒(0.02~2mm)、粉粒(0.002~0.02mm)和黏粒(<0.002mm)含量
    total_sand = sand_2_0_2 + sand_0_2_0_02  # 砂粒(0.02~2mm)
    total_silt = silt_0_02_0_002  # 粉粒(0.002~0.02mm)
    total_clay = clay_lt_0_002  # 黏粒(<0.002mm)

    # 检查总和是否为100% (允许1%的误差)
    total = total_sand + total_silt + total_clay
    if abs(total - 100) > 1:
        return f"数据异常(总和{total}%)", False

    # 根据国际制土壤质地分类标准判断
    if total_clay >= 60:
        return "黏土", True
    elif 35 <= total_clay < 60:
        if total_silt >= 40:
            return "粉砂质黏土", True
        elif total_sand >= 45:
            return "砂质黏土", True
        else:
            return "黏土", True
    elif 15 <= total_clay < 35:
        if total_silt >= 40:
            return "粉砂质黏壤土", True
        elif total_sand >= 45:
            return "砂质黏壤土", True
        else:
            return "黏壤土", True
    elif total_clay < 15:
        if total_silt >= 50:
            return "粉砂土", True
        elif total_sand >= 85:
            return "砂土", True
        elif total_sand >= 70:
            return "壤质砂土", True
        elif total_sand >= 50:
            if total_silt >= 30:
                return "粉砂质壤土", True
            else:
                return "砂质壤土", True
        else:
            if total_silt >= 30:
                return "壤土", True
            else:
                return "砂质壤土", True
    else:
        return "无法分类", False


def compare_texture(original, calculated):
    """比较两个土壤质地是否一致（考虑同义词）"""
    if pd.isna(original):
        return "原始数据为空"

    # 常见同义词映射（可根据实际情况补充）
    synonyms = {
        "黏土": ["粘土"],
        "砂土": ["砂土及壤质砂土"],
        "壤土": ["砂质壤土", "粉砂质壤土"]  # 示例，需要根据实际分类标准调整
    }

    # 检查是否完全相同
    if original == calculated:
        return "一致"

    # 检查是否为同义词
    for key, values in synonyms.items():
        if (original in values and calculated == key) or (calculated in values and original == key):
            return "同义词"

    return "不一致"


# 读取Excel文件
file_path = r"C:\Users\zll16\Desktop\机械组成.xlsx"
try:
    # 读取Excel文件
    df = pd.read_excel(file_path)

    # 检查必要的列是否存在
    required_columns = ['机械组成2~0.2mm颗粒含量', '机械组成0.2~0.02mm颗粒含量',
                        '机械组成0.02~0.002mm颗粒含量', '机械组成0.002mm以下颗粒含量']

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"缺少必要的列: {', '.join(missing_cols)}")

    # 计算每行的土壤质地
    results = []
    for _, row in df.iterrows():
        # 获取各组分的值，处理可能的空值
        sand_2_0_2 = row.get('机械组成2~0.2mm颗粒含量', 0)
        sand_0_2_0_02 = row.get('机械组成0.2~0.02mm颗粒含量', 0)
        silt_0_02_0_002 = row.get('机械组成0.02~0.002mm颗粒含量', 0)
        clay_lt_0_002 = row.get('机械组成0.002mm以下颗粒含量', 0)

        # 计算土壤质地
        texture, is_valid = determine_soil_texture(
            sand_2_0_2, sand_0_2_0_02, silt_0_02_0_002, clay_lt_0_002
        )

        # 获取原始土壤质地（如果有）
        original_texture = row.get('机械组成土壤质地', None)

        # 比较结果
        comparison = compare_texture(original_texture, texture) if '机械组成土壤质地' in df.columns else "无原始数据"

        results.append({
            '计算土壤质地': texture,
            '数据有效性': "有效" if is_valid else "无效",
            '原始土壤质地': original_texture if '机械组成土壤质地' in df.columns else None,
            '一致性判断': comparison
        })

    # 合并结果到原DataFrame
    result_df = pd.concat([df, pd.DataFrame(results)], axis=1)

    # 保存结果到新文件
    output_path = r"C:\Users\zll16\Desktop\机械组成_土壤质地结果.xlsx"
    result_df.to_excel(output_path, index=False)

    print(f"处理完成，结果已保存到: {output_path}")

    # 输出统计信息
    if '机械组成土壤质地' in df.columns:
        stats = pd.DataFrame(results)['一致性判断'].value_counts()
        print("\n一致性统计:")
        print(stats.to_string())

        valid_count = sum([1 for r in results if r['数据有效性'] == "有效"])
        print(f"\n有效数据: {valid_count}/{len(results)} ({valid_count / len(results):.1%})")

except FileNotFoundError:
    print(f"错误: 文件未找到 - {file_path}")
except Exception as e:
    print(f"处理过程中发生错误: {str(e)}")
    if hasattr(e, 'args') and e.args:
        print("详细信息:", e.args[0])
