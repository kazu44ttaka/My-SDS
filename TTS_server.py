import requests
import sounddevice as sd
import soundfile as sf
import io
import threading
import queue
import time

# VoiceVoxをローカルホストでサーバーとして構築し、音声合成する
# 音声合成される順番がバラバラなので非推奨
class TTS:
    def __init__(self, speakerID=1):
        self.speakerID = speakerID
        self.q_audio = queue.Queue()

    def voice_synth(self, text):
        # クエリ生成
        query = requests.post(
            "http://localhost:50021/audio_query",
            params={"text": text, "speaker": self.speakerID}
        )
        query.raise_for_status()
        
        query_json = query.json()
        # query_json["speedScale"] = 1.25        # 速く話す

        # 合成
        audio = requests.post(
            "http://localhost:50021/synthesis",
            params={"speaker": self.speakerID},
            json=query_json
        )
        audio.raise_for_status()

        self.q_audio.put(audio.content)
    
    def voice_synth_async(self, text):
        threading.Thread(target=self.voice_synth, daemon=True, args=(text,)).start()

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
            time.sleep(0.5)