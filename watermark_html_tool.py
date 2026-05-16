import base64
import json
import streamlit as st
import streamlit.components.v1 as components


def show_html_watermark_tool():
    st.subheader("ウォーターマーク編集")
    st.write("画像を読み込んで、文字をドラッグして自由に配置できます。")

    st.sidebar.header("ウォーターマーク設定")

    watermark_text = st.sidebar.text_input("文字", "SAMPLE")
    watermark_color = st.sidebar.color_picker("文字色", "#FFFFFF")
    watermark_size = st.sidebar.slider("文字サイズ", 20, 250, 100)
    watermark_opacity = st.sidebar.slider("透明度", 0.0, 1.0, 0.55, 0.05)
    watermark_angle = st.sidebar.slider("角度", -180, 180, 0)

    watermark_font = st.sidebar.selectbox(
        "フォント",
        [
            "Arial",
            "Helvetica",
            "Times New Roman",
            "Courier New",
            "serif",
            "sans-serif"
        ]
    )

    uploaded_file = st.file_uploader(
        "画像をドラッグ&ドロップしてください",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=False,
        key="html_watermark_upload"
    )

    if not uploaded_file:
        return

    image_bytes = uploaded_file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    text_js = json.dumps(watermark_text)
    color_js = json.dumps(watermark_color)
    font_js = json.dumps(watermark_font)
    file_key_js = json.dumps(uploaded_file.name)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        body {{
          margin: 0;
          background: #f7f9fc;
          font-family: Arial, sans-serif;
        }}

        .notice {{
          margin-bottom: 10px;
          font-size: 14px;
          color: #333;
        }}

        canvas {{
          border: 2px dashed #4a90e2;
          background: white;
          max-width: 100%;
          cursor: grab;
        }}

        canvas:active {{
          cursor: grabbing;
        }}

        button {{
          margin-top: 12px;
          padding: 10px 18px;
          background: #4a90e2;
          color: white;
          border: none;
          border-radius: 10px;
          font-weight: bold;
          cursor: pointer;
        }}
      </style>
    </head>

    <body>
      <div class="notice">
        文字をクリックして掴むと、自由な位置に移動できます。
      </div>

      <canvas id="canvas"></canvas>
      <br>
      <button onclick="downloadImage()">ウォーターマーク画像をダウンロード</button>

      <script>
        const imageData = "data:image/png;base64,{image_base64}";
        const canvas = document.getElementById("canvas");
        const ctx = canvas.getContext("2d");

        const text = {text_js};
        const color = {color_js};
        const size = {watermark_size};
        const opacity = {watermark_opacity};
        const angle = {watermark_angle};
        const font = {font_js};
        const fileKey = "watermark_position_" + {file_key_js};

        const img = new Image();
        img.src = imageData;

        let textX = 200;
        let textY = 200;
        let dragging = false;
        let offsetX = 0;
        let offsetY = 0;

        function draw() {{
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

          ctx.save();
          ctx.globalAlpha = opacity;
          ctx.translate(textX, textY);
          ctx.rotate(angle * Math.PI / 180);
          ctx.font = `${{size}}px ${{font}}`;
          ctx.fillStyle = color;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText(text, 0, 0);
          ctx.restore();
        }}

        img.onload = function() {{
          const maxWidth = 900;
          const ratio = img.width > maxWidth ? maxWidth / img.width : 1;

          canvas.width = img.width * ratio;
          canvas.height = img.height * ratio;

          const saved = localStorage.getItem(fileKey);

          if (saved) {{
            const pos = JSON.parse(saved);
            textX = pos.x;
            textY = pos.y;
          }} else {{
            textX = canvas.width / 2;
            textY = canvas.height / 2;
          }}

          draw();
        }};

        function isNearText(x, y) {{
          const hitWidth = Math.max(180, text.length * size * 0.6);
          const hitHeight = size * 1.5;

          return (
            Math.abs(x - textX) < hitWidth / 2 &&
            Math.abs(y - textY) < hitHeight / 2
          );
        }}

        canvas.addEventListener("mousedown", function(e) {{
          const rect = canvas.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;

          if (isNearText(x, y)) {{
            dragging = true;
            offsetX = x - textX;
            offsetY = y - textY;
          }}
        }});

        canvas.addEventListener("mousemove", function(e) {{
          const rect = canvas.getBoundingClientRect();
          const x = e.clientX - rect.left;
          const y = e.clientY - rect.top;

          if (!dragging) return;

          textX = x - offsetX;
          textY = y - offsetY;

          localStorage.setItem(
            fileKey,
            JSON.stringify({{ x: textX, y: textY }})
          );

          draw();
        }});

        canvas.addEventListener("mouseup", function() {{
          dragging = false;
        }});

        canvas.addEventListener("mouseleave", function() {{
          dragging = false;
        }});

        function downloadImage() {{
          const link = document.createElement("a");
          link.download = "watermark_image.png";
          link.href = canvas.toDataURL("image/png");
          link.click();
        }}
      </script>
    </body>
    </html>
    """

    components.html(html_code, height=1000, scrolling=True)