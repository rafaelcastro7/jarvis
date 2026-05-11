---
name: react-course-player
description: Build de un LMS/course player React completo con sidebar responsive, video/audio player local, progreso persistido en sessionStorage, dark theme premium y mobile-first. Basado en RAIO English Course clone.
tools: Read, Write, Edit, Bash
---

# React Course Player — LMS Clone

## Stack
- React 19 + TypeScript strict
- Vite 8 + `@tailwindcss/vite` (v4, sin config file)
- CSS custom properties + vanilla CSS (no Tailwind classes en JSX)
- sessionStorage para progreso (nunca localStorage)

---

## Estructura de archivos

```
src/
  App.tsx                    # Estado global, routing de lecciones
  index.css                  # Design system completo con CSS vars
  courseData.json            # Datos del curso (generado por scraper)
  components/
    Sidebar.tsx              # Navegación módulos/lecciones + responsive
    LessonPlayer.tsx         # Player video/audio/texto
```

---

## Design Tokens (index.css)

```css
:root {
  --bg:        #080812;    /* fondo principal */
  --bg2:       #0e0e1f;    /* sidebar, cards secundarias */
  --bg3:       #141428;    /* superficies */
  --surface:   #1a1a35;
  --surface2:  #20203f;
  --accent:    #e040a0;    /* rosa primary */
  --accent2:   #7c3aed;    /* púrpura secondary */
  --accent3:   #06b6d4;    /* cyan audio */
  --text:      #f0f0f8;
  --text2:     #b0b0cc;
  --muted:     #6666aa;
  --border:    rgba(255,255,255,0.06);
  --border2:   rgba(255,255,255,0.1);
  --sidebar-w: 320px;
  --topbar-h:  56px;
  --radius:    16px;
  --radius-sm: 10px;
  --transition: 0.2s cubic-bezier(0.4,0,0.2,1);
}
```

---

## App.tsx — Estado global

```tsx
import { useState, useMemo, useEffect } from 'react'
import { Sidebar } from './components/Sidebar'
import { LessonPlayer } from './components/LessonPlayer'
import courseData from './courseData.json'
import './index.css'

export type Lesson = {
  id: string; index: string; title: string; type: string
  vimeo_id?: string | null
  audio_src?: string | null
  text_preview?: string
  video_file?: string | null  // precalculado en Python — NO recalcular en JS
}

export const allLessons: Lesson[] =
  (courseData as any).modules.flatMap((m: any) => m.lessons)

const STORAGE_KEY = 'course_completed'

export default function App() {
  const [activeLessonId, setActiveLessonId] = useState(() =>
    sessionStorage.getItem('course_last') || allLessons[0]?.id || ''
  )
  const [completed, setCompleted] = useState<Set<string>>(() => {
    try { return new Set(JSON.parse(sessionStorage.getItem(STORAGE_KEY) || '[]')) }
    catch { return new Set() }
  })
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const activeLesson = useMemo(
    () => allLessons.find(l => l.id === activeLessonId) ?? allLessons[0],
    [activeLessonId]
  )
  const idx = allLessons.findIndex(l => l.id === activeLessonId)
  const pct = allLessons.length
    ? Math.round(completed.size / allLessons.length * 100) : 0

  useEffect(() => {
    sessionStorage.setItem('course_last', activeLessonId)
  }, [activeLessonId])

  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') setSidebarOpen(false) }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [])

  const markDone = (id: string) =>
    setCompleted(prev => {
      const next = new Set(prev).add(id)
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify([...next]))
      return next
    })

  const selectLesson = (lesson: Lesson) => {
    setActiveLessonId(lesson.id)
    setSidebarOpen(false)  // cierra sidebar en mobile
  }

  const goNext = () => { if (idx < allLessons.length - 1) setActiveLessonId(allLessons[idx+1].id) }
  const goPrev = () => { if (idx > 0) setActiveLessonId(allLessons[idx-1].id) }

  return (
    <div className="app">
      <div className={`sidebar-backdrop${sidebarOpen ? ' visible' : ''}`}
           onClick={() => setSidebarOpen(false)} aria-hidden />
      <Sidebar activeLessonId={activeLessonId} completed={completed}
               onSelect={selectLesson} isOpen={sidebarOpen}
               onClose={() => setSidebarOpen(false)} />
      <div className="content-area">
        {/* Mobile topbar */}
        <header className="topbar">
          <button className="topbar-menu-btn"
                  onClick={() => setSidebarOpen(true)} aria-label="Menú">☰</button>
          <div className="topbar-title">{activeLesson?.title}</div>
          <span className="topbar-pct">{pct}%</span>
        </header>
        {activeLesson && (
          <LessonPlayer lesson={activeLesson} allLessons={allLessons}
                        idx={idx} completed={completed}
                        onComplete={markDone} onNext={goNext} onPrev={goPrev} />
        )}
      </div>
    </div>
  )
}
```

---

## Sidebar.tsx — Responsive con auto-scroll

```tsx
import { useState, useEffect, useRef } from 'react'

export function Sidebar({ activeLessonId, completed, onSelect, isOpen, onClose }) {
  const modules = courseData.modules
  const activeMod = modules.find(m => m.lessons.some(l => l.id === activeLessonId))
  const [open, setOpen] = useState(new Set([activeMod?.id].filter(Boolean)))
  const activeItemRef = useRef(null)
  const scrollRef = useRef(null)

  // Abrir módulo activo al cambiar lección
  useEffect(() => {
    if (activeMod) setOpen(prev => new Set([...prev, activeMod.id]))
  }, [activeMod?.id])

  // Auto-scroll al item activo
  useEffect(() => {
    if (activeItemRef.current) {
      activeItemRef.current.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }
  }, [activeLessonId])

  // ... render
}
```

---

## LessonPlayer.tsx — Video con fallback

```tsx
{hasVideo && (
  <div className="video-container">
    <div className="video-aspect">
      {localVideo ? (
        <video key={localVideo} controls preload="metadata"
               onError={e => {
                 e.currentTarget.style.display = 'none'
                 const fb = e.currentTarget.nextElementSibling as HTMLElement
                 if (fb) fb.style.display = 'flex'
               }}>
          <source src={localVideo} type="video/mp4" />
        </video>
      ) : null}
      <div className="video-placeholder"
           style={{ display: localVideo ? 'none' : 'flex' }}>
        <div className="video-placeholder-icon">▶</div>
        <div className="video-placeholder-text">Video descargando...</div>
      </div>
    </div>
  </div>
)}
```

**Regla video/fallback:** El placeholder empieza con `display:none` cuando hay `localVideo`.
Al error del video, se hace display:none en video y se remueve el display del placeholder.

---

## Responsive CSS (3 breakpoints)

```css
/* Desktop > 1024px: sidebar fijo 320px */
/* Tablet 768-1024px: sidebar 280px, padding reducido */
@media (max-width: 1024px) {
  :root { --sidebar-w: 280px; }
  .content-inner { padding: 32px 32px 60px; }
}

/* Mobile < 768px: sidebar slide-in, topbar visible */
@media (max-width: 768px) {
  .topbar { display: flex; }
  .sidebar {
    position: fixed; top: 0; left: 0; height: 100vh;
    z-index: 300; transform: translateX(-100%);
    transition: transform 0.2s cubic-bezier(0.4,0,0.2,1);
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar-close-btn { display: flex !important; }
}

/* Mobile pequeño < 480px: buttons full width */
@media (max-width: 480px) {
  .nav-row { flex-direction: column; align-items: stretch; }
  .nav-row .btn { justify-content: center; }
}
```

---

## courseData.json — Estructura requerida

```json
{
  "name": "Nombre del Curso",
  "modules": [
    {
      "id": "mod_1",
      "name": "Módulo 1",
      "section_number": "1",
      "lesson_count": 10,
      "lessons": [
        {
          "id": "12345678",
          "index": "1-1",
          "title": "Lección de ejemplo",
          "type": "video",
          "vimeo_id": "768577280",
          "audio_src": "/audio/12345678_title.mp3",
          "text_preview": "Texto de la lección...",
          "video_file": "12345678_Leccion_de_ejemplo.mp4"
        }
      ]
    }
  ]
}
```

---

## vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
})
```

---

## Build y serve

```bash
# Limpiar temporales antes de build
rm -f public/videos/*.part* public/videos/*.ytdl

# Build producción
npm run build

# Serve local
npx serve -s dist -l 4200

# Tunnel público
cloudflared tunnel --url http://localhost:4200 --no-autoupdate &>/tmp/tunnel.log &
grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/tunnel.log | head -1
```
