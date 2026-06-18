'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/cn'

interface TextGenerateEffectProps {
  words: string
  className?: string
  /** Duration per word in seconds. */
  duration?: number
  /** Initial delay before animation starts. */
  delay?: number
}

/**
 * TextGenerateEffect — word-by-word reveal animation.
 * Ideal for AI/copilot responses and hero text.
 * Adapted from Aceternity UI.
 */
function TextGenerateEffect({
  words,
  className,
  duration = 0.05,
  delay = 0,
}: TextGenerateEffectProps) {
  const wordArray = words.split(' ')

  return (
    <p className={cn('text-sm text-text leading-relaxed', className)}>
      {wordArray.map((word, idx) => (
        <motion.span
          key={`${word}-${idx}`}
          className="inline-block mr-[0.25em]"
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: delay + idx * duration,
            duration: 0.2,
            ease: 'easeOut',
          }}
        >
          {word}
        </motion.span>
      ))}
    </p>
  )
}

/**
 * TypewriterEffect — character-by-character reveal.
 * Suitable for shorter strings like page titles.
 */
function TypewriterEffect({
  text,
  className,
  speed = 50,
  delay = 0,
}: {
  text: string
  className?: string
  speed?: number
  delay?: number
}) {
  const [displayed, setDisplayed] = useState('')

  useEffect(() => {
    let active = true
    let i = 0
    let timer: ReturnType<typeof setInterval> | null = null

    // Initially clear displayed state asynchronously or let it be handled by the effect timer
    const delayTimer = setTimeout(() => {
      if (!active) return
      timer = setInterval(() => {
        if (!active) return
        setDisplayed(text.slice(0, i + 1))
        i++
        if (i >= text.length && timer) clearInterval(timer)
      }, speed)
    }, delay)

    return () => {
      active = false
      clearTimeout(delayTimer)
      if (timer) clearInterval(timer)
    }
  }, [text, speed, delay])

  return (
    <span className={cn('', className)}>
      {displayed}
      <motion.span
        className="inline-block w-0.5 h-[1em] bg-accent ml-0.5 align-middle"
        animate={{ opacity: [1, 0] }}
        transition={{ duration: 0.8, repeat: Infinity, repeatType: 'reverse' }}
      />
    </span>
  )
}

export { TextGenerateEffect, TypewriterEffect }
