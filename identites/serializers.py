from rest_framework import serializers
from .models import Personne, Entreprise, Utilisateur
from cartes.models import CarteRFID
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
import logging
from django.db import transaction
from django.contrib.auth.hashers import make_password

logger = logging.getLogger(__name__)

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}

class PersonneSerializer(serializers.ModelSerializer):
    from cartes.serializers import CarteRFIDSerializer
    carte_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False,
        allow_empty=True
    )
    # Ajouter le champ user_data pour recevoir les données utilisateur
    user_data = serializers.DictField(
        write_only=True,
        required=False,
        allow_empty=True
    )
    cartes_rfid_details = CarteRFIDSerializer(source='cartes_rfid', many=True, read_only=True)
    nombre_cartes = serializers.SerializerMethodField(read_only=True)
    utilisateur_info = UtilisateurSerializer(source='utilisateur_set.first', read_only=True)
    
    class Meta:
        model = Personne
        fields = '__all__'
        extra_kwargs = {
            'numero_piece': {'required': True},
            'date_naissance': {'required': True},
            'lieu_naissance': {'required': True},
            'nationalite': {'required': True},
            'type_piece': {'required': True}
        }

    def get_nombre_cartes(self, obj):
        return obj.cartes_rfid.count()

    def validate(self, data):
        required_fields = ['nom', 'prenom', 'date_naissance', 
                         'nationalite', 'type_piece', 'numero_piece']
        for field in required_fields:
            if field not in data or not data[field]:
                raise serializers.ValidationError({field: "Ce champ est obligatoire"})
        
        return data

    @transaction.atomic
    def create(self, validated_data):
        carte_ids_data = validated_data.pop('carte_ids', [])
        user_data = validated_data.pop('user_data', None)
        
        try:
            # Créer la personne
            personne = Personne.objects.create(**validated_data)
            logger.info(f"Personne créée: {personne.id}")
            
            # Créer l'utilisateur si les données sont fournies
            if user_data:
                try:
                    
                    username = user_data.get('username')
                    password = user_data.get('password')
                    role = user_data.get('role', 'CLIENT')
                    
                    if not username or not password:
                        logger.error("Nom d'utilisateur ou mot de passe manquant")
                        raise serializers.ValidationError("Le nom d'utilisateur et le mot de passe sont requis")
                    
                    
                    if Utilisateur.objects.filter(username=username).exists():
                        logger.error(f"Le nom d'utilisateur '{username}' existe déjà")
                        raise serializers.ValidationError(f"Le nom d'utilisateur '{username}' existe déjà.")
                    
                    
                    utilisateur = Utilisateur.objects.create(
                        username=username,
                        email=personne.email or '',
                        password=make_password(password),
                        role=role,
                        personne=personne,
                        actif=True
                    )
                    logger.info(f"Utilisateur créé avec succès: {utilisateur.id} pour la personne {personne.id}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
                    
                    personne.delete()
                    raise serializers.ValidationError(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            
            # Assigner les cartes si spécifiées
            if carte_ids_data:
                for carte_id in carte_ids_data:
                    try:
                        carte = CarteRFID.objects.get(
                            id=carte_id,
                            personne__isnull=True,
                            entreprise__isnull=True,
                            statut='INACTIVE'
                        )
                        carte.personne = personne
                        carte.statut = 'ACTIVE'
                        carte.date_activation = timezone.now()
                        carte.save()
                        
                        # Créer l'entrée d'historique
                        from cartes.models import HistoriqueStatutsCarte
                        HistoriqueStatutsCarte.objects.create(
                            carte=carte,
                            ancien_statut='INACTIVE',
                            nouveau_statut='ACTIVE',
                            motif_changement="Assignation automatique",
                            commentaire="",
                            agent_modificateur=self.context.get('request').user if self.context.get('request') else None,
                            adresse_ip="127.0.0.1",
                            user_agent=""
                        )
                        
                        logger.info(f"Carte {carte.id} assignée à la personne {personne.id}")
                    except CarteRFID.DoesNotExist:
                        logger.warning(f"Carte RFID {carte_id} non trouvée ou non disponible")
                        continue
            
            return personne
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la personne: {str(e)}")
            raise serializers.ValidationError(f"Erreur lors de la création: {str(e)}")

class EntrepriseSerializer(serializers.ModelSerializer):
    from cartes.serializers import CarteRFIDSerializer
    carte_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    # Ajouter le champ user_data pour recevoir les données utilisateur
    user_data = serializers.DictField(
        write_only=True,
        required=False,
        allow_empty=True
    )
    cartes_rfid_details = CarteRFIDSerializer(source='cartes_rfid', many=True, read_only=True)
    nombre_cartes = serializers.SerializerMethodField(read_only=True)
    utilisateur_info = UtilisateurSerializer(source='utilisateur_set.first', read_only=True)
    
    class Meta:
        model = Entreprise
        fields = '__all__'
        extra_kwargs = {
            'raison_sociale': {'required': True},
            'forme_juridique': {'required': True},
            'stat': {'required': True},
            'nif': {'required': True},
            'adresse_siege': {'required': True},
            'secteur_activite': {'required': True}
        }

    def get_nombre_cartes(self, obj):
        return obj.cartes_rfid.count()

    def validate_carte_ids(self, value):
        if value:
            for carte_id in value:
                try:
                    carte = CarteRFID.objects.get(
                        id=carte_id,
                        personne__isnull=True,
                        entreprise__isnull=True,
                        statut='INACTIVE'
                    )
                except CarteRFID.DoesNotExist:
                    raise serializers.ValidationError(
                        f"La carte {carte_id} n'existe pas, est déjà assignée ou n'est pas inactive"
                    )
        return value

    @transaction.atomic
    def create(self, validated_data):
        carte_ids_data = validated_data.pop('carte_ids', [])
        user_data = validated_data.pop('user_data', None)
        
        # Validation des champs obligatoires
        required_fields = ['raison_sociale', 'forme_juridique', 'stat', 'nif', 'adresse_siege']
        for field in required_fields:
            if field not in validated_data or not validated_data[field]:
                raise serializers.ValidationError({field: "Ce champ est obligatoire"})
        
        try:
           
            entreprise = Entreprise.objects.create(**validated_data)
            logger.info(f"Entreprise créée: {entreprise.id}")
            
            
            if user_data:
                try:
                    # Validation des données utilisateur
                    username = user_data.get('username')
                    password = user_data.get('password')
                    role = user_data.get('role', 'CLIENT')
                    
                    if not username or not password:
                        logger.error("Nom d'utilisateur ou mot de passe manquant")
                        raise serializers.ValidationError("Le nom d'utilisateur et le mot de passe sont requis")
                    
                    # Vérifier que le nom d'utilisateur n'existe pas déjà
                    if Utilisateur.objects.filter(username=username).exists():
                        logger.error(f"Le nom d'utilisateur '{username}' existe déjà")
                        raise serializers.ValidationError(f"Le nom d'utilisateur '{username}' existe déjà.")
                    
                    # Créer l'utilisateur
                    utilisateur = Utilisateur.objects.create(
                        username=username,
                        email=entreprise.email or '',
                        password=make_password(password),
                        role=role,
                        entreprise=entreprise,
                        actif=True
                    )
                    logger.info(f"Utilisateur créé avec succès: {utilisateur.id} pour l'entreprise {entreprise.id}")
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la création de l'utilisateur: {str(e)}")
                    entreprise.delete()
                    raise serializers.ValidationError(f"Erreur lors de la création de l'utilisateur: {str(e)}")
            
            # Assigner les cartes si spécifiées
            if carte_ids_data:
                for carte_id in carte_ids_data:
                    try:
                        carte = CarteRFID.objects.get(
                            id=carte_id,
                            personne__isnull=True,
                            entreprise__isnull=True,
                            statut='INACTIVE'
                        )
                        carte.entreprise = entreprise
                        carte.statut = 'ACTIVE'
                        carte.date_activation = timezone.now()
                        carte.save()
                        
             
                        from cartes.models import HistoriqueStatutsCarte
                        HistoriqueStatutsCarte.objects.create(
                            carte=carte,
                            ancien_statut='INACTIVE',
                            nouveau_statut='ACTIVE',
                            motif_changement="Assignation automatique",
                            commentaire="",
                            agent_modificateur=self.context.get('request').user if self.context.get('request') else None,
                            adresse_ip="127.0.0.1",
                            user_agent=""
                        )
                        
                        logger.info(f"Carte {carte.id} assignée à l'entreprise {entreprise.id}")
                    except CarteRFID.DoesNotExist:
                        logger.warning(f"Carte RFID {carte_id} non trouvée ou non disponible")
                        continue
            
            return entreprise
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'entreprise: {str(e)}")
            raise serializers.ValidationError(f"Erreur lors de la création: {str(e)}")
