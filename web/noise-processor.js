/**
 * ノイズ生成コア + AudioWorkletProcessor。
 *
 * アルゴリズムは noise_engine.py の移植（そちらが正本）。
 * 対応関係:
 *   NoiseCore#_brown   <- _brown_noise()
 *   NoiseCore#_pink    <- _pink_noise()
 *   NoiseCore#_bass    <- _bass_shape()
 *
 * このファイルは2つの文脈で読み込まれる:
 *   1. AudioWorklet   -> registerProcessor が存在するので NoiseProcessor を登録する
 *   2. メインスレッド -> NoiseCore だけを import し、正規化ゲインの実測に使う
 */

export const SAMPLE_RATE = 44100;

/** シード指定時に使う PRNG。Python の random.Random とは別物なので波形は一致しない。 */
function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

/**
 * 1サンプルずつノイズを生成する。状態を持ち続けるので、
 * バッファを繰り返さずに無限に生成できる（= ループの継ぎ目が存在しない）。
 */
export class NoiseCore {
  constructor(params = {}) {
    this.setParams(params);
    this.reset(params.seed);
  }

  setParams({ kind, step, damping, smooth, bass } = {}) {
    if (kind !== undefined) this.kind = kind;
    // clamp 範囲は noise_engine.py の _brown_noise / _bass_shape に合わせる
    if (step !== undefined) this.step = step;
    if (damping !== undefined) this.damping = clamp(damping, 0, 0.9999);
    if (smooth !== undefined) this.smooth = clamp(smooth, 0.001, 1);
    if (bass !== undefined) this.bass = bass;

    const amount = clamp(this.bass ?? 0, 0, 1.5);
    this._bassEnabled = this.kind !== 'white' && (this.bass ?? 0) > 0;
    this._lowMix = Math.min(0.92, 0.35 + amount * 0.38);
    this._cutoff = clamp(0.08 / Math.max(0.2, amount), 0.005, 0.15);
  }

  /** 生成状態を初期化する。seed 未指定なら Math.random を使う。 */
  reset(seed) {
    this._rand = seed === undefined || seed === null ? Math.random : mulberry32(seed);
    // brown
    this._value = 0;
    this._smoothed = 0;
    // pink (Voss-McCartney)
    this._rows = new Float64Array(16);
    this._runningSum = 0;
    this._counter = 0;
    // bass shaping
    this._low = 0;
  }

  /** [-1, 1) の一様乱数 */
  _uniform() {
    return this._rand() * 2 - 1;
  }

  _brown() {
    this._value += this._uniform() * this.step;
    this._value *= this.damping;
    this._smoothed += (this._value - this._smoothed) * this.smooth;
    return this._smoothed;
  }

  _pink() {
    this._counter += 1;
    const counter = this._counter;
    // _trailing_zeros(): 最下位ビットの位置。
    // counter が 2^32 の倍数だと & が 32bit に丸められて 0 になり zeros = -1 になる。
    // Python 版は 32 を返して弾かれる分岐なので、ここでも同様にスキップする
    // （踏まないと rows[-1] が undefined で runningSum が NaN のまま戻らなくなる）。
    const zeros = 31 - Math.clz32(counter & -counter);
    if (zeros >= 0 && zeros < this._rows.length) {
      this._runningSum -= this._rows[zeros];
      this._rows[zeros] = this._uniform();
      this._runningSum += this._rows[zeros];
    }
    return (this._runningSum + this._uniform()) / (this._rows.length + 1);
  }

  _bassShape(sample) {
    this._low += (sample - this._low) * this._cutoff;
    return sample * (1 - this._lowMix) + this._low * this._lowMix;
  }

  /** 正規化前の生サンプルを1つ返す。音量調整は呼び出し側（GainNode）の責務。 */
  next() {
    let sample;
    if (this.kind === 'white') {
      sample = this._uniform();
    } else if (this.kind === 'pink') {
      sample = this._pink();
    } else {
      sample = this._brown();
    }
    return this._bassEnabled ? this._bassShape(sample) : sample;
  }

  fill(channel) {
    for (let i = 0; i < channel.length; i += 1) {
      channel[i] = this.next();
    }
  }
}

if (typeof registerProcessor === 'function') {
  class NoiseProcessor extends AudioWorkletProcessor {
    constructor(options) {
      super();
      this.core = new NoiseCore(options.processorOptions ?? {});
      // 再生を止めずにスライダーを反映するための経路
      this.port.onmessage = (event) => this.core.setParams(event.data);
    }

    process(_inputs, outputs) {
      this.core.fill(outputs[0][0]);
      return true;
    }
  }

  registerProcessor('noise-processor', NoiseProcessor);
}
