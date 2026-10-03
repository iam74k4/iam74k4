#!/usr/bin/env node
/*
  Bake the board's star system (cosmos.svg): the same black hole, orbits,
  stardust and nebula as the AstLog landing page, so the profile and the site
  show one picture.

  The geometry is not copied here. AstLog's repository is private, so this
  script reads src/lib/orbits.ts and the black-hole art from a local AstLog
  checkout and commits only the drawn result -- the same markup the site
  already serves in public. Same work counts give the same system, so re-run
  it only when the number of published works on the site changes.

  The board is one <img> on GitHub, so the browser repaints the whole picture
  for every animation step. Anything heavy and still -- the nebula's
  turbulence filters, the blurred light bands, the fixed stars -- is baked to
  WebP through Chromium; only what moves stays vector (orbit lines, stardust,
  bodies, flowing stars, falling grains, the hole's light). Once settled,
  every step lands on one 40 ms grid (TICK below), so the picture changes at
  most 25 times a second.

  Motion follows AstLog: on arrival the system is born once and settles within
  5 s (the hole ignites, orbits are traced inner to outer, bodies light up);
  afterwards stardust and bodies keep orbiting. Under prefers-reduced-motion
  everything rests in its final pose, which is the complete picture.

  The left column is the board's copy. The sky is darkened under it (the
  "veil", as on AstLog: nothing behind the text) and the root carries the
  veil's box as data-copy="x0 y0 x1 y1"; make_dashboard_svg.py refuses copy
  that would leave it.

  Usage: node scripts/make_cosmos_svg.mjs [--astlog ../AstLog] [--apps 5] [--works 2]
  Needs Node 22.18+ (it runs orbits.ts by stripping the types, as AstLog's own
  scripts do) and the AstLog checkout with its node_modules (Playwright). Set
  CHROMIUM to a browser binary if Playwright's own download is missing.
*/
import { readFileSync, writeFileSync } from 'node:fs'
import { createRequire, registerHooks } from 'node:module'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const arg = (name, fallback) => {
  const at = process.argv.indexOf(`--${name}`)
  return at > 0 ? process.argv[at + 1] : fallback
}
const ASTLOG = resolve(arg('astlog', join(ROOT, '..', 'AstLog')))
// published works on the site: personal apps and client work (AstLog's Tally)
const COUNTS = { app: Number(arg('apps', 5)), work: Number(arg('works', 2)) }
const OUT = join(ROOT, 'cosmos.svg')

// orbits.ts imports '../domain' without an extension; Node strips the types
registerHooks({
  resolve(spec, ctx, next) {
    if (ctx.parentURL?.endsWith('.ts') && spec.startsWith('.') && !/\.[a-z]+$/.test(spec)) {
      return next(`${spec}.ts`, ctx)
    }
    return next(spec, ctx)
  },
})
const astlog = (path) => import(pathToFileURL(join(ASTLOG, path)).href)
const O = await astlog('src/lib/orbits.ts')
const { BLACKHOLE_ART } = await astlog('src/ui/logo.ts')
const { chromium } = createRequire(join(ASTLOG, 'package.json'))('playwright')

// ------------------------------------------------------------------ palette
// AstLog's public/app.css :root with the default mono accent
const BG = '#0c0c0e'
const INK = '#f2f2f4'
const ACCENT = INK
const CORE = '#000'
const NEBULA = { a: '#8f8ff5', b: '#f0899f', c: '#6fb6f2', ink: INK, dust: BG }

// ------------------------------------------------------------------ geometry
// the board is 860 wide (make_dashboard_svg.py W); this is its top band
const W = 860
const H = 366
const FRAME = O.HERO_FRAME
const FIG_W = 452
const UNIT = FIG_W / FRAME.width
const FIG_H = FRAME.height * UNIT
// the outermost orbit stays MARGIN inside AstLog's frame; nudging the frame 8 px
// right lines that orbit up with the board's right gutter (W - 32)
const FIG_X = W - 32 - FIG_W + 8
// the hole's height: the system's and the copy column's vertical centres meet
const FOCUS = { x: FIG_X + FRAME.focus.x * UNIT, y: 148 }
const FIG_Y = FOCUS.y - FRAME.focus.y * UNIT
// the copy column: fully dark from the top edge down, eased out to the right over
// VEIL_SIDE. A top edge inside the band cut the nebula's upper-left arm into a
// strip; a short side ramp showed as a vertical line through the clouds
const COPY = { x0: 0, y0: 0, x1: 340, y1: 352 }
const VEIL_SIDE = 200

// ------------------------------------------------------------------ timing
// arrival (ms), as AstLog's --sky-dur, --ignite-*, --trace-*, --birth-*
const T = { sky: 1400, igniteDelay: 150, ignite: 2000, traceDelay: 800, trace: 500, stagger: 800, fill: 1400, birth: 900 }
T.count = T.traceDelay + T.stagger + T.trace * 2
// the one step grid for everything that keeps moving (ms)
const TICK = 40
const steps = (seconds) => Math.max(1, Math.round((seconds * 1000) / TICK))
const onGrid = (seconds) => (Math.round((seconds * 1000) / TICK) * TICK) / 1000
const EASE = 'cubic-bezier(0.23,1,0.32,1)'

// ------------------------------------------------------------------ helpers
const r1 = (v) => Math.round(v * 10) / 10
const r3 = (v) => Math.round(v * 1000) / 1000
const ellipseFrame = ({ cx, cy, rx, ry, angle }) =>
  `translate(${cx} ${cy})${angle ? ` rotate(${angle})` : ''} scale(${rx} ${ry})`
const unstretch = ({ rx, ry, angle }) =>
  `scale(${Number((1 / rx).toPrecision(5))} ${Number((1 / ry).toPrecision(5))})${angle ? ` rotate(${-angle})` : ''}`
// a body's size along its orbit as a stepped linear() (AstLog's stairs)
const stairs = (sway) => {
  const n = sway.length - 1
  const at = (k) => `${Math.round((k / n) * 100000) / 1000}%`
  const level = (k) => r3(((sway[k] ?? 0) + (sway[k + 1] ?? 0)) / 2)
  return `linear(${Array.from({ length: n }, (_, k) => `${level(k)} ${at(k)} ${at(k + 1)}`).join(',')})`
}

const map = O.orbitMap(COUNTS, FRAME)
const reachOf = (i) => r3(i / Math.max(1, map.orbits.length - 1))
const cosmos = O.cosmosMap()
const nebula = O.nebulaMap()

// the star field is cropped to the band (AstLog's preserveAspectRatio slice)
const skyScale = Math.max(W / cosmos.width, H / cosmos.height)
const skyPoint = (s) => [
  r1((W - cosmos.width * skyScale) / 2 + s.x * skyScale),
  r1((H - cosmos.height * skyScale) / 2 + s.y * skyScale),
]
const inVeil = (x, y) => x < COPY.x1 + VEIL_SIDE / 2 && y < COPY.y1 + 12

// ------------------------------------------------------------------ baked: sky
// a soft edge: white whose opacity eases along an axis with AstLog's veil stops
// (0, .16, .5, .84, 1) -- a straight ramp shows its two kinks as lines on the nebula
const ramp = (id, [x1, y1, x2, y2]) =>
  `<linearGradient id="${id}" gradientUnits="userSpaceOnUse" x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}">${[0, 0.16, 0.5, 0.84, 1]
    .map((o, k) => `<stop offset="${k / 4}" stop-color="#fff" stop-opacity="${o}"/>`)
    .join('')}</linearGradient>`

const nebulaSvg = () => {
  const nw = FIG_W * 3.53
  const nh = (nw * nebula.height) / nebula.width
  const ellipse = (l) =>
    `<ellipse cx="${l.cx}" cy="${l.cy}" rx="${l.rx}" ry="${l.ry}" transform="rotate(${l.rot} ${l.cx} ${l.cy})" fill="url(#n-${l.tone})" opacity="${l.o}"/>`
  const region = `x="0" y="0" width="${nebula.width}" height="${nebula.height}" filterUnits="userSpaceOnUse" color-interpolation-filters="sRGB"`
  return `<svg x="${r1(FOCUS.x - nw / 2)}" y="${r1(FOCUS.y - nh / 2)}" width="${r1(nw)}" height="${r1(nh)}" viewBox="0 0 ${nebula.width} ${nebula.height}"><defs>${Object.entries(
    NEBULA,
  )
    .map(
      ([k, c]) =>
        `<radialGradient id="n-${k}"><stop offset="0" stop-color="${c}"/><stop offset="0.45" stop-color="${c}" stop-opacity="0.5"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`,
    )
    .join('')}
<g id="n-glow">${nebula.lobes.filter((l) => l.tone !== 'dust').map(ellipse).join('')}</g>
<g id="n-dusk">${nebula.lobes.filter((l) => l.tone === 'dust').map(ellipse).join('')}</g>
<filter id="n-cloud" ${region}><feTurbulence type="fractalNoise" baseFrequency="0.0042 0.0075" numOctaves="5" seed="4" result="noise"/><feColorMatrix in="noise" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2.1 0 0 0 -0.62" result="mask"/><feComposite in="SourceGraphic" in2="mask" operator="in"/></filter>
<filter id="n-veil" ${region}><feTurbulence type="turbulence" baseFrequency="0.006 0.01" numOctaves="4" seed="9" result="ridge"/><feTurbulence type="fractalNoise" baseFrequency="0.003" numOctaves="2" seed="21" result="warp"/><feDisplacementMap in="ridge" in2="warp" scale="90" xChannelSelector="R" yChannelSelector="G" result="bent"/><feColorMatrix in="bent" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 -4.6 0 0 0 1.05" result="mask"/><feComposite in="SourceGraphic" in2="mask" operator="in"/></filter>
<filter id="n-dust" ${region}><feTurbulence type="fractalNoise" baseFrequency="0.008 0.016" numOctaves="4" seed="33" result="noise"/><feColorMatrix in="noise" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 2.6 0 0 0 -0.9" result="mask"/><feComposite in="SourceGraphic" in2="mask" operator="in"/></filter></defs>
<use href="#n-glow" opacity="0.3"/><use href="#n-glow" filter="url(#n-cloud)" opacity="0.95"/><use href="#n-glow" filter="url(#n-veil)" opacity="0.85"/><use href="#n-dusk" filter="url(#n-dust)" opacity="0.85"/></svg>`
}

const skySvg = () => {
  const stars = cosmos.stars
    .filter((s) => !s.twinkle)
    .map((s) => {
      const [x, y] = skyPoint(s)
      return `<path d="M${x} ${y}h0" opacity="${s.o}" stroke-width="${s.w}"/>`
    })
    .join('')
  const glints = cosmos.stars
    .filter((s) => s.glint)
    .map((s) => {
      const [x, y] = skyPoint(s)
      const arm = r1(s.w * 6 * skyScale * 1.6)
      return `<path d="M${r1(x - arm)} ${y}h${r1(arm * 2)}M${x} ${r1(y - arm)}v${r1(arm * 2)}" stroke="url(#glint)" stroke-width="1" opacity="0.5"/>`
    })
    .join('')
  // the nebula's two-colour wash around the hole (AstLog's .cosmos--hero background)
  const wash = (id, color, dx, sx, sy) => {
    const cx = r1(FOCUS.x + W * dx)
    return `<radialGradient id="${id}" cx="${cx}" cy="${FOCUS.y}" r="${r1(FIG_W * sx)}" gradientUnits="userSpaceOnUse" gradientTransform="translate(0 ${FOCUS.y}) scale(1 ${r3((FIG_H * sy) / (FIG_W * sx))}) translate(0 ${-FOCUS.y})"><stop offset="0" stop-color="${color}" stop-opacity="0.16"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></radialGradient>`
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>
${wash('wash-a', NEBULA.a, -0.08, 0.9, 0.9)}${wash('wash-b', NEBULA.b, 0.1, 0.7, 0.8)}
<radialGradient id="glint"><stop offset="0" stop-color="${INK}"/><stop offset="1" stop-color="${INK}" stop-opacity="0"/></radialGradient>
<linearGradient id="fade-y" x1="0" y1="0" x2="0" y2="${H}" gradientUnits="userSpaceOnUse"><stop offset="${r3((H - 150) / H)}" stop-color="#fff"/><stop offset="${r3((H - 70) / H)}" stop-color="#fff" stop-opacity="0.35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="fade" maskUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="url(#fade-y)"/></mask>
${ramp('veil-x', [COPY.x1 + VEIL_SIDE, 0, COPY.x1, 0])}
<mask id="veil" maskUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="url(#veil-x)"/></mask>
</defs>
<rect width="${W}" height="${H}" fill="${BG}"/>
<g mask="url(#fade)">
<rect width="${W}" height="${H}" fill="url(#wash-a)"/><rect width="${W}" height="${H}" fill="url(#wash-b)"/>
<g fill="none" stroke="${INK}" stroke-linecap="round">${stars}</g>
${nebulaSvg()}
<g fill="none" stroke-linecap="butt">${glints}</g>
</g>
<rect width="${W}" height="${H}" fill="${BG}" mask="url(#veil)"/>
</svg>`
}

// ------------------------------------------------------------------ baked: light bands
const bandsSvg = (side) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${r1(FIG_W)}" height="${r1(FIG_H)}" viewBox="0 0 ${FRAME.width} ${FRAME.height}" overflow="visible"><defs><filter id="b" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="5"/></filter></defs><g fill="none" stroke="${ACCENT}" opacity="0.42" filter="url(#b)">${map.bands
    .filter((b) => b.side === side)
    .map((b) => `<path d="${b.d}" stroke-width="${b.w}" stroke-opacity="${b.o}"/>`)
    .join('')}</g></svg>`

// ------------------------------------------------------------------ bake through Chromium
// WebP is encoded by the browser's canvas (as AstLog's scripts/logo/export.mjs
// does), so nothing beyond Playwright has to be installed
const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {})
const webp = async (base64, type, width, height, quality) => {
  const page = await browser.newPage()
  const out = await page.evaluate(
    async ({ base64, type, width, height, quality }) => {
      const image = new Image()
      image.src = `data:${type};base64,${base64}`
      await image.decode()
      const canvas = document.createElement('canvas')
      canvas.width = width ?? image.naturalWidth
      canvas.height = height ?? image.naturalHeight
      const context = canvas.getContext('2d')
      context.imageSmoothingQuality = 'high'
      context.drawImage(image, 0, 0, canvas.width, canvas.height)
      return canvas.toDataURL('image/webp', quality).split(',')[1]
    },
    { base64, type, width, height, quality },
  )
  await page.close()
  return out
}
// draw an SVG and keep the pixels; alpha keeps the page transparent. The sky is
// drawn at 2x for its pin-point stars; the bands are blurred already and gain
// nothing from it but bytes
const bake = async (svg, width, height, { alpha = false, quality = 0.8, scale = 2 } = {}) => {
  const page = await browser.newPage({
    viewport: { width: Math.ceil(width), height: Math.ceil(height) },
    deviceScaleFactor: scale,
  })
  await page.setContent(`<!doctype html><style>html,body{margin:0;background:transparent}svg{display:block}</style>${svg}`)
  await page.evaluate(() => new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done))))
  const png = await page.screenshot({ omitBackground: alpha })
  await page.close()
  return webp(png.toString('base64'), 'image/png', undefined, undefined, quality)
}

let sky
let bandsFar
let bandsNear
let holeArt
try {
  sky = await bake(skySvg(), W, H, { quality: 0.78 })
  bandsFar = await bake(bandsSvg('far'), FIG_W, FIG_H, { alpha: true, quality: 0.85, scale: 1 })
  bandsNear = await bake(bandsSvg('near'), FIG_W, FIG_H, { alpha: true, quality: 0.85, scale: 1 })
  // the hole's light, redrawn small (the same art as AstLog's logo O)
  const art = readFileSync(join(ASTLOG, 'public', BLACKHOLE_ART.src.split('?')[0])).toString('base64')
  holeArt = await webp(art, 'image/webp', 384, Math.round((384 * BLACKHOLE_ART.height) / BLACKHOLE_ART.width), 0.9)
} finally {
  await browser.close()
}

// ------------------------------------------------------------------ vector: what moves
const clip = (side) => `<clipPath id="c-half-${side}" clipPathUnits="userSpaceOnUse"><path d="${map.halves[side]}"/></clipPath>`
const spinStyle = (seconds, n) => `animation-duration:${seconds}s;animation-timing-function:steps(${n})`

const lines = (side) =>
  map.orbits
    .map(
      (o, i) =>
        `<path class="c-orbit" d="${o[side]}" pathLength="100" stroke="url(#c-depth)" style="opacity:${r3(1 - reachOf(i) * 0.45)};animation-delay:${T.traceDelay + (side === 'near' ? T.trace : 0) + Math.round(reachOf(i) * T.stagger)}ms"/>`,
    )
    .join('')

// AstLog's --stardust-w, clamp(0.6px, 0.16cqi, 1.25px) of the frame. Inside an
// <img>, vw is the picture's displayed width, so the grains thin out with it
// instead of staying screen-sized in a shrunken picture. The floor is half the
// site's: on a phone this frame is about half as wide as the site's figure
// (~180 px against ~358 px), and at 0.6 px the grains clogged the bands
const DUST_W = `clamp(.3px,${r3((0.16 * FIG_W) / W)}vw,1.25px)`
const stardust = (side) =>
  `<g clip-path="url(#c-half-${side})" mask="url(#c-sd-fade)">${map.orbits
    .map(
      (o) =>
        `<g transform="${ellipseFrame(o.ellipse)}"><g class="c-spin" style="${spinStyle(o.period, steps(o.period))}">${o.stardust
          .map((d, level) => (d ? `<path class="c-sd c-sd${level}" d="${d}"/>` : ''))
          .join('')}</g></g>`,
    )
    .join('')}</g>`

const bodies = (side) => {
  const { rx, ry, tilt } = map.ring
  const dx = r1(rx * Math.cos((tilt * Math.PI) / 180))
  const dy = r1(rx * Math.sin((tilt * Math.PI) / 180))
  const ring = (sweep) => `<path class="c-ring" d="M${-dx} ${-dy}A${rx} ${ry} ${tilt} 0 ${sweep} ${dx} ${dy}"/>`
  return `<g clip-path="url(#c-half-${side})">${map.orbits
    .map((o, i) => {
      const riders = map.bodies.filter((b) => b.orbit === i)
      if (!riders.length) return ''
      const birth = T.traceDelay + Math.round(reachOf(i) * T.stagger) + T.trace * 2
      const spin = spinStyle(o.period, steps(o.period))
      return `<g transform="${ellipseFrame(o.ellipse)}"><g class="c-spin" style="${spin}">${riders
        .map(
          (b) =>
            `<g transform="translate(${b.u} ${b.v})"><g class="c-unspin" style="${spin}"><g transform="${unstretch(o.ellipse)}"><g class="c-born" style="animation-delay:${birth}ms"><g class="c-body" style="scale:${b.scale};--sway:${stairs(o.sway)};animation-duration:${o.period}s;animation-delay:-${onGrid((b.turn / 360) * o.period)}s"><circle r="${r1(rx * 1.6)}" fill="url(#c-halo)" opacity="0.55"/>${
              b.kind === 'work' ? ring(1) : ''
            }<circle r="${r1(rx * 0.9)}" fill="url(#c-core)"/>${b.kind === 'work' ? ring(0) : ''}</g></g></g></g></g>`,
        )
        .join('')}</g></g>`
    })
    .join('')}</g>`
}

// one bright star per orbit with a faint tail, faster than the stardust (AstLog's Flows)
const flows = (side) => {
  const four = (v) => Math.round(v * 10000) / 10000
  const TRAIL = 16
  const wedge = (rx) => {
    const edge = (s) =>
      Array.from({ length: 9 }, (_, k) => {
        const a = ((-TRAIL * k) / 8) * (Math.PI / 180)
        const r = 1 + s * (2.4 / rx) * (1 - k / 8)
        return `${four(r * Math.cos(a))} ${four(r * Math.sin(a))}`
      })
    return `M${edge(1).join('L')}L${edge(-1).slice(0, -1).reverse().join('L')}Z`
  }
  const core = r1(map.ring.rx * 0.45)
  const arm = r1(map.ring.rx * 1.2)
  return `<g class="c-moving" clip-path="url(#c-half-${side})">${map.orbits
    .map((o, i) => {
      const period = map.flows[i] ?? o.period
      const turn = r1(((i * 0.618) % 1) * 360)
      const size = Math.round((o.sway.reduce((s, v) => s + v, 0) / o.sway.length) * 100) / 100
      const spin = spinStyle(period, steps(period))
      return `<g transform="${ellipseFrame(o.ellipse)}"><g class="c-spin" style="${spin}"><g transform="rotate(${turn})"><path d="${wedge(o.ellipse.rx)}" fill="url(#c-trail)"/><g transform="translate(1 0)"><g class="c-unspin" style="${spin}"><g transform="rotate(${-turn}) ${unstretch(o.ellipse)}"><g style="scale:${size}"><circle r="${core}" fill="url(#c-flow)"/><path class="c-glint" d="M${-arm} 0h${arm * 2}M0 ${-arm}v${arm * 2}" stroke="url(#c-spark)"/></g></g></g></g></g></g></g>`
    })
    .join('')}</g>`
}

// grains spiralling into the hole, behind it only (AstLog's Dust)
const grains = () =>
  `<g class="c-moving" transform="${map.plane}">${map.dust
    .map((g) => {
      const dur = Math.max(0.4, Math.round(g.dur / 0.4) * 0.4)
      const timing = `animation-duration:${r3(dur)}s;animation-delay:${onGrid(g.delay)}s;animation-timing-function:steps(${steps(dur / 10)})`
      return `<g transform="rotate(${g.a})"><g class="c-grain" style="${timing}"><g transform="translate(${g.r1} 0) scale(${r1(g.r0 - g.r1)})" opacity="${g.o}"><path class="c-dot" d="M0 0h0" style="stroke-width:${g.w}px;${timing}"/></g></g></g>`
    })
    .join('')}</g>`

const holeW = (BLACKHOLE_ART.width / BLACKHOLE_ART.shadow) * FRAME.hole
const holeH = (BLACKHOLE_ART.height / BLACKHOLE_ART.shadow) * FRAME.hole
const hole = `<g class="c-hole"><circle cx="${FRAME.focus.x}" cy="${FRAME.focus.y}" r="${FRAME.hole}" fill="${CORE}"/><image class="c-glow" href="data:image/webp;base64,${holeArt}" x="${r1(FRAME.focus.x - holeW / 2)}" y="${r1(FRAME.focus.y - holeH / 2)}" width="${r1(holeW)}" height="${r1(holeH)}"/></g><circle class="c-flare" cx="${FRAME.focus.x}" cy="${FRAME.focus.y}" r="${FRAME.hole * 2.6}" fill="url(#c-flare)"/>`

const twinkles = cosmos.stars
  .filter((s) => s.twinkle)
  .map((s) => {
    const [x, y] = skyPoint(s)
    if (y > H - 80 || inVeil(x, y)) return ''
    return `<path class="c-twinkle" d="M${x} ${y}h0" opacity="${s.o}" style="stroke-width:${s.w}px;animation-duration:${onGrid(s.twinkle.dur)}s;animation-delay:${onGrid(s.twinkle.delay)}s;animation-timing-function:steps(${steps(s.twinkle.dur / 2)})"/>`
  })
  .join('')

// ------------------------------------------------------------------ one file
const style = `
.c-orbit{fill:none;stroke-width:1px;vector-effect:non-scaling-stroke;stroke-dasharray:100}
.c-sd{fill:none;stroke:${INK};stroke-linecap:round;vector-effect:non-scaling-stroke}
.c-sd0{stroke-width:${DUST_W};opacity:.45}.c-sd1{stroke-width:calc(${DUST_W}*1.5);opacity:.65}
.c-sd2{stroke-width:calc(${DUST_W}*2.1);opacity:.85}.c-sd3{stroke-width:calc(${DUST_W}*2.8)}
.c-ring{fill:none;stroke:${INK};stroke-width:1px;stroke-linecap:round;vector-effect:non-scaling-stroke}
.c-glint{fill:none;stroke-width:1px;vector-effect:non-scaling-stroke;opacity:.75}
.c-dot{fill:none;stroke:${INK};stroke-linecap:round;vector-effect:non-scaling-stroke;opacity:0}
.c-twinkle{fill:none;stroke:${INK};stroke-linecap:round}
.c-hole{transform-origin:${FRAME.focus.x}px ${FRAME.focus.y}px}
.c-glow{opacity:.72}
.c-flare{opacity:0}
.c-moving{display:none}
@keyframes c-fade{from{opacity:0}}
@keyframes c-ignite{from{opacity:0;transform:scale(.1)}16%{opacity:1;transform:scale(.3)}42%{transform:scale(1.7)}}
@keyframes c-flare{16%{opacity:.9}42%{opacity:.4}}
@keyframes c-trace{from{stroke-dashoffset:-100}}
@keyframes c-birth{from{opacity:0;scale:0}45%{opacity:1;scale:2.4}}
@keyframes c-spin{to{transform:rotate(1turn)}}
@keyframes c-unspin{to{transform:rotate(-1turn)}}
@keyframes c-sway{from{scale:0}to{scale:1}}
@keyframes c-breathe{from{opacity:.59}}
@keyframes c-twinkle{50%{opacity:.15}}
@keyframes c-swirl{10%{transform:rotate(2.2deg)}20%{transform:rotate(9deg)}30%{transform:rotate(20.9deg)}40%{transform:rotate(38.5deg)}50%{transform:rotate(62.6deg)}60%{transform:rotate(94deg)}70%{transform:rotate(134.6deg)}80%{transform:rotate(187.2deg)}90%{transform:rotate(257.4deg)}to{transform:rotate(1turn)}}
@keyframes c-fall{from{transform:translate(1px,0);opacity:0}10%{transform:translate(.994px,0);opacity:.34}20%{transform:translate(.975px,0);opacity:1}30%{transform:translate(.942px,0)}40%{transform:translate(.893px,0)}50%{transform:translate(.826px,0)}60%{transform:translate(.739px,0)}70%{transform:translate(.626px,0)}80%{transform:translate(.48px,0);opacity:1}90%{transform:translate(.285px,0);opacity:.83}to{transform:translate(0,0);opacity:0}}
@media (prefers-reduced-motion:no-preference){
.c-sky{animation:c-fade ${T.sky}ms ${EASE} backwards}
.c-hole{animation:c-ignite ${T.ignite}ms ${EASE} ${T.igniteDelay}ms backwards}
.c-flare{animation:c-flare ${T.ignite}ms ${EASE} ${T.igniteDelay}ms}
.c-orbit{animation:c-trace ${T.trace}ms linear backwards}
.c-fill{animation:c-fade ${T.fill}ms ${EASE} ${T.traceDelay + T.trace}ms backwards}
.c-born{animation:c-birth ${T.birth}ms ${EASE} backwards}
.c-spin{animation-name:c-spin;animation-iteration-count:infinite}
.c-unspin{animation-name:c-unspin;animation-iteration-count:infinite}
.c-body{animation-name:c-sway;animation-timing-function:var(--sway);animation-iteration-count:infinite}
.c-moving{display:inline;animation:c-fade ${T.fill}ms ${EASE} ${T.count}ms backwards}
.c-grain{animation-name:c-swirl;animation-iteration-count:infinite}
.c-dot{animation-name:c-fall;animation-iteration-count:infinite}
.c-glow{animation:c-breathe 4s steps(${steps(4)}) infinite alternate}
.c-twinkle{animation-name:c-twinkle;animation-iteration-count:infinite}
}`

const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" data-copy="${COPY.x0} ${COPY.y0} ${COPY.x1} ${COPY.y1}" data-works="${COUNTS.app} ${COUNTS.work}" aria-hidden="true">
<!-- generated by scripts/make_cosmos_svg.mjs from AstLog's src/lib/orbits.ts; do not edit by hand -->
<style>${style}</style>
<defs>
${clip('far')}${clip('near')}
<linearGradient id="c-depth" gradientUnits="userSpaceOnUse" x1="${map.depth.x1}" y1="${map.depth.y1}" x2="${map.depth.x2}" y2="${map.depth.y2}"><stop offset="0" stop-color="${ACCENT}" stop-opacity="${r3(0.34 * 0.15)}"/><stop offset="1" stop-color="${ACCENT}" stop-opacity="0.34"/></linearGradient>
<linearGradient id="c-sd-depth" gradientUnits="userSpaceOnUse" x1="${map.depth.x1}" y1="${map.depth.y1}" x2="${map.depth.x2}" y2="${map.depth.y2}"><stop offset="0" stop-color="#fff" stop-opacity="0.35"/><stop offset="1" stop-color="#fff"/></linearGradient>
<mask id="c-sd-fade" maskUnits="userSpaceOnUse" x="0" y="0" width="${FRAME.width}" height="${FRAME.height}" style="mask-type:alpha"><rect width="${FRAME.width}" height="${FRAME.height}" fill="url(#c-sd-depth)"/></mask>
<radialGradient id="c-core"><stop offset="0" stop-color="${INK}"/><stop offset=".25" stop-color="${INK}"/><stop offset=".4" stop-color="${INK}" stop-opacity=".75"/><stop offset=".55" stop-color="${INK}" stop-opacity=".4"/><stop offset=".75" stop-color="${INK}" stop-opacity=".12"/><stop offset="1" stop-color="${INK}" stop-opacity="0"/></radialGradient>
<radialGradient id="c-halo"><stop offset="0" stop-color="${ACCENT}"/><stop offset=".3" stop-color="${ACCENT}" stop-opacity=".4"/><stop offset="1" stop-color="${ACCENT}" stop-opacity="0"/></radialGradient>
<linearGradient id="c-trail" gradientUnits="userSpaceOnUse" x1="${r3(Math.cos((-16 * Math.PI) / 180))}" y1="${r3(Math.sin((-16 * Math.PI) / 180))}" x2="1" y2="0"><stop offset="0" stop-color="${INK}" stop-opacity="0"/><stop offset="1" stop-color="${INK}" stop-opacity="0.5"/></linearGradient>
<radialGradient id="c-flow"><stop offset="0" stop-color="${INK}"/><stop offset=".2" stop-color="${INK}"/><stop offset=".45" stop-color="${INK}" stop-opacity=".55"/><stop offset=".75" stop-color="${INK}" stop-opacity=".15"/><stop offset="1" stop-color="${INK}" stop-opacity="0"/></radialGradient>
<radialGradient id="c-spark"><stop offset="0" stop-color="${INK}"/><stop offset="1" stop-color="${INK}" stop-opacity="0"/></radialGradient>
<radialGradient id="c-flare"><stop offset="0" stop-color="${INK}"/><stop offset=".35" stop-color="${INK}" stop-opacity=".35"/><stop offset="1" stop-color="${INK}" stop-opacity="0"/></radialGradient>
</defs>
<image class="c-sky" href="data:image/webp;base64,${sky}" width="${W}" height="${H}"/>
<g class="c-sky">${twinkles}</g>
<svg x="${r1(FIG_X)}" y="${r1(FIG_Y)}" width="${r1(FIG_W)}" height="${r1(FIG_H)}" viewBox="0 0 ${FRAME.width} ${FRAME.height}" overflow="visible">
<image class="c-fill" href="data:image/webp;base64,${bandsFar}" width="${FRAME.width}" height="${FRAME.height}"/>
${lines('far')}
<g class="c-fill">${stardust('far')}</g>
${flows('far')}
${grains()}
${bodies('far')}
${hole}
<image class="c-fill" href="data:image/webp;base64,${bandsNear}" width="${FRAME.width}" height="${FRAME.height}"/>
${lines('near')}
<g class="c-fill">${stardust('near')}</g>
${flows('near')}
${bodies('near')}
</svg>
</svg>
`
writeFileSync(OUT, svg)
console.log(
  `wrote cosmos.svg ${W}x${H} ${Math.round(Buffer.byteLength(svg) / 1024)}KB; ${COUNTS.app} apps + ${COUNTS.work} works, ${map.orbits.length} orbits`,
)
