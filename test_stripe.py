#!/usr/bin/env python3
"""
Stripe API Connection Test Tool

This script tests the direct connection to the Stripe API,
allowing you to verify that your Stripe integration is working correctly.

Usage:
    python test_stripe.py [email]

    If email is not provided, it defaults to "test@example.com"
"""

import os
import sys
import json
from datetime import datetime

def test_stripe_connection(email):
    """Test connection to Stripe API for a specific email"""
    try:
        # Try to import the stripe module first
        try:
            import stripe
            print("✅ Stripe module successfully imported")
        except ImportError:
            print("❌ ERROR: Stripe module not found")
            print("Please install it with: pip install stripe")
            return False

        # Try to get API key from environment
        stripe_api_key = os.environ.get("STRIPE_API_KEY")
        if not stripe_api_key:
            try:
                # Try to get from streamlit secrets
                import streamlit as st
                stripe_api_key = st.secrets.get("stripe_api_key")
                if stripe_api_key:
                    print("✅ Found Stripe API key in Streamlit secrets")
            except:
                # If not in environment or secrets, check for a .env file
                try:
                    from dotenv import load_dotenv
                    load_dotenv()
                    stripe_api_key = os.environ.get("STRIPE_API_KEY")
                    if stripe_api_key:
                        print("✅ Found Stripe API key in .env file")
                except:
                    pass

        # Check if we have an API key now
        if not stripe_api_key:
            print("❌ ERROR: No Stripe API key found")
            print("Please set STRIPE_API_KEY in your environment or .env file")
            return False

        # Set the API key for stripe
        stripe.api_key = stripe_api_key
        print(f"✅ Set Stripe API key: {stripe_api_key[:4]}...{stripe_api_key[-4:]}")

        # Test connection by listing customers
        print(f"\nTesting connection by looking up customers with email: {email}")
        customers = stripe.Customer.list(email=email)
        print(f"✅ Successfully connected to Stripe API")
        print(f"Found {len(customers.data)} customers with that email")

        if not customers.data:
            print(f"❌ No customers found with email: {email}")
            return False

        # Get the first customer
        customer = customers.data[0]
        print(f"\nCustomer details:")
        print(f"  ID: {customer['id']}")
        print(f"  Email: {customer['email']}")
        print(f"  Created: {datetime.fromtimestamp(customer['created']).isoformat()}")

        # List subscriptions for this customer
        print(f"\nListing subscriptions for customer {customer['id']}...")
        subscriptions = stripe.Subscription.list(customer=customer['id'])
        print(f"Found {len(subscriptions.data)} subscriptions")

        if not subscriptions.data:
            print(f"❌ No subscriptions found for customer: {customer['id']}")
            return False

        # Check for active subscriptions
        active_subscriptions = [s for s in subscriptions.data if s['status'] == 'active']
        print(f"Active subscriptions: {len(active_subscriptions)}")

        if not active_subscriptions:
            print(f"❌ No active subscriptions found")
            print(f"Subscription statuses: {[s['status'] for s in subscriptions.data]}")
            return False

        # Display details of the first active subscription
        subscription = active_subscriptions[0]
        print(f"\nSubscription details:")
        print(f"  ID: {subscription['id']}")
        print(f"  Status: {subscription['status']}")
        print(f"  Created: {datetime.fromtimestamp(subscription['created']).isoformat()}")
        print(f"  Current period start: {datetime.fromtimestamp(subscription['current_period_start']).isoformat()}")
        print(f"  Current period end: {datetime.fromtimestamp(subscription['current_period_end']).isoformat()}")
        print(f"  Items: {len(subscription['items']['data'])}")

        # Get the plans/prices
        for i, item in enumerate(subscription['items']['data']):
            print(f"\nItem {i+1}:")
            print(f"  Price ID: {item['price']['id']}")
            print(f"  Product ID: {item['price']['product']}")
            
            # Try to get product details
            try:
                product = stripe.Product.retrieve(item['price']['product'])
                print(f"  Product name: {product['name']}")
                print(f"  Product description: {product.get('description', 'N/A')}")
            except Exception as e:
                print(f"  Could not get product details: {e}")

        print("\n✅ SUCCESS: Stripe API integration is working correctly!")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    # Get email from command line argument or use default
    email = sys.argv[1] if len(sys.argv) > 1 else "test@example.com"
    
    print("=" * 60)
    print(f"Stripe API Connection Test for {email}")
    print("=" * 60)
    
    success = test_stripe_connection(email)
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED: Stripe integration is working correctly!")
    else:
        print("❌ TEST FAILED: Issues found with Stripe integration")
    print("=" * 60)
    
    sys.exit(0 if success else 1)