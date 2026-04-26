from typing import TypeVar

from pydantic import BaseModel, ValidationError


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class SchemaGuard:
    """Validate plain payloads against Pydantic contracts."""

    def validate(self, schema: type[SchemaT], payload: object) -> SchemaT:
        try:
            return schema.model_validate(payload)
        except ValidationError as error:
            raise ValueError(f"schema validation failed for {schema.__name__}") from error

    def validate_many(self, schema: type[SchemaT], payloads: list[object]) -> list[SchemaT]:
        return [self.validate(schema, payload) for payload in payloads]
