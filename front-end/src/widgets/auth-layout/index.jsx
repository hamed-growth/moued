import { Box, Paper, Typography } from '@mui/material'

export function AuthLayout({ title, description, children, footer }) {
  return (
    <Box component="main" className="auth-layout">
      <aside className="auth-layout__art" aria-hidden="true">
        <div className="auth-layout__art-stage">
          <img src="/media/images/Minimal%20Hot%20Air%20Balloon%20Scene.png" alt="" />
        </div>
      </aside>
      <section className="auth-layout__panel" aria-labelledby="auth-title">
        <div className="auth-layout__content">
          <header className="auth-layout__heading">
            <Typography id="auth-title" component="h1" className="auth-layout__title">{title}</Typography>
            <Typography component="p" className="auth-layout__description">{description}</Typography>
          </header>
          <Paper component="div" elevation={0} className="auth-layout__card">
            {children}
          </Paper>
          {footer && <div className="auth-layout__footer">{footer}</div>}
        </div>
      </section>
    </Box>
  )
}
