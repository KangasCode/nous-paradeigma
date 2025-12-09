"""
Stripe webhook handlers for subscription management
"""
import stripe
import os
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from models import User, Subscription

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeWebhookHandler:
    """Handle Stripe webhook events"""
    
    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str) -> dict:
        """
        Verify Stripe webhook signature
        
        Args:
            payload: Raw webhook payload
            signature: Stripe signature header
            
        Returns:
            Verified event object
        """
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )
    
    @staticmethod
    def handle_checkout_completed(event_data: dict, db: Session):
        """Handle checkout.session.completed event"""
        session = event_data['object']
        customer_email = session.get('customer_email')
        customer_id = session.get('customer')
        subscription_id = session.get('subscription')
        
        # Find user by email
        user = db.query(User).filter(User.email == customer_email).first()
        if not user:
            print(f"User not found for email: {customer_email}")
            return
        
        # Create or update subscription
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()
        
        if subscription:
            subscription.stripe_customer_id = customer_id
            subscription.stripe_subscription_id = subscription_id
            subscription.status = "active"
            subscription.updated_at = datetime.utcnow()
        else:
            subscription = Subscription(
                user_id=user.id,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
                status="active"
            )
            db.add(subscription)
        
        # Update user subscriber status
        user.is_subscriber = True
        db.commit()
        
        # Sync to ACTIVE_SUBSCRIBERS audience (removes from CHECKOUT_VISITED)
        try:
            from email_service import sync_active_subscriber
            user_name = user.first_name or user.full_name or None
            sync_active_subscriber(user.email, user_name)
            print(f"✅ Stripe: Synced {user.email} to active subscribers")
        except Exception as e:
            print(f"⚠️ Resend sync error in checkout_completed (non-critical): {e}")
    
    @staticmethod
    def handle_subscription_updated(event_data: dict, db: Session):
        """Handle customer.subscription.updated event"""
        subscription_obj = event_data['object']
        subscription_id = subscription_obj['id']
        status = subscription_obj['status']
        current_period_start = datetime.fromtimestamp(subscription_obj['current_period_start'])
        current_period_end = datetime.fromtimestamp(subscription_obj['current_period_end'])
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if not subscription:
            print(f"Subscription not found: {subscription_id}")
            return
        
        # Update subscription
        subscription.status = status
        subscription.current_period_start = current_period_start
        subscription.current_period_end = current_period_end
        subscription.updated_at = datetime.utcnow()
        
        # Update user subscriber status
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.is_subscriber = (status == "active")
        
        db.commit()
        
        # Sync to appropriate Resend audience based on status
        if user:
            try:
                user_name = user.first_name or user.full_name or None
                if status == "active":
                    from email_service import sync_active_subscriber
                    sync_active_subscriber(user.email, user_name)
                    print(f"✅ Stripe: Synced {user.email} to active subscribers (status: {status})")
                elif status in ["canceled", "past_due", "unpaid"]:
                    from email_service import sync_canceled_subscriber
                    sync_canceled_subscriber(user.email, user_name)
                    print(f"✅ Stripe: Synced {user.email} to canceled subscribers (status: {status})")
            except Exception as e:
                print(f"⚠️ Resend sync error in subscription_updated (non-critical): {e}")
    
    @staticmethod
    def handle_subscription_deleted(event_data: dict, db: Session):
        """Handle customer.subscription.deleted event"""
        subscription_obj = event_data['object']
        subscription_id = subscription_obj['id']
        
        # Find subscription
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()
        
        if not subscription:
            print(f"Subscription not found: {subscription_id}")
            return
        
        # Update subscription status
        subscription.status = "canceled"
        subscription.updated_at = datetime.utcnow()
        
        # Update user subscriber status
        user = db.query(User).filter(User.id == subscription.user_id).first()
        if user:
            user.is_subscriber = False
        
        db.commit()
        
        # Sync to CANCELED_SUBSCRIBERS audience
        if user:
            try:
                from email_service import sync_canceled_subscriber
                user_name = user.first_name or user.full_name or None
                sync_canceled_subscriber(user.email, user_name)
                print(f"✅ Stripe: Synced {user.email} to canceled subscribers (deleted)")
            except Exception as e:
                print(f"⚠️ Resend sync error in subscription_deleted (non-critical): {e}")
    
    @staticmethod
    def process_webhook_event(event: dict, db: Session):
        """
        Process webhook event based on type
        
        Args:
            event: Stripe event object
            db: Database session
        """
        event_type = event['type']
        event_data = event['data']
        
        handlers = {
            'checkout.session.completed': StripeWebhookHandler.handle_checkout_completed,
            'customer.subscription.updated': StripeWebhookHandler.handle_subscription_updated,
            'customer.subscription.deleted': StripeWebhookHandler.handle_subscription_deleted,
        }
        
        handler = handlers.get(event_type)
        if handler:
            handler(event_data, db)
        else:
            print(f"Unhandled event type: {event_type}")

# Stripe helper functions
def create_checkout_session(price_id: str, customer_email: str, success_url: str, cancel_url: str) -> dict:
    """
    Create a Stripe checkout session
    
    Args:
        price_id: Stripe price ID
        customer_email: Customer email
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is canceled
        
    Returns:
        Checkout session object
    """
    try:
        session = stripe.checkout.Session.create(
            customer_email=customer_email,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create checkout session: {str(e)}"
        )

def create_customer_portal_session(customer_id: str, return_url: str) -> dict:
    """
    Create a Stripe customer portal session for managing subscriptions
    
    Args:
        customer_id: Stripe customer ID
        return_url: URL to return to after portal session
        
    Returns:
        Portal session object
    """
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create portal session: {str(e)}"
        )


