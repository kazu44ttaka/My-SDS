import sounddevice as sd, numpy as np, queue, threading, time
from faster_whisper import WhisperModel
import silero_vad

class ASR:
    def __init__(self, model="large-v3", device="cuda", compute_type="int8_float16", model_size_or_path="deepdml/faster-whisper-large-v3-turbo-ct2", use_path=False):
        self.model = model                               # fast-Whisperのモデル指定
        self.model_size_or_path = model_size_or_path     # 同上
        self.device = device                             # 動作デバイス指定
        self.compute_type = compute_type                 # 演算精度指定
        self.SILENCE_TIME = 0.05                         # 発話の区切りを検出する秒数(秒)
        self.CHUNK_SEC = 3.0                             # ASRモデルに渡す秒数の最大値(秒)
        self.SAMPLE_RATE = 16000                         # サンプリングレート
        self.BLOCK = 320                                 # 1ブロック当たりのサンプル数
        self.VAD_SECONDS = 5                             # VADを実施する秒数(秒)
        self.vad_full = []                               # VAD_SECONDS秒のVAD結果を保存
        self.VAD_LEN = 0                                 # vadの長さ

        self.audio_q = queue.Queue()                     # マイクからの音声を保持するQueue
        self.audio2inf = queue.Queue()                   # 推論に回す音声を保持するQueue
        self.user_text = queue.Queue()                   # ASR結果のテキストを保持するQueue
        
        # Fast-whisperモデルを定義
        if use_path:
            self.whisper = WhisperModel(model_size_or_path=self.model_size_or_path, device=self.device, compute_type=self.compute_type)
        else:
            self.whisper = WhisperModel(model, device=self.device, compute_type=self.compute_type)

        # VADモデルを定義
        self.vad_model = silero_vad.load_silero_vad()

    # ASR
    def worker(self):
        buf_voice = []
        while True:
            segment = self.audio2inf.get()
            if len(segment) < self.SAMPLE_RATE * 0.5:
                continue
            segments, _ = self.whisper.transcribe(segment, 
                                                language="ja", 
                                                without_timestamps=True,
                                                beam_size=5)
            for seg in segments:
                # print(f"[{seg.start:.2f}-{seg.end:.2f}] {seg.text}")
                self.user_text.put(seg.text)
            buf_voice.clear()
            time.sleep(0.01)

    # VAD、発話区間だけをASRに渡す
    def process_vad(self):
        vad_count = 0
        buf_user = []
        user_utterance = []
        trigger = False
        num_vad = 5
        last_index = 0
        while True:
            data = self.audio_q.get()
            buf_user.append(data[:,0])
            buf_user = buf_user[- int(self.VAD_SECONDS / (self.BLOCK / self.SAMPLE_RATE)):]
            self.VAD_LEN = len(np.concatenate(buf_user))
            if vad_count > num_vad - 2:
                full = np.concatenate(buf_user)
                self.vad_full = silero_vad.get_speech_timestamps(
                    full, 
                    self.vad_model,  
                    sampling_rate=self.SAMPLE_RATE,
                    threshold=0.3,                          # VADの出力を音声と判断するしきい値
                    min_speech_duration_ms=150,              # 発話とみなす最短長（ミリ秒）
                    max_speech_duration_s=self.VAD_SECONDS, # 発話区間の最大長（秒）
                    min_silence_duration_ms=50,            # 区切りとみなす無音の最短長（ミリ秒）
                    window_size_samples=1024,               # 内部処理に使うウィンドウサイズ（サンプル数）
                    speech_pad_ms=150,                      # 出力範囲の前後に付け足すバッファ時間（ミリ秒）
                    )
                if len(self.vad_full) > 0:
                    for i in range(len(self.vad_full)):
                        start_index = (int(self.vad_full[i]["start"]) // self.BLOCK) * self.BLOCK
                        end_index = ((int(self.vad_full[i]["end"]) - 1) // self.BLOCK + 1) * self.BLOCK - 1
                        if end_index > len(full) - self.BLOCK * num_vad:
                            if len(user_utterance) == 0 and start_index > last_index:
                                user_utterance.append(full[start_index:end_index])
                            else:
                                user_utterance.append(full[max(start_index, len(full) - self.BLOCK * num_vad):end_index])
                            last_index = end_index
                        else:
                            last_index -= self.BLOCK * num_vad
                    if len(full) - self.vad_full[-1]["end"] > self.SAMPLE_RATE * self.SILENCE_TIME:
                        trigger = True
                    else:
                        trigger = False
                else:
                    last_index -= self.BLOCK * num_vad
                    trigger = False
                
                if len(user_utterance) > 0:
                    if trigger or len(np.concatenate(user_utterance)) >= self.SAMPLE_RATE * self.CHUNK_SEC:
                        self.audio2inf.put(np.concatenate(user_utterance))
                        user_utterance.clear()
                        trigger = False
                vad_count = 0
            else:
                vad_count += 1

    # マイクからの音声をQueueに保持
    def callback(self, indata, frames, t, status):
        if status: 
            print(status)
        self.audio_q.put(indata.copy())
    
    # マイクからの音声を処理するループ
    def stream(self):
        with sd.InputStream(channels=1,
                            samplerate=self.SAMPLE_RATE,
                            blocksize=self.BLOCK,
                            dtype='float32',
                            latency='low',
                            callback=self.callback):
            print("Listening... Ctrl+C to stop.")
            while True: 
                # if self.audio_q.qsize() > 0:
                #     print("qsize :", self.audio_q.qsize(), "*", self.audio_q.queue[0].shape)
                time.sleep(0.5)

# if __name__ == "__main__":
#     myASR = ASR()
    
#     threading.Thread(target=myASR.worker, daemon=True).start()
#     threading.Thread(target=myASR.stream, daemon=True).start()
#     threading.Thread(target=myASR.process_vad, daemon=True).start()
    
#     while True:
#         print("latency :", myASR.audio_q.qsize() * (myASR.BLOCK / myASR.SAMPLE_RATE), "s")
#         time.sleep(1)
        