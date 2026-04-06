import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './store/theme' // initialize theme store (applies dark/light class)
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
