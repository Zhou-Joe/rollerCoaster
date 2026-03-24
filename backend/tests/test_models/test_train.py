from app.models.train import Vehicle, Train
from app.models.common import LoadCase, TrainState


def test_vehicle_creation():
    vehicle = Vehicle(id="veh_001", length_m=2.5, dry_mass_kg=500.0, capacity=4)
    assert vehicle.id == "veh_001"
    assert vehicle.length_m == 2.5
    assert vehicle.passenger_mass_per_person_kg == 75.0


def test_train_creation():
    train = Train(id="train_001", vehicle_ids=["veh_001", "veh_002"])
    assert train.id == "train_001"
    assert train.coupling_gap_m == 0.5
    assert train.current_state == TrainState.STOPPED
    assert train.load_case == LoadCase.EMPTY


def test_train_with_route():
    train = Train(
        id="train_001",
        vehicle_ids=["veh_001"],
        route_assignment="route_main",
        current_state=TrainState.MOVING,
        load_case=LoadCase.FULLY_LOADED,
        front_position_s=150.0
    )
    assert train.route_assignment == "route_main"
    assert train.current_state == TrainState.MOVING