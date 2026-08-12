from typing import Literal

from pydantic import BaseModel, Field

class Dependency(BaseModel):

    source: str = Field(
        ...,
        description="ID of the source node"
    )


    target: str = Field(
        ...,
        description="ID of the target node"
    )


    type: Literal["depends_on", "communicates_with"] = Field(
        default="depends_on",
        description="Type of dependency relationship"
    )

