import pytest
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any
from core.models.contract import Contract, ContractStatus, SignerInfo
from core.services.contract_service import ContractService


class TestContractService:
    """Test-driven development tests for ContractService with expected input/output pairs."""
    
    def test_create_contract_with_valid_data(self):
        """Test contract creation with complete valid data."""
        # Expected input
        contract_data = {
            "tenant_id": "tenant_001",
            "created_by_user_id": 1,
            "property_address": "Musterstraße 123, 12345 Berlin",
            "rental_amount": Decimal("1200.50"),
            "deposit_amount": Decimal("3600.00"),
            "lease_start_date": date(2024, 3, 1),
            "lease_end_date": date(2026, 2, 28),
            "landlord": {
                "name": "Max Mustermann",
                "email": "max.mustermann@landlord.com",
                "phone": "+49 30 12345678"
            },
            "tenants": [
                {
                    "name": "Anna Schmidt",
                    "email": "anna.schmidt@tenant.com", 
                    "phone": "+49 30 87654321"
                },
                {
                    "name": "Peter Schmidt",
                    "email": "peter.schmidt@tenant.com",
                    "phone": "+49 30 87654322"
                }
            ],
            "additional_terms": "Haustiere erlaubt nach Absprache"
        }
        
        # Expected output
        service = ContractService()
        result = service.create_contract(contract_data)
        
        assert result.tenant_id == "tenant_001"
        assert result.property_address == "Musterstraße 123, 12345 Berlin"
        assert result.rental_amount == Decimal("1200.50")
        assert result.deposit_amount == Decimal("3600.00")
        assert result.lease_start_date == date(2024, 3, 1)
        assert result.lease_end_date == date(2026, 2, 28)
        assert result.status == ContractStatus.DRAFT
        assert len(result.signers) == 3  # 1 landlord + 2 tenants
        assert result.id > 0
        assert result.created_at is not None
    
    def test_generate_contract_pdf(self):
        """Test PDF generation from contract data."""
        # Setup: create contract
        contract_data = {
            "tenant_id": "tenant_001",
            "created_by_user_id": 1,
            "property_address": "Teststraße 456, 10115 Berlin",
            "rental_amount": Decimal("950.00"),
            "deposit_amount": Decimal("2850.00"),
            "lease_start_date": date(2024, 4, 1),
            "lease_end_date": date(2025, 3, 31),
            "landlord": {
                "name": "Maria Müller",
                "email": "maria.mueller@example.com",
                "phone": "+49 30 11111111"
            },
            "tenants": [
                {
                    "name": "Tom Weber",
                    "email": "tom.weber@example.com",
                    "phone": "+49 30 22222222"
                }
            ]
        }
        
        service = ContractService()
        contract = service.create_contract(contract_data)
        
        # Expected input
        contract_id = contract.id
        
        # Expected output - PDF bytes
        pdf_result = service.generate_pdf(contract_id)
        
        assert pdf_result is not None
        assert isinstance(pdf_result, bytes)
        assert pdf_result.startswith(b'%PDF')  # PDF file signature
        assert len(pdf_result) > 1000  # Reasonable minimum size
    
    def test_send_for_signature(self):
        """Test sending contract for eSignature."""
        # Setup contract
        contract_data = {
            "tenant_id": "tenant_001", 
            "created_by_user_id": 1,
            "property_address": "Signaturstraße 789, 20095 Hamburg",
            "rental_amount": Decimal("1500.00"),
            "deposit_amount": Decimal("4500.00"),
            "lease_start_date": date(2024, 5, 1),
            "lease_end_date": date(2026, 4, 30),
            "landlord": {
                "name": "Klaus Hansen",
                "email": "klaus.hansen@landlord.de",
                "phone": "+49 40 33333333"
            },
            "tenants": [
                {
                    "name": "Lisa Becker",
                    "email": "lisa.becker@tenant.de",
                    "phone": "+49 40 44444444"
                }
            ]
        }
        
        service = ContractService()
        contract = service.create_contract(contract_data)
        
        # Expected input
        signature_request = {
            "contract_id": contract.id,
            "send_immediately": True,
            "reminder_days": 3
        }
        
        # Expected output - signature process initiated
        signature_result = service.send_for_signature(signature_request)
        
        assert signature_result["status"] == "sent"
        assert "esignature_id" in signature_result
        assert signature_result["esignature_id"] is not None
        
        # Verify contract status updated
        updated_contract = service.get_contract(contract.id)
        assert updated_contract.status == ContractStatus.PENDING_SIGNATURE
        assert updated_contract.esignature_id is not None
    
    def test_contract_status_tracking(self):
        """Test contract status progression through workflow."""
        # Setup contract
        contract_data = {
            "tenant_id": "tenant_001",
            "created_by_user_id": 1,
            "property_address": "Statusstraße 101, 80331 München",
            "rental_amount": Decimal("1800.00"),
            "deposit_amount": Decimal("5400.00"),
            "lease_start_date": date(2024, 6, 1),
            "lease_end_date": date(2025, 5, 31),
            "landlord": {
                "name": "Andrea Wolf",
                "email": "andrea.wolf@example.com",
                "phone": "+49 89 55555555"
            },
            "tenants": [
                {
                    "name": "Michael Klein",
                    "email": "michael.klein@example.com", 
                    "phone": "+49 89 66666666"
                }
            ]
        }
        
        service = ContractService()
        contract = service.create_contract(contract_data)
        
        # Expected status progression
        status_transitions = [
            (ContractStatus.DRAFT, ContractStatus.PENDING_SIGNATURE),
            (ContractStatus.PENDING_SIGNATURE, ContractStatus.PARTIALLY_SIGNED),
            (ContractStatus.PARTIALLY_SIGNED, ContractStatus.FULLY_SIGNED),
            (ContractStatus.FULLY_SIGNED, ContractStatus.ACTIVE)
        ]
        
        for from_status, to_status in status_transitions:
            # Verify current status
            current_contract = service.get_contract(contract.id)
            assert current_contract.status == from_status
            
            # Update status
            updated_contract = service.update_contract_status(contract.id, to_status)
            assert updated_contract.status == to_status
            assert updated_contract.updated_at > current_contract.updated_at
    
    def test_search_contracts_by_criteria(self):
        """Test contract search with various filter criteria."""
        # Setup: create multiple contracts
        contracts_data = [
            {
                "tenant_id": "tenant_001",
                "created_by_user_id": 1,
                "property_address": "Suchstraße 1, 50667 Köln",
                "rental_amount": Decimal("1000.00"),
                "lease_start_date": date(2024, 1, 1),
                "lease_end_date": date(2024, 12, 31),
                "status": ContractStatus.ACTIVE,
                "landlord": {"name": "Owner A", "email": "a@test.com", "phone": "123"},
                "tenants": [{"name": "Tenant A", "email": "ta@test.com", "phone": "456"}]
            },
            {
                "tenant_id": "tenant_001", 
                "created_by_user_id": 1,
                "property_address": "Suchstraße 2, 50667 Köln",
                "rental_amount": Decimal("1200.00"),
                "lease_start_date": date(2024, 2, 1),
                "lease_end_date": date(2025, 1, 31),
                "status": ContractStatus.PENDING_SIGNATURE,
                "landlord": {"name": "Owner B", "email": "b@test.com", "phone": "789"},
                "tenants": [{"name": "Tenant B", "email": "tb@test.com", "phone": "012"}]
            },
            {
                "tenant_id": "tenant_002",
                "created_by_user_id": 2, 
                "property_address": "Anderestraße 3, 60311 Frankfurt",
                "rental_amount": Decimal("1500.00"),
                "lease_start_date": date(2024, 3, 1),
                "lease_end_date": date(2025, 2, 28),
                "status": ContractStatus.ACTIVE,
                "landlord": {"name": "Owner C", "email": "c@test.com", "phone": "345"},
                "tenants": [{"name": "Tenant C", "email": "tc@test.com", "phone": "678"}]
            }
        ]
        
        service = ContractService()
        created_contracts = []
        for data in contracts_data:
            contract = service.create_contract(data)
            service.update_contract_status(contract.id, data["status"])
            created_contracts.append(contract)
        
        # Test search criteria and expected results
        search_tests = [
            {
                "criteria": {"tenant_id": "tenant_001"},
                "expected_count": 2,
                "description": "Filter by tenant"
            },
            {
                "criteria": {"status": ContractStatus.ACTIVE},
                "expected_count": 2,
                "description": "Filter by status"
            },
            {
                "criteria": {"city": "Köln"},
                "expected_count": 2,
                "description": "Filter by city"
            },
            {
                "criteria": {
                    "tenant_id": "tenant_001",
                    "status": ContractStatus.ACTIVE
                },
                "expected_count": 1,
                "description": "Multiple filters"
            },
            {
                "criteria": {"rental_amount_min": Decimal("1100.00")},
                "expected_count": 2,
                "description": "Rental amount filter"
            }
        ]
        
        for test in search_tests:
            results = service.search_contracts(test["criteria"])
            assert len(results) == test["expected_count"], (
                f"Search test failed: {test['description']} - "
                f"Expected {test['expected_count']}, got {len(results)}"
            )
    
    def test_contract_validation_rules(self):
        """Test business rule validation for contracts."""
        service = ContractService()
        
        # Test invalid data scenarios and expected validation errors
        invalid_data_tests = [
            {
                "data": {
                    "tenant_id": "",  # Empty tenant_id
                    "property_address": "Test Address",
                    "rental_amount": Decimal("1000.00"),
                    "lease_start_date": date(2024, 1, 1),
                    "lease_end_date": date(2023, 12, 31),  # End before start
                    "landlord": {"name": "Test", "email": "test@test.com", "phone": "123"},
                    "tenants": []  # No tenants
                },
                "expected_errors": ["tenant_id", "lease_dates", "tenants"]
            },
            {
                "data": {
                    "tenant_id": "tenant_001",
                    "property_address": "",  # Empty address
                    "rental_amount": Decimal("-100.00"),  # Negative amount
                    "lease_start_date": date(2024, 1, 1),
                    "lease_end_date": date(2024, 12, 31),
                    "landlord": {"name": "", "email": "invalid", "phone": ""},  # Invalid landlord
                    "tenants": [{"name": "Test", "email": "test@test.com", "phone": "123"}]
                },
                "expected_errors": ["property_address", "rental_amount", "landlord"]
            }
        ]
        
        for test in invalid_data_tests:
            with pytest.raises(ValueError) as exc_info:
                service.create_contract(test["data"])
            
            error_message = str(exc_info.value)
            for expected_error in test["expected_errors"]:
                assert expected_error in error_message.lower()
