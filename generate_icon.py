import math
from PIL import Image, ImageDraw, ImageFont

def make_app_icon(output_path="app_icon.ico"):
    # 创建 256x256 高清原图
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # 1. 绘制带有科技金融质感的圆角矩形背景 (深邃暗蓝 #0f172a 到 #1e293b 质感)
    pad = 16
    radius = 52
    
    # 外层发光与边框
    draw.rounded_rectangle(
        [pad, pad, size - pad, size - pad],
        radius=radius,
        fill=(15, 23, 42, 255),
        outline=(56, 189, 248, 200),
        width=4
    )

    # 2. 内层微光网格与估值曲线设计 (科技金融 K 线/折现趋势微缩图)
    grid_color = (30, 41, 59, 180)
    for y in [70, 110, 150, 190]:
        draw.line([(pad + 15, y), (size - pad - 15, y)], fill=grid_color, width=1)

    # 绘制估值增长曲线趋势 (渐变科技亮青蓝)
    trend_pts = [
        (pad + 25, 175),
        (pad + 65, 155),
        (pad + 105, 160),
        (pad + 145, 120),
        (pad + 185, 85),
        (size - pad - 25, 65),
    ]
    draw.line(trend_pts, fill=(14, 165, 233, 160), width=3)

    # 3. 核心大标：投行专业金融 "V" 字母标志 (代表 Valuation 估值与 Victory 稳健增值)
    # 使用多段多边形绘制几何切角的现代科技感 V 字
    # 左侧斜边 (深金/科技蓝过渡色)
    # 坐标定义
    cx, cy = size // 2, size // 2 + 10
    
    # 绘制金融金/青蓝几何 "V"
    # 左翼
    left_wing = [
        (60, 75),
        (95, 75),
        (128, 170),
        (95, 170),
    ]
    draw.polygon(left_wing, fill=(2, 132, 199, 255))

    # 右翼 (更亮的主视觉翼)
    right_wing = [
        (128, 170),
        (161, 75),
        (196, 75),
        (144, 195),
        (112, 195),
    ]
    draw.polygon(right_wing, fill=(56, 189, 248, 255))

    # 顶端科技光芒点
    draw.ellipse([186, 68, 202, 84], fill=(250, 204, 21, 255), outline=(255, 255, 255, 220), width=2)

    # 保存为全尺寸多分辨率的高清 Windows ICO
    sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    img.save(output_path, format="ICO", sizes=sizes)
    print(f"Icon generated successfully at: {output_path}")

if __name__ == "__main__":
    make_app_icon()
