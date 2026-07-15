-- Lock down Django-managed tables exposed in Supabase's public schema.
-- The app uses Django as the only server-side API, so Supabase anon/authenticated
-- roles should not query these tables directly through PostgREST.

alter table public.auth_group enable row level security;
alter table public.auth_group_permissions enable row level security;
alter table public.auth_permission enable row level security;
alter table public.detection_customuser enable row level security;
alter table public.detection_customuser_groups enable row level security;
alter table public.detection_customuser_user_permissions enable row level security;
alter table public.detection_diseasedetection enable row level security;
alter table public.detection_useractivity enable row level security;
alter table public.detection_userstatistics enable row level security;
alter table public.django_admin_log enable row level security;
alter table public.django_content_type enable row level security;
alter table public.django_migrations enable row level security;
alter table public.django_session enable row level security;

revoke all on table public.auth_group from anon, authenticated;
revoke all on table public.auth_group_permissions from anon, authenticated;
revoke all on table public.auth_permission from anon, authenticated;
revoke all on table public.detection_customuser from anon, authenticated;
revoke all on table public.detection_customuser_groups from anon, authenticated;
revoke all on table public.detection_customuser_user_permissions from anon, authenticated;
revoke all on table public.detection_diseasedetection from anon, authenticated;
revoke all on table public.detection_useractivity from anon, authenticated;
revoke all on table public.detection_userstatistics from anon, authenticated;
revoke all on table public.django_admin_log from anon, authenticated;
revoke all on table public.django_content_type from anon, authenticated;
revoke all on table public.django_migrations from anon, authenticated;
revoke all on table public.django_session from anon, authenticated;

revoke all on all sequences in schema public from anon, authenticated;
