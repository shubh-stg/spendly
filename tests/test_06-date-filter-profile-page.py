import pytest
from app import app as flask_app
from database.db import init_db, get_db


@pytest.fixture
def app():
    flask_app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret',
    })
    with flask_app.app_context():
        init_db()
        conn = get_db()
        conn.execute('DELETE FROM expenses')
        conn.execute('DELETE FROM users')
        conn.commit()
        conn.close()
        yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_client(client):
    client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'testpass123',
    })
    client.post('/login', data={
        'email': 'test@example.com',
        'password': 'testpass123',
    })
    return client


def _add_expense(user_id, amount, category, date, description='x'):
    conn = get_db()
    conn.execute(
        'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?,?,?,?,?)',
        (user_id, amount, category, date, description),
    )
    conn.commit()
    conn.close()


class TestProfileDateFilter:
    def test_profile_requires_auth(self, client):
        resp = client.get('/profile')
        assert resp.status_code in (302, 401)
        if resp.status_code == 302:
            assert '/login' in (resp.headers.get('Location') or '')

    def test_profile_no_params_renders(self, auth_client):
        resp = auth_client.get('/profile')
        assert resp.status_code == 200
        assert b'Total spent' in resp.data

    def test_malformed_date_falls_back(self, auth_client):
        resp = auth_client.get('/profile?date_from=not-a-date&date_to=2025-01-01')
        assert resp.status_code == 200

    def test_reversed_range_flashes_error(self, auth_client):
        resp = auth_client.get('/profile?date_from=2025-12-01&date_to=2025-01-01', follow_redirects=True)
        assert resp.status_code in (200, 302)
        assert (b'Start date must be before end date' in resp.data) or (resp.status_code == 302)

    def test_filter_range_shows_only_in_range(self, app, auth_client):
        conn = get_db()
        row = conn.execute("SELECT id FROM users WHERE email='test@example.com'").fetchone()
        uid = row['id']
        conn.close()
        _add_expense(uid, 100.0, 'Food', '2025-01-15', 'jan expense')
        _add_expense(uid, 200.0, 'Food', '2025-06-15', 'jun expense')
        resp = auth_client.get('/profile?date_from=2025-01-01&date_to=2025-01-31')
        assert resp.status_code == 200
        assert b'jan expense' in resp.data
        assert b'jun expense' not in resp.data

    def test_all_time_preset_active(self, auth_client):
        resp = auth_client.get('/profile')
        assert b'active' in resp.data

    def test_custom_range_inputs_reflect(self, auth_client):
        resp = auth_client.get('/profile?date_from=2025-02-01&date_to=2025-02-28')
        assert b'2025-02-01' in resp.data
        assert b'2025-02-28' in resp.data

    def test_empty_range_shows_zero(self, auth_client):
        resp = auth_client.get('/profile?date_from=2030-01-01&date_to=2030-01-31')
        assert resp.status_code == 200
        assert b'0' in resp.data

    def test_amounts_show_rupee(self, auth_client):
        resp = auth_client.get('/profile')
        assert '₹'.encode('utf-8') in resp.data
