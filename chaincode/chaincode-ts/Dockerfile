# Stage 1: Build the Typescript code
FROM node:18-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm install

# Copy source code
COPY . .

# Build the Typescript code
RUN npm run build

# Stage 2: Production image
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install only production dependencies
RUN npm install --only=production

# Copy compiled JS from build stage
COPY --from=build /app/dist ./dist

# Create a non-root user
RUN addgroup -S chaincode && adduser -S chaincode -G chaincode
USER chaincode

# Expose the gRPC port
EXPOSE 9999

# Set the command to start the chaincode server
CMD ["npm", "start"]
