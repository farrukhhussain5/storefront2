from django.urls import path

# from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers
from . import views

# URLConf
router = routers.DefaultRouter()
router.register("products", views.ProductViewSet, basename="product")
router.register("collections", views.CollectionViewSet)
router.register("cart", views.CartViewSet)
router.register("customer", views.CustomerViewSet)
router.register("orders", views.OrderViewSet, basename="order")

products_router = routers.NestedDefaultRouter(router, "products", lookup="product")
products_router.register("reviews", views.ReviewsViewSet, basename="product-reviews")
products_router.register("images", views.ProductImageViewSet, basename="product-images")

cart_router = routers.NestedDefaultRouter(router, "cart", lookup="cart")
cart_router.register("items", views.CartItemViewSet, basename="cart-items")

router.urls

urlpatterns = router.urls + products_router.urls + cart_router.urls


# urlpatterns = [
#     path("products/", views.ProductList.as_view()),
#     path("collections/", views.CollectionList.as_view()),
#     path("products/<int:pk>/", views.ProductDetails.as_view()),
#     path(
#         "collections/<int:pk>/",
#         views.CollectionDetails.as_view(),
#         name="collection-details",
#     ),
# ]
