#!/usr/bin/env python3
from flask import request, make_response, redirect, jsonify, session

import models
from config import config
from models.shopify.shopify_store import ShopifyStore
from services.shopify_service import ShopifyService
from utils.logger import logger
from utils.pagination import PaginationParams, PaginatedResponse
from api.v1.views.shopify import shopify_auth_bp, shopify_bp


@shopify_auth_bp.route("/install", methods=["GET", "POST"], strict_slashes=False)
def install_shopify():
    """Initiate shopify app installation
    """
    shop = request.args.get("shop")

    if not shop:
        return make_response(jsonify({
            'error': 'Shop parameter is required',
        }), 400)

    # Generate the authorization URL
    redirect_uri = f'{config.APP_URL}/api/v1/shopify/auth/callback'
    auth_url = ShopifyService.generate_auth_url(shop, redirect_uri)

    return redirect(auth_url, code=302)

@shopify_auth_bp.route("/callback", methods=["GET"], strict_slashes=False)
def auth_callback():
    """Handle Shopify OAuth callback
    """
    shop = request.args.get('shop')
    code = request.args.get('code')
    state = request.args.get('state')
    hmac_param = request.args.get('hmac')

    # # Verify the HMAC signature from Shopify
    # if not verify_shopify_hmac(request, config.SHOPIFY_CLIENT_SECRET)

    # Verify state parameter to prevent CSRF
    if state != config.SHOPIFY_STATE_TOKEN:
        logger.error(f"invalid state parameter: {state}")

    if not shop or not code:
        return make_response(jsonify({
            'error': 'Missing shop or code parameter',
        }), 400)

    try:
        # Exchange code for access token
        token_data = ShopifyService.exchange_token(shop, code)
        access_token = token_data.get('access_token')
        scope = token_data.get('scope')

        if not access_token:
            return make_response(jsonify({
                'error': 'Failed to get access token'
            }), 400)

        shopify_store = models.storage.find(ShopifyStore, shop_domain=shop)
        if shopify_store:
            shopify_store.access_token = access_token
            shopify_store.scope = scope
            shopify_store.is_active = True
        else:
            shopify_store = ShopifyStore()
            shopify_store.shop_domain=shop
            shopify_store.access_token=access_token
            shopify_store.is_active=True
            shopify_store.scope=scope

            models.storage.new(shopify_store)

        models.storage.save()

        # Initialize the shopify service with the access token
        shopify_service = ShopifyService(access_token=access_token, shop=shop)

        shop_info = shopify_service.get_shop_info()

        # Register required webhooks
        webhooks_callback_url = f'{config.APP_URL}/api/v1/shopify/webhooks'
        webhooks_to_register = [
            'orders/paid',
            'orders/create',
        ]

        for topic in webhooks_to_register:
            try:
                shopify_service.register_webhook(topic, webhooks_callback_url)
                logger.info(f'Registered webhook {topic} for shop {shop}')
            except Exception as e:
                logger.error(f'Failed to register webhook {topic}: {str(e)}')

        # store installation info in session
        session['shopify_shop'] = shop
        session['shopify_access_token'] = access_token

        # Redirect to success page or dashboard
        redirect_url = f'{config.APP_URL}/dashboard?shop={shop}&installed=true'
        logger.info(redirect_url)
        return redirect(redirect_url)
    except Exception as e:
        logger.error(f'Error during OAuth callback: {str(e)}')
        return make_response(jsonify({
            'error': str(e)
        }), 500)


@shopify_bp.route("/stores", methods=["GET"], strict_slashes=False)
def get_shops():
    """Get all installed Shopify stores with pagination"""

    # Get pagination parameters from request
    pagination_params = PaginationParams.from_request(
        default_per_page=20,
        max_per_page=100
    )

    # Build query for ShopifyStore
    query = models.storage.query(ShopifyStore)

    # Optional: Add filters if needed (e.g., only active stores)
    is_active = request.args.get('is_active', type=bool)
    if is_active is not None:
        query = query.filter(ShopifyStore.is_active == is_active)

    # Optional: Add search functionality
    search = request.args.get('search')
    if search:
        query = query.filter(
            ShopifyStore.shop_domain.ilike(f'%{search}%')
        )

    # Get total count before pagination
    total_items = query.count()

    # Apply pagination
    paginated_query = query.offset(pagination_params.offset).limit(pagination_params.per_page)
    shops = paginated_query.all()

    # Define serializer for ShopifyStore objects
    def serialize_shop(shop: ShopifyStore) -> dict:
        """Convert ShopifyStore object to dictionary"""
        return {
            'id': shop.id,
            'shop_domain': shop.shop_domain,
            'access_token': shop.access_token[:3] + '...........' if shop.access_token else None,  # Mask token for security
            'scope': shop.scope,
            'is_active': shop.is_active,
            'created_at': shop.created_at.isoformat() if shop.created_at else None,
            'updated_at': shop.updated_at.isoformat() if shop.updated_at else None,
            'webhooks_registered': shop.webhooks_registered if hasattr(shop, 'webhooks_registered') else None
        }

    # Create paginated response
    response = PaginatedResponse(
        items=shops,
        params=pagination_params,
        total_items=total_items
    )

    # Return response with serializer
    return response.to_response(item_serializer=serialize_shop)