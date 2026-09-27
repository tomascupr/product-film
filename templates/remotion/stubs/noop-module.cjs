// Telemetry and other side-effect SDKs (Sentry, analytics) outside the app: every export is a no-op.
const noop = () => undefined
module.exports = new Proxy({ __esModule: true }, { get: (target, key) => (key in target ? target[key] : noop) })
