import argparse
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path

from app.cases.matching.analyzer import PersonCaseAnalysis, analyze_person_cases
from app.config.settings import Settings
from app.people.models import Person
from app.people.names import build_search_query
from app.providers.base import CapProvider
from app.providers.errors import CaptchaRequired, NoResults, ProviderError
from app.providers.factory import create_provider
from app.providers.models import SearchResponse

DETAIL_PREVIEW_LIMIT = 5


def parse_arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Supervised check of one person against the real portal."
    )
    parser.add_argument("first_name")
    parser.add_argument("last_name")
    parser.add_argument("--details", type=int, default=1, help="cases to open (default 1)")
    parser.add_argument("--headed", action="store_true", help="show the browser window")
    parser.add_argument("--record", type=Path, help="folder where the raw JSON is saved")
    parser.add_argument("--yes", action="store_true", help="skip the confirmation question")
    return parser.parse_args(argv)


def build_settings(arguments: argparse.Namespace) -> Settings:
    return Settings.model_validate(
        {
            "cap_provider": "live",
            "admin_token": "local-smoke",
            "live_headless": not arguments.headed,
        }
    )


def confirm(settings: Settings) -> bool:
    print(f"This will contact {settings.cap_base_url} with the configured pacing:")
    print(f"  {settings.cap_action_delay_seconds:g} s after every action, max")
    print(f"  {settings.cap_max_actions_per_minute} actions per minute.")
    return input("Continue? [y/N] ").strip().lower() == "y"


def save_raw(folder: Path | None, name: str, payload: object) -> None:
    if folder is None:
        return
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"  saved {folder / name}")


async def search_with_captcha_help(
    provider: CapProvider, query: str, headed: bool
) -> SearchResponse:
    try:
        return await provider.search(query)
    except CaptchaRequired:
        if not headed:
            raise
        input("A CAPTCHA appeared. Solve it in the browser window, then press Enter. ")
        return await provider.search(query)


def print_summary(person: Person, analysis: PersonCaseAnalysis) -> None:
    statuses = Counter(item.case.public_status_label for item in analysis.cases)
    print(f"Kept {len(analysis.cases)} cases of {person.first_name} {person.last_name};")
    print(f"discarded {analysis.discarded_total} ({dict(analysis.discarded_counts)})")
    print(f"statuses: {dict(statuses)}; possible identities: {len(analysis.identity_groups)}")


async def open_details(
    provider: CapProvider, query: str, analysis: PersonCaseAnalysis, arguments: argparse.Namespace
) -> None:
    eligible = [item.case for item in analysis.cases if item.case.is_detail_eligible]
    for case in eligible[: arguments.details]:
        response = await provider.fetch_detail(query, case.case_number)
        detail = response.detail
        charges = [charge.statute for charge in detail.displayed_charges]
        print(f"  {case.case_number}: amount due {detail.amount_due}, charges {charges}")
        save_raw(arguments.record, f"select_{case.case_key}.json", response.raw_payload)


async def run(arguments: argparse.Namespace, settings: Settings) -> int:
    person = Person(first_name=arguments.first_name, last_name=arguments.last_name)
    query = build_search_query(person.first_name, person.last_name)
    provider = create_provider(settings)
    try:
        print(f"Searching {query!r}…")
        response = await search_with_captcha_help(provider, query, arguments.headed)
        save_raw(arguments.record, f"search_{query.replace(', ', '_')}.json", response.raw_payload)
        analysis = analyze_person_cases(person, response.cases)
        print_summary(person, analysis)
        await open_details(provider, query, analysis, arguments)
    except NoResults:
        print("The portal found no cases for that name.")
    except ProviderError as error:
        print(f"{type(error).__name__}: {error}")
        return 1
    finally:
        await provider.aclose()
    return 0


def main() -> int:
    arguments = parse_arguments(sys.argv[1:])
    settings = build_settings(arguments)
    if not arguments.yes and not confirm(settings):
        return 0
    return asyncio.run(run(arguments, settings))


if __name__ == "__main__":
    raise SystemExit(main())
