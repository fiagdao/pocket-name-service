create role web_anon nologin;
grant select on all tables in schema public to web_anon;

create role authenticator noinherit login password 'password';
grant web_anon to authenticator;
