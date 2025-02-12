git clone https://github.com/votre-username/VALWRLD-Bot.git
cd VALWRLD-Bot
```

2. Installez les dépendances
```bash
# Pour Node.js
npm install

# Pour Python
pip install -r requirements.txt
```

3. Configurez les variables d'environnement
Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```env
# Discord Bot Token (Obligatoire)
TOKEN=votre_token_discord

# Configuration de la base de données (Optionnel)
DATABASE_URL=votre_url_de_base_de_données

# OpenAI API Key (Optionnel - Pour les fonctionnalités d'IA)
OPENAI_API_KEY=votre_clé_api_openai

# Twilio (Optionnel - Pour les notifications SMS)
TWILIO_ACCOUNT_SID=votre_sid_twilio
TWILIO_AUTH_TOKEN=votre_token_twilio
TWILIO_PHONE_NUMBER=votre_numéro_twilio
```

4. Lancez le bot
```bash
# Pour Node.js
node index.js

# Pour Python
python main.py