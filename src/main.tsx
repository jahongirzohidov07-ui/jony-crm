import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { detectAppMode } from './lib/appMode'

// Jony Student PWA'dan ochilganini birinchi qatorda aniqlab olamiz
detectAppMode()

// Yangi versiya chiqqanda ochiq turgan tab eski JS bo'laklarini qidirib
// topolmaydi va sahifa "Yuklanmoqda..."da qotib qoladi. Vite bunda
// "vite:preloadError" hodisasini beradi — bir marta o'zi yangilab olamiz.
window.addEventListener('vite:preloadError', (e) => {
  e.preventDefault()
  const k = 'jonyos_chunk_reload'
  if (!sessionStorage.getItem(k)) {
    sessionStorage.setItem(k, '1')
    window.location.reload()
  }
})
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
