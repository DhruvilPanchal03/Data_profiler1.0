from django.urls import path
from .views import IndexView, SignupView, SigninView, SignoutView, DeleteView, ChartsView, TablesView, PasswordView, SettingsView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('signin/', SigninView.as_view(), name='signin'),
    path('signout/', SignoutView.as_view(), name='signout'),
    path('delete/', DeleteView.as_view(), name='delete'),
    path('charts/', ChartsView.as_view(), name='charts'),
    path('tables/', TablesView.as_view(), name='tables'),
    path('password/', PasswordView.as_view(), name='password'),
    path('settings/', SettingsView.as_view(), name='settings'),
]
