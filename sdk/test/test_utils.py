# Local libraries
from tracers.utils import (
    delta
)


def test_delta() -> None:
    assert delta(start_timestamp=0.0, end_timestamp=0.0) == 0.0
