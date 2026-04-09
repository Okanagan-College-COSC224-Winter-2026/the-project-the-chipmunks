from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class CriterionInputSchema(Schema):
    id = fields.Int(load_default=None)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    description = fields.Str(load_default="")
    max_score = fields.Int(required=True, validate=validate.Range(min=1, max=100))
    weight = fields.Float(required=True, validate=validate.Range(min=0, max=100))
    position = fields.Int(required=True, validate=validate.Range(min=0))


class RubricBuilderInputSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=200))
    criteria = fields.List(
        fields.Nested(CriterionInputSchema),
        required=True,
        validate=validate.Length(min=1),
    )
    is_template = fields.Bool(load_default=False)
    template_name = fields.Str(load_default=None)

    @validates_schema
    def validate_weights(self, data, **kwargs):
        criteria = data.get("criteria", [])
        total = sum(c["weight"] for c in criteria)
        if abs(total - 100) > 0.01:
            raise ValidationError(
                f"Criteria weights must sum to 100 (got {total})",
                field_name="criteria",
            )


class CriterionOutputSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str()
    description = fields.Str()
    max_score = fields.Int()
    weight = fields.Float()
    position = fields.Int()


class RubricOutputSchema(Schema):
    id = fields.Int(dump_only=True)
    assignment_id = fields.Int()
    name = fields.Str()
    is_template = fields.Bool()
    template_name = fields.Str()
    criteria = fields.List(fields.Nested(CriterionOutputSchema))


rubric_builder_input = RubricBuilderInputSchema()
rubric_output = RubricOutputSchema()
rubrics_output = RubricOutputSchema(many=True)
