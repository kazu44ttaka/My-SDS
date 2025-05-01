# My-SDS
faster-Whisper、ChatGPT API、VOICEVOX coreを組み合わせた音声対話システムです。ASR、TTSをローカル環境で動かし、高速なレスポンス生成を実現しています。
 
# 想定環境
- Windows OS
- それなりのスペックをもったデスクトップPC
  + Intel 第13世代以上かそれに相当するCPU
  + VRAM 6GB以上のNVIDIA製GPU
- CUDA 12.6以上
  + 対応するcuDNNもインストールしてください
  + 11.xは動かない可能性が高いです

# インストール
※各モデルのライセンスに関しては対応するgit レポジトリを参照してください。
### クローン
まず、レポジトリをローカル環境へクローンしましょう。

```bash
git clone https://github.com/kazu44ttaka/My-SDS
```

お好みのPython仮想環境上にrequirements.txtに書かれているパッケージをインストールしてください。

Pytorchに関してはrequirements.txtに書かれていないので、ご自身のCUDA環境にあったバージョンを手動でインストールしてください。

https://pytorch.org/

私の場合はCUDA 12.6なので、以下のようにPytorchをインストールします。

```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

### faster-Whisperのセットアップ
ASRにはfaster-Whisperというものを使います。

https://github.com/SYSTRAN/faster-whisper

こちらは高性能ASRモデルであるWhisperをリアルタイム動作用にカスタマイズしたもので、これを用いればローカル環境で高速かつ高性能なASRを実現できます。

セットアップといってもやることは一つで、対応するPython ライブラリのインストールです。

```bash
pip install git+https://github.com/guillaumekln/faster-whisper.git
```

初回動作時に指定されたモデルが自動でダウンロードされます。

### VOICEVOX coreのセットアップ
TTSにはVOICEVOX coreというものを使います。

https://github.com/VOICEVOX/voicevox_core

こちらは有名なVOICEVOXという読み上げソフトウェアの音声合成コアで、ローカル環境で高速に音声合成を行うことができます。
以下の作業を[インストールガイド](https://github.com/VOICEVOX/voicevox_core/blob/main/docs/guide/user/usage.md)を見ながら行ってください。

Windows版のダウンローダをReleasesからダウンロード、先ほどクローンした場所(C: \\...\My-SDS)に配置し、それを起動してVOICEVOX coreのインストールを行ってください。
インストールが完了したら以下のようにvoicevox_coreというファイルが生成されていると思います。

![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2524638/b29ea33e-4dde-49e3-827d-902c8d419b28.png)

次に、対応するVOICEVOX coreのPython ライブラリをpipでインストールしてください。執筆時点での最新バージョンは0.16.0ですので、この場合のpipコマンドは以下のようになります。

```bash
pip install https://github.com/VOICEVOX/voicevox_core/releases/download/0.16.0/voicevox_core-0.16.0-cp310-abi3-win_amd64.whl
```

ここまででTTSのセットアップは完了です。

# 諸準備
### プロンプトファイルの指定
レポジトリをクローンした場所(C: \\...\My-SDS)にChatGPTに与えるプロンプトを書いたテキストファイルをおいてください。ファイル名は例えば`prompt.txt`などとし、下記のように`main.py`の冒頭で指定してください。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2524638/133b5b9d-a2a0-4329-a5d9-204ac13dcd0a.png)

たとえば、プロンプトの例は以下のようになります。
```prompt.txt
あなたはユーザーと雑談を楽しむカジュアルな会話パートナーです。
口語的な自然な日本語で話し、短いフレーズで返答してください。
質問には答えすぎず、会話が続くようにユーザーにも質問を返してください。
表情豊かな語り口で、親しみやすさを重視してください。

以下から会話が始まります。
```
### OpenAI API keyの指定
先ほどと同じ場所に、OpenAIから発行されるAPI Keyを格納したテキストファイルをおいてください。Keyの発行方法などは別途記事を参照してください。ファイル名は例えば`key.txt`などとし、下記のように`GPT.py`の冒頭で指定してください。
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/2524638/c111cf6b-772e-4dd0-b651-95759c117eae.png)

# 実行
`main.py`がメインプログラムになっています。これを実行し、以下のように`Listening... Ctrl+C to stop.`と表示されたら話しかけます。

↓動作例(音が出ます)

https://www.youtube.com/embed/XXmTUK0o3Pg?si=ju7k5aHi7PIIrEB4

CV：VOICEVOX、春日部つむぎ

# 使用ライブラリ
https://github.com/SYSTRAN/faster-whisper

https://github.com/VOICEVOX/voicevox_core

https://github.com/snakers4/silero-vad
