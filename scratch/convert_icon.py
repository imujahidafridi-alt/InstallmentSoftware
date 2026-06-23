from PIL import Image
import os

png_path = "src/views/assets/app_icon.png"
ico_path = "src/views/assets/app_icon.ico"

if os.path.exists(png_path):
    print(f"Converting {png_path} to {ico_path}...")
    img = Image.open(png_path)
    img.save(ico_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Icon successfully converted!")
else:
    print(f"Error: {png_path} not found.")
