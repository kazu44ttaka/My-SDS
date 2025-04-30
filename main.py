import ASR, GPT, threading, time, TTS
import numpy as np
import asyncio
import websockets
import re

# プロンプトを記載したファイルを指定
PROMPT_FILE = "prompt.txt"

with open(PROMPT_FILE) as f:
    sys_prompt = f.read()

# ChatGPTの出力から除去する絵文字を定義
emoji_pattern = re.compile(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        u"\U00002600-\U000026FF"
        u"\U00002500-\U00002BEF"
        "]+", flags=re.UNICODE)

if __name__ == "__main__":
    # MMD-Agentを用いるか
    use_MMD = False
    myASR = ASR.ASR()

    # ASR、マイクからの音声処理、VAD用のスレッドを定義
    threading.Thread(target=myASR.worker, daemon=True).start()
    threading.Thread(target=myASR.stream, daemon=True).start()
    threading.Thread(target=myASR.process_vad, daemon=True).start()

    myGPT = GPT.GPT()
    myGPT.init_prompt(sys_prompt=sys_prompt)
    
    # ターンテイキング用のスレッドを定義
    threading.Thread(target=myGPT.turn_taking, daemon=True, args=(myASR,)).start()

    myTTS = TTS.TTS()
    loop_voice_synth = asyncio.new_event_loop()

    def loop_runner(loop:asyncio.AbstractEventLoop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def server_main():
        await websockets.serve(myTTS.send_voice, "localhost", 9001)

    # 音声合成用のスレッドを定義
    threading.Thread(target=loop_runner, daemon=True, args=(loop_voice_synth,)).start()
    asyncio.run_coroutine_threadsafe(myTTS.init_model(), loop_voice_synth).result()
    
    if use_MMD:
        asyncio.run_coroutine_threadsafe(server_main(), loop_voice_synth).result()
    else:
        threading.Thread(target=myTTS.speak, daemon=True).start()

    while True:
        # ユーザーの発話を取得
        if not myASR.user_utterance.empty():
            user_utterance = myASR.user_utterance.get()
            print(user_utterance)
            myGPT.update_messages(user_utterance, "user")

        # ロボットがターンを取得したらGPTに渡してレスポンスを生成
        if myGPT.robot_turn:
            stream = myGPT.create_response()
            text_full = ""
            text_tmp = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content == None:
                    continue
                if  len(content) > 0 and content[-1] in set(["、", "。", "！", "？", "♪", "♡"]) and text_tmp != "":
                    if content[-1] in set(["！", "？"]):
                        text_tmp += content
                    print("Agent speak :", text_tmp)
                    asyncio.run_coroutine_threadsafe(myTTS.voice_synth(emoji_pattern.sub("、", text_tmp)), loop_voice_synth)
                    text_tmp = ""
                else:
                    text_tmp += content
                text_full += content
                # print(content, end="")
            if emoji_pattern.sub(r'', text_tmp) != "":
                print("Agent speak :", text_tmp)
                asyncio.run_coroutine_threadsafe(myTTS.voice_synth(emoji_pattern.sub("、", text_tmp)), loop_voice_synth)
            # print(text_full)
            myGPT.update_messages(text_full, "assistant")
            myGPT.robot_turn = False

        # print("latency :", myASR.audio_q.qsize() * (myASR.BLOCK / myASR.SAMPLE_RATE), "s")
        time.sleep(0.1)