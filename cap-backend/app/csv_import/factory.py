from datetime import date

from app.config.settings import Settings
from app.csv_import.importer import CsvImporter
from app.csv_import.row_validator import RowValidator
from app.people.variants.config import NameVariantConfig


def create_csv_importer(
    settings: Settings, variant_config: NameVariantConfig, today: date
) -> CsvImporter:
    validator = RowValidator(variant_config, today)
    return CsvImporter(validator, settings.csv_max_bytes, settings.csv_max_rows)
