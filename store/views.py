from django.shortcuts import get_object_or_404
from .filters import ProductFilter
from .pagination import DefaultPagination
from rest_framework.mixins import (
    CreateModelMixin,
    RetrieveModelMixin,
    DestroyModelMixin,
    UpdateModelMixin,
)
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
from django.db.models import Count
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import generics
from rest_framework import viewsets
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework import status
from .permissions import IsAdminOrReadOnly
from .models import (
    Product,
    Collection,
    OrderItem,
    Reviews,
    Cart,
    CartItem,
    Customer,
    Order,
    ProductImage,
)
from .serializers import (
    ProductSerializer,
    CollectionSerializer,
    ReviewsSerializer,
    CartSerializer,
    CartItemSerializer,
    AddCartItemSerializer,
    UpdateCartItemSerializer,
    CustomerSerializer,
    OrderSerializer,
    CreateOrderSerializer,
    UpdateOrderSerializer,
    ProductImageSerializer,
)


# Create your views here.


class CartItemViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return AddCartItemSerializer
        elif self.request.method == "PATCH":
            return UpdateCartItemSerializer
        return CartItemSerializer

    def get_serializer_context(self):
        return {"cart_id": self.kwargs["cart_pk"]}

    def get_queryset(self):
        return CartItem.objects.filter(cart_id=self.kwargs["cart_pk"]).select_related(
            "product"
        )


class CartViewSet(
    CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, GenericViewSet
):
    queryset = Cart.objects.prefetch_related("items__product").all()
    serializer_class = CartSerializer


class ReviewsViewSet(viewsets.ModelViewSet):
    # queryset = Reviews.objects.all()
    serializer_class = ReviewsSerializer

    def get_queryset(self):
        return Reviews.objects.filter(product_id=self.kwargs["product_pk"])

    def get_serializer_context(self):
        return {"product_id": self.kwargs["product_pk"]}


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.prefetch_related("images").all()
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ["title", "description"]
    ordering_fields = ["unit_price", "last_update"]

    # def get_queryset(self):
    #     query_set = Product.objects.all()
    #     collection_id = self.request.query_params.get("collection_id")
    #     if collection_id is not None:
    #         query_set = query_set.filter(collection_id=collection_id)

    #     return query_set

    def get_serializer_context(self):
        return {"request": self.request}

    def destroy(self, request, *args, **kwargs):
        if OrderItem.objects.filter(product_id=kwargs["pk"]).exists():
            return Response(
                {"Error": "Product cannot be deleted."},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return super().destroy(request, *args, **kwargs)

    # def delete(self, request, pk):
    #     product = get_object_or_404(Product, pk=pk)
    #     product.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class ProductImageViewSet(ModelViewSet):
    serializer_class = ProductImageSerializer

    def get_serializer_context(self):
        return {"product_id": self.kwargs["product_pk"]}

    def get_queryset(self):
        return ProductImage.objects.filter(product_id=self.kwargs["product_pk"])


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAdminUser]

    @action(detail=False, methods=["GET", "PUT"], permission_classes=[IsAuthenticated])
    def me(self, request):
        (customer, created) = Customer.objects.get_or_create(user_id=request.user.id)
        if request.method == "GET":
            serializer = CustomerSerializer(customer)
            return Response(serializer.data)
        elif request.method == "PUT":
            serializer = CustomerSerializer(customer, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.annotate(products_count=Count("products")).all()
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        collection = self.get_object()
        if Product.objects.filter(collection=collection).exists():
            return Response(
                {"error": "Collection has products so it cannot be deleted"},
                status=status.HTTP_405_METHOD_NOT_ALLOWED,
            )
        return super().destroy(request, *args, **kwargs)

    # def delete(self, request, pk):
    #     collection = get_object_or_404(Collection, pk=pk)
    #     if collection.products.count() > 0:
    #         return Response(
    #             {"error": "Collection has products so it cannot be deleted"},
    #             status=status.HTTP_405_METHOD_NOT_ALLOWED,
    #         )
    #     collection.delete()
    #     return Response(status=status.HTTP_204_NO_CONTENT)


class OrderViewSet(ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAdminUser()]
        return [IsAuthenticated()] 

    def create(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data, context={"user_id": self.request.user.id}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateOrderSerializer
        elif self.request.method == "PATCH":
            return UpdateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all()
        (customer_id, created) = Customer.objects.only("id").get_or_create(
            user_id=user.id
        )
        return Order.objects.filter(customer_id=customer_id)


# class ProductList(generics.ListCreateAPIView):  # GENERIC VIEWS
#     queryset = Product.objects.select_related("collection").all()
#     serializer_class = ProductSerializer

#     def get_serializer_context(self):
#         return {"request": self.request}


# class ProductDetails(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Product.objects.all()
#     serializer_class = ProductSerializer

#     def delete(self, request, pk):
#         product = get_object_or_404(Product, pk=pk)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class CollectionList(generics.ListCreateAPIView):  # GENERIC VIEWS
#     queryset = Collection.objects.annotate(products_count=Count("products")).all()
#     serializer_class = CollectionSerializer


# class CollectionDetails(generics.RetrieveUpdateDestroyAPIView):
#     queryset = Collection.objects.annotate(products_count=Count("products"))
#     serializer_class = CollectionSerializer

#     def delete(self, request, pk):
#         collection = get_object_or_404(Collection, pk=pk)
#         if collection.products.count() > 0:
#             return Response(
#                 {"error": "Collection has products so it cannot be deleted"},
#                 status=status.HTTP_405_METHOD_NOT_ALLOWED,
#             )
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# class ProductList(APIView):  #CLASS BASED VIEWS
#     def get(self, request):
#         query_set = Product.objects.select_related("collection").all()
#         serializer = ProductSerializer(
#             query_set, many=True, context={"request": request}
#         )
#         return Response(serializer.data)

#     def post(self, request):
#         serializer = ProductSerializer(data=request.data)
#         serializer.is_valid(
#             raise_exception=True
#         )  # it validate data if validation faild it automatically raise error 400
#         serializer.validated_data
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# class ProductDetails(APIView):
#     def get(self, request, id):
#         product = get_object_or_404(Product, pk=id)
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)

#     def put(self, request, id):
#         product = get_object_or_404(Product, pk=id)
#         serializer = ProductSerializer(product, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     def delete(self, request, id):
#         product = get_object_or_404(Product, pk=id)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(["GET", "POST"])
# def products_list(request):    #FUNCTION BASED VIEWS
#     if request.method == "GET":
#         query_set = Product.objects.select_related("collection").all()
#         serializer = ProductSerializer(
#             query_set, many=True, context={"request": request}
#         )
#         return Response(serializer.data)
#     elif request.method == "POST":  # it use for deserializing objects
#         serializer = ProductSerializer(data=request.data)
#         serializer.is_valid(
#             raise_exception=True
#         )  # it validate data if validation faild it automatically raise error 400
#         serializer.validated_data
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)


# @api_view(["GET", "PUT", "DELETE"])
# def product_details(request, id):
#     product = get_object_or_404(Product, pk=id)
#     if request.method == "GET":
#         serializer = ProductSerializer(product)
#         return Response(serializer.data)
#     elif request.method == "PUT":
#         serializer = ProductSerializer(product, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
#     elif request.method == "DELETE":
#         # if product.orderitem_set.Count() > 0:
#         # return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
#         product.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)


# @api_view(["GET", "PUT", "DELETE"])
# def collection_details(request, pk):
#     collection = get_object_or_404(
#         Collection.objects.annotate(products_count=Count("products")), pk=pk
#     )
#     if request.method == "GET":
#         serializer = CollectionSerializer(collection)
#         return Response(serializer.data)
#     elif request.method == "PUT":
#         serializer = CollectionSerializer(Collection, data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.validated_data()
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     elif request.method == "DELETE":
#         if collection.products.count() > 0:
#             return Response(
#                 {"error": "Collection has products so it cannot be deleted"},
#                 status=status.HTTP_405_METHOD_NOT_ALLOWED,
#             )
#         collection.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)

#     return Response("ok")


# @api_view(["GET", "POST"])
# def collection_list(request):
#     if request.method == "GET":
#         query_set = Collection.objects.annotate(products_count=Count("products")).all()
#         serializer = CollectionSerializer(query_set, many=True)
#         return Response(serializer.data)
#     elif request.method == "POST":
#         serializer = CollectionSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.validated_data()
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
