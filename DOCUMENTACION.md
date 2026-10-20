# 🎮 Mica & Vale vs. El Resfrio — Documentación del proyecto

Juego web de defensa para tocar en pantalla. Hecho con **HTML + CSS + JavaScript puro**
(sin frameworks, sin build, sin dependencias). Se juega tocando los virus antes de
que suban a la cuna de las bebés Mica y Vale. Hay que resistir **60 segundos**.

---

## 📁 Estructura del proyecto

```
JUEGO_MICA_VALE/
├── index.html          ← página principal (interfaz + estilos)
├── js/
│   └── game.js         ← toda la lógica del juego + Top 5 + login Google
├── assets/
│   ├── fondo_hd.jpg    ← fondo de la habitación
│   ├── portada_hd.jpg  ← portada del menú
│   └── sprites/        ← bebés, virus, efectos, botones, corazones...
├── background/         ← originales de fondo (no usados por el juego)
├── personajes/         ← arte de personajes (no usado por el juego)
├── Arte/               ← bocetos y concepto (no usar al publicar)
└── tools/              ← scripts Python de recorte/limpieza de sprites
```

> ⚠️ Al subir a la web, sube **solo** `index.html`, `js/` y `assets/`.
> Las carpetas `Arte/`, `tools/`, `background/` y `personajes/` no son necesarias.

---

## 🕹️ Cómo funciona el juego

| Elemento | Valor |
|---|---|
| Lienzo lógico | 480 × 800 px (vertical, estilo móvil) |
| Línea de peligro | `DANGER_Y = 228` (baranda de la cuna) |
| Cabezas de las bebés | `BABY_Y = 192` |
| Duración de la ronda | `ROUND_TIME = 60` segundos |
| Vidas de cada bebé | 3 corazones (6 en total) |

**Tipos de virus** (velocidad, puntos y vida):

| Tipo | Velocidad | Puntos | Vida | Nota |
|---|---|---|---|---|
| `normal` | 1.00 | 100 | 1 | el básico |
| `enojado` | 1.38 | 150 | 1 | rápido |
| `sorprendido` | 0.86 | 120 | 1 | se mueve mucho de lado |
| `baba` | 0.78 | 180 | 1 | lanza babas que también restan vida |
| `grande` | 0.66 | 250 | **2** | hay que tocarlo dos veces |
| `pequeno` | 1.75 | 200 | 1 | muy rápido |
| `rojo` | 1.95 | 350 | 1 | el más rápido, aparece en el último tercio |

**Power-ups:**
- 🍭 `patito` — +100 puntos
- ⭐ `estrella` — puntos ×2 durante 8 s
- 🩹 `vida_extra` — devuelve un corazón a la bebé que menos vida tenga
- 🤧 `panuelo` — "pañuelazo": elimina todos los virus en pantalla (+50 c/u)

**Combo:** encadenar toques da multiplicador hasta ×5. Si pasan 2.6 s sin tocar nada, se reinicia.

**Dificultad progresiva:** los virus salen más seguidos y más rápido según avanza el tiempo, y a partir del 50% salen dobles, y del 78% a veces triples.

---

## ✅ Cambios realizados hasta ahora

### 1. Ejecución del proyecto
- Se sirvió el juego en local con un servidor HTTP (`python -m http.server 8080`)
- Se comprobó que carga sin errores de consola, el menú, la partida, la pausa,
  la pantalla final y el reinicio funcionan correctamente.

### 2. Ranking Top 5 (global o local)

**En `index.html`:**
- Caja "🏆 Top 5 jugadores" visible en el menú y en la pantalla final.
- Campo de nombre + botón "💾 Guardar en el Top 5" al terminar la partida.
- Estilos `.top5`, `.miniAv`, `#saveBox`, `#playerName`.

**En `js/game.js`:**
- `top5Leer()` — lee el Top 5 desde Supabase, o desde `localStorage` si no está configurado.
- `top5Guardar()` — guarda la puntuación con respaldo local **siempre**.
- `pintarTop5()` — dibuja el ranking con medallas 🥇🥈🥉, avatares y puntos.
- Control de "ya guardado" (`S.guardado`) para que el formulario no reaparezca.
- Se subió la versión de caché a `?v=20261020b` para forzar la recarga.

### 3. Login con Google (Supabase Auth)

**En `index.html`:**
- Caja de login en el menú con botón "🔵 Entrar con Google".
- Al iniciar sesión, el botón se sustituye por un **chip con tu foto + nombre + botón Salir**.
- En la pantalla final aparece tu foto y nombre, y el botón de Google si aún no entraste.
- Estilos `#loginBox`, `#btnGoogle`, `.userChip`, `#btnLogout`, `#endUser`.

**En `js/game.js`:**
- `entrarConGoogle()` — redirige a Supabase Auth con `provider=google`.
- `procesarCallback()` — recoge el `#access_token` que Google devuelve al volver y limpia la URL.
- `cargarUsuario()` — llama a `/auth/v1/user` y extrae `full_name` y `avatar_url` de tu cuenta Google.
- `salir()` — borra el token y vuelve al modo invitado.
- `pintarUsuario()` — pinta el estado de login (chip o botón) en menú y pantalla final.
- `sbFetch()` — usa **tu token** en lugar del anónimo para que la política
  `auth.uid() = user_id` permita insertar solo tus propias filas.
- Avatares circulares en el ranking y escapado de HTML en nombres y URLs (seguridad).

> 🔎 **Estado actual:** el botón de Google está implementado pero **oculto** hasta que
> configures Supabase (`SB_URL` y `SB_KEY`). Mientras tanto, el juego funciona en
> **modo local**: el ranking se guarda en `localStorage` (solo ese navegador).

---

## 🚀 Pasos para publicar en la web (gratis)

### Opción A — Netlify Drop (la más fácil, sin Git)
1. Entra en https://app.netlify.com/drop
2. Arrastra la carpeta del proyecto (solo `index.html`, `js/`, `assets/`)
3. Te da una URL al instante, gratis y con HTTPS.
4. Luego crea cuenta con tu email para conservarla y poner nombre propio.

### Opción B — GitHub Pages (permanente, con control de versiones)
1. Cuenta gratis en https://github.com
2. Nuevo repositorio público (ej. `juego-mica-vale`) → sube los archivos conservando la estructura.
3. **Settings → Pages → Source:** *Deploy from a branch*, **Branch:** `main` → Save.
4. En 1–2 min estará en `https://tuusuario.github.io/juego-mica-vale/`

---

## 🏆 Configurar el Top 5 mundial (Supabase, gratis y sin tarjeta)

1. Cuenta gratis en https://supabase.com → **New Project** (elige región de Europa, guarda la contraseña).
2. **SQL Editor** → pega y ejecuta:

```sql
drop policy if exists "insersion publica" on scores;
drop table if exists scores;
create table scores (
  id bigint generated always as identity primary key,
  user_id uuid,
  nombre text not null check (char_length(nombre) between 1 and 20),
  avatar text,
  puntos integer not null,
  created_at timestamp with time zone default now()
);
alter table scores enable row level security;
create policy "lectura publica" on scores for select using (true);
create policy "solo el propio usuario" on scores for insert
  with check (auth.uid() = user_id);
```

3. **Project Settings → API** → copia la **Project URL** y la **anon public key**.
4. Pega esas dos claves en `js/game.js` (líneas ~152-153):

```js
const SB_URL = 'https://abcdefghij.supabase.co';   // tu URL
const SB_KEY = 'eyJhbGciOi...';                    // tu anon public key
```

5. Vuelve a subir el archivo. Ya tienes ranking mundial.

---

## 🔐 Configurar el login con Google

### Paso 1 — Google Cloud Console
1. Entra en https://console.cloud.google.com/
2. Arriba, crea un **proyecto nuevo** (ej. `juego-mica-vale`).
3. **APIs y servicios → Biblioteca** → busca **"Google People API"** → *Activar*.
   (Necesaria para leer tu nombre y tu foto.)
4. **APIs y servicios → Pantalla de consentimiento OAuth:**
   - Tipo: *Externo* → Crear
   - Nombre de la app, email de soporte → Guardar
   - En **Usuarios de prueba** añade **tu propio Gmail**
     (mientras la app no esté verificada, solo tú podrás entrar)
   - *Guardar y continuar*
5. **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth:**
   - Tipo: **Aplicación web**
   - **Orígenes autorizados de JavaScript:** la URL de tu juego (ej. `https://tu-juego.netlify.app`)
   - **URIs de redirección autorizados:** esa misma URL **con `/` final**
   - Copia el **Client ID** y el **Client secret**

### Paso 2 — Supabase
6. **Authentication → Sign In / Providers → Google** → activar → pega Client ID y Client secret → Save.
7. **Authentication → URL Configuration:**
   - *Site URL:* la URL de tu juego
   - *Redirect URLs:* añade `https://tu-juego.netlify.app/**`

---

## ⚠️ Avisos importantes

- **La URL debe coincidir exactamente** entre Google Cloud y Supabase (con `/` final
  en los *redirect URLs*). Si no, verás el error `redirect_uri_mismatch`.
- Mientras la app de Google **no esté verificada**, solo entrarán los usuarios
  añadidos en "Usuarios de prueba". Para abrirlo a más gente hay que verificar la
  app (gratis, pero con formulario y tiempo de espera).
- El guardado en la nube **requiere sesión**. Sin ella, el botón de guardar
  desaparece y el juego queda en modo local.
- El servidor local de pruebas se lanza con:
  ```bash
  python -m http.server 8080 --bind 127.0.0.1
  ```
  y se abre en `http://127.0.0.1:8080/index.html`

---

## 🧪 API de pruebas (consola del navegador)

El juego expone `window.MicaVale` para depurar desde la consola:

```js
MicaVale.start()          // empieza una partida
MicaVale.step(0.016)      // avanza un frame manualmente
MicaVale.tap(x, y)        // simula un toque en coordenadas lógicas
MicaVale.state()          // devuelve el estado del juego
MicaVale.set({score: 999})// modifica el estado
MicaVale.final(true)      // termina la partida (true = ganar)
MicaVale.finNow(true)     // termina y muestra la pantalla final ya
```

---

*Última actualización: 20 de octubre de 2026 — versión de caché `?v=20261020b`*
