# Media Project Server

Speech to Text と Text to Speech 双方を扱うサーバをDockerベースで構築するプロジェクト。
また、カスタム辞書を登録する機能を有することとする。
基本的にOSSのみで構成するため、publicプロジェクトとして公開する。

## Speech to Text

WaveファイルをPOSTすると識別結果を返すAPIを実装する。

* Web API部分は、Flaskを用いて実装
* Speech to Text 部分は、voskを用いて実装

## Text to Speech

まだ未実装