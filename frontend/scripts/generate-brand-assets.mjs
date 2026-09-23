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

/** Prévia de link (WhatsApp, Telegram, LinkedIn, X…): 1200×630, o formato padrão do Open Graph. */
function ogSvg() {
  const gridLines = []
  for (let x = 0; x <= 1200; x += 60) gridLines.push(`<line x1="${x}" y1="0" x2="${x}" y2="630"/>`)
  for (let y = 0; y <= 630; y += 60) gridLines.push(`<line x1="0" y1="${y}" x2="1200" y2="${y}"/>`)
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="${MIDNIGHT}"/>
  <g stroke="#FFFFFF" stroke-opacity="0.04" stroke-width="1">${gridLines.join("")}</g>
  <g transform="translate(700 70) scale(8)" opacity="0.08">${mark({ stroke: 6, dot: 5 })}</g>
  <g transform="translate(96 150)">
    <g transform="scale(2.6)">
      <rect width="64" height="64" rx="14" fill="#111827"/>
      ${mark()}
    </g>
    <text x="206" y="118" font-family="Space Grotesk" font-weight="600" font-size="104" fill="#F1F5F9">Nex<tspan fill="${TEAL}">Fi</tspan></text>
  </g>
  <text x="96" y="398" font-family="Space Grotesk" font-weight="600" font-size="46" fill="${TEAL_LIGHT}">Finanças pessoais</text>
  <text x="96" y="452" font-family="Space Grotesk" font-weight="400" font-size="30" fill="#94A3B8">Contas, cartões, financiamentos e metas em um só lugar,</text>
  <text x="96" y="494" font-family="Space Grotesk" font-weight="400" font-size="30" fill="#94A3B8">com projeção de saldo e das faturas mês a mês.</text>
  <text x="96" y="566" font-family="Space Grotesk" font-weight="400" font-size="24" fill="#64748B">nexfi.abdalanexus.com</text>
</svg>`
}

writeFileSync(join(publicDir, "favicon.svg"), iconSvg() + "\n")
console.log("favicon.svg")
png(iconSvg({ strokeBoost: 1 }), 32, "favicon-32x32.png") // traço um pouco mais grosso: legível em 32px
png(iconSvg({ rounded: false, scale: 0.8 }), 180, "apple-touch-icon.png") // o iOS arredonda sozinho
png(iconSvg(), 192, "icon-192.png")
png(iconSvg(), 512, "icon-512.png")
png(iconSvg({ rounded: false, scale: 0.72 }), 512, "icon-maskable-512.png") // área segura de 80%
png(ogSvg(), 1200, "og-image.png")
