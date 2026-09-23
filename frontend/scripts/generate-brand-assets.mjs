/**
 * Gera os ícones e a imagem de compartilhamento do NexFi a partir da logo ("N em alta").
 *
 * Uso (dentro de frontend/):
 *   npm install --no-save @resvg/resvg-js
 *   node scripts/generate-brand-assets.mjs
 *
 * Os arquivos gerados em public/ são versionados; rode de novo só quando a logo mudar (e atualize
 * também src/components/BrandMark.tsx, que desenha a mesma arte no app). Depois de regerar,
 * incremente o ?v= dos ícones em index.html — os nomes não mudam, e sem isso navegadores e a
 * Cloudflare continuam mostrando o ícone antigo por um tempo.
 */
import { writeFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"
import { Resvg } from "@resvg/resvg-js"

const root = join(dirname(fileURLToPath(import.meta.url)), "..")
const publicDir = join(root, "public")
const fonts = [join(root, "scripts/fonts/SpaceGrotesk-600.ttf"), join(root, "scripts/fonts/SpaceGrotesk-400.ttf")]

const MIDNIGHT = "#0B0F19"
const TEAL = "#14BBA6"
const TEAL_LIGHT = "#5EEEA4"

/** O "N em alta" desenhado numa grade de 64×64. */
function mark({ stroke = 7, dot = 5.5 } = {}) {
  return (
    `<path d="M19 46V19L45 45V21" fill="none" stroke="${TEAL}" stroke-width="${stroke}" ` +
    `stroke-linecap="round" stroke-linejoin="round"/>` +
    `<circle cx="45" cy="18" r="${dot}" fill="${TEAL_LIGHT}"/>`
  )
}

/** Ícone quadrado 64×64. `rounded` = cantos arredondados (favicon); `scale` < 1 encolhe o N
 * em volta do centro (área segura dos ícones "maskable" e do iOS, que recortam as bordas). */
function iconSvg({ rounded = true, scale = 1, strokeBoost = 0 } = {}) {
  const offset = (64 - 64 * scale) / 2
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">` +
    `<rect width="64" height="64" ${rounded ? 'rx="14"' : ""} fill="${MIDNIGHT}"/>` +
    `<g transform="translate(${offset} ${offset}) scale(${scale})">${mark({ stroke: 7 + strokeBoost, dot: 5.5 + strokeBoost / 2 })}</g>` +
    `</svg>`
  )
}

function png(svg, width, path) {
  const data = new Resvg(svg, {
    fitTo: { mode: "width", value: width },
    font: { fontFiles: fonts, loadSystemFonts: false, defaultFontFamily: "Space Grotesk" },
  })
    .render()
    .asPng()
  writeFileSync(join(publicDir, path), data)
  console.log(`${path.padEnd(26)} ${width}px  ${(data.length / 1024).toFixed(1)} KB`)
}

writeFileSync(join(publicDir, "favicon.svg"), iconSvg() + "\n")
console.log("favicon.svg")
png(iconSvg({ strokeBoost: 1 }), 32, "favicon-32x32.png") // traço um pouco mais grosso: legível em 32px
png(iconSvg({ rounded: false, scale: 0.8 }), 180, "apple-touch-icon.png") // o iOS arredonda sozinho
png(iconSvg(), 192, "icon-192.png")
png(iconSvg(), 512, "icon-512.png")
png(iconSvg({ rounded: false, scale: 0.72 }), 512, "icon-maskable-512.png") // área segura de 80%
// Prévia de link (WhatsApp, Telegram, X…): só o ícone, quadrado. O WhatsApp mostra a prévia como
// miniatura quadrada — uma imagem larga era recortada e o N ficava pequeno junto com texto.
png(iconSvg({ rounded: false, scale: 0.72 }), 600, "og-image.png")
