"""
Tests for biometric data requirements and automatic recalculation

This test file validates the implementation following DEVELOPMENT_GUIDELINES.md requirements:
- Biometric fields are now required
- Automatic recalculation when any biometric field is updated
- Proper error handling and validation
"""
import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from app.schemas.user import UserBiometricsUpdate, Gender, ActivityLevel
from app.services.biometric_service import BiometricService
from app.services.user_service import UserService
from app.core.custom_exceptions import BiometricValidationError
from app.constants import BiometricConstants


class TestBiometricRequirements:
    """Test biometric data requirements and calculations"""
    
    def setup_method(self):
        """Setup test data"""
        self.mock_db = Mock()
        self.biometric_service = BiometricService()
        self.user_service = UserService(self.mock_db)
        
        # Sample user data
        self.complete_user_data = {
            'id': 1,
            'email': 'test@example.com',
            'age': 30,
            'gender': 'male',
            'weight': 75.0,
            'height': 180.0,
            'activity_level': 1.50,
            'bmr': 1800.0,
            'daily_caloric_expenditure': 2700.0
        }
    
    def test_calculate_bmr_with_constants(self):
        """Test that BMR calculation uses constants instead of magic numbers"""
        weight = 70.0
        height = 175.0
        age = 30
        gender = Gender.MALE
        
        bmr = self.biometric_service.calculate_bmr(weight, height, age, gender)
        
        # Verify calculation uses constants
        expected = (
            BiometricConstants.WEIGHT_MULTIPLIER * weight +
            BiometricConstants.HEIGHT_MULTIPLIER * height -
            BiometricConstants.AGE_MULTIPLIER * age +
            BiometricConstants.MALE_ADJUSTMENT
        )
        
        assert bmr == expected
        assert bmr == 1648.75  # Expected value for male with updated calculation
    
    def test_calculate_bmr_female(self):
        """Test BMR calculation for female"""
        weight = 60.0
        height = 165.0
        age = 25
        gender = Gender.FEMALE
        
        bmr = self.biometric_service.calculate_bmr(weight, height, age, gender)
        
        expected = (
            BiometricConstants.WEIGHT_MULTIPLIER * weight +
            BiometricConstants.HEIGHT_MULTIPLIER * height -
            BiometricConstants.AGE_MULTIPLIER * age +
            BiometricConstants.FEMALE_ADJUSTMENT
        )
        
        assert bmr == expected
        assert bmr == 1345.25  # Expected value for female with updated calculation
    
    def test_calculate_user_metrics_required_fields(self):
        """Test that calculate_user_metrics works with required fields"""
        weight = 75.0
        height = 180.0
        age = 30
        gender = Gender.MALE
        activity_level = ActivityLevel.MODERATELY_ACTIVE
        
        bmr, daily_expenditure = self.biometric_service.calculate_user_metrics(
            weight=weight,
            height=height,
            age=age,
            gender=gender,
            activity_level=activity_level
        )
        
        assert bmr is not None
        assert daily_expenditure is not None
        assert daily_expenditure == bmr * activity_level.value
        assert isinstance(bmr, float)
        assert isinstance(daily_expenditure, float)
    
    def test_biometric_validation_valid_data(self):
        """Test validation with valid biometric data"""
        # Should not raise exception
        self.biometric_service.validate_biometric_data(
            weight=70.0,
            height=175.0,
            age=30,
            gender=Gender.MALE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE
        )
    
    def test_biometric_validation_invalid_weight(self):
        """Test validation with invalid weight"""
        with pytest.raises(BiometricValidationError) as exc_info:
            self.biometric_service.validate_biometric_data(
                weight=500.0,  # Too high
                height=175.0,
                age=30,
                gender=Gender.MALE,
                activity_level=ActivityLevel.MODERATELY_ACTIVE
            )
        
        assert "weight" in exc_info.value.errors
    
    def test_biometric_validation_invalid_height(self):
        """Test validation with invalid height"""
        with pytest.raises(BiometricValidationError) as exc_info:
            self.biometric_service.validate_biometric_data(
                weight=70.0,
                height=50.0,  # Too low
                age=30,
                gender=Gender.MALE,
                activity_level=ActivityLevel.MODERATELY_ACTIVE
            )
        
        assert "height" in exc_info.value.errors
    
    def test_biometric_validation_invalid_age(self):
        """Test validation with invalid age"""
        with pytest.raises(BiometricValidationError) as exc_info:
            self.biometric_service.validate_biometric_data(
                weight=70.0,
                height=175.0,
                age=150,  # Too high
                gender=Gender.MALE,
                activity_level=ActivityLevel.MODERATELY_ACTIVE
            )
        
        assert "age" in exc_info.value.errors
    
    def test_has_complete_biometric_data_complete(self):
        """Test has_complete_biometric_data with complete data"""
        result = self.biometric_service.has_complete_biometric_data(
            weight=70.0,
            height=175.0,
            age=30,
            gender=Gender.MALE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE
        )
        
        assert result is True
    
    def test_has_complete_biometric_data_incomplete(self):
        """Test has_complete_biometric_data with missing data"""
        result = self.biometric_service.has_complete_biometric_data(
            weight=70.0,
            height=175.0,
            age=None,  # Missing age
            gender=Gender.MALE,
            activity_level=ActivityLevel.MODERATELY_ACTIVE
        )
        
        assert result is False
    
    def test_update_user_biometrics_with_recalculation(self):
        """Test automatic recalculation when updating biometric data"""
        # Mock user
        mock_user = Mock()
        mock_user.weight = 70.0
        mock_user.height = 175.0
        mock_user.age = 30
        mock_user.gender = 'male'
        mock_user.activity_level = 1.35
        
        # Test updating weight - should trigger recalculation
        new_bmr, new_daily_expenditure = self.biometric_service.update_user_biometrics_with_recalculation(
            current_user=mock_user,
            weight=75.0  # Updated weight
        )
        
        assert new_bmr is not None
        assert new_daily_expenditure is not None
        assert new_bmr != mock_user.weight * 10  # Should be different due to new weight
    
    @patch('app.services.user_service.BiometricService')
    def test_user_service_update_biometrics_calls_recalculation(self, mock_biometric_service):
        """Test that UserService calls recalculation when updating biometrics"""
        # Setup mocks
        mock_user = Mock()
        mock_user.weight = 70.0
        mock_user.height = 175.0
        mock_user.age = 30
        mock_user.gender = 'male'
        mock_user.activity_level = 1.35
        
        mock_biometric_service.update_user_biometrics_with_recalculation.return_value = (1800.0, 2430.0)
        
        # Create update data
        biometric_update = UserBiometricsUpdate(weight=75.0)
        
        # Call update method
        self.user_service.update_user_biometrics(mock_user, biometric_update)
        
        # Verify recalculation was called
        mock_biometric_service.update_user_biometrics_with_recalculation.assert_called_once()
        
        # Verify user values were updated
        assert mock_user.weight == 75.0
        assert mock_user.bmr == 1800.0
        assert mock_user.daily_caloric_expenditure == 2430.0


class TestBiometricAPIEndpoints:
    """Test API endpoints for biometric updates"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from app.main import app
        return TestClient(app)
    
    def test_biometric_update_endpoint_exists(self, client):
        """Test that biometric update endpoint exists"""
        # This would need proper authentication setup in real test
        # For now, just verify the endpoint is registered
        response = client.put("/users/me/biometrics", json={
            "weight": 75.0
        })
        
        # Should get 401 (unauthorized) not 404 (not found)
        assert response.status_code != 404
    
    def test_recalculate_endpoint_exists(self, client):
        """Test that recalculation endpoint exists"""
        response = client.post("/users/me/recalculate")
        
        # Should get 401 (unauthorized) not 404 (not found)
        assert response.status_code != 404


class TestBiometricSchemas:
    """Test biometric schemas validation"""
    
    def test_user_biometrics_update_schema(self):
        """Test UserBiometricsUpdate schema validation"""
        # Valid data
        valid_data = {
            "weight": 75.0,
            "height": 180.0,
            "age": 30,
            "gender": "male",
            "activity_level": 1.50
        }
        
        update = UserBiometricsUpdate(**valid_data)
        assert update.weight == 75.0
        assert update.gender == Gender.MALE
        assert update.activity_level == ActivityLevel.MODERATELY_ACTIVE
    
    def test_user_biometrics_update_partial(self):
        """Test UserBiometricsUpdate with partial data"""
        # Only updating weight
        partial_data = {
            "weight": 80.0
        }
        
        update = UserBiometricsUpdate(**partial_data)
        assert update.weight == 80.0
        assert update.height is None
        assert update.age is None
    
    def test_user_biometrics_update_validation_errors(self):
        """Test validation errors in UserBiometricsUpdate"""
        # Invalid weight
        with pytest.raises(ValueError):
            UserBiometricsUpdate(weight=500.0)  # Too high
        
        # Invalid height
        with pytest.raises(ValueError):
            UserBiometricsUpdate(height=50.0)  # Too low
        
        # Invalid age
        with pytest.raises(ValueError):
            UserBiometricsUpdate(age=150)  # Too high


if __name__ == "__main__":
    pytest.main([__file__, "-v"])