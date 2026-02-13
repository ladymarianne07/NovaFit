"""
Unit tests for fitness objective and macronutrient calculations

Tests the BiometricService methods that handle objective-based calorie and macro targets
"""
import pytest
from app.services.biometric_service import BiometricService


class TestObjectiveTargetCalculations:
    """Test suite for objective-based calorie and macro calculations"""
    
    def test_calculate_objective_targets_maintenance(self):
        """Test maintenance objective uses TDEE without modification"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='maintenance',
            aggressiveness_level=2
        )
        
        assert targets['target_calories'] == 2500  # No delta
        assert targets['protein_g'] == 128  # 1.6 g/kg * 80 kg
        assert targets['fat_g'] == 83  # 30% of calories
        # Carbs = (2500 - (128*4) - (83*9)) / 4 = (2500 - 512 - 747) / 4 = 1241 / 4 = 310g
        assert targets['carbs_g'] == 310  # Remainder
    
    def test_calculate_objective_targets_fat_loss_default(self):
        """Test fat loss objective with moderate (default) aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='fat_loss',
            aggressiveness_level=2  # Default moderate
        )
        
        # 20% deficit: TDEE * (1 - 0.20) = 2000 kcal
        assert targets['target_calories'] == 2000
        assert targets['protein_g'] == 160  # 2.0 g/kg * 80 kg
        # Remaining calculation
        assert targets['fat_g'] > 0
        assert targets['carbs_g'] > 0
    
    def test_calculate_objective_targets_fat_loss_conservative(self):
        """Test fat loss with conservative aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='fat_loss',
            aggressiveness_level=1  # Conservative
        )
        
        # 15% deficit
        assert targets['target_calories'] == 2125  # 2500 * 0.85
        assert targets['protein_g'] == 160
    
    def test_calculate_objective_targets_fat_loss_aggressive(self):
        """Test fat loss with aggressive aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='fat_loss',
            aggressiveness_level=3  # Aggressive
        )
        
        # 25% deficit
        assert targets['target_calories'] == 1875  # 2500 * 0.75
        assert targets['protein_g'] == 160
    
    def test_calculate_objective_targets_muscle_gain_default(self):
        """Test muscle gain with moderate aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='muscle_gain',
            aggressiveness_level=2  # Default
        )
        
        # 10% surplus
        assert targets['target_calories'] == 2750  # 2500 * 1.10
        assert targets['protein_g'] == 144  # 1.8 g/kg * 80 kg
    
    def test_calculate_objective_targets_muscle_gain_conservative(self):
        """Test muscle gain with conservative aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='muscle_gain',
            aggressiveness_level=1  # Conservative
        )
        
        # 5% surplus
        assert targets['target_calories'] == 2625  # 2500 * 1.05
        assert targets['protein_g'] == 144
    
    def test_calculate_objective_targets_muscle_gain_aggressive(self):
        """Test muscle gain with aggressive aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='muscle_gain',
            aggressiveness_level=3  # Aggressive
        )
        
        # 15% surplus
        assert targets['target_calories'] == 2875  # 2500 * 1.15
        assert targets['protein_g'] == 144
    
    def test_calculate_objective_targets_body_recomp_default(self):
        """Test body recomposition with moderate aggressiveness"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='body_recomp',
            aggressiveness_level=2  # Default
        )
        
        # 5% deficit
        assert targets['target_calories'] == 2375  # 2500 * 0.95
        assert targets['protein_g'] == 160  # 2.0 g/kg
    
    def test_calculate_objective_targets_performance(self):
        """Test performance objective maintains TDEE"""
        tdee = 2500.0
        weight = 80.0
        
        targets = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='performance',
            aggressiveness_level=2
        )
        
        assert targets['target_calories'] == 2500  # No delta
        assert targets['protein_g'] == 128  # 1.6 g/kg
    
    def test_macronutrients_sum_to_target_calories(self):
        """Verify calculated macros sum to target calories"""
        tdee = 2500.0
        weight = 75.0
        
        for objective in ['maintenance', 'fat_loss', 'muscle_gain', 'body_recomp', 'performance']:
            targets = BiometricService.calculate_objective_targets(
                tdee=tdee,
                weight_kg=weight,
                objective=objective,
                aggressiveness_level=2
            )
            
            # Calculate calories from macros
            calculated_cals = (
                targets['protein_g'] * 4 +
                targets['fat_g'] * 9 +
                targets['carbs_g'] * 4
            )
            
            # Should be within 10 kcal (due to rounding)
            assert abs(calculated_cals - targets['target_calories']) <= 10, \
                f"Macros don't sum for {objective}: {calculated_cals} vs {targets['target_calories']}"
    
    def test_carbs_never_negative(self):
        """Verify carbohydrates never goes negative even with extreme parameters"""
        # Test with very high protein requirement and high fat percentage
        tdee = 1500.0  # Low tdee
        weight = 100.0  # High weight
        
        for objective in ['fat_loss', 'body_recomp']:
            targets = BiometricService.calculate_objective_targets(
                tdee=tdee,
                weight_kg=weight,
                objective=objective,
                aggressiveness_level=3  # Most aggressive
            )
            
            assert targets['carbs_g'] >= 0, f"Carbs went negative for {objective}"
            assert targets['protein_g'] > 0
            assert targets['fat_g'] > 0
    
    def test_default_aggressiveness_level(self):
        """Test that None aggressiveness_level defaults to moderate (level 2)"""
        tdee = 2500.0
        weight = 80.0
        
        targets_explicit = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='fat_loss',
            aggressiveness_level=2
        )
        
        targets_default = BiometricService.calculate_objective_targets(
            tdee=tdee,
            weight_kg=weight,
            objective='fat_loss',
            aggressiveness_level=None
        )
        
        assert targets_explicit['target_calories'] == targets_default['target_calories']
        assert targets_explicit['protein_g'] == targets_default['protein_g']
    
    def test_none_objective_returns_zero_delta(self):
        """Test that None objective returns 0 delta (maintenance-like)"""
        delta = BiometricService.get_calorie_delta_by_objective(None, 2)
        assert delta == 0.0
    
    def test_protein_factors_match_objective(self):
        """Test that protein factors are correct for each objective"""
        assert BiometricService.get_protein_factor_by_objective('fat_loss') == 2.0
        assert BiometricService.get_protein_factor_by_objective('muscle_gain') == 1.8
        assert BiometricService.get_protein_factor_by_objective('body_recomp') == 2.0
        assert BiometricService.get_protein_factor_by_objective('maintenance') == 1.6
        assert BiometricService.get_protein_factor_by_objective('performance') == 1.6
    
    def test_fat_percentages_match_objective(self):
        """Test that fat percentages are correct for each objective"""
        assert BiometricService.get_fat_percent_by_objective('maintenance') == 0.30
        assert BiometricService.get_fat_percent_by_objective('fat_loss') == 0.25
        assert BiometricService.get_fat_percent_by_objective('muscle_gain') == 0.25
        assert BiometricService.get_fat_percent_by_objective('body_recomp') == 0.25
        assert BiometricService.get_fat_percent_by_objective('performance') == 0.25


class TestObjectiveDeltas:
    """Test suite for calorie delta calculations per objective"""
    
    def test_all_deltas_by_aggressiveness(self):
        """Test all delta combinations"""
        expected_deltas = {
            'maintenance': {1: 0.0, 2: 0.0, 3: 0.0},
            'fat_loss': {1: -0.15, 2: -0.20, 3: -0.25},
            'muscle_gain': {1: 0.05, 2: 0.10, 3: 0.15},
            'body_recomp': {1: 0.0, 2: -0.05, 3: -0.10},
            'performance': {1: 0.0, 2: 0.0, 3: 0.05}
        }
        
        for objective, deltas in expected_deltas.items():
            for level, expected_delta in deltas.items():
                actual_delta = BiometricService.get_calorie_delta_by_objective(objective, level)
                assert actual_delta == expected_delta, \
                    f"Delta mismatch for {objective} level {level}: {actual_delta} vs {expected_delta}"
