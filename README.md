# noise-generator-python

ブラウンノイズ・ピンクノイズ等を生成する Python ツール。CLI と Streamlit UI の 2 通りで使える。

## 構成

| ファイル | 役割 |
| --- | --- |
| `noise_engine.py` | ノイズ生成・WAV 書き出しの共通ロジック（プリセット定義含む） |
| `generate_brown_noise.py` | デフォルトプリセット（brown_deep / 60秒）の WAV を生成する CLI |
| `noise_ui.py` | パラメータを調整しながら生成・プレビューできる Streamlit UI |

## セットアップ

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使い方

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
- 最大長: 600 秒
