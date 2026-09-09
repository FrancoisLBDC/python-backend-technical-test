"""URL configuration for the currency conversion API."""

from django.urls import path

from infrastructure.django_app.views import ConvertMoneyView

urlpatterns = [
    path("money/convert", ConvertMoneyView.as_view()),
]
