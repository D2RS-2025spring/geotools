import os
from osgeo import gdal
from tqdm import tqdm

# 输入和输出路径配置
input_folder = r'E:\gee data\投影完成'  # 输入文件夹路径
output_folder = os.path.join(input_folder, 'resampled_30m')  # 自动创建输出文件夹
os.makedirs(output_folder, exist_ok=True)  # 确保输出文件夹存在

# 重采样参数设置
target_res = 30  # 目标分辨率（米）
resample_method = gdal.GRA_Bilinear  # 最优方法：双线性插值（连续数据）

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
    output_path = os.path.join(output_folder, f"30m_{filename}")
    resample_tif(input_path, output_path)

print(f"\n处理完成！结果已保存至：{output_folder}")
