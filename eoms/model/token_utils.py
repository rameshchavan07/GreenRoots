import time
import secrets
from eoms.model.db import get_cursor, get_connection

def generate_token(email, expiry_minutes=30):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Delete any old tokens for this email
    cursor.execute('DELETE FROM reset_tokens WHERE email = %(email)s;', {'email': email})
    
    token = secrets.token_hex(16)
    expiry_time = time.time() + (expiry_minutes * 60)

    query = '''
        INSERT INTO reset_tokens (token, email, expiry_time)
        VALUES (%(token)s, %(email)s, %(expiry_time)s);
    '''
    cursor.execute(query, {'token': token, 'email': email, 'expiry_time': expiry_time})
    conn.commit()
    return token


def is_token_valid(token):
    cleanup_expired_tokens()
    reset_token = get_reset_token_by_token(token)
    if not reset_token:
        return {'valid': False, 'message': 'Token not found'}

    if time.time() <= reset_token['expiry_time']:
        return {'valid': True, 'email': reset_token['email']}
    else:
        delete_reset_token_by_token(token)
        return {'valid': False, 'message': 'Token expired'}


def get_reset_token_by_token(token):
    cursor = get_cursor()
    query = 'SELECT * FROM reset_tokens WHERE token = %(token)s;'
    cursor.execute(query, {'token': token})
    return cursor.fetchone()


def delete_reset_token_by_token(token):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reset_tokens WHERE token = %(token)s;', {'token': token})
    conn.commit()
    return cursor.rowcount


def cleanup_expired_tokens():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reset_tokens WHERE expiry_time < %(now)s;', {'now': time.time()})
    conn.commit()
