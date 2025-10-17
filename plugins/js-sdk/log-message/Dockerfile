FROM node:18-slim
WORKDIR /app

# Copy SDK library first
COPY ../psor-sdk-lib ./psor-sdk-lib

# Copy plugin-specific files
COPY package.json .
COPY plugin.js .

# Install dependencies (this will link the local SDK library)
RUN npm install --omit=dev

ENTRYPOINT ["node", "plugin.js"]
