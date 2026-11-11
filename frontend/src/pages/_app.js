import '../styles/globals.css'
import { Inter, Outfit } from 'next/font/google'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })
const outfit = Outfit({ subsets: ['latin'], variable: '--font-outfit' })

function MyApp({ Component, pageProps }) {
  return (
    <div className={`${inter.variable} ${outfit.variable}`}>
      <Component {...pageProps} />
    </div>
  )
}

export default MyApp
