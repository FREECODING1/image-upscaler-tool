from resize_tool import show_resize_tool
import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import zipfile
from pathlib import Path
from watermark_html_tool import show_html_watermark_tool

st.set_page_config(
    page_title="AI画像高画質化ツール",
    layout="wide"
)

st.title("AI画像高画質化ツール")
st.write("一度に30枚までアップロードして、印刷向けに高画質化できます。")

with open("style.css", "r", encoding="utf-8") as f:
    st.markdown(
        f"<style>{f.read()}</style>",
        unsafe_allow_html=True
    )

# =========================
# 関数
# =========================

def opencv_enhance(file_bytes, scale, sharpen_strength, denoise_strength):
    file_array = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(file_array, cv2.IMREAD_COLOR)

    if img is None:
        return None

    if denoise_strength > 0:
        img = cv2.fastNlMeansDenoisingColored(
            img,
            None,
            denoise_strength,
            denoise_strength,
            7,
            21
        )

    height, width = img.shape[:2]

    new_width = int(width * scale)
    new_height = int(height * scale)

    img = cv2.resize(
        img,
        (new_width, new_height),
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

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    return img_rgb


def get_paper_size(size_name):
    sizes = {
        "A4": (2480, 3508),
        "A3": (3508, 4961),
        "B5": (2079, 2953),
        "L判": (1051, 1500),
        "2L判": (1500, 2102),
        "はがき": (1181, 1748),
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

    canvas = np.ones(
        (target_h, target_w, 3),
        dtype=np.uint8
    ) * 255

    y_offset = (target_h - new_h) // 2
    x_offset = (target_w - new_w) // 2

    canvas[
        y_offset:y_offset + new_h,
        x_offset:x_offset + new_w
    ] = resized

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

    start_x = (new_w - target_w) // 2
    start_y = (new_h - target_h) // 2

    cropped = resized[
        start_y:start_y + target_h,
        start_x:start_x + target_w
    ]

    return cropped

# =========================
# サイドバー
# =========================

menu = st.sidebar.selectbox(
    "機能を選択",
    ["高画質", "ウォーターマーク", "リサイズ"]
)

if menu == "ウォーターマーク":
    show_html_watermark_tool()
    st.stop()

if menu == "リサイズ":
    show_resize_tool()
    st.stop()

st.sidebar.header("設定")

scale = 3
sharpen_strength = 0.8
denoise_strength = 8
paper_size = "A4"
output_format = "PNG（高画質・容量大きめ）"
print_mode = "余白あり"

if menu == "高画質":
    scale = st.sidebar.selectbox(
        "OpenCV拡大倍率",
        [1.0, 1.5, 2, 3, 4],
        index=2
    )

    sharpen_strength = st.sidebar.slider(
        "シャープ強度",
        0.0,
        2.0,
        0.8,
        0.1
    )

    st.sidebar.caption(
        "輪郭をくっきりさせます。"
    )

    denoise_strength = st.sidebar.slider(
        "ノイズ除去",
        0,
        30,
        8
    )

    st.sidebar.caption(
        "画像のザラつきを減らします。"
    )

    st.sidebar.markdown("""
### おすすめ設定（印刷向け）

- OpenCV拡大倍率：2〜3
- シャープ強度：0.6〜0.8
- ノイズ除去：5〜10
""")

    paper_size = st.sidebar.selectbox(
        "印刷サイズ",
        [
            "A4",
            "A3",
            "B5",
            "L判",
            "2L判",
            "はがき"
        ]
    )

    output_format = st.sidebar.radio(
        "出力形式",
        [
            "PNG（高画質・容量大きめ）",
            "JPG（軽量・容量小さめ）"
        ]
    )

# =========================
# アップロード
# =========================

uploaded_files = st.file_uploader(
    "画像をドラッグ&ドロップしてください",
    type=["jpg", "jpeg", "png", "webp"],
    accept_multiple_files=True
)

if uploaded_files:

    st.write(
        f"{len(uploaded_files)}枚の画像が選択されました。"
    )

    if len(uploaded_files) > 30:
        st.error(
            "一度に処理できる画像は最大30枚までです。"
        )
        st.stop()

    if st.button("高画質化する"):

        zip_buffer = io.BytesIO()

        progress = st.progress(0)

        status_text = st.empty()

        with zipfile.ZipFile(
            zip_buffer,
            "w"
        ) as zip_file:

            for i, uploaded_file in enumerate(uploaded_files):

                status_text.text(
                    f"処理中: {i + 1}/{len(uploaded_files)}"
                )

                file_bytes = uploaded_file.read()

                enhanced = opencv_enhance(
                    file_bytes,
                    scale,
                    sharpen_strength,
                    denoise_strength
                )

                if enhanced is None:
                    continue

                output_image = Image.fromarray(enhanced)

                output_buffer = io.BytesIO()

                if "PNG" in output_format:
                    output_ext = "png"

                    output_image.save(
                        output_buffer,
                        format="PNG"
                    )

                else:
                    output_ext = "jpg"

                    rgb_image = output_image.convert("RGB")

                    rgb_image.save(
                        output_buffer,
                        format="JPEG",
                        quality=95
                    )

                original_stem = Path(
                    uploaded_file.name
                ).stem

                output_name = (
                    f"{original_stem}_print_upscaled.{output_ext}"
                )

                zip_file.writestr(
                    output_name,
                    output_buffer.getvalue()
                )

                progress.progress(
                    (i + 1) / len(uploaded_files)
                )

        zip_buffer.seek(0)

        st.download_button(
            label="高画質化した画像をZIPでダウンロード",
            data=zip_buffer,
            file_name="print_upscaled_images.zip",
            mime="application/zip"
        )