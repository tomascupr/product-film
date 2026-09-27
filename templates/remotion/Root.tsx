import { Composition } from 'remotion'
import film from '../film.json'
import { Film } from './Film'
// The product's global CSS, imported here (not with CSS @import) so it runs through Tailwind.
import '@/app/globals.css'
// next/font sets font variables that do not exist outside Next: load the same font locally
// (e.g. pnpm add @fontsource-variable/inter) and set the variable in fonts.css.
import '@fontsource-variable/inter'
import './fonts.css'
// Product CSS animations and transitions run on the wall clock: stop them; the film moves things from t.
import './freeze.css'
import { MotionGlobalConfig } from 'framer-motion'

// framer-motion (used inside product components) also runs on the wall clock: jump to end states.
MotionGlobalConfig.skipAnimations = true

export const Root = () => (
  <Composition
    id="Film"
    component={Film}
    width={film.size?.[0] ?? 1920}
    height={film.size?.[1] ?? 1080}
    fps={60}
    durationInFrames={Math.round(film.duration * 60)}
    defaultProps={{ fps: 60, debug: false }}
    calculateMetadata={({ props }) => ({ fps: props.fps, durationInFrames: Math.round(film.duration * props.fps) })}
  />
)
