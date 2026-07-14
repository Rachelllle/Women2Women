# Women2Women

Application web de **suivi du cycle menstruel et de bien-être féminin**.
Elle accompagne l'utilisatrice au quotidien à travers quatre fonctionnalités.

Construite avec **Flask** (Python) et **React** (chargé dans le navigateur, sans build).

---

## Fonctionnalités

| Fonctionnalité | Description | Techno |
|---|---|---|
| **Recommandations** | Conseils quotidiens personnalisés (nutrition, mouvement, mental, soin) selon la phase et le ressenti | Sentence Transformers `all-MiniLM-L6-v2` + similarité cosinus |
| **Suivi du cycle** | Roue du cycle, prédiction des règles, calendrier, historique (ajout / édition / suppression de cycles) | Calcul des phases + apprentissage de la durée moyenne |
| **Chatbot Lea** | Assistante santé qui répond aux questions sur le cycle | Qwen2.5-0.5B + LoRA + RAG (FAISS), 100 % local |
| **Alertes intelligentes** | Détection d'irrégularité / douleur anormale, suggestions de symptômes, notifications WhatsApp | Règles cliniques + Isolation Forest (scikit-learn) + Twilio |

---

## Prérequis

- **Python 3.10+**
- **Aucun serveur de base de données** — l'app utilise **SQLite** : un fichier
  `database/women2women.db` est créé automatiquement au premier lancement.

### Installation des dépendances

```bash
# Base de l'app + recommandations
pip install flask flask-cors flask-login werkzeug sentence-transformers

# Chatbot Lea (Qwen + LoRA + RAG)
pip install torch transformers "peft>=0.19.1" "accelerate>=1.0" faiss-cpu

# Alertes (ML + WhatsApp)
pip install scikit-learn joblib pandas twilio python-dotenv
```

---

## Lancer le projet

```bash
python app.py
```

- **App** : http://localhost:5000
- **Panneau admin** (type phpMyAdmin pour SQLite) : http://localhost:5000/admin — mot de passe : `admin123`

> ⚠️ Le tout premier message au chatbot télécharge le modèle Qwen (~1 Go) et le
> charge en mémoire (~30 s). Les messages suivants sont rapides.

---

## Alertes WhatsApp (optionnel)

Les alertes s'affichent dans l'app sans configuration. Pour les recevoir **sur
WhatsApp**, il faut un compte **Twilio** (mode sandbox) :

1. Créer un fichier `.env` à la racine (jamais commité) :
   ```
   TWILIO_ACCOUNT_SID=...
   TWILIO_AUTH_TOKEN=...
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   ```
2. Depuis WhatsApp, rejoindre le sandbox (envoyer `join <code>` au numéro Twilio).
3. Dans l'app : **You → WhatsApp alerts**, renseigner son numéro (`+33…`) et activer.
4. Lancer le job d'envoi :
   ```bash
   python -m alerting.alerting_job
   ```

> Sans `.env`, le job fonctionne en **mode simulation** (affiche les messages dans la console).

### Ré-entraîner / préparer les données d'alerting (déjà fait, si besoin)
```bash
python -m alerting.seed_from_kaggle      # catalogue de symptômes
python -m alerting.irregularity_model    # entraîne l'Isolation Forest
```

---

## Structure du projet

```
women2women/
├── app.py                  # point d'entrée : assemble les blueprints
├── database/               # SQLite : db.py, schema.py, admin_panel.py
├── auth/                   # inscription / connexion / session
├── profiles/               # profil + avatar
├── recommandation/         # modèle sémantique + endpoint /api/recommendations
│   ├── model.py
│   └── recommendations.csv # 1200 conseils
├── prediction/             # prédiction du prochain cycle
├── history/                # historique des cycles (log / ajout / édition)
├── chat/                   # chatbot Lea (Qwen + LoRA + RAG)
├── alerting/               # alertes ML + suggestions + job WhatsApp
├── static/
│   ├── styles.css
│   └── js/                 # lib, ui, onboarding, screens, app
└── Women2Women.html        # squelette de la SPA React
```

