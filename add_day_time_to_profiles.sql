-- Add day_of_week and time_bucket columns to profiles table
-- Following the user's working SQL structure exactly

ALTER TABLE public.profiles
ADD COLUMN day_of_week INTEGER,
ADD COLUMN time_bucket TEXT;

ALTER TABLE public.profiles
ALTER COLUMN day_of_week
SET DEFAULT floor(random() * 7)::int;

ALTER TABLE public.profiles
ALTER COLUMN time_bucket
SET DEFAULT (
  ARRAY['morning','afternoon','evening','night']
)[floor(random() * 4 + 1)];

ALTER TABLE public.profiles
ALTER COLUMN day_of_week DROP DEFAULT,
ALTER COLUMN time_bucket DROP DEFAULT;

ALTER TABLE public.profiles
ALTER COLUMN day_of_week
SET DEFAULT floor(random() * 7)::int;

ALTER TABLE public.profiles
ALTER COLUMN time_bucket
SET DEFAULT (
  ARRAY['morning','afternoon','evening','night']
)[floor(random() * 4 + 1)];

ALTER TABLE public.profiles
ADD CONSTRAINT check_day_of_week_range
CHECK (day_of_week BETWEEN 0 AND 6);

ALTER TABLE public.profiles
ADD CONSTRAINT check_time_bucket_values
CHECK (time_bucket IN ('morning','afternoon','evening','night'));
