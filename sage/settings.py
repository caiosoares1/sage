EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "seuemail@gmail.com"
EMAIL_HOST_PASSWORD = "suasenha_app"  
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# não é a senha do gmail, é uma App Password
## para Gmail você precisa gerar uma Senha de App: Google → Segurança → Senhas de app → Copiar a senha gerada.