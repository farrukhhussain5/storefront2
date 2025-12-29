from django.core.mail import send_mail, mail_admins, BadHeaderError, EmailMessage
from django.shortcuts import render
from templated_mail.mail import BaseEmailMessage
from .tasks import notify_customer


def say_hello(request):
    notify_customer.delay('Hello')
    # try:
    #     message = BaseEmailMessage(
    #         template_name="emails/hello.html", context={"name": "Farrukh"}
    #     )
    #     message.send(["info@farrukh.com"])
    #     # message = EmailMessage(
    #     #     "subject", "message", "info@mosh.com", ["bob@moshbut.com"]
    #     # )
    #     # message.attach_file("playground\static\images\cat.png")
    #     # message.send()
    #     # mail_admins("subject", "message", html_message="message")
    #     # send_mail("subject", "message", "info@mosh.com", ["bob@moshbut.com"])
    # except BadHeaderError:
    #     pass
    return render(request, "hello.html", {"name": "Mosh"})
