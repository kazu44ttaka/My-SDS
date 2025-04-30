import multiprocessing

from voicevox_core.asyncio import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
import queue
import sounddevice as sd
import soundfile as sf
import io
import time
import asyncio
import threading
import websockets
import librosa

class TTS:
    def __init__(self, speakerID=8, onnxruntime_file="voicevox_core/onnxruntime/lib/voicevox_onnxruntime.dll", OpenJtalk_dict="voicevox_core/dict/open_jtalk_dic_utf_8-1.11", mode="CPU", vvm="voicevox_core/models/vvms/0.vvm"):
        self.speakerID = speakerID               # speaker IDを指定
        self.q_audio = queue.Queue()             # エージェントの音声を管理するQueue
        self.onnxruntime_file = onnxruntime_file # onnxruntime_fileを指定
        self.OpenJtalk_dict = OpenJtalk_dict     # OpenJtalk_dictを指定
        self.mode = mode                         # 動作デバイスを指定
        self.vvm = vvm                           # vvmモデルを指定

    # 音声合成モデルを初期化
    async def init_model(self):
        ort = await Onnxruntime.load_once(filename=self.onnxruntime_file)
        ojt = await OpenJtalk.new(self.OpenJtalk_dict)
        self.synthesizer = Synthesizer(
            ort,
            ojt,
            acceleration_mode=self.mode,
            cpu_num_threads=max(
                multiprocessing.cpu_count(), 2
            ),
        )
        async with await VoiceModelFile.open(self.vvm) as model:
            await self.synthesizer.load_voice_model(model)
    
    # 音声合成
    async def voice_synth(self, text):
        
        # クエリ生成
        query = await self.synthesizer.create_audio_query(text, self.speakerID)
        # 合成
        audio = await self.synthesizer.synthesis(query, self.speakerID)
        
        self.q_audio.put(audio)

    # エージェントの音声を再生するループ
    def speak(self):
        while True:
            if not self.q_audio.empty():
                audio = self.q_audio.get()
                
                # メモリ上のWAVデータを直接再生
                audio_bytes = io.BytesIO(audio)
                
                # soundfileで読み込み → sounddeviceで再生
                with sf.SoundFile(audio_bytes) as f:
                    data = f.read(dtype='float32')
                    sd.play(data, f.samplerate)
                    sd.wait()
            time.sleep(0.05)

    # MMD-Agentに音声を送信
    async def send_voice(self, ws:websockets.ServerConnection):
        chunk_samples = 2048
        while True:
            if not self.q_audio.empty():
                await ws.send("__AV_START\n")
                await ws.send("__AV_SETMODEL,0\n")
                audio = self.q_audio.get()
                audio_bytes = io.BytesIO(audio)
                
                with sf.SoundFile(audio_bytes) as f:
                    data = f.read(dtype='float32')  # 16bit signed integer
                    samplerate = f.samplerate
                
                data_16k = librosa.resample(data, orig_sr=samplerate, target_sr=16000)
                pcm_bytes = (data_16k * 20000).astype('int16').tobytes()

                pos = 0
                while pos < len(pcm_bytes):
                    chunk = pcm_bytes[pos:pos + chunk_samples]
                    chunk_len = len(chunk)
                    header = f"SND{chunk_len:04}".encode("ascii")
                    payload = header + chunk
                    if chunk != b'':
                        await ws.send(payload)
                    pos += chunk_samples
                    await asyncio.sleep(0.01)  # 遅延を入れてスムーズに送信（調整可）

            await asyncio.sleep(0.1)

# if __name__ == "__main__":
    
#     myTTS = TTS()
#     loop = asyncio.new_event_loop()

#     def loop_runner():
#         asyncio.set_event_loop(loop)
#         loop.run_forever()

#     threading.Thread(target=loop_runner, daemon=True).start()
#     asyncio.run_coroutine_threadsafe(myTTS.init_model(), loop).result()

#     threading.Thread(target=myTTS.speak, daemon=True).start()
    
#     asyncio.run_coroutine_threadsafe(myTTS.voice_synth("こんにちは！"), loop)
    
#     while True:
#         time.sleep(1.0)
    