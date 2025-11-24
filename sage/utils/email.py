from django.core.mail import send_mail

def enviar_notificacao_email(destinatario, assunto, mensagem):
    send_mail(
        subject=assunto,
        message=mensagem,
        from_email=None,  # usa DEFAULT_FROM_EMAIL
        recipient_list=[destinatario],
        fail_silently=False,
    )
