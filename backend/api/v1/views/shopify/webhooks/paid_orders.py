#!/usr/bin/env python3
from flask import request, make_response, jsonify

import models
from config import config
from models.shopify.shopify_store import ShopifyStore
from services.print_job_service import PrintJobService
from utils.logger import logger
from api.v1.views.shopify import shopify_utils
from api.v1.views.shopify.webhooks import webhook_bp


@webhook_bp.route("", methods=["POST"], strict_slashes=False)
def handle_shopify_webhook():
    """Handle incoming Shopify webhooks
    """
    # Verify the webhook is from Shopify
    hmac_header = request.headers.get("X-Shopify-Hmac-Sha256")
    if not hmac_header:
        logger.warning('Webhook missing HMAC header')
        return make_response(jsonify({
            'error': 'unauthorized',
        }), 401)

    # Verify HMAC signature
    raw_data = request.get_data()
    is_valid = shopify_utils.verify_shopify_hmac(raw_data, hmac_header, config.SHOPIFY_CLIENT_SECRET)

    if not is_valid:
        logger.warning('Invalid webhook HMAC signature')
        return make_response(jsonify({
            'error': 'unauthorized',
        }), 401)

    # Get webhook topic
    topic = request.headers.get('X-Shopify-Topic')
    shop_domain = request.headers.get('X-Shopify-Shop-Domain')

    logger.info(f'Received webhook topic {topic}')

    try:
        webhook_data = request.get_json()

        # Process based on topic
        if topic == 'orders/paid':
            process_paid_order(webhook_data, shop_domain)
        elif topic == 'orders/create':
            process_new_order(webhook_data, shop_domain)
        elif topic == 'orders/fulfilled':
            process_fulfilled_order(webhook_data, shop_domain)

        logger.info(f'Successfully processed {topic} webhook for {shop_domain}')
        return make_response(jsonify({
            'status': 'success',
        }), 200)
    except Exception as e:
        logger.error(f'Error processing webhook: {str(e)}')
        return make_response(jsonify({
            'error': 'Internal server error',
        }), 500)

def process_paid_order(order_data: dict, shop_domain: str):
    """Process paid order and generate receipt
    """
    order_id = str(order_data.get('id', ''))
    order_number = order_data.get('order_number')
    customer = order_data.get('customer', {})
    total_price = order_data.get('total_price')

    logger.info(f'Processing paid order #{order_number} for {shop_domain}')

    shop = models.storage.find(ShopifyStore, shop_domain=shop_domain, is_active=True)
    if shop is None:
        return

    print_service = PrintJobService(shop_id=shop.id)
    print_job = print_service.create_from_order(order_data)
    if print_job:
        logger.info(f'Print job created: #{print_job.job_number} for order {order_id}')

    return
    # TODO: Implement receipt generation logic here
    # 1. Generate unique receipt ID
    # 2. Store receipt in your database
    # 3. Add receipt reference to Shopify order notes
    # 4. Send receipt to customer via email

    # Example: Add receipt reference to order
    # receipt_id = generate_receipt()
    # add_receipt_to_order(shop_domain, order_id, receipt_id)

def process_new_order(order_data: dict, shop_domain: str):
    """Process new order webhook
    """
    order_id = order_data.get('id')
    logger.info(f'New order #{order_id} created for {shop_domain}')

    if order_data.get('financial_status') == 'paid':
        process_paid_order(order_data, shop_domain)


def process_fulfilled_order(order_data: dict, shop_domain: str):
    """Process fulfilled order webhook
    """
    order_id = order_data.get('id')
    logger.info(f'Order #{order_id} fulfilled for {shop_domain}')
