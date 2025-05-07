import flet as ft
import pref
import os
import time
import asyncio
import subprocess
import global_vars as g
import io
import base64
import capture
import threading

def gui_main(page: ft.Page):
    # load preference
    pref.load()
    # top parameters
    page.title = "MY SDS"

    page.window.width = int(pref.data["window"]["width"])
    page.window.height = int(pref.data["window"]["height"])
    page.window.top = int(pref.data["window"]["top"])
    page.window.left = int(pref.data["window"]["left"])
    page.update()
    
    run_exec = ft.Text(pref.data["mmdagent_exec"])
    run_mdf = ft.Text(pref.data["mmdagent_mdf"])
    run_pycom = ft.Text(pref.data["mmdagent_python_command"])
    
    def run_mmdagent(e):
        command = [run_exec.value, run_mdf.value]
        env = os.environ.copy()
        env["WEBSOCKET_USE_CA_WEBSOCKET"] = "false"
        env["WEBSOCKET_SERVER"] = "localhost"
        env["WEBSOCKET_PORT"] = pref.data["websocket"]["server_port"]
        env["WEBSOCKET_CHANNEL"] = "/chat"
        env["MMDAGENT_FULLSCREEN"] = "false"
        g.mmdagent_process = subprocess.Popen(command, env=env)
        capture.start_ffmpeg()

    def pick_exec_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            a = e.files[0].path
            pref.data["mmdagent_exec"] = a
            pref.save()
            run_exec.value = a
            run_exec.update()
    def pick_mdf_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            a = e.files[0].path
            pref.data["mmdagent_mdf"] = a
            pref.save()
            run_mdf.value = a
            run_mdf.update()
    def pick_python_exec_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            a = e.files[0].path
            pref.data["mmdagent_python_command"] = a
            pref.save()
            run_pycom.value = a
            run_pycom.update()
    
    pick_exec_files_dialog = ft.FilePicker(on_result=pick_exec_file_result)
    pick_mdf_files_dialog = ft.FilePicker(on_result=pick_mdf_file_result)
    pick_python_exec_files_dialog = ft.FilePicker(on_result=pick_python_exec_file_result)
    page.overlay.append(pick_exec_files_dialog)
    page.overlay.append(pick_mdf_files_dialog)
    page.overlay.append(pick_python_exec_files_dialog)
    
    run_MMD = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        run_exec,
                        ft.FilledTonalButton(
                                "Choose...",
                                icon=ft.Icons.FILE_OPEN,
                                on_click=lambda _: pick_exec_files_dialog.pick_files(
                                    allow_multiple=False,
                                    allowed_extensions=["exe"]
                                ),
                        ),
                    ]
                ),
                ft.Row(
                    [
                        run_mdf,
                        ft.FilledTonalButton(
                                "Choose...",
                                icon=ft.Icons.FILE_OPEN,
                                on_click=lambda _: pick_mdf_files_dialog.pick_files(
                                    allow_multiple=False,
                                    allowed_extensions=["mdf"]
                                ),
                        ),
                    ]
                ),
                ft.Row(
                    [
                        run_pycom,
                        ft.FilledTonalButton(
                                "Choose or set python exec...",
                                icon=ft.Icons.FILE_OPEN,
                                on_click=lambda _: pick_python_exec_files_dialog.pick_files(
                                    allow_multiple=False,
                                    allowed_extensions=["exe"]
                                ),
                        ),
                    ]
                ),
                ft.FilledButton(
                    "Launch local MMDAgent-EX",
                    on_click=run_mmdagent
                )
            ]
        ),
        bgcolor=ft.Colors.ON_INVERSE_SURFACE,
        border=ft.border.all(1, ft.Colors.OUTLINE),
        padding=2,
        margin=2,
        border_radius=10,
    )
    
    def tab_selected(e):
        g.tab_index = tabs.selected_index
        # if g.tab_index == 3:
        #     video.volume = 100.0
        #     play_button.visible = False
        #     page.update()
        #     if websocket_comm_fix.read_txtfile():
        #         play_button.visible = True
        #     page.update()
        # else:
        #     video.volume = 0.0
    
    # キャプチャ画像の初期化
    img = ft.Image(width=800, height=800, src_base64=capture.load_external_image())
    
    tabs = ft.Tabs(
        selected_index=0,
        tabs=[
            ft.Tab(
                text="Settings",
                icon=ft.Icons.SETTINGS,
                content=ft.Container(
                    content=ft.Column(
                        [
                            run_MMD,
                        ]
                    )
                )
            ),
        ],
        expand=1,
        width=page.window.width - 40,
        height=page.window.height,
        on_change=tab_selected
    )
    
    page.add(
        ft.Container(
            content=ft.Row(
                [
                img,
                ft.Container(
                    content=ft.Column(
                        controls=[
                            tabs,
                        ],
                        alignment=ft.MainAxisAlignment.START
                    ),
                )
                ],
                vertical_alignment=ft.CrossAxisAlignment.START
            ),
        ),
    )
    page.update()
    threading.Thread(target=capture.mjpeg_reader, args=(img,), daemon=True).start()
    
if __name__ == "__main__":
    ft.app(target=gui_main)
