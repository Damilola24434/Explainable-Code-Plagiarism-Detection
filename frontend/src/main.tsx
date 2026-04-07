// about the main entry point for the frontend application
// this is the frontend entry point that starts the react app and mounts it into the  HTML page
// it import index.css and the main app component

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import './ui-refresh.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
