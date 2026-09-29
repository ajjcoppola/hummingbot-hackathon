from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))

from mainnet_health_watchdog import flat_restart_decision  # noqa: E402


def test_ignores_a_managed_position():
    assert flat_restart_decision(
        n_running=1, n_pos=1, flat_streak=9, flat_polls=3, cooldown_active=False
    ) == ""


def test_watches_until_the_poll_threshold():
    assert flat_restart_decision(
        n_running=1, n_pos=0, flat_streak=2, flat_polls=3, cooldown_active=False
    ) == "watching_flat"


def test_hard_restarts_a_flat_running_bot():
    assert flat_restart_decision(
        n_running=1, n_pos=0, flat_streak=3, flat_polls=3, cooldown_active=False
    ) == "flat_hard_restart"


def test_cooldown_blocks_a_second_restart():
    assert flat_restart_decision(
        n_running=1, n_pos=0, flat_streak=5, flat_polls=3, cooldown_active=True
    ) == "flat_restart_cooldown"


def test_no_bot_is_not_this_branch():
    assert flat_restart_decision(
        n_running=0, n_pos=0, flat_streak=5, flat_polls=3, cooldown_active=False
    ) == ""


def test_unconfirmed_flat_holds_even_at_threshold():
    assert flat_restart_decision(
        n_running=1,
        n_pos=0,
        flat_streak=8,
        flat_polls=3,
        cooldown_active=False,
        confirmed_flat=False,
    ) == "rpc_flake_hold"


def test_confirmed_flat_still_hard_restarts():
    assert flat_restart_decision(
        n_running=1,
        n_pos=0,
        flat_streak=8,
        flat_polls=8,
        cooldown_active=False,
        confirmed_flat=True,
    ) == "flat_hard_restart"
