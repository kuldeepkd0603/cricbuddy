from iplfreak import views
from django.urls import path
from . import views


urlpatterns = [
    path('seasons/<int:year>/', views.season_details, name='season_details'),
    path('seasons/<int:year>/<int:match_id>/', views.match_details, name='match_details'),
    path('seasons/<int:year>/points-table/', views.points_table, name='points_table'),
    path('login/', views.LoginController.as_view(), name='login'),
    path('signup/', views.SignupController.as_view(), name='signup'),
    path('logout/', views.logout_user, name='logout'),
    path('', views.index, name='index'),
    path('teams/<int:year>/', views.teams, name='teams'),
    path('teams/<int:year>/<str:team_name>', views.team_details, name='team_details'),
    path('first_inning', views.first_inning, name='first_inning'),
    path('second_inning', views.second_inning, name='second_inning'),
    path('result_first', views.result_first, name='result_first'),
    path('result_second', views.result_second, name='result_second'),
    path('score_predictor', views.score_predictor, name='score_predictor'),
    path('ipl_dashboard', views.ipl_dashboard, name='ipl_dashboard'),
    path('batting', views.batting, name='batting'),
    path('bowling', views.bowling, name='bowling'),
    path('ipl', views.ipl, name='ipl'),
    path('all_teams', views.all_teams, name='all_teams'),
    
    
]
