import ASR, GPT, threading, time, TTS
import numpy as np
import asyncio

PROMPT_FILE = "prompt.txt"

with open(PROMPT_FILE) as f:
    sys_prompt = f.read()

if __name__ == "__main__":
    myASR = ASR.ASR()

    threading.Thread(target=myASR.worker, daemon=True).start()
    threading.Thread(target=myASR.stream, daemon=True).start()
    threading.Thread(target=myASR.process_vad, daemon=True).start()

    myGPT = GPT.GPT()
    myGPT.init_prompt(sys_prompt=sys_prompt)

    myTTS = TTS.TTS()
    asyncio.run(myTTS.init_model())

    threading.Thread(target=myTTS.speak, daemon=True).start()

    while True:
        myGPT.vad_to_robot_turn(myASR.vad_full, len(np.concatenate(myASR.buf_user)))

        if not myASR.user_utterance.empty():
            user_utterance = myASR.user_utterance.get()
            print(user_utterance)
            myGPT.update_messages(user_utterance, "user")

        if myGPT.robot_turn:
            stream = myGPT.create_response()
            text_full = ""
            text_tmp = ""
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content == None:
                    print()
                    break
                text_full += content
                if len(content) > 0 and content[-1] in set(["、", "。", "！", "？", "♪"]) and text_tmp != "":
                    text_tmp += content
                    print("speak :", text_tmp)
                    asyncio.run(myTTS.voice_synth(text_tmp))
                    text_tmp = ""
                else:
                    text_tmp += content
                # print(content, end="")
            myGPT.update_messages(text_full, "assistant")
            myGPT.robot_turn = False

        # print("latency :", myASR.audio_q.qsize() * (myASR.BLOCK / myASR.SAMPLE_RATE), "s")
        time.sleep(0.5)