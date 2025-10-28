import React from 'react'

interface PreProps extends React.HTMLAttributes<HTMLPreElement> {
  icon?: unknown // Nextra passes this, but we need to filter it out
}

export function Pre({ icon, ...props }: PreProps) {
  // Filter out the 'icon' prop that Nextra incorrectly passes to <pre>
  return <pre {...props} />
}
