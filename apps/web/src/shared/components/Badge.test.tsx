import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Badge } from './Badge'

describe('Badge', () => {
  it('renders its children', () => {
    render(<Badge variant="ok">Active</Badge>)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders a leading status dot when `dot` is set', () => {
    const { container } = render(
      <Badge variant="err" dot>
        Failed
      </Badge>,
    )
    expect(screen.getByText('Failed')).toBeInTheDocument()
    // outer badge span contains an inner dot span only when dot is set
    expect(container.querySelector('span > span')).not.toBeNull()
  })
})
