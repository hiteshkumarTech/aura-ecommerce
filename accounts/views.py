"""Authentication views with anonymous-cart merging on login."""
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from store.services import merge_session_cart

from .forms import RegisterForm, StyledLoginForm


class StoreLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        # Capture the session key BEFORE login() cycles it, then merge carts.
        old_session_key = self.request.session.session_key
        response = super().form_valid(form)
        merge_session_cart(self.request, self.request.user, old_session_key)
        messages.success(self.request, f"Welcome back, {self.request.user.username}.")
        return response


class StoreLogoutView(LogoutView):
    next_page = reverse_lazy("store:product_list")


def register(request):
    if request.user.is_authenticated:
        return redirect("store:product_list")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            old_session_key = request.session.session_key
            user = form.save()
            login(request, user)
            merge_session_cart(request, user, old_session_key)
            messages.success(request, "Your account is ready. Happy shopping!")
            return redirect("store:product_list")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
