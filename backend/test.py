import models
from models.shopify.shopify_store import ShopifyStore

test_store = ShopifyStore()
test_store.shop_domain = 'test.shopify.com'
print(test_store)
test_store.save()
stores = models.storage.all(ShopifyStore)
print(stores)