import os
import sys

# Boot django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from django.apps import apps
from django.db import models

def get_sqlalchemy_type(field):
    if isinstance(field, models.AutoField):
        return "Integer", "index=True"
    elif isinstance(field, models.BigAutoField):
        return "BigInteger", "index=True"
    elif isinstance(field, models.EmailField):
        return f"String({field.max_length or 255})", f"unique={field.unique}, index=True"
    elif isinstance(field, models.CharField):
        return f"String({field.max_length or 255})", ""
    elif isinstance(field, models.TextField):
        return "Text", ""
    elif isinstance(field, models.IntegerField) or isinstance(field, models.PositiveIntegerField):
        return "Integer", ""
    elif isinstance(field, models.SmallIntegerField) or isinstance(field, models.PositiveSmallIntegerField):
        return "SmallInteger", ""
    elif isinstance(field, models.DateTimeField):
        return "DateTime", ""
    elif isinstance(field, models.DateField):
        return "Date", ""
    elif isinstance(field, models.TimeField):
        return "Time", ""
    elif isinstance(field, models.DecimalField):
        return f"Numeric(precision={field.max_digits}, scale={field.decimal_places})", ""
    elif isinstance(field, models.FileField):
        return "String(255)", ""
    elif isinstance(field, models.JSONField):
        return "JSON", ""
    elif isinstance(field, models.BooleanField):
        return "Boolean", ""
    elif isinstance(field, models.ForeignKey):
        # We need to map to foreign key
        related_model = field.related_model
        related_table = related_model._meta.db_table
        related_field = field.target_field
        # Find type of target field
        target_type, _ = get_sqlalchemy_type(related_field)
        fk_str = f"ForeignKey('{related_table}.{related_field.column}')"
        return target_type, f"{fk_str}"
    else:
        return "String(255)", ""

def main():
    app = apps.get_app_config('api')
    
    output = []
    output.append('# Generated SQLAlchemy models from Django models')
    output.append('from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, Date, Time, Numeric, Boolean, JSON, ForeignKey, SmallInteger')
    output.append('from sqlalchemy.orm import relationship, declarative_base')
    output.append('')
    output.append('Base = declarative_base()')
    output.append('')
    
    # Sort models so tables referenced by foreign keys are declared first or we just declare them normally.
    # Declarative base in SQLAlchemy can resolve string foreign keys, so order doesn't strictly matter.
    for model_name, model in app.models.items():
        class_name = model.__name__
        table_name = model._meta.db_table
        managed = getattr(model._meta, 'managed', True)
        
        output.append(f'class {class_name}(Base):')
        output.append(f'    __tablename__ = "{table_name}"')
        
        # We can add a docstring
        doc = model.__doc__ or f"SQLAlchemy model for table {table_name}"
        output.append(f'    """{doc.strip()}"""')
        output.append('')
        
        for field in model._meta.fields:
            col_name = field.column
            sq_type, extra = get_sqlalchemy_type(field)
            
            # Check if this is primary key
            pk_args = []
            if field.primary_key:
                pk_args.append("primary_key=True")
                # If AutoField, set autoincrement
                if isinstance(field, (models.AutoField, models.BigAutoField)):
                    pk_args.append("autoincrement=True")
            
            if extra:
                if pk_args:
                    col_def = f'Column({sq_type}, {extra}, {", ".join(pk_args)})'
                else:
                    col_def = f'Column({sq_type}, {extra})'
            else:
                if pk_args:
                    col_def = f'Column({sq_type}, {", ".join(pk_args)})'
                else:
                    col_def = f'Column({sq_type}, nullable={field.null})'
                    
            output.append(f'    {col_name} = {col_def}')
            
        output.append('')
        output.append('')
        
    os.makedirs('api_fastapi', exist_ok=True)
    with open('api_fastapi/models_sqlalchemy.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
        
    print("SQLAlchemy models generated successfully in api_fastapi/models_sqlalchemy.py")

if __name__ == '__main__':
    main()
