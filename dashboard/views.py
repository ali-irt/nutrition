from django.shortcuts import render, HttpResponse

def home(request):
    """Home page view"""
    context = {
        'page_title': 'Home',
        'current_page': 'home'
    }
    return render(request, 'home.html', context)

def lead(request):
    """Lead page view"""
    context = {
        'page_title': 'Lead',
        'current_page': 'lead'
    }
    return render(request, 'lead.html', context)

def client_profile(request, client_id):
    """Client profile view"""
    # Sample client data
    client_data = {
        'id': client_id,
        'name': 'Vera Rossakoff',
        'initials': 'VR',
        'weight_change': '-2.2',
        'weight_unit': 'lbs',
        'weight_status': 'Lost 2.2 lbs',
        'checkin_status': 'None',
        'checkin_message': 'No Check-in day',
        'nutrition_plan': '1 day to',
        'training_sessions': 'No',
        'training_message': 'Tracked last week',
        'calories': '1954',
        'calories_target': '3 Meals/day',
        'membership_status': 'Free',
        'membership_duration': 'for 3 months',
        'trial_message': 'Trial ends in 3 days',
        'app_message': 'Try the client app',
        'show_me_how': 'Show me how'
    }
    
    context = {
        'page_title': 'Client Profile',
        'current_page': 'clients',
        'client': client_data,
        'current_tab': request.GET.get('tab', 'overview')
    }
    return render(request, 'client_profile.html', context)

def nutrition(request):
    """Nutrition page view"""
    context = {
        'page_title': 'Nutrition',
        'current_page': 'nutrition'
    }
    return render(request, 'nutrition.html', context)

def workouts(request):
    """Workouts page view"""
    context = {
        'page_title': 'Workouts',
        'current_page': 'workouts'
    }
    return render(request, 'workouts.html', context)

def content(request):
    """Content page view"""
    context = {
        'page_title': 'Content',
        'current_page': 'content'
    }
    return render(request, 'content.html', context)

def meals(request):
    """Meals page view"""
    context = {
        'page_title': 'Meals',
        'current_page': 'meals'
    }
    return render(request, 'meals.html', context)

def clients_active(request):
   
    return render(request, 'clients.html')
def clients_started(request):
    return render(request,'clients_started.html')
def clients_completed(request):
    return render(request,'clients_ended.html')