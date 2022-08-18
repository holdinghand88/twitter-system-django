from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import View

class PaymentCheck(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.twitteruser.is_notified