from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from enum import Enum


class ConditionOperator(str, Enum):
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_OR_EQUAL = ">="
    LESS_OR_EQUAL = "<="
    IS_TRUE = "is_true"
    IS_FALSE = "is_false"


class LogicGate(str, Enum):
    AND = "and"
    OR = "or"


class Condition(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    property_name: str
    operator: ConditionOperator
    value: Optional[Any] = None


class Action(BaseModel):
    id: str
    target_type: str
    target_id: str
    command: str
    parameters: Dict[str, Any] = {}


class Timer(BaseModel):
    id: str
    duration_s: float
    start_condition_id: Optional[str] = None
    reset_condition_id: Optional[str] = None
    current_value_s: float = 0.0
    running: bool = False


class VisualRule(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    conditions: List[str]
    condition_logic: LogicGate = LogicGate.AND
    actions: List[str]
    timers: List[str] = []
    priority: int = 0
    enabled: bool = True


class ControlScript(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    script_content: str
    allowed_apis: List[str] = [
        "get_train", "is_block_clear", "set_switch",
        "set_equipment_state", "allow_dispatch", "get_timer"
    ]
    enabled: bool = True