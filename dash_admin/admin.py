from django.contrib import admin
from .models import Ferme, LotPoulets, Alimentation, Depense, Production, Vente, Mortalite,Categories,Capital

# Enregistrement simple des modèles
admin.site.register(Ferme)
admin.site.register(LotPoulets)
admin.site.register(Alimentation)
admin.site.register(Depense)
admin.site.register(Production)
admin.site.register(Vente)
admin.site.register(Mortalite)
admin.site.register(Categories)
admin.site.register(Capital)