// next/navigation outside Next. A scene can set globalThis.__filmPathname before it renders
// the shell, so nav items show the right active page.
export const usePathname = () => ((globalThis as any).__filmPathname as string | undefined) ?? '/'
export const useSearchParams = () => new URLSearchParams()
export const useRouter = () => ({ push() {}, replace() {}, prefetch() {}, back() {}, refresh() {} })
export const useParams = () => ({ teamId: 'team-1' })
export const redirect = () => {}
export const notFound = () => {}
