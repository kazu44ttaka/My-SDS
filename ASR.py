import sounddevice as sd, numpy as np, queue, threading, time
from faster_whisper import WhisperModel
import silero_vad

class ASR:
    def __init__(self, model="large-v3", device="cuda", compute_type="int8_float16", model_size_or_path="deepdml/faster-whisper-large-v3-turbo-ct2", use_path=False):
        self.model = model                               # fast-Whisperのモデル指定
        self.model_size_or_path = model_size_or_path     # 同上
        self.device = device                             # 動作デバイス指定
        self.compute_type = compute_type                 # 演算精度指定
        self.SILENCE_TIME = 0.1                          # 発話の区切りを検出する秒数(秒)
        self.CHUNK_SEC = 2.5                             # ASRモデルに渡す秒数の間隔(秒)
        self.SAMPLE_RATE = 16000                         # サンプリングレート
        self.BLOCK = 320                                 # 1ブロック当たりのサンプル数
        self.VAD_LEN = 10                                # VADを実施する秒数(秒)
        self.buf_user = []                               # 過去VAD_LEN秒間のユーザーの音声を保存する
        self.vad_full = []                               # VAD_LEN秒のVAD結果を保存

        self.audio_q = queue.Queue()                     # マイクからの音声を保持するQueue
        self.user_utterance = queue.Queue()              # ASR結果のテキストを保持するQueue
        
        # Fast-whisperモデルを定義
        if use_path:
            self.whisper = WhisperModel(model_size_or_path=self.model_size_or_path, device=self.device, compute_type=self.compute_type)
        else:
            self.whisper = WhisperModel(model, device=self.device, compute_type=self.compute_type)

        # VADモデルを2つ定義(ASR用とターンテイキング用)
        self.vad_model1 = silero_vad.load_silero_vad()
        self.vad_model2 = silero_vad.load_silero_vad()

    # ASR
    def worker(self):
        buf_tmp = []
        buf_voice = []
        trigger = False
        vad_count = 0
        vad = []
        while True:
            data = self.audio_q.get()
            self.buf_user.append(data[:,0])
            self.buf_user = self.buf_user[- int(self.VAD_LEN / (self.BLOCK / self.SAMPLE_RATE)):]

            buf_tmp.append(data[:,0])
            # 音声がある程度溜まったら処理開始
            if len(buf_tmp) < 1.0 / (self.BLOCK / self.SAMPLE_RATE):
                continue

            # 5回に1回vad処理
            vad_count += 1
            if vad_count > 5:
                full = np.concatenate(buf_tmp)
                vad = silero_vad.get_speech_timestamps(
                    full, 
                    self.vad_model1,  
                    sampling_rate=self.SAMPLE_RATE,
                    threshold=0.5,                      # VADの出力を音声と判断するしきい値
                    min_speech_duration_ms=150,         # 発話とみなす最短長（ミリ秒）
                    max_speech_duration_s=self.VAD_LEN, # 発話区間の最大長（秒）
                    min_silence_duration_ms=50,         # 区切りとみなす無音の最短長（ミリ秒）
                    window_size_samples=1024,           # 内部処理に使うウィンドウサイズ（サンプル数）
                    speech_pad_ms=100,                  # 出力範囲の前後に付け足すバッファ時間（ミリ秒）
                    )
                vad_count = 0

                # 有音区間だけを推論に回す
                if len(vad) > 0:
                    for i in range(len(vad)):
                        buf_voice.append(full[int(vad[i]["start"]):int(vad[i]["end"])])
                    if len(full) - vad[-1]["end"] > self.SAMPLE_RATE * self.SILENCE_TIME:
                        trigger = True
                else:
                    buf_tmp.clear()

            # バッファが一定秒数に達したら or 無音区間を検出したら推論
            if trigger or (len(np.concatenate(buf_voice))  if len(buf_voice) > 0 else len(buf_voice)) >= self.SAMPLE_RATE * self.CHUNK_SEC:
                segment = np.concatenate(buf_voice)
                buf_tmp.clear()

                segments, _ = self.whisper.transcribe(segment, 
                                                      language="ja", 
                                                      without_timestamps=True,
                                                      beam_size=5)
                for seg in segments:
                    # print(f"[{seg.start:.2f}-{seg.end:.2f}] {seg.text}")
                    self.user_utterance.put(seg.text)
                trigger = False

            buf_voice.clear()

    # ターンテイキング用のVAD
    def process_vad(self):
        while True:
            if len(self.buf_user) > 0:
                self.vad_full = silero_vad.get_speech_timestamps(
                np.concatenate(self.buf_user), 
                self.vad_model2,  
                sampling_rate=self.SAMPLE_RATE,
                threshold=0.5,                      # VADの出力を音声と判断するしきい値
                min_speech_duration_ms=150,         # 発話とみなす最短長（ミリ秒）
                max_speech_duration_s=self.VAD_LEN, # 発話区間の最大長（秒）
                min_silence_duration_ms=50,         # 区切りとみなす無音の最短長（ミリ秒）
                window_size_samples=1024,           # 内部処理に使うウィンドウサイズ（サンプル数）
                speech_pad_ms=100,                  # 出力範囲の前後に付け足すバッファ時間（ミリ秒）
                )

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
    
#     while True:
#         print("latency :", myASR.audio_q.qsize() * (myASR.BLOCK / myASR.SAMPLE_RATE), "s")
#         time.sleep(1)
        