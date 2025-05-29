import os
from osgeo import gdal, osr
from tqdm import tqdm


def get_srs_from_raster(raster_path):
    """从栅格文件中获取坐标系"""
    ds = gdal.Open(raster_path)
    srs = osr.SpatialReference()
    srs.ImportFromWkt(ds.GetProjection())
    ds = None
    return srs


def reproject_raster(input_path, output_path, target_srs):
    """重投影栅格数据"""
    # 打开输入文件
    src_ds = gdal.Open(input_path)

    # 获取输入文件的投影
    src_srs = osr.SpatialReference()
    src_srs.ImportFromWkt(src_ds.GetProjection())

    # 设置重投影选项
    warp_options = gdal.WarpOptions(
        srcSRS=src_srs,
        dstSRS=target_srs,
        resampleAlg=gdal.GRA_Bilinear,
        format='GTiff',
        dstNodata=0,  # 设置输出NoData值为0
        creationOptions=['COMPRESS=LZW']  # 添加压缩选项
    )

    # 执行重投影
    gdal.Warp(output_path, src_ds, options=warp_options)

    # 关闭数据集
    src_ds = None


def batch_reproject(input_dir, output_dir, reference_raster):
    """批量重投影"""
    # 获取参考栅格文件的坐标系
    target_srs = get_srs_from_raster(reference_raster)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 获取输入文件列表
    input_files = [f for f in os.listdir(input_dir) if f.endswith('.tif')]

    # 处理每个文件
    for filename in tqdm(input_files, desc="Processing files"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        reproject_raster(input_path, output_path, target_srs)


if __name__ == "__main__":
    # 获取用户输入的路径
    print("请输入以下路径信息（可直接复制粘贴带引号的路径）：")
    input_dir = input("输入原始TIFF文件所在文件夹路径: ").strip().strip('"\'')
    output_dir = input("输入投影转换后TIFF文件保存路径: ").strip().strip('"\'')
    reference_raster = input("输入参考栅格文件路径: ").strip().strip('"\'' )

    # 检查路径是否存在
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在: {input_dir}")
        exit(1)
    if not os.path.exists(reference_raster):
        print(f"错误: 参考栅格文件不存在: {reference_raster}")
        exit(1)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 执行批量重投影
    batch_reproject(input_dir, output_dir, reference_raster)
    print("All files processed successfully!")