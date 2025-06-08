import pytest
from datetime import datetime
from typing import Dict, Any
from core.models.user import User, UserRole
from core.services.user_service import UserService


class TestUserService:
    """Test-driven development tests for UserService with expected input/output pairs."""
    
    def test_create_user_with_valid_data(self):
        """Test user creation with valid input data."""
        # Expected input
        user_data = {
            "username": "john.doe@example.com",
            "email": "john.doe@example.com", 
            "password": "SecurePass123!",
            "first_name": "John",
            "last_name": "Doe",
            "role": UserRole.USER,
            "tenant_id": "tenant_001"
        }
        
        # Expected output
        expected_user = User(
            id=1,
            username="john.doe@example.com",
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe", 
            role=UserRole.USER,
            tenant_id="tenant_001",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        service = UserService()
        result = service.create_user(user_data)
        
        assert result.username == expected_user.username
        assert result.email == expected_user.email
        assert result.role == expected_user.role
        assert result.tenant_id == expected_user.tenant_id
        assert result.is_active == True
        assert result.id > 0
    
    def test_authenticate_user_valid_credentials(self):
        """Test user authentication with correct credentials."""
        # Setup: create user first
        user_data = {
            "username": "auth.test@example.com",
            "email": "auth.test@example.com",
            "password": "ValidPass456!",
            "first_name": "Auth",
            "last_name": "Test",
            "role": UserRole.USER,
            "tenant_id": "tenant_001"
        }
        
        service = UserService()
        created_user = service.create_user(user_data)
        
        # Expected input for authentication
        auth_input = {
            "username": "auth.test@example.com",
            "password": "ValidPass456!"
        }
        
        # Expected output - successful authentication
        auth_result = service.authenticate_user(
            auth_input["username"], 
            auth_input["password"]
        )
        
        assert auth_result is not None
        assert auth_result.username == "auth.test@example.com"
        assert auth_result.is_active == True
    
    def test_authenticate_user_invalid_password(self):
        """Test authentication failure with wrong password."""
        # Setup user
        user_data = {
            "username": "fail.test@example.com",
            "email": "fail.test@example.com", 
            "password": "CorrectPass789!",
            "first_name": "Fail",
            "last_name": "Test",
            "role": UserRole.USER,
            "tenant_id": "tenant_001"
        }
        
        service = UserService()
        service.create_user(user_data)
        
        # Expected input with wrong password
        auth_input = {
            "username": "fail.test@example.com",
            "password": "WrongPassword123!"
        }
        
        # Expected output - authentication failure
        auth_result = service.authenticate_user(
            auth_input["username"],
            auth_input["password"] 
        )
        
        assert auth_result is None
    
    def test_get_users_by_tenant(self):
        """Test retrieving users filtered by tenant."""
        # Setup: create users in different tenants
        tenant_a_users = [
            {
                "username": "user1@tenant-a.com",
                "email": "user1@tenant-a.com",
                "password": "Pass123!",
                "first_name": "User",
                "last_name": "One", 
                "role": UserRole.USER,
                "tenant_id": "tenant_a"
            },
            {
                "username": "user2@tenant-a.com", 
                "email": "user2@tenant-a.com",
                "password": "Pass123!",
                "first_name": "User",
                "last_name": "Two",
                "role": UserRole.ADMIN,
                "tenant_id": "tenant_a"
            }
        ]
        
        tenant_b_user = {
            "username": "user1@tenant-b.com",
            "email": "user1@tenant-b.com", 
            "password": "Pass123!",
            "first_name": "User",
            "last_name": "Three",
            "role": UserRole.USER,
            "tenant_id": "tenant_b"
        }
        
        service = UserService()
        
        # Create users
        for user_data in tenant_a_users:
            service.create_user(user_data)
        service.create_user(tenant_b_user)
        
        # Expected input
        target_tenant = "tenant_a"
        
        # Expected output - only tenant_a users
        result = service.get_users_by_tenant(target_tenant)
        
        assert len(result) == 2
        assert all(user.tenant_id == "tenant_a" for user in result)
        assert any(user.username == "user1@tenant-a.com" for user in result)
        assert any(user.username == "user2@tenant-a.com" for user in result)
    
    def test_update_user_profile(self):
        """Test updating user profile information."""
        # Setup: create initial user
        initial_data = {
            "username": "update.test@example.com",
            "email": "update.test@example.com",
            "password": "InitialPass123!",
            "first_name": "Initial",
            "last_name": "Name",
            "role": UserRole.USER,
            "tenant_id": "tenant_001"
        }
        
        service = UserService()
        created_user = service.create_user(initial_data)
        
        # Expected input for update
        update_data = {
            "first_name": "Updated",
            "last_name": "Profile",
            "email": "updated.email@example.com"
        }
        
        # Expected output - updated user
        updated_user = service.update_user(created_user.id, update_data)
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Profile" 
        assert updated_user.email == "updated.email@example.com"
        assert updated_user.username == initial_data["username"]  # Should not change
        assert updated_user.tenant_id == initial_data["tenant_id"]  # Should not change
    
    def test_deactivate_user(self):
        """Test user deactivation."""
        # Setup user
        user_data = {
            "username": "deactivate.test@example.com",
            "email": "deactivate.test@example.com",
            "password": "DeactivatePass123!",
            "first_name": "Deactivate",
            "last_name": "Test",
            "role": UserRole.USER,
            "tenant_id": "tenant_001"
        }
        
        service = UserService()
        created_user = service.create_user(user_data)
        
        # Verify initially active
        assert created_user.is_active == True
        
        # Expected input
        user_id = created_user.id
        
        # Expected output - deactivated user
        deactivated_user = service.deactivate_user(user_id)
        
        assert deactivated_user.is_active == False
        assert deactivated_user.id == user_id
        
        # Verify authentication fails for deactivated user
        auth_result = service.authenticate_user(
            user_data["username"],
            user_data["password"]
        )
        assert auth_result is None
    
    def test_role_based_access_validation(self):
        """Test role-based access control validation."""
        # Expected input - different role combinations
        test_cases = [
            {
                "user_role": UserRole.MASTER_ADMIN,
                "required_role": UserRole.ADMIN,
                "expected_access": True
            },
            {
                "user_role": UserRole.ADMIN, 
                "required_role": UserRole.USER,
                "expected_access": True
            },
            {
                "user_role": UserRole.USER,
                "required_role": UserRole.ADMIN,
                "expected_access": False
            },
            {
                "user_role": UserRole.INTERNAL,
                "required_role": UserRole.USER,
                "expected_access": False  # Different access pattern
            }
        ]
        
        service = UserService()
        
        for case in test_cases:
            result = service.validate_role_access(
                case["user_role"],
                case["required_role"]
            )
            assert result == case["expected_access"], (
                f"Role {case['user_role']} should {'have' if case['expected_access'] else 'not have'} "
                f"access to {case['required_role']} level"
            )
