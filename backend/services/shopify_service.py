#!/usr/bin/env python3
from typing import Optional, Dict, Any

import requests
from shopify.resources import shop

from config import config
from utils.logger import logger


class ShopifyService:

    def __init__(self, access_token: Optional[str]=None, shop: Optional[str]=None):
        self.access_token = access_token
        self.shop = shop
        self.session = requests.Session()
        self.session.headers.update({
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
        }) if access_token else None

    @staticmethod
    def generate_auth_url(shop: str, redirect_uri: str) -> str:
        """Generate the shopify OAuth authorization URL

        Args:
            shop: The shop's myshopify domain (e.g., 'your-store.myshopify.com)
            redirect_uri: where Shopify redirects after authorization

        Returns:
            Authorization URL to redirect the merchant to
        """
        # Remove protocol if present
        shop = shop.replace('https://', '').replace('http://', '')

        # Ensure it ends with myshopify.com
        if not shop.endswith('.myshopify.com'):
            shop = f'{shop}.myshopify.com'

        params = {
            'client_id': config.SHOPIFY_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'scope': config.SHOPIFY_SCOPE,
            'state': config.SHOPIFY_STATE_TOKEN,
            'grant_options[]': 'per-user'
        }

        # 'response_type': 'code',

        url = f"https://{shop}/admin/oauth/authorize"
        request = requests.Request('GET', url, params=params).prepare()

        return request.url

    @staticmethod
    def exchange_token(shop: str, code: str) -> Dict[str, Any]:
        """Exchange OAuth code for access token
        """
        url = (
            f"https://{shop}/admin/oauth/access_token"
        )

        payload = {
            'client_id': config.SHOPIFY_CLIENT_ID,
            'client_secret': config.SHOPIFY_CLIENT_SECRET,
            'code': code,
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()

        return response.json()

    def get_shop_info(self, version: str = '2026-01') -> Dict[str, Any]:
        """Get shop information
        """
        if not self.access_token or not shop:
            raise ValueError('Access token and shop are required')

        url = f'https://{self.shop}/admin/api/{version}/shop.json'

        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        return response.json()

    def register_webhook(self, topic: str, address: str, version: str='2026-01') -> Dict[str, Any]:
        """Register a webhook with shopify

        Args:
            topic: Webhook topic (e.g., 'orders/create', 'orders/paid', 'orders/fulfilled')
            address: The URL where shopify should send the webhook payload
            version: API version to use

        Returns:
            Webhook registration response
        """
        if not self.access_token or not self.shop:
            raise ValueError('Access token and shop is required for webhook registration')

        url = f"https://{self.shop}/admin/api/{version}/webhooks.json"
        payload = {
            'webhook': {
                'topic': topic,
                'address': address,
                'format': 'json'
            }
        }

        try:
            response = self.session.post(url, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(response.text)
            if response.status_code == 422:
                error_response = response.json()
                if 'already_exists' in str(error_response):
                    raise ValueError(f"Webhook for topic '{topic}' already exists")
            raise Exception(f'Failed to register webhook: {str(e)}')

    def get_webhoooks(self, version: str='2026-01') -> Dict[str, Any]:
        """Get all registered webhooks for the store
        """
        if not self.access_token or not self.shop:
            raise ValueError('Access token and shop are required')

        url = f'https://{self.shop}/admin/api/{version}/webhooks.json'

        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def delete_webhook(self, webhook_id: int, version: str = '2026-01') -> bool:
        """Delete a specific webhook by ID
        """
        if not self.access_token or not self.shop:
            raise ValueError('Access token and shop are required')

        url = f"https://{self.shop}/admin/api/{version}/webhooks/{webhook_id}.json"

        response = self.session.delete(url, timeout=30)
        response.raise_for_status()
        return response.status_code == 200

    def get_order(self, order_id: int, version: str='2026-01') -> Dict[str, Any]:
        """Get a specific order by ID
        """
        if not self.access_token or not self.shop:
            raise ValueError('Access token and shop are required')

        url = f"https://{self.shop}/admin/api/{version}/orders/{order_id}.json"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def set_access_token(self, access_token: str, shop: str):
        """Update the access token and shop after initialization
        """
        self.access_token = access_token
        self.shop = shop
        self.session.headers.update({
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json',
        })