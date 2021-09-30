import requests
from io import BytesIO
from PIL import Image

def main():
    icons = [
        "01",
        "02",
        "03",
        "04",
        "09",
        "10",
        "11",
        "13",
        "50"
    ]    

    for suffix in ["d", "n"]:
        for icon in icons:
            url = f"https://openweathermap.org/img/wn/{icon}{suffix}@2x.png"
            image = requests.get(url)

            icon_image = Image.open(BytesIO(image.content))
            icon_image.save(f"./icons/{icon}{suffix}.png", "PNG")

main()