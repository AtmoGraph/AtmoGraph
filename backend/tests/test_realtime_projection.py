import pytest
from pydantic import ValidationError

from backend.api.prediction import (
    PredictionRequest,
    project_predictions,
)
from backend.api.realtime import EventBroker


BASE_PREDICTIONS = [
    {
        "node_id": "MARKET001",
        "node_name": "European Consumer Market",
        "node_type": "Market",
        "prediction": 0.4,
    }
]


def test_horizon_projection_changes_transparently():
    day_30 = project_predictions(BASE_PREDICTIONS, 30)[0]
    day_60 = project_predictions(BASE_PREDICTIONS, 60)[0]
    day_90 = project_predictions(BASE_PREDICTIONS, 90)[0]

    assert day_30["prediction"] == 0.4
    assert day_60["prediction"] == 0.328
    assert day_90["prediction"] == 0.272
    assert day_30["base_prediction"] == 0.4


def test_invalid_projection_horizon_is_rejected():
    with pytest.raises(ValueError, match="30, 60, 90"):
        project_predictions(BASE_PREDICTIONS, 45)


def test_prediction_request_validates_severity():
    with pytest.raises(ValidationError):
        PredictionRequest(
            disrupted_port_id="PORT003",
            disruption_type="PORT_CLOSURE",
            severity=1.5,
        )

    with pytest.raises(ValidationError):
        PredictionRequest(
            disrupted_port_id="PORT003",
            disruption_type="PORT_CLOSURE",
            severity=0.9,
            horizon_days=45,
        )


def test_event_broker_returns_only_new_events():
    broker = EventBroker(history_size=2)
    first = broker.publish("first", {"value": 1})
    second = broker.publish("second", {"value": 2})

    assert broker.events_since(0) == [first, second]
    assert broker.events_since(first["id"]) == [second]
