# Property Underwriter MVP

A Streamlit-based property investment analysis tool for rental and flip analysis.

## Features

- **Rental Analysis**: Calculate NOI, cash flow, cap rate, and IRR
- **Flip Analysis**: Estimate ARV, costs, and profit margins
- **Data Integration**: Mock data provider with extensible API integrations
- **Clean Architecture**: Separated concerns for maintainability and testing

## Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

3. **Run the app**:
   ```bash
   streamlit run src/app.py
   ```

## Architecture

```
underwriter/
├─ src/
│  ├─ app.py                 # Main Streamlit application
│  ├─ core/                  # Business logic and data models
│  ├─ services/              # Data fetching and analysis services
│  ├─ ui/                    # Streamlit UI components
│  └─ utils/                 # Configuration and utilities
├─ tests/                    # Unit tests
└─ requirements.txt          # Python dependencies
```

## Data Providers

- **Mock Provider**: Deterministic test data (always available)
- **Zillow**: Property details and market value estimates
- **Rentometer**: Rental market data
- **ATTOM**: Property and tax information
- **ClosingCorp**: Closing cost estimates

## Analysis Types

### Rental Analysis
- Net Operating Income (NOI)
- Annual debt service
- Cash flow projections
- Cap rate calculations
- IRR estimates
- Target purchase price suggestions

### Flip Analysis
- After Repair Value (ARV) estimates
- Total cost calculations
- Profit margin analysis
- Suggested purchase price
- Hold time considerations

## Development

### Adding New Data Providers
1. Create provider in `src/services/providers/`
2. Implement the `PropertyDataProvider` interface
3. Add to `src/services/data_fetch.py`
4. Update configuration in `src/utils/config.py`

### Testing
```bash
pytest tests/
```

## Next Steps

- [ ] Real API integrations
- [ ] Export functionality (PDF/Excel)
- [ ] Data persistence
- [ ] User authentication
- [ ] Advanced analytics and charts
- [ ] Comps analysis
- [ ] Background task processing 