from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Personne, Entreprise, Utilisateur


@admin.register(Personne)
class PersonneAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'numero_piece', 'statut', 'date_creation']
    list_filter = ['statut', 'type_piece', 'nationalite']
    search_fields = ['nom', 'prenom', 'numero_piece', 'email']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ['raison_sociale', 'stat', 'nif', 'statut', 'date_creation']
    list_filter = ['statut', 'forme_juridique', 'secteur_activite']
    search_fields = ['raison_sociale', 'stat', 'nif', 'email']
    readonly_fields = ['id', 'date_creation', 'date_modification']


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'actif', 'date_creation']
    list_filter = ['role', 'actif', 'region_assignee']
    search_fields = ['username', 'email']
    readonly_fields = ['id', 'date_creation']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations supplémentaires', {
            'fields': ('personne', 'entreprise', 'role', 'region_assignee', 
                      'permissions_speciales', 'actif', 'force_changement_mdp')
        }),
    )
