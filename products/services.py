from .repositories import ProductRepository

class ProductService:
    """
    Handles business logic and ETL pipelines for the products app.
    Communicates with ProductRepository for data access.
    """
    def __init__(self):
        self.repository = ProductRepository()
