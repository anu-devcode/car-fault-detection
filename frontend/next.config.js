/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    const origin = (process.env.PLATFORM_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
    return [{ source: '/api/platform/:path*', destination: `${origin}/platform/:path*` }]
  },
  async headers() {
    return [
      {
        source: '/dashboard',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'same-origin' },
        ],
      },
    ]
  },
}

module.exports = nextConfig
