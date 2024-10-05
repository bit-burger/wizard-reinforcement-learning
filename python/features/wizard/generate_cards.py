import os
from PIL import Image, ImageDraw, ImageFont


def create_card(color, value, size=(105, 132)):
    img = Image.new('RGBA', size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    colors = {
        'blue': (0, 168, 252, 200),  # Discord Blue
        'green': (87, 242, 135, 200),  # Discord Green
        'yellow': (254, 231, 92, 200),  # Discord Yellow
        'red': (235, 69, 158, 200),  # Discord Fuchsia
        'white': (255, 255, 255, 255)
    }

    # Draw border
    taken_color = colors[color]
    if value in ['Joker', 'Wizard']:
        taken_color = colors['white']
        value = 'a'
    padding = 1
    draw.rounded_rectangle([padding, padding, size[0] - padding, size[1] - padding],
                           fill=None, radius=24, width=7, outline=taken_color)

    # Draw text
    font = ImageFont.truetype("./Arial Rounded Bold.ttf", 70)

    add = 1
    if value in [12, 13]:
        add = 0

    draw.text((size[0] // 2 + add, size[1] // 2), str(value), fill=taken_color, font=font, anchor="mm")

    return img


def generate_deck():
    colors = ['red', 'green', 'yellow', 'blue']
    values = list(range(1, 14))

    if not os.path.exists('card_deck'):
        os.makedirs('card_deck')

    for color in colors:
        for value in values:
            card = create_card(color, value)
            card.save(f'card_deck/{color}_{value}.png')


if __name__ == "__main__":
    generate_deck()
    print("Card deck generated successfully!")