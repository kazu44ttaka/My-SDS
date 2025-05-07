import flet as ft
import threading
import subprocess
import io
import base64
from PIL import Image
import pygetwindow as gw

ffmpeg_process = None
DUMMY_IMAGE_PATH = "dummy.png"

# FFmpeg プロセスを開始して MJPEG ストリームを取得
def start_ffmpeg():
    global ffmpeg_process

    cmd = [
        "ffmpeg",
        "-f", "gdigrab",
        "-framerate", "60",
        "-i", "title=MMDAgent-EX - Toolkit for conversational user interface and voice interaction",
        # "-vf", "scale=800:-1",
        "-q:v", "1",
        "-f", "image2pipe",
        "-vcodec", "mjpeg",
        "-"
    ]
    
    try:
        ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        print("[INFO] FFmpeg process started")
    except Exception as e:
        print(f"[ERROR] Failed to start FFmpeg: {e}")

# FFmpeg プロセスを終了
def stop_ffmpeg():
    global ffmpeg_process

    if ffmpeg_process and ffmpeg_process.poll() is None:
        print("[INFO] Terminating FFmpeg process...")
        ffmpeg_process.terminate()
        try:
            ffmpeg_process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            ffmpeg_process.kill()
        print("[INFO] FFmpeg process terminated")
    
    ffmpeg_process = None

# ウィンドウが存在しているかチェック
def is_window_open(window_title):
    windows = gw.getWindowsWithTitle(window_title)
    return len(windows) > 0

# 外部画像を読み込み、Base64 形式で返す
def load_external_image():
    try:
        with open(DUMMY_IMAGE_PATH, "rb") as f:
            img_data = f.read()
        return base64.b64encode(img_data).decode("utf-8")
    except FileNotFoundError:
        print(f"[WARNING] External image not found: {DUMMY_IMAGE_PATH}")
        return ""

def mjpeg_reader(image_control: ft.Image):
    global ffmpeg_process

    buffer = b""
    external_image_b64 = load_external_image()
    while True:
        # MMDAgent-EX が存在しているか確認
        if is_window_open("MMDAgent-EX - Toolkit for conversational user interface and voice interaction"):
            # FFmpeg プロセスが未起動または停止している場合、再起動
            if ffmpeg_process is None or ffmpeg_process.poll() is not None:
                start_ffmpeg()

            try:
                # FFmpeg プロセスの出力を読み取る
                chunk = ffmpeg_process.stdout.read(4096)
                if not chunk:
                    continue

                buffer += chunk
                start = buffer.find(b"\xff\xd8")
                end = buffer.find(b"\xff\xd9")

                if start != -1 and end != -1 and end > start:
                    jpeg_data = buffer[start:end + 2]
                    buffer = buffer[end + 2:]

                    # 画像を PIL で読み込み
                    try:
                        image = Image.open(io.BytesIO(jpeg_data))
                        b = io.BytesIO()
                        image.save(b, format="JPEG")
                        encoded = base64.b64encode(b.getvalue()).decode("utf-8")
                        
                        # Flet イメージコンポーネントに反映
                        image_control.src_base64 = encoded
                        image_control.update()

                    except Exception as e:
                        print(f"[ERROR] Image processing error: {e}")

            except Exception as e:
                print(f"[ERROR] FFmpeg reading error: {e}")

        else:
            # ウィンドウが閉じられている場合は FFmpeg プロセスを停止
            stop_ffmpeg()

            # キャプチャをクリア
            if image_control.src_base64 != external_image_b64:
                image_control.src_base64 = external_image_b64
                image_control.update()

# def main(page: ft.Page):
#     page.title = "MMDAgent-EX キャプチャ表示"
#     img = ft.Image(width=800, fit=ft.ImageFit.CONTAIN, src_base64="")  # 初期化
#     page.add(img)

#     threading.Thread(target=mjpeg_reader, args=(img,), daemon=True).start()

# ft.app(target=main)
