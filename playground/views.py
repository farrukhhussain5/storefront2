from django.core.mail import send_mail, mail_admins, BadHeaderError, EmailMessage
from django.shortcuts import render
from templated_mail.mail import BaseEmailMessage
from .tasks import notify_customer
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.views import APIView
import requests

class HelloView(APIView):
    @method_decorator(cache_page(5 * 60))
    def get(self, request):
        response = requests.get('https://httpbin.org/delay/2')
        data = response.json()
        return render(request, "hello.html", {"name": 'Mosh'})



# def say_hello(request):
#     key = 'httpbin.org'
#     if cache.get(key) is None:
#         response = requests.get('https://httpbin.org/delay/2')
#         data = response.json()
#         cache.set(key, data)
#     # notify_customer.delay('Hello')
#     # try:
#     #     message = BaseEmailMessage(
#     #         template_name="emails/hello.html", context={"name": "Farrukh"}
#     #     )
#     #     message.send(["info@farrukh.com"])
#     #     # message = EmailMessage(
#     #     #     "subject", "message", "info@mosh.com", ["bob@moshbut.com"]
#     #     # )
#     #     # message.attach_file("playground\static\images\cat.png")
#     #     # message.send()
#     #     # mail_admins("subject", "message", html_message="message")
#     #     # send_mail("subject", "message", "info@mosh.com", ["bob@moshbut.com"])
#     # except BadHeaderError:
#     #     pass
#     return render(request, "hello.html", {"name": cache.get(key)})
