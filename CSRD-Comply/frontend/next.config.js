/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',

  /**
   * 🔒 ATTENZIONE: Non usare rewrites per proxy API!
   * 
   * HttpOnly cookie JWT NON vengono inviati dal proxy server-side di Next.js.
   * Il frontend deve chiamare il backend DIRETTAMENTE dal browser usando
   * l'URL completo configurato in NEXT_PUBLIC_API_URL.
   * 
   * In sviluppo locale, usa NEXT_PUBLIC_API_URL=http://localhost:8000
   * in .env.local per chiamare FastAPI direttamente.
   */
}

module.exports = nextConfig
