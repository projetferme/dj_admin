from django.db import models
from django.contrib.auth.models import User


class Ferme(models.Model):
    nom = models.CharField(max_length=100)
    proprietaire = models.CharField(max_length=100)
    localisation = models.CharField(max_length=255, blank=True, null=True)
    capital_investi = models.PositiveIntegerField()
    date_creation = models.DateField(auto_now_add=True)
    commentaire = models.CharField(max_length=100)


    def __str__(self):
        return self.nom
    

class LotPoulets(models.Model):
    
    nom_lot = models.CharField(max_length=100)
    fournisseur = models.CharField(max_length=100, blank=True, null=True)
    nombre_initial = models.PositiveIntegerField()
    prix_unitaire = models.PositiveIntegerField()
    date_arrivee = models.DateField()
    

    def __str__(self):
        return f"{self.nom_lot}"
    

class Alimentation(models.Model):
    lot = models.ForeignKey(LotPoulets, on_delete=models.CASCADE, related_name='alimentations')
    type_aliment = models.CharField(max_length=100)
    quantite_kg = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"{self.type_aliment} - {self.quantite_kg} kg pour {self.lot.nom_lot} le {self.date}"
    


class Categories(models.Model):
    libelle = models.CharField(max_length=100)



class Depense(models.Model):
    montant = models.PositiveIntegerField(verbose_name="Montant (FCFA)")
    date = models.DateField()
    categorie = models.ForeignKey(Categories,blank=True,on_delete=models.SET_NULL,null=True)
    remarque = models.TextField(blank=True, null=True, verbose_name="Remarques (facultatif)")

    def __str__(self):
        return f"{self.montant} FCFA"


# models.py


class Production(models.Model):
    
    date = models.DateField(auto_now_add=True, verbose_name="Date")
    lot = models.ForeignKey(LotPoulets, on_delete=models.CASCADE, related_name='productions')
    quantite = models.PositiveIntegerField()
    date = models.DateField()

    def __str__(self):
        return f"{self.type_production.capitalize()} - {self.quantite} {self.unite}"


class Vente(models.Model):
 
    type_produit = models.CharField(max_length=10)
    lot = models.ForeignKey('LotPoulets', on_delete=models.CASCADE, related_name='ventes')
    quantite_vendue = models.PositiveIntegerField(help_text="Nombre de poulets ou nombre d'œufs")
    prix_unitaire = models.PositiveIntegerField()
    montant_total = models.PositiveIntegerField(blank=True, null=True)
    client = models.CharField(max_length=100, blank=True, null=True)
    date_vente = models.DateField()

    def save(self, *args, **kwargs):
        if not self.montant_total:
            self.montant_total = self.quantite_vendue * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Vente {self.type_produit} - {self.quantite_vendue} unités"
    


class Mortalite(models.Model):
    lot = models.ForeignKey(LotPoulets, on_delete=models.CASCADE, related_name='mortalites')
    quantite_mort = models.PositiveIntegerField()
    date_mortalite = models.DateField()
    types = models.CharField(max_length=255, blank=True, null=True)

    cause = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Mortalité {self.quantite_mort} poulets le {self.date_mortalite}"

class Capital(models.Model):
    designation = models.CharField(max_length=100)
    quantites  = models.PositiveIntegerField()
    prix = models.PositiveIntegerField()
    date = models.DateField(blank=True, null=True)
    total = models.PositiveIntegerField(blank=True, null=True)
      
     