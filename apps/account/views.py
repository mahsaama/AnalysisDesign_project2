from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from .forms import AccountCreationForm, LoginForm, SignUpForm
from django.contrib import messages
from .models import UserType, Doctor, Account, Order, Expertise
from django.views import generic


def being_doctor_check(user):
    return user.user_type == UserType.DOCTOR


# register A User using Account Creation Form And django auth app
def register(request):
    # form = AccountCreationForm()
    form = SignUpForm()

    if request.method == "POST":
        form = AccountCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('signin')
        else:
            # TODO error
            pass

    context = {"form": form}

    return render(request, 'account/register.html', context)


def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if being_doctor_check(user):
                #return redirect('expertise_orders_list')

                return redirect('doctor_list')
            else:
                return redirect('patient_orders_list')
        else:
            return HttpResponse('Username or Password is incorrect. <a href="">Return to login</a>')

    # form = AccountCreationForm()
    form = LoginForm()
    context = {"form": form}
    # print("----- form:", form)
    return render(request, 'account/login.html', context)


# log out from site
def signout(request):
    logout(request)
    return render(request, "home.html", {})


def home(request):
    return HttpResponse("Home Page")


# @login_required
# @user_passes_test(being_doctor_check)
def expertise_orders_list(request):
    if not request.user.is_authenticated:
        return HttpResponse("Log in")
    if request.user.user_type == UserType.PATIENT:
        return HttpResponse("You are not a doctor")
    doctor = Doctor.objects.get(user=request.user)
    expertise = doctor.expertise
    orders_list = Order.objects.filter(expertise=expertise, doctor=None)
    return render(request, 'account/expertise_orders_list.html', {'orders_list': orders_list})


# @login_required
# @user_passes_test(being_doctor_check)
# Change Doctor Status of Order in DB
def accept_order(request, order_id):
    if not request.user.is_authenticated:
        return HttpResponse("Log in")
    if request.user.user_type == UserType.PATIENT:
        return HttpResponse("You are not a doctor")
    order = Order.objects.get(id=order_id)
    if order.doctor:
        return HttpResponse("This Order was accepted by another doctor!")
    doctor = Doctor.objects.get(user=request.user)
    order.doctor = doctor
    order.save()
    doctor.not_processed_income += order.expertise.price
    doctor.save()
    return render(request, 'account/accept_order.html', {'order': order})

# View Expertise List For Patient
class ExpertiseView(generic.ListView):
    template_name = 'account/expertise_list.html'
    context_object_name = 'expertise_list'

    def get_queryset(self):
        return Expertise.objects.all()


class DoctorView(generic.ListView):
    template_name = 'account/doctor_list.html'
    context_object_name = 'doctor_list'

    def get_queryset(self):
        return Doctor.objects.all()

# View Request Page After Choosing Expertise
def request_for_chosen_expertise(request, exp_id):
    expertise = get_object_or_404(Expertise, pk=exp_id)
    return render(request, 'account/request_for_expertise.html', {'expertise': expertise})

# ADD Order Into DB
def add_order(request, exp_id):
    if not request.user.is_authenticated:
        return HttpResponse("Log in")
    if request.user.user_type != UserType.PATIENT:
        return HttpResponse("You are not a Patient")
    expertise = get_object_or_404(Expertise, pk=exp_id)
    address = request.POST['address']
    details = request.POST['details']
    o = Order(user_id=request.user.id, expertise_id=expertise.id, address=address, details=details)
    o.save()
    return HttpResponseRedirect(reverse('patient_orders_list'))

# View Patient's Previous Orders List
def patient_orders_list(request):
    orders_list = Order.objects.filter(user_id=request.user.id)
    return render(request, 'account/patient_orders_list.html', {'orders_list': orders_list[::-1]})

# save a score for orders
def rate_order(request):
    if request.method == 'POST':
        el_id = request.POST.get('el_id')
        val = request.POST.get('val')
        # print("***************", el_id, val, "********************")
        order = Order.objects.get(id=el_id)
        order.score = val
        order.save()
        return JsonResponse({'success':'true', 'score': val}, safe=False)
    return JsonResponse({'success':'false'})

def doctor_list(request, exp_id):

    expertise = get_object_or_404(Expertise, pk=exp_id)
    docs_list = Doctor.objects.filter(expertise=expertise)
    return render(request, 'account/doctor_list.html', {'doctor_list': docs_list})
