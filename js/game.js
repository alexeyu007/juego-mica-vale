/* ============================================================
   Mica & Vale vs. El Resfrio
   Juego de defensa: toca los virus antes de que suban a la cuna.
   ============================================================ */
(() => {
'use strict';

// ---------- lienzo lógico ----------
const W = 480, H = 800;
const DANGER_Y = 228;          // línea de la cuna: los virus no deben pasar
const BABY_Y = 192;            // centro de las cabezas de las bebés
const ROUND_TIME = 60;         // segundos a resistir para ganar

const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const stage = document.getElementById('stage');
let RATIO = 1;                 // píxeles reales por píxel lógico (nitidez)

function fit() {
  const dpr = Math.min(window.devicePixelRatio || 1, 3);
  const s = Math.min(window.innerWidth / W, window.innerHeight / H) * 0.98;
  // el buffer del lienzo se hace igual al tamaño CSS real: así no hay reescalado
  RATIO = Math.min(dpr * s, 3);
  canvas.width = Math.round(W * RATIO);
  canvas.height = Math.round(H * RATIO);
  ctx.setTransform(RATIO, 0, 0, RATIO, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = 'high';
  canvas.style.width = (W * s) + 'px';
  canvas.style.height = (H * s) + 'px';
  stage.style.width = (W * s) + 'px';
  stage.style.height = (H * s) + 'px';
}
window.addEventListener('resize', fit);
fit();

// ---------- audio (sintetizado, sin archivos) ----------
const Audio2 = {
  ctx: null, muted: false,
  init() {
    if (this.ctx) return;
    try { this.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {}
  },
  tone(freq, dur, type = 'sine', vol = .18, slide = 0) {
    if (this.muted || !this.ctx) return;
    const t = this.ctx.currentTime;
    const o = this.ctx.createOscillator(), g = this.ctx.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t);
    if (slide) o.frequency.exponentialRampToValueAtTime(Math.max(40, freq + slide), t + dur);
    g.gain.setValueAtTime(vol, t);
    g.gain.exponentialRampToValueAtTime(.0001, t + dur);
    o.connect(g); g.connect(this.ctx.destination);
    o.start(t); o.stop(t + dur + .02);
  },
  pop()   { this.tone(760, .09, 'square', .13, 320); this.tone(1180, .07, 'sine', .10, 260); },
  big()   { this.tone(520, .14, 'square', .14, 500); this.tone(880, .12, 'sine', .12, 400); },
  hurt()  { this.tone(220, .28, 'sawtooth', .16, -140); },
  power() { [660, 880, 1180].forEach((f, i) => setTimeout(() => this.tone(f, .12, 'triangle', .14), i * 70)); },
  miss()  { this.tone(160, .1, 'triangle', .08); },
  win()   { [523, 659, 784, 1046].forEach((f, i) => setTimeout(() => this.tone(f, .22, 'triangle', .16), i * 130)); },
  lose()  { [440, 370, 294, 220].forEach((f, i) => setTimeout(() => this.tone(f, .3, 'sawtooth', .13), i * 160)); },
};

// ---------- carga de assets ----------
const IMG = {};
const VER = '20261020b';
const LISTA = {
  fondo: 'assets/fondo_hd.jpg',
  mica_normal: 'assets/sprites/mica_normal.png',
  mica_preocupada: 'assets/sprites/mica_preocupada.png',
  mica_moquito: 'assets/sprites/mica_moquito.png',
  mica_estornudo: 'assets/sprites/mica_estornudo.png',
  mica_enferma: 'assets/sprites/mica_enferma.png',
  mica_feliz: 'assets/sprites/mica_feliz.png',
  mica_celebrando: 'assets/sprites/mica_celebrando.png',
  vale_normal: 'assets/sprites/vale_normal.png',
  vale_preocupada: 'assets/sprites/vale_preocupada.png',
  vale_moquito: 'assets/sprites/vale_moquito.png',
  vale_estornudo: 'assets/sprites/vale_estornudo.png',
  vale_enferma: 'assets/sprites/vale_enferma.png',
  vale_feliz: 'assets/sprites/vale_feliz.png',
  vale_celebrando: 'assets/sprites/vale_celebrando.png',
  virus_normal: 'assets/sprites/virus_normal.png',
  virus_enojado: 'assets/sprites/virus_enojado.png',
  virus_sorprendido: 'assets/sprites/virus_sorprendido.png',
  virus_baba: 'assets/sprites/virus_baba.png',
  virus_grande: 'assets/sprites/virus_grande.png',
  virus_pequeno: 'assets/sprites/virus_pequeno.png',
  virus_rojo: 'assets/sprites/virus2_rojo.png',
  virus_triste: 'assets/sprites/virus_triste.png',
  fx_puf: 'assets/sprites/fx_puf.png',
  fx_achis: 'assets/sprites/fx_achis.png',
  fx_lluvia: 'assets/sprites/fx_lluvia.png',
  fx_moquito: 'assets/sprites/fx_moquito.png',
  corazon: 'assets/sprites/corazon.png',
  corazon_gris: 'assets/sprites/corazon_gris.png',
  pausa: 'assets/sprites/ui_pausa2.png',
  estrella: 'assets/sprites/estrella_ui.png',
  panuelo: 'assets/sprites/panuelo_caja.png',
  patito: 'assets/sprites/patito_ui.png',
  vida_extra: 'assets/sprites/vida_extra.png',
};
let cargado = 0, total = Object.keys(LISTA).length;
// URL con versión para evitar que el navegador sirva copias cacheadas.
const url = k => LISTA[k] + (LISTA[k].includes('?') ? '&' : '?') + 'v=' + VER;

function cargar(done) {
  for (const k in LISTA) {
    const im = new Image();
    im.onload = im.onerror = () => { if (++cargado === total) done(); };
    im.src = url(k);
    IMG[k] = im;
  }
}

// ---------- utilidades ----------
const rnd = (a, b) => a + Math.random() * (b - a);
const pick = arr => arr[(Math.random() * arr.length) | 0];
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));

function rr(x, y, w, h, r) {          // rectángulo redondeado
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}
function drawImg(name, x, y, w, h, opts = {}) {
  const im = IMG[name];
  if (!im || !im.complete || !im.naturalWidth) return;
  const iw = im.naturalWidth, ih = im.naturalHeight;
  const dw = w || iw, dh = h || (dw * ih / iw);
  ctx.save();
  ctx.translate(x, y);
  if (opts.rot) ctx.rotate(opts.rot);
  if (opts.flip) ctx.scale(-1, 1);
  ctx.globalAlpha = opts.alpha == null ? 1 : opts.alpha;
  if (opts.sx != null) {             // ancla: 0 izq, .5 centro, 1 der
    const ax = (opts.sx == null ? .5 : opts.sx) * dw, ay = (opts.sy == null ? .5 : opts.sy) * dh;
    ctx.drawImage(im, -ax, -ay, dw, dh);
  } else {
    ctx.drawImage(im, -dw / 2, -dh / 2, dw, dh);
  }
  ctx.restore();
}

// ---------- TOP 5 (Supabase o local) ----------
// Pega aquí tus datos de Supabase (Project Settings → API).
const SB_URL = 'https://aladtbjatyvnxuilzsug.supabase.co/rest/v1/';   // tu URL
const SB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFsYWR0YmphdHl2bnh1aWx6c3VnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTI1MzE3NDksImV4cCI6MjEwODEwNzc0OX0.G4IeZnnE0al3H05iv_Gab86QMmTD8HXpRcfRigVTP0U';                    // tu anon key
// Mientras estén vacíos, el ranking funciona en "local" (solo en este navegador).
const SB_URL = '';               // p.ej. 'https://abcdefghij.supabase.co'
const SB_KEY = '';               // anon public key (empieza por eyJ...)
const SB_ON  = !!(SB_URL && SB_KEY);

const LS_TOP5 = 'mv_top5', LS_TOKEN = 'mv_token', LS_USER = 'mv_user';

// ---------- LOGIN CON GOOGLE (Supabase Auth) ----------
let USUARIO = null;              // { id, nombre, avatar }

function sbFetch(path, opts = {}) {
  // si hay sesión, se manda su token (necesario para que auth.uid() funcione)
  const tok = localStorage.getItem(LS_TOKEN);
  return fetch(SB_URL + path, {
    ...opts,
    headers: {
      apikey: SB_KEY,
      Authorization: 'Bearer ' + (tok || SB_KEY),
      'Content-Type': 'application/json',
      ...(opts.headers || {}),
    },
  });
}

function entrarConGoogle() {
  if (!SB_ON) { alert('Configura Supabase (SB_URL y SB_KEY) en js/game.js para habilitar el login.'); return; }
  const aqui = location.origin + location.pathname;
  // flujo implícito: Supabase vuelve a esta URL con #access_token=...
  location.href = `${SB_URL}/auth/v1/authorize?provider=google&redirect_to=${encodeURIComponent(aqui)}`;
}

// recoge el token si volvimos de Google (#access_token=... en la URL)
async function procesarCallback() {
  const h = new URLSearchParams(location.hash.slice(1));
  const tok = h.get('access_token');
  if (!tok) return false;
  localStorage.setItem(LS_TOKEN, tok);
  history.replaceState(null, '', location.pathname);   // limpia la URL
  await cargarUsuario();
  return true;
}

async function cargarUsuario() {
  const tok = localStorage.getItem(LS_TOKEN);
  if (!SB_ON || !tok) { USUARIO = null; return null; }
  try {
    const r = await fetch(SB_URL + '/auth/v1/user', {
      headers: { apikey: SB_KEY, Authorization: 'Bearer ' + tok },
    });
    if (!r.ok) { localStorage.removeItem(LS_TOKEN); USUARIO = null; return null; }
    const u = await r.json();
    const m = u.user_metadata || {};
    USUARIO = {
      id: u.id,
      nombre: (m.full_name || m.name || u.email || 'Jugador').split(' ')[0].slice(0, 20),
      avatar: m.avatar_url || m.picture || '',
    };
    localStorage.setItem(LS_USER, JSON.stringify(USUARIO));
  } catch (e) { /* sin red: usamos lo guardado */
    try { USUARIO = JSON.parse(localStorage.getItem(LS_USER) || 'null'); } catch (_) { USUARIO = null; }
  }
  return USUARIO;
}

function salir() {
  localStorage.removeItem(LS_TOKEN);
  localStorage.removeItem(LS_USER);
  USUARIO = null;
  pintarUsuario();
}

// ---------- TOP 5 ----------
async function top5Leer() {
  if (SB_ON) {
    try {
      const r = await sbFetch('/rest/v1/scores?select=nombre,avatar,puntos&order=puntos.desc&limit=5');
      if (r.ok) return await r.json();
    } catch (e) { /* sin red: seguimos con local */ }
  }
  try { return JSON.parse(localStorage.getItem(LS_TOP5) || '[]'); } catch (e) { return []; }
}

async function top5Guardar(nombre, puntos) {
  // respaldo local siempre
  let l;
  try { l = JSON.parse(localStorage.getItem(LS_TOP5) || '[]'); } catch (e) { l = []; }
  l.push({ nombre, puntos });
  l.sort((a, b) => b.puntos - a.puntos);
  localStorage.setItem(LS_TOP5, JSON.stringify(l.slice(0, 20)));

  if (SB_ON && USUARIO) {           // guardado mundial, con el usuario de Google
    try {
      const r = await sbFetch('/rest/v1/scores', {
        method: 'POST', headers: { Prefer: 'return=minimal' },
        body: JSON.stringify({
          user_id: USUARIO.id, nombre: USUARIO.nombre,
          avatar: USUARIO.avatar, puntos,
        }),
      });
      if (r.ok) return top5Leer();
    } catch (e) { /* sin red: se queda el respaldo local */ }
  }
  return l.slice(0, 5);
}

const esc = s => String(s == null ? '' : s).replace(/[<>&"']/g, c =>
  ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;', "'": '&#39;' }[c]));

function pintarTop5(lista, ol) {
  const med = ['🥇', '🥈', '🥉'];
  ol.innerHTML = lista.length
    ? lista.map((r, i) => {
        const av = r.avatar
          ? `<img src="${esc(r.avatar)}" class="miniAv" alt="" onerror="this.style.display='none'">`
          : '';
        return `<li><span class="celda">${med[i] || (i + 1) + '.'} ${av}${esc(r.nombre)}</span><span>${r.puntos} pts</span></li>`;
      }).join('')
    : '<li class="vacio">Sin registros aún</li>';
}
async function refrescarTop5(ol) { pintarTop5(await top5Leer(), ol); }

// pinta el estado de login (menú y pantalla final)
function pintarUsuario() {
  const hay = !!USUARIO;
  const nubeDisponible = SB_ON;               // con Supabase configurado se pide login
  $('userChipBox').classList.toggle('hidden', !hay);
  $('btnGoogle').classList.toggle('hidden', hay || !nubeDisponible);
  $('endUser').classList.toggle('hidden', !hay);
  $('btnGoogleEnd').classList.toggle('hidden', hay || !nubeDisponible);
  $('playerName').classList.toggle('hidden', hay && nubeDisponible);
  // se guarda en la nube si hay sesión; si no hay Supabase, se guarda en local con nombre
  $('btnSave').classList.toggle('hidden', nubeDisponible && !hay);
  if (hay) {
    $('menuName').textContent = USUARIO.nombre;
    $('endName').textContent = USUARIO.nombre;
    if (USUARIO.avatar) { $('menuAvatar').src = USUARIO.avatar; $('endAvatar').src = USUARIO.avatar; }
    $('playerName').value = USUARIO.nombre;
  }
}

// ---------- tipos de virus ----------
const TIPOS = {
  normal:      { img: 'virus_normal',      r: 34, speed: 1.00, pts: 100, hp: 1, sway: 14 },
  enojado:     { img: 'virus_enojado',     r: 34, speed: 1.38, pts: 150, hp: 1, sway: 10 },
  sorprendido: { img: 'virus_sorprendido', r: 33, speed: 0.86, pts: 120, hp: 1, sway: 34 },
  baba:        { img: 'virus_baba',        r: 36, speed: 0.78, pts: 180, hp: 1, sway: 12, spit: true },
  grande:      { img: 'virus_grande',      r: 46, speed: 0.66, pts: 250, hp: 2, sway: 8 },
  pequeno:     { img: 'virus_pequeno',     r: 22, speed: 1.75, pts: 200, hp: 1, sway: 26 },
  rojo:        { img: 'virus_rojo',        r: 36, speed: 1.95, pts: 350, hp: 1, sway: 18 },
};

// ---------- estado ----------
let S = null;
function nuevoJuego() {
  S = {
    fase: 'playing',
    t: 0,                 // tiempo transcurrido
    score: 0,
    combo: 0, comboT: 0,
    doubleT: 0,           // estrella: puntos x2
    spawnT: .4,
    powerT: rnd(7, 11),
    vir: [], pow: [], fx: [], txts: [], slime: [],
    shake: 0, flash: 0,
    babys: [
      { name: 'mica', x: 138, hp: 3, hurtT: 0, cheer: 0 },
      { name: 'vale', x: 342, hp: 3, hurtT: 0, cheer: 0 },
    ],
    best: +(localStorage.getItem('mv_best') || 0),
    guardado: false,      // si ya se envió esta partida al Top 5
  };
}

// ---------- entidades ----------
function spawnVirus() {
  const p = S.t / ROUND_TIME;                        // progreso 0..1
  const pool = ['normal', 'sorprendido', 'normal', 'enojado'];
  if (p > .12) pool.push('baba', 'grande');
  if (p > .3) pool.push('pequeno', 'enojado');
  if (p > .5) pool.push('rojo', 'pequeno', 'grande');
  if (p > .7) pool.push('rojo', 'enojado', 'pequeno');
  const key = pick(pool);
  const tp = TIPOS[key];
  S.vir.push({
    key, ...tp,
    x: rnd(48, W - 48), y: H + 60,
    base: rnd(48, 72) * (1 + p * 1.05),               // px/s
    phase: rnd(0, Math.PI * 2),
    spitT: rnd(1.0, 2.0),
    hitT: 0, wob: rnd(0, 6.28),
  });
}

function spawnPower() {
  const key = pick(['panuelo', 'patito', 'estrella', 'patito', 'estrella', 'patito', 'vida_extra']);
  S.pow.push({
    key, x: rnd(60, W - 60), y: H + 50,
    speed: rnd(52, 70), phase: rnd(0, 6.28),
    r: key === 'panuelo' ? 40 : 34,
  });
}

function pop(v, idx) {
  S.vir.splice(idx, 1);
  S.combo++; S.comboT = 2.6;
  const mult = Math.min(S.combo, 5) * (S.doubleT > 0 ? 2 : 1);
  const pts = v.pts * mult;
  S.score += pts;
  S.fx.push({ img: 'fx_puf', x: v.x, y: v.y, t: 0, dur: .38, size: v.r * 3.4 });
  S.fx.push({ img: 'fx_lluvia', x: v.x, y: v.y, t: 0, dur: .5, size: v.r * 3.6 });
  S.txts.push({ txt: '+' + pts, x: v.x, y: v.y - 10, t: 0, dur: .9,
                col: S.doubleT > 0 ? '#ffcf3f' : '#fff', big: mult >= 3 });
  if (S.combo >= 3) S.txts.push({ txt: '¡Racha x' + mult + '!', x: W / 2, y: 300,
                t: 0, dur: 1, col: '#ffe36b', big: true });
  (v.r > 40 ? Audio2.big : Audio2.pop).call(Audio2);
  S.shake = Math.max(S.shake, v.r > 40 ? 6 : 3);
}

function hitBaby(b) {
  b.hp--;
  b.hurtT = 1.1;
  S.combo = 0; S.shake = 10; S.flash = .5;
  S.fx.push({ img: 'fx_achis', x: b.x, y: BABY_Y + 8, t: 0, dur: .7, size: 165 });
  S.txts.push({ txt: '¡Achís!', x: b.x, y: 140, t: 0, dur: 1, col: '#ff6a6a', big: true });
  Audio2.hurt();
  if (b.hp <= 0) finalizar(false);
}

function collect(p, idx) {
  S.pow.splice(idx, 1);
  Audio2.power();
  if (p.key === 'patito') {
    S.txts.push({ txt: '¡Patito! +100', x: p.x, y: p.y, t: 0, dur: 1, col: '#ffd23f', big: false });
    S.score += 100;
  } else if (p.key === 'estrella') {
    S.doubleT = 8;
    S.txts.push({ txt: '¡Puntos x2!', x: p.x, y: p.y, t: 0, dur: 1, col: '#ffd23f', big: true });
  } else if (p.key === 'vida_extra') {
    const b = S.babys.reduce((a, c) => a.hp <= c.hp ? a : c);
    b.hp = Math.min(3, b.hp + 1);
    S.txts.push({ txt: '¡Vida extra!', x: p.x, y: p.y, t: 0, dur: 1, col: '#ff7ab8', big: true });
  } else if (p.key === 'panuelo') {
    let n = 0;
    S.vir.forEach(v => {
      S.fx.push({ img: 'fx_puf', x: v.x, y: v.y, t: rnd(0, .12), dur: .38, size: v.r * 3 });
      n++;
    });
    S.score += n * 50;
    S.txts.push({ txt: '¡Pañuelazo! +' + n * 50, x: W / 2, y: 330, t: 0, dur: 1.2, col: '#8be9ff', big: true });
    S.vir.length = 0;
    S.shake = 8;
  }
  S.fx.push({ img: 'fx_lluvia', x: p.x, y: p.y, t: 0, dur: .55, size: 130 });
}

function finalizar(ganó) {
  if (S.fase !== 'playing') return;
  S.fase = ganó ? 'won' : 'lost';
  if (S.score > S.best) { S.best = S.score; localStorage.setItem('mv_best', S.best); }
  if (ganó) { S.babys.forEach(b => b.cheer = 99); Audio2.win(); }
  else { S.babys.forEach(b => { b.hp = 0; }); Audio2.lose(); }
  setTimeout(() => mostrarFin(ganó), 900);
}

// ---------- actualización ----------
function update(dt) {
  if (S.fase !== 'playing') return;
  S.t += dt;
  if (S.t >= ROUND_TIME) { finalizar(true); return; }

  const p = S.t / ROUND_TIME;

  // spawn
  S.spawnT -= dt;
  if (S.spawnT <= 0) {
    spawnVirus();
    S.spawnT = (1.0 - .68 * p) * rnd(.7, 1.2);
    // a partir de la mitad a veces salen dobles
    if (p > .5 && Math.random() < .22) spawnVirus();
    if (p > .78 && Math.random() < .18) spawnVirus();
  }
  S.powerT -= dt;
  if (S.powerT <= 0) { spawnPower(); S.powerT = rnd(10, 15); }

  // combo
  if (S.comboT > 0) { S.comboT -= dt; if (S.comboT <= 0) S.combo = 0; }
  if (S.doubleT > 0) S.doubleT -= dt;

  // virus
  for (let i = S.vir.length - 1; i >= 0; i--) {
    const v = S.vir[i];
    v.y -= v.base * v.speed * dt;
    v.phase += dt * 2.1;
    v.wob += dt * 5;
    const sway = Math.sin(v.phase) * v.sway;
    if (v.hitT > 0) v.hitT -= dt;

    if (v.spit) {                          // virus que lanza babas
      v.spitT -= dt;
      if (v.spitT <= 0 && v.y > DANGER_Y + 140) {
        v.spitT = rnd(1.6, 2.6);
        S.slime.push({ x: v.x + sway, y: v.y, speed: rnd(70, 95), r: 15, phase: rnd(0, 6.28) });
      }
    }
    if (v.y < DANGER_Y - v.r * .3) {
      S.vir.splice(i, 1);
      const b = S.babys[0].x < v.x ? S.babys[1] : S.babys[0];
      hitBaby(b);
    }
  }

  // babas
  for (let i = S.slime.length - 1; i >= 0; i--) {
    const s = S.slime[i];
    s.y -= s.speed * dt; s.phase += dt * 4;
    if (s.y < DANGER_Y + 10) {
      S.slime.splice(i, 1);
      const b = S.babys[0].x < s.x ? S.babys[1] : S.babys[0];
      hitBaby(b);
    }
  }

  // powerups
  for (let i = S.pow.length - 1; i >= 0; i--) {
    const q = S.pow[i];
    q.y -= q.speed * dt; q.phase += dt * 2.4;
    if (q.y < -60) S.pow.splice(i, 1);
  }

  // efectos y textos
  for (let i = S.fx.length - 1; i >= 0; i--) { S.fx[i].t += dt; if (S.fx[i].t >= S.fx[i].dur) S.fx.splice(i, 1); }
  for (let i = S.txts.length - 1; i >= 0; i--) { S.txts[i].t += dt; if (S.txts[i].t >= S.txts[i].dur) S.txts.splice(i, 1); }

  if (S.shake > 0) S.shake = Math.max(0, S.shake - dt * 26);
  if (S.flash > 0) S.flash = Math.max(0, S.flash - dt * 1.6);

  // animaciones de las bebés
  S.babys.forEach(b => {
    if (b.hurtT > 0) b.hurtT = Math.max(0, b.hurtT - dt);
    if (b.cheer > 0) b.cheer = Math.max(0, b.cheer - dt);
  });
}

// ---------- dibujo ----------
let fondoOff = null;
function prepararFondo() {
  fondoOff = document.createElement('canvas');
  fondoOff.width = Math.round(W * RATIO);
  fondoOff.height = Math.round(H * RATIO);
  const c = fondoOff.getContext('2d');
  c.setTransform(RATIO, 0, 0, RATIO, 0, 0);
  c.imageSmoothingEnabled = true;
  c.imageSmoothingQuality = 'high';
  const im = IMG.fondo;
  const sc = Math.max(W / im.naturalWidth, H / im.naturalHeight);
  const dw = im.naturalWidth * sc, dh = im.naturalHeight * sc;
  c.drawImage(im, (W - dw) / 2, 150 - 290 * sc, dw, dh);
  // desvanecido suave arriba
  const g = c.createLinearGradient(0, 0, 0, 240);
  g.addColorStop(0, 'rgba(255,235,250,.92)');
  g.addColorStop(1, 'rgba(255,235,250,0)');
  c.fillStyle = g; c.fillRect(0, 0, W, 240);
}

function exprBaby(b) {
  if (S.fase === 'won' || b.cheer > 0) return b.name + '_celebrando';
  if (S.fase === 'lost') return b.name + '_enferma';
  if (b.hurtT > .35) return b.name + '_estornudo';
  if (b.hp <= 1) return b.name + '_moquito';
  if (b.hp === 2) return b.name + '_preocupada';
  return b.name + '_normal';
}

function dibujarBebes() {
  const bob = Math.sin(S.t * 2) * 3;
  S.babys.forEach((b, i) => {
    const spr = exprBaby(b);
    const puls = b.hurtT > 0 ? 1 + Math.sin(b.hurtT * 30) * .05 : 1;
    drawImg(spr, b.x, BABY_Y + bob + (i ? -bob * 2 : 0), 156 * puls, null, {});
    // corazones de cada bebé, anclados a las esquinas del HUD
    const cx = i ? 370 : 42;
    for (let k = 0; k < 3; k++) {
      drawImg(k < b.hp ? 'corazon' : 'corazon_gris',
              cx + k * 34, 30, 28, null, {});
    }
  });
}

function dibujarCuna() {
  // baranda blanca de la cuna
  ctx.save();
  const y = DANGER_Y + 12;
  ctx.fillStyle = '#fff';
  ctx.shadowColor = 'rgba(150,80,140,.35)'; ctx.shadowBlur = 10; ctx.shadowOffsetY = 3;
  rr(-6, y, W + 12, 16, 8); ctx.fill();
  ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
  ctx.fillStyle = '#f4e3f4';
  for (let x = 12; x < W; x += 34) { rr(x, y + 16, 12, 46, 5); ctx.fill(); }
  ctx.fillStyle = 'rgba(255,255,255,.85)';
  rr(-6, y + 58, W + 12, 12, 6); ctx.fill();
  ctx.restore();
}

function dibujarVirus() {
  S.vir.forEach(v => {
    const sway = Math.sin(v.phase) * v.sway;
    const rot = Math.sin(v.wob) * .12;
    const squish = 1 + Math.sin(v.wob * 1.3) * .06;
    let img = v.img;
    if (v.hitT > 0) img = 'virus_triste';
    const d = v.r * 2 * squish;
    ctx.save();
    ctx.globalAlpha = .18;
    ctx.fillStyle = '#7a4a86';
    ctx.beginPath(); ctx.ellipse(v.x + sway, v.y + v.r * .95, v.r * .8, v.r * .28, 0, 0, 6.28); ctx.fill();
    ctx.restore();
    drawImg(img, v.x + sway, v.y, d, null, { rot });
    if (v.hp > 1) {   // indicador de 2 golpes
      drawImg('corazon', v.x + sway + v.r * .8, v.y - v.r * .8, 16, null, {});
    }
  });
}

function dibujarTodo() {
  ctx.clearRect(0, 0, W, H);
  ctx.save();
  if (S.shake > 0) ctx.translate(rnd(-S.shake, S.shake), rnd(-S.shake, S.shake));

  if (!fondoOff || fondoOff.width !== Math.round(W * RATIO)) prepararFondo();
  ctx.drawImage(fondoOff, 0, 0, W, H);

  dibujarBebes();
  dibujarCuna();

  // babas
  S.slime.forEach(s => {
    const sq = 1 + Math.sin(s.phase) * .12;
    drawImg('fx_moquito', s.x + Math.sin(s.phase) * 6, s.y, s.r * 2.2 * sq, null, {});
  });

  dibujarVirus();

  // powerups
  S.pow.forEach(q => {
    const bob = Math.sin(q.phase) * 6;
    ctx.save();
    ctx.globalAlpha = .9;
    ctx.fillStyle = '#fff';
    ctx.beginPath(); ctx.arc(q.x, q.y + bob, q.r + 6, 0, 6.28);
    ctx.shadowColor = q.key === 'estrella' ? '#ffd23f' : '#7ee0ff';
    ctx.shadowBlur = 18; ctx.fill();
    ctx.restore();
    drawImg(q.key, q.x, q.y + bob, q.r * 2, null, {});
  });

  // efectos
  S.fx.forEach(f => {
    const k = f.t / f.dur;
    drawImg(f.img, f.x, f.y, f.size * (.6 + k * .7), null, { alpha: 1 - k });
  });

  // textos flotantes
  S.txts.forEach(t => {
    const k = t.t / t.dur;
    ctx.save();
    ctx.globalAlpha = 1 - k;
    ctx.font = `800 ${t.big ? 26 : 20}px 'Baloo 2',sans-serif`;
    ctx.textAlign = 'center';
    ctx.lineWidth = 5; ctx.strokeStyle = 'rgba(90,30,80,.75)';
    ctx.strokeText(t.txt, t.x, t.y - k * 42);
    ctx.fillStyle = t.col;
    ctx.fillText(t.txt, t.x, t.y - k * 42);
    ctx.restore();
  });

  ctx.restore();  // fin shake

  dibujarHUD();

  if (S.flash > 0) {
    ctx.fillStyle = `rgba(255,60,90,${S.flash * .35})`;
    ctx.fillRect(0, 0, W, H);
  }
}

function dibujarHUD() {
  // puntuación
  ctx.save();
  ctx.fillStyle = 'rgba(255,255,255,.9)';
  rr(10, 62, 118, 38, 19); ctx.fill();
  drawImg('estrella', 30, 81, 26, null, {});
  ctx.font = "800 21px 'Baloo 2',sans-serif";
  ctx.fillStyle = '#7a2f86'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
  ctx.fillText(S.score, 48, 83);

  // barra de tiempo
  const bw = 168, bx = W / 2 - bw / 2;
  ctx.fillStyle = 'rgba(255,255,255,.9)';
  rr(bx - 6, 6, bw + 12, 30, 15); ctx.fill();
  const k = clamp(S.t / ROUND_TIME, 0, 1);
  ctx.fillStyle = k < .7 ? '#8bd450' : '#ffb02e';
  rr(bx, 12, Math.max(12, bw * (1 - k)), 18, 9); ctx.fill();
  ctx.font = "800 15px 'Baloo 2',sans-serif";
  ctx.fillStyle = '#5b2a6b'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillText('¡Resiste! ' + Math.max(0, Math.ceil(ROUND_TIME - S.t)) + 's', W / 2, 48);

  // x2
  if (S.doubleT > 0) {
    ctx.fillStyle = 'rgba(255,210,63,.95)';
    rr(W / 2 - 40, 70, 80, 26, 13); ctx.fill();
    ctx.font = "800 15px 'Baloo 2',sans-serif";
    ctx.fillStyle = '#7a4a00';
    ctx.fillText('x2 ' + Math.ceil(S.doubleT) + 's', W / 2, 84);
  }

  // pausa
  ctx.fillStyle = 'rgba(255,255,255,.92)';
  ctx.beginPath(); ctx.arc(W - 38, 80, 25, 0, 6.28); ctx.fill();
  drawImg('pausa', W - 38, 80, 34, null, {});
  ctx.restore();
}

// ---------- entrada ----------
function coords(e) {
  const r = canvas.getBoundingClientRect();
  const cx = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
  const cy = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
  return { x: cx * W / r.width, y: cy * H / r.height };
}

function tap(x, y) {
  if (S.fase !== 'playing') return;
  Audio2.init();
  // pausa
  if (Math.hypot(x - (W - 38), y - 80) < 32) { pausar(); return; }

  // powerups (radio generoso)
  for (let i = S.pow.length - 1; i >= 0; i--) {
    const q = S.pow[i];
    if (Math.hypot(x - q.x, y - q.y) < q.r + 26) { collect(q, i); return; }
  }
  // babas
  for (let i = S.slime.length - 1; i >= 0; i--) {
    const s = S.slime[i];
    if (Math.hypot(x - s.x, y - s.y) < s.r + 22) {
      S.slime.splice(i, 1);
      S.fx.push({ img: 'fx_puf', x: s.x, y: s.y, t: 0, dur: .3, size: 70 });
      S.score += 20; Audio2.pop();
      return;
    }
  }
  // virus (el más cercano al toque)
  let best = -1, bd = 1e9;
  S.vir.forEach((v, i) => {
    const d = Math.hypot(x - (v.x + Math.sin(v.phase) * v.sway), y - v.y);
    if (d < v.r + 20 && d < bd) { bd = d; best = i; }
  });
  if (best >= 0) {
    const v = S.vir[best];
    if (v.hp > 1) {
      v.hp--; v.hitT = .45; v.speed *= 1.18;
      S.fx.push({ img: 'fx_puf', x: v.x, y: v.y, t: 0, dur: .3, size: v.r * 2.6 });
      S.txts.push({ txt: '¡Otro golpe!', x: v.x, y: v.y - 12, t: 0, dur: .8, col: '#fff' });
      Audio2.pop();
    } else pop(v, best);
    return;
  }
  Audio2.miss();
}

canvas.addEventListener('pointerdown', e => { e.preventDefault(); const c = coords(e); tap(c.x, c.y); });

// ---------- pausa / flujos ----------
const $ = id => document.getElementById(id);
const menuEl = $('menu'), pauseEl = $('pausePanel'), endEl = $('endPanel'), hintEl = $('hint');

function pausar() {
  if (S.fase !== 'playing') return;
  S.fase = 'paused';
  pauseEl.classList.remove('hidden');
}
function reanudar() {
  if (S.fase !== 'paused') return;
  S.fase = 'playing';
  pauseEl.classList.add('hidden');
  last = performance.now();
}
function irMenu() {
  pauseEl.classList.add('hidden');
  endEl.classList.add('hidden');
  menuEl.classList.remove('hidden');
  $('bestLine').textContent = S && S.best ? '🏆 Mejor puntuación: ' + S.best : '';
  refrescarTop5($('top5Menu'));
  S = null;
}
function mostrarFin(ganó) {
  $('endTitle').textContent = ganó ? '¡Ganaste! 🎉' : '¡Se resfriaron! 🤧';
  $('endMsg').textContent = ganó
    ? 'Mica y Vale se mantuvieron sanas durante ' + ROUND_TIME + ' segundos. ¡Eres su guardaespaldas!'
    : 'Los virus llegaron a la cuna y las bebés se resfriaron. ¡Inténtalo de nuevo!';
  $('endScore').textContent = 'Puntos: ' + S.score + (S.score >= S.best && S.score > 0 ? '  🏆 ¡Récord!' : '');
  $('endImg1').src = url(ganó ? 'mica_celebrando' : 'mica_enferma');
  $('endImg2').src = url(ganó ? 'vale_celebrando' : 'vale_enferma');
  if (S.guardado) {
    $('saveBox').classList.add('hidden');
  } else {
    $('saveBox').classList.remove('hidden');
    $('btnSave').disabled = false;
    $('btnSave').textContent = '💾 Guardar en el Top 5';
    $('playerName').value = USUARIO ? USUARIO.nombre : (localStorage.getItem('mv_nombre') || '');
    pintarUsuario();
  }
  endEl.classList.remove('hidden');
  refrescarTop5($('top5End'));
}

$('btnPlay').onclick = () => {
  Audio2.init();
  menuEl.classList.add('hidden');
  endEl.classList.add('hidden');
  nuevoJuego();
  mostrarHint('¡Toca los virus antes de que suban a la cuna! 🛟', 3200);
};
$('btnResume').onclick = reanudar;
$('btnRestart').onclick = () => { pauseEl.classList.add('hidden'); nuevoJuego(); };
$('btnMenu').onclick = irMenu;
$('btnAgain').onclick = () => { endEl.classList.add('hidden'); nuevoJuego(); };
$('btnMenu2').onclick = irMenu;
$('btnSound').onclick = e => {
  Audio2.init();
  Audio2.muted = !Audio2.muted;
  e.currentTarget.textContent = Audio2.muted ? '🔇' : '🔊';
};
$('btnSave').onclick = async () => {
  const nombre = USUARIO ? USUARIO.nombre
                         : $('playerName').value.trim().slice(0, 20);
  if (!nombre) { $('playerName').focus(); return; }
  localStorage.setItem('mv_nombre', nombre);
  $('btnSave').disabled = true;
  $('btnSave').textContent = '⏳ Guardando…';
  const lista = await top5Guardar(nombre, S ? S.score : 0);
  if (S) S.guardado = true;
  pintarTop5(lista, $('top5End'));
  refrescarTop5($('top5Menu'));
  $('saveBox').classList.add('hidden');
};
$('playerName').addEventListener('keydown', e => { if (e.key === 'Enter') $('btnSave').click(); });
$('btnGoogle').onclick = entrarConGoogle;
$('btnGoogleEnd').onclick = entrarConGoogle;
$('btnLogout').onclick = salir;
document.addEventListener('keydown', e => {
  if (e.key === 'Escape' || e.key.toLowerCase() === 'p') {
    if (!pauseEl.classList.contains('hidden')) reanudar(); else pausar();
  }
});

let hintTimer = null;
function mostrarHint(txt, ms) {
  hintEl.textContent = txt;
  hintEl.classList.remove('hidden');
  hintEl.style.opacity = 1;
  clearTimeout(hintTimer);
  hintTimer = setTimeout(() => { hintEl.style.opacity = 0; }, ms);
}

// ---------- pausa automática al ocultar la pestaña ----------
// Evita que las bebés "se resfríen" en segundo plano mientras el jugador mira otra cosa.
document.addEventListener('visibilitychange', () => {
  if (document.hidden) { if (S && S.fase === 'playing') pausar(); }
  else last = performance.now();
});

// ---------- bucle ----------
let last = performance.now();
function loop(now) {
  const dt = Math.min(.05, (now - last) / 1000);
  last = now;
  if (S) {
    update(dt);
    dibujarTodo();
  }
  requestAnimationFrame(loop);
}

// API mínima para pruebas / depuración desde la consola del navegador.
window.MicaVale = {
  start: () => { menuEl.classList.add('hidden'); nuevoJuego(); },
  step: (dt) => { update(dt); dibujarTodo(); },
  tap,
  state: () => S,
  set: (o) => Object.assign(S, o),
  final: (win) => finalizar(win),
  finNow: (win) => { if (S && S.fase === 'playing') finalizar(win); mostrarFin(win); },
};

cargar(async () => {
  prepararFondo();
  $('bestLine').textContent = localStorage.getItem('mv_best') > 0
    ? '🏆 Mejor puntuación: ' + localStorage.getItem('mv_best') : '';
  // ¿volvimos de login con Google? (#access_token en la URL)
  await procesarCallback();
  if (!USUARIO) await cargarUsuario();   // sesión guardada de antes
  pintarUsuario();
  refrescarTop5($('top5Menu'));
  requestAnimationFrame(loop);
});

})();
