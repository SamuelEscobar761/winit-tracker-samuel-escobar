from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from app.ai.errors import AiUnavailable
from app.rules.healing.healer import RulesHealer
from app.rules.healing.incidents import DriftIncident, IncidentLog
from app.rules.healing.patch import RuleEdit, RulesPatchProposal
from app.rules.healing.proposals import ProposalBoard
from app.rules.registry import RulesRegistry
from app.rules.store import RulesStore
from tests.ai.fakes import FixedCanary, ScriptedModel

GOOD_PATCH = RulesPatchProposal(
    diagnosis="The Party Name button was renamed",
    edits=[RuleEdit(path="ui.party_name_button", value="Search by Name")],
)


class Setup:
    def __init__(
        self,
        tmp_path: Path,
        answer: RulesPatchProposal | Exception = GOOD_PATCH,
        canary_passes: bool = True,
        auto_apply: bool = True,
        max_repairs: int = 3,
    ) -> None:
        self.registry = RulesRegistry(RulesStore(tmp_path))
        self.incidents = IncidentLog()
        self.proposals = ProposalBoard()
        self.canary = FixedCanary(canary_passes)
        self.model = ScriptedModel(answer)
        self.now = datetime(2026, 10, 16, tzinfo=UTC)
        self.healer = RulesHealer(
            self.model,
            self.registry,
            self.incidents,
            self.proposals,
            self.canary,
            auto_apply,
            max_repairs,
            lambda: self.now,
        )

    def open_incident(self, message: str = "Locator timed out") -> str:
        incident = DriftIncident(
            kind="ui", message=message, rules_version=1, evidence={"buttons": [{"label": "X"}]}
        )
        return self.incidents.add(incident).id


async def test_a_verified_repair_is_applied_without_a_developer(tmp_path: Path) -> None:
    setup = Setup(tmp_path)

    outcome = await setup.healer.repair(setup.open_incident())

    assert outcome.status == "repaired"
    assert outcome.applied_version == 2
    assert setup.registry.current.ui.party_name_button == "Search by Name"
    entry = setup.registry.changelog()[-1]
    assert (entry.actor, entry.model, entry.canary) == ("agent", "scripted", "fixed")


async def test_the_canary_runs_on_the_candidate_before_activation(tmp_path: Path) -> None:
    setup = Setup(tmp_path)

    await setup.healer.repair(setup.open_incident())

    assert setup.canary.verified[0].ui.party_name_button == "Search by Name"


async def test_a_failed_canary_never_changes_the_active_rules(tmp_path: Path) -> None:
    setup = Setup(tmp_path, canary_passes=False)
    incident_id = setup.open_incident()

    outcome = await setup.healer.repair(incident_id)

    assert outcome.status == "failed"
    assert setup.registry.current.version == 1
    assert setup.proposals.all()[0].status == "rejected"
    assert setup.incidents.get(incident_id) is not None


async def test_without_auto_apply_a_person_approves_the_proposal(tmp_path: Path) -> None:
    setup = Setup(tmp_path, auto_apply=False)

    outcome = await setup.healer.repair(setup.open_incident())

    assert outcome.status == "awaiting_review"
    assert setup.registry.current.version == 1
    assert outcome.proposal_id is not None
    setup.healer.approve(outcome.proposal_id)
    assert setup.registry.current.ui.party_name_button == "Search by Name"
    assert setup.registry.changelog()[-1].actor == "manual"


async def test_a_rejected_proposal_cannot_be_approved_later(tmp_path: Path) -> None:
    setup = Setup(tmp_path, auto_apply=False)
    outcome = await setup.healer.repair(setup.open_incident())
    assert outcome.proposal_id is not None

    setup.healer.reject(outcome.proposal_id)

    with pytest.raises(ValueError, match="rejected"):
        setup.healer.approve(outcome.proposal_id)


async def test_a_patch_with_forbidden_content_is_refused(tmp_path: Path) -> None:
    bad = RulesPatchProposal(
        diagnosis="x", edits=[RuleEdit(path="api.search_path", value="https://evil.example/")]
    )
    setup = Setup(tmp_path, answer=bad)

    outcome = await setup.healer.repair(setup.open_incident())

    assert outcome.status == "failed"
    assert setup.canary.verified == []
    assert setup.registry.current.version == 1


async def test_an_empty_patch_is_reported_as_not_understood(tmp_path: Path) -> None:
    setup = Setup(tmp_path, answer=RulesPatchProposal(diagnosis="Nothing differs", edits=[]))

    outcome = await setup.healer.repair(setup.open_incident())

    assert outcome.status == "failed"
    assert "Nothing differs" in outcome.message or "between 1 and" in outcome.message


async def test_a_model_outage_leaves_the_rules_untouched(tmp_path: Path) -> None:
    setup = Setup(tmp_path, answer=AiUnavailable("down"))

    outcome = await setup.healer.repair(setup.open_incident())

    assert outcome.status == "failed"
    assert setup.registry.current.version == 1


async def test_repairs_are_rate_limited_per_hour(tmp_path: Path) -> None:
    setup = Setup(tmp_path, answer=AiUnavailable("down"), max_repairs=2)
    first, second, third = (setup.open_incident(f"m{i}") for i in range(3))

    await setup.healer.repair(first)
    await setup.healer.repair(second)
    limited = await setup.healer.repair(third)
    setup.now += timedelta(hours=1, seconds=1)
    later = await setup.healer.repair(third)

    assert limited.status == "open"
    assert "rate limit" in limited.message
    assert later.status == "failed"


async def test_the_prompt_carries_evidence_but_no_credentials(tmp_path: Path) -> None:
    setup = Setup(tmp_path)

    await setup.healer.repair(setup.open_incident())

    prompt = setup.model.prompts[0]
    assert '"evidence"' in prompt
    assert '"current_rules"' in prompt
    assert "token" not in prompt.lower()
