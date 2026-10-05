import re
from contextlib import contextmanager
from decimal import Decimal

import mysql.connector
from mysql.connector import Error

import config


class AppError(Exception):
    """An error whose message is safe and useful to show to the user."""


class ValidationError(AppError):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


CONSTRAINT_MESSAGES = {
    "uq_license_key": "That license key already exists. Use a different key.",
    "uq_active_seat": "That user already holds an active seat on this license.",
    "uq_vendor_name": "A vendor with that name already exists.",
    "uq_product_vendor_name": "That vendor already has a product with this name.",
    "uq_ltype_product_name": "That product already has a license type with this name.",
    "uq_dept_name": "A department with that name already exists.",
    "uq_dept_cc": "That cost center code is already used by another department.",
    "uq_user_email": "A user with that email already exists.",
    "uq_device_tag": "That asset tag is already in use.",
    "uq_purchase_order": "That order reference is already used by another purchase.",
    "uq_license_purchase": "That purchase already has a license.",
    "uq_subscription_license": "That license already has a subscription.",
    "chk_renewal_cost": "Renewal cost must be greater than zero.",
    "chk_renewal_dates": "The new end date must be after the previous end date.",
    "chk_alloc_period": "The allocation expiry date must be after the allocation date.",
    "chk_license_dates": "The license end date must be after its start date.",
    "chk_license_qty": "License quantity must be greater than zero.",
    "chk_license_status": "Invalid license status.",
    "chk_purchase_qty": "Purchase quantity must be greater than zero.",
    "chk_purchase_cost": "Unit cost cannot be negative.",
    "chk_sub_cost": "Cost per billing cycle must be greater than zero.",
    "chk_ltype_seats": "Seats per license must be greater than zero.",
    "chk_vendor_email": "Enter a valid contact email address.",
    "chk_user_email": "Enter a valid email address.",
}


def translate(err: Error) -> AppError:
    """Turn a driver error into a message a user can act on."""
    msg = err.msg or str(err)
    if err.errno == 1644:  # SIGNAL from a business-rule trigger
        return AppError(msg)
    if err.errno in (1062, 3819):
        m = re.search(r"key '(?:\w+\.)?(\w+)'", msg) or re.search(r"constraint '(\w+)'", msg)
        if m and m.group(1) in CONSTRAINT_MESSAGES:
            return AppError(CONSTRAINT_MESSAGES[m.group(1)])
        return AppError("That value conflicts with an existing record or violates a data rule.")
    if err.errno == 1451:
        return AppError("This record is still referenced by other records, so it can't be deleted.")
    if err.errno == 1452:
        return AppError("A selected related record doesn't exist.")
    if err.errno in (1048, 1364):
        return AppError("A required field is missing.")
    if err.errno in (2003, 2002, 1045, 1049):
        return AppError("Can't connect to the database. Check the DB settings in app/.env and that MySQL is running.")
    return AppError(f"Database error: {msg}")


def connect():
    try:
        return mysql.connector.connect(**config.DB, autocommit=False)
    except Error as e:
        raise translate(e) from e


def _plain(rows):
    for r in rows:
        for k, v in r.items():
            if isinstance(v, Decimal):
                r[k] = float(v)
    return rows


def query(sql, params=None):
    conn = connect()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        return _plain(cur.fetchall())
    except Error as e:
        raise translate(e) from e
    finally:
        conn.close()


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


@contextmanager
def transaction():
    """Yield a cursor; commit on success, roll back everything on any error."""
    conn = connect()
    try:
        cur = conn.cursor(dictionary=True)
        yield cur
        conn.commit()
    except Error as e:
        conn.rollback()
        raise translate(e) from e
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def call_procedure(name, args=()):
    conn = connect()
    try:
        cur = conn.cursor()
        result = cur.callproc(name, list(args))
        conn.commit()
        return result
    except Error as e:
        conn.rollback()
        raise translate(e) from e
    finally:
        conn.close()
