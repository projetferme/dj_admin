from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login_view'),
    path('login_view.html', views.login_view, name='login_view'),

    path('register.html', views.register, name='register'),
    path('index.html', views.index, name='index'),
    path('ferme.html', views.ferme, name='ferme'),
    path('supprimer_ferme/<int:ferme_id>/', views.supprimer_ferme, name='supprimer_ferme'),

    path('ferme/<int:ferme_id>/', views.ferme, name='modifier_ferme'),
    path('loteDePoulets.html', views.loteDePoulets, name='loteDePoulets'),
    #path('lots/', views.loteDePoulets, name='loteDePoulets'),  # Création
    path('lots/<int:lot_id>/', views.loteDePoulets, name='modifier_lot'),  # Modification
    path('lots/supprimer/<int:lot_id>/', views.supprimer_lot, name='supprimer_lot'),
    #path('Alimentation.html', views.Alimentation, name='Alimentation'),

    path('alimentations.html', views.alimentations, name='alimentations'),

    
    path('alimentations/supprimer/<int:alimentation_id>/', views.supprimer_alimentation, name='supprimer_alimentation'),
    
    
    path('depense.html', views.depense, name='depense'),
    path('depense/<int:depense_id>/', views.depense, name='depense'),
             # Liste + formulaire création
    #path('depenses/<int:depense_id>/', views.depense, name='modifier_depense'),  # Modification

    # Suppression dépense
    path('depenses/<int:depense_id>/', views.supprimer_depense, name='supprimer_depense'),

    path('production.html', views.production, name='production'),  # liste + formulaire (sans id)
    # Modifier une production
    #path('production/', views.production, name='production'),
    path('production/<int:production_id>/', views.production, name='production'),


    # Supprimer une production
    path('supprimer_production/<int:production_id>/', views.supprimer_production, name='supprimer_production'),
        # Vue de la liste des productions (sans paramètre)

    path('ventes.html', views.ventes, name='ventes'),
    path('ventes/<int:vente_id>/', views.ventes, name='modifier_vente'),
    path('supprimer_vente/<int:vente_id>/', views.supprimer_vente, name='supprimer_vente'),
    path('mortalites.html', views.mortalites, name='mortalites'),
    path('supprimer_mortalite/<int:mortalite_id>/', views.supprimer_mortalite, name='supprimer_mortalite'),
    path('traitements.html', views.traitements, name='traitements'),
    path('parametres.html', views.parametres, name='parametres'),
    



]



