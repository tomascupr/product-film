// Tailwind v3: the product's own config, scanning the film and the product folders it imports from.
// Its plugins resolve from the product repo. For Tailwind v4 use @remotion/tailwind-v4 instead.
import base from '/abs/path/to/product/app/tailwind.config'
export default {
  ...base,
  content: ['./src/**/*.{ts,tsx}', '/abs/path/to/product/app/components/**/*.{ts,tsx}', '/abs/path/to/product/app/lib/**/*.{ts,tsx}'],
}
