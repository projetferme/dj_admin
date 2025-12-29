
# Create your views here.
from django.shortcuts import render,redirect, get_object_or_404
from django.db.models import F, Sum, ExpressionWrapper,Q,DecimalField
from .models import Vente,Ferme,Depense,LotPoulets,Mortalite,Alimentation,Categories,Production,Capital
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.conf import settings
# users/views.py

from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from decimal import Decimal
from datetime import datetime
import os,json


fichier = os.path.join(settings.BASE_DIR,"dash_admin/compteur.json")


def register(request):
    print('here 1')

    if request.method == 'POST':
    

        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confpassword = request.POST.get('confpassword', '')
        print(password,confpassword)
        # Découper le nom complet
        first_name, last_name = "", ""
        if " " in full_name:
            first_name, last_name = full_name.split(" ", 1)
        else:
            first_name = full_name
        
        # Vérifications
        if not full_name or not email or not password:
            messages.error(request, "Tous les champs sont obligatoires.")
            return redirect('parametres')

        if User.objects.filter(username=email).exists():
            messages.error(request, "Cet email est déjà utilisé.")
            return redirect('parametres')

        if confpassword != password:
            messages.error(request, "Pas de confirmation de mot de passe")
            return redirect('parametres')
        
        # Création de l’utilisateur
        User.objects.create(
            username=email,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=make_password(password)
        )

        messages.success(request, "Compte créé avec succès ! Vous pouvez vous connecter.")
        return redirect('login_view')

    return render(request, 'parametres.html',{'page':1})






def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            messages.error(request, "Email ou mot de passe incorrect.")
            return redirect('login_view')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)  # ici on utilise l'alias pour login django
            messages.success(request, f"Bienvenue {user.first_name or user.username} 👋")
            return redirect('index')
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'login_view.html')




@login_required(login_url='login_view')  # redirige vers la page login si pas connecté
def index(request):

        # totale par rapport au poulet
    total_pond = LotPoulets.objects.aggregate(Sum("nombre_initial"))['nombre_initial__sum'] or 0
    mortalite_cumulee_poulet = Mortalite.objects.filter(types='pondeuse').aggregate(total_morts=Sum('quantite_mort'))['total_morts'] or 0
    total_vend_poulet = Vente.objects.filter(type_produit='pondeuse').aggregate(total_ventes=Sum('quantite_vendue'))['total_ventes'] or 0


    # totale par rapport au oeuf

    total_prod = Production.objects.aggregate(Sum("quantite"))['quantite__sum'] or 0       
    mortalite_cumulee_oeuf = Mortalite.objects.filter(types='oeuf de pondeuse').aggregate(total_morts=Sum('quantite_mort'))['total_morts'] or 0
    total_vents_oeufs = Vente.objects.filter(type_produit__icontains='oeuf').aggregate(total_ventes=Sum('quantite_vendue'))['total_ventes'] or 0






    capital_investi = Capital.objects.aggregate(
    total=Sum('total')
    )['total'] or Decimal('0')

    chiffre_affaires = Vente.objects.aggregate(
        total=Sum(
            ExpressionWrapper(
                F('quantite_vendue') * F('prix_unitaire'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0

    fermes = Ferme.objects.all()
    depenses_ferme=0
    for ma_ferme in fermes:
        depenses_ferme = Depense.objects.aggregate(
        total_depenses=Sum('montant')
    )['total_depenses'] or 0
    
    marge_brute = chiffre_affaires - depenses_ferme


    # Récupération évolutions par mois/année
    evolution_raw = Vente.objects.annotate(
        mois=F('date_vente__month'),
        annee=F('date_vente__year')
    ).values('annee', 'mois').annotate(
        Pondeuses_vendus=Sum('quantite_vendue'),
        ca=Sum(
            ExpressionWrapper(
                F('quantite_vendue') * F('prix_unitaire'),
                output_field=DecimalField()
            )
        )
    ).order_by('annee', 'mois')

    calendrier = []
    Pondeuses_vendus_list = []
    ca_list = []
    
        # 1. Préparer les labels et données par mois/année
    for item in evolution_raw:
        label = f"{item['annee']}-{str(item['mois']).zfill(2)}"
        calendrier.append(label)
        Pondeuses_vendus_list.append(float(item['Pondeuses_vendus'] or 0))
        ca_list.append(float(item['ca'] or 0))

    # 2. Agrégation des ventes par type_produit pour le graphique barres
    ventes_par_type = Vente.objects.values('type_produit').annotate(
        total_quantite=Sum('quantite_vendue'),
        chiffre_affaires=Sum(
            ExpressionWrapper(
                F('prix_unitaire') * F('quantite_vendue'),
                output_field=DecimalField()
            )
        )
    )

    # 3. Types à afficher (uniformiser la casse)
    types_voulu = ['Oeuf de Pondeuse', 'Pondeuse']

    # 4. Initialisation du dictionnaire résultat
    resultats = {t: {'ca': 0, 'quantite': 0} for t in types_voulu}
    print(resultats)
    # 5. Remplissage des résultats avec les données récupérées (insensible à la casse et aux espaces)
    for vente in ventes_par_type:
        t_raw = vente['type_produit']
        
        if not t_raw:
            continue
        t_clean = t_raw.strip().lower()  # uniformisation
        
        for t_v in types_voulu:
            print(t_clean,t_v.lower())
            
            if t_clean == t_v.lower():
                resultats[t_v]['ca'] = float(vente['chiffre_affaires'] or 0)
                resultats[t_v]['quantite'] = vente['total_quantite'] or 0
                

    # 6. Préparation des listes pour le template (JS friendly)
    types = []
    ca = []
    quantites = []

    for t in types_voulu:
        types.append(t)  # garder le format original pour l'affichage
        ca.append(resultats[t]['ca'])
        quantites.append(resultats[t]['quantite'])



        # Calcul des totaux avec fallback à 0 pour éviter None
    total_commandes = LotPoulets.objects.aggregate(total=Sum('nombre_initial'))['total'] or 0
    total_depenses = Depense.objects.aggregate(total=Sum('montant'))['total'] or Decimal('0')
    total_mortalite = Mortalite.objects.aggregate(total=Sum('quantite_mort'))['total'] or 0

    # Pour les dépenses liées à l'alimentation, on filtre par catégories "aliment" ou "nourri" (insensible à la casse)
    total_quant = Production.objects.aggregate(Sum("quantite"))['quantite__sum'] or 0       

    # Convertir Decimal en float/int pour faciliter l'injection JS et affichage
    def to_number(val):
        if val is None:
            return 0
        if isinstance(val, Decimal):
            val = float(val)
        try:
            f = float(val)
            return int(f) if f.is_integer() else f
        except:
            return 0

    popularites = [
        {"id": "1", "article": "Commandes effectués", "valeur": to_number(total_commandes)},
        {"id": "2", "article": "Les dépenses effectuées", "valeur": to_number(total_depenses)},
        {"id": "3", "article": "Pertes", "valeur": to_number(total_mortalite)},
        {"id": "4", "article": "Productions d'Oeuf", "valeur": to_number(total_quant)},
    ]
   

    user = request.user  # l'utilisateur connecté

    # Exemples d'infos accessibles :
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name

    context = {
        'popularites': popularites,
        'total_Pondeuses':total_pond-mortalite_cumulee_poulet-total_vend_poulet,
        'total_oeuf':total_prod-mortalite_cumulee_oeuf-total_vents_oeufs ,

        'capital_investi': capital_investi,
        'chiffre_affaires': chiffre_affaires,
        'marge_brute': marge_brute,
        'calendrier': calendrier,
        'Pondeuses_vendus_list': Pondeuses_vendus_list,
        'ca_list': ca_list,
        'types': types,
        'ca': ca,
        'quantites': quantites,
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
    }

    return render(request, 'index.html', context)
   





def ferme(request):
    """
    Création d'une ferme (pas d'édition ici) + affichage de la liste.
    Tous les champs attendus : nom, localisation, proprietaire,
    capital_investi, date_creation, commentaire.
    """
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        localisation = request.POST.get('localisation', '').strip()
        proprietaire = request.POST.get('proprietaire', '').strip()
        capital_investi_str = request.POST.get('capital_investi', '').strip()
        date_creation_str = request.POST.get('date_creation', '').strip()
        commentaire = request.POST.get('commentaire', '').strip()

        errors = []

        # Validation basique
        if not nom:
            errors.append("Le nom de la ferme est requis.")
        if not localisation:
            errors.append("La localisation est requise.")
        if not proprietaire:
            errors.append("Le propriétaire est requis.")
        if not capital_investi_str:
            errors.append("Le capital investi est requis.")
        if not date_creation_str:
            errors.append("La date de création est requise.")
        if not commentaire:
            errors.append("Le commentaire est requis.")  # si tu veux le rendre optionnel, enlève cette ligne

        # conversions
        capital_investi = None
        try:
            capital_investi = Decimal(capital_investi_str)
        except Exception:
            errors.append("Le capital investi doit être un nombre valide.")

        date_creation = None
        try:
            date_creation = datetime.strptime(date_creation_str, '%Y-%m-%d').date()
        except Exception:
            errors.append("Format de la date invalide (attendu YYYY-MM-DD).")

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            # création
            Ferme.objects.create(
                nom=nom,
                localisation=localisation,
                proprietaire=proprietaire,
                capital_investi=capital_investi,
                date_creation=date_creation,
                commentaire=commentaire
            )
            messages.success(request, "✅ Ferme enregistrée avec succès.")
            return redirect('ferme')

    user = request.user  # l'utilisateur connecté
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    # GET ou erreurs -> affichage de la liste
    fermes = Ferme.objects.all().order_by('-date_creation')

    context = {
        'fermes': fermes,
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
    }
    return render(request, 'ferme.html',context )


def supprimer_ferme(request, ferme_id):
    ferme_obj = get_object_or_404(Ferme, id=ferme_id)
    ferme_obj.delete()
    messages.success(request, "🗑️ Ferme supprimée avec succès.")
    return redirect('ferme')


def loteDePoulets(request):
    lots = LotPoulets.objects.all()
    total_quantite = LotPoulets.objects.aggregate(Sum("nombre_initial"))['nombre_initial__sum'] or 0
   # total_quant_poule = LotPoulets.objects.filter(race="Pondeuse").aggregate(Sum("nombre_initial"))['nombre_initial__sum'] or 0
    names =0
    total = {
        'total_quantite':total_quantite,
       # 'total_quant_poule':total_quant_poule,
    }

    def lire_compteur():
        with open(fichier,"r") as f:
            return json.load(f)

    def ecrire_compteur(data):
        with open(fichier,"w") as f:
            json.dump(data,f)

    if request.method == 'POST':
        compte = lire_compteur()

        compte["valeur"] +=1
        ecrire_compteur(compte)
        compte = lire_compteur()

        
        try:
            if request.POST.get('modif'):
                print(type(int(request.POST.get('nombre_initial'))))
                
                names = LotPoulets.objects.get(id=request.POST.get('modif'))
                names.nom_lot =names.nom_lot
                
                names.fournisseur=request.POST.get('fournisseur')
                names.nombre_initial=request.POST.get('nombre_initial')
                names.prix=int(request.POST.get('prix_unitaire'))
                names.date_arrivee=request.POST.get('datetime')
                names.save()
            else:
                print(request.POST.get('date_arrivee')  )
                LotPoulets.objects.create(
                    
                    nom_lot="LOT"+"-"+str(int(compte["valeur"])),       
                    
                    fournisseur=request.POST.get('fournisseur', '').strip(),
                    nombre_initial=request.POST.get('nombre_initial', '').strip(),
                    prix_unitaire=request.POST.get('prix_unitaire', '').strip(),
                    date_arrivee=request.POST.get('datetime')

                )
                messages.success(request, "Lot enregistré avec succès.")
            return redirect('loteDePoulets')

        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            

    if request.GET.get('name'):
        
        names = LotPoulets.objects.get(id=request.GET.get('name'))
    

    user = request.user  # l'utilisateur connecté
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    # GET ou erreurs -> affichage de la liste
    fermes = Ferme.objects.all().order_by('-date_creation')

   
    context = {
        'fermes': fermes,
        'lots': lots,
        'fermes': fermes,
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'total':total,
        'names':names,
        
    }
    return render(request, 'loteDePoulets.html', context)


def supprimer_lot(request, lot_id):
    lot = get_object_or_404(LotPoulets, id=lot_id)
    lot.delete()
    messages.success(request, f"Le lot « {lot.nom_lot} » a été supprimé avec succès.")
    return redirect('loteDePoulets')

#def modifier_lot(request,lot_id):
    


def alimentations(request,  alimentation_id=None):
    
    if request.POST.get('modifi'):
        print()
        alimentation = get_object_or_404(Alimentation, pk=request.POST.get('modifi'))
    else:
        alimentation = None

    lots = LotPoulets.objects.all()
    types_aliments = [
        ('Prédémarrage', 'Prédémarrage'),
        ('Demarrage', 'Démarrage'),
        
    ]   
    passes=0
   
    if request.method == 'POST':
        lot_id = request.POST.get('lot')
        type_aliment = request.POST.get('type_aliment')
        quantite_kg = request.POST.get('quantite_kg')
        
        date = request.POST.get('datetime')
        print("ici")
        
        


        if alimentation:
            alimentation.lot_id = lot_id
            alimentation.type_aliment = type_aliment
            alimentation.quantite_kg = quantite_kg
            alimentation.date = date
            alimentation.save()
            messages.success(request, "Modifié avec succès.")
        else:
            Alimentation.objects.create(
                lot_id=lot_id,
                type_aliment=type_aliment,
                quantite_kg=quantite_kg,
                date=date
            )
            messages.success(request, "Ajouté avec succès.")
        return redirect('alimentations')

    alimentations_list = Alimentation.objects.all().order_by('-date')
    print("i")    


    if request.GET.get('modifier'):
        print("ii")    
        passes=2
        alimentation = Alimentation.objects.get(pk=request.GET.get('modifier'))

            
    quantite_kg = Alimentation.objects.aggregate(Sum("quantite_kg"))['quantite_kg__sum']
    user = request.user  # l'utilisateur connecté
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    # GET ou erreurs -> affichage de la liste
    fermes = Ferme.objects.all().order_by('-date_creation')

    context = {
        'nom':passes,
        'fermes': fermes,
        'alimentation': alimentation,
        'lots': lots,
        'types_aliments': types_aliments,
        'alimentations': alimentations_list,
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'quantite_kg':quantite_kg,
    }
    return render(request, 'alimentations.html', context)




def supprimer_alimentation(request, alimentation_id):
    alimentation = get_object_or_404(Alimentation, id=alimentation_id)
    alimentation.delete()
    messages.success(request, "Alimentation supprimée avec succès.")
    return redirect('alimentations')


@login_required(login_url='login_view')  # redirige vers la page login si pas connecté

def depense(request, depense_id=None):
    
    total_montant = Depense.objects.aggregate(Sum("montant"))['montant__sum']
    # Si on modifie, on récupère la dépense correspondante
    #depense = None
    #if depense_id:
     #   depense = get_object_or_404(Depense, pk=depense_id)

   

    if request.method == 'POST':
        if request.POST.get('libelle'):
            categories = Categories.objects.create(
                libelle = request.POST.get('libelle')
            )
            messages.success(request, "Catégories enregistrée avec succès.")
        
        
        categorie = request.POST.get('categorie')
        montant = request.POST.get('montant')
        remarque = request.POST.get('textes') 
        date_str = request.POST.get('date') 

        errors = []

     

        # Validation des champs
        if not remarque:
            pass
        if not categorie:
            errors.append("Le libellé est obligatoire.")
        if not montant:
            errors.append("Le montant est obligatoire.")
        if not date_str:
            errors.append("La date est obligatoire.")

        # Conversion et validation montant
        try:
            montant = montant
            
        except:
            errors.append("Le montant doit être un nombre valide.")

        if request.POST.get("modifi_dep"):
            save_me=Depense.objects.get(pk=request.POST.get("modifi_dep"))
            save_me.categorie=Categories.objects.get(pk=categorie)
            save_me.montant=montant
            save_me.remarque = remarque
            save_me.date=date_str
            save_me.save()
            messages.success(request, "Modifier  avec succès.")
        print(request.POST.get('ajout'))

        if request.POST.get('ajout'):
                
                # Création
                Depense.objects.create(
                    
                    categorie=Categories.objects.get(pk=categorie),
                    montant=montant,
                    remarque = remarque,
                    date=date_str
                )
                messages.success(request, "Dépense ajoutée avec succès.")

        return redirect('depense')

    # Liste des dépenses pour afficher dans le tableau
    depenses_list = Depense.objects.all().order_by('-date')
    
    depense=0
    if request.GET.get('modifier'):
        depense = Depense.objects.get(pk=request.GET.get('modifier'))
        print(depense)
    user = request.user  # l'utilisateur connecté
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    # GET ou erreurs -> affichage de la liste
    type_production = Categories.objects.all().order_by('-id')
   
    context = {
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'modifi_dep': depense,
        'type_production':type_production,
        
        'depenses': depenses_list,
        'total_montant':total_montant,
    }

    return render(request, 'depense.html', context)


def supprimer_depense(request, depense_id):
    depense = get_object_or_404(Depense, id=depense_id)
    depense.delete()
    messages.success(request, "Dépense supprimée avec succès.")
    return redirect('depense')



# views.py


@login_required(login_url='login_view')  # redirige vers la page login si pas connecté
def production(request):
    #les différents informations de production (total Oeuf poulet )
    lots = LotPoulets.objects.all()
    total_quant = Production.objects.aggregate(Sum("quantite"))['quantite__sum'] or 0       
    
    
    
    def lire_compteur():
        with open(fichier,"r") as f:
            return json.load(f)

    def ecrire_compteur(data):
        with open(fichier,"w") as f:
            json.dump(data,f)
    compte = lire_compteur()
    total={
        'total_quant':total_quant,
      
    }
       

    if request.method == 'POST':

        lot_id = request.POST.get('lot')
        
        quantite = request.POST.get('quantite')
        date = request.POST.get('date')
       
     

        errors = []

        if not lot_id:
            errors.append("Le lot est obligatoire.")
        
        if not quantite:
            errors.append("La quantité est obligatoire.")
       
       

        try:
            quantite = Decimal(quantite)
        except:
            errors.append("La quantité doit être un nombre valide.")

      

        if errors:
            for error in errors:    
                messages.error(request, error)
        else:
                
            ecrire_compteur(compte)
            compte = lire_compteur()
            lot = get_object_or_404(LotPoulets, pk=lot_id)
            print(lot,date)
            if request.POST.get('modifie'):
                saves= Production.objects.get(pk=request.POST.get('modifie'))
                saves.date = date
                saves.lot = lot
                saves.quantite = quantite
                saves.save()
                messages.success(request, "Production Modifier avec succès.")

            print("here")
            if request.POST.get("ajout"):
                print("here 2")

                Production.objects.create(
                    lot=lot,
                    
                    quantite=quantite,
                    date=date
                )
                messages.success(request, "Production enregistrée avec succès.")
            return redirect('production')

    productions_list = Production.objects.all().order_by('-date')

    total=total
    types_voulu = ['Oeuf de Pondeuse', 'Pondeuse']  # adapte à tes valeurs exactes dans la base
    only_product=0
    if request.GET.get("modifier"):
        only_product=Production.objects.get(pk=request.GET.get("modifier"))
    user = request.user  # l'utilisateur connecté
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    # GET ou erreurs -> affichage de la liste

    context = {
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'productions': productions_list,
        'lots': lots,
        'modif':only_product,
        'type_production_choices': types_voulu,
        'total':total,
    }
    return render(request, 'production.html', context)





def supprimer_production(request, production_id):
    production = get_object_or_404(Production, pk=production_id)
    production.delete()
    messages.success(request, "L'enregistrement de production a bien été supprimé.")
    return redirect('production')


@login_required(login_url='login_view')  # redirige vers la page login si pas connecté


def ventes(request):

        # totale par rapport au poulet
    total_pond = LotPoulets.objects.aggregate(Sum("nombre_initial"))['nombre_initial__sum'] or 0
    mortalite_cumulee_poulet = Mortalite.objects.filter(types='pondeuse').aggregate(total_morts=Sum('quantite_mort'))['total_morts'] or 0
    total_vend_poulet = Vente.objects.filter(type_produit='pondeuse').aggregate(total_ventes=Sum('quantite_vendue'))['total_ventes'] or 0

    # totale par rapport au oeuf

    total_prod = Production.objects.aggregate(Sum("quantite"))['quantite__sum'] or 0       
    mortalite_cumulee_oeuf = Mortalite.objects.filter(types='oeuf de pondeuse').aggregate(total_morts=Sum('quantite_mort'))['total_morts'] or 0
    total_vents_oeufs = Vente.objects.filter(type_produit__icontains='oeuf').aggregate(total_ventes=Sum('quantite_vendue'))['total_ventes'] or 0

    # 🟢 On peut aussi calculer le total global si besoin
    total_quant = Vente.objects.aggregate(total=Sum("quantite_vendue"))['total'] or 0
    lots = LotPoulets.objects.all()
    ventes = Vente.objects.all().order_by('-date_vente')
    page=0
    if request.GET.get('modifier'):
        page=Vente.objects.get(id=request.GET.get('modifier'))
    
   
    types_autorises = ['Pondeuse', 'oeuf de Pondeuse']


    

    if request.method == 'POST':
        type_produit = request.POST.get('type_produit', '').strip().lower()
        lot_id = request.POST.get('lot')
        quantite_vendue = request.POST.get('quantite_vendue')
        prix_unitaire = request.POST.get('prix_unitaire')
        
        date_vente = request.POST.get('date')
        errors=[]

        # --- Conversion des valeurs ---
        try:
            quantite_vendue = int(quantite_vendue)
            if quantite_vendue <= 0:
                errors.append("La quantité vendue doit être un entier positif.")
        except:
            errors.append("Quantité invalide.")

        try:
            prix_unitaire = Decimal(prix_unitaire)
        except:
            errors.append("Prix invalide.")

        lot = None
        if lot_id:
            lot = get_object_or_404(LotPoulets, pk=lot_id)

                # --- Suite de tes validations de stock (inchangée) ---
        if quantite_vendue and not errors:

            if type_produit == 'pondeuse':
                mortalite_cumulee = Mortalite.objects.filter(lot=lot,types="pondeuse").aggregate(
                    total_morts=Sum('quantite_mort')
                )['total_morts'] or 0
                    
                total_vendu = Vente.objects.filter(lot=lot,type_produit='pondeuse').aggregate(
                    total_ventes=Sum('quantite_vendue')
                )['total_ventes'] or 0
                stock_reel = lot.nombre_initial - mortalite_cumulee - total_vendu

                if request.POST.get('modifier'):
                    quantite=Vente.objects.get(id=request.POST.get('modifier'))
                    if quantite.type_produit == type_produit:

                            stock_reel = stock_reel + quantite.quantite_vendue
                

                if stock_reel <= 0:
                    errors.append("Plus de Pondeuses disponibles dans ce lot, impossible de vendre.")
                elif quantite_vendue > stock_reel:
                    errors.append(
                        f"Quantité vendue ({quantite_vendue}) dépasse la disponibilité réelle du lot ({stock_reel})."
                    )
            elif 'oeuf' in type_produit:
                mortalite_cumulee = Mortalite.objects.filter(lot=lot,types="oeuf de pondeuse").aggregate(
                    total_morts=Sum('quantite_mort')
                )['total_morts'] or 0

                production = Production.objects.filter(lot=lot).aggregate(
                    total_produit=Sum('quantite')
                )['total_produit'] or 0
               
                total_ventes_oeufs = Vente.objects.filter(
                    lot=lot, type_produit__icontains='oeuf'
                ).aggregate(total_ventes=Sum('quantite_vendue'))['total_ventes'] or 0
                
                    
                stock_oeufs = production - total_ventes_oeufs - mortalite_cumulee
                
                if request.POST.get('modifier'):
                    quantite=Vente.objects.get(id=request.POST.get('modifier'))
                    if quantite.type_produit == type_produit:

                        stock_oeufs = stock_oeufs + quantite.quantite_vendue
                print(stock_oeufs)
                if stock_oeufs <= 0:
                    errors.append("Plus d'oeufs disponibles dans ce lot, impossible de vendre.")
                elif quantite_vendue > stock_oeufs:
                    errors.append(  
                        f"Quantité vendue ({quantite_vendue}) dépasse la disponibilité réelle des oeufs ({stock_oeufs})."
                    )

        # --- Résultat final ---
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            if request.POST.get('modifier'):
                

                saves=Vente.objects.get(id=request.POST.get('modifier'))
                saves.ype_produit=type_produit
                saves.lot=lot
                saves.quantite_vendue=quantite_vendue
                saves.prix_unitaire=prix_unitaire
                saves.date_vente=date_vente
                saves.save()
                messages.success(request, f"Vente de {saves.type_produit} modifier avec succès.")
            if request.POST.get('Ajout'):
                vente = Vente.objects.create(
                    type_produit=type_produit,
                    lot=lot,
                    quantite_vendue=quantite_vendue,
                    prix_unitaire=prix_unitaire,
                
                    date_vente=date_vente
                )
                messages.success(request, f"Vente de {vente.type_produit} enregistrée avec succès.")
            return redirect('ventes')



    
    user = request.user  # l'utilisateur connecté
    username = user.username
    email = user.email
    first_name = user.first_name
    last_name = user.last_name
    # GET ou erreurs -> affichage de la liste
    types_voulu = ['Oeuf de Pondeuse', 'Pondeuse']  # adapte à tes valeurs exactes dans la base
  
    context = {
        'username': username,
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'lots': lots,
        'ventes': ventes,
        'type_production_choices':types_autorises or ['Pondeuse', 'oeuf de Pondeuse'],
        'total_prod':total_prod-total_vents_oeufs-mortalite_cumulee_oeuf,
        'total_pond' :total_pond-total_vend_poulet-mortalite_cumulee_poulet,
        'total_quant':total_quant,
        'nom':page,
       
    }

    return render(request, 'ventes.html', context)


def supprimer_vente(request, vente_id):
    vente = get_object_or_404(Vente, pk=vente_id)
    vente.delete()
    messages.success(request, "La vente a bien été supprimée.")
    return redirect('ventes')  





def mortalites(request):
    # Totaux
    total_quant = Mortalite.objects.aggregate(Sum("quantite_mort"))['quantite_mort__sum'] or 0
    total_prod = LotPoulets.objects.aggregate(Sum("nombre_initial"))['nombre_initial__sum'] or 0
    total_opo = Mortalite.objects.filter(types="oeuf de pondeuse").aggregate(Sum("quantite_mort"))['quantite_mort__sum'] or 0
    total_po = Mortalite.objects.filter(types="pondeuse").aggregate(Sum("quantite_mort"))['quantite_mort__sum'] or 0

    

    lots = LotPoulets.objects.all()
    mortalites = Mortalite.objects.all().order_by('-date_mortalite')
    total_mort = Mortalite.objects.aggregate(Sum("quantite_mort"))['quantite_mort__sum']

    # Types autorisés par défaut (au chargement initial)
    types_autorises = ['pondeuse', 'oeuf de pondeuse']

    if request.method == 'POST':
        lot_id = request.POST.get('lot')
        quantite_mort_str = request.POST.get('quantite_mort')
        cause = request.POST.get('cause', '').strip()
        types = request.POST.get('type_production', '').strip()
        date_mortalite =request.POST.get('date')
        errors = []

        lot = None
        if lot_id:
            lot = get_object_or_404(LotPoulets, pk=lot_id)
            lot_nom = lot.nom_lot.lower()

        # Validation quantité
        try:
            quantite_mort = int(quantite_mort_str)
            if quantite_mort <= 0:
                errors.append("La quantité doit être un entier positif.")
        except (ValueError, TypeError):
            errors.append("Quantité invalide.")

                       # --- Suite de tes validations de stock (inchangée) ---
        if quantite_mort and not errors:
            
            if types == 'pondeuse':
                mortalite_cumulee = Mortalite.objects.filter(lot=lot,types="pondeuse").aggregate(
                    total_morts=Sum('quantite_mort')
                )['total_morts'] or 0
                    
                total_vendu = Vente.objects.filter(lot=lot,type_produit='pondeuse').aggregate(
                    total_ventes=Sum('quantite_vendue')
                )['total_ventes'] or 0
                stock_reel = lot.nombre_initial - mortalite_cumulee - total_vendu

                if request.POST.get('modifier'):
                    quantite=Mortalite.objects.get(id=request.POST.get('modifier'))
                    if  quantite.types == types:     
                         stock_reel = stock_reel + quantite.quantite_mort
                

                if stock_reel <= 0:
                    errors.append("Plus de Pondeuses disponibles dans ce lot, impossible de vendre.")
                elif quantite_mort > stock_reel:
                    errors.append(
                        f"Quantité vendue ({quantite_mort}) dépasse la disponibilité réelle du lot ({stock_reel})."
                    )
            elif 'oeuf' in types:
                
                mortalite_cumulee = Mortalite.objects.filter(lot=lot,types="oeuf de pondeuse").aggregate(
                    total_morts=Sum('quantite_mort')
                )['total_morts'] or 0

                production = Production.objects.filter(lot=lot).aggregate(
                    total_produit=Sum('quantite')
                )['total_produit'] or 0
               
                total_ventes_oeufs = Vente.objects.filter(
                    lot=lot, type_produit__icontains='oeuf'
                ).aggregate(total_ventes=Sum('quantite_vendue'))['total_ventes'] or 0
                
                    
                stock_oeufs = production - total_ventes_oeufs - mortalite_cumulee
                
                if request.POST.get('modifier'):
                    quantite=Mortalite.objects.get(id=request.POST.get('modifier'))
                    if  quantite.types == types:     
                 
                        stock_oeufs = stock_oeufs + quantite.quantite_mort
            
                if stock_oeufs <= 0:
                    errors.append("Plus d'oeufs disponibles dans ce lot, impossible de vendre.")
                elif quantite_mort > stock_oeufs:
                    errors.append(
                        f"Quantité vendue ({quantite_mort}) dépasse la disponibilité réelle des oeufs ({stock_oeufs})."
                    )


            if errors:
        
                for error in errors:
                    messages.error(request, error)
            else:
                if request.POST.get("modifier"):
                    saves= Mortalite.objects.get(id=request.POST.get("modifier"))
                    saves.lot=lot
                    saves.quantite_mort=quantite_mort
                    saves.date_mortalite=date_mortalite
                    saves.cause=cause
                    saves.types=types
                    saves.save()
                    messages.success(request, "Mortalité modifier avec succès.")
                

                if request.POST.get("ajout"):

                    Mortalite.objects.create(
                        lot=lot,
                        quantite_mort=quantite_mort,
                        date_mortalite=date_mortalite,
                        cause=cause,
                        types=types
                    )
                    messages.success(request, "Mortalité enregistrée avec succès.")
                return redirect('mortalites')
      

   
    nom=0
    if request.GET.get('modif'):
        nom = Mortalite.objects.get(id=request.GET.get("modif"))
    # Infos utilisateur
    user = request.user
    context = {
        'nom':nom, 
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'lots': lots,
        'mortalites': mortalites,
        'total_mort': total_mort,
        'type_production_choices': types_autorises,

        'total_quant': total_quant,
        'total_po': total_po,
      
        'total_opo': total_opo,
        
    }

    return render(request, 'mortalites.html', context)





def supprimer_mortalite(request, mortalite_id):
    mortalite = get_object_or_404(Mortalite, pk=mortalite_id)
    mortalite.delete()
    messages.success(request, "L'enregistrement de mortalité a bien été supprimé.")
    return redirect('mortalites')  #

def traitements(request):
    return render(request ,"traitements.html")



def parametres(request):
    capital_investi = Capital.objects.aggregate(total=Sum('total'))['total'] or Decimal('0')
    
    page=0
    capital,total ='',''
    nom=0
    if request.GET.get('page')=="1":
        page=1
    if request.GET.get('page')=="2":
        if request.method == 'GET':
            

            if request.GET.get('ajout'):
            
                Enregistrer_capital = Capital.objects.create(
                  designation = request.GET.get('designation'),
                  quantites = int(request.GET.get('quantite')),
                  prix = int(request.GET.get('prix')),
                 date = request.GET.get('date'),
                 total = int(request.GET.get('quantite'))*int(request.GET.get('prix')),

                )
                messages.success(request, " enregistrée avec succès.")

            if request.GET.get('modifie'):
                motif = Capital.objects.get(id=request.GET.get('modifie'))
                motif.designation =  request.GET.get('designation')
                motif.quantites = int(request.GET.get('quantite'))
                motif.prix = int(request.GET.get('prix'))
                motif.date = request.GET.get('date')
                motif.total = int(request.GET.get('quantite'))*int(request.GET.get('prix'))
                motif.save()
                messages.success(request, "Modifier avec succès.")
                
            page = 2
        
    
    if request.GET.get('pages'):
        print('here i am')
        vente_id=request.GET.get('pages')
        page=2
        capital_id =  Capital.objects.get(pk=vente_id)
        capital_id.delete()
    if request.GET.get('modif'):
        page=2
        nom=Capital.objects.get(id=request.GET.get('modif'))

        

    capital = Capital.objects.all()
    
    context={
    'nom': nom,
     'page' : page,
     'capital':capital,
     'capital_investi': capital_investi
    }
    

    return render(request ,"parametres.html",context)



   
