# 🎮 Mica & Vale vs. El Resfrio — Documentación del proyecto

Juego web de defensa para tocar en pantalla. Hecho con **HTML + CSS + JavaScript puro**
(sin frameworks, sin build, sin dependencias). Se juega tocando los virus antes de
que suban a la cuna de las bebés Mica y Vale. Hay que resistir **60 segundos**.

**Jugando ya en:** https://alexeyu007.github.io/juego-mica-vale/
**Repositorio:** https://github.com/alexeyu007/juego-mica-vale

---

## 📁 Estructura del proyecto

```
JUEGO_MICA_VALE/
├── index.html          ← página principal (interfaz + estilos)
├── js/
│   └── game.js         ← toda la lógica del juego + Top 5 + login Google + vibración
├── assets/
│   ├── fondo_hd.jpg    ← fondo de la habitación (se dibuja en el lienzo)
│   └── sprites/        ← bebés, virus, efectos, botones, corazones...
├── Arte/
│   └── pantalla_inicial.png  ← portada del menú (⭐ se usa como fondo del menú)
├── background/         ← originales de fondo (no usados por el juego)
├── personajes/         ← arte de personajes (no usado por el juego)
└── tools/              ← scripts Python de recorte/limpieza de sprites
```

> ⚠️ Para publicar hacen falta `index.html`, `js/`, `assets/` **y `Arte/`**
> (el menú usa `Arte/pantalla_inicial.png`). Las carpetas `tools/`,
> `background/` y `personajes/` no son necesarias.

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

**Combo:** encadenar toques da multiplicador hasta ×5 (×2 adicional con la estrella).
Si pasan 2.6 s sin tocar nada, se reinicia.

**Dificultad progresiva:** los virus salen más seguidos y más rápido según avanza el
tiempo, y a partir del 50% salen dobles, y del 78% a veces triples.

---

## 🧩 Cómo está montado el menú y el arranque

- **El menú es la propia portada** (`Arte/pantalla_inicial.png`), que ya trae el
  botón de play pintado. El botón real (`#btnPlay`) es un **área de clic transparente**
  superpuesta sobre ese play, así que no hay dos botones.
- **Abajo a la izquierda:** el botón de Google (abreviado). Con sesión iniciada se
  sustituye por tu foto + nombre + "Salir".
- **Abajo a la derecha:** un **botón-trofeo** 🏆 que abre un panel con el Top 5 y tu
  mejor puntuación. Se cierra pulsando el trofeo de nuevo o fuera del panel.
- **Intro de 5 s:** al pulsar JUGAR el estado pasa a `intro`, se muestra el mensaje
  "¡Toca los virus antes de que suban a la cuna!" y a los 5 s arranca la partida.
- En el lienzo se dibuja siempre el fondo (`dibujarFondo()`), también en el menú.

---

## 🎨 Controles, sonido y vibración

- **Pulsar virus** con el ratón o el dedo. La pausa se activa con `Esc` / `P`.
- **Botón 🔊** (arriba a la derecha) — silencia/activa el sonido.
- **Botón 📳** — activa/desactiva la **vibración** (solo en dispositivos táctiles;
  en pantallas sin vibración no aparece).
- La vibración se dispara al tocar un virus, al fallar, al recibir daño, al coger un
  power-up y al ganar/perder. La preferencia se guarda en el navegador.

---

## 🏆 Top 5: local y mundial (con respaldo)

- **Con sesión de Google:** la puntuación se guarda en **Supabase** (la tabla
  `scores`, con la política `auth.uid() = user_id`, así que cada uno solo inserta
  sus propias filas) y se muestra el ranking mundial.
- **Sin sesión o si falla la nube:** se guarda en **`localStorage`** del dispositivo
  y se muestra el "Top 5 de este dispositivo".
- El guardado es **automático** al terminar la partida (no hay formulario ni botón
  de guardar). El mensaje final te dice si se subió a la nube o se quedó local.
- `top5Guardar()` devuelve si la fila llegó a la nube, para no prometer una subida
  que falló.

### ✨ Solo se guarda si mejoras tu marca

La puntuación **solo se registra en el Top 5 si supera la mejor marca que ese
jugador ya tenía**:

- **Con sesión:** se consulta la fila más alta del jugador en Supabase
  (`mejorDeJugador()`); si la nueva no la supera, no se inserta nada.
- **Sin sesión:** se compara contra la marca local de ese nombre.
- Cada jugador ocupa **una sola casilla** con su mejor puntuación: al mejorar, se
  sustituye su registro anterior (en local se filtra por nombre; en el ranking
  mundial `top5Leer()` agrupa por `user_id` y se queda con la fila más alta).
- Si no mejora, la pantalla final avisa: *«🔒 X pts: no mejora tu mejor marca de
  Y pts, el Top 5 no cambia»*.

---

## 🚀 Publicación (gratis)

El juego está publicado en **GitHub Pages** (gratis, con HTTPS y control de versiones):

1. Repositorio público en https://github.com (ej. `juego-mica-vale`).
2. **Settings → Pages → Source:** *Deploy from a branch*, **Branch:** `main` → Save.
3. Queda en `https://tuusuario.github.io/juego-mica-vale/`

Para publicar cambios basta con hacer `git push` a `main`; Pages lo redespliega solo.

*(Alternativa sin Git: Netlify Drop, arrastrando la carpeta en https://app.netlify.com/drop)*

---

## 🏆 Configurar el Top 5 mundial (Supabase, gratis y sin tarjeta)

1. Cuenta gratis en https://supabase.com → **New Project** (elige región, guarda la contraseña).
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
4. Pega esas dos claves en `js/game.js` (constantes `SB_URL` y `SB_KEY`).
5. Vuelve a subir el archivo. Ya tienes ranking mundial.

---

## 🔐 Login con Google (Supabase Auth)

Ya está **configurado y funcionando** en el proyecto publicado. El flujo, por si hay
que repetirlo:

### Paso 1 — Google Cloud Console
1. https://console.cloud.google.com/ → crear proyecto.
2. **APIs y servicios → Biblioteca** → activar **Google People API** (lee nombre y foto).
3. **Pantalla de consentimiento OAuth:** tipo *Externo*, añade tu Gmail en *Usuarios de prueba*.
4. **Credenciales → ID de cliente de OAuth** (tipo *Aplicación web*):
   - *Orígenes autorizados de JavaScript:* la URL del juego
   - *URIs de redirección autorizados:* esa misma URL **con `/` final**
   - Copia **Client ID** y **Client secret**

### Paso 2 — Supabase
5. **Authentication → Providers → Google** → activar → pega Client ID y Client secret.
6. **Authentication → URL Configuration:** *Site URL* y *Redirect URLs* (con `/**`).

---

## ⚠️ Avisos importantes

- **La URL debe coincidir exactamente** entre Google Cloud y Supabase (con `/` final
  en los *redirect URLs*), o verás `redirect_uri_mismatch`.
- Mientras la app de Google **no esté verificada**, solo entrarán los usuarios en
  "Usuarios de prueba".
- El guardado en la nube **requiere sesión**; sin ella, el juego funciona igual en
  modo local.
- **Los secretos nunca se pegan en el chat ni en el repositorio:** el *Client secret*
  de Google va únicamente en Supabase; en el código solo van la URL y la *anon key*.
- El servidor local de pruebas:
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
MicaVale.vibra()          // estado de la vibración (móvil / soportado / activo)
```

---

*Última actualización: 21 de octubre de 2026 — versión de caché `?v=20261021g`*
