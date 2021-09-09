from PIL import Image

WIDTH = 25
HEIGHT = 15

def main():
    img = Image.open("world-map.png").convert("1")
    # img.thumbnail((WIDTH, HEIGHT), Image.BOX)
    img = img.resize((WIDTH, HEIGHT), Image.BOX)

    img.save("test.png", "PNG")

if __name__ == "__main__":
    main()