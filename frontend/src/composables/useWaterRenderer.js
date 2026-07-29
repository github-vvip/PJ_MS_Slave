// WebGL 水面渲染器 v3：俯视海水 + GPU 波动方程交互涟漪
// 双 pass：模拟 pass（ping-pong FBO 解算波动方程）+ 渲染 pass（海域/碎波/泡沫）
// 原生 WebGL1，零依赖。半浮点纹理不可用时自动回退 RGBA8 编码。

const MAX_DROPS = 4 // 每帧最多注入的扰动数

const VERT_SRC = `
attribute vec2 a_pos;
void main() { gl_Position = vec4(a_pos, 0.0, 1.0); }
`

// ---- 波动方程模拟 pass ----
// 纹理 RG 通道打包：R=当前高度 G=上帧高度，ping-pong 交换
const SIM_FS = `
precision highp float;

uniform sampler2D u_wave;
uniform vec2  u_simRes;
uniform vec4  u_drops[${MAX_DROPS}]; // x,y (sim 像素), 半径, 强度
uniform float u_damping;

float decodeH(float v) {
#ifdef HFLOAT
  return v;
#else
  return v * 2.0 - 1.0;
#endif
}

float readH(vec4 t) {
  return decodeH(t.r);
}

float encodeH(float h) {
#ifdef HFLOAT
  return h;
#else
  return clamp(h, -1.0, 1.0) * 0.5 + 0.5;
#endif
}

void main() {
  vec2 uv = gl_FragCoord.xy / u_simRes;
  vec2 texel = 1.0 / u_simRes;
  vec4 c = texture2D(u_wave, uv);
  float curr = decodeH(c.r);
  float prev = decodeH(c.g);
  float l = readH(texture2D(u_wave, uv - vec2(texel.x, 0.0)));
  float r = readH(texture2D(u_wave, uv + vec2(texel.x, 0.0)));
  float t = readH(texture2D(u_wave, uv + vec2(0.0, texel.y)));
  float b = readH(texture2D(u_wave, uv - vec2(0.0, texel.y)));

  // 离散波动方程：H(t+1) = 四邻均值 * 2 - H(t-1)
  float next = (l + r + t + b) * 0.5 - prev;
  next *= u_damping;

  // 注入扰动（投石下压为负脉冲，回弹后自然形成波列）
  for (int i = 0; i < ${MAX_DROPS}; i++) {
    vec4 d = u_drops[i];
    if (d.w == 0.0) continue;
    vec2 delta = gl_FragCoord.xy - d.xy;
    float dist2 = dot(delta, delta);
    next -= d.w * exp(-dist2 / (d.z * d.z));
  }

  gl_FragColor = vec4(encodeH(next), encodeH(curr), 0.0, 1.0);
}
`

// ---- 渲染 pass：俯视海水（上深下浅蜿蜒海域 + 白帽碎波 + 交互白沫）----
const DRAW_FS = `
precision highp float;

uniform vec2  u_res;        // 渲染尺寸 (device px)
uniform vec2  u_simRes;     // 模拟网格尺寸
uniform float u_time;
uniform sampler2D u_wave;   // 交互高度场（波动方程）

// 海水（上深下浅）
const vec3 DEEP_BLUE = vec3(0.051, 0.310, 0.753); // 深海蓝
const vec3 MID_BLUE  = vec3(0.071, 0.565, 0.784); // 过渡蓝青
const vec3 SHALLOWS  = vec3(0.133, 0.816, 0.753); // 浅滩绿松石
const vec3 WHITE     = vec3(0.933, 0.980, 0.980); // 碎波白

float hash(vec2 p) {
  p = fract(p * vec2(123.34, 456.21));
  p += dot(p, p + 45.32);
  return fract(p.x * p.y);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float readH(vec4 t) {
#ifdef HFLOAT
  return t.r;
#else
  return t.r * 2.0 - 1.0;
#endif
}

// 手动双线性采样（不依赖 half-float-linear 扩展）
float sampleH(vec2 uv) {
  vec2 p = uv * u_simRes - 0.5;
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = readH(texture2D(u_wave, (i + vec2(0.5, 0.5)) / u_simRes));
  float b = readH(texture2D(u_wave, (i + vec2(1.5, 0.5)) / u_simRes));
  float c = readH(texture2D(u_wave, (i + vec2(0.5, 1.5)) / u_simRes));
  float d = readH(texture2D(u_wave, (i + vec2(1.5, 1.5)) / u_simRes));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

// 环境波高度场（cap1+cap2 尺度，用于法线/阳光高光，不含高频 cap3 避免法线过碎）
float envHeight(vec2 p) {
  float t = mod(u_time, 3600.0);  // 取模防止大数值下 hash 精度退化
  float a = vnoise(p * vec2(0.08, 0.10) + vec2(t * 0.9, -t * 0.6));
  float b = vnoise(p * vec2(0.16, 0.20) + vec2(t * 1.4,  t * 0.5));
  return a * 0.6 + b * 0.4;
}

void main() {
  vec2 fc = gl_FragCoord.xy;
  float domY = u_res.y - fc.y;                     // 向下为正：0=顶部深海 res.y=底部浅滩
  float distF = smoothstep(0.25, 1.0, domY / u_res.y);  // 0=近 1=远（风区长度）

  // u_time 取模：防止长时间运行后大数值导致 hash/vnoise 浮点精度退化（白帽闪烁变快、纹理抖动）
  // noise 用 1 小时周期（连续函数无明显跳变），闪烁用 256 步短周期（@4Hz=64s / @10Hz=25.6s，人眼无感知）
  float tMod = mod(u_time, 3600.0);
  float flickT = mod(floor(u_time * 4.0), 256.0);
  float sparkT = mod(floor(u_time * 10.0), 256.0);

  // ---- 环境层：涌浪云移 / 高频毛细(FBM) / 风纹(各向异性) ----
  float swell = vnoise(fc * vec2(0.008, 0.012) + vec2(tMod * 0.12, tMod * 0.05));
  // FBM 2 层（移除 cap3 高频 octave，最小白帽尺寸 ~5-6px，避免盐粒感）
  float cap1 = vnoise(fc * vec2(0.08, 0.10) + vec2(tMod * 0.9, -tMod * 0.6));
  float cap2 = vnoise(fc * vec2(0.16, 0.20) + vec2(tMod * 1.4,  tMod * 0.5));
  float capFBM = cap1 * 0.65 + cap2 * 0.35;
  // 风纹：强各向异性（x:y≈1:15），横向拉伸条纹，与碎波排列方向一致
  float wind = vnoise(fc * vec2(0.004, 0.06) + vec2(tMod * 0.04, 0.0));

  // ---- 海域：上深下浅，蜿蜒分界 + 潮汐慢漂移 ----
  float shore = domY / u_res.y;
  float wob = (vnoise(fc * vec2(0.004, 0.002) + vec2(tMod * 0.008, 0.0)) - 0.5) * 0.3;
  float k = shore + wob;
  vec3 col = mix(DEEP_BLUE, MID_BLUE, smoothstep(0.05, 0.5, k));
  col = mix(col, SHALLOWS, smoothstep(0.45, 0.95, k));

  // ---- 明暗：涌浪收敛(大块云移呼吸 ±6%) + 毛细 + 风纹 ----
  float shade = (swell - 0.5) * 0.3 + (capFBM - 0.5) * 0.16 + (wind - 0.5) * 0.10;
  col *= 1.0 + shade * 0.12;

  // ---- 白帽碎波：阈值随距离降低(远处更密) × 风纹亮带 + 颗粒 + 闪烁 + 冷暖 ----
  float capLow  = 0.80 - 0.06 * distF;   // 远处阈值降低 → 白帽更密集（+0.08 减半密度）
  float capHigh = 0.93 - 0.04 * distF;
  float whitecap = smoothstep(capLow, capHigh, capFBM);
  float windBand = smoothstep(0.32, 0.72, wind);
  float wcap = whitecap * windBand;
  // 尺寸门控：仅在大尺度活跃带(cap1 高)保留白帽，孤立小斑被抑制
  float sizeGate = smoothstep(0.58, 0.72, cap1);
  wcap *= sizeGate;
  // 泡沫颗粒纹理：高频噪声调制白帽亮度
  float grain = vnoise(fc * vec2(0.9, 1.1) + vec2(tMod * 3.0, -tMod * 2.0));
  wcap *= 0.65 + 0.35 * grain;
  // 闪烁瞬生瞬灭（~4Hz，白帽随机出现/消失）
  float wFlick = hash(fc * 0.3 + flickT * 7.3);
  wcap *= smoothstep(0.25, 0.7, wFlick);
  // 冷暖渐变：近处暖白、远处蓝灰
  vec3 wcapColor = mix(vec3(0.96, 0.95, 0.92), vec3(0.76, 0.83, 0.88), distF);
  col += wcapColor * wcap * 0.8;

  // ---- 阳光碎点：环境波法线镜面反射 + 高频闪烁（暖白金黄）----
  float eps = 1.5;
  float eC = envHeight(fc);
  float eR = envHeight(fc + vec2(eps, 0.0));
  float eU = envHeight(fc + vec2(0.0, eps));
  vec3 envN = normalize(vec3(eC - eR, eC - eU, 1.2));  // z 控制法线强度
  vec3 sunDir = normalize(vec3(0.35, 0.5, 0.85));      // 太阳方位（俯视斜射）
  vec3 halfV = normalize(sunDir + vec3(0.0, 0.0, 1.0));
  float spec = pow(max(dot(envN, halfV), 0.0), 64.0);  // 高幂次集中高光
  // 高频闪烁（~10Hz）：只有部分像素瞬亮
  float flick = hash(fc * 0.7 + sparkT * 3.1);
  flick = smoothstep(0.55, 1.0, flick);
  float glitter = spec * flick * (0.4 + 0.6 * distF);  // 远处更密集
  col += vec3(1.0, 0.93, 0.80) * glitter * 1.3;

  // ---- 交互波：明暗起伏 + 白色泡沫脊线(波峰二阶导<0) ----
  vec2 uv = fc / u_res;
  vec2 tx = vec2(1.0 / u_simRes.x, 0.0);
  vec2 ty = vec2(0.0, 1.0 / u_simRes.y);
  float hC = sampleH(uv);
  float hL = sampleH(uv - tx);
  float hR = sampleH(uv + tx);
  float gx = hR - hL;
  col *= 1.0 + hC * 0.3 + gx * 0.6;
  // 脊线检测：高度高于两侧邻居才是波峰，白沫只沿脊线渲染
  float ridge = smoothstep(0.0, 0.015, hC - max(hL, hR));
  float foam = smoothstep(0.08, 0.30, hC) * ridge;
  col += WHITE * foam * 0.6;

  gl_FragColor = vec4(col, 1.0);
}
`

export class WaterRenderer {
  constructor(canvas) {
    this.canvas = canvas
    this.gl = null
    this.running = false
    this.raf = 0
    this.dpr = Math.min(window.devicePixelRatio || 1, 2)
    this.startTime = performance.now()
    this.dropQueue = []
    this.cssW = 1
    this.cssH = 1
    this.simW = 0
    this.simH = 0
    this.useHF = false
    this.onContextLost = null
    this._render = this._render.bind(this)
    this._onLost = (e) => {
      e.preventDefault()
      this.stop()
      if (this.onContextLost) this.onContextLost()
    }
    this._onRestored = () => {
      if (this._setupGL()) this.start()
    }
  }

  init() {
    try {
      const gl = this.canvas.getContext('webgl', {
        alpha: false,
        antialias: false,
        depth: false,
        stencil: false,
        powerPreference: 'low-power'
      }) || this.canvas.getContext('experimental-webgl')
      if (!gl) return false
      this.gl = gl
      if (!this._setupGL()) return false
      this.canvas.addEventListener('webglcontextlost', this._onLost, false)
      this.canvas.addEventListener('webglcontextrestored', this._onRestored, false)
      return true
    } catch (err) {
      return false
    }
  }

  _compile(type, src) {
    const gl = this.gl
    const s = gl.createShader(type)
    gl.shaderSource(s, src)
    gl.compileShader(s)
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      gl.deleteShader(s)
      return null
    }
    return s
  }

  _link(fsSrc) {
    const gl = this.gl
    const vs = this._compile(gl.VERTEX_SHADER, VERT_SRC)
    const fs = this._compile(gl.FRAGMENT_SHADER, fsSrc)
    if (!vs || !fs) return null
    const prog = gl.createProgram()
    gl.attachShader(prog, vs)
    gl.attachShader(prog, fs)
    gl.linkProgram(prog)
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return null
    return prog
  }

  // 创建模拟纹理 + FBO，返回是否成功
  _createSimTarget(type) {
    const gl = this.gl
    const tex = gl.createTexture()
    gl.bindTexture(gl.TEXTURE_2D, tex)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, this.simW, this.simH, 0, gl.RGBA, type, null)
    const fbo = gl.createFramebuffer()
    gl.bindFramebuffer(gl.FRAMEBUFFER, fbo)
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0)
    const ok = gl.checkFramebufferStatus(gl.FRAMEBUFFER) === gl.FRAMEBUFFER_COMPLETE
    gl.bindFramebuffer(gl.FRAMEBUFFER, null)
    if (!ok) {
      gl.deleteTexture(tex)
      gl.deleteFramebuffer(fbo)
      return null
    }
    return { tex, fbo }
  }

  _setupGL() {
    const gl = this.gl

    // 模拟网格：约 1/4 CSS 分辨率，128~400 之间
    this.simW = Math.max(128, Math.min(400, Math.round(this.cssW / 4)))
    this.simH = Math.max(32, Math.round(this.simW * this.cssH / Math.max(this.cssW, 1)))

    // 半浮点支持检测（纹理格式 + 可渲染性）
    const extHF = gl.getExtension('OES_texture_half_float')
    this.useHF = false
    this.simA = null
    this.simB = null
    if (extHF) {
      const a = this._createSimTarget(extHF.HALF_FLOAT_OES)
      const b = a && this._createSimTarget(extHF.HALF_FLOAT_OES)
      if (a && b) {
        this.useHF = true
        this.simA = a
        this.simB = b
      }
    }
    if (!this.useHF) {
      const a = this._createSimTarget(gl.UNSIGNED_BYTE)
      const b = a && this._createSimTarget(gl.UNSIGNED_BYTE)
      if (!a || !b) return false
      this.simA = a
      this.simB = b
    }

    const define = this.useHF ? '#define HFLOAT 1\n' : ''
    this.simProg = this._link(define + SIM_FS)
    this.drawProg = this._link(define + DRAW_FS)
    if (!this.simProg || !this.drawProg) return false

    // 全屏三角形
    const buf = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buf)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW)
    for (const prog of [this.simProg, this.drawProg]) {
      gl.useProgram(prog)
      const loc = gl.getAttribLocation(prog, 'a_pos')
      gl.enableVertexAttribArray(loc)
      gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0)
    }

    gl.useProgram(this.simProg)
    this.simU = {
      wave: gl.getUniformLocation(this.simProg, 'u_wave'),
      simRes: gl.getUniformLocation(this.simProg, 'u_simRes'),
      drops: gl.getUniformLocation(this.simProg, 'u_drops[0]'),
      damping: gl.getUniformLocation(this.simProg, 'u_damping')
    }
    gl.uniform1i(this.simU.wave, 0)
    gl.uniform2f(this.simU.simRes, this.simW, this.simH)
    gl.uniform1f(this.simU.damping, 0.99)

    gl.useProgram(this.drawProg)
    this.drawU = {
      res: gl.getUniformLocation(this.drawProg, 'u_res'),
      simRes: gl.getUniformLocation(this.drawProg, 'u_simRes'),
      time: gl.getUniformLocation(this.drawProg, 'u_time'),
      wave: gl.getUniformLocation(this.drawProg, 'u_wave')
    }
    gl.uniform1i(this.drawU.wave, 0)
    gl.uniform2f(this.drawU.simRes, this.simW, this.simH)

    this.resize()
    return true
  }

  resize() {
    const gl = this.gl
    const c = this.canvas
    if (!gl || !c.clientWidth || !c.clientHeight) return
    this.cssW = c.clientWidth
    this.cssH = c.clientHeight
    const W = Math.round(this.cssW * this.dpr)
    const H = Math.round(this.cssH * this.dpr)
    if (c.width !== W || c.height !== H) {
      c.width = W
      c.height = H
    }
    gl.uniform2f(this.drawU.res, c.width, c.height)

    // 模拟网格尺寸随 CSS 尺寸变化时重建（波场清零）
    const simW = Math.max(128, Math.min(400, Math.round(this.cssW / 4)))
    const simH = Math.max(32, Math.round(simW * this.cssH / Math.max(this.cssW, 1)))
    if ((simW !== this.simW || simH !== this.simH) && this.simA) {
      this.simW = simW
      this.simH = simH
      const type = this.useHF ? (gl.getExtension('OES_texture_half_float') || {}).HALF_FLOAT_OES : gl.UNSIGNED_BYTE
      for (const key of ['simA', 'simB']) {
        const target = this._createSimTarget(type)
        if (target) {
          gl.deleteTexture(this[key].tex)
          gl.deleteFramebuffer(this[key].fbo)
          this[key] = target
        }
      }
      gl.useProgram(this.simProg)
      gl.uniform2f(this.simU.simRes, this.simW, this.simH)
      gl.useProgram(this.drawProg)
      gl.uniform2f(this.drawU.simRes, this.simW, this.simH)
    }
  }

  // 投一滴水：x,y 为 CSS px（banner 坐标），radius CSS px，strength 建议 0.1~2
  addDrop(x, y, radius = 5, strength = 0.6) {
    if (!this.gl || !this.simW) return
    this.dropQueue.push({
      x: x / this.cssW * this.simW,
      y: (1 - y / this.cssH) * this.simH,
      r: Math.max(radius / this.cssW * this.simW, 1.2),
      s: strength
    })
    if (this.dropQueue.length > 24) this.dropQueue.splice(0, this.dropQueue.length - 24)
  }

  start() {
    if (this.running || !this.gl) return
    this.running = true
    this.raf = requestAnimationFrame(this._render)
  }

  stop() {
    this.running = false
    cancelAnimationFrame(this.raf)
  }

  _render() {
    if (!this.running) return
    const gl = this.gl

    // ---- pass 1：波动方程 ----
    gl.bindFramebuffer(gl.FRAMEBUFFER, this.simB.fbo)
    gl.viewport(0, 0, this.simW, this.simH)
    gl.useProgram(this.simProg)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, this.simA.tex)
    const drops = new Float32Array(MAX_DROPS * 4)
    for (let i = 0; i < MAX_DROPS; i++) {
      const d = this.dropQueue.shift()
      if (!d) break
      drops[i * 4] = d.x
      drops[i * 4 + 1] = d.y
      drops[i * 4 + 2] = d.r
      drops[i * 4 + 3] = d.s
    }
    gl.uniform4fv(this.simU.drops, drops)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
    const tmp = this.simA
    this.simA = this.simB
    this.simB = tmp

    // ---- pass 2：渲染 ----
    gl.bindFramebuffer(gl.FRAMEBUFFER, null)
    gl.viewport(0, 0, this.canvas.width, this.canvas.height)
    gl.useProgram(this.drawProg)
    gl.activeTexture(gl.TEXTURE0)
    gl.bindTexture(gl.TEXTURE_2D, this.simA.tex)
    gl.uniform1f(this.drawU.time, (performance.now() - this.startTime) / 1000)
    gl.drawArrays(gl.TRIANGLES, 0, 3)

    this.raf = requestAnimationFrame(this._render)
  }

  destroy() {
    this.stop()
    this.canvas.removeEventListener('webglcontextlost', this._onLost)
    this.canvas.removeEventListener('webglcontextrestored', this._onRestored)
    const gl = this.gl
    if (gl) {
      const ext = gl.getExtension('WEBGL_lose_context')
      if (ext) ext.loseContext()
    }
    this.gl = null
  }
}
