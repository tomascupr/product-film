// next/image outside Next: Remotion's <Img>, which the renderer waits for.
import { Img, staticFile } from 'remotion'
export default function Image({ src, alt, width, height, fill, priority, unoptimized, quality, placeholder, blurDataURL, loader, sizes, ...props }: any) {
  const raw = typeof src === 'string' ? src : src?.src
  // The product serves /x from its public folder; the film serves the same files from its own public/.
  const url = raw?.startsWith('/') ? staticFile(raw.slice(1)) : raw
  return <Img src={url} alt={alt} width={fill ? undefined : width} height={fill ? undefined : height} style={fill ? { position: 'absolute', inset: 0, width: '100%', height: '100%' } : undefined} {...props} />
}
