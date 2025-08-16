from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any
from datetime import date
import math

# Import the quarter calculation function from drawdowns module
from ..api.drawdowns import calculate_quarter_string

class UnitCalculationEngine:
    """
    Service for calculating unit allocations, management fees, and stamp duties
    based on the specifications in UC-LP-3.
    """
    
    # Constants
    GST_RATE = Decimal('0.18')  # 18% GST
    
    def calculate_units(self, drawdown_amount: Decimal, nav_value: int) -> int:
        """
        Calculate allocated units based on drawdown amount and NAV.
        Formula: Units = Drawdown Amount ÷ NAV
        
        Args:
            drawdown_amount: The amount drawn down by the LP
            nav_value: Net Asset Value per unit (typically 100)
            
        Returns:
            int: Number of units allocated (rounded down to nearest integer)
        """
        if nav_value <= 0:
            raise ValueError("NAV value must be greater than 0")
        
        if drawdown_amount <= 0:
            raise ValueError("Drawdown amount must be greater than 0")
        
        units = drawdown_amount / Decimal(nav_value)
        return units 
    
    def calculate_management_fees(self, commitment_amount: Decimal, mgmt_fee_rate: Decimal) -> Decimal:
        """
        Calculate management fees including GST.
        Formula: Management Fees = Commitment Amount × Management Fee Rate × (1 + GST Rate)
        
        Args:
            commitment_amount: Total commitment amount of the LP
            mgmt_fee_rate: Management fee rate (typically 0.01 for 1%)
            
        Returns:
            Decimal: Management fees including GST, rounded to 2 decimal places
        """
        if commitment_amount <= 0:
            raise ValueError("Commitment amount must be greater than 0")
        
        if mgmt_fee_rate < 0:
            raise ValueError("Management fee rate cannot be negative")
        
        base_fees = commitment_amount * mgmt_fee_rate
        total_fees_with_gst = base_fees * (Decimal('1') + self.GST_RATE)
        
        return total_fees_with_gst.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_stamp_duty(self, drawdown_amount: Decimal, stamp_duty_rate: Decimal) -> Decimal:
        """
        Calculate stamp duty based on drawdown amount and rate from fund details.
        Formula: Stamp Duty = Drawdown Amount × Stamp Duty Rate
        
        Args:
            drawdown_amount: The amount drawn down by the LP
            stamp_duty_rate: Stamp duty rate from fund details (typically 0.00005 for 0.005%)
            
        Returns:
            Decimal: Stamp duty amount, rounded to 2 decimal places
        """
        if drawdown_amount <= 0:
            raise ValueError("Drawdown amount must be greater than 0")
        
        if stamp_duty_rate < 0:
            raise ValueError("Stamp duty rate cannot be negative")
        
        stamp_duty = drawdown_amount * stamp_duty_rate
        return stamp_duty.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def calculate_drawdown_quarter(self, drawdown_date: date) -> str:
        """
        Calculate the drawdown quarter based on the drawdown date.
        Reuses the function from drawdowns API module.
        
        Args:
            drawdown_date: The date of the drawdown
            
        Returns:
            str: Formatted quarter string (e.g., "Q1'25")
        """
        return calculate_quarter_string(drawdown_date)
    
    def validate_calculation_inputs(self, calculation_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Validate all input data for unit allocation calculations.
        
        Args:
            calculation_data: Dictionary containing all calculation inputs
            
        Returns:
            Dict[str, str]: Dictionary of validation errors (empty if all valid)
        """
        errors = {}
        
        # Required fields validation
        required_fields = [
            'drawdown_amount', 'nav_value', 'commitment_amount', 
            'mgmt_fee_rate', 'stamp_duty_rate', 'drawdown_date'
        ]
        
        for field in required_fields:
            if field not in calculation_data or calculation_data[field] is None:
                errors[field] = f"{field} is required"
        
        # Numeric validations
        if 'drawdown_amount' in calculation_data:
            try:
                amount = Decimal(str(calculation_data['drawdown_amount']))
                if amount <= 0:
                    errors['drawdown_amount'] = "Drawdown amount must be greater than 0"
            except (ValueError, TypeError):
                errors['drawdown_amount'] = "Drawdown amount must be a valid number"
        
        if 'nav_value' in calculation_data:
            try:
                nav = int(calculation_data['nav_value'])
                if nav <= 0:
                    errors['nav_value'] = "NAV value must be greater than 0"
            except (ValueError, TypeError):
                errors['nav_value'] = "NAV value must be a valid integer"
        
        if 'commitment_amount' in calculation_data:
            try:
                commitment = Decimal(str(calculation_data['commitment_amount']))
                if commitment <= 0:
                    errors['commitment_amount'] = "Commitment amount must be greater than 0"
            except (ValueError, TypeError):
                errors['commitment_amount'] = "Commitment amount must be a valid number"
        
        if 'mgmt_fee_rate' in calculation_data:
            try:
                rate = Decimal(str(calculation_data['mgmt_fee_rate']))
                if rate < 0:
                    errors['mgmt_fee_rate'] = "Management fee rate cannot be negative"
                if rate > 1:
                    errors['mgmt_fee_rate'] = "Management fee rate cannot exceed 100%"
            except (ValueError, TypeError):
                errors['mgmt_fee_rate'] = "Management fee rate must be a valid number"
        
        if 'stamp_duty_rate' in calculation_data:
            try:
                rate = Decimal(str(calculation_data['stamp_duty_rate']))
                if rate < 0:
                    errors['stamp_duty_rate'] = "Stamp duty rate cannot be negative"
                if rate > 1:
                    errors['stamp_duty_rate'] = "Stamp duty rate cannot exceed 100%"
            except (ValueError, TypeError):
                errors['stamp_duty_rate'] = "Stamp duty rate must be a valid number"
        
        return errors
    
    def calculate_all_for_drawdown(self, 
                                   drawdown_amount: Decimal,
                                   nav_value: int,
                                   commitment_amount: Decimal,
                                   mgmt_fee_rate: Decimal,
                                   stamp_duty_rate: Decimal,
                                   drawdown_date: date) -> Dict[str, Any]:
        """
        Calculate all values for a single drawdown in one operation.
        
        Args:
            drawdown_amount: The amount drawn down by the LP
            nav_value: Net Asset Value per unit (integer, typically 100)
            commitment_amount: Total commitment amount of the LP
            mgmt_fee_rate: Management fee rate
            stamp_duty_rate: Stamp duty rate from fund details
            drawdown_date: Date of the drawdown
            
        Returns:
            Dict[str, Any]: Dictionary containing all calculated values
        """
        # Validate inputs
        calculation_data = {
            'drawdown_amount': drawdown_amount,
            'nav_value': nav_value,
            'commitment_amount': commitment_amount,
            'mgmt_fee_rate': mgmt_fee_rate,
            'stamp_duty_rate': stamp_duty_rate,
            'drawdown_date': drawdown_date
        }
        
        validation_errors = self.validate_calculation_inputs(calculation_data)
        if validation_errors:
            raise ValueError(f"Validation errors: {validation_errors}")
        
        # Perform calculations
        units = self.calculate_units(drawdown_amount, nav_value)
        mgmt_fees = self.calculate_management_fees(commitment_amount, mgmt_fee_rate)
        stamp_duty = self.calculate_stamp_duty(drawdown_amount, stamp_duty_rate)
        quarter = self.calculate_drawdown_quarter(drawdown_date)
        
        return {
            'allotted_units': units,
            'mgmt_fees': mgmt_fees,
            'stamp_duty': stamp_duty,
            'drawdown_quarter': quarter,
            'nav_value': nav_value,
            'drawdown_amount': drawdown_amount,
            'committed_amt': commitment_amount,
            'amt_accepted': drawdown_amount  # Assuming full acceptance for now
        }