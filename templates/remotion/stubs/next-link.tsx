// next/link outside Next: a plain anchor (films never navigate).
import type { AnchorHTMLAttributes } from 'react'
export default function Link({ href, prefetch, replace, scroll, ...props }: AnchorHTMLAttributes<HTMLAnchorElement> & { href: string | { pathname?: string }; prefetch?: boolean; replace?: boolean; scroll?: boolean }) {
  return <a href={typeof href === 'string' ? href : href.pathname} {...props} />
}
