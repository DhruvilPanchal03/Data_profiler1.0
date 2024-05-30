from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, FormView, RedirectView
from django import forms

# Create your views here.
from django.http import HttpResponse

class IndexView(TemplateView):
    template_name = "authapp/index.html"

class SignupForm(forms.Form):
    username = forms.CharField(max_length=150)
    fname = forms.CharField(max_length=30)
    lname = forms.CharField(max_length=30)
    email = forms.EmailField()
    pass1 = forms.CharField(widget=forms.PasswordInput)
    pass2 = forms.CharField(widget=forms.PasswordInput)

class SignupView(FormView):
    template_name = "authapp/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy('signin')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        fname = form.cleaned_data['fname']
        lname = form.cleaned_data['lname']
        email = form.cleaned_data['email']
        pass1 = form.cleaned_data['pass1']
        pass2 = form.cleaned_data['pass2']

        if User.objects.filter(username=username).exists():
            messages.error(self.request, "Username already exists! Please try another username.")
            return redirect('index')
        
        if pass1 != pass2:
            messages.error(self.request, "Passwords didn't match!")
            return redirect('signup')

        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()

        messages.success(self.request, "Your Account has been successfully created.")
        return super().form_valid(form)

class SigninForm(forms.Form):
    username = forms.CharField(max_length=150)
    pass1 = forms.CharField(widget=forms.PasswordInput)

class SigninView(FormView):
    template_name = "authapp/signin.html"
    form_class = SigninForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        pass1 = form.cleaned_data['pass1']
        user = authenticate(username=username, password=pass1)

        if user is not None:
            login(self.request, user)
            fname = user.first_name
            messages.success(self.request, f"Welcome back, {fname}!")
            return render(self.request, "authapp/index.html", {'fname': fname})
        else:
            messages.error(self.request, "Bad Credentials!")
            return redirect('index')

class SignoutView(RedirectView):
    url = reverse_lazy('index')

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Logged Out Successfully!")
        return super().get(request, *args, **kwargs)

class DeleteForm(forms.Form):
    username = forms.CharField(max_length=150)

class DeleteView(FormView):
    template_name = "authapp/delete.html"
    form_class = DeleteForm
    success_url = reverse_lazy('index')

    def form_valid(self, form):
        username = form.cleaned_data['username']
        User.objects.filter(username=username).delete()
        messages.success(self.request, "User deleted successfully.")
        return super().form_valid(form)

class ChartsView(TemplateView):
    template_name = "authapp/charts.html"

class TablesView(TemplateView):
    template_name = "authapp/tables.html"

class PasswordView(TemplateView):
    template_name = "authapp/password.html"

class SettingsView(TemplateView):
    template_name = "authapp/settings.html"
