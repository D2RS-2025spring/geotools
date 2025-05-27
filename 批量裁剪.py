import os
import logging
from datetime import datetime
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import glob
from tqdm import tqdm
import sys
from pathlib import Path


# 配置日志记录
def setup_logging():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"clip_raster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def validate_paths(shapefile_path, raster_dir, output_dir):
    """验证输入路径的有效性"""
    if not os.path.exists(shapefile_path):
        raise FileNotFoundError(f"Shapefile not found: {shapefile_path}")
    if not os.path.exists(raster_dir):
        raise FileNotFoundError(f"Raster directory not found: {raster_dir}")
    if not shapefile_path.lower().endswith('.shp'):
        raise ValueError("Input shapefile must have .shp extension")
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)


def clip_raster_with_shapefile(input_raster, output_raster, shapes, logger, reference_raster=None):
    """裁剪单个栅格文件，可选择与参考栅格对齐"""
    try:
        with rasterio.open(input_raster) as src:
            if reference_raster:
                # 使用参考栅格进行捕捉
                with rasterio.open(reference_raster) as ref:
                    ref_transform = ref.transform
                    ref_height = ref.height
                    ref_width = ref.width
                    ref_crs = ref.crs

                    # 执行裁剪但使用参考栅格的尺寸和变换
                    out_image, out_transform = mask(src, shapes, crop=False, 
                                                   transform=ref_transform, 
                                                   all_touched=True, 
                                                   nodata=src.nodata)

                    # 复制并更新元数据，使用参考栅格的尺寸和变换
                    out_meta = src.meta.copy()
                    out_meta.update({
                        "driver": "GTiff",
                        "height": ref_height,
                        "width": ref_width,
                        "transform": ref_transform,
                        "crs": ref_crs,
                        "nodata": src.nodata
                    })
            else:
                # 执行普通裁剪
                out_image, out_transform = mask(src, shapes, crop=True, nodata=src.nodata)

                # 复制并更新元数据
                out_meta = src.meta.copy()
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform,
                    "nodata": src.nodata
                })

            # 创建输出目录（如果不存在）
            os.makedirs(os.path.dirname(output_raster), exist_ok=True)

            # 保存裁剪后的栅格
            with rasterio.open(output_raster, "w", **out_meta) as dest:
                dest.write(out_image)

            return True
    except Exception as e:
        logger.error(f"Error processing {input_raster}: {str(e)}")
        return False


def main():
    # 设置日志记录
    logger = setup_logging()
    logger.info("Starting raster clipping process...")

    try:
        # 设置输入路径
        shapefile_path = r"D:\A曾都区三普\环境因子处理\曾都区缓冲区cgcsgk20.shp" # 保持不变
        raster_dir = r"D:\A曾都区三普\环境因子处理\植被指数\NDVI\季度NDVI投影"  # 更新的输入栅格目录
        output_dir = r"D:\A曾都区三普\环境因子处理\植被指数\NDVI\季度NDVI裁剪"  # 更新的输出目录
        
        # 参考栅格数据路径 - 直接指定特定的参考栅格
        reference_raster_path = r"D:\A曾都区三普\环境因子处理\曾都区DEM30m.tif" # 更新的参考栅格路径
        
        # 验证路径
        validate_paths(shapefile_path, raster_dir, output_dir)
        # 验证参考栅格路径
        if not os.path.exists(reference_raster_path):
             raise FileNotFoundError(f"Reference raster not found: {reference_raster_path}")

        # 读取裁剪边界
        logger.info("Reading shapefile...")
        gdf = gpd.read_file(shapefile_path)

        # 获取所有tif文件
        tif_files = glob.glob(os.path.join(raster_dir, "*.tif"))
        total_files = len(tif_files)

        if total_files == 0:
            logger.warning("No TIF files found in the specified directory!")
            return
            
        # 记录使用的参考栅格
        logger.info(f"Using raster as reference: {os.path.basename(reference_raster_path)}")
        logger.info(f"Found {total_files} TIF files to process")

        # 获取shapes（只需要做一次）
        shapes = [feature for feature in gdf.geometry]

        # 处理进度计数器
        successful = 0
        failed = 0

        # 使用tqdm创建进度条
        with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
            for tif_file in tif_files:
                try:
                    # 生成输出文件名
                    filename = os.path.basename(tif_file)
                    output_file = os.path.join(output_dir, filename)  # 去掉了"clipped_"前缀

                    # 处理单个文件，使用指定的参考栅格进行捕捉
                    if clip_raster_with_shapefile(tif_file, output_file, shapes, logger, reference_raster=reference_raster_path):
                        successful += 1
                    else:
                        failed += 1

                except Exception as e:
                    logger.error(f"Unexpected error processing {filename}: {str(e)}")
                    failed += 1

                finally:
                    pbar.update(1)

        # 输出最终统计信息
        logger.info(f"""
Processing completed:
- Total files: {total_files}
- Successfully processed: {successful}
- Failed: {failed}
- Success rate: {(successful / total_files) * 100:.2f}%
- Reference raster: {os.path.basename(reference_raster_path)}
        """)

    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
