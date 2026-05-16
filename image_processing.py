import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def opencv_enhance(file_bytes, scale, sharpen_strength, denoise_strength):
    file_array = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(file_array, cv2.IMREAD_COLOR)

    if img is None:
        return None

    if denoise_strength > 0:
        img = cv2.fastNlMeansDenoisingColored(
            img, None, denoise_strength, denoise_strength, 7, 21
        )

    h, w = img.shape[:2]

    img = cv2.resize(
        img,
        (int(w * scale), int(h * scale)),
        interpolation=cv2.INTER_CUBIC
    )

    if sharpen_strength > 0:
        blurred = cv2.GaussianBlur(img, (0, 0), 3)
        img = cv2.addWeighted(
            img,
            1.0 + sharpen_strength,
            blurred,
            -sharpen_strength,
            0
        )

    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def get_paper_size(size_name):
    sizes = {
        "A4": (2480, 3508),
        "A3": (3508, 4961),
        "B5": (2079, 2953),
        "L判": (1051, 1500),
        "2L判": (1500, 2102),
        "はがき": (1181, 1748),
        "正方形": (2000, 2000),
    }

    return sizes.get(size_name, (2480, 3508))


def resize_with_margin(image_rgb, paper_size):
    target_w, target_h = get_paper_size(paper_size)
    h, w = image_rgb.shape[:2]

    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(
        image_rgb,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    canvas = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255

    y = (target_h - new_h) // 2
    x = (target_w - new_w) // 2

    canvas[y:y + new_h, x:x + new_w] = resized

    return canvas


def resize_full(image_rgb, paper_size):
    target_w, target_h = get_paper_size(paper_size)
    h, w = image_rgb.shape[:2]

    scale = max(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    resized = cv2.resize(
        image_rgb,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    x = (new_w - target_w) // 2
    y = (new_h - target_h) // 2

    return resized[y:y + target_h, x:x + target_w]


def add_watermark(
    image_rgb,
    text,
    position,
    font_size,
    opacity,
    color_name,
    angle=0,
    font_name="Arial"
):
    img = Image.fromarray(image_rgb).convert("RGBA")

    hex_color = color_name.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    color = (r, g, b, opacity)

    try:
        font = ImageFont.truetype(font_name, font_size)
    except:
        font = ImageFont.load_default()

    dummy_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_layer)

    bbox = dummy_draw.textbbox((0, 0), text, font=font)

    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    w, h = img.size
    margin = 50

    if position == "中央":
        x = (w - text_w) // 2
        y = (h - text_h) // 2
    elif position == "右下":
        x = w - text_w - margin
        y = h - text_h - margin
    elif position == "左上":
        x = margin
        y = margin
    elif position == "右上":
        x = w - text_w - margin
        y = margin
    else:
        x = margin
        y = h - text_h - margin

    text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)

    text_draw.text((x, y), text, font=font, fill=color)

    if angle != 0:
        text_layer = text_layer.rotate(angle, expand=False)

    combined = Image.alpha_composite(img, text_layer).convert("RGB")

    return np.array(combined)