import { useEffect, useLayoutEffect, useState, type RefObject } from 'react'
import { continueRender, delayRender } from 'remotion'

/**
 * Holds rendering until async product layout has settled: `selector` matches inside `ref`
 * and the xyflow viewport transform stops changing (ELK in a worker, node measuring,
 * fitView). Once per mount. Keep the component's props constant while it is on screen:
 * many graphs re-run their async layout when a prop changes identity.
 */
export function useSettled(ref: RefObject<HTMLElement | null>, selector: string, label: string) {
  const [handle] = useState(() => delayRender(label, { timeoutInMilliseconds: 30000 }))
  useEffect(() => {
    let last = '', stable = 0, stopped = false
    const check = () => {
      if (stopped) return
      const root = ref.current
      const count = root?.querySelectorAll(selector).length ?? 0
      const signature = `${count}|${root?.querySelector('.react-flow__viewport')?.getAttribute('style') ?? ''}`
      stable = count > 0 && signature === last ? stable + 1 : 0
      last = signature
      if (stable >= 6) continueRender(handle)
      else setTimeout(check, 50)
    }
    check()
    return () => { stopped = true }
  }, [handle, ref, selector])
}

/**
 * Holds this frame until every phrase is in `ref`'s text. Product text can arrive late:
 * markdown renderers load asynchronously and chat UIs type text in on a timer. `key`
 * changes per frame (e.g. Math.round(t * 1000)).
 */
export function useTextOnScreen(ref: RefObject<HTMLElement | null>, phrases: string[], key: number) {
  useLayoutEffect(() => {
    const handle = delayRender(`text on screen at ${key}`, { timeoutInMilliseconds: 15000 })
    let stopped = false
    const check = () => {
      if (stopped) return
      const text = ref.current?.innerText ?? ''
      if (phrases.every((p) => text.includes(p))) continueRender(handle)
      else setTimeout(check, 30)
    }
    check()
    return () => { stopped = true; continueRender(handle) }
  }, [key, phrases.join('|')])
}
