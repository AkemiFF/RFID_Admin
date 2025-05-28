# RFID Pay Frontend

Interface utilisateur moderne pour le système de gestion de cartes RFID, construite avec Next.js 14, React Query et Tailwind CSS.

## 🚀 Fonctionnalités

### 📊 Tableau de bord
- Vue d'ensemble des statistiques en temps réel
- Aperçu des cartes RFID et tickets actifs
- Activité récente des transactions
- Gestion des plateformes liées
- Actions rapides

### 💳 Gestion des cartes
- Liste complète des cartes RFID
- Filtrage avancé (statut, type, recherche)
- Création de nouvelles cartes
- Activation/blocage des cartes
- Détails complets des cartes
- Pagination optimisée

### 🔄 Intégrations API
- Services TypeScript pour tous les endpoints Django
- Gestion d'état avec React Query
- Authentification automatique
- Gestion d'erreurs centralisée
- Cache intelligent des données

## 🛠️ Technologies

- **Next.js 14** - Framework React avec App Router
- **TypeScript** - Typage statique
- **Tailwind CSS** - Framework CSS utilitaire
- **React Query** - Gestion d'état serveur
- **React Hook Form** - Gestion des formulaires
- **Headless UI** - Composants accessibles
- **Heroicons** - Icônes SVG
- **Axios** - Client HTTP

## 📦 Installation

1. **Installer les dépendances**
\`\`\`bash
npm install
\`\`\`

2. **Configurer les variables d'environnement**
\`\`\`bash
cp .env.local.example .env.local
\`\`\`

3. **Démarrer le serveur de développement**
\`\`\`bash
npm run dev
\`\`\`

4. **Ouvrir l'application**
\`\`\`
http://localhost:3000
\`\`\`

## 🔧 Configuration

### Variables d'environnement
\`\`\`env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
\`\`\`

### Structure des services API

\`\`\`typescript
// Services disponibles
- cartesService: Gestion des cartes RFID
- transactionsService: Gestion des transactions
- identitesService: Gestion des personnes/entreprises
- notificationsService: Gestion des notifications
\`\`\`

### Endpoints Django intégrés

\`\`\`typescript
// Cartes RFID
GET    /api/cartes/cartes/          // Liste des cartes
POST   /api/cartes/cartes/          // Créer une carte
GET    /api/cartes/cartes/{id}/     // Détails d'une carte
PATCH  /api/cartes/cartes/{id}/     // Modifier une carte
DELETE /api/cartes/cartes/{id}/     // Supprimer une carte

// Transactions
GET    /api/transactions/transactions/     // Liste des transactions
POST   /api/transactions/transactions/     // Créer une transaction
POST   /api/transactions/transactions/{id}/reprocess/  // Retraiter

// Identités
GET    /api/identites/personnes/    // Liste des personnes
POST   /api/identites/personnes/    // Créer une personne
GET    /api/identites/entreprises/  // Liste des entreprises

// Notifications
GET    /api/notifications/notifications/   // Liste des notifications
POST   /api/notifications/notifications/   // Créer une notification
POST   /api/notifications/notifications/mark_as_read/  // Marquer comme lu
\`\`\`

## 🎨 Design System

### Couleurs principales
- **Purple**: Couleur primaire (#7c3aed)
- **Blue**: Actions secondaires (#0ea5e9)
- **Green**: Succès (#10b981)
- **Red**: Erreurs/Alertes (#ef4444)
- **Yellow**: Avertissements (#f59e0b)

### Composants réutilisables
- **Layout**: Structure de page avec sidebar et header
- **Modal**: Modales accessibles avec animations
- **StatusBadge**: Badges de statut colorés
- **Sidebar**: Navigation principale
- **Header**: Barre de navigation supérieure

### Animations
- **fade-in**: Apparition en fondu
- **slide-up**: Glissement vers le haut
- **card-hover**: Effet de survol des cartes

## 📱 Responsive Design

L'interface est entièrement responsive avec des breakpoints optimisés :
- **Mobile**: < 768px
- **Tablet**: 768px - 1024px
- **Desktop**: > 1024px

## 🔐 Authentification

Le système gère automatiquement :
- Stockage du token JWT
- Ajout automatique aux headers
- Redirection en cas d'expiration
- Gestion des erreurs 401

## 🚀 Déploiement

### Build de production
\`\`\`bash
npm run build
npm start
\`\`\`

### Variables d'environnement de production
\`\`\`env
NEXT_PUBLIC_API_URL=https://your-api-domain.com/api
\`\`\`

## 🔄 Intégration avec le backend Django

Le frontend communique avec le backend Django via les services TypeScript qui encapsulent tous les appels API. Chaque service correspond à une application Django :

- **cartesService** ↔ **cartes** app
- **transactionsService** ↔ **transactions** app  
- **identitesService** ↔ **identites** app
- **notificationsService** ↔ **notifications** app

## 📊 Gestion d'état

React Query gère intelligemment :
- **Cache** des données (5 min par défaut)
- **Refetch** automatique
- **Optimistic updates**
- **Background sync**
- **Error boundaries**

## 🎯 Prochaines fonctionnalités

- [ ] Page des transactions
- [ ] Gestion des rechargements
- [ ] Interface de notifications
- [ ] Rapports et analytics
- [ ] Mode sombre
- [ ] PWA (Progressive Web App)
- [ ] Tests unitaires et e2e

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT.
# RFID_Admin
