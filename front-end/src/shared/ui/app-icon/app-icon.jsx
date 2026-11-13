import { forwardRef } from 'react'

export const AppIcon = forwardRef(function AppIcon(
  { icon, size = 20, color = 'inherit', className, style, 'aria-hidden': ariaHidden = true, ...props },
  ref,
) {
  const dimension = typeof size === 'number' ? `${size}px` : size
  const maskImage = `url("${icon}")`
  const mask = `${maskImage} center / contain no-repeat`

  return (
    <span
      {...props}
      ref={ref}
      className={className}
      aria-hidden={ariaHidden}
      style={{
        display: 'inline-block',
        flex: '0 0 auto',
        width: dimension,
        height: dimension,
        color,
        backgroundColor: 'currentColor',
        mask,
        WebkitMask: mask,
        maskImage,
        WebkitMaskImage: maskImage,
        maskRepeat: 'no-repeat',
        WebkitMaskRepeat: 'no-repeat',
        maskPosition: 'center',
        WebkitMaskPosition: 'center',
        maskSize: 'contain',
        WebkitMaskSize: 'contain',
        ...style,
      }}
    />
  )
})
