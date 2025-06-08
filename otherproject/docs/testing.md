# Testing Strategy

## Overview

Comprehensive testing approach ensuring reliability, security, and performance of the Digital Rental Contract Management System.

## Testing Principles

### Quality Standards
- **Code Coverage**: Minimum 80% line coverage, target 90%
- **Test Isolation**: Each test runs independently with clean state
- **Real Data Usage**: Prefer production-like data over synthetic data
- **Fast Feedback**: Unit tests complete in <5 minutes, integration tests in <15 minutes
- **Documentation**: Every test clearly documents its purpose and expected behavior

### Testing Pyramid
```
    /\
   /  \     E2E Tests (10%)
  /____\    Integration Tests (20%)
 /_______\   Unit Tests (70%)
```

## Test Categories

### Unit Testing

#### Scope and Coverage
- **Business Logic**: Core contract validation, calculation logic
- **Data Models**: Pydantic model validation and serialization
- **Utilities**: Authentication, password hashing, PDF generation
- **API Endpoints**: Request/response handling and validation

#### Test Structure
```python
# test_contract_service.py
import pytest
from datetime import date
from core.contracts.contract_service import ContractService
from core.contracts.contract_models import ContractDraftCreate

class TestContractService:
    def test_create_contract_valid_data(self, db_session, sample_user):
        """Test contract creation with valid data."""
        service = ContractService(db_session)
        contract_data = ContractDraftCreate(
            tenant_id=1,
            user_id=sample_user.id,
            mieter1_vorname="Max",
            mieter1_nachname="Mustermann",
            mieter1_geburtstag=date(1990, 1, 1),
            mieter1_email="max@example.com",
            mieter1_telefon="+49123456789",
            liegenschaft="Test Property",
            lage="Test Location",
            mietbeginn=date(2024, 1, 1),
            kaltmiete=800.0,
            betriebskosten=150.0,
            heizkosten=100.0,
            kaution=2400.0,
            empfaenger_name="Test Recipient",
            empfaenger_email="recipient@example.com",
            versand_kanal="email",
            signatur_kanal="email"
        )
        
        contract = service.create_contract(contract_data)
        
        assert contract.id is not None
        assert contract.status == "Entwurf"
        assert contract.mieter1_email == "max@example.com"
        assert contract.kaltmiete == 800.0

    def test_create_contract_invalid_email(self, db_session, sample_user):
        """Test contract creation fails with invalid email."""
        service = ContractService(db_session)
        
        with pytest.raises(ValidationError) as exc_info:
            ContractDraftCreate(
                # ... other valid fields ...
                mieter1_email="invalid-email"
            )
        
        assert "email" in str(exc_info.value)
```

#### Fixtures and Test Data
```python
# conftest.py
@pytest.fixture
def db_session():
    """Create test database session with transaction rollback."""
    from db.database import SessionLocal, engine
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    from db.models.user_profile import UserProfile
    user = UserProfile(
        tenant_id=1,
        email="test@example.com",
        name="Test User",
        password_hash="$2b$12$test_hash",
        role="user"
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def sample_tenant(db_session):
    """Create a sample tenant for testing."""
    from db.models.tenant_profile import TenantProfile
    tenant = TenantProfile(
        tenant_name="Test Tenant",
        street="Test Street 1",
        postal_code="12345",
        city="Test City",
        phone="+49123456789",
        email="tenant@example.com",
        default_signature_channel="email"
    )
    db_session.add(tenant)
    db_session.commit()
    return tenant
```

### Integration Testing

#### Database Integration Tests
```python
# test_database_integration.py
class TestDatabaseIntegration:
    def test_contract_creation_with_relationships(self, db_session):
        """Test contract creation with proper foreign key relationships."""
        # Create tenant
        tenant = TenantProfile(...)
        db_session.add(tenant)
        db_session.flush()
        
        # Create user
        user = UserProfile(tenant_id=tenant.id, ...)
        db_session.add(user)
        db_session.flush()
        
        # Create contract
        contract = ContractDraft(
            tenant_id=tenant.id,
            user_id=user.id,
            ...
        )
        db_session.add(contract)
        db_session.commit()
        
        # Verify relationships
        assert contract.tenant_id == tenant.id
        assert contract.user_id == user.id
        
        # Test cascade operations
        db_session.delete(tenant)
        db_session.commit()
        
        # Verify contract is not orphaned (if cascade delete is configured)
        remaining_contract = db_session.query(ContractDraft).filter_by(id=contract.id).first()
        assert remaining_contract is None
```

#### API Integration Tests
```python
# test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAPIIntegration:
    def test_contract_creation_workflow(self, authenticated_headers):
        """Test complete contract creation workflow via API."""
        # Create contract
        contract_data = {
            "mieter1_vorname": "Max",
            "mieter1_nachname": "Mustermann",
            # ... other required fields ...
        }
        
        response = client.post(
            "/api/v1/contracts",
            json=contract_data,
            headers=authenticated_headers
        )
        assert response.status_code == 201
        contract_id = response.json()["id"]
        
        # Retrieve contract
        response = client.get(
            f"/api/v1/contracts/{contract_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "Entwurf"
        
        # Update contract
        update_data = {"kaltmiete": 850.0}
        response = client.put(
            f"/api/v1/contracts/{contract_id}",
            json=update_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["kaltmiete"] == 850.0
```

#### External Service Integration Tests
```python
# test_esignatures_integration.py
import pytest
from unittest.mock import patch, Mock
from core.documents.esignatures_client import ESignaturesClient

class TestESignaturesIntegration:
    @patch('requests.post')
    def test_send_for_signature_success(self, mock_post):
        """Test successful signature request to eSignatures.com."""
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "esig_12345",
            "status": "sent",
            "recipients": [{"email": "test@example.com", "status": "pending"}]
        }
        mock_post.return_value = mock_response
        
        client = ESignaturesClient(api_key="test_key", sandbox=True)
        
        result = client.send_for_signature(
            document_data=b"PDF_CONTENT",
            recipients=["test@example.com"],
            title="Test Contract"
        )
        
        assert result["id"] == "esig_12345"
        assert result["status"] == "sent"
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_for_signature_retry_logic(self, mock_post):
        """Test retry logic on API failures."""
        # Mock failing responses followed by success
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503
        mock_response_fail.raise_for_status.side_effect = requests.HTTPError()
        
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"id": "esig_12345"}
        
        mock_post.side_effect = [
            requests.exceptions.RequestException(),  # First attempt fails
            requests.exceptions.RequestException(),  # Second attempt fails
            mock_response_success  # Third attempt succeeds
        ]
        
        client = ESignaturesClient(api_key="test_key", sandbox=True)
        
        result = client.send_for_signature(
            document_data=b"PDF_CONTENT",
            recipients=["test@example.com"],
            title="Test Contract"
        )
        
        assert result["id"] == "esig_12345"
        assert mock_post.call_count == 3
```

### End-to-End Testing

#### User Workflow Tests
```python
# test_e2e_workflows.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestE2EWorkflows:
    @pytest.fixture(scope="class")
    def browser(self):
        """Setup browser for E2E tests."""
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def test_complete_contract_creation_workflow(self, browser):
        """Test complete contract creation from login to PDF generation."""
        # Login
        browser.get("http://localhost:8501")
        
        email_input = browser.find_element(By.NAME, "email")
        password_input = browser.find_element(By.NAME, "password")
        
        email_input.send_keys("test@example.com")
        password_input.send_keys("test_password")
        
        login_button = browser.find_element(By.TEXT, "Login")
        login_button.click()
        
        # Wait for dashboard
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TEXT, "Dashboard"))
        )
        
        # Navigate to contract creation
        create_button = browser.find_element(By.TEXT, "Neuen Vertrag erstellen")
        create_button.click()
        
        # Fill contract form
        browser.find_element(By.NAME, "mieter1_vorname").send_keys("Max")
        browser.find_element(By.NAME, "mieter1_nachname").send_keys("Mustermann")
        # ... fill other required fields ...
        
        # Submit form
        submit_button = browser.find_element(By.TEXT, "Vertrag erstellen")
        submit_button.click()
        
        # Verify success
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TEXT, "Vertrag erfolgreich erstellt"))
        )
        
        # Verify PDF generation
        pdf_button = browser.find_element(By.TEXT, "PDF herunterladen")
        assert pdf_button.is_enabled()
```

### Performance Testing

#### Load Testing with Locust
```python
# locustfile.py
from locust import HttpUser, task, between

class ContractUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tests."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "test_password"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)
    def view_contracts(self):
        """Test contract listing performance."""
        self.client.get("/api/v1/contracts", headers=self.headers)

    @task(1)
    def create_contract(self):
        """Test contract creation performance."""
        contract_data = {
            "mieter1_vorname": "Test",
            "mieter1_nachname": "User",
            "mieter1_geburtstag": "1990-01-01",
            "mieter1_email": "test@example.com",
            "mieter1_telefon": "+49123456789",
            "liegenschaft": "Test Property",
            "lage": "Test Location",
            "mietbeginn": "2024-01-01",
            "kaltmiete": 800.0,
            "betriebskosten": 150.0,
            "heizkosten": 100.0,
            "kaution": 2400.0,
            "empfaenger_name": "Test Recipient",
            "empfaenger_email": "recipient@example.com",
            "versand_kanal": "email",
            "signatur_kanal": "email"
        }
        
        self.client.post("/api/v1/contracts", json=contract_data, headers=self.headers)

# Run with: locust -f locustfile.py --host=http://localhost:8000
```

### Security Testing

#### Authentication and Authorization Tests
```python
# test_security.py
class TestSecurity:
    def test_unauthorized_access_denied(self):
        """Test that unauthorized requests are denied."""
        response = client.get("/api/v1/contracts")
        assert response.status_code == 401
        assert "authentication required" in response.json()["error"]["message"].lower()

    def test_role_based_access_control(self, user_headers, admin_headers):
        """Test RBAC enforcement."""
        # Regular user cannot access admin endpoints
        response = client.get("/api/v1/admin/tenants", headers=user_headers)
        assert response.status_code == 403
        
        # Admin can access admin endpoints
        response = client.get("/api/v1/admin/tenants", headers=admin_headers)
        assert response.status_code == 200

    def test_tenant_isolation(self, tenant1_user_headers, tenant2_user_headers):
        """Test that users can only access their tenant's data."""
        # Create contract as tenant1 user
        contract_data = {...}
        response = client.post("/api/v1/contracts", json=contract_data, headers=tenant1_user_headers)
        contract_id = response.json()["id"]
        
        # Tenant2 user cannot access tenant1's contract
        response = client.get(f"/api/v1/contracts/{contract_id}", headers=tenant2_user_headers)
        assert response.status_code == 404

    def test_sql_injection_prevention(self):
        """Test SQL injection attack prevention."""
        malicious_input = "'; DROP TABLE contract_draft; --"
        response = client.get(f"/api/v1/contracts?search={malicious_input}")
        # Should not cause server error, should be safely handled
        assert response.status_code in [200, 400]  # Not 500
```

## Test Data Management

### Test Database Strategy
```python
# test_data_factory.py
import factory
from factory.alchemy import SQLAlchemyModelFactory
from db.models.contract_draft import ContractDraft
from db.models.user_profile import UserProfile

class UserProfileFactory(SQLAlchemyModelFactory):
    class Meta:
        model = UserProfile
        sqlalchemy_session_persistence = "commit"

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    name = factory.Faker("name")
    password_hash = "$2b$12$test_hash"
    role = "user"
    tenant_id = 1

class ContractDraftFactory(SQLAlchemyModelFactory):
    class Meta:
        model = ContractDraft
        sqlalchemy_session_persistence = "commit"

    mieter1_vorname = factory.Faker("first_name")
    mieter1_nachname = factory.Faker("last_name")
    mieter1_geburtstag = factory.Faker("date_of_birth", minimum_age=18, maximum_age=80)
    mieter1_email = factory.Faker("email")
    mieter1_telefon = factory.Faker("phone_number")
    liegenschaft = factory.Faker("address")
    lage = factory.Faker("address")
    mietbeginn = factory.Faker("future_date")
    kaltmiete = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    betriebskosten = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    heizkosten = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    kaution = factory.LazyAttribute(lambda obj: obj.kaltmiete * 3)
    empfaenger_name = factory.Faker("company")
    empfaenger_email = factory.Faker("email")
    versand_kanal = "email"
    signatur_kanal = "email"
    tenant_id = 1
    user_id = factory.SubFactory(UserProfileFactory)
```

### Mock Strategy for External Services
```python
# test_mocks.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_esignatures_client():
    """Mock eSignatures.com client for testing."""
    with patch('core.documents.esignatures_client.ESignaturesClient') as mock:
        mock_instance = Mock()
        mock_instance.send_for_signature.return_value = {
            "id": "esig_test_12345",
            "status": "sent",
            "recipients": [{"email": "test@example.com", "status": "pending"}]
        }
        mock_instance.get_signature_status.return_value = {
            "id": "esig_test_12345",
            "status": "completed",
            "completed_at": "2024-01-01T12:00:00Z"
        }
        mock.return_value = mock_instance
        yield mock_instance
```

## Test Execution

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=api --cov=ui --cov-report=html

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
pytest tests/e2e/              # End-to-end tests only

# Run tests in parallel
pytest -n auto                 # Auto-detect CPU cores

# Run with verbose output
pytest -v                      # Verbose mode
pytest -s                      # Don't capture output
```

### Continuous Integration
```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run unit tests
      run: pytest tests/unit/ --cov=core --cov-report=xml
    
    - name: Run integration tests
      run: pytest tests/integration/
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Quality Metrics

### Coverage Targets
- **Unit Tests**: 90% line coverage minimum
- **Integration Tests**: 80% feature coverage
- **E2E Tests**: 100% critical path coverage

### Performance Benchmarks
- **API Response Time**: <200ms for 95th percentile
- **PDF Generation**: <2 seconds for standard contract
- **Database Queries**: <50ms for complex queries
- **Page Load Time**: <3 seconds for initial load

### Test Maintenance
- **Test Review**: All tests reviewed during code review
- **Test Updates**: Tests updated with feature changes
- **Test Cleanup**: Remove obsolete tests quarterly
- **Documentation**: Test purpose documented in docstrings
