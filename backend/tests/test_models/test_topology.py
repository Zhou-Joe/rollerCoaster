# backend/tests/test_models/test_topology.py
from app.models.topology import Junction, BlockPathInterval, Block, Station
from app.models.common import StationType


def test_junction_creation():
    junction = Junction(
        id="jct_001",
        incoming_path_id="path_001",
        outgoing_path_ids=["path_002", "path_003"],
        position_s=100.0
    )
    assert junction.id == "jct_001"
    assert junction.incoming_path_id == "path_001"
    assert len(junction.outgoing_path_ids) == 2


def test_block_path_interval():
    interval = BlockPathInterval(path_id="path_001", start_s=0.0, end_s=50.0)
    assert interval.path_id == "path_001"
    assert interval.start_s == 0.0
    assert interval.end_s == 50.0


def test_block_creation():
    block = Block(
        id="block_001",
        path_intervals=[
            BlockPathInterval(path_id="path_001", start_s=0.0, end_s=100.0)
        ]
    )
    assert block.id == "block_001"
    assert block.occupied is False
    assert block.reserved_by is None


def test_block_occupied():
    block = Block(
        id="block_001",
        path_intervals=[
            BlockPathInterval(path_id="path_001", start_s=0.0, end_s=100.0)
        ],
        occupied=True,
        reserved_by="train_001"
    )
    assert block.occupied is True
    assert block.reserved_by == "train_001"


def test_station_creation():
    station = Station(
        id="station_001",
        name="Main Station",
        station_type=StationType.LOAD,
        associated_block_ids=["block_001"],
        position_path_id="path_001",
        position_s=50.0
    )
    assert station.id == "station_001"
    assert station.name == "Main Station"
    assert station.station_type == StationType.LOAD