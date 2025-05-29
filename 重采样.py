import os
from osgeo import gdal
from tqdm import tqdm

# 用户输入参数
print("==== 栅格重采样工具 ====")
# 输入路径并处理可能的引号
input_folder = input("请输入需要重采样的TIFF文件所在文件夹路径: ").strip().strip('"\'' )

# 检查路径是否存在
if not os.path.exists(input_folder):
    print(f"错误: 目录不存在: {input_folder}")
    exit(1)

# 设置输出文件夹
output_folder = os.path.join(input_folder, 'resampled')
# 询问是否使用默认输出路径
use_default = input(f"是否使用默认输出路径 {output_folder}? (y/n): ").strip().lower()
if use_default != 'y':
    output_folder = input("请输入输出文件夹路径: ").strip().strip('"\'' )

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

# 目标分辨率输入
try:
    target_res = float(input("请输入目标分辨率(米): ").strip())
except ValueError:
    print("错误: 请输入有效的数值")
    exit(1)

# 重采样方法选择
print("\n可用的重采样方法:")
print("1. 最近邻法 (分类数据)")
print("2. 双线性插值 (连续数据)")
print("3. 三次卷积 (连续数据，高质量)")
print("4. 平均法 (适合降采样)")
print("5. 众数法 (分类数据)")

# 获取用户选择的方法
try:
    method_choice = int(input("请选择重采样方法 (1-5): ").strip())
    if method_choice < 1 or method_choice > 5:
        raise ValueError()
except ValueError:
    print("错误: 请输入1-5之间的数字")
    exit(1)

# 映射用户选择到GDAL重采样方法
resample_methods = {
    1: gdal.GRA_NearestNeighbour,
    2: gdal.GRA_Bilinear,
    3: gdal.GRA_Cubic,
    4: gdal.GRA_Average,
    5: gdal.GRA_Mode
}
resample_method = resample_methods[method_choice]

def resample_tif(input_path, output_path):
    """执行单个TIFF文件的重采样"""
    try:
        # 打开原始栅格
        src_ds = gdal.Open(input_path)
        if src_ds is None:
            raise ValueError(f"无法打开文件: {input_path}")

        # 获取原始地理信息
        src_proj = src_ds.GetProjection()
        src_geotrans = src_ds.GetGeoTransform()

        # 计算目标栅格尺寸
        x_size = int((src_ds.RasterXSize * abs(src_geotrans[1])) / target_res)
        y_size = int((src_ds.RasterYSize * abs(src_geotrans[5])) / target_res)

        # 配置重采样参数
        warp_options = gdal.WarpOptions(
            format='GTiff',
            xRes=target_res,
            yRes=target_res,
            resampleAlg=resample_method,
            outputBounds=(
                src_geotrans[0],  # 左上角X
                src_geotrans[3] + src_geotrans[5] * src_ds.RasterYSize,  # 左下角Y
                src_geotrans[0] + src_geotrans[1] * src_ds.RasterXSize,  # 右下角X
                src_geotrans[3]  # 右上角Y
            ),
            outputType=gdal.GDT_Float32,  # 保持浮点类型（适合LAI）
            dstSRS=src_proj,  # 保持原始坐标系
            multithread=True,  # 启用多线程加速
            warpMemoryLimit=1024  # 内存限制（MB）
        )

        # 执行重采样
        gdal.Warp(output_path, src_ds, options=warp_options)
        src_ds = None  # 显式关闭数据集

    except Exception as e:
        print(f"\n处理文件 {os.path.basename(input_path)} 时出错: {str(e)}")

# 获取所有TIFF文件
tif_files = [f for f in os.listdir(input_folder) if f.endswith('.tif')]
print(f"发现 {len(tif_files)} 个TIFF文件需要处理...")

# 批量处理带进度条
for filename in tqdm(tif_files, desc="重采样进度", unit="file"):
    input_path = os.path.join(input_folder, filename)
    # 使用用户输入的分辨率作为文件名前缀
    output_path = os.path.join(output_folder, f"{int(target_res)}m_{filename}")
    resample_tif(input_path, output_path)

print(f"\n处理完成！结果已保存至：{output_folder}")
