from django.db import migrations

SQL = """
CREATE OR REPLACE FUNCTION task_set_timestamps()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    IF NEW.created_at IS NULL THEN
      NEW.created_at := NOW();
    END IF;
    IF NEW.updated_at IS NULL THEN
      NEW.updated_at := NOW();
    END IF;
  END IF;

  IF TG_OP = 'UPDATE' THEN
    NEW.updated_at := NOW();
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_task_timestamps ON task_task;

CREATE TRIGGER trg_task_timestamps
BEFORE INSERT OR UPDATE ON task_task
FOR EACH ROW
EXECUTE FUNCTION task_set_timestamps();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS trg_task_timestamps ON task_task;
DROP FUNCTION IF EXISTS task_set_timestamps();
"""

class Migration(migrations.Migration):

    dependencies = [
        ("task", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(SQL, REVERSE_SQL),
    ]