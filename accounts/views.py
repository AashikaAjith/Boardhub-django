# accounts/views.py
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login 
from django.shortcuts import redirect, render
from .forms import SignUpForm
from django.contrib.auth.forms import AuthenticationForm
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView
from django.contrib.auth.models import User

# Existing signup view stays
def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

# Optional: your logout function (POST method recommended)
def logout_view(request):
    if request.method == 'POST':
        from django.contrib.auth import logout
        logout(request)
    return redirect('home')

@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    fields = ('first_name', 'last_name', 'email', )
    template_name = 'my_account.html'
    success_url = reverse_lazy('my_account')

    def get_object(self):
        return self.request.user