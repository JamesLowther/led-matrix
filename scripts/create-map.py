from PIL import Image

WIDTH = 80
HEIGHT = 40

def main():
    img = Image.open("world-map.png").convert("1")
    # img.thumbnail((WIDTH, HEIGHT), Image.BOX)
    img = img.resize((WIDTH, HEIGHT), Image.BOX)

    img.save("converted-map.png", "PNG")

if __name__ == "__main__":
    main()
