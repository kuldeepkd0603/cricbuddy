from django.views import View
from django.shortcuts import render,redirect
from django.db.models import Sum, Count
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


from math import floor
from iplfreak.models import Match, Deliveries, UserProfile
from iplfreak.forms import LoginForm, SignupForm, UserProfileForm


# Create your views here.
def index(request):
    return HttpResponseRedirect('/seasons/2019/')


def season_details(request, year):
    context = dict()

    matches = Match.objects.filter(season=year)[::-1]
    seasons = Match.objects.values('season').order_by('-season').distinct()
    special_matches = matches[:4]
    matches = matches[4:]

    context['matches'] = matches
    context['special_matches'] = special_matches
    context['seasons'] = seasons
    context['year'] = year
    context['total_matches'] = len(matches)

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        context['profile_pic'] = user_profile.profile_picture

    return render(request, 'iplfreak/season_details.html', context)


@login_required()
def match_details(request, year, match_id):
    context = dict()

    match = Match.objects.get(match_id=match_id)
    deliveries = Deliveries.objects.filter(match_id=match_id).values('batting_team', 'bowling_team')

    context['match'] = match
    context['year'] = year
    context['extras'] = sum(
        extra['extra_runs'] for extra in Deliveries.objects.filter(match_id=match_id).values('extra_runs'))

    context['team_1'] = deliveries[0]['batting_team']
    context['team_2'] = deliveries[0]['bowling_team']

    context['team_1_deliveries'] = Deliveries.objects.filter(match_id=match_id, innings=1)
    context['team_2_deliveries'] = Deliveries.objects.filter(match_id=match_id, innings=2)

    context['top_batsmen_1'] = Deliveries.objects.filter(match_id=match_id, innings=1).values('batsman').annotate(
        total=Sum('batsman_runs')).order_by('-total')[:3]
    context['top_batsmen_2'] = Deliveries.objects.filter(match_id=match_id, innings=2).values('batsman').annotate(
        total=Sum('batsman_runs')).order_by('-total')[:3]

    context['top_bowler_1'] = Deliveries.objects.filter(match_id=match_id, innings=1).exclude(
        player_dismissed=None).values('bowler').annotate(total=Count('bowler')).order_by('-total')[:3]
    context['top_bowler_2'] = Deliveries.objects.filter(match_id=match_id, innings=2).exclude(
        player_dismissed=None).values('bowler').annotate(total=Count('bowler')).order_by('-total')[:3]

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        context['profile_pic'] = user_profile.profile_picture

    return render(request, 'iplfreak/match_details.html', context)


class LoginController(View):
    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect('/seasons/2019/')

        login_form = LoginForm()
        return render(request, 'iplfreak/login.html', {
            'login_form': login_form
        })

    def post(self, request):
        login_form = LoginForm(request.POST)

        if login_form.is_valid():
            user = authenticate(
                request,
                username=login_form.cleaned_data['username'],
                password=login_form.cleaned_data['password']
            )

            if user is not None:
                login(request, user)
            else:
                messages.error(request, "Invalid Credentials")
        else:
            print(login_form.errors)

        return HttpResponseRedirect('/login/')


class SignupController(View):
    def get(self, request):
        signup_form = SignupForm()
        user_profile_form = UserProfileForm()
        return render(request, 'iplfreak/signup.html', {
            'signup_form': signup_form,
            'user_profile_form': user_profile_form
        })

    def post(self, request):
        signup_form = SignupForm(request.POST)
        user_profile_form = UserProfileForm(request.POST, request.FILES)

        if signup_form.is_valid() and user_profile_form.is_valid():
            new_user = User.objects.create_user(**signup_form.cleaned_data)

            user_profile_form = user_profile_form.save(commit=False)
            user_profile_form.user = User.objects.get(username=request.POST['username'])

            if not request.FILES:
                user_profile_form.profile_picture = 'profile_pictures/nopic.png'

            user_profile_form.save()

            login(request, user=new_user)
            return HttpResponseRedirect('/seasons/2019/')
        else:
            print(signup_form.errors, user_profile_form.errors)

        signup_form = SignupForm()
        return render(request, 'iplfreak/signup.html', {
            'signup_form': signup_form,
            'user_profile_form': user_profile_form
        })


@login_required()
def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/login/')


def points_table(request, year):
    context = dict()
    matches = Match.objects.filter(season=year)[::-1][4:] # removed non-league matches

    table = dict()
    for match in matches:
        if match.team1 not in table:
            table[match.team1] = 0

        if match.team2 not in table:
            table[match.team2] = 0

        if match.result == 'normal':
            table[match.winner] += 2
        else:
            table[match.team1] += 1
            table[match.team2] += 1

    context['points_table'] = sorted(table.items(), key=lambda x: x[1], reverse=True)

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        context['profile_pic'] = user_profile.profile_picture

    context['year'] = year
    return render(request, 'iplfreak/points_table.html', context)


@login_required()
def teams(request, year):
    context = dict()
    context['teams'] = Match.objects.filter(season=year).values('team1').distinct()
    context['year'] = year

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        context['profile_pic'] = user_profile.profile_picture

    return render(request, 'iplfreak/teams.html', context)


@login_required()
def team_details(request, year, team_name):
    context = dict()
    context['year'] = year
    context['team_name'] = team_name

    if request.user.is_authenticated:
        user_profile = UserProfile.objects.get(user=request.user)
        context['profile_pic'] = user_profile.profile_picture

    played = Match.objects.filter(Q(season=year) & (Q(team1=team_name) | Q(team2=team_name))).count()
    won = Match.objects.filter(Q(season=year) & Q(winner=team_name)).count()

    context['win_percentage'] = floor((won / played) * 100)
    context['played'] = played
    context['won'] = won

    context['best_players'] = Match.objects.filter(Q(season=year) & (Q(winner=team_name))).values('player_of_the_match').annotate(total=Count('player_of_the_match')).order_by('-total')
    context['recent_matches'] = Match.objects.filter(Q(season=year) & (Q(team1=team_name) | Q(team2=team_name)))[:3]
    context['best_batsman'] = Deliveries.objects.filter(Q(match_id__season=year) & Q(batting_team=team_name)).values('batsman').annotate(total=Count('batsman_runs')).order_by('-total')[:5]
    context['best_bowlers'] = Deliveries.objects.filter(Q(match_id__season=year) & Q(bowling_team=team_name)).exclude(player_dismissed__exact='').values('bowler').annotate(total=Count('player_dismissed')).order_by('-total')[:5]

    return render(request, 'iplfreak/team_details.html', context)
#-----------------------------------------------------------------
import pandas as pd
import pickle
import sklearn
from  joblib import load
import numpy as np
import os

# model 
pipe =pickle.load(open('iplfreak\pipe1.pkl','rb'))
filename =r'C:\IPLFreak-master\iplfreak\first-innings-score-lr-model.joblib'
regressor = load(filename)


def first_inning(request):   
    return render(request, 'iplfreak/second_inning.html')
def result_first(request):
    batting_team = request.GET['batting-team']
    bowling_team = request.GET['bowling-team']
    selected_city= request.GET['host_city']
    target=int(request.GET['Target'])
    overs= float(request.GET['over_completed'])
    wickets= float(request.GET['wicket_out'])
    score=float(request.GET['Score'])
    runs_left=target - score
    balls_left= 120 - (overs*6)
    wickets= 10-wickets
    crr= score/overs
    rrr= (runs_left*6)/balls_left
    
    input_df=pd.DataFrame({'batting_team':[batting_team],'bowling_team':[bowling_team],'city':[selected_city],
                           'runs_left':[runs_left],'balls_left':[balls_left],'wickets':[wickets],'total_runs_x':
                               [target],'crr':[crr],'rrr':[rrr]})
    result=pipe.predict_proba(input_df)
    loss=result[0][0]
    win=result[0][1]
    return render(request, 'iplfreak/result_second.html',{'loss':loss,'win':win})

def second_inning(request):
    return render(request, 'iplfreak/first_inning.html')

def result_second(request):
    
    temp_array = list()
    
    batting_team=request.GET['batting-team']
    if batting_team == 'Chennai Super Kings':
        temp_array = temp_array + [1,0,0,0,0,0,0,0]
    elif batting_team == 'Delhi Daredevils':
        temp_array = temp_array + [0,1,0,0,0,0,0,0]
    elif batting_team == 'Kings XI Punjab':
        temp_array = temp_array + [0,0,1,0,0,0,0,0]
    elif batting_team == 'Kolkata Knight Riders':
        temp_array = temp_array + [0,0,0,1,0,0,0,0]
    elif batting_team == 'Mumbai Indians':
        temp_array = temp_array + [0,0,0,0,1,0,0,0]
    elif batting_team == 'Rajasthan Royals':
        temp_array = temp_array + [0,0,0,0,0,1,0,0]
    elif batting_team == 'Royal Challengers Bangalore':
        temp_array = temp_array + [0,0,0,0,0,0,1,0]
    elif batting_team == 'Sunrisers Hyderabad':
        temp_array = temp_array + [0,0,0,0,0,0,0,1]
        
        
    bowling_team = request.GET['bowling-team']
    if bowling_team == 'Chennai Super Kings':
        temp_array = temp_array + [1,0,0,0,0,0,0,0]
    elif bowling_team == 'Delhi Daredevils':
        temp_array = temp_array + [0,1,0,0,0,0,0,0]
    elif bowling_team == 'Kings XI Punjab':
        temp_array = temp_array + [0,0,1,0,0,0,0,0]
    elif bowling_team == 'Kolkata Knight Riders':
        temp_array = temp_array + [0,0,0,1,0,0,0,0]
    elif bowling_team == 'Mumbai Indians':
        temp_array = temp_array + [0,0,0,0,1,0,0,0]
    elif bowling_team == 'Rajasthan Royals':
        temp_array = temp_array + [0,0,0,0,0,1,0,0]
    elif bowling_team == 'Royal Challengers Bangalore':
        temp_array = temp_array + [0,0,0,0,0,0,1,0]
    elif bowling_team == 'Sunrisers Hyderabad':
        temp_array = temp_array + [0,0,0,0,0,0,0,1]
    overs = float(request.GET['overs'])
    runs = int(request.GET['runs'])
    wickets = int(request.GET['wickets'])
    runs_in_prev_5 = int(request.GET['runs_in_prev_5'])
    wickets_in_prev_5 = int(request.GET['wickets_in_prev_5'])
    
    temp_array = temp_array + [overs, runs, wickets, runs_in_prev_5, wickets_in_prev_5]
    data = np.array([temp_array])
    my_prediction = int(regressor.predict(data)[0])
    #print(my_prediction)
    
    
    
    return render(request, 'iplfreak/result_first.html',{'lower_limit':my_prediction-10, 'upper_limit' : my_prediction+5})
    '''if request.method == 'POST':
        batting_team = request.POST.get('batting_team')
        bowling_team = request.POST.get('bowling_team')
        selected_city= request.POST.get('selected_city')
        target= request.POST.get('target')
        score= request.POST.get('score')
        wickets= request.POST.get('wickets')
        runs_left=target - score
        balls_left= 120 - (overs*6)
        wickets= 10-wickets
        crr= score/overs
        rrr= (runs_left*6)/balls_left
    
        input_df=pd.DataFrame({'batting_team':[batting_team],'bowling_team':[bowling_team],'city':[selected_city],
                           'runs_left':[runs_left],'balls_left':[balls_left],'wickets':[wickets],'total_runs_x':
                               [target],'crr':[crr],'rrr':[rrr]})
        result=pipe.predict_proba(input_df)
        return render(request, 'iplfreak/result_second.html',context=result)
        '''
        
def score_predictor(request):
    return render(request, 'iplfreak/score_predictor.html')
def ipl_dashboard(request):
    return redirect("https://rdpahalavan.github.io/IPL-Data-Visualization/")
    #return render(request, 'iplfreak/ipl_dashboard.html')
def batting(request):
    return render(request, 'iplfreak/batting.html')
def bowling(request):
    return render(request, 'iplfreak/bowling.html')
def ipl(request):
    return render(request, 'iplfreak/ipl.html')
def all_teams(request):
    return render(request, 'iplfreak/all_teams.html')