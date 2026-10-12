"""Exercise the real cold-start schema path against a pre-Russian database."""
import hashlib
import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ['DATABASE_URL'] = 'sqlite://'
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'api'))
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import common
import models
from database import Base

table = models.RussianPlacementResult.__table__
tokens = common._model_signature_tokens()
start = tokens.index(table.name)
model_tokens = tokens[start:start + 1 + len(table.columns)]
assert model_tokens == [table.name, *[column.name for column in table.columns]]
old_tokens = tokens[:start] + tokens[start + len(model_tokens):]
old_fingerprint = hashlib.sha1('|'.join(old_tokens).encode()).hexdigest()[:10]
old_stamp = common._STAMP_BASE + '_' + old_fingerprint
common._STAMP_CACHE['v'] = None
new_stamp = common.schema_stamp()
assert new_stamp != old_stamp, 'Adding only the Russian model must change the stamp'
assert new_stamp.endswith(common.models_fingerprint())

engine = create_engine('sqlite://', poolclass=StaticPool)
Session = sessionmaker(bind=engine)
# Fixture only: simulate an already migrated database from the prior release.
# Explicitly EXCLUDE the new table. Its creation must happen inside bootstrap.
Base.metadata.create_all(engine, tables=[t for t in Base.metadata.sorted_tables if t.name != table.name])
with Session() as db:
    db.add(models.SchemaMigration(version=old_stamp))
    for version, _ in common.migrations.MIGRATIONS:
        db.add(models.SchemaMigration(version=version))
    db.commit()
assert table.name not in inspect(engine).get_table_names()

with patch.object(common, 'engine', engine), patch.object(common, 'SessionLocal', Session):
    common._SCHEMA_OK = None
    common._SCHEMA_BOOT_OK = False
    common._SCHEMA_PENDING = False
    assert not common._schema_ready(), 'The previous release stamp must not skip bootstrap'
    # Same gate and real helper used by main.py; no schema helpers are mocked.
    if not common._schema_ready():
        common._schema_bootstrap()
    assert table.name in inspect(engine).get_table_names()
    columns = {column['name'] for column in inspect(engine).get_columns(table.name)}
    assert columns == {column.name for column in table.columns}
    indexes = inspect(engine).get_indexes(table.name)
    assert any(index['column_names'] == ['attempt_id'] and index['unique'] for index in indexes)
    assert {fk['referred_table'] for fk in inspect(engine).get_foreign_keys(table.name)} == {'leads', 'branches'}
    assert common._SCHEMA_PENDING
    assert common.seal_schema(), 'entry.py must persist the new stamp after bootstrap'
    with Session() as db:
        assert db.query(models.SchemaMigration).filter_by(version=new_stamp).count() == 1
    # Next cold start must recognize the new stamp and avoid schema work.
    common._SCHEMA_OK = None
    common._SCHEMA_BOOT_OK = False
    assert common._schema_ready()
    with patch.object(common, '_create_missing_tables', side_effect=AssertionError('Unexpected repeat DDL')):
        common._schema_bootstrap()
    assert not common.seal_schema()
print('PASS: automatic model fingerprint changes stamp; real cold-start bootstrap creates Russian table, columns, unique attempt index and foreign keys; seal and next-start fast path succeed')
print(f'Previous-model stamp: {old_stamp}; current stamp: {new_stamp}')
