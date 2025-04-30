from openai import OpenAI
import queue
import time
import numpy as np
import ASR

# ChatGPTのkeyが書かれたファイルを指定
KEY_FILE = "key.txt"

with open(KEY_FILE, "r", encoding="utf-8_sig") as f:
    api_key = f.readline().strip()

class GPT:
    def __init__(self, model="gpt-3.5-turbo", context_len=20):
        self.api_key = api_key                     # API Keyを指定
        self.model = model                         # Chat GPTのモデルを指定
        self.client = OpenAI(api_key=self.api_key) # クライアントを初期化
        self.context_len = context_len             # GPTに送る会話数
        self.robot_turn = False                    # ロボットのターンを制御
        self.SAMPLE_RATE = 16000                   # サンプリングレート
        self.MAX_SILENCE_TIME = 0.3                # ユーザーが話し終わってからエージェントが話し出すまでの時間(秒)
        
        self.robot_utterance = queue.Queue()       # ロボットの発話を管理するQueue

    # 発話をストリームとして生成
    def create_response(self):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True
        )
        return stream

    # プロンプトを初期化
    def init_prompt(self, sys_prompt):
        self.messages = [
            {"role": "system", "content": sys_prompt},
        ]

    # プロンプトを更新
    def update_messages(self, message, role):
        if len(self.messages) > self.context_len + 1:
            self.messages = [self.messages[0]] + self.messages[2:] + [{"role": role, "content": message}]
        else:
            self.messages.append({"role": role, "content": message})
        return self.messages

    # ロボットがターンを取るかどうか
    def turn_taking(self, ASR:ASR):
        while True:
            if not self.messages[-1]["role"] == "assistant":
                if len(ASR.vad_full) > 0:
                    if len(np.concatenate(ASR.buf_user)) - ASR.vad_full[-1]["end"] > self.SAMPLE_RATE * self.MAX_SILENCE_TIME:
                        self.robot_turn = True
                else:
                    self.robot_turn = False
            time.sleep(0.5)

# if __name__ == "__main__":
#     messages = [
#         {"role": "system", "content": sys_prompt},
#         {"role": "user", "content": "おはよう！"},
#     ]

#     myGPT = GPT()
#     stream = myGPT.create_response(messages)

#     for chunk in stream:
#         # print(chunk)
#         content = chunk.choices[0].delta.content
#         print(content)