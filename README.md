# Media Project Server

Speech to Text と Text to Speech 双方を扱うサーバをDockerベースで構築するプロジェクト。
また、カスタム辞書を登録する機能を有することとする。
基本的にOSSのみで構成するため、publicプロジェクトとして公開する。

## Getting Started

**準備中**

## 設計

### Speech to Text

WaveファイルをPOSTすると識別結果を返すAPIを実装する。

* Web API部分は、Flaskを用いて実装
* Speech to Text 部分は、[vosk](https://github.com/alphacep/vosk-api)を用いて実装

#### 調査

とにかく簡単にSSTできるソフトウェアを調査した

* deepspeech: 最近人気だが、日本語モデルで公開されているものが簡単に調べたものがない
* Google Cloud, AWS, Azure等のSST API: 無料枠はあるが、基本有料。使用量が高めであるため、採用が難しい
* vosk: kaldiベースの音声認識APIを提供するパッケージ。調査したOSS中では唯一日本語モデルを公開している。

### Text to Speech

Text to Speechに関しては、料金が比較的安価であるため、Google Cloud Text to Speech APIをそのまま利用する。
以下のコードを参考に構築する。

* https://github.com/dvdbisong/text-to-speech-cloud-run

### Lazy API Docs

* /tts: text to speech の機能をマッピングする
* /stt: speech to text の機能をマッピングする
* /dict: カスタム辞書編集機能をマッピングする




