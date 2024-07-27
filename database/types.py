"""Database Types

Sometimes nodes fail type validation because the node author accidentally defined a tuple like `'output': ('image')` instead of `'output': ('image',)`
"""

from typing import Any, Dict, List, Tuple, Union, Optional, Literal
from pydantic import BaseModel, Field, model_validator
import json


InputData = Dict[
    str,
    Dict[
        str,
        Union[
            Tuple[str],
            Tuple[str, Dict[str, Any]],
            Tuple[List[str]],
            Tuple[List[str], Dict[str, Any]],
            List[Any],  # Hard to validate. E.g., see VHS VideoCombine input types
            Literal["*"],
        ],
    ],
]


class DatabaseNodeAttributes(BaseModel):
    name: str
    input: InputData
    output: Tuple[Union[str, List[str]], ...] = Field(default_factory=tuple)
    output_is_list: List[bool] = Field(default_factory=list)
    output_name: Optional[Tuple[str, ...]] = Field(default_factory=tuple)
    display_name: str
    description: str
    python_module: str
    category: str
    output_node: bool

    @model_validator(mode="before")
    def delete_hidden_input(cls, values):
        if "input" in values and "hidden" in values["input"]:
            del values["input"]["hidden"]
        return values

    @classmethod
    def from_tuple(cls, node_record: Tuple):
        node_dict = {
            "name": node_record[0],
            "input": json.loads(node_record[1]),
            "output": json.loads(node_record[2]),
            "output_is_list": json.loads(node_record[3]),
            "output_name": json.loads(node_record[4]) if node_record[4] else None,
            "display_name": node_record[5],
            "description": node_record[6],
            "python_module": node_record[7],
            "category": node_record[8],
            "output_node": bool(node_record[9]),
        }
        return cls(**node_dict)
