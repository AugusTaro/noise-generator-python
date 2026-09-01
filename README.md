# noise-generator-python

ブラウンノイズ・ピンクノイズ等を生成するツール。**ブラウザ版**と **Python 版**の2実装がある。

| | 用途 | 実行環境 |
| --- | --- | --- |
| **ブラウザ版** (`web/`) | 聴く。継ぎ目なしで流しっぱなしにする | 静的ホスティングのみ（サーバー不要） |
| **Python 版** (ルート) | WAV ファイルを作る | Python / Streamlit |

生成アルゴリズムは同一で、`noise_engine.py` が正本。`web/noise-processor.js` はその移植。

## 構成

| ファイル | 役割 |
| --- | --- |
| `noise_engine.py` | ノイズ生成・WAV 書き出しの共通ロジック（プリセット定義含む） |
| `generate_brown_noise.py` | デフォルトプリセット（brown_deep / 60秒）の WAV を生成する CLI |
| `noise_ui.py` | パラメータを調整しながら生成・プレビューできる Streamlit UI |
| `web/index.html` | ブラウザ版の UI・再生制御・WAV 書き出し |
| `web/noise-processor.js` | 生成アルゴリズム（`AudioWorkletProcessor`） |

## ブラウザ版

```bash
python3 -m http.server -d web 8000
# => http://localhost:8000
```

ビルド不要・依存ゼロ。`web/` をそのまま静的ホスティングに置ける。

`AudioWorkletNode` で**1サンプルずつリアルタイム生成**しているため、音声ファイルを繰り返しているわけではない。したがって再生し続けても波形が一巡せず、**ループの継ぎ目でクリックノイズが鳴らない**。再生を止めずにパラメータを変更できる。

WAV の書き出しも `OfflineAudioContext` を使ってブラウザ内で完結する。

> **注意**: `AudioWorklet` はセキュアコンテキストを要求するため、`index.html` を `file://` で直接開くと動かない。上記のように `http://localhost` 経由で表示すること。

## Python 版

### セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### CLI

```bash
python generate_brown_noise.py
# => brown_noise_60s_deeper.wav を生成
```

`noise_engine.py` のみ標準ライブラリで動くため、CLI だけなら依存インストールは不要。

### Streamlit UI

```bash
streamlit run noise_ui.py
```

プリセット選択・duration / amplitude / step / damping / smooth / bass の調整・プレビュー再生・WAV ダウンロードができる。

## 仕様メモ

- サンプルレート: 44,100 Hz
- 最大長: 600 秒（Python 版）/ 300 秒（ブラウザ版の書き出し）

### 2実装の差分

- **音量の正規化**: `noise_engine.py` の `_normalize()` は全サンプル生成後にピークで割る。ブラウザ版の**再生**は終端のないストリームで全体のピークが取れないため、同じ生成コードを3秒ぶん回してピークを実測し、そのゲインを `GainNode` に与えている。推定を超えたピークは末尾の `WaveShaperNode`（閾値以下は素通しのソフトクリップ）で受ける。`DynamicsCompressorNode` は仕様上メイクアップゲインが常時かかり、この正規化を崩すため使っていない。ブラウザ版の**書き出し**は全バッファが手に入るので、Python 版と同一のピーク正規化を行う
- **シード**: 疑似乱数のアルゴリズムが異なる（Python は `random.Random`、ブラウザ版は mulberry32）ため、同じシードを指定しても両者の波形は一致しない
