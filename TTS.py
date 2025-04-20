import multiprocessing

from voicevox_core.asyncio import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile
import queue
import sounddevice as sd
import soundfile as sf
import io
import time

class TTS:
    def __init__(self, speakerID=8, onnxruntime_file="voicevox_core/onnxruntime/lib/voicevox_onnxruntime.dll", OpenJtalk_dict="voicevox_core/dict/open_jtalk_dic_utf_8-1.11", mode="AUTO", vvm="voicevox_core/models/vvms/0.vvm"):
        self.speakerID = speakerID
        self.q_audio = queue.Queue()
        self.onnxruntime_file = onnxruntime_file
        self.OpenJtalk_dict = OpenJtalk_dict
        self.mode = mode
        self.vvm = vvm

    async def init_model(self):
        ort = await Onnxruntime.load_once(filename=self.onnxruntime_file)
        ojt = await OpenJtalk.new(self.OpenJtalk_dict)
        self.synthesizer = Synthesizer(
            ort,
            ojt,
            acceleration_mode=self.mode,
            cpu_num_threads=max(
                multiprocessing.cpu_count(), 2
            ),  # https://github.com/VOICEVOX/voicevox_core/issues/888
        )
        async with await VoiceModelFile.open(self.vvm) as model:
            await self.synthesizer.load_voice_model(model)
    
    async def voice_synth(self, text):
        
        # クエリ生成
        query = await self.synthesizer.create_audio_query(text, self.speakerID)
        # 合成
        audio = await self.synthesizer.synthesis(query, self.speakerID)
        
        self.q_audio.put(audio)

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

# if __name__ == "__main__":
    
#     myTTS = TTS()
#     threading.Thread(target=myTTS.speak, daemon=True).start()
    
#     myTTS.voice_synth_async("こんにちは")
    
#     while True:
#         time.sleep(0.5)
    