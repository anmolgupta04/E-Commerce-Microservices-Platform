from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer, StockAdjustSerializer
from .permissions import IsInternalService


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    """
    list/search/filter/paginate products, plus an internal stock endpoint
    that the Orders service calls synchronously before confirming an order.
    """
    queryset = Product.objects.all().order_by("id")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "sku"]
    search_fields = ["name", "description", "sku"]
    ordering_fields = ["price", "stock", "created_at"]

    @action(detail=True, methods=["post"], url_path="adjust-stock", permission_classes=[IsInternalService])
    def adjust_stock(self, request, pk=None):
        """
        Internal service-to-service endpoint: Orders calls this (REST, sync)
        to decrement stock when an order is placed, and to roll it back if
        payment fails.
        """
        product = self.get_object()
        serializer = StockAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        qty = serializer.validated_data["quantity"]

        if product.stock + qty < 0:
            return Response(
                {"detail": "insufficient stock", "available": product.stock},
                status=status.HTTP_409_CONFLICT,
            )
        product.stock += qty
        product.save(update_fields=["stock"])
        return Response(ProductSerializer(product).data)
