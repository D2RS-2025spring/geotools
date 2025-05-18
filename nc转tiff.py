import netCDF4 as nc
import os
import glob

# 定义NC文件夹路径
folder_path = r"E:\降雨数据"


def examine_nc_file(file_path):
    """检查并显示NC文件的详细信息"""
    print(f"\n{'=' * 50}")
    print(f"正在分析文件: {os.path.basename(file_path)}")
    print(f"{'=' * 50}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}")
        return

    try:
        # 尝试加载文件
        data = nc.Dataset(file_path)
        print("文件加载成功！")

        # 查看文件内容
        print("\n=== 基本信息 ===")
        print(data)

        # 显示维度信息
        print("\n=== 维度信息 ===")
        for dim_name, dim in data.dimensions.items():
            print(f"维度名称: {dim_name}, 大小: {len(dim)}, 无限制: {dim.isunlimited()}")

        # 显示变量信息
        print("\n=== 变量信息 ===")
        for var_name, var in data.variables.items():
            print(f"变量名称: {var_name}")
            print(f"  形状: {var.shape}")
            print(f"  数据类型: {var.dtype}")
            print(f"  属性: {var.ncattrs()}")
            for attr in var.ncattrs():
                print(f"    {attr}: {var.getncattr(attr)}")

        # 显示全局属性
        print("\n=== 全局属性 ===")
        for attr in data.ncattrs():
            print(f"{attr}: {data.getncattr(attr)}")

        # 关闭文件
        data.close()
        print("\n文件已关闭")

    except Exception as e:
        print(f"加载文件时出错：{e}")
        if isinstance(e, PermissionError):
            print("权限不足，无法访问文件。")
        else:
            print("可能是文件损坏或格式不兼容。")


# 主程序
def main():
    # 获取文件夹中所有NC文件
    nc_files = glob.glob(os.path.join(folder_path, "*.nc"))

    if not nc_files:
        print(f"在 {folder_path} 中没有找到NC文件")
        return

    print(f"在 {folder_path} 中找到了 {len(nc_files)} 个NC文件")
    print("开始自动查看所有NC文件...")

    # 直接循环查看所有文件，无需用户确认
    for i, file_path in enumerate(nc_files):
        print(f"\n处理第 {i + 1}/{len(nc_files)} 个文件")
        examine_nc_file(file_path)


if __name__ == "__main__":
    main()
