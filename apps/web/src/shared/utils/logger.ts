/**
 * Unified logger utility for the Fuse V2 frontend.
 * Enforces consistent logging patterns and avoids direct console.log usage.
 */

type LogLevel = 'info' | 'warn' | 'error' | 'debug'

const LOG_LEVELS: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
}

// In production, only show warnings and errors or info
const CURRENT_LOG_LEVEL = import.meta.env.DEV ? LOG_LEVELS.debug : LOG_LEVELS.info

class Logger {
  private format(level: LogLevel, message: string, ...args: unknown[]) {
    const timestamp = new Date().toISOString()
    const prefix = `[FuseV2][${level.toUpperCase()}][${timestamp}]:`
    return [prefix, message, ...args]
  }

  debug(message: string, ...args: unknown[]) {
    if (CURRENT_LOG_LEVEL <= LOG_LEVELS.debug) {
      console.debug(...this.format('debug', message, ...args))
    }
  }

  info(message: string, ...args: unknown[]) {
    if (CURRENT_LOG_LEVEL <= LOG_LEVELS.info) {
      console.info(...this.format('info', message, ...args))
    }
  }

  warn(message: string, ...args: unknown[]) {
    if (CURRENT_LOG_LEVEL <= LOG_LEVELS.warn) {
      console.warn(...this.format('warn', message, ...args))
    }
  }

  error(message: string, ...args: unknown[]) {
    if (CURRENT_LOG_LEVEL <= LOG_LEVELS.error) {
      console.error(...this.format('error', message, ...args))
    }
  }
}

export const logger = new Logger()
