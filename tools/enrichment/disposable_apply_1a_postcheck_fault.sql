-- Disposable-only postcheck fault injection. It deliberately changes the
-- publication status of the is_free target so the migration's publication
-- digest postcheck must roll the transaction back.

CREATE OR REPLACE FUNCTION public.disposable_apply_1a_postcheck_trip()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF NEW.id = '41bb7d76-9416-4e46-a065-7a51c9735d0e'::uuid
     AND NEW.is_free IS DISTINCT FROM OLD.is_free THEN
    NEW.publication_status := 'under_review';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER disposable_apply_1a_postcheck_trip_trigger
BEFORE UPDATE OF is_free ON public.facilities
FOR EACH ROW
EXECUTE FUNCTION public.disposable_apply_1a_postcheck_trip();
