/** @type {import('next').NextConfig} */
const nextConfig = {
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

  /**
   * output: 'standalone' è SOLO per Docker, non per Vercel.
   * Su Vercel si usa il comportamento predefinito.
   * Per Docker: decommentare la riga sottostante o passare
   * NEXT_OUTPUT=standalone come env var.
   */
  // output: process.env.NEXT_OUTPUT || undefined,
}

module.exports = nextConfig

