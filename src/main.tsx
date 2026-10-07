import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { detectAppMode } from './lib/appMode'
import { installNativeBridge } from './lib/nativeBridge'

// Jony Student PWA'dan ochilganini birinchi qatorda aniqlab olamiz
detectAppMode()
// Android ilovasi (2-versiya) ichida: ovoz va nutq tanish ko'prigi
installNativeBridge()

// YANGI VERSIYA CHIQQANDA (2026-08-24 kengaytirildi).
//
// Deploy bo'lgach ochiq turgan tab eski JS bo'laklarini qidiradi va
// topolmaydi — sahifa yiqiladi ("Bu bo'limni ochishda xatolik").
// Kuniga bir necha marta deploy qilinganda bu tez-tez uchraydi.
//
// Uch qatlam himoya:
//   1. Vite'ning "vite:preloadError" hodisasi;
//   2. Har qanday dinamik import xatosi (SW keshi sabab ham bo'ladi);
//   3. Muvaffaqiyatli yuklangach bayroq tozalanadi — ya'ni himoya
//      HAR deployda qaytadan ishlaydi, bir martalik emas.
const RELOAD_KEY = 'jonyos_chunk_reload'

function isChunkError(msg: string) {
  const m = (msg || '').toLowerCase()
  return (
    m.includes('dynamically imported module') ||
    m.includes('failed to fetch dynamically') ||
    m.includes('importing a module script failed') ||
    m.includes('loading chunk') ||
    m.includes('loading css chunk')
  )
}

export function reloadOnceForNewVersion(): boolean {
  if (sessionStorage.getItem(RELOAD_KEY)) return false
  sessionStorage.setItem(RELOAD_KEY, '1')
  window.location.reload()
  return true
}

window.addEventListener('vite:preloadError', (e) => {
  e.preventDefault()
  reloadOnceForNewVersion()
})

window.addEventListener('unhandledrejection', (e) => {
  const msg = String((e as PromiseRejectionEvent).reason?.message || '')
  if (isChunkError(msg)) reloadOnceForNewVersion()
})

// Ilova muammosiz yuklandi — bayroqni tozalaymiz, keyingi deployda
// himoya yana ishlasin.
window.addEventListener('load', () => {
  setTimeout(() => sessionStorage.removeItem(RELOAD_KEY), 4000)
})

// SERVIS WORKER YANGILANGANDA. PWA (Jony Student / ota-ona ilovasi)
// eski qobiqni ushlab turmasin: yangi servis worker boshqaruvni
// olganda sahifani bir marta yangilaymiz. Birinchi o'rnatishda
// (controller hali yo'q) yangilanmaydi — aks holda aylanib qolardi.
if ('serviceWorker' in navigator) {
  const hadController = !!navigator.serviceWorker.controller
  let swReloaded = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (!hadController || swReloaded) return
    swReloaded = true
    window.location.reload()
  })
}
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
