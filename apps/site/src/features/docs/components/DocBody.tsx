import { compileMDX } from 'next-mdx-remote/rsc'
import remarkGfm from 'remark-gfm'
import rehypeSlug from 'rehype-slug'
import rehypePrettyCode from 'rehype-pretty-code'
import { mdxComponents } from './mdx'

/**
 * Server-compiles a single MDX string with the docs plugin chain and renders
 * it with our styled components. Syntax highlighting is Shiki via
 * rehype-pretty-code; `keepBackground:false` lets `.prose-docs pre` own the
 * block's background so it matches the site theme instead of Shiki's.
 */
export async function DocBody({ source }: { source: string }) {
  const { content } = await compileMDX({
    source,
    components: mdxComponents,
    options: {
      mdxOptions: {
        remarkPlugins: [remarkGfm],
        rehypePlugins: [
          rehypeSlug,
          [
            rehypePrettyCode,
            {
              theme: 'github-dark-default',
              keepBackground: false,
              defaultLang: 'plaintext',
            },
          ],
        ],
      },
    },
  })
  return content
}
