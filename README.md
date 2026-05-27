# OfferSense Marketing Analytics Backend

A FastAPI-based backend system for marketing campaign analytics, providing insights into campaign performance, KPIs, customer segmentation, and offer effectiveness.

## 🚀 Features

- **Campaign Management**: Full CRUD operations for marketing campaigns
- **KPI Analytics**: Calculate key metrics (Impressions, Clicks, Conversions, CTR, Conversion Rate)
- **Performance Analysis**: Track and compare campaign performance
- **Customer Segmentation**: Segment campaigns into High/Medium/Low performers
- **Offer Effectiveness**: Identify best and worst performing offers
- **Error Handling**: Comprehensive error handling and logging
- **Data Validation**: Pydantic models for request/response validation

## 📋 Prerequisites

- Python 3.8+
- pip (Python package manager)

## 🛠️ Installation

1. **Clone the repository**
```bash
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

## 🏃 Running the Application

1. **Start the development server**
```bash
uvicorn app.main:app --reload
```

2. **Access the API**
   - API Base URL: `http://localhost:8000`
   - Interactive API Docs: `http://localhost:8000/docs`
   - Alternative Docs: `http://localhost:8000/redoc`

## 📡 API Endpoints

### Core Endpoints

#### Health Check
- **GET** `/` - Check if server is running

#### Data Management
- **GET** `/api/load-data` - Load sample campaign data
- **GET** `/api/check-data` - View all raw campaign data

### Analytics Endpoints

#### KPIs
- **GET** `/api/kpis`
- Returns overall metrics: impressions, clicks, conversions, CTR, conversion rate

**Response Example:**
```json
{
  "impressions": 4500,
  "clicks": 500,
  "conversions": 60,
  "ctr": 11.11,
  "conversion_rate": 12.0
}
```

#### Campaign Performance
- **GET** `/api/campaign-performance`
- Returns all campaigns with metrics and identifies the best performer

**Response Example:**
```json
{
  "campaigns": [
    {
      "name": "Campaign A",
      "impressions": 1000,
      "clicks": 100,
      "conversions": 10,
      "ctr": 10.0,
      "conversion_rate": 10.0
    }
  ],
  "best_campaign": {...}
}
```

#### Customer Segments
- **GET** `/api/segments`
- Segments campaigns by performance level

**Response Example:**
```json
[
  {
    "name": "Campaign C",
    "impressions": 2000,
    "clicks": 250,
    "conversions": 30,
    "ctr": 12.5,
    "conversion_rate": 12.0,
    "segment": "High Performer"
  }
]
```

#### Offer Effectiveness
- **GET** `/api/offer-effectiveness`
- Analyzes offer performance with drop-off rates

**Response Example:**
```json
{
  "campaigns": [...],
  "best_offer": {...},
  "worst_offer": {...}
}
```

### CRUD Endpoints

#### Create Campaign
- **POST** `/api/campaigns`
- **Body:**
```json
{
  "name": "New Campaign",
  "impressions": 5000,
  "clicks": 400,
  "conversions": 50
}
```

#### Get All Campaigns
- **GET** `/api/campaigns`
- Returns all campaigns with calculated metrics

#### Get Single Campaign
- **GET** `/api/campaigns/{campaign_id}`
- Returns a specific campaign by ID

#### Update Campaign
- **PUT** `/api/campaigns/{campaign_id}`
- **Body:** (all fields optional)
```json
{
  "name": "Updated Name",
  "impressions": 6000,
  "clicks": 500,
  "conversions": 60
}
```

#### Delete Campaign
- **DELETE** `/api/campaigns/{campaign_id}`
- Deletes a campaign by ID

## 🗂️ Project Structure

```
offersense-marketing-analytics-backend/
├── app/
│   ├── main.py                      # FastAPI application entry point
│   ├── database/
│   │   ├── db.py                    # Database connection handler
│   │   ├── init_db.py              # Database initialization script
│   │   └── schema.sql              # Database schema
│   ├── models/
│   │   └── models.py               # Pydantic models for validation
│   ├── routes/
│   │   └── campaign_routes.py      # API route definitions
│   ├── services/
│   │   ├── campaign_analysis.py    # Campaign analysis logic
│   │   ├── kpi_service.py          # KPI calculations
│   │   ├── segmentation_service.py # Customer segmentation
│   │   └── crud_service.py         # CRUD operations
│   └── utils/
│       └── helpers.py              # Utility functions
├── notebooks/
│   └── eda.ipynb                   # Exploratory data analysis
├── tests/
│   └── test_kpis.py               # Unit tests
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## 🧪 Running Tests

```bash
python -m unittest tests.test_kpis
```

Or run with verbose output:
```bash
python -m unittest tests.test_kpis -v
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
