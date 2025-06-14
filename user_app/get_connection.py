from django.core.mail import EmailMultiAlternatives, get_connection

def send_reset_email(subject, html_content, from_email, from_password, to_email):
    connection = get_connection(
        host='smtpout.secureserver.net',
        port=587,
        username=from_email,
        password=from_password,
        use_tls=True
    )
    email = EmailMultiAlternatives(
        subject=subject,
        body=html_content,
        from_email=from_email,
        to=to_email,
        connection=connection
    )
    email.attach_alternative(html_content, "text/html")
    email.send()
