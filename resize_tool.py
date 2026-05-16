import io
import zipfile
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image


def resize_image(image_rgb, mode, width_px, height_px, keep_ratio, scale_percent):
    h, w = image_rgb.shape[:2]

    if mode == "％で調整":
        scale = scale_percent / 100
        new_w = int(w * scale)
        new_h = int(h * scale)

    else:
        if keep_ratio:
            ratio = min(width_px / w, height_px / h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
        else:
            new_w = width_px
            new_h = height_px

    resized = cv2.resize(
        image_rgb,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )

    return resized


def show_resize_tool():
    st.subheader("画像リサイズ")
    st.write("複数画像をまとめてリサイズして、ZIPでダウンロードできます。")

    st.sidebar.header("リサイズ設定")

    resize_mode = st.sidebar.radio(
        "リサイズ方法",
        [
            "pxで指定",
            "％で調整"
        ]
    )

    width_px = st.sidebar.number_input(
        "横幅 px",
        min_value=1,
        max_value=10000,
        value=2480,
        step=10
    )

    height_px = st.sidebar.number_input(
        "縦幅 px",
        min_value=1,
        max_value=10000,
        value=3508,
        step=10
    )

    keep_ratio = st.sidebar.checkbox(
        "縦横比を保つ",
        value=True
    )

    scale_percent = st.sidebar.slider(
        "拡大・縮小率（％）",
        10,
        500,
        100
    )

    output_format = st.sidebar.radio(
        "出力形式",
        ["PNG", "JPG"]
    )

    uploaded_files = st.file_uploader(
        "画像をドラッグ&ドロップしてください",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        key="resize_upload"
    )

    if uploaded_files:
        st.write(f"{len(uploaded_files)}枚の画像が選択されました。")

        if len(uploaded_files) > 30:
            st.error("一度に処理できる画像は最大30枚までです。")
            st.stop()

        if st.button("リサイズする"):
            zip_buffer = io.BytesIO()
            progress = st.progress(0)
            status_text = st.empty()

            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for i, uploaded_file in enumerate(uploaded_files):
                    status_text.text(
                        f"処理中: {i + 1}/{len(uploaded_files)}"
                    )

                    image = Image.open(uploaded_file).convert("RGB")
                    image_np = np.array(image)

                    resized = resize_image(
                        image_np,
                        resize_mode,
                        width_px,
                        height_px,
                        keep_ratio,
                        scale_percent
                    )

                    output_image = Image.fromarray(resized)
                    output_buffer = io.BytesIO()

                    if output_format == "PNG":
                        output_ext = "png"
                        output_image.save(output_buffer, format="PNG")
                    else:
                        output_ext = "jpg"
                        output_image.convert("RGB").save(
                            output_buffer,
                            format="JPEG",
                            quality=95
                        )

                    original_stem = Path(uploaded_file.name).stem
                    output_name = f"{original_stem}_resized.{output_ext}"

                    zip_file.writestr(
                        output_name,
                        output_buffer.getvalue()
                    )

                    progress.progress((i + 1) / len(uploaded_files))

            zip_buffer.seek(0)

            st.download_button(
                label="リサイズ画像をZIPでダウンロード",
                data=zip_buffer,
                file_name="resized_images.zip",
                mime="application/zip"
            )