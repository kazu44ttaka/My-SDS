import json
from uuid import uuid4

# 設定ファイルのパス
user_setting_file = "settings.json"

# デフォルトの設定値
data_default = {
    # ウィンドウの設定
    "window" : {
        "width" : "1920",   # 幅
        "height" : "1200",  # 高さ 
        "top" : "0",        # 上端位置
        "left" : "0"        # 左端位置
    },
    # WebSocket接続の設定
    "websocket" : {
        "server_port" : "9001",      # サーバーポート
        "client_host" : "localhost", # クライアントホスト
        "client_port" : "8443"      # クライアントポート
    },
    # MMDAgentの設定
    "mmdagent_exec" : "D:\\MMDAgent-EX\\MMDAgent-EX.exe",  # 実行ファイルパス
    "mmdagent_mdf" : "test\\main.mdf",                     # MDFファイルパス
    "mmdagent_python_command" : "python.exe",              # Pythonコマンド
}

# 現在の設定データ
data = data_default

# 設定をJSONファイルに保存する
def save():
    global data
    with open(user_setting_file, 'w') as f:
        try:
            json.dump(data, f, indent=2)
        except Exception as e:
            print(e)

# 2つの辞書を再帰的にマージする 
def merge_dicts(base_dict, update_dict):
    for key, value in update_dict.items():
        if key in base_dict:
            if isinstance(base_dict[key], dict) and isinstance(value, dict):
                merge_dicts(base_dict[key], value)
            else:
                base_dict[key] = value
        else:
            base_dict[key] = value

# 設定ファイルから設定を読み込む
def load():
    global data
    try:
        with open(user_setting_file) as f:
            filedata = json.load(f)
            data = data_default
            merge_dicts(data, filedata)
            save()
    except FileNotFoundError:
        data = data_default

# UUIDを取得または生成する
def uuid():
    global data
    if "uuid" not in data:
        data["uuid"] = str(uuid4())
        save()
    return data["uuid"]
