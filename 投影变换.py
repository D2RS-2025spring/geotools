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
    # 输入输出路径
    input_dir = r"E:\下载数据\gee data\LAI_500m_HalfMonth_2000_out" # 输入目录
    output_dir = r"E:\下载数据\gee data\LAI_500m_HalfMonth_2000_out_ty" # 输出目录
    reference_raster = r"D:\丹江口市生态产品价值核算论文\数据\土壤侵蚀量计算2\现期侵蚀量计算\A.tif" # 参考栅格文件路径 

    # 执行批量重投影
    batch_reproject(input_dir, output_dir, reference_raster)
    print("All files processed successfully!")