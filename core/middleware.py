"""
Custome middleware
"""

import os

from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse,FileResponse, Http404
from django.contrib.auth.models import User
from authorization.models import TwitterUser
from core.models import PaymentHistory
from datetime import date, datetime
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config.settings import EMAIL_FROM,SENDGRID_API_KEY

class FilterUserMiddleware(MiddlewareMixin):
   
    def process_request(self, request):
        if request.path != '/payment':
            user = request.user
            try:
                paid_user = PaymentHistory.objects.get(user=user)
                return None
            except:
                if request.user.is_authenticated:
                    joined_date = request.user.date_joined
                    joined_date = joined_date.date()
                    today = date.today()
                    delta_day = today - joined_date
                    print(delta_day)
                    if delta_day.days > 30:
                        if request.user.twitteruser.is_notified:
                            print("already sent")
                            return redirect("core:payment")
                        else:
                            profile = TwitterUser.objects.get(user=user)
                            profile.is_notified = True
                            profile.save()
                            user_id = request.user.id
                            to_email = request.user.email
                            p_name = request.user.last_name
                            url = reverse_lazy('core:payment')
                            confirm_url = request.build_absolute_uri(url)
                            subject = request.user.last_name + '様プランをアップグレードする必要があります。'
                            html_body = render_to_string("payment/plan_email.html", {'url':confirm_url, 'username':p_name})        
                            print(confirm_url)
                            message = Mail(
                                from_email=EMAIL_FROM,
                                to_emails=to_email,
                                subject=subject,
                                html_content=html_body)
                            
                            try:
                                sg = SendGridAPIClient(SENDGRID_API_KEY)
                                response = sg.send(message)
                                #print(response)
                            except Exception as e:
                                print(e)
                            return redirect("core:payment")
                        #raise Http404 

                
                return None