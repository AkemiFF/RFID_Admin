from celery import shared_task
from django.utils import timezone
import logging
import pytesseract
from PIL import Image
import json
import hashlib
from .models import DocumentIdentite

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_document_ocr(self, document_id):
    """Traite un document avec OCR pour extraire les données"""
    try:
        document = DocumentIdentite.objects.get(id=document_id)
        
        if document.statut_verification != 'EN_ATTENTE':
            return f"Document {document_id} déjà traité"
        
        # Chargement de l'image
        image_path = document.chemin_fichier
        image = Image.open(image_path)
        
        # Extraction du texte avec OCR
        extracted_text = pytesseract.image_to_string(image, lang='fra')
        
        # Analyse du texte selon le type de document
        ocr_data = analyze_document_text(extracted_text, document.type_document)
        
        # Mise à jour du document
        document.donnees_ocr = ocr_data
        document.statut_verification = 'VERIFIE' if ocr_data.get('valid', False) else 'REJETE'
        document.date_verification = timezone.now()
        document.save()
        
        # Log de l'opération
        from logs.models import LogSysteme
        LogSysteme.objects.create(
            niveau='INFO',
            action='DOCUMENT_OCR_PROCESSED',
            module='documents',
            message=f'Document {document_id} traité par OCR',
            donnees_apres={'ocr_result': ocr_data}
        )
        
        # Notification du résultat
        if document.personne:
            user_id = document.personne.utilisateur_set.first()
        elif document.entreprise:
            user_id = document.entreprise.utilisateur_set.first()
        else:
            user_id = None
            
        if user_id:
            from transactions.tasks import create_notification_task
            status_msg = "vérifié" if document.statut_verification == 'VERIFIE' else "rejeté"
            create_notification_task.delay(
                str(user_id.id),
                'INFO' if document.statut_verification == 'VERIFIE' else 'WARNING',
                f'Document {status_msg}',
                f'Votre document {document.type_document} a été {status_msg}.',
                'EMAIL'
            )
        
        logger.info(f"Document {document_id} traité par OCR avec succès")
        return f"Document {document_id} traité - statut: {document.statut_verification}"
        
    except DocumentIdentite.DoesNotExist:
        logger.error(f"Document {document_id} introuvable")
        return f"Document {document_id} introuvable"
    except Exception as exc:
        logger.error(f"Erreur lors du traitement OCR du document {document_id}: {exc}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries), exc=exc)
        else:
            # Marquer comme rejeté après épuisement des tentatives
            try:
                document = DocumentIdentite.objects.get(id=document_id)
                document.statut_verification = 'REJETE'
                document.commentaire_verification = f"Erreur OCR: {exc}"
                document.save()
            except:
                pass
            return f"Échec définitif du traitement OCR après {self.max_retries} tentatives"

def analyze_document_text(text, document_type):
    """Analyse le texte extrait selon le type de document"""
    ocr_data = {
        'raw_text': text,
        'extracted_fields': {},
        'valid': False,
        'confidence': 0.0
    }
    
    text_upper = text.upper()
    
    if document_type in ['CNI_RECTO', 'CNI_VERSO']:
        # Analyse d'une CNI
        if 'CARTE NATIONALE' in text_upper or 'IDENTITE' in text_upper:
            ocr_data['valid'] = True
            ocr_data['confidence'] = 0.8
            
            # Extraction des champs (regex basique)
            import re
            
            # Recherche du nom
            nom_match = re.search(r'NOM[:\s]*([A-Z\s]+)', text_upper)
            if nom_match:
                ocr_data['extracted_fields']['nom'] = nom_match.group(1).strip()
            
            # Recherche du prénom
            prenom_match = re.search(r'PRENOM[:\s]*([A-Z\s]+)', text_upper)
            if prenom_match:
                ocr_data['extracted_fields']['prenom'] = prenom_match.group(1).strip()
            
            # Recherche de la date de naissance
            date_match = re.search(r'(\d{2}[/\-]\d{2}[/\-]\d{4})', text)
            if date_match:
                ocr_data['extracted_fields']['date_naissance'] = date_match.group(1)
    
    elif document_type == 'PASSEPORT':
        # Analyse d'un passeport
        if 'PASSEPORT' in text_upper or 'PASSPORT' in text_upper:
            ocr_data['valid'] = True
            ocr_data['confidence'] = 0.7
    
    elif document_type in ['PERMIS_RECTO', 'PERMIS_VERSO']:
        # Analyse d'un permis de conduire
        if 'PERMIS' in text_upper or 'CONDUIRE' in text_upper:
            ocr_data['valid'] = True
            ocr_data['confidence'] = 0.7
    
    return ocr_data

@shared_task
def cleanup_temp_documents():
    """Nettoie les documents temporaires"""
    try:
        import os
        from django.conf import settings
        
        # Suppression des documents rejetés depuis plus de 30 jours
        old_rejected = DocumentIdentite.objects.filter(
            statut_verification='REJETE',
            date_verification__lt=timezone.now() - timezone.timedelta(days=30)
        )
        
        deleted_count = 0
        for doc in old_rejected:
            try:
                if os.path.exists(doc.chemin_fichier):
                    os.remove(doc.chemin_fichier)
                doc.delete()
                deleted_count += 1
            except Exception as e:
                logger.warning(f"Erreur lors de la suppression du document {doc.id}: {e}")
        
        logger.info(f"Suppression de {deleted_count} documents rejetés")
        return f"Suppression de {deleted_count} documents"
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des documents: {exc}")
        return f"Erreur: {exc}"

@shared_task
def generate_document_hash(document_id):
    """Génère le hash d'un document pour vérifier son intégrité"""
    try:
        document = DocumentIdentite.objects.get(id=document_id)
        
        # Calcul du hash SHA-256
        hash_sha256 = hashlib.sha256()
        with open(document.chemin_fichier, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        
        document.hash_fichier = hash_sha256.hexdigest()
        document.save()
        
        logger.info(f"Hash généré pour le document {document_id}")
        return f"Hash généré: {document.hash_fichier}"
        
    except Exception as exc:
        logger.error(f"Erreur lors de la génération du hash pour {document_id}: {exc}")
        return f"Erreur: {exc}"
