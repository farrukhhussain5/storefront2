from rest_framework import serializers
from django.db import transaction
from store.models import (
    Product,
    Collection,
    Reviews,
    Cart,
    CartItem,
    Customer,
    Order,
    OrderItem,
    ProductImage,
)
from decimal import Decimal


class ReviewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reviews
        fields = ["id", "name", "discription", "date"]

    def create(self, validated_data):
        product_id = self.context["product_id"]
        return Reviews.objects.create(product_id=product_id, **validated_data)


class SimpleProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "title", "unit_price"]


class CartItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart_item: CartItem):
        return cart_item.quantity * cart_item.product.unit_price

    class Meta:
        model = CartItem
        fields = ["id", "product", "quantity", "total_price"]


class CartSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()

    def get_total_price(self, cart: Cart):
        return sum(
            [item.quantity * item.product.unit_price for item in cart.items.all()]
        )

    class Meta:
        model = Cart
        fields = ["id", "items", "total_price"]


class AddCartItemSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField()

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("No Product found with this ID.")
        return value

    def save(self, **kwargs):
        cart_id = self.context["cart_id"]
        product_id = self.validated_data["product_id"]
        quantity = self.validated_data["quantity"]

        try:
            cart_item = CartItem.objects.get(cart_id=cart_id, product_id=product_id)
            cart_item.quantity += quantity
            cart_item.save()
            self.instance = cart_item
        except CartItem.DoesNotExist:
            self.instance = CartItem.objects.create(
                cart_id=cart_id, **self.validated_data
            )

        return self.instance

    class Meta:
        model = CartItem
        fields = ["id", "product_id", "quantity"]


class UpdateCartItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CartItem
        fields = ["quantity"]


class CollectionSerializer(serializers.ModelSerializer):
    # id = serializers.IntegerField()
    # title = serializers.CharField(max_length=255)
    class Meta:
        model = Collection
        fields = ["id", "title", "products_count"]

    products_count = serializers.IntegerField(read_only=True)


class ProductImageSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        product_id = self.context["product_id"]
        return ProductImage.objects.create(product_id=product_id, **validated_data)

    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "slug",
            "inventory",
            "unit_price",
            "collection",
            "images",
        ]

    # price = serializers.DecimalField(
    #     max_digits=6, decimal_places=2, source="unit_price"
    # )
    # price_with_tax = serializers.SerializerMethodField(method_name="calculate_tax")
    # collection = serializers.StringRelatedField()
    # collection = serializers.HyperlinkedRelatedField(
    #     view_name="collection-details", queryset=Collection.objects.all()
    # )

    def calculate_tax(self, product: Product):
        return product.unit_price * Decimal(1.1)


class CustomerSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = Customer
        fields = ["id", "user_id", "phone", "birth_date", "membership"]


class OrderItemSerializer(serializers.ModelSerializer):
    product = SimpleProductSerializer()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ["id", "placed_at", "payment_status", "customer", "items"]


class UpdateOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["payment_status"]


class CreateOrderSerializer(serializers.Serializer):
    cart_id = serializers.UUIDField()

    def validate_cart_id(self, cart_id):
        if not Cart.objects.filter(pk=cart_id).exists():
            raise serializers.ValidationError("No cart found with the given id.")
        elif CartItem.objects.filter(cart_id=cart_id).count() == 0:
            raise serializers.ValidationError("Cart is Empty.")
        return cart_id

    def save(self, **kwargs):
        with transaction.atomic():
            cart_id = self.validated_data["cart_id"]
            (customer, created) = Customer.objects.get_or_create(
                user_id=self.context["user_id"]
            )
            order = Order.objects.create(customer=customer)

            cart_item = CartItem.objects.select_related("product").filter(
                cart_id=cart_id
            )

            order_items = [
                OrderItem(
                    order=order,
                    product=item.product,
                    unit_price=item.product.unit_price,
                    quantity=item.quantity,
                )
                for item in cart_item
            ]

            OrderItem.objects.bulk_create(order_items)

            Cart.objects.filter(pk=cart_id).delete()

            return order
