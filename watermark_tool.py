import io
import numpy as np
import streamlit as st
from PIL import Image

from image_processing import (
    resize_with_margin,
    add_watermark
)


def show_watermark_tool():
    st.subheader("ウォーターマーク編集")
    st.write("画像をドラッグ&ドロップして、ウォーターマークを編集できます。")

    st.sidebar.header("ウォーターマーク設定")

    paper_size = st.sidebar.selectbox(
        "枠サイズ",
        ["A4", "A3", "B5", "L判", "2L判", "はがき", "正方形"]
    )

    watermark_text = st.sidebar.text_input("文字", "SAMPLE")

    font_name = st.sidebar.selectbox(
        "フォント",
        [
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Courier",
            "Hiragino Sans",
            "Hiragino Mincho"
        ]
    )


    watermark_size = st.sidebar.slider("文字サイズ", 20, 250, 100)

    watermark_opacity = st.sidebar.slider("透明度", 0, 255, 140)

    watermark_color = st.sidebar.color_picker(
        "文字色",
        "#FFFFFF"
    )


    output_format = st.sidebar.radio(
        "出力形式",
        ["PNG", "JPG"]
    )

    uploaded_file = st.file_uploader(
        "ここに画像をドラッグ&ドロップ",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        key="watermark_upload"
    )

    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        image_np = np.array(image)

        preview = resize_with_margin(image_np, paper_size)

        output_image = Image.fromarray(preview)
        output_buffer = io.BytesIO()

        if output_format == "PNG":
            output_image.save(output_buffer, format="PNG")
            file_name = "watermark_image.png"
            mime = "image/png"
        else:
            output_image.convert("RGB").save(
                output_buffer,
                format="JPEG",
                quality=95
            )
            file_name = "watermark_image.jpg"
            mime = "image/jpeg"

        output_buffer.seek(0)

        st.download_button(
            label="ウォーターマーク画像をダウンロード",
            data=output_buffer,
            file_name=file_name,
            mime=mime
        )