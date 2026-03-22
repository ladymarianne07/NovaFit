import React from 'react'

export function Logo({ size = 32, className = '' }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <polygon points="32,6 54,24 32,58 10,24" stroke="currentColor" strokeWidth="2" fill="none"/>
      <polygon points="32,6 54,24 32,58 10,24" fill="currentColor" opacity="0.06"/>
      <line x1="10" y1="24" x2="54" y2="24" stroke="currentColor" strokeWidth="1.5" opacity="0.5"/>
      <line x1="32" y1="6" x2="10" y2="24" stroke="currentColor" strokeWidth="2"/>
      <line x1="32" y1="6" x2="54" y2="24" stroke="currentColor" strokeWidth="2"/>
      <polyline points="10,24 32,36 54,24" stroke="currentColor" strokeWidth="1.5" opacity="0.4" fill="none"/>
      <circle cx="32" cy="6" r="2.5" fill="currentColor"/>
    </svg>
  )
}

export default Logo
