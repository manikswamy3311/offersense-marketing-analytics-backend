# OfferSense Marketing Analytics Backend

A FastAPI-based backend system for marketing campaign analytics, providing insights into campaign performance, KPIs, customer segmentation, and offer effectiveness.

## 🚀 Features

- **Campaign Management**: Full CRUD operations for marketing campaigns
- **KPI Analytics**: Impressions, Clicks, Conversions, CTR, Conversion Rate
- **Performance Analysis**: Track and compare campaign performance
- **Customer Segmentation**: High/Medium/Low performer tiers
- **Offer Effectiveness**: Drop-off rate analysis, best/worst offer detection
- **Advanced Analytics**: Statistical summary, benchmark vs average, performance scores, top performers
- **CSV Export**: Download campaigns, performance, and segments as `.csv`
- **🔐 JWT Authentication**: Register, login, refresh tokens, logout with token blacklist
- **👥 Role-Based Access Control**: Admin / Analyst / Viewer permission tiers
- **🌐 OAuth2**: Google and GitHub social login
- **CI/CD**: GitHub Actions — runs tests on every push
- **Docker Ready**: Dev, production, and ELK stack docker-compose files
- **Kubernetes**: Full K8s manifests with HPA auto-scaling
- **Monitoring**: Prometheus + Grafana + ELK logging

## 📋 Prerequisites

### For Local Development
- Python 3.8+
- pip (Python package manager)

### For Docker
- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

## 🛠️ Quick Start - Choose Your Path

### Option 1: Docker (Recommended for All Users)

**Start the application in 30 seconds:**

```bash
# Clone repository
git clone https://github.com/manikswamy3311/offersense-marketing-analytics-backend.git
cd offersense-marketing-analytics-backend

# Start services with Docker Compose
docker-compose up
```

Then access:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Redis Cache**: localhost:6379
- **DB Manager**: http://localhost:8080

### Option 2: Local Python

1. **Clone the repository**
```bash
git clone https://github.com/manikswamy3311/offersense-marketing-analytics-backend.git
cd offersense-marketing-analytics-backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize the database**
```bash
python -m app.database.init_db
```

4. **Start the development server**
```bash
uvicorn app.main:app --reload
```

5. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive API Docs: `http://localhost:8000/docs`
   - Alternative Docs: `http://localhost:8000/redoc`

## 🐳 Docker Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild image
docker-compose build --no-cache

# Scale API instances
docker-compose up -d --scale api=3
```

## 🌍 Deployment

For comprehensive deployment guides, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Quick Deployment Options:

- **VPS/Dedicated Server**: Use `docker-compose-prod.yml`
- **Kubernetes**: Use `k8s-deployment.yaml`
- **AWS ECS**: Push to ECR, configure ECS
- **Heroku**: Use Procfile with Docker
- **Google Cloud Run**: Deploy directly
- **DigitalOcean App Platform**: Connect GitHub repo

## 📡 API Endpoints

> All analytics and CRUD endpoints require a valid JWT `Authorization: Bearer <token>` header.
> Role required is shown in brackets.

### Authentication
| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/auth/register` | Register new user | Public |
| POST | `/auth/login` | Login, receive tokens | Public |
| POST | `/auth/refresh` | Refresh access token | Public |
| GET | `/auth/me` | Get current user | Any |
| POST | `/auth/change-password` | Change password | Any |
| POST | `/auth/logout` | Logout + invalidate token | Any |
| GET | `/auth/google/login` | Google OAuth login | Public |
| GET | `/auth/github/login` | GitHub OAuth login | Public |

### Analytics
| Method | Endpoint | Description | Role |
|---|---|---|---|
| GET | `/api/kpis` | Overall KPIs | Analyst, Admin |
| GET | `/api/campaign-performance` | Per-campaign metrics | Analyst, Admin |
| GET | `/api/segments` | High/Medium/Low tiers | Analyst, Admin |
| GET | `/api/offer-effectiveness` | Drop-off rates | Analyst, Admin |
| GET | `/api/analytics/summary` | Statistical summary | Analyst, Admin |
| GET | `/api/analytics/benchmark` | vs portfolio average | Analyst, Admin |
| GET | `/api/analytics/scores` | Composite score 0–100 | Analyst, Admin |
| GET | `/api/analytics/top` | Top N by any metric | Analyst, Admin |

### Campaigns (CRUD)
| Method | Endpoint | Description | Role |
|---|---|---|---|
| GET | `/api/campaigns` | List all campaigns | Any |
| GET | `/api/campaigns/{id}` | Get single campaign | Any |
| POST | `/api/campaigns` | Create campaign | Admin |
| PUT | `/api/campaigns/{id}` | Update campaign | Admin |
| DELETE | `/api/campaigns/{id}` | Delete campaign | Admin |

### CSV Export
| Method | Endpoint | Description | Role |
|---|---|---|---|
| GET | `/api/export/campaigns` | Export campaigns CSV | Any |
| GET | `/api/export/performance` | Export performance CSV | Analyst, Admin |
| GET | `/api/export/segments` | Export segments CSV | Analyst, Admin |

### Public
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/test` | Health check |
| GET | `/api/load-data` | Load sample data |
| GET | `/api/check-data` | View raw data |

## 🗂️ Project Structure

```
offersense-marketing-analytics-backend/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── dependencies.py              # JWT auth dependency injection
│   ├── database/
│   │   ├── db.py                    # SQLite connection handler
│   │   ├── init_db.py               # Database initialisation script
│   │   └── schema.sql               # Table definitions
│   ├── models/
│   │   └── models.py                # Pydantic request/response models
│   ├── routes/
│   │   ├── auth_routes.py           # Authentication endpoints
│   │   ├── oauth_routes.py          # OAuth2 (Google/GitHub) endpoints
│   │   └── campaign_routes.py       # Analytics, CRUD, export endpoints
│   └── services/
│       ├── auth_service.py          # JWT + password hashing logic
│       ├── oauth_service.py         # OAuth2 token exchange + user linking
│       ├── campaign_analysis.py     # Performance analysis
│       ├── kpi_service.py           # KPI calculations
│       ├── segmentation_service.py  # Campaign segmentation
│       ├── crud_service.py          # CRUD operations
│       └── analytics_service.py    # Advanced analytics
├── notebooks/
│   └── eda.ipynb                    # Exploratory data analysis
├── tests/
│   ├── test_kpis.py                 # KPI & CRUD unit tests
│   ├── test_auth.py                 # Auth service unit tests
│   └── test_analytics.py           # Analytics service unit tests
├── .github/workflows/ci.yml         # GitHub Actions CI pipeline
├── Dockerfile                       # Multi-stage production image
├── docker-compose.yml               # Development stack
├── docker-compose-prod.yml          # Production stack (PostgreSQL + Nginx)
├── docker-compose-elk.yml           # ELK logging stack
├── k8s-deployment.yaml              # Kubernetes manifests
├── nginx.conf                       # Nginx reverse proxy config
├── prometheus.yml                   # Prometheus scrape config
├── requirements.txt                 # Python dependencies
└── README.md
```

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

## 📊 Data Model

### Campaign Table Schema
```sql
CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY,
    name TEXT,
    impressions INTEGER,
    clicks INTEGER,
    conversions INTEGER
);
```

### Calculated Metrics
- **CTR (Click-Through Rate)**: `(clicks / impressions) * 100`
- **Conversion Rate**: `(conversions / clicks) * 100`
- **Drop-off Rate**: `((clicks - conversions) / clicks) * 100`

### Segmentation Rules
- **High Performer**: Conversion rate ≥ 12%
- **Medium Performer**: Conversion rate between 10% and 12%
- **Low Performer**: Conversion rate < 10%

## 🔧 Configuration

### CORS Settings
Currently configured for frontend at `http://localhost:5173`. To modify, edit [app/main.py](app/main.py):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Logging
Logging is configured in [app/main.py](app/main.py). Default level: `INFO`

## 📦 Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pandas**: Data manipulation
- **NumPy**: Numerical operations
- **Pydantic**: Data validation

## 🐛 Error Handling

All endpoints include comprehensive error handling:
- **500 Internal Server Error**: Database or processing errors
- **404 Not Found**: Campaign not found (CRUD operations)
- **422 Unprocessable Entity**: Invalid request data (automatic Pydantic validation)

## 📝 Logging

Application logs include:
- API request/response information
- Database operations
- Error traces with full context

Logs format: `timestamp - module - level - message`

## 🔐 Security Considerations

**Current Status**: Development mode
- No authentication implemented
- No rate limiting
- CORS restricted to specific origin
- SQL injection protected by parameterized queries

**Production Recommendations**:
- Implement JWT authentication
- Add rate limiting
- Use environment variables for configuration
- Enable HTTPS
- Add API key validation

## 🚧 Future Enhancements

- [ ] Time-series analysis with date tracking
- [ ] Advanced forecasting models
- [ ] A/B testing framework
- [ ] ROI calculations
- [ ] Data export functionality (CSV, Excel)
- [ ] Dashboard integration
- [ ] Real-time analytics
- [ ] Multi-user support with authentication

## 📄 License

This project is for educational/internal use.

## 👥 Contributors

Manikanta - Backend Development

## 📞 Support

For issues or questions, please contact the development team.

---

**Version**: 1.0.0  
**Last Updated**: May 2026
