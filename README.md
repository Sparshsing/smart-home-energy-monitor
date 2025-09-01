# Smart Home Energy Monitoring with Conversational AI

## Overview

- This application enables smart home devices to upload their energy usage data to a database.
- It allows users to analyze their data with the help of charts.
- Users can also query the database in plain english.

## Tech Stack

### Database - TimescaleDB
**Pros:**
- An extension of PostgreSQL, for time series data
- High performance for data analytics suited for time series data
- Hypertables for efficient storage of timestamp data
- Continuous aggregates to precompute aggregates for fast summaries

**Cons:**
- Slightly complicated setup
- Not enough documentation

### Backend API - FastAPI
- Minimalistic and easy to use
- Automatic Swagger documentation

### Frontend - React + Vite.js
- Component based architecture for designing UI
- Vite enables fast build times

### Technology Choices
I have previously worked with PostgreSQL, hence TimescaleDB was a natural extension. I have built frontends using React earlier, and since it required a SPA, I used Vite because it's quite simple. I chose FastAPI due to its simplicity and fast development.

## Architecture

### Microservices Design
The APIs are developed as microservices with loose coupling. They share the database, but tables are owned by individual services:

- **Auth Service** - User table
- **Telemetry Service** - Product, Device, Telemetry tables  
- **AI Service** - None

### Service Responsibilities

**Auth Service**
- Responsible for user authentication with JWT token authentication
- Handles user registration and login

**Telemetry Service**
- Responsible for telemetry data ingestion and query
- Shares the same JWT secret to validate user credentials directly, instead of calling auth service on every request

**AI Service**
- Utilizes LLM to generate SQL queries related to telemetry data
- Sends LLM generated SQL queries to Telemetry service for execution
- Analyzes results using LLM to generate final response for the user

## LLM Safety

To ensure the LLM generates queries that utilize only the user's data, first the user's devices, along with product type are fetched. Then the LLM is provided these device IDs, and instructed to utilize only these device IDs to generate queries on the Telemetry table.

- LLM generated query is checked to reject any query with delete/update etc commands
- Later on, we can have a special user in the database with only readonly permissions for such LLM generated queries

## CI/CD - GitHub Actions

### Backend
- Utilizes GitHub Actions to automatically build Docker images, push to Azure Container Registry, and deploy to Azure Container Apps
- Gets triggered on any change in any service's code, or manually

### Frontend
- Utilizes GitHub Actions to automatically build the frontend and deploy to Azure Static Web Apps

## Deployment

- **Backend APIs** - Azure Container Apps (within a Container App environment)
- **Frontend** - Azure Static Web Apps  
- **Database** - Azure Database for PostgreSQL flexible server

**Demo Link:** https://kind-sea-0bc019c0f.1.azurestaticapps.net/

*Note: Above link may take upto 1 minute on login (due to cold start of containers) 

*Note: The above services are free (database is only free for 12 months)*



## How To Run

### Prerequisites
- Git
- Docker

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sparshsing/smart-home-energy-monitor
   cd smart-home-energy-monitor
   ```

2. **Add environment variables:**
   - Rename `sample.env` to `.env`
   - Provide any one of the LLM API keys (If you need AI chat)

3. **Run the application:**
   ```bash
   docker compose up --build
   ```

4. **Access the UI:**
   - Navigate to http://localhost:5173
   - Register a new user

5. **Initialize sample data in database:**
   ```bash
   docker compose exec telemetry-service uv run python initialize_data.py
   ```

6. **Query the AI:**
   - Open UI at http://localhost:5173
   - Login with your registered user
   - Ask queries to AI or click "Go to My Devices" to see data summary



## Assumptions

- It is assumed that telemetry data stores the power usage of the device (not energy consumed). Total energy consumed is calculated on the basis of average power during a given time period.
- Telemetry data upload endpoint is currently not protected. It's assumed that devices will authenticate themselves with a certificate, which is out of scope for this project.
- Tests have not been written due to time constraints
