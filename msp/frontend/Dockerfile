FROM node:20-alpine

WORKDIR /app

# Installer les dépendances au démarrage (pas au build)
# Le volume mount préserve node_modules entre les redémarrages
COPY package.json ./

# Exposer le port
EXPOSE 3000

# Commande de démarrage: installer les deps si nécessaire puis lancer le dev server
CMD ["sh", "-c", "npm install && npm run dev"]
