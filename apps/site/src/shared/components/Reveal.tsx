'use client'

import { useEffect, useRef, useState, type HTMLAttributes, type ReactNode } from 'react'

interface RevealProps extends HTMLAttributes<HTMLDivElement> {
  children?: ReactNode
  /** Delay in seconds — use `i * 0.05` for stagger. */
  delay?: number
  /** Distance the element rises from. Default 18px reads as a soft lift. */
  y?: number
}

/**
 * Scroll-reveal wrapper. Plain React + IntersectionObserver + CSS
 * transition — no animation library so there's no SSR/HMR/React-19
 * mismatch surface. Fades up once on first viewport entry then stays
 * settled (repeated reveals on every scroll-back read as cheap).
 *
 * `prefers-reduced-motion` is honoured by skipping the initial offset
 * and the transition entirely.
 */
export function Reveal({ children, delay = 0, y = 18, style, className, ...rest }: RevealProps) {
  const ref = useRef<HTMLDivElement | null>(null)
  const [shown, setShown] = useState(false)
  const [prefersReduce, setPrefersReduce] = useState(false)

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReduce(mq.matches)
    const onChange = () => setPrefersReduce(mq.matches)
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])

  useEffect(() => {
    if (prefersReduce) { setShown(true); return }
    const el = ref.current
    if (!el) return
    if (typeof IntersectionObserver === 'undefined') { setShown(true); return }

    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setShown(true)
            io.disconnect()
            break
          }
        }
      },
      { threshold: 0.15, rootMargin: '0px 0px -60px 0px' },
    )
    io.observe(el)
    return () => io.disconnect()
  }, [prefersReduce])

  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: shown ? 1 : 0,
        transform: shown ? 'none' : `translate3d(0, ${y}px, 0)`,
        transition: prefersReduce
          ? 'none'
          : `opacity 700ms cubic-bezier(0.22, 1, 0.36, 1) ${delay}s, transform 700ms cubic-bezier(0.22, 1, 0.36, 1) ${delay}s`,
        willChange: shown ? 'auto' : 'opacity, transform',
        ...style,
      }}
      {...rest}
    >
      {children}
    </div>
  )
}
