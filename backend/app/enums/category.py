from enum import Enum


class ProductCategory(str, Enum):
    DAIRY = "dairy"
    MEAT = "meat"
    FISH = "fish"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    GROCERIES = "groceries"
    DRINKS = "drinks"
    FROZEN = "frozen"
    SWEETS = "sweets"
    OTHER = "other"