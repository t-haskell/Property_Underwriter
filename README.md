# Property Underwriter MVP

A Streamlit-based property investment analysis tool for rental and flip analysis.

https://t-haskell.github.io/Property_Underwriter/

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
   Available settings:

   | Variable | Description | Default |
   | --- | --- | --- |
   | `ZILLOW_API_KEY` | API key for Zillow/Bridge Interactive | _unset_ |
   | `ZILLOW_BASE_URL` | Base URL for the Zillow API wrapper | `https://api.bridgedataoutput.com/api/v2` |
   | `RENTOMETER_API_KEY` | API key for Rentometer | _unset_ |
   | `RENTOMETER_BASE_URL` | Base URL for Rentometer API | `https://www.rentometer.com/api/v1` |
   | `RENTOMETER_DEFAULT_BEDROOMS` | Optional default bedroom count for Rentometer queries | _unset_ |
   | `ATTOM_API_KEY` | API key for ATTOM | _unset_ |
   | `ATTOM_BASE_URL` | Base URL for ATTOM API | `https://api.gateway.attomdata.com/propertyapi/v1.0.0` |
   | `CLOSINGCORP_API_KEY` | API key for ClosingCorp | _unset_ |
   | `CLOSINGCORP_BASE_URL` | Base URL for ClosingCorp API (if provided) | _unset_ |
   | `GOOGLE_PLACES_API_KEY` | API key for Google Places Autocomplete | _unset_ |
   | `CACHE_TTL_MIN` | Cache time-to-live (minutes) | `60` |
   | `PROVIDER_TIMEOUT_SEC` | Timeout for provider HTTP requests | `10` |
   | `USE_MOCK_PROVIDER_IF_NO_KEYS` | Use mock data when no providers are configured | `true` |

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
python -m venv venv  # if you haven't created one yet
source venv/bin/activate
pip install -r requirements.txt
pytest tests/
```

### Scaffolding in-progress features

Use the helpers in `src/utils/scaffolding.py` while building new functionality that
is not ready for production. They provide consistent logging, a dedicated
`ScaffoldingIncomplete` exception, and Pytest integration that marks affected
cases as skipped instead of failed.

- Call `scaffold("Feature name")` inside branches that are still being
  implemented.
- Decorate placeholder functions with `@scaffoldable` (optionally passing a
  `feature_name`) to automatically raise the custom exception when invoked.
- The Pytest hook in `tests/conftest.py` converts any `ScaffoldingIncomplete`
  errors into skipped tests so the test report highlights unfinished work.

Remove the scaffold calls once the feature is complete.

## Continuous Integration with GitHub Actions

This repository includes an automated workflow defined in
`.github/workflows/ci.yml`. The workflow runs on every push and pull request to
the `main` branch and performs the following steps:

1. Checks out the repository code.
2. Sets up Python 3.11 on the runner.
3. Installs the dependencies listed in `requirements.txt`.
4. Executes the test suite with `pytest`.

No additional configuration is required—any push or pull request to `main` will
trigger the workflow automatically. You can monitor run results under the
**Actions** tab of the GitHub repository.

## Continuous Deployment to GitHub Pages

A complementary workflow at `.github/workflows/deploy.yml` builds the Next.js
frontend and publishes the static export to GitHub Pages whenever changes are
pushed to `main` (or when manually triggered).

To enable deployments:

1. Open **Settings → Pages** and select **GitHub Actions** as the deployment source.
2. Add a repository secret named `NEXT_PUBLIC_API_BASE_URL` that points to the
   running backend API the frontend should call.
3. (Optional) Define a repository variable `NEXT_PUBLIC_BASE_PATH` if the site
   should be served from a custom sub-path. Leave it unset to default to the
   repository name (ideal for project pages) or set it to `/` for a root/custom
   domain. The build workflow automatically trims any leading or trailing
   slashes, so values such as `underwriter`, `/underwriter/`, or `//underwriter`
   all resolve to the same final base path of `/underwriter`.

After the workflow finishes, the static assets live in the `frontend/out`
directory. You can also generate the export locally via `npm run export` in the
`frontend` folder, which produces the exact same output that GitHub Pages serves.

On every successful run the published site URL will be reported in the workflow
summary, giving you a static URL that is always up to date with the `main`
branch.

## Next Steps

- [ ] Real API integrations
- [ ] Export functionality (PDF/Excel)
- [ ] Data persistence
- [ ] User authentication
- [ ] Advanced analytics and charts
- [ ] Comps analysis
- [ ] Background task processing

