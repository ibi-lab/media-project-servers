# Media Project Server

Speech to Text と Text to Speech 双方を扱うサーバをDockerベースで構築するプロジェクト。
また、カスタム辞書を登録する機能を有することとする。
基本的にOSSのみで構成するため、publicプロジェクトとして公開する。

## Getting Started

### 前提

自分のパソコンで実行する場合はパソコンの実行環境にPythonの実行環境がインストールされていること、
Google Cloud Runやコンテナ実行をする場合は、Dockerがインストールされていることが必要である。

* https://www.python.org/downloads/
* https://www.docker.com/products/docker-desktop/

また、Google Text to Speech APIを利用するため、Google Cloud Platformのアカウントを作成し、
その中でサービスアカウントの発行、共有鍵の発行を行なっている必要がある。
共有鍵はjson形式でダウンロードし、```media-project-credential.json```という名前でリネームし、
プロジェクトトップに配置すること。

* https://cloud.google.com/docs/authentication/production?hl=ja

### 自分のパソコンで実行する場合

pipで必要なパッケージをインストールして、app.pyを実行してください

```
$ pip install -r requirements.txt
$ bash ./setup.sh
$ python ./app.py
```

setup.shでは、voskの日本語モデルのダウンロードを行う。
無事に実行ができると、3000番ポートで待ち受けが発生しますので、以下のいずれかでアクセスできるはずである。

* http://127.0.0.1:3000/tts
* http://127.0.0.1:3000/stt

## Dockerでビルドする場合

Dockerでビルドする場合は、以下のコマンドを実行する

```
$ docker build -t media-project-server .
```

なお、タグは他のタグ名をつけても構わない。ビルドが成功すると、イメージ一覧にmedia-project-server:latestという
イメージが確認できる。

```
% docker images
REPOSITORY              TAG       IMAGE ID       CREATED       SIZE
media-project-server    latest    70c2f2c6e435   2 days ago    1.12GB
...
```

なお、ビルド時にvoskの日本語モデルをインストールするプロセスが入るため、それなりの時間がかかる。
テザリング環境ではなく、インターネット接続環境で実施すること。

ビルドしたイメージの実行は以下のようにすると良い、

```
$ docker run --rm -it -p 3000:3000 media-project-server:latest
```

Docker Desktopを用いている場合は、パソコンで実行した場合と同様のURLでアクセスできる。

* http://127.0.0.1:3000/tts
* http://127.0.0.1:3000/stt

他のDocker Serverで実行した場合はホストIPを指定のものに置き換えること。

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




