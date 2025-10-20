#!/usr/bin/env python3
"""
Test script for Zillow provider integration.
Run this to test your Zillow API key and see the data returned.
"""

from src.core.models import Address
from src.services.providers.zillow import ZillowProvider
from src.utils.config import settings

def test_zillow_provider():
    """Test the Zillow provider with a sample address."""
    
    # Check if API key is configured
    if not settings.ZILLOW_API_KEY:
        print("❌ ZILLOW_API_KEY not found in environment variables")
        print("Please set your Zillow API key in .env file")
        return
    
    print(f"✅ Using Zillow API key: {settings.ZILLOW_API_KEY[:8]}...")
    
    # Create a sample address
    address = Address(
        line1="123 Main St",
        city="San Francisco", 
        state="CA",
        zip="94102"
    )
    
    print(f"🔍 Searching for property: {address.line1}, {address.city}, {address.state} {address.zip}")
    
    # Create Zillow provider and fetch data
    provider = ZillowProvider(settings.ZILLOW_API_KEY)
    
    try:
        property_data = provider.fetch(address)
        
        if property_data:
            print("✅ Successfully fetched property data from Zillow!")
            print(f"   Beds: {property_data.beds}")
            print(f"   Baths: {property_data.baths}")
            print(f"   Sq Ft: {property_data.sqft}")
            print(f"   Market Value: ${property_data.market_value_estimate:,.0f}" if property_data.market_value_estimate else "   Market Value: Not available")
            print(f"   Rent Estimate: ${property_data.rent_estimate:,.0f}" if property_data.rent_estimate else "   Rent Estimate: Not available")
            print(f"   Annual Taxes: ${property_data.annual_taxes:,.0f}" if property_data.annual_taxes else "   Annual Taxes: Not available")
            print(f"   Sources: {[s.value for s in property_data.sources]}")
            print(f"   Meta: {property_data.meta}")
        else:
            print("❌ No property data returned from Zillow")
            print("   This could mean:")
            print("   - Address not found in Zillow database")
            print("   - API key is invalid or expired")
            print("   - Rate limiting or API error")
            
    except Exception as e:
        print(f"❌ Error occurred: {e}")

if __name__ == "__main__":
    test_zillow_provider() 
