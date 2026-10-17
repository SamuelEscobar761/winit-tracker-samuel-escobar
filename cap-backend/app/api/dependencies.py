from fastapi import Request

from app.ai.services import AiServices
from app.csv_import.importer import CsvImporter
from app.jobs.container import JobSystem
from app.jobs.service import JobService


def get_job_system(request: Request) -> JobSystem:
    system: JobSystem = request.app.state.job_system
    return system


def get_job_service(request: Request) -> JobService:
    return get_job_system(request).service


def get_ai_services(request: Request) -> AiServices:
    services: AiServices = request.app.state.ai
    return services


def get_csv_importer(request: Request) -> CsvImporter:
    importer: CsvImporter = request.app.state.csv_importer
    return importer
