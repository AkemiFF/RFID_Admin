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


logger = logging.getLogger(__name__)

class PersonneSerializer(serializers.ModelSerializer):
    from cartes.serializers import CarteRFIDSerializer
    carte_ids = serializers.ListField(
        child=serializers.UUIDField(), 
        write_only=True, 
        required=False,
        allow_empty=True
    )
    cartes_rfid_details = CarteRFIDSerializer(source='cartes_rfid', many=True, read_only=True)
    nombre_cartes = serializers.SerializerMethodField(read_only=True)
    
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
        # Validation des champs obligatoires
        required_fields = ['nom', 'prenom', 'date_naissance', 'lieu_naissance', 
                         'nationalite', 'type_piece', 'numero_piece']
        for field in required_fields:
            if field not in data or not data[field]:
                raise serializers.ValidationError({field: "Ce champ est obligatoire"})
        
        return data

    def create(self, validated_data):
        carte_ids_data = validated_data.pop('carte_ids', [])
        
        try:
            personne = Personne.objects.create(**validated_data)
            
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
                        
                        # Sauvegarder avec l'adresse IP (peut être une IP par défaut)
                        with transaction.atomic():
                            carte.save()
                            # Créer l'entrée d'historique avec une IP par défaut
                            from cartes.models import HistoriqueStatutsCarte
                            HistoriqueStatutsCarte.objects.create(
                                 carte=carte,
                                ancien_statut='INACTIVE',
                                nouveau_statut='ACTIVE',
                                motif_changement="Assignation automatique",  # Champ correct
                                commentaire="",  # Champ obligatoire
                                agent_modificateur=self.context['request'].user if self.context.get('request') else None,  # Champ correct
                                adresse_ip="127.0.0.1",  # IP par défaut
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
    cartes_rfid_details = CarteRFIDSerializer(source='cartes_rfid', many=True, read_only=True)
    nombre_cartes = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Entreprise
        fields = '__all__'
        extra_kwargs = {
            'raison_sociale': {'required': True},
            'forme_juridique': {'required': True},
            'stat': {'required': True},
            'nif': {'required': True},
            'adresse_siege': {'required': True},
            'date_creation_entreprise': {'required': True},
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

    def create(self, validated_data):
        carte_ids_data = validated_data.pop('carte_ids', [])
        
        # Validation des champs obligatoires
        required_fields = ['raison_sociale', 'forme_juridique', 'stat', 'nif',
                         'adresse_siege', 'date_creation_entreprise', 'secteur_activite']
        for field in required_fields:
            if field not in validated_data or not validated_data[field]:
                raise serializers.ValidationError({field: "Ce champ est obligatoire"})
        
        entreprise = Entreprise.objects.create(**validated_data)
        
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
                    with transaction.atomic():
                            carte.save()
                            # Créer l'entrée d'historique avec une IP par défaut
                            from cartes.models import HistoriqueStatutsCarte
                            HistoriqueStatutsCarte.objects.create(
                                carte=carte,
                                ancien_statut='INACTIVE',
                                nouveau_statut='ACTIVE',
                                motif_changement="Assignation automatique",
                                commentaire="", 
                                agent_modificateur=self.context['request'].user if self.context.get('request') else None,  # Champ correct
                                adresse_ip="127.0.0.1", 
                                user_agent=""
                            )


                    logger.info(f"Carte {carte.id} assignée à l'entreprise {entreprise.id}")
                except CarteRFID.DoesNotExist:
                    logger.warning(f"Carte RFID {carte_id} non trouvée ou non disponible")
                    continue
        
        return entreprise

class UtilisateurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Utilisateur
        fields = '__all__'
        extra_kwargs = {'password': {'write_only': True}}