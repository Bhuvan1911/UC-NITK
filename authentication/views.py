from django.shortcuts import render, redirect
from django.views import View
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
# from validate_email import validate_email
from django.contrib import messages
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes, force_text, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from .utils import account_activation_token
# from validate_email import validate_email
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm, ProfileUpdateForm , UserInfoForm
from .models import Profile


class RegistrationView(View):
    def get(self, request):

        context = {
            'u_form': UserInfoForm,
        }

        return render(request, 'authentication/register.html',context)

    def post(self, request):
        #GET USER DATA
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        print(request.POST)

        context={
            'fieldValues':request.POST,
            'u_form': UserInfoForm,
        }

        if not User.objects.filter(username=username).exists():
            if not User.objects.filter(email=email).exists():
                if len(password)<6:
                    messages.error(request, 'Password too short')
                    return render(request, 'authentication/register.html', context)
                contains_digit = any(map(str.isdigit, password))
                contains_alpha = any(map(str.isalpha, password))
                if not contains_digit or not contains_alpha:
                    messages.error(request, 'Password is not alphanumeric')
                    return render(request, 'authentication/register.html', context)

                # print(request.POST['usertype'])
                # print(request.POST['service'])

                if request.POST['usertype'] == 'Customer' and request.POST['service'] != 'Delivery':
                    messages.error(request, 'Customers can only do Delivery')
                    return render(request, 'authentication/register.html', context)

                user = User.objects.create_user(username = username, email = email)
                user.set_password(password)
                user.is_active = False
                p = Profile.objects.create(user=user,usertype = request.POST['usertype'],service = request.POST['service'])
                p.save()



                user.save()
                # p.save()

                #path to views
                # getting domain we are on
                # relative url to verification
                # encode uid
                # token
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                domain = get_current_site(request).domain
                link = reverse('activate', kwargs={'uidb64':uidb64, 'token':account_activation_token.make_token(user)})
                email_subject = 'Activate your account'

                activate_url = 'http://'+domain+link

                email_body = 'Hi' +user.username + 'Please use this link to verify your account\n' +activate_url
                # email_body = 'Activate account'


                email = EmailMessage(
                    email_subject,
                    email_body,
                    'noreply@semycolon.com',
                    [email],
                )
                email.send(fail_silently=False)
                messages.success(request, 'Account created successfully')
                return render(request, 'authentication/register.html')

        return render(request, 'authentication/register.html')


class UsernameValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        username = data['username']
        if not str(username).isalnum():
            return JsonResponse({'username_error': 'username should only contain alphanumeric characters'}, status=400)
        if User.objects.filter(username=username).exists():
            return JsonResponse({'username_error': 'sorry username in use,choose another one '}, status=409)
        return JsonResponse({'username_valid': True})


class EmailValidationView(View):
    def post(self, request):
        data = json.loads(request.body)
        email = data['email']
        if not validate_email(email):
            return JsonResponse({'email_error': 'Email is invalid'}, status=400)
        # if email[-11:]!="nitk.edu.in":
        #     return JsonResponse({'email_error': 'Email is invalid'}, status=400)
        if User.objects.filter(email=email).exists():
            return JsonResponse({'email_error': 'Sorry email in use,choose another one '}, status=409)
        return JsonResponse({'Email_valid': True})

# Create your views here.


class VerificationView(View):
    def get(self, request,uidb64, token):
        try:
            id = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=id)

            if not account_activation_token.check_token(user, token):
                return redirect('login'+'?message='+'User already activated')

            if user.is_active:
                return redirect('login')
            user.is_active = True
            user.save()

            messages.success(request, 'Account activated successfully')
            return redirect('login')
        except Exception as ex:
            pass

        return redirect('login')


class LoginView(View):
    def get(self, request):
        return render(request, 'authentication/login.html')

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        if username and password:
            user = auth.authenticate(username=username, password=password)

            if user:
                if user.is_active:
                    auth.login(request, user)
                    return redirect('/')
                messages.error(
                    request, 'Account is not active,please check your email')
                return render(request, 'authentication/login.html')
            messages.error(
                request, 'Invalid credentials,try again')
            return render(request, 'authentication/login.html')

        messages.error(
            request, 'Please fill all fields')
        return render(request, 'authentication/login.html')

class LogoutView(View):
    def post(self, request):
        auth.logout(request)
        messages.success(request, 'You have been logged out')
        return redirect('login')

@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST,
                                   request.FILES,
                                   instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect('profile')

    else:

        try:
            request.user.profile
        except Exception:
            Profile.objects.create(user=request.user)

        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'authentication/profile.html', context)
